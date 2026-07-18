"""PHH albumin-secretion observation operator and identifiability boundary.

The source assay reports one cumulative extracellular endpoint over 24 hours.
This module can convert an exact model trajectory into that observation space,
but it cannot infer translation or secretory-path kinetics from the endpoint.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from math import isclose, isfinite
from pathlib import Path
from typing import Literal

from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain
from cell_engine.quantitative.geometry import AVOGADRO


DATE_VERIFIED = "2026-07-14"
VERSION = "phh_albumin_secretion_v1"
SCHEMA_VERSION = "cell.phh-albumin-secretion.v1"
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "phh_baseline"
    / "curated"
    / "peng2025_phh_albumin_secretion.v1.json"
)
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


PHH_ALBUMIN_SECRETION_SOURCES: dict[str, SourceReference] = {
    "peng2025_phh_quality_attributes": SourceReference(
        id="peng2025_phh_quality_attributes",
        title="The validation of quality attributes in Primary Human Hepatocytes Standard",
        url="https://doi.org/10.1186/s13619-025-00258-6",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Primary study of commercial PHH batches. Six batches had secreted albumin measured "
            "by ELISA after 24 hours of regular 2D culture."
        ),
    ),
    "uniprot_p02768": SourceReference(
        id="uniprot_p02768",
        title="UniProtKB P02768: human albumin",
        url="https://www.uniprot.org/uniprotkb/P02768/entry",
        source_type="database",
        date_verified=DATE_VERIFIED,
        notes="Reviewed human ALB entry; canonical precursor is 609 residues and is processed to a mature form.",
    ),
    "usp_human_albumin_reference_standard": SourceReference(
        id="usp_human_albumin_reference_standard",
        title="USP rAlbumin Human reference standard",
        url="https://doi.usp.org/USPNF/USPNF_M2992_03_01.html",
        source_type="database",
        date_verified=DATE_VERIFIED,
        notes="Compendial reference reports the 585-residue mature albumin composition and 66,438 Da mass.",
    ),
    "peng2022_phh_requirements_standard": SourceReference(
        id="peng2022_phh_requirements_standard",
        title="Requirments for primary human hepatocyte",
        url="https://doi.org/10.1111/cpr.13147",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Published CSCB standard source for the >=800 ng/(10^6 cells x 24 h) PHH albumin criterion.",
    ),
}


QuantityClass = Literal["aggregate_output", "mechanistic_rate"]


@dataclass(frozen=True)
class AlbuminAssayContract:
    source_id: str
    species: str
    biological_system: str
    culture_format: str
    culture_duration_h: float
    measured_compartment: str
    analyte: str
    assay: str
    assay_kit: str
    normalization_denominator: str
    reported_unit: str
    source_formula: str
    denominator_caveat: str


@dataclass(frozen=True)
class AlbuminObservedBatchSpan:
    measured_batch_count: int
    individual_batch_table_loaded: bool
    low_batch_mean: float
    low_batch_sd: float
    high_batch_mean: float
    high_batch_sd: float
    unit: str
    scope: str


@dataclass(frozen=True)
class AlbuminBatchObservation:
    batch_id: str
    mean: float
    sd: float


@dataclass(frozen=True)
class AlbuminQualityCriterion:
    authority: str
    source_id: str
    threshold: float
    unit: str
    role: str
    may_be_used_as_model_pass_threshold: bool


@dataclass(frozen=True)
class AlbuminMolecularEntity:
    gene: str
    uniprot_accession: str
    canonical_precursor_length_aa: int
    mature_chain_length_aa: int
    mature_albumin_molar_mass_g_per_mol: float
    sequence_source_id: str
    mass_source_id: str


@dataclass(frozen=True)
class AlbuminProteomeContext:
    baseline_anchor_id: str
    expected_value: float
    unit: str
    sample_size: int
    source_id: str
    cohort_matched_to_secretion_assay: bool
    is_secretion_rate: bool


@dataclass(frozen=True)
class AlbuminReportedAssociation:
    id: str
    variables: str
    correlation_r: float | None
    p_value: float | None
    sample_size: int
    statistically_significant_as_reported: bool
    model_consequence: str


@dataclass(frozen=True)
class AlbuminMeasurementContract:
    input_quantity: str
    input_unit: str
    required_timepoints_h: tuple[float, ...]
    input_constraints: tuple[str, ...]
    output_quantity: str
    output_unit: str
    operator_formula: str


@dataclass(frozen=True)
class AlbuminQuantityIdentifiabilityAudit:
    id: str
    quantity_class: QuantityClass
    identified_from_current_assay: bool
    may_fit_kinetic_parameter: bool
    reason: str
    required_measurement_ids: tuple[str, ...]


@dataclass(frozen=True)
class AlbuminRequiredMeasurement:
    id: str
    label: str
    requirements: tuple[str, ...]
    purpose: str


@dataclass(frozen=True)
class PhhAlbuminSecretionState:
    version: str
    status: str
    date_verified: str
    assay_contract: AlbuminAssayContract
    observed_batch_span: AlbuminObservedBatchSpan
    batch_records: tuple[AlbuminBatchObservation, ...]
    quality_criterion: AlbuminQualityCriterion
    molecular_entity: AlbuminMolecularEntity
    proteome_context: AlbuminProteomeContext
    reported_associations: tuple[AlbuminReportedAssociation, ...]
    measurement_contract: AlbuminMeasurementContract
    quantity_audit: tuple[AlbuminQuantityIdentifiabilityAudit, ...]
    required_measurements: tuple[AlbuminRequiredMeasurement, ...]
    measurement_operator_ready: bool
    individual_batch_table_loaded: bool
    exact_model_trajectory_loaded: bool
    mechanistic_rate_fit_ready: bool
    automatic_state_coupling: bool
    model_pass_threshold_defined: bool
    predictive_ready: bool
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


@dataclass(frozen=True)
class AlbuminCumulativeModelPoint:
    time_h: float
    cumulative_secreted_mature_albumin_molecules_per_cell: float


@dataclass(frozen=True)
class AlbuminCumulativeModelTrajectory:
    trajectory_id: str
    model_id: str
    model_artifact_sha256: str
    measurement_contract_version: str
    species: str
    biological_system: str
    culture_format: str
    culture_duration_h: float
    denominator: str
    input_quantity: str
    input_unit: str
    points: tuple[AlbuminCumulativeModelPoint, ...]


@dataclass(frozen=True)
class AlbuminCumulativeInputAudit:
    measurement_contract_match: bool
    biological_system_match: bool
    denominator_match: bool
    point_matrix_match: bool
    initial_value_zero: bool
    values_finite_nonnegative: bool
    cumulative_output_nondecreasing: bool
    artifact_provenance_present: bool
    exact_input_match: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class AlbuminMeasurementProjection:
    status: str
    input_audit: AlbuminCumulativeInputAudit
    secreted_molecules_per_cell_24h: float
    secreted_molecules_per_cell_s: float
    albumin_ng_per_24h_per_1e6_cells: float
    observed_batch_mean_span_classification: str
    fitted_parameter_count: int
    pass_fail_assigned: bool
    may_drive_cell_state: bool

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain one JSON object")
    return payload


def _optional_float(value: object) -> float | None:
    return None if value is None else float(value)


def build_phh_albumin_secretion(data_path: Path = DATA_PATH) -> PhhAlbuminSecretionState:
    payload = _load_json(data_path)
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported PHH albumin-secretion schema")
    assay_raw = payload["assay_contract"]
    span_raw = payload["observed_batch_span"]
    criterion_raw = payload["quality_criterion"]
    entity_raw = payload["molecular_entity"]
    context_raw = payload["proteome_context"]
    measurement_raw = payload["measurement_contract"]
    gates = payload["gates"]
    if not all(
        isinstance(item, dict)
        for item in (assay_raw, span_raw, criterion_raw, entity_raw, context_raw, measurement_raw, gates)
    ):
        raise ValueError("PHH albumin-secretion payload is malformed")
    associations_raw = payload.get("reported_associations")
    batches_raw = payload.get("batch_records")
    quantities_raw = payload.get("quantity_audit")
    required_raw = payload.get("required_measurements")
    if not isinstance(associations_raw, list) or not isinstance(batches_raw, list) or not isinstance(quantities_raw, list) or not isinstance(required_raw, list):
        raise ValueError("PHH albumin-secretion list payload is malformed")

    state = PhhAlbuminSecretionState(
        version=VERSION,
        status=str(payload["status"]),
        date_verified=str(payload["date_verified"]),
        assay_contract=AlbuminAssayContract(
            source_id=str(assay_raw["source_id"]),
            species=str(assay_raw["species"]),
            biological_system=str(assay_raw["biological_system"]),
            culture_format=str(assay_raw["culture_format"]),
            culture_duration_h=float(assay_raw["culture_duration_h"]),
            measured_compartment=str(assay_raw["measured_compartment"]),
            analyte=str(assay_raw["analyte"]),
            assay=str(assay_raw["assay"]),
            assay_kit=str(assay_raw["assay_kit"]),
            normalization_denominator=str(assay_raw["normalization_denominator"]),
            reported_unit=str(assay_raw["reported_unit"]),
            source_formula=str(assay_raw["source_formula"]),
            denominator_caveat=str(assay_raw["denominator_caveat"]),
        ),
        observed_batch_span=AlbuminObservedBatchSpan(
            measured_batch_count=int(span_raw["measured_batch_count"]),
            individual_batch_table_loaded=bool(span_raw["individual_batch_table_loaded"]),
            low_batch_mean=float(span_raw["low_batch_mean"]),
            low_batch_sd=float(span_raw["low_batch_sd"]),
            high_batch_mean=float(span_raw["high_batch_mean"]),
            high_batch_sd=float(span_raw["high_batch_sd"]),
            unit=str(span_raw["unit"]),
            scope=str(span_raw["scope"]),
        ),
        batch_records=tuple(
            AlbuminBatchObservation(
                batch_id=str(item["batch_id"]),
                mean=float(item["mean"]),
                sd=float(item["sd"]),
            )
            for item in batches_raw
            if isinstance(item, dict)
        ),
        quality_criterion=AlbuminQualityCriterion(
            authority=str(criterion_raw["authority"]),
            source_id=str(criterion_raw["source_id"]),
            threshold=float(criterion_raw["threshold"]),
            unit=str(criterion_raw["unit"]),
            role=str(criterion_raw["role"]),
            may_be_used_as_model_pass_threshold=bool(criterion_raw["may_be_used_as_model_pass_threshold"]),
        ),
        molecular_entity=AlbuminMolecularEntity(
            gene=str(entity_raw["gene"]),
            uniprot_accession=str(entity_raw["uniprot_accession"]),
            canonical_precursor_length_aa=int(entity_raw["canonical_precursor_length_aa"]),
            mature_chain_length_aa=int(entity_raw["mature_chain_length_aa"]),
            mature_albumin_molar_mass_g_per_mol=float(entity_raw["mature_albumin_molar_mass_g_per_mol"]),
            sequence_source_id=str(entity_raw["sequence_source_id"]),
            mass_source_id=str(entity_raw["mass_source_id"]),
        ),
        proteome_context=AlbuminProteomeContext(
            baseline_anchor_id=str(context_raw["baseline_anchor_id"]),
            expected_value=float(context_raw["expected_value"]),
            unit=str(context_raw["unit"]),
            sample_size=int(context_raw["sample_size"]),
            source_id=str(context_raw["source_id"]),
            cohort_matched_to_secretion_assay=bool(context_raw["cohort_matched_to_secretion_assay"]),
            is_secretion_rate=bool(context_raw["is_secretion_rate"]),
        ),
        reported_associations=tuple(
            AlbuminReportedAssociation(
                id=str(item["id"]),
                variables=str(item["variables"]),
                correlation_r=_optional_float(item["correlation_r"]),
                p_value=_optional_float(item["p_value"]),
                sample_size=int(item["sample_size"]),
                statistically_significant_as_reported=bool(item["statistically_significant_as_reported"]),
                model_consequence=str(item["model_consequence"]),
            )
            for item in associations_raw
            if isinstance(item, dict)
        ),
        measurement_contract=AlbuminMeasurementContract(
            input_quantity=str(measurement_raw["input_quantity"]),
            input_unit=str(measurement_raw["input_unit"]),
            required_timepoints_h=tuple(float(item) for item in measurement_raw["required_timepoints_h"]),  # type: ignore[index]
            input_constraints=tuple(str(item) for item in measurement_raw["input_constraints"]),  # type: ignore[index]
            output_quantity=str(measurement_raw["output_quantity"]),
            output_unit=str(measurement_raw["output_unit"]),
            operator_formula=str(measurement_raw["operator_formula"]),
        ),
        quantity_audit=tuple(
            AlbuminQuantityIdentifiabilityAudit(
                id=str(item["id"]),
                quantity_class=str(item["quantity_class"]),  # type: ignore[arg-type]
                identified_from_current_assay=bool(item["identified_from_current_assay"]),
                may_fit_kinetic_parameter=bool(item["may_fit_kinetic_parameter"]),
                reason=str(item["reason"]),
                required_measurement_ids=tuple(str(value) for value in item["required_measurement_ids"]),  # type: ignore[index]
            )
            for item in quantities_raw
            if isinstance(item, dict)
        ),
        required_measurements=tuple(
            AlbuminRequiredMeasurement(
                id=str(item["id"]),
                label=str(item["label"]),
                requirements=tuple(str(value) for value in item["requirements"]),  # type: ignore[index]
                purpose=str(item["purpose"]),
            )
            for item in required_raw
            if isinstance(item, dict)
        ),
        measurement_operator_ready=bool(gates["measurement_operator_ready"]),
        individual_batch_table_loaded=bool(gates["individual_batch_table_loaded"]),
        exact_model_trajectory_loaded=bool(gates["exact_model_trajectory_loaded"]),
        mechanistic_rate_fit_ready=bool(gates["mechanistic_rate_fit_ready"]),
        automatic_state_coupling=bool(gates["automatic_state_coupling"]),
        model_pass_threshold_defined=bool(gates["model_pass_threshold_defined"]),
        predictive_ready=bool(gates["predictive_ready"]),
        source_ids=tuple(str(item) for item in payload["source_ids"]),  # type: ignore[index]
        limitations=tuple(str(item) for item in payload["limitations"]),  # type: ignore[index]
    )
    validate_phh_albumin_secretion(state)
    return state


def validate_phh_albumin_secretion(state: PhhAlbuminSecretionState) -> None:
    # Local import avoids a core -> quantitative -> validation package cycle at engine startup.
    from cell_engine.validation.phh_baseline import load_phh_baseline

    assay = state.assay_contract
    span = state.observed_batch_span
    criterion = state.quality_criterion
    entity = state.molecular_entity
    contract = state.measurement_contract
    if state.version != VERSION or state.date_verified != DATE_VERIFIED:
        raise ValueError("PHH albumin-secretion version or verification date changed")
    if (
        assay.source_id != "peng2025_phh_quality_attributes"
        or assay.species != "Homo sapiens"
        or assay.biological_system != "commercial_primary_human_hepatocytes"
        or assay.culture_format != "regular_2d_culture"
        or assay.culture_duration_h != 24.0
        or assay.measured_compartment != "culture_supernatant"
        or assay.analyte != "secreted_human_albumin"
        or assay.assay != "ELISA"
        or assay.assay_kit != "Bethyl Laboratories E88-129"
        or assay.normalization_denominator != "reported_phh_cell_number"
        or assay.reported_unit != "ng_per_24h_per_1e6_cells"
    ):
        raise ValueError("PHH albumin assay contract changed")
    if (
        span.measured_batch_count != 6
        or not span.individual_batch_table_loaded
        or span.unit != assay.reported_unit
        or not all(
            isfinite(value) and value >= 0.0
            for value in (span.low_batch_mean, span.low_batch_sd, span.high_batch_mean, span.high_batch_sd)
        )
        or span.low_batch_mean != 762.7
        or span.low_batch_sd != 174.1
        or span.high_batch_mean != 6957.7
        or span.high_batch_sd != 2440.5
        or span.high_batch_mean <= span.low_batch_mean
    ):
        raise ValueError("PHH albumin batch span changed or exceeded the published data")
    expected_batches = (
        ("PHH330", 762.7, 174.1),
        ("PHH409", 6957.7, 2440.5),
        ("PHH416", 4076.1, 422.5),
        ("PHH211", 2358.7, 742.6),
        ("PHH025", 4122.0, 955.2),
        ("PHH789", 2792.5, 774.9),
    )
    if tuple((item.batch_id, item.mean, item.sd) for item in state.batch_records) != expected_batches:
        raise ValueError("PHH albumin Table S3 batch records changed")
    if min(item.mean for item in state.batch_records) != span.low_batch_mean or max(
        item.mean for item in state.batch_records
    ) != span.high_batch_mean:
        raise ValueError("PHH albumin batch records no longer match the published span")
    if (
        criterion.authority != "T_CSCB_0008_2021_group_standard"
        or criterion.source_id != "peng2022_phh_requirements_standard"
        or criterion.threshold != 800.0
        or criterion.unit != assay.reported_unit
        or criterion.may_be_used_as_model_pass_threshold
    ):
        raise ValueError("PHH product-quality criterion was promoted to a model threshold")
    if (
        entity.gene != "ALB"
        or entity.uniprot_accession != "P02768"
        or entity.canonical_precursor_length_aa != 609
        or entity.mature_chain_length_aa != 585
        or entity.mature_albumin_molar_mass_g_per_mol != 66_438.0
        or entity.sequence_source_id != "uniprot_p02768"
        or entity.mass_source_id != "usp_human_albumin_reference_standard"
    ):
        raise ValueError("mature human albumin entity contract changed")

    baseline = load_phh_baseline()
    baseline_anchors = {item.id: item for item in baseline.anchors}
    anchor = baseline_anchors.get(state.proteome_context.baseline_anchor_id)
    if (
        anchor is None
        or anchor.measurement.value != state.proteome_context.expected_value
        or anchor.measurement.unit != state.proteome_context.unit
        or anchor.sample_size != state.proteome_context.sample_size
        or anchor.source_id != state.proteome_context.source_id
        or state.proteome_context.expected_value != 19_332_782.426021077
        or state.proteome_context.unit != "copies_per_nucleus"
        or state.proteome_context.cohort_matched_to_secretion_assay
        or state.proteome_context.is_secretion_rate
    ):
        raise ValueError("PHH albumin proteome context no longer matches the curated baseline")

    associations = {item.id: item for item in state.reported_associations}
    if set(associations) != {"alb_secretion_vs_alb_mrna", "alb_secretion_vs_cyp450_activity"}:
        raise ValueError("PHH albumin association set is incomplete")
    alb_mrna = associations["alb_secretion_vs_alb_mrna"]
    cyp = associations["alb_secretion_vs_cyp450_activity"]
    if (
        alb_mrna.correlation_r != 0.78
        or alb_mrna.p_value != 0.07
        or alb_mrna.sample_size != 6
        or alb_mrna.statistically_significant_as_reported
        or cyp.correlation_r is not None
        or cyp.p_value is not None
        or cyp.sample_size != 6
        or cyp.statistically_significant_as_reported
    ):
        raise ValueError("PHH albumin associations were promoted beyond the reported evidence")
    expected_constraints = (
        "cumulative_output_starts_at_zero",
        "cumulative_output_is_nonnegative_and_nondecreasing",
        "model_artifact_sha256_and_biological_context_are_present",
    )
    if (
        contract.input_quantity != "cumulative_secreted_mature_albumin"
        or contract.input_unit != "molecules_per_cell"
        or contract.required_timepoints_h != (0.0, 24.0)
        or contract.input_constraints != expected_constraints
        or contract.output_quantity != "albumin_secreted_over_24h"
        or contract.output_unit != assay.reported_unit
        or contract.operator_formula
        != "delta_molecules_per_cell_divided_by_avogadro_times_mature_albumin_g_per_mol_times_1e9_ng_per_g_times_1e6_cells"
    ):
        raise ValueError("PHH albumin measurement operator changed")

    expected_quantity_ids = {
        "cumulative_medium_albumin_24h",
        "albumin_translation_rate",
        "albumin_er_export_rate",
        "albumin_golgi_maturation_rate",
        "albumin_exocytosis_rate",
        "albumin_intracellular_degradation_rate",
    }
    if {item.id for item in state.quantity_audit} != expected_quantity_ids:
        raise ValueError("PHH albumin identifiability audit is incomplete")
    identified = tuple(item for item in state.quantity_audit if item.identified_from_current_assay)
    mechanistic = tuple(item for item in state.quantity_audit if item.quantity_class == "mechanistic_rate")
    if (
        len(identified) != 1
        or identified[0].id != "cumulative_medium_albumin_24h"
        or len(mechanistic) != 5
        or any(item.identified_from_current_assay or item.may_fit_kinetic_parameter for item in mechanistic)
    ):
        raise ValueError("PHH albumin endpoint was used to identify a hidden mechanism")
    expected_required_ids = {
        "donor_resolved_secretion_timecourse",
        "phh_compartment_resolved_pulse_chase",
        "matched_synthesis_and_mrna_timecourse",
        "intracellular_albumin_pool_timecourse",
        "matched_secretory_perturbation_timecourse",
    }
    required_ids = {item.id for item in state.required_measurements}
    if required_ids != expected_required_ids:
        raise ValueError("PHH albumin required-measurement set is incomplete")
    if any(not set(item.required_measurement_ids) <= required_ids for item in state.quantity_audit):
        raise ValueError("PHH albumin audit references an unknown required measurement")

    registered_sources = set(PHH_ALBUMIN_SECRETION_SOURCES) | set(baseline.sources)
    if set(state.source_ids) != {
        "peng2025_phh_quality_attributes",
        "peng2022_phh_requirements_standard",
        "human_hepatocyte_proteome_2016",
        "uniprot_p02768",
        "usp_human_albumin_reference_standard",
    } or not set(state.source_ids) <= registered_sources:
        raise ValueError("PHH albumin provenance changed")
    if (
        not state.measurement_operator_ready
        or not state.individual_batch_table_loaded
        or state.exact_model_trajectory_loaded
        or state.mechanistic_rate_fit_ready
        or state.automatic_state_coupling
        or state.model_pass_threshold_defined
        or state.predictive_ready
    ):
        raise ValueError("PHH albumin readiness gates exceeded the evidence")
    if len(state.limitations) < 5:
        raise ValueError("PHH albumin limitations are incomplete")


def mature_albumin_ng_per_1e6_cells(
    molecules_per_cell: float,
    *,
    molar_mass_g_per_mol: float = 66_438.0,
) -> float:
    if not isfinite(molecules_per_cell) or molecules_per_cell < 0.0:
        raise ValueError("albumin molecules per cell must be finite and non-negative")
    if not isfinite(molar_mass_g_per_mol) or molar_mass_g_per_mol <= 0.0:
        raise ValueError("albumin molar mass must be finite and positive")
    return molecules_per_cell / AVOGADRO * molar_mass_g_per_mol * 1.0e15


def mature_albumin_molecules_per_cell(
    ng_per_1e6_cells: float,
    *,
    molar_mass_g_per_mol: float = 66_438.0,
) -> float:
    if not isfinite(ng_per_1e6_cells) or ng_per_1e6_cells < 0.0:
        raise ValueError("albumin ng per million cells must be finite and non-negative")
    if not isfinite(molar_mass_g_per_mol) or molar_mass_g_per_mol <= 0.0:
        raise ValueError("albumin molar mass must be finite and positive")
    return ng_per_1e6_cells * AVOGADRO / (molar_mass_g_per_mol * 1.0e15)


def audit_albumin_cumulative_model_input(
    state: PhhAlbuminSecretionState,
    trajectory: AlbuminCumulativeModelTrajectory,
) -> AlbuminCumulativeInputAudit:
    validate_phh_albumin_secretion(state)
    assay = state.assay_contract
    contract = state.measurement_contract
    measurement_contract_match = (
        trajectory.measurement_contract_version == state.version
        and trajectory.input_quantity == contract.input_quantity
        and trajectory.input_unit == contract.input_unit
    )
    biological_system_match = (
        trajectory.species == assay.species
        and trajectory.biological_system == assay.biological_system
        and trajectory.culture_format == assay.culture_format
        and trajectory.culture_duration_h == assay.culture_duration_h
    )
    denominator_match = trajectory.denominator == assay.normalization_denominator
    actual_times = [point.time_h for point in trajectory.points]
    point_matrix_match = (
        len(actual_times) == len(set(actual_times))
        and tuple(sorted(actual_times)) == contract.required_timepoints_h
    )
    points = {point.time_h: point.cumulative_secreted_mature_albumin_molecules_per_cell for point in trajectory.points}
    initial_value_zero = point_matrix_match and isclose(points[0.0], 0.0, rel_tol=0.0, abs_tol=1e-12)
    values_finite_nonnegative = all(
        isfinite(point.time_h)
        and isfinite(point.cumulative_secreted_mature_albumin_molecules_per_cell)
        and point.cumulative_secreted_mature_albumin_molecules_per_cell >= 0.0
        for point in trajectory.points
    )
    cumulative_output_nondecreasing = point_matrix_match and points[24.0] >= points[0.0]
    artifact_provenance_present = bool(trajectory.trajectory_id and trajectory.model_id) and bool(
        SHA256_PATTERN.fullmatch(trajectory.model_artifact_sha256)
    )
    checks = {
        "measurement-contract version, input quantity or unit differs": measurement_contract_match,
        "species, PHH system, culture format or duration differs": biological_system_match,
        "cell-number denominator differs": denominator_match,
        "the exact 0-hour and 24-hour point matrix is incomplete or duplicated": point_matrix_match,
        "cumulative secretion does not start at zero": initial_value_zero,
        "one or more cumulative values is non-finite or negative": values_finite_nonnegative,
        "cumulative secretion decreases": cumulative_output_nondecreasing,
        "trajectory/model identifier or SHA-256 provenance is missing": artifact_provenance_present,
    }
    blockers = tuple(message for message, passed in checks.items() if not passed)
    return AlbuminCumulativeInputAudit(
        measurement_contract_match=measurement_contract_match,
        biological_system_match=biological_system_match,
        denominator_match=denominator_match,
        point_matrix_match=point_matrix_match,
        initial_value_zero=initial_value_zero,
        values_finite_nonnegative=values_finite_nonnegative,
        cumulative_output_nondecreasing=cumulative_output_nondecreasing,
        artifact_provenance_present=artifact_provenance_present,
        exact_input_match=not blockers,
        blockers=blockers,
    )


def project_cumulative_albumin_to_assay(
    state: PhhAlbuminSecretionState,
    trajectory: AlbuminCumulativeModelTrajectory,
) -> AlbuminMeasurementProjection:
    audit = audit_albumin_cumulative_model_input(state, trajectory)
    if not audit.exact_input_match:
        raise ValueError("cumulative albumin trajectory does not match the assay: " + "; ".join(audit.blockers))
    values = {
        point.time_h: point.cumulative_secreted_mature_albumin_molecules_per_cell
        for point in trajectory.points
    }
    delta = values[24.0] - values[0.0]
    output = mature_albumin_ng_per_1e6_cells(
        delta,
        molar_mass_g_per_mol=state.molecular_entity.mature_albumin_molar_mass_g_per_mol,
    )
    span = state.observed_batch_span
    if output < span.low_batch_mean:
        classification = "below_reported_batch_mean_span"
    elif output > span.high_batch_mean:
        classification = "above_reported_batch_mean_span"
    else:
        classification = "within_reported_batch_mean_span"
    return AlbuminMeasurementProjection(
        status="descriptive_projection_no_fit_no_pass_threshold",
        input_audit=audit,
        secreted_molecules_per_cell_24h=delta,
        secreted_molecules_per_cell_s=delta / (24.0 * 60.0 * 60.0),
        albumin_ng_per_24h_per_1e6_cells=output,
        observed_batch_mean_span_classification=classification,
        fitted_parameter_count=0,
        pass_fail_assigned=False,
        may_drive_cell_state=False,
    )


def phh_albumin_secretion_snapshot() -> dict[str, object]:
    state = build_phh_albumin_secretion()
    payload = state.to_dict()
    span = state.observed_batch_span
    molar_mass = state.molecular_entity.mature_albumin_molar_mass_g_per_mol
    low_molecules = mature_albumin_molecules_per_cell(span.low_batch_mean, molar_mass_g_per_mol=molar_mass)
    high_molecules = mature_albumin_molecules_per_cell(span.high_batch_mean, molar_mass_g_per_mol=molar_mass)
    mechanistic = tuple(item for item in state.quantity_audit if item.quantity_class == "mechanistic_rate")
    payload["summary"] = {
        "measured_batch_count": span.measured_batch_count,
        "published_numeric_endpoint_count": len(state.batch_records),
        "low_batch_mean_ng_per_24h_per_1e6_cells": span.low_batch_mean,
        "low_batch_sd_ng_per_24h_per_1e6_cells": span.low_batch_sd,
        "high_batch_mean_ng_per_24h_per_1e6_cells": span.high_batch_mean,
        "high_batch_sd_ng_per_24h_per_1e6_cells": span.high_batch_sd,
        "low_batch_mean_molecules_per_cell_24h": low_molecules,
        "high_batch_mean_molecules_per_cell_24h": high_molecules,
        "low_batch_mean_molecules_per_cell_s": low_molecules / (24.0 * 60.0 * 60.0),
        "high_batch_mean_molecules_per_cell_s": high_molecules / (24.0 * 60.0 * 60.0),
        "contextual_albumin_pool_copies_per_nucleus": state.proteome_context.expected_value,
        "mechanism_specific_rate_count": len(mechanistic),
        "mechanism_specific_rate_identified_count": sum(
            item.identified_from_current_assay for item in mechanistic
        ),
        "required_measurement_class_count": len(state.required_measurements),
        "individual_batch_numeric_record_count": len(state.batch_records),
        "exact_model_trajectory_count": int(state.exact_model_trajectory_loaded),
        "pass_fail_count": 0,
    }
    return payload
