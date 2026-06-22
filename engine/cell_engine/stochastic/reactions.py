from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

from cell_engine.core.provenance import ParameterProvenance
from cell_engine.quantitative.geometry import AVOGADRO

# A propensity is a function (counts, volume_l) -> rate in molecules / second.
PropensityFn = Callable[[Mapping[str, float], float], float]
ParameterProvenanceInput = ParameterProvenance | tuple[ParameterProvenance, ...] | None


@dataclass(frozen=True)
class Reaction:
    """One reaction channel acting on molecule counts.

    ``reactants`` / ``products`` are stoichiometric multiplicities. ``propensity``
    returns the firing rate in molecules/second given current counts and the
    compartment volume. Build reactions with :func:`mass_action` or
    :func:`michaelis_menten` so the real-world rate constants convert correctly.
    ``parameter_provenance`` records source/unit/assumption/confidence metadata
    for constants without changing the numerical kinetics.
    """

    id: str
    reactants: dict[str, int]
    products: dict[str, int]
    propensity: PropensityFn
    source_id: str = ""
    notes: str = ""
    parameter_provenance: tuple[ParameterProvenance, ...] = ()

    def net_change(self) -> dict[str, int]:
        delta: dict[str, int] = {}
        for species, n in self.reactants.items():
            delta[species] = delta.get(species, 0) - n
        for species, n in self.products.items():
            delta[species] = delta.get(species, 0) + n
        return {s: d for s, d in delta.items() if d != 0}


@dataclass(frozen=True)
class ReactionNetwork:
    species: tuple[str, ...]
    reactions: tuple[Reaction, ...]
    volume_l: float

    def propensities(self, counts: Mapping[str, float]) -> list[float]:
        return [max(r.propensity(counts, self.volume_l), 0.0) for r in self.reactions]


_FACTORIAL = {0: 1, 1: 1, 2: 2, 3: 6, 4: 24}


def _normalize_parameter_provenance(
    parameter_provenance: ParameterProvenanceInput,
) -> tuple[ParameterProvenance, ...]:
    if parameter_provenance is None:
        return ()
    if isinstance(parameter_provenance, ParameterProvenance):
        return (parameter_provenance,)
    return tuple(parameter_provenance)


def _falling_factorial(x: float, n: int) -> float:
    """x*(x-1)*...*(x-n+1), clamped at 0. Reduces to x**n for large x and is the
    exact combinatorial count for small integer x (low-copy correctness)."""
    term = 1.0
    for i in range(n):
        term *= max(x - i, 0.0)
    return term


def mass_action(
    reaction_id: str,
    reactants: dict[str, int],
    products: dict[str, int],
    k: float,
    *,
    source_id: str = "",
    notes: str = "",
    parameter_provenance: ParameterProvenanceInput = None,
) -> Reaction:
    """Mass-action reaction from a *deterministic* rate constant ``k``.

    ``k`` is given in the usual macroscopic units (1/s for first order,
    M^-1 s^-1 for second order, M/s for zeroth-order production). The stochastic
    constant is ``c = k * (N_A * V)^(1 - order)`` and the propensity uses the
    combinatorial count so it stays exact at low copy numbers.
    """
    order = sum(reactants.values())

    def propensity(counts: Mapping[str, float], volume_l: float) -> float:
        c = k * (AVOGADRO * volume_l) ** (1 - order)
        combinatorial = 1.0
        for species, n in reactants.items():
            combinatorial *= _falling_factorial(counts.get(species, 0.0), n) / _FACTORIAL[n]
        return c * combinatorial

    return Reaction(
        reaction_id,
        dict(reactants),
        dict(products),
        propensity,
        source_id,
        notes,
        _normalize_parameter_provenance(parameter_provenance),
    )


def michaelis_menten(
    reaction_id: str,
    reactants: dict[str, int],
    products: dict[str, int],
    *,
    vmax_M_per_s: float = 0.0,
    km_M: float,
    substrate: str,
    hill: float = 1.0,
    cosubstrate: str | None = None,
    cosubstrate_km_M: float = 0.0,
    enzyme: str | None = None,
    kcat_per_s: float = 0.0,
    source_id: str = "",
    notes: str = "",
    parameter_provenance: ParameterProvenanceInput = None,
) -> Reaction:
    """Enzyme reaction with Michaelis-Menten (or Hill, if ``hill != 1``) kinetics.

    ``km_M`` (Km or S0.5) is in molar units. Concentration is read from the
    substrate count and compartment volume; the resulting velocity (M/s) is
    converted back to molecules/s.

    Vmax is set one of two ways:
    - fixed: pass ``vmax_M_per_s`` (= kcat * [E] with a fixed enzyme level), or
    - expressed: pass ``enzyme`` + ``kcat_per_s`` and Vmax is computed live as
      ``kcat * [enzyme]`` from the current enzyme count. This is the seam that
      lets gene expression (M034) drive metabolic flux (M033).

    For bi-substrate enzymes, pass ``cosubstrate`` and ``cosubstrate_km_M`` to add
    a Michaelis availability factor ``[C]/(Km_C+[C])`` for the second substrate
    (e.g. ATP for a kinase). It is ~1 when the cofactor is saturating — the regime
    the grounded ``km_M``/``hill`` were measured in — and falls to 0 as the
    cofactor is exhausted, so the reaction cannot drive a co-substrate negative.
    """
    if km_M <= 0:
        raise ValueError("km_M must be positive")

    def propensity(counts: Mapping[str, float], volume_l: float) -> float:
        scale = AVOGADRO * volume_l
        if enzyme is not None:
            vmax = kcat_per_s * counts.get(enzyme, 0.0) / scale  # M/s, live enzyme level
        else:
            vmax = vmax_M_per_s
        s_conc = counts.get(substrate, 0.0) / scale
        s_h = s_conc ** hill
        velocity = vmax * s_h / (km_M ** hill + s_h)  # M/s
        if cosubstrate is not None and cosubstrate_km_M > 0:
            c_conc = counts.get(cosubstrate, 0.0) / scale
            velocity *= c_conc / (cosubstrate_km_M + c_conc)
        return velocity * scale  # molecules/s

    return Reaction(
        reaction_id,
        dict(reactants),
        dict(products),
        propensity,
        source_id,
        notes,
        _normalize_parameter_provenance(parameter_provenance),
    )


def compose_networks(*networks: ReactionNetwork, volume_l: float | None = None) -> ReactionNetwork:
    """Merge sub-networks into one system: union of species, all reactions, shared volume.

    Reactions referencing the same species name share that pool automatically, so
    coupling is by naming (e.g. a gene-expression network whose ``protein`` is an
    enzyme a metabolic network reads). This is how scope grows: compose validated
    pathways rather than hand-write one monolith.
    """
    if not networks:
        raise ValueError("need at least one network to compose")
    species: list[str] = []
    seen: set[str] = set()
    reactions: list[Reaction] = []
    for net in networks:
        for s in net.species:
            if s not in seen:
                seen.add(s)
                species.append(s)
        reactions.extend(net.reactions)
    volume = volume_l if volume_l is not None else networks[0].volume_l
    return ReactionNetwork(species=tuple(species), reactions=tuple(reactions), volume_l=volume)
