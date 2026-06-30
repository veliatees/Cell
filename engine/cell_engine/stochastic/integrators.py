from __future__ import annotations

from dataclasses import dataclass
from math import inf, sqrt

from cell_engine.core.random import EngineRng
from cell_engine.stochastic.reactions import Reaction, ReactionNetwork


@dataclass(frozen=True)
class TrajectoryPoint:
    t: float
    counts: dict[str, float]


# ---------------------------------------------------------------------------
# Exact stochastic simulation (Gillespie Direct Method)
#
# Correct for any copy number and the right tool for low-copy species (genes,
# mRNA), where the discreteness and noise dominate. Cost scales with the number
# of reaction events, so it is slow for high-copy/high-flux systems.
# ---------------------------------------------------------------------------
def gillespie_step(
    network: ReactionNetwork,
    counts: dict[str, float],
    rng: EngineRng,
) -> tuple[Reaction | None, float]:
    """Advance one exact SSA event. Returns (fired_reaction, dt). Mutates counts."""
    props = network.propensities(counts)
    total = sum(props)
    if total <= 0.0:
        return None, inf

    dt = rng.expovariate(total)
    threshold = rng.random() * total
    cumulative = 0.0
    chosen = network.reactions[-1]
    for reaction, a in zip(network.reactions, props):
        cumulative += a
        if cumulative >= threshold:
            chosen = reaction
            break

    for species, delta in chosen.net_change().items():
        counts[species] = counts.get(species, 0.0) + delta
    return chosen, dt


def simulate_ssa(
    network: ReactionNetwork,
    initial_counts: dict[str, float],
    t_end: float,
    rng: EngineRng,
    *,
    max_steps: int = 5_000_000,
) -> TrajectoryPoint:
    """Run exact SSA to ``t_end`` (or until all propensities vanish)."""
    counts = dict(initial_counts)
    t = 0.0
    for _ in range(max_steps):
        _, dt = gillespie_step(network, counts, rng)
        if dt == inf:
            break
        if t + dt > t_end:
            break
        t += dt
    return TrajectoryPoint(t=t, counts=counts)


# ---------------------------------------------------------------------------
# Chemical Langevin Equation (Euler-Maruyama)
#
# Continuous approximation of the SSA, valid when every reaction fires many
# times per step (high-copy species). Each reaction contributes a drift term and
# a sqrt(propensity) diffusion term, so it preserves the right noise scaling
# (CV ~ 1/sqrt(N)) at a fixed cost per step rather than per event.
# ---------------------------------------------------------------------------
def cle_step(
    network: ReactionNetwork,
    counts: dict[str, float],
    dt: float,
    rng: EngineRng,
) -> dict[str, float]:
    """One Euler-Maruyama step of the chemical Langevin equation."""
    props = network.propensities(counts)
    updated = dict(counts)
    for reaction, a in zip(network.reactions, props):
        if a <= 0.0:
            continue
        fires = a * dt + sqrt(a * dt) * rng.gauss()
        for species, stoich in reaction.net_change().items():
            updated[species] = updated.get(species, 0.0) + stoich * fires
    for species in updated:
        if updated[species] < 0.0:
            updated[species] = 0.0
    return updated


def simulate_cle(
    network: ReactionNetwork,
    initial_counts: dict[str, float],
    t_end: float,
    dt: float,
    rng: EngineRng,
) -> TrajectoryPoint:
    if dt <= 0:
        raise ValueError("dt must be positive")
    counts = dict(initial_counts)
    t = 0.0
    while t < t_end - 1e-12:
        step = min(dt, t_end - t)
        counts = cle_step(network, counts, step, rng)
        t += step
    return TrajectoryPoint(t=t, counts=counts)


def partition_species_by_copy(
    counts: dict[str, float], *, threshold: float = 1000.0
) -> tuple[set[str], set[str]]:
    """Split species into (low_copy -> SSA, high_copy -> CLE) by a count threshold.

    The hybrid regime real cells require: genes/mRNA stay exact while abundant
    metabolites use the cheaper Langevin update.
    """
    low: set[str] = set()
    high: set[str] = set()
    for species, value in counts.items():
        (high if value >= threshold else low).add(species)
    return low, high


