"""Fail-closed cell-population kernel and PHH clonal-dynamics evidence contract.

The kernel can test inheritance, stochastic partitioning and finite-capacity
bookkeeping. It contains no built-in biological parameter set and publishes no
canonical cancer/transformation scenario. A caller must supply every numerical
assumption and declare a software-fixture or exploratory purpose.

This boundary matters because p53 loss alone is not an experimentally calibrated
healthy-PHH transformation law. Human liver studies establish spatial clonal
expansion, while a direct PHH transformation experiment required defined
combinations of oncogenic factors and an in-vivo host context. Those observations
define evidence requirements; they do not authorize a project-defined threshold.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from math import isfinite
from typing import Literal

from cell_engine.core.provenance import SourceReference
from cell_engine.core.random import EngineRng
from cell_engine.core.serialization import to_plain


DATE_VERIFIED = "2026-08-08"
VERSION = "cell_population_authority_v2"

CellPopulationPurpose = Literal[
    "software_fixture",
    "exploratory_candidate",
    "quantitative_validation",
    "predictive_execution",
    "authoritative_cell_state_coupling",
]


class CellPopulationAuthorityError(RuntimeError):
    """Raised when the uncalibrated population kernel is requested scientifically."""


CELL_POPULATION_SOURCES: dict[str, SourceReference] = {
    "brunner2019_somatic_liver_clones": SourceReference(
        id="brunner2019_somatic_liver_clones",
        title="Somatic mutations and clonal dynamics in healthy and cirrhotic human liver",
        url="https://doi.org/10.1038/s41586-019-1670-9",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Human liver sequencing and spatial clone evidence. It supports the "
            "existence of somatic selection, not this repository's numerical kernel."
        ),
    ),
    "braun2023_periportal_expansion": SourceReference(
        id="braun2023_periportal_expansion",
        title=(
            "Hepatocytes undergo punctuated expansion dynamics from a periportal "
            "stem cell niche in normal human liver"
        ),
        url="https://pubmed.ncbi.nlm.nih.gov/37088309/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Lineage, mitochondrial-sequence and spatial modelling evidence for "
            "human hepatocyte clonal expansion. It demonstrates that niche and "
            "geometry belong in a quantitative population model."
        ),
    ),
    "jiang2022_defined_phh_transformation": SourceReference(
        id="jiang2022_defined_phh_transformation",
        title=(
            "Transforming primary human hepatocytes into hepatocellular carcinoma "
            "with genetically defined factors"
        ),
        url="https://doi.org/10.15252/embr.202154275",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "PHHs from multiple donors were transformed in an immunodeficient-mouse "
            "liver context using defined oncogenic combinations. This does not "
            "support a p53-null-only or dimensionless stress-threshold rule."
        ),
    ),
}


@dataclass(frozen=True)
class CellPopulationCandidateParameters:
    """All numerical assumptions required by the non-authoritative kernel."""

    initial_cells: int
    initial_checkpoint_null_fraction: float
    carrying_capacity: int
    cycles: int
    stress_relative_sigma: float
    division_partition_noise: float
    repair_fraction_per_cycle: float
    division_safe_damage: float
    repair_capacity: float
    senescence_arrest_limit: int
    checkpoint_null_lethal_damage: float


@dataclass(frozen=True)
class CellAgent:
    cell_id: int
    checkpoint_functional: bool
    damage: float
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
    deaths: int
    new_senescent: int


@dataclass(frozen=True)
class CellPopulationCandidateOutcome:
    version: str
    purpose: str
    parameter_authority: str
    is_reaction_transport_authority: bool
    scenario: str
    seed: int
    cycles_requested: int
    carrying_capacity: int
    genotoxic_stress_per_cycle: float
    initial_checkpoint_null_fraction: float
    final_checkpoint_null_fraction: float
    final_alive: int
    checkpoint_null_majority_generation: int | None
    checkpoint_null_majority_reached: bool
    checkpoint_null_fraction_series: tuple[float, ...]
    alive_series: tuple[int, ...]
    mean_damage_series: tuple[float, ...]
    timeline: tuple[PopulationGeneration, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


@dataclass(frozen=True)
class CellPopulationAuthority:
    version: str
    status: str
    is_reaction_transport_authority: bool
    explicit_purpose_required: bool
    software_fixture_execution_allowed: bool
    exploratory_candidate_execution_allowed: bool
    quantitative_validation_allowed: bool
    predictive_execution_allowed: bool
    authoritative_cell_state_coupling_allowed: bool
    bundled_biological_parameter_set_count: int
    canonical_simulated_scenario_count: int
    canonical_transformation_claim_count: int
    healthy_phh_calibrated_population_parameter_count: int
    required_evidence: tuple[str, ...]
    blockers: tuple[str, ...]
    source_ids: tuple[str, ...]
    policy: str

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def build_cell_population() -> CellPopulationAuthority:
    authority = CellPopulationAuthority(
        version=VERSION,
        status="software_kernel_only_no_phh_population_execution",
        is_reaction_transport_authority=False,
        explicit_purpose_required=True,
        software_fixture_execution_allowed=True,
        exploratory_candidate_execution_allowed=True,
        quantitative_validation_allowed=False,
        predictive_execution_allowed=False,
        authoritative_cell_state_coupling_allowed=False,
        bundled_biological_parameter_set_count=0,
        canonical_simulated_scenario_count=0,
        canonical_transformation_claim_count=0,
        healthy_phh_calibrated_population_parameter_count=0,
        required_evidence=(
            "donor-resolved lineage or clone trajectories with genotype and ploidy",
            "injury, nutrient, zonation and tissue-niche context for every trajectory",
            "time-resolved proliferation, arrest, senescence, death and clearance observations",
            "spatial cell-neighbour and portal-central geometry with boundary conditions",
            "measurement-operator definitions and uncertainty for each readout",
            "donor-disjoint held-out validation and independent biological review",
        ),
        blockers=(
            "No matched healthy-PHH dataset identifies the kernel's population parameters.",
            "The p53 candidate itself has no healthy-PHH quantitative or fate authority.",
            "No bundled data map a checkpoint genotype to cycle-resolved PHH fate probabilities.",
            "No spatial niche, immune clearance or multicellular validation authorizes a transformation readout.",
        ),
        source_ids=tuple(CELL_POPULATION_SOURCES),
        policy=(
            "The generic kernel may be exercised with caller-supplied software-fixture "
            "or exploratory parameters. No built-in scenario, threshold or outcome may "
            "be presented as healthy-PHH clonal evolution or cancer prediction."
        ),
    )
    validate_cell_population_authority(authority)
    return authority


def validate_cell_population_authority(authority: CellPopulationAuthority) -> None:
    if (
        authority.version != VERSION
        or authority.status != "software_kernel_only_no_phh_population_execution"
        or not authority.explicit_purpose_required
    ):
        raise ValueError("cell-population authority identity changed")
    if (
        not authority.software_fixture_execution_allowed
        or not authority.exploratory_candidate_execution_allowed
        or authority.quantitative_validation_allowed
        or authority.predictive_execution_allowed
        or authority.authoritative_cell_state_coupling_allowed
    ):
        raise ValueError("cell-population kernel escaped its scientific-use firewall")
    if (
        authority.bundled_biological_parameter_set_count != 0
        or authority.canonical_simulated_scenario_count != 0
        or authority.canonical_transformation_claim_count != 0
        or authority.healthy_phh_calibrated_population_parameter_count != 0
        or not authority.blockers
    ):
        raise ValueError("cell-population evidence gate changed without validation")


def assert_cell_population_authority(
    purpose: CellPopulationPurpose,
) -> CellPopulationAuthority:
    authority = build_cell_population()
    allowed = {
        "software_fixture": authority.software_fixture_execution_allowed,
        "exploratory_candidate": authority.exploratory_candidate_execution_allowed,
        "quantitative_validation": authority.quantitative_validation_allowed,
        "predictive_execution": authority.predictive_execution_allowed,
        "authoritative_cell_state_coupling": (
            authority.authoritative_cell_state_coupling_allowed
        ),
    }
    if purpose not in allowed:
        raise ValueError(f"Unsupported cell-population purpose: {purpose}")
    if not allowed[purpose]:
        raise CellPopulationAuthorityError(
            f"{purpose} is blocked for the cell-population kernel: "
            + "; ".join(authority.blockers)
        )
    return authority


def validate_candidate_parameters(
    parameters: CellPopulationCandidateParameters,
) -> None:
    if (
        parameters.initial_cells <= 0
        or parameters.carrying_capacity <= 0
        or parameters.cycles <= 0
    ):
        raise ValueError("population sizes and cycles must be positive")
    if parameters.initial_cells > parameters.carrying_capacity:
        raise ValueError("initial_cells cannot exceed carrying_capacity")
    numeric_values = (
        parameters.initial_checkpoint_null_fraction,
        parameters.stress_relative_sigma,
        parameters.division_partition_noise,
        parameters.repair_fraction_per_cycle,
        parameters.division_safe_damage,
        parameters.repair_capacity,
        parameters.checkpoint_null_lethal_damage,
    )
    if any(not isfinite(value) for value in numeric_values):
        raise ValueError("cell-population candidate parameters must be finite")
    if not 0.0 <= parameters.initial_checkpoint_null_fraction <= 1.0:
        raise ValueError("initial checkpoint-null fraction must be within [0, 1]")
    if (
        parameters.stress_relative_sigma < 0.0
        or parameters.division_partition_noise < 0.0
    ):
        raise ValueError("noise terms must be non-negative")
    if not 0.0 <= parameters.repair_fraction_per_cycle <= 1.0:
        raise ValueError("repair fraction must be within [0, 1]")
    if (
        parameters.division_safe_damage < 0.0
        or parameters.repair_capacity <= parameters.division_safe_damage
        or parameters.checkpoint_null_lethal_damage <= parameters.repair_capacity
        or parameters.senescence_arrest_limit < 0
    ):
        raise ValueError("candidate fate boundaries must be ordered and non-negative")


def population_fate_from_damage(
    damage: float,
    *,
    checkpoint_functional: bool,
    consecutive_arrests: int,
    parameters: CellPopulationCandidateParameters,
    purpose: CellPopulationPurpose,
) -> str:
    """Evaluate the caller-supplied candidate fate ladder after authority checks."""

    assert_cell_population_authority(purpose)
    validate_candidate_parameters(parameters)
    return _candidate_population_fate(
        damage,
        checkpoint_functional=checkpoint_functional,
        consecutive_arrests=consecutive_arrests,
        parameters=parameters,
    )


def _candidate_population_fate(
    damage: float,
    *,
    checkpoint_functional: bool,
    consecutive_arrests: int,
    parameters: CellPopulationCandidateParameters,
) -> str:
    if not isfinite(damage) or damage < 0.0:
        raise ValueError("damage must be finite and non-negative")
    if not checkpoint_functional:
        if damage > parameters.checkpoint_null_lethal_damage:
            return "candidate_death"
        return "candidate_divide_with_unresolved_damage"
    if damage > parameters.repair_capacity:
        return "candidate_death"
    if damage < parameters.division_safe_damage:
        return "candidate_divide"
    if consecutive_arrests >= parameters.senescence_arrest_limit:
        return "candidate_senescence"
    return "candidate_arrest_and_repair"


def simulate_cell_population(
    *,
    purpose: CellPopulationPurpose,
    parameters: CellPopulationCandidateParameters,
    scenario: str,
    genotoxic_stress_per_cycle: float,
    seed: int,
) -> CellPopulationCandidateOutcome:
    """Exercise generic population bookkeeping with explicit candidate inputs."""

    assert_cell_population_authority(purpose)
    validate_candidate_parameters(parameters)
    if not scenario.strip():
        raise ValueError("scenario must be non-empty")
    if not isfinite(genotoxic_stress_per_cycle) or genotoxic_stress_per_cycle < 0.0:
        raise ValueError("genotoxic_stress_per_cycle must be finite and non-negative")

    rng = EngineRng(seed)
    n_null = round(
        parameters.initial_cells * parameters.initial_checkpoint_null_fraction
    )
    cells = [
        CellAgent(
            cell_id=index,
            checkpoint_functional=index >= n_null,
            damage=0.0,
            generation=0,
            consecutive_arrests=0,
            senescent=False,
        )
        for index in range(parameters.initial_cells)
    ]
    next_id = parameters.initial_cells
    initial_null_fraction = _null_fraction(cells)
    timeline: list[PopulationGeneration] = []
    null_series: list[float] = []
    alive_series: list[int] = []
    damage_series: list[float] = []
    majority_generation: int | None = None

    for generation in range(1, parameters.cycles + 1):
        survivors: list[CellAgent] = []
        dividers: list[CellAgent] = []
        deaths = 0
        new_senescent = 0

        for cell in cells:
            damage = cell.damage
            if genotoxic_stress_per_cycle > 0.0:
                damage += max(
                    0.0,
                    rng.gauss(
                        genotoxic_stress_per_cycle,
                        genotoxic_stress_per_cycle * parameters.stress_relative_sigma,
                    ),
                )
            if cell.senescent:
                if damage > parameters.repair_capacity:
                    deaths += 1
                    continue
                survivors.append(replace(cell, damage=damage))
                continue

            fate = _candidate_population_fate(
                damage,
                checkpoint_functional=cell.checkpoint_functional,
                consecutive_arrests=cell.consecutive_arrests,
                parameters=parameters,
            )
            if fate == "candidate_death":
                deaths += 1
                continue
            if fate == "candidate_senescence":
                new_senescent += 1
                survivors.append(replace(cell, damage=damage, senescent=True))
                continue
            if fate == "candidate_arrest_and_repair":
                survivors.append(
                    replace(
                        cell,
                        damage=damage * (1.0 - parameters.repair_fraction_per_cycle),
                        consecutive_arrests=cell.consecutive_arrests + 1,
                    )
                )
                continue
            survivor = replace(cell, damage=damage, consecutive_arrests=0)
            survivors.append(survivor)
            dividers.append(survivor)

        open_slots = max(0, parameters.carrying_capacity - len(survivors))
        if len(dividers) > open_slots:
            dividers = _neutral_lottery(dividers, open_slots, rng)

        offspring: list[CellAgent] = []
        for parent in dividers:
            daughter_damage = max(
                0.0,
                parent.damage
                * (1.0 + rng.gauss(0.0, parameters.division_partition_noise)),
            )
            offspring.append(
                CellAgent(
                    cell_id=next_id,
                    checkpoint_functional=parent.checkpoint_functional,
                    damage=daughter_damage,
                    generation=generation,
                    consecutive_arrests=0,
                    senescent=False,
                )
            )
            next_id += 1

        cells = survivors + offspring
        null_fraction = _null_fraction(cells)
        alive = len(cells)
        cycling = sum(not cell.senescent for cell in cells)
        senescent = alive - cycling
        mean_damage = sum(cell.damage for cell in cells) / alive if alive else 0.0
        timeline.append(
            PopulationGeneration(
                generation=generation,
                alive=alive,
                cycling=cycling,
                senescent=senescent,
                checkpoint_null_fraction=null_fraction,
                mean_damage=mean_damage,
                divisions=len(dividers),
                deaths=deaths,
                new_senescent=new_senescent,
            )
        )
        null_series.append(null_fraction)
        alive_series.append(alive)
        damage_series.append(mean_damage)
        if majority_generation is None and null_fraction > 0.5:
            majority_generation = generation
        if alive == 0:
            break

    return CellPopulationCandidateOutcome(
        version=VERSION,
        purpose=purpose,
        parameter_authority="caller_supplied_non_authoritative_candidate",
        is_reaction_transport_authority=False,
        scenario=scenario,
        seed=seed,
        cycles_requested=parameters.cycles,
        carrying_capacity=parameters.carrying_capacity,
        genotoxic_stress_per_cycle=genotoxic_stress_per_cycle,
        initial_checkpoint_null_fraction=initial_null_fraction,
        final_checkpoint_null_fraction=(
            null_series[-1] if null_series else initial_null_fraction
        ),
        final_alive=alive_series[-1] if alive_series else 0,
        checkpoint_null_majority_generation=majority_generation,
        checkpoint_null_majority_reached=majority_generation is not None,
        checkpoint_null_fraction_series=tuple(null_series),
        alive_series=tuple(alive_series),
        mean_damage_series=tuple(damage_series),
        timeline=tuple(timeline),
    )


def _null_fraction(cells: list[CellAgent]) -> float:
    if not cells:
        return 0.0
    return sum(not cell.checkpoint_functional for cell in cells) / len(cells)


def _neutral_lottery(
    dividers: list[CellAgent], keep: int, rng: EngineRng
) -> list[CellAgent]:
    if keep <= 0:
        return []
    keyed = sorted((rng.random(), index, cell) for index, cell in enumerate(dividers))
    return [cell for _, _, cell in keyed[:keep]]


def cell_population_snapshot() -> dict[str, object]:
    """Return only the authority contract; no invented scenario is executed."""

    return build_cell_population().to_dict()
