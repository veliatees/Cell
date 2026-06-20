from __future__ import annotations

from dataclasses import dataclass, field, replace
from math import sqrt

from cell_engine.core.random import EngineRng

# Ordered cell-cycle phases.
PHASES = ("G1", "S", "G2", "M")


@dataclass(frozen=True)
class CellCycleParams:
    """Checkpoints and durations for one cell's cycle.

    Growth here is a biomass *proxy* (a scalar that accumulates while nutrients
    are present), not full biomass synthesis from the metabolic network — that
    coupling is a later refinement. The state logic, checkpoints, genome
    replication, and stochastic division are the real content.
    """

    g1s_biomass: float = 2.0        # size checkpoint to leave G1
    g2m_biomass: float = 3.5        # size checkpoint to leave G2
    s_duration_s: float = 20.0      # time to replicate the genome
    m_duration_s: float = 5.0       # time spent in mitosis before division
    growth_per_s: float = 0.05      # biomass added per second when fed
    genome_species: tuple[str, ...] = ("gene",)
    oncogene_active: bool = False   # True -> checkpoints bypassed (uncontrolled)
    nutrient_species: str = "ATP"   # growth requires this to be present


@dataclass(frozen=True)
class CellCycleState:
    phase: str = "G1"
    biomass: float = 1.0
    counts: dict[str, float] = field(default_factory=dict)
    phase_time_s: float = 0.0       # time spent in the current phase
    generation: int = 0
    divisions: int = 0
    ready_to_divide: bool = False


def _fed(state: CellCycleState, params: CellCycleParams) -> bool:
    return state.counts.get(params.nutrient_species, 1.0) > 0.0


def step(state: CellCycleState, dt_s: float, params: CellCycleParams) -> CellCycleState:
    """Advance one cell by dt: grow, then evaluate the current phase's transition.

    Sets ``ready_to_divide`` at the end of M; the caller invokes :func:`divide`.
    With ``oncogene_active`` the size checkpoints (G1/S and G2/M) are ignored, so
    the cell cycles on phase durations alone regardless of size — uncontrolled
    proliferation.
    """
    if state.ready_to_divide:
        return state

    biomass = state.biomass + (params.growth_per_s * dt_s if _fed(state, params) else 0.0)
    phase_time = state.phase_time_s + dt_s
    phase = state.phase
    counts = state.counts
    bypass = params.oncogene_active

    if phase == "G1":
        if biomass >= params.g1s_biomass or bypass:
            phase, phase_time = "S", 0.0
    elif phase == "S":
        if phase_time >= params.s_duration_s:
            # Genome replication: duplicate the genome species.
            counts = dict(counts)
            for g in params.genome_species:
                counts[g] = counts.get(g, 0.0) * 2.0
            phase, phase_time = "G2", 0.0
    elif phase == "G2":
        if biomass >= params.g2m_biomass or bypass:
            phase, phase_time = "M", 0.0
    elif phase == "M":
        if phase_time >= params.m_duration_s:
            return replace(state, biomass=biomass, counts=counts, phase="M",
                           phase_time_s=phase_time, ready_to_divide=True)

    return replace(state, biomass=biomass, counts=counts, phase=phase, phase_time_s=phase_time)


def _binomial_split(n: float, rng: EngineRng) -> float:
    """Draw daughter A's share of n molecules, ~Binomial(n, 0.5).

    Exact Bernoulli sum for small counts (true partitioning noise at low copy);
    a clamped normal approximation for large counts (mean n/2, variance n/4).
    """
    n_round = int(round(n))
    if n_round <= 0:
        return 0.0
    if n_round <= 2000:
        return float(sum(1 for _ in range(n_round) if rng.random() < 0.5))
    a = round(0.5 * n_round + rng.gauss() * sqrt(0.25 * n_round))
    return float(min(max(a, 0), n_round))


def divide(
    state: CellCycleState, params: CellCycleParams, rng: EngineRng
) -> tuple[CellCycleState, CellCycleState]:
    """Split a mitotic cell into two daughters.

    Genome species segregate **exactly** in half (sister chromatids to each
    daughter); every other species partitions **binomially** (stochastic
    partitioning noise). Total counts are conserved exactly. Biomass halves.
    """
    if not state.ready_to_divide:
        raise ValueError("cell is not ready to divide")

    counts_a: dict[str, float] = {}
    counts_b: dict[str, float] = {}
    for species, n in state.counts.items():
        if species in params.genome_species:
            half = n / 2.0           # deterministic chromosome segregation
            counts_a[species] = half
            counts_b[species] = n - half
        else:
            a = _binomial_split(n, rng)
            counts_a[species] = a
            counts_b[species] = n - a

    daughter = lambda c: CellCycleState(
        phase="G1", biomass=state.biomass / 2.0, counts=c, phase_time_s=0.0,
        generation=state.generation + 1, divisions=0, ready_to_divide=False,
    )
    return daughter(counts_a), daughter(counts_b)


def simulate_lineage(
    state: CellCycleState,
    params: CellCycleParams,
    t_end_s: float,
    dt_s: float,
    rng: EngineRng,
) -> tuple[CellCycleState, int]:
    """Follow one daughter through repeated divisions; return (final cell, division count).

    A simple single-lineage tracker (keep daughter A at each division) used to
    compare proliferation rates, e.g. normal vs oncogene-active.
    """
    divisions = 0
    t = 0.0
    while t < t_end_s:
        state = step(state, dt_s, params)
        if state.ready_to_divide:
            state, _ = divide(state, params, rng)
            divisions += 1
        t += dt_s
    return state, divisions