def simulate_hybrid(
    network: ReactionNetwork,
    initial_counts: dict[str, float],
    t_end: float,
    dt: float,
    rng: EngineRng,
    *,
    threshold: float = 1000.0,
    discrete_species: set[str] | None = None,
) -> TrajectoryPoint:
    """Operator-split hybrid: SSA for reactions touching a low-copy reactant,
    CLE for the rest, re-partitioned every step.

    A reaction is integrated exactly (SSA) whenever any of its reactants is below
    ``threshold`` copies, so discreteness is preserved exactly where it matters
    (gene expression, scarce intermediates) while abundant metabolite reactions
    take the cheap continuous update. In the all-low-copy limit it reduces to
    pure SSA; in the all-high-copy limit, to pure CLE.

    ``discrete_species`` pins a fixed set as the SSA partition (e.g. genes/mRNA)
    regardless of instantaneous count. This is the right choice for whole-cell
    runs: it keeps gene expression exact while metabolism stays on CLE, avoiding
    the trap where a fast-turnover but low-copy metabolic intermediate forces SSA
    into astronomically many events.
    """
    if dt <= 0:
        raise ValueError("dt must be positive")
    counts = dict(initial_counts)
    t = 0.0
    while t < t_end - 1e-12:
        step = min(dt, t_end - t)
        if discrete_species is not None:
            low = discrete_species
        else:
            low, _ = partition_species_by_copy(counts, threshold=threshold)
        slow = tuple(r for r in network.reactions if any(s in low for s in r.reactants))
        fast = tuple(r for r in network.reactions if r not in slow)

        if fast:
            counts = cle_step(
                ReactionNetwork(network.species, fast, network.volume_l), counts, step, rng
            )
        if slow:
            sub = ReactionNetwork(network.species, slow, network.volume_l)
            local = 0.0
            while True:
                _, event_dt = gillespie_step(sub, counts, rng)
                if event_dt == inf or local + event_dt > step:
                    break
                local += event_dt
        t += step
    return TrajectoryPoint(t=t, counts=counts)


# ---------------------------------------------------------------------------
# Tau-leaping (explicit Poisson tau-leap)
#
# Instead of advancing one reaction event at a time (SSA), fix a time step tau
# and fire each reaction a Poisson(a*tau) number of times. Cost is independent
# of the flux, so it is far cheaper than SSA for high-copy/high-flux species
# while preserving discreteness and the right (Poisson) event statistics in the
# regime where propensities are roughly constant over tau. It is an
# approximation: tau must be small enough that no propensity changes much over
# the step. Counts are clamped at zero (a known tau-leap artefact); choose tau
# conservatively for low-copy reactants or keep those on SSA via the hybrid.
# ---------------------------------------------------------------------------


def tau_leap_step(
    network: ReactionNetwork,
    counts: dict[str, float],
    tau: float,
    rng: EngineRng,
) -> dict[str, float]:
    """One explicit Poisson tau-leap of length ``tau``. Returns updated counts.

    Each reaction fires ``Poisson(propensity * tau)`` times; net stoichiometric
    changes are accumulated and applied, then every species is clamped at zero.
    """
    if tau <= 0:
        raise ValueError("tau must be positive")
    updated = dict(counts)
    props = network.propensities(updated)
    for reaction, a in zip(network.reactions, props):
        if a <= 0.0:
            continue
        fires = rng.poisson(a * tau)
        if fires == 0:
            continue
        for species, delta in reaction.net_change().items():
            updated[species] = updated.get(species, 0.0) + delta * fires
    for species, value in updated.items():
        if value < 0.0:
            updated[species] = 0.0
    return updated


def simulate_tau_leap(
    network: ReactionNetwork,
    initial_counts: dict[str, float],
    t_end: float,
    tau: float,
    rng: EngineRng,
) -> TrajectoryPoint:
    """Advance the network to ``t_end`` in fixed Poisson tau-leaps of size ``tau``."""
    if tau <= 0:
        raise ValueError("tau must be positive")
    counts = dict(initial_counts)
    t = 0.0
    while t < t_end - 1e-12:
        step = min(tau, t_end - t)
        counts = tau_leap_step(network, counts, step, rng)
        t += step
    return TrajectoryPoint(t=t, counts=counts)
