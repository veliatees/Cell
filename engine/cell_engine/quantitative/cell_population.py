"""Minimal heritable cell-population substrate with p53-gated fate and selection.

This is the "not-a-mirror" increment of the cancer roadmap: transformation
(clonal dominance) must **emerge** from the substrate, never be coded. There is
no rule anywhere that says "stress > threshold -> cancer"; there is only

  1. ONE hepatocyte fate law, instantiated N times. Per-cell differences live in
     STATE values, not in code -- heterogeneity is same-law/different-state,
     seeded from stochastic damage accrual and division partitioning
     (Elowitz & Swain 2002 intrinsic/extrinsic noise).
  2. The grounded p53 fate contract (population-scale reduction, see
     ``p53_dynamics.population_fate_from_damage``) deciding each cell's fate per
     generation: divide / arrest+repair / senescence / apoptosis, and -- for a
     checkpoint-null (p53-knockout) cell -- divide-with-unresolved-damage.
  3. A finite niche (carrying capacity + contact inhibition): cells that arrest,
     senesce or apoptose vacate the competition for division slots; the survivors
     that still divide fill the open slots by a neutral lottery.

From those ingredients alone, a rare checkpoint-null subclone expands to
dominance **only** under chronic genotoxic stress (wild-type cells arrest,
senesce or die while the null clone keeps dividing with its inherited damage);
without stress the same subclone stays neutral, and a pure wild-type population
under the same stress simply contracts. Clonal dominance is a *readout* of the
composition, not a driver: no cell is ever labelled "cancer".

HONESTY / firewall:
- ``is_reaction_transport_authority`` is always ``False``.
- Damage, stress and repair are normalised to the p53 contract's scale, NOT
  absolute DSB counts; the endogenous double-strand-break rate (Vilenchik &
  Knudson 2003) only anchors the *relative* chronic-vs-acute magnitude.
- Carrying capacity and the niche lottery are a minimal contact-inhibition
  abstraction, not a measured tissue geometry. "Generations" are damage-response
  cycles, not calendar time (hepatocytes are largely quiescent in homeostasis).
- Checkpoint loss enabling expansion under damage is known biology
  (Kastenhuber & Lowe 2017; Hanahan & Weinberg 2011); this module demonstrates
  the dynamic, it is not a validated tumourigenesis predictor.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from cell_engine.core.provenance import SourceReference
from cell_engine.core.random import EngineRng
from cell_engine.core.serialization import to_plain
from cell_engine.quantitative.p53_dynamics import (
    REPAIR_CAPACITY,
    population_fate_from_damage,
)

DATE_VERIFIED = "2026-08-05"
VERSION = "cell_population_emergent_selection_v1"

# --- population / selection parameters (normalised; disclosed abstractions) ---
DEFAULT_INITIAL_CELLS = 200
DEFAULT_CARRYING_CAPACITY = 400
DEFAULT_GENERATIONS = 40
DEFAULT_INITIAL_NULL_FRACTION = 0.02   # rare checkpoint-null founder subclone
REPAIR_PER_GENERATION = 0.55           # fraction of damage a p53-competent
#                                        arrested cell clears per generation
STRESS_RELATIVE_SIGMA = 0.4            # cell-to-cell variability in accrued damage
DIVISION_PARTITION_NOISE = 0.15        # heritable damage-partitioning noise
# Emergence readout thresholds (disclosed; they classify the outcome, not drive it)
TRANSFORMATION_FRACTION_GAIN = 0.2
TRANSFORMATION_MAJORITY = 0.5

CELL_POPULATION_SOURCES: dict[str, SourceReference] = {
    "vilenchik_knudson2003_endogenous_dsb": SourceReference(
        id="vilenchik_knudson2003_endogenous_dsb",
        title="Endogenous DNA double-strand breaks: production, fidelity of repair, and induction of cancer",
        url="https://doi.org/10.1073/pnas.2135498100",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Estimates ~50 endogenous DSBs per cell per day, the great majority faithfully "
            "repaired; anchors the relative magnitude of chronic vs acute genotoxic stress. "
            "Not a hepatocyte-specific rate; used only to scale normalised damage."
        ),
    ),
    "elowitz_swain2002_intrinsic_extrinsic_noise": SourceReference(
        id="elowitz_swain2002_intrinsic_extrinsic_noise",
        title="Stochastic gene expression in a single cell",
        url="https://doi.org/10.1126/science.1070919",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Intrinsic/extrinsic noise decomposition: identical genotypes diverge in state. "
            "Grounds the same-law/different-state basis for population heterogeneity here."
        ),
    ),
    "kastenhuber_lowe2017_p53_in_context": SourceReference(
        id="kastenhuber_lowe2017_p53_in_context",
        title="Putting p53 in Context",
        url="https://doi.org/10.1016/j.cell.2017.08.028",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes=(
            "Review: loss of p53 checkpoint function permits survival and proliferation of "
            "damaged cells, enabling clonal expansion under stress. Context for the emergent readout."
        ),
    ),
    "hanahan_weinberg2011_hallmarks": SourceReference(
        id="hanahan_weinberg2011_hallmarks",
        title="Hallmarks of cancer: the next generation",
        url="https://doi.org/10.1016/j.cell.2011.02.013",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes=(
            "Evading growth suppressors and replicative immortality as acquired capabilities; "
            "framing for why a checkpoint-null clone can outcompete under selection."
        ),
    ),
}


@dataclass(frozen=True)
class CellAgent:
    cell_id: int
    p53_functional: bool      # heritable checkpoint competence
    dna_damage: float         # normalised, on the p53 contract's damage scale
    generation: int
    consecutive_arrests: int
    senescent: bool


@dataclass(frozen=True)
class PopulationGeneration:
    generation: int
    alive: int
    cycling: int
    senescent: int
    checkpoint_null_fraction: float
    mean_damage: float
    divisions: int
    apoptoses: int
    new_senescent: int


@dataclass(frozen=True)
class CellPopulationOutcome:
    version: str
    is_reaction_transport_authority: bool
    scenario: str
    seed: int
    generations: int
    carrying_capacity: int
    genotoxic_stress_per_generation: float
    initial_checkpoint_null_fraction: float
    final_checkpoint_null_fraction: float
    final_alive: int
    generations_to_null_majority: int | None
    transformation_emerged: bool
    checkpoint_null_fraction_series: tuple[float, ...]
    alive_series: tuple[int, ...]
    mean_damage_series: tuple[float, ...]
    timeline: tuple[PopulationGeneration, ...]
    honesty_status: str
    grounded: tuple[str, ...]
    not_grounded: tuple[str, ...]
    blockers: tuple[str, ...]
    source_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def simulate_cell_population(
    *,
    scenario: str = "",
    n_initial: int = DEFAULT_INITIAL_CELLS,
    initial_null_fraction: float = DEFAULT_INITIAL_NULL_FRACTION,
    genotoxic_stress_per_generation: float = 0.0,
    carrying_capacity: int = DEFAULT_CARRYING_CAPACITY,
    generations: int = DEFAULT_GENERATIONS,
    seed: int = 0,
) -> CellPopulationOutcome:
    """Evolve a heritable cell population under the p53-gated fate law and a
    finite niche. Deterministic for a given seed (uses :class:`EngineRng`)."""
    if n_initial <= 0 or carrying_capacity <= 0 or generations <= 0:
        raise ValueError("n_initial, carrying_capacity and generations must be positive")

    rng = EngineRng(seed)
    n_null0 = round(n_initial * initial_null_fraction)
    cells: list[CellAgent] = [
        CellAgent(
            cell_id=i,
            p53_functional=(i >= n_null0),
            dna_damage=0.0,
            generation=0,
            consecutive_arrests=0,
            senescent=False,
        )
        for i in range(n_initial)
    ]
    next_id = n_initial

    initial_null_frac = _null_fraction(cells)
    timeline: list[PopulationGeneration] = []
    null_series: list[float] = []
    alive_series: list[int] = []
    damage_series: list[float] = []
    generations_to_majority: int | None = None

    for gen in range(1, generations + 1):
        survivors: list[CellAgent] = []
        dividers: list[CellAgent] = []
        apoptoses = 0
        new_senescent = 0

        for cell in cells:
            damage = cell.dna_damage
            if genotoxic_stress_per_generation > 0.0:
                damage = max(
                    0.0,
                    damage
                    + max(
                        0.0,
                        rng.gauss(
                            genotoxic_stress_per_generation,
                            genotoxic_stress_per_generation * STRESS_RELATIVE_SIGMA,
                        ),
                    ),
                )
            if cell.senescent:
                # Senescent cells never divide, but they are not immortal: under
                # continued genotoxic stress their damage still accrues and a
                # sufficiently damaged senescent cell undergoes secondary
                # apoptosis, vacating the niche. No immune clearance is modelled.
                if damage > REPAIR_CAPACITY:
                    apoptoses += 1
                    continue
                survivors.append(replace(cell, dna_damage=damage))
                continue
            fate = population_fate_from_damage(
                damage,
                p53_functional=cell.p53_functional,
                consecutive_arrests=cell.consecutive_arrests,
            )
            if fate == "apoptosis":
                apoptoses += 1
                continue
            if fate == "senescence":
                new_senescent += 1
                survivors.append(replace(cell, dna_damage=damage, senescent=True))
                continue
            if fate == "arrest_and_repair":
                survivors.append(
                    replace(
                        cell,
                        dna_damage=damage * (1.0 - REPAIR_PER_GENERATION),
                        consecutive_arrests=cell.consecutive_arrests + 1,
                    )
                )
                continue
            # "divide" or "divide_with_unresolved_damage"
            survivors.append(replace(cell, dna_damage=damage, consecutive_arrests=0))
            dividers.append(replace(cell, dna_damage=damage))

        # Finite niche: contact inhibition caps the population. Cells that
        # arrested / senesced / died are not in `dividers`, so they cede slots.
        open_slots = max(0, carrying_capacity - len(survivors))
        if len(dividers) > open_slots:
            dividers = _neutral_lottery(dividers, open_slots, rng)

        offspring: list[CellAgent] = []
        for parent in dividers:
            daughter_damage = max(
                0.0,
                parent.dna_damage * (1.0 + rng.gauss(0.0, DIVISION_PARTITION_NOISE)),
            )
            offspring.append(
                CellAgent(
                    cell_id=next_id,
                    p53_functional=parent.p53_functional,  # heritable
                    dna_damage=daughter_damage,
                    generation=gen,
                    consecutive_arrests=0,
                    senescent=False,
                )
            )
            next_id += 1

        cells = survivors + offspring

        null_frac = _null_fraction(cells)
        alive = len(cells)
        cycling = sum(1 for c in cells if not c.senescent)
        senescent = alive - cycling
        mean_damage = (sum(c.dna_damage for c in cells) / alive) if alive else 0.0
        timeline.append(
            PopulationGeneration(
                generation=gen,
                alive=alive,
                cycling=cycling,
                senescent=senescent,
                checkpoint_null_fraction=null_frac,
                mean_damage=mean_damage,
                divisions=len(dividers),
                apoptoses=apoptoses,
                new_senescent=new_senescent,
            )
        )
        null_series.append(null_frac)
        alive_series.append(alive)
        damage_series.append(mean_damage)
        if generations_to_majority is None and null_frac > TRANSFORMATION_MAJORITY:
            generations_to_majority = gen
        if alive == 0:
            break

    final_null = null_series[-1] if null_series else initial_null_frac
    transformation_emerged = (
        final_null - initial_null_frac >= TRANSFORMATION_FRACTION_GAIN
        and final_null > TRANSFORMATION_MAJORITY
    )
    return CellPopulationOutcome(
        version=VERSION,
        is_reaction_transport_authority=False,
        scenario=scenario or f"stress={genotoxic_stress_per_generation:g}",
        seed=seed,
        generations=generations,
        carrying_capacity=carrying_capacity,
        genotoxic_stress_per_generation=genotoxic_stress_per_generation,
        initial_checkpoint_null_fraction=initial_null_frac,
        final_checkpoint_null_fraction=final_null,
        final_alive=alive_series[-1] if alive_series else 0,
        generations_to_null_majority=generations_to_majority,
        transformation_emerged=transformation_emerged,
        checkpoint_null_fraction_series=tuple(null_series),
        alive_series=tuple(alive_series),
        mean_damage_series=tuple(damage_series),
        timeline=tuple(timeline),
        honesty_status=(
            "emergent_clonal_selection_from_one_fate_law_no_transformation_rule"
        ),
        grounded=(
            "one hepatocyte fate law instantiated N times; heterogeneity is same-law/different-state (Elowitz-Swain 2002)",
            "per-cell fate is the grounded p53 contract's population-scale reduction (see p53_dynamics)",
            "checkpoint loss enabling expansion of damaged cells under stress is known biology (Kastenhuber-Lowe 2017, Hanahan-Weinberg 2011)",
            "clonal dominance is a readout of composition; no cell is labelled 'cancer' and no stress->transformation rule exists",
        ),
        not_grounded=(
            "damage, stress and repair are normalised to the p53 contract's scale, not absolute DSB counts",
            "endogenous DSB rate (Vilenchik-Knudson 2003) only anchors relative chronic-vs-acute magnitude",
            "carrying capacity and the niche lottery are a minimal contact-inhibition abstraction, not measured tissue geometry",
            "generations are damage-response cycles, not calendar time",
        ),
        blockers=(
            "not a reaction-transport authority: sets no rate, diffusivity or concentration field",
            "a minimal population demonstrator, not a validated tumourigenesis predictor",
        ),
        source_ids=tuple(CELL_POPULATION_SOURCES),
    )


def _null_fraction(cells: list[CellAgent]) -> float:
    if not cells:
        return 0.0
    return sum(1 for c in cells if not c.p53_functional) / len(cells)


def _neutral_lottery(
    dividers: list[CellAgent], keep: int, rng: EngineRng
) -> list[CellAgent]:
    """Pick ``keep`` division slots by a neutral, deterministic lottery: the
    competition for space is unbiased -- any selective difference must come from
    *who is in the pool*, not from a rigged draw."""
    if keep <= 0:
        return []
    keyed = sorted(((rng.random(), i, c) for i, c in enumerate(dividers)))
    return [c for _, _, c in keyed[:keep]]


# Scenario panel exported in the engine snapshot: the neutral control, the
# emergent selection case, and the pure-wild-type control that cannot expand.
_SCENARIO_PANEL: tuple[tuple[str, float, float], ...] = (
    ("unstressed_neutral", 0.0, DEFAULT_INITIAL_NULL_FRACTION),
    ("chronic_stress_clonal_selection", 0.45, DEFAULT_INITIAL_NULL_FRACTION),
    ("chronic_stress_all_wildtype_control", 0.6, 0.0),
)


def build_cell_population(*, seed: int = 0) -> dict[str, CellPopulationOutcome]:
    return {
        name: simulate_cell_population(
            scenario=name,
            genotoxic_stress_per_generation=stress,
            initial_null_fraction=null0,
            seed=seed,
        )
        for name, stress, null0 in _SCENARIO_PANEL
    }


def cell_population_snapshot(*, seed: int = 0) -> dict[str, object]:
    return {name: outcome.to_dict() for name, outcome in build_cell_population(seed=seed).items()}
