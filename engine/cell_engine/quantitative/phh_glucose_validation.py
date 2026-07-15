"""Curated healthy-PHH spheroid glucose and insulin-response validation.

The primary observations remain attached to their 3D spheroid format, complete
media exposure bundle, time window and denominator.  Human hepatocellularity is
used only for an explicit organ-to-cell context calculation; neither surface is
allowed to initialize or alter the mechanistic cell automatically.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from math import isclose, isfinite
from pathlib import Path

from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain


DATE_VERIFIED = "2026-07-14"
VERSION = "healthy_phh_spheroid_glucose_validation_v1"
SCHEMA_VERSION = "cell.healthy-phh-glucose-validation.v1"
REVIEW_SCHEMA_VERSION = "cell.external-evidence-review.v1"
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = REPOSITORY_ROOT / "data" / "phh_baseline" / "curated" / "healthy_phh_glucose_validation.v1.json"
REVIEW_PATH = REPOSITORY_ROOT / "data" / "evidence_intake" / "reviews" / "2026-07-14_phh_signal_flux_review.v1.json"


PHH_GLUCOSE_VALIDATION_SOURCES: dict[str, SourceReference] = {
    "kemas2021_phh_glucose": SourceReference(
        id="kemas2021_phh_glucose",
        title="Insulin-dependent glucose consumption dynamics in 3D primary human liver cultures measured by a sensitive and specific glucose sensor with nanoliter input volume",
        url="https://faseb.onlinelibrary.wiley.com/doi/10.1096/fj.202001989RR",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Two-donor PHH 3D-spheroid study; Table 1 and the methods were reviewed directly. Validation-only outside the same culture format.",
    ),
    "honka2018_human_liver_glucose_uptake": SourceReference(
        id="honka2018_human_liver_glucose_uptake",
        title="Insulin-stimulated glucose uptake in skeletal muscle, adipose tissue and liver: a positron emission tomography study",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC5920018/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="18F-FDG PET plus euglycemic-hyperinsulinemic clamp in 326 participants without diabetes; whole-liver tissue denominator.",
    ),
    "wilson2003_human_hepatocellularity": SourceReference(
        id="wilson2003_human_hepatocellularity",
        title="Inter-individual variability in levels of human microsomal protein and hepatocellularity per gram of liver",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC1884378/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Human hepatocellularity and microsomal-protein scaling anchors corrected for processing loss; not a single-cell geometry study.",
    ),
}


@dataclass(frozen=True)
class PhhSpheroidStudyContext:
    species: str
    cell_format: str
    health_context: str
    provider: str
    study_wide_donor_count: int
    seeded_viable_cells_per_spheroid: int
    table_replicate_n: int
    table_replicate_semantics: str
    conditioning: str
    measurement: str
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class PhhExposureCondition:
    id: str
    label: str
    glucose_mM: float
    insulin_pM: float
    glucagon_nM: float | None
    glucagon_status: str


@dataclass(frozen=True)
class PhhGlucoseConsumptionObservation:
    id: str
    condition_id: str
    time_start_h: float
    time_end_h: float
    mean_fmol_per_cell_h: float
    sd_fmol_per_cell_h: float
    overlaps_subwindows: bool
    unit: str
    uncertainty_type: str
    replicate_n: int
    evidence: str
    source_locator: str
    may_validate_same_format_output: bool
    may_parameterize_fresh_phh_or_in_vivo_single_cell: bool
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class PhhInsulinResponseObservation:
    id: str
    pathway_id: str
    response: str
    direction: str
    reported_fold_change: float
    duration_min: float
    insulin_challenge_pM: float
    reported_n_results: int | None
    reported_n_figure_caption: int | None
    reported_n_range: tuple[int, int] | None
    uncertainty_value: float | None
    source_locator: str
    may_fit_quantitative_kinetics: bool
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class HumanScaleQuantity:
    geometric_mean: float
    low: float
    high: float
    sample_size: int
    unit: str


@dataclass(frozen=True)
class HumanHepatocellularityScaleBridge:
    hepatocytes_per_g_liver: HumanScaleQuantity
    microsomal_protein_per_g_liver: HumanScaleQuantity
    source_ids: tuple[str, ...]
    supports_single_hepatocyte_geometry: bool
    supports_direct_cell_state_initialization: bool


@dataclass(frozen=True)
class InVivoLiverUptakeContext:
    mean_umol_per_kg_liver_min: float
    sd_umol_per_kg_liver_min: float
    sample_size: int
    population: str
    protocol: str
    source_ids: tuple[str, ...]
    source_reported_derived_per_cell_mean_fmol_h: float
    source_reported_derived_per_cell_low_fmol_h: float
    source_reported_derived_per_cell_high_fmol_h: float
    source_reported_conversion_source_ids: tuple[str, ...]
    direct_per_cell_measurement: bool
    may_parameterize_single_cell: bool


@dataclass(frozen=True)
class ContextualOrganToCellConversion:
    mean_fmol_per_cell_h: float
    low_sensitivity_fmol_per_cell_h: float
    high_sensitivity_fmol_per_cell_h: float
    sensitivity_definition: str
    formula: str
    direct_measurement: bool
    may_drive_cell_state: bool
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class ExternalArtifactReview:
    file: str
    delivery_wave: str
    byte_size: int
    sha256: str
    review_status: str
    reason: str


@dataclass(frozen=True)
class ExternalEvidenceReview:
    review_id: str
    review_status: str
    contract_required_file_count: int
    contract_present_file_count: int
    missing_required_files: tuple[str, ...]
    raw_artifacts_redistributed: bool
    artifacts: tuple[ExternalArtifactReview, ...]
    review_findings: tuple[str, ...]


@dataclass(frozen=True)
class HealthyPhhGlucoseValidation:
    version: str
    status: str
    policy: str
    study_context: PhhSpheroidStudyContext
    conditions: tuple[PhhExposureCondition, ...]
    glucose_consumption_observations: tuple[PhhGlucoseConsumptionObservation, ...]
    insulin_response_observations: tuple[PhhInsulinResponseObservation, ...]
    observation_limitations: tuple[str, ...]
    human_scale_bridge: HumanHepatocellularityScaleBridge
    in_vivo_liver_uptake_context: InVivoLiverUptakeContext
    contextual_organ_to_cell_conversion: ContextualOrganToCellConversion
    corrections_to_supplied_tables: tuple[str, ...]
    evidence_review: ExternalEvidenceReview
    primary_source_review_complete: bool
    same_format_validation_ready: bool
    fresh_phh_parameterization_ready: bool
    endocrine_kinetic_fit_ready: bool
    exact_published_model_protocol_match: bool
    independent_heldout_human_result_count: int
    automatic_state_coupling: bool
    predictive_ready: bool
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain one JSON object")
    return payload


def _scale_quantity(payload: dict[str, object]) -> HumanScaleQuantity:
    return HumanScaleQuantity(
        geometric_mean=float(payload["geometric_mean"]),
        low=float(payload["low"]),
        high=float(payload["high"]),
        sample_size=int(payload["sample_size"]),
        unit=str(payload["unit"]),
    )


def _organ_rate_to_per_cell_fmol_h(rate_umol_per_kg_liver_min: float, hepatocytes_per_g_liver: float) -> float:
    cells_per_kg_liver = hepatocytes_per_g_liver * 1000.0
    return rate_umol_per_kg_liver_min * 60_000_000_000.0 / cells_per_kg_liver


def _load_review(payload: dict[str, object]) -> ExternalEvidenceReview:
    if payload.get("schema_version") != REVIEW_SCHEMA_VERSION:
        raise ValueError("unsupported external-evidence review schema")
    artifacts_payload = payload.get("artifacts")
    if not isinstance(artifacts_payload, list):
        raise ValueError("external-evidence artifacts are missing")
    artifacts = tuple(
        ExternalArtifactReview(
            file=str(item["file"]),
            delivery_wave=str(item["delivery_wave"]),
            byte_size=int(item["byte_size"]),
            sha256=str(item["sha256"]),
            review_status=str(item["review_status"]),
            reason=str(item["reason"]),
        )
        for item in artifacts_payload
        if isinstance(item, dict)
    )
    return ExternalEvidenceReview(
        review_id=str(payload["review_id"]),
        review_status=str(payload["review_status"]),
        contract_required_file_count=int(payload["contract_required_file_count"]),
        contract_present_file_count=int(payload["contract_present_file_count"]),
        missing_required_files=tuple(str(item) for item in payload["missing_required_files"]),  # type: ignore[index]
        raw_artifacts_redistributed=bool(payload["raw_artifacts_redistributed"]),
        artifacts=artifacts,
        review_findings=tuple(str(item) for item in payload["review_findings"]),  # type: ignore[index]
    )


def load_healthy_phh_glucose_validation(
    data_path: Path = DATA_PATH,
    review_path: Path = REVIEW_PATH,
) -> HealthyPhhGlucoseValidation:
    payload = _load_json(data_path)
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported healthy-PHH glucose validation schema")
    review = _load_review(_load_json(review_path))
    study_raw = payload["study_context"]
    if not isinstance(study_raw, dict):
        raise ValueError("PHH study context is malformed")
    study = PhhSpheroidStudyContext(
        species=str(study_raw["species"]),
        cell_format=str(study_raw["cell_format"]),
        health_context=str(study_raw["health_context"]),
        provider=str(study_raw["provider"]),
        study_wide_donor_count=int(study_raw["study_wide_donor_count"]),
        seeded_viable_cells_per_spheroid=int(study_raw["seeded_viable_cells_per_spheroid"]),
        table_replicate_n=int(study_raw["table_replicate_n"]),
        table_replicate_semantics=str(study_raw["table_replicate_semantics"]),
        conditioning=str(study_raw["conditioning"]),
        measurement=str(study_raw["measurement"]),
        source_ids=tuple(str(item) for item in study_raw["source_ids"]),  # type: ignore[index]
    )
    condition_payload = payload["conditions"]
    if not isinstance(condition_payload, list):
        raise ValueError("PHH exposure conditions are malformed")
    conditions = tuple(
        PhhExposureCondition(
            id=str(item["id"]),
            label=str(item["label"]),
            glucose_mM=float(item["glucose_mM"]),
            insulin_pM=float(item["insulin_pM"]),
            glucagon_nM=None if item["glucagon_nM"] is None else float(item["glucagon_nM"]),
            glucagon_status=str(item["glucagon_status"]),
        )
        for item in condition_payload
        if isinstance(item, dict)
    )
    contract = payload["observation_contract"]
    if not isinstance(contract, dict):
        raise ValueError("PHH observation contract is malformed")
    observation_payload = payload["glucose_consumption_observations"]
    if not isinstance(observation_payload, list):
        raise ValueError("PHH glucose observations are malformed")
    observations = tuple(
        PhhGlucoseConsumptionObservation(
            id=str(item["id"]),
            condition_id=str(item["condition_id"]),
            time_start_h=float(item["time_start_h"]),
            time_end_h=float(item["time_end_h"]),
            mean_fmol_per_cell_h=float(item["mean_fmol_per_cell_h"]),
            sd_fmol_per_cell_h=float(item["sd_fmol_per_cell_h"]),
            overlaps_subwindows=bool(item["overlaps_subwindows"]),
            unit=str(contract["unit"]),
            uncertainty_type=str(contract["uncertainty_type"]),
            replicate_n=study.table_replicate_n,
            evidence=str(contract["evidence"]),
            source_locator=str(contract["source_locator"]),
            may_validate_same_format_output=bool(contract["may_validate_same_format_output"]),
            may_parameterize_fresh_phh_or_in_vivo_single_cell=bool(contract["may_parameterize_fresh_phh_or_in_vivo_single_cell"]),
            source_ids=("kemas2021_phh_glucose",),
        )
        for item in observation_payload
        if isinstance(item, dict)
    )
    response_payload = payload["insulin_response_observations"]
    if not isinstance(response_payload, list):
        raise ValueError("PHH insulin responses are malformed")
    responses = tuple(
        PhhInsulinResponseObservation(
            id=str(item["id"]),
            pathway_id=str(item["pathway_id"]),
            response=str(item["response"]),
            direction=str(item["direction"]),
            reported_fold_change=float(item["reported_fold_change"]),
            duration_min=float(item["duration_min"]),
            insulin_challenge_pM=float(item["insulin_challenge_pM"]),
            reported_n_results=None if item.get("reported_n_results") is None else int(item["reported_n_results"]),
            reported_n_figure_caption=None if item.get("reported_n_figure_caption") is None else int(item["reported_n_figure_caption"]),
            reported_n_range=None if item.get("reported_n_range") is None else tuple(int(value) for value in item["reported_n_range"]),  # type: ignore[arg-type]
            uncertainty_value=None if item.get("uncertainty_value") is None else float(item["uncertainty_value"]),
            source_locator=str(item["source_locator"]),
            may_fit_quantitative_kinetics=bool(item["may_fit_quantitative_kinetics"]),
            source_ids=("kemas2021_phh_glucose",),
        )
        for item in response_payload
        if isinstance(item, dict)
    )
    scale_raw = payload["human_scale_bridge"]
    if not isinstance(scale_raw, dict) or not isinstance(scale_raw["hepatocytes_per_g_liver"], dict) or not isinstance(scale_raw["microsomal_protein_per_g_liver"], dict):
        raise ValueError("human scale bridge is malformed")
    scale_bridge = HumanHepatocellularityScaleBridge(
        hepatocytes_per_g_liver=_scale_quantity(scale_raw["hepatocytes_per_g_liver"]),
        microsomal_protein_per_g_liver=_scale_quantity(scale_raw["microsomal_protein_per_g_liver"]),
        source_ids=tuple(str(item) for item in scale_raw["source_ids"]),  # type: ignore[index]
        supports_single_hepatocyte_geometry=bool(scale_raw["supports_single_hepatocyte_geometry"]),
        supports_direct_cell_state_initialization=bool(scale_raw["supports_direct_cell_state_initialization"]),
    )
    uptake_raw = payload["in_vivo_liver_uptake_context"]
    if not isinstance(uptake_raw, dict):
        raise ValueError("in-vivo liver uptake context is malformed")
    uptake = InVivoLiverUptakeContext(
        mean_umol_per_kg_liver_min=float(uptake_raw["mean_umol_per_kg_liver_min"]),
        sd_umol_per_kg_liver_min=float(uptake_raw["sd_umol_per_kg_liver_min"]),
        sample_size=int(uptake_raw["sample_size"]),
        population=str(uptake_raw["population"]),
        protocol=str(uptake_raw["protocol"]),
        source_ids=tuple(str(item) for item in uptake_raw["source_ids"]),  # type: ignore[index]
        source_reported_derived_per_cell_mean_fmol_h=float(uptake_raw["source_reported_derived_per_cell_mean_fmol_h"]),
        source_reported_derived_per_cell_low_fmol_h=float(uptake_raw["source_reported_derived_per_cell_low_fmol_h"]),
        source_reported_derived_per_cell_high_fmol_h=float(uptake_raw["source_reported_derived_per_cell_high_fmol_h"]),
        source_reported_conversion_source_ids=tuple(str(item) for item in uptake_raw["source_reported_conversion_source_ids"]),  # type: ignore[index]
        direct_per_cell_measurement=bool(uptake_raw["direct_per_cell_measurement"]),
        may_parameterize_single_cell=bool(uptake_raw["may_parameterize_single_cell"]),
    )
    cell_anchor = scale_bridge.hepatocytes_per_g_liver
    conversion = ContextualOrganToCellConversion(
        mean_fmol_per_cell_h=_organ_rate_to_per_cell_fmol_h(uptake.mean_umol_per_kg_liver_min, cell_anchor.geometric_mean),
        low_sensitivity_fmol_per_cell_h=_organ_rate_to_per_cell_fmol_h(uptake.mean_umol_per_kg_liver_min - uptake.sd_umol_per_kg_liver_min, cell_anchor.high),
        high_sensitivity_fmol_per_cell_h=_organ_rate_to_per_cell_fmol_h(uptake.mean_umol_per_kg_liver_min + uptake.sd_umol_per_kg_liver_min, cell_anchor.low),
        sensitivity_definition="mean_plus_or_minus_one_reported_SD_crossed_with_observed_hepatocellularity_extremes_not_a_confidence_interval",
        formula="rate_umol_per_kg_liver_min * 1e9_fmol_per_umol * 60_min_per_h / (hepatocytes_per_g_liver * 1000_g_per_kg)",
        direct_measurement=False,
        may_drive_cell_state=False,
        source_ids=("honka2018_human_liver_glucose_uptake", "wilson2003_human_hepatocellularity"),
    )
    gates = payload["gates"]
    if not isinstance(gates, dict):
        raise ValueError("PHH glucose validation gates are malformed")
    state = HealthyPhhGlucoseValidation(
        version=VERSION,
        status=str(payload["status"]),
        policy=str(payload["policy"]),
        study_context=study,
        conditions=conditions,
        glucose_consumption_observations=observations,
        insulin_response_observations=responses,
        observation_limitations=tuple(str(item) for item in contract["limitations"]),  # type: ignore[index]
        human_scale_bridge=scale_bridge,
        in_vivo_liver_uptake_context=uptake,
        contextual_organ_to_cell_conversion=conversion,
        corrections_to_supplied_tables=tuple(str(item) for item in payload["corrections_to_supplied_tables"]),  # type: ignore[index]
        evidence_review=review,
        primary_source_review_complete=bool(gates["primary_source_review_complete"]),
        same_format_validation_ready=bool(gates["same_format_validation_ready"]),
        fresh_phh_parameterization_ready=bool(gates["fresh_phh_parameterization_ready"]),
        endocrine_kinetic_fit_ready=bool(gates["endocrine_kinetic_fit_ready"]),
        exact_published_model_protocol_match=bool(gates["exact_published_model_protocol_match"]),
        independent_heldout_human_result_count=int(gates["independent_heldout_human_result_count"]),
        automatic_state_coupling=bool(gates["automatic_state_coupling"]),
        predictive_ready=bool(gates["predictive_ready"]),
        source_ids=tuple(PHH_GLUCOSE_VALIDATION_SOURCES),
        limitations=(
            "The validation targets are PHH 3D-spheroid net-consumption windows, not fresh-suspension production fluxes.",
            "The exact exposure bundles include a glucagon difference, so high-versus-low insulin rows are not pure insulin interventions.",
            "The human organ-to-cell conversion is contextual and cannot be applied to a per-kg-body-mass model output without a matched liver-mass bridge.",
            "No exact-protocol model prediction or independent held-out human result is available.",
        ),
    )
    validate_healthy_phh_glucose_validation(state)
    return state


def validate_healthy_phh_glucose_validation(state: HealthyPhhGlucoseValidation) -> None:
    if state.version != VERSION or not state.primary_source_review_complete:
        raise ValueError("healthy-PHH glucose validation version or review status is invalid")
    source_ids = set(PHH_GLUCOSE_VALIDATION_SOURCES)
    if set(state.source_ids) != source_ids:
        raise ValueError("healthy-PHH glucose source registry is incomplete")
    study = state.study_context
    if (
        study.species != "Homo sapiens"
        or study.cell_format != "primary_human_hepatocyte_3d_spheroid"
        or study.study_wide_donor_count != 2
        or study.seeded_viable_cells_per_spheroid != 1500
        or study.table_replicate_n != 6
    ):
        raise ValueError("Kemas PHH study context changed")
    expected_conditions = {
        "hi_hg": (11.0, 1_700_000.0, None),
        "li_hg": (11.0, 100.0, 100.0),
        "hi_lg": (5.5, 1_700_000.0, None),
        "li_lg": (5.5, 100.0, 100.0),
    }
    conditions = {condition.id: condition for condition in state.conditions}
    if set(conditions) != set(expected_conditions):
        raise ValueError("Kemas exposure-condition matrix is incomplete")
    for condition_id, expected in expected_conditions.items():
        condition = conditions[condition_id]
        actual = (condition.glucose_mM, condition.insulin_pM, condition.glucagon_nM)
        if actual != expected:
            raise ValueError(f"Kemas condition {condition_id} no longer matches the primary source")
        if condition.glucose_mM == 25.0:
            raise ValueError("supplied 25 mM transcription error leaked into curated data")
        if condition.glucagon_nM is None and "unmeasured" not in condition.glucagon_status:
            raise ValueError("absence of supplemented glucagon was converted into a measured zero")
    observations = state.glucose_consumption_observations
    if len(observations) != 16 or len({item.id for item in observations}) != 16:
        raise ValueError("healthy insulin-sensitive Table 1 observation matrix is incomplete")
    expected_windows = {(0.0, 6.0), (6.0, 24.0), (24.0, 72.0), (0.0, 72.0)}
    observed_matrix = {(item.condition_id, item.time_start_h, item.time_end_h) for item in observations}
    expected_matrix = {(condition_id, start, end) for condition_id in conditions for start, end in expected_windows}
    if observed_matrix != expected_matrix:
        raise ValueError("PHH glucose time-window matrix changed")
    for item in observations:
        if not all(isfinite(value) for value in (item.time_start_h, item.time_end_h, item.mean_fmol_per_cell_h, item.sd_fmol_per_cell_h)):
            raise ValueError(f"PHH glucose observation {item.id} is non-finite")
        if item.time_end_h <= item.time_start_h or item.mean_fmol_per_cell_h < 0 or item.sd_fmol_per_cell_h <= 0:
            raise ValueError(f"PHH glucose observation {item.id} has invalid bounds")
        if item.overlaps_subwindows != (item.time_start_h == 0.0 and item.time_end_h == 72.0):
            raise ValueError(f"PHH glucose overlap semantics changed for {item.id}")
        if (
            item.unit != "fmol_per_cell_per_h"
            or item.uncertainty_type != "SD"
            or item.replicate_n != 6
            or item.may_parameterize_fresh_phh_or_in_vivo_single_cell
            or not item.may_validate_same_format_output
            or set(item.source_ids) != {"kemas2021_phh_glucose"}
        ):
            raise ValueError(f"PHH glucose authority contract changed for {item.id}")
    responses = {item.id: item for item in state.insulin_response_observations}
    if set(responses) != {"kemas_insulin_pakt_ser473_7min", "kemas_insulin_pck1_6h", "kemas_insulin_g6pc_6h"}:
        raise ValueError("PHH insulin-response chain is incomplete")
    pakt = responses["kemas_insulin_pakt_ser473_7min"]
    if (
        pakt.reported_fold_change != 3.5
        or pakt.duration_min != 7.0
        or pakt.reported_n_results != 4
        or pakt.reported_n_figure_caption != 3
    ):
        raise ValueError("pAKT response or its source-internal n discrepancy was lost")
    if any(item.may_fit_quantitative_kinetics or item.uncertainty_value is not None for item in responses.values()):
        raise ValueError("insufficient insulin-response data was promoted into a kinetic fit")
    scale = state.human_scale_bridge
    hpgl = scale.hepatocytes_per_g_liver
    mppgl = scale.microsomal_protein_per_g_liver
    if (
        (hpgl.geometric_mean, hpgl.low, hpgl.high, hpgl.sample_size, hpgl.unit)
        != (107_000_000.0, 65_000_000.0, 185_000_000.0, 7, "cells_per_g_liver")
        or (mppgl.geometric_mean, mppgl.low, mppgl.high, mppgl.sample_size)
        != (33.0, 26.0, 54.0, 20)
        or scale.supports_single_hepatocyte_geometry
        or scale.supports_direct_cell_state_initialization
    ):
        raise ValueError("Wilson human scale bridge changed or exceeded its evidence")
    uptake = state.in_vivo_liver_uptake_context
    if (
        (uptake.mean_umol_per_kg_liver_min, uptake.sd_umol_per_kg_liver_min, uptake.sample_size)
        != (22.4, 9.2, 326)
        or uptake.direct_per_cell_measurement
        or uptake.may_parameterize_single_cell
    ):
        raise ValueError("Honka liver-uptake context changed or was promoted to a direct per-cell measurement")
    conversion = state.contextual_organ_to_cell_conversion
    expected_conversion = (
        _organ_rate_to_per_cell_fmol_h(22.4, 107_000_000.0),
        _organ_rate_to_per_cell_fmol_h(22.4 - 9.2, 185_000_000.0),
        _organ_rate_to_per_cell_fmol_h(22.4 + 9.2, 65_000_000.0),
    )
    actual_conversion = (
        conversion.mean_fmol_per_cell_h,
        conversion.low_sensitivity_fmol_per_cell_h,
        conversion.high_sensitivity_fmol_per_cell_h,
    )
    if any(not isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12) for actual, expected in zip(actual_conversion, expected_conversion)):
        raise ValueError("organ-to-cell context conversion arithmetic changed")
    if conversion.direct_measurement or conversion.may_drive_cell_state:
        raise ValueError("derived organ-to-cell context cannot drive cell state")
    review = state.evidence_review
    if (
        review.contract_present_file_count != 7
        or review.contract_required_file_count != 9
        or set(review.missing_required_files) != {"human_phh_scale_bridge.csv", "koenig_model_provenance_audit.md"}
        or review.raw_artifacts_redistributed
        or len(review.artifacts) != 11
    ):
        raise ValueError("external research-bundle review is inconsistent")
    review_by_file = {item.file: item for item in review.artifacts}
    if "quarantined_model_predictions_not_heldout_validation" not in review_by_file["heldout_validation_trajectories.csv"].review_status:
        raise ValueError("model-only trajectory was not quarantined")
    if "quarantined_conflicts" not in review_by_file["integration_contract.json"].review_status:
        raise ValueError("conflicting external integration contract was not quarantined")
    if (
        not state.same_format_validation_ready
        or state.fresh_phh_parameterization_ready
        or state.endocrine_kinetic_fit_ready
        or state.exact_published_model_protocol_match
        or state.independent_heldout_human_result_count
        or state.automatic_state_coupling
        or state.predictive_ready
    ):
        raise ValueError("healthy-PHH validation gates exceeded the evidence")


def healthy_phh_glucose_validation_snapshot() -> dict[str, object]:
    state = load_healthy_phh_glucose_validation()
    payload = state.to_dict()
    payload["summary"] = {
        "measured_glucose_window_count": len(state.glucose_consumption_observations),
        "nonoverlapping_glucose_window_count": sum(not item.overlaps_subwindows for item in state.glucose_consumption_observations),
        "measured_insulin_response_count": len(state.insulin_response_observations),
        "same_format_validation_target_count": sum(item.may_validate_same_format_output for item in state.glucose_consumption_observations),
        "exact_protocol_model_prediction_count": 0,
        "independent_heldout_human_result_count": state.independent_heldout_human_result_count,
        "reviewed_contract_files": state.evidence_review.contract_present_file_count,
        "required_contract_files": state.evidence_review.contract_required_file_count,
        "quarantined_artifact_count": sum("quarantined" in item.review_status for item in state.evidence_review.artifacts),
        "correction_count": len(state.corrections_to_supplied_tables),
    }
    return payload

