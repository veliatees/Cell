"""Exact-protocol validation harness for the Kemas 2021 PHH spheroids.

Only transformations identified by the primary paper are allowed.  The three
non-overlapping rate windows can be integrated into cumulative mean
disappearance per seeded cell.  Their uncertainty cannot be pooled because the
covariance/repeated-measures structure is not reported.  The overlapping 0-72 h
rows are therefore descriptive consistency audits, never extra independent
targets or an acceptance test.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from math import isclose, isfinite
from pathlib import Path

from cell_engine.core.serialization import to_plain
from cell_engine.quantitative.phh_glucose_validation import (
    PhhExposureCondition,
    load_healthy_phh_glucose_validation,
)


VERSION = "phh_spheroid_glucose_validation_protocol_v1"
SCHEMA_VERSION = "cell.phh-spheroid-validation-protocol.v1"
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = REPOSITORY_ROOT / "data" / "phh_baseline" / "curated" / "kemas2021_phh_spheroid_protocol.v1.json"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _stable_decimal(value: float) -> float:
    """Remove binary floating-point display noise without changing source precision."""
    return round(value, 12)


@dataclass(frozen=True)
class PhhSpheroidMethodContract:
    species: str
    cell_format: str
    plate_format: str
    seeded_viable_cells_per_well: int
    single_spheroid_observed_per_well_after_aggregation: bool
    culture_seeding_medium_volume_uL: float
    glucose_challenge_initial_medium_volume_uL: float | None
    assay_sample_supernatant_volume_uL: float
    assay_replication: str
    assay_replication_count: int
    remaining_medium_volume_schedule_uL: tuple[float, ...] | None
    volumetric_factor_VF: float | None
    viable_cell_count_at_each_observation_window: tuple[int, ...] | None
    reported_calculation: str
    reported_symbol_semantics: dict[str, str]


@dataclass(frozen=True)
class PhhSpheroidOutputContract:
    quantity: str
    positive_direction: str
    rate_unit: str
    cumulative_unit: str
    denominator: str
    uncertainty_type: str
    nonoverlapping_windows_h: tuple[tuple[float, float], ...]
    overlapping_audit_window_h: tuple[float, float]


@dataclass(frozen=True)
class PhhSpheroidWindowTarget:
    observation_id: str
    condition_id: str
    time_start_h: float
    time_end_h: float
    duration_h: float
    observed_mean_fmol_per_cell_h: float
    observed_sd_fmol_per_cell_h: float
    cumulative_mean_increment_fmol_per_seeded_cell: float
    cumulative_sd_increment_fmol_per_seeded_cell: float
    overlaps_subwindows: bool
    independent_trajectory_target: bool
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class PhhCumulativeTargetPoint:
    time_h: float
    cumulative_mean_fmol_per_seeded_cell: float
    cumulative_sd_fmol_per_seeded_cell: None
    source_window_ids: tuple[str, ...]
    origin_is_mathematical_definition: bool


@dataclass(frozen=True)
class PhhCumulativeTargetTrajectory:
    condition_id: str
    points: tuple[PhhCumulativeTargetPoint, ...]
    combined_cumulative_uncertainty_available: bool
    uncertainty_limitation: str


@dataclass(frozen=True)
class PhhOverlapConsistencyAudit:
    condition_id: str
    subwindow_observation_ids: tuple[str, ...]
    reported_overlap_observation_id: str
    derived_subwindow_cumulative_mean_fmol_per_seeded_cell: float
    reported_overlap_cumulative_mean_fmol_per_seeded_cell: float
    cumulative_residual_reported_minus_derived_fmol_per_seeded_cell: float
    derived_time_weighted_mean_fmol_per_cell_h: float
    reported_overlap_mean_fmol_per_cell_h: float
    rate_residual_reported_minus_derived_fmol_per_cell_h: float
    acceptance_threshold: None
    pass_fail_assigned: bool


@dataclass(frozen=True)
class PhhSpheroidValidationProtocol:
    version: str
    protocol_id: str
    status: str
    method_contract: PhhSpheroidMethodContract
    output_contract: PhhSpheroidOutputContract
    conditions: tuple[PhhExposureCondition, ...]
    window_targets: tuple[PhhSpheroidWindowTarget, ...]
    cumulative_target_trajectories: tuple[PhhCumulativeTargetTrajectory, ...]
    overlap_consistency_audits: tuple[PhhOverlapConsistencyAudit, ...]
    medium_concentration_trajectory_reconstruction_ready: bool
    cumulative_mean_trajectory_ready: bool
    combined_cumulative_uncertainty_ready: bool
    vectorial_flux_decomposition_ready: bool
    exact_protocol_prediction_loaded: bool
    acceptance_threshold: None
    automatic_state_coupling: bool
    predictive_ready: bool
    source_ids: tuple[str, ...]
    source_locators: tuple[str, ...]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


@dataclass(frozen=True)
class PhhSpheroidPredictionWindow:
    condition_id: str
    time_start_h: float
    time_end_h: float
    predicted_mean_fmol_per_cell_h: float


@dataclass(frozen=True)
class PhhSpheroidModelPrediction:
    prediction_set_id: str
    model_id: str
    model_artifact_sha256: str
    protocol_version: str
    species: str
    cell_format: str
    health_context: str
    seeded_viable_cells_per_spheroid: int
    denominator: str
    output_quantity: str
    positive_direction: str
    unit: str
    conditions: tuple[PhhExposureCondition, ...]
    windows: tuple[PhhSpheroidPredictionWindow, ...]


@dataclass(frozen=True)
class PhhPredictionProtocolMatchAudit:
    protocol_version_match: bool
    biological_system_match: bool
    denominator_match: bool
    output_contract_match: bool
    exposure_matrix_match: bool
    window_matrix_match: bool
    prediction_values_finite: bool
    artifact_provenance_present: bool
    exact_protocol_match: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class PhhPredictionResidual:
    observation_id: str
    condition_id: str
    time_start_h: float
    time_end_h: float
    observed_mean_fmol_per_cell_h: float
    observed_sd_fmol_per_cell_h: float
    predicted_mean_fmol_per_cell_h: float
    predicted_minus_observed_fmol_per_cell_h: float
    relative_residual: float | None
    sd_standardized_residual: float
    sd_interpretation: str
    independent_trajectory_target: bool
    pass_fail_assigned: bool


@dataclass(frozen=True)
class PhhSpheroidProtocolComparison:
    prediction_set_id: str
    status: str
    match_audit: PhhPredictionProtocolMatchAudit
    residuals: tuple[PhhPredictionResidual, ...]
    aggregate_score: None
    acceptance_threshold: None
    pass_fail_assigned: bool
    may_drive_cell_state: bool

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain one JSON object")
    return payload


def _optional_float_tuple(value: object) -> tuple[float, ...] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError("optional numeric schedule must be a list or null")
    return tuple(float(item) for item in value)


def _optional_int_tuple(value: object) -> tuple[int, ...] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError("optional cell-count schedule must be a list or null")
    return tuple(int(item) for item in value)


def _build_trajectories(
    conditions: tuple[PhhExposureCondition, ...],
    targets: tuple[PhhSpheroidWindowTarget, ...],
) -> tuple[PhhCumulativeTargetTrajectory, ...]:
    trajectories: list[PhhCumulativeTargetTrajectory] = []
    for condition in conditions:
        windows = sorted(
            (
                target
                for target in targets
                if target.condition_id == condition.id and target.independent_trajectory_target
            ),
            key=lambda target: target.time_start_h,
        )
        cumulative = 0.0
        source_window_ids: list[str] = []
        points = [
            PhhCumulativeTargetPoint(
                time_h=0.0,
                cumulative_mean_fmol_per_seeded_cell=0.0,
                cumulative_sd_fmol_per_seeded_cell=None,
                source_window_ids=(),
                origin_is_mathematical_definition=True,
            )
        ]
        for window in windows:
            cumulative = _stable_decimal(cumulative + window.cumulative_mean_increment_fmol_per_seeded_cell)
            source_window_ids.append(window.observation_id)
            points.append(
                PhhCumulativeTargetPoint(
                    time_h=window.time_end_h,
                    cumulative_mean_fmol_per_seeded_cell=cumulative,
                    cumulative_sd_fmol_per_seeded_cell=None,
                    source_window_ids=tuple(source_window_ids),
                    origin_is_mathematical_definition=False,
                )
            )
        trajectories.append(
            PhhCumulativeTargetTrajectory(
                condition_id=condition.id,
                points=tuple(points),
                combined_cumulative_uncertainty_available=False,
                uncertainty_limitation=(
                    "Window SDs are retained separately; covariance and repeated-measures structure are not reported, "
                    "so no cumulative SD is calculated."
                ),
            )
        )
    return tuple(trajectories)


def _build_overlap_audits(
    conditions: tuple[PhhExposureCondition, ...],
    targets: tuple[PhhSpheroidWindowTarget, ...],
) -> tuple[PhhOverlapConsistencyAudit, ...]:
    audits: list[PhhOverlapConsistencyAudit] = []
    for condition in conditions:
        subwindows = sorted(
            (
                target
                for target in targets
                if target.condition_id == condition.id and target.independent_trajectory_target
            ),
            key=lambda target: target.time_start_h,
        )
        overlaps = [
            target
            for target in targets
            if target.condition_id == condition.id and target.overlaps_subwindows
        ]
        if len(overlaps) != 1:
            raise ValueError(f"condition {condition.id} must have one overlapping 0-72 h observation")
        overlap = overlaps[0]
        total_duration = sum(window.duration_h for window in subwindows)
        derived_cumulative = _stable_decimal(sum(window.cumulative_mean_increment_fmol_per_seeded_cell for window in subwindows))
        reported_cumulative = _stable_decimal(overlap.cumulative_mean_increment_fmol_per_seeded_cell)
        derived_rate = _stable_decimal(derived_cumulative / total_duration)
        audits.append(
            PhhOverlapConsistencyAudit(
                condition_id=condition.id,
                subwindow_observation_ids=tuple(window.observation_id for window in subwindows),
                reported_overlap_observation_id=overlap.observation_id,
                derived_subwindow_cumulative_mean_fmol_per_seeded_cell=derived_cumulative,
                reported_overlap_cumulative_mean_fmol_per_seeded_cell=reported_cumulative,
                cumulative_residual_reported_minus_derived_fmol_per_seeded_cell=_stable_decimal(reported_cumulative - derived_cumulative),
                derived_time_weighted_mean_fmol_per_cell_h=derived_rate,
                reported_overlap_mean_fmol_per_cell_h=overlap.observed_mean_fmol_per_cell_h,
                rate_residual_reported_minus_derived_fmol_per_cell_h=_stable_decimal(overlap.observed_mean_fmol_per_cell_h - derived_rate),
                acceptance_threshold=None,
                pass_fail_assigned=False,
            )
        )
    return tuple(audits)


def build_phh_spheroid_validation_protocol(
    data_path: Path = DATA_PATH,
) -> PhhSpheroidValidationProtocol:
    payload = _load_json(data_path)
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported PHH spheroid protocol schema")
    curated = load_healthy_phh_glucose_validation()
    method_raw = payload.get("method_contract")
    output_raw = payload.get("output_contract")
    gates = payload.get("gates")
    if not isinstance(method_raw, dict) or not isinstance(output_raw, dict) or not isinstance(gates, dict):
        raise ValueError("PHH spheroid protocol contract is malformed")
    symbol_semantics = method_raw.get("reported_symbol_semantics")
    if not isinstance(symbol_semantics, dict):
        raise ValueError("reported formula symbol semantics are missing")
    method = PhhSpheroidMethodContract(
        species=str(method_raw["species"]),
        cell_format=str(method_raw["cell_format"]),
        plate_format=str(method_raw["plate_format"]),
        seeded_viable_cells_per_well=int(method_raw["seeded_viable_cells_per_well"]),
        single_spheroid_observed_per_well_after_aggregation=bool(method_raw["single_spheroid_observed_per_well_after_aggregation"]),
        culture_seeding_medium_volume_uL=float(method_raw["culture_seeding_medium_volume_uL"]),
        glucose_challenge_initial_medium_volume_uL=(
            None
            if method_raw["glucose_challenge_initial_medium_volume_uL"] is None
            else float(method_raw["glucose_challenge_initial_medium_volume_uL"])
        ),
        assay_sample_supernatant_volume_uL=float(method_raw["assay_sample_supernatant_volume_uL"]),
        assay_replication=str(method_raw["assay_replication"]),
        assay_replication_count=int(method_raw["assay_replication_count"]),
        remaining_medium_volume_schedule_uL=_optional_float_tuple(method_raw["remaining_medium_volume_schedule_uL"]),
        volumetric_factor_VF=None if method_raw["volumetric_factor_VF"] is None else float(method_raw["volumetric_factor_VF"]),
        viable_cell_count_at_each_observation_window=_optional_int_tuple(method_raw["viable_cell_count_at_each_observation_window"]),
        reported_calculation=str(method_raw["reported_calculation"]),
        reported_symbol_semantics={str(key): str(value) for key, value in symbol_semantics.items()},
    )
    nonoverlap_raw = output_raw.get("nonoverlapping_windows_h")
    overlap_raw = output_raw.get("overlapping_audit_window_h")
    if not isinstance(nonoverlap_raw, list) or not isinstance(overlap_raw, list):
        raise ValueError("PHH spheroid window contract is malformed")
    output = PhhSpheroidOutputContract(
        quantity=str(output_raw["quantity"]),
        positive_direction=str(output_raw["positive_direction"]),
        rate_unit=str(output_raw["rate_unit"]),
        cumulative_unit=str(output_raw["cumulative_unit"]),
        denominator=str(output_raw["denominator"]),
        uncertainty_type=str(output_raw["uncertainty_type"]),
        nonoverlapping_windows_h=tuple((float(item[0]), float(item[1])) for item in nonoverlap_raw),
        overlapping_audit_window_h=(float(overlap_raw[0]), float(overlap_raw[1])),
    )
    targets = tuple(
        PhhSpheroidWindowTarget(
            observation_id=observation.id,
            condition_id=observation.condition_id,
            time_start_h=observation.time_start_h,
            time_end_h=observation.time_end_h,
            duration_h=observation.time_end_h - observation.time_start_h,
            observed_mean_fmol_per_cell_h=observation.mean_fmol_per_cell_h,
            observed_sd_fmol_per_cell_h=observation.sd_fmol_per_cell_h,
            cumulative_mean_increment_fmol_per_seeded_cell=_stable_decimal(
                observation.mean_fmol_per_cell_h * (observation.time_end_h - observation.time_start_h)
            ),
            cumulative_sd_increment_fmol_per_seeded_cell=_stable_decimal(
                observation.sd_fmol_per_cell_h * (observation.time_end_h - observation.time_start_h)
            ),
            overlaps_subwindows=observation.overlaps_subwindows,
            independent_trajectory_target=not observation.overlaps_subwindows,
            source_ids=observation.source_ids,
        )
        for observation in curated.glucose_consumption_observations
    )
    protocol = PhhSpheroidValidationProtocol(
        version=VERSION,
        protocol_id=str(payload["protocol_id"]),
        status=str(payload["status"]),
        method_contract=method,
        output_contract=output,
        conditions=curated.conditions,
        window_targets=targets,
        cumulative_target_trajectories=_build_trajectories(curated.conditions, targets),
        overlap_consistency_audits=_build_overlap_audits(curated.conditions, targets),
        medium_concentration_trajectory_reconstruction_ready=bool(gates["medium_concentration_trajectory_reconstruction_ready"]),
        cumulative_mean_trajectory_ready=bool(gates["cumulative_mean_trajectory_ready"]),
        combined_cumulative_uncertainty_ready=bool(gates["combined_cumulative_uncertainty_ready"]),
        vectorial_flux_decomposition_ready=bool(gates["vectorial_flux_decomposition_ready"]),
        exact_protocol_prediction_loaded=bool(gates["exact_protocol_prediction_loaded"]),
        acceptance_threshold=None,
        automatic_state_coupling=bool(gates["automatic_state_coupling"]),
        predictive_ready=bool(gates["predictive_ready"]),
        source_ids=tuple(str(item) for item in payload["source_ids"]),  # type: ignore[index]
        source_locators=tuple(str(item) for item in payload["source_locators"]),  # type: ignore[index]
        limitations=tuple(str(item) for item in payload["limitations"]),  # type: ignore[index]
    )
    validate_phh_spheroid_validation_protocol(protocol)
    return protocol


def validate_phh_spheroid_validation_protocol(protocol: PhhSpheroidValidationProtocol) -> None:
    if protocol.version != VERSION or protocol.source_ids != ("kemas2021_phh_glucose",):
        raise ValueError("unexpected PHH spheroid validation protocol or provenance")
    method = protocol.method_contract
    if (
        method.species != "Homo sapiens"
        or method.cell_format != "primary_human_hepatocyte_3d_spheroid"
        or method.plate_format != "ultra_low_attachment_96_well_plate"
        or method.seeded_viable_cells_per_well != 1500
        or not method.single_spheroid_observed_per_well_after_aggregation
        or method.culture_seeding_medium_volume_uL != 100.0
        or method.assay_sample_supernatant_volume_uL != 10.0
        or method.assay_replication != "duplicates"
        or method.assay_replication_count != 2
    ):
        raise ValueError("source-locked Kemas culture or assay method changed")
    if (
        method.glucose_challenge_initial_medium_volume_uL is not None
        or method.remaining_medium_volume_schedule_uL is not None
        or method.volumetric_factor_VF is not None
        or method.viable_cell_count_at_each_observation_window is not None
    ):
        raise ValueError("unreported Kemas volume, VF or viable-cell schedule was invented")
    if method.reported_calculation != "(C0 * V0 - Ct * Vt) / (VF * n)" or set(method.reported_symbol_semantics) != {"C0", "V0", "Ct", "Vt", "n", "VF"}:
        raise ValueError("reported Kemas glucose-disappearance calculation changed")
    output = protocol.output_contract
    if (
        output.quantity != "net_medium_glucose_disappearance"
        or output.positive_direction != "positive_is_net_disappearance"
        or output.rate_unit != "fmol_per_cell_per_h"
        or output.cumulative_unit != "fmol_per_seeded_cell"
        or output.denominator != "seeded_cells_per_spheroid"
        or output.uncertainty_type != "SD"
        or output.nonoverlapping_windows_h != ((0.0, 6.0), (6.0, 24.0), (24.0, 72.0))
        or output.overlapping_audit_window_h != (0.0, 72.0)
    ):
        raise ValueError("PHH spheroid output contract changed")
    curated = load_healthy_phh_glucose_validation()
    if protocol.conditions != curated.conditions:
        raise ValueError("PHH spheroid exposure matrix no longer matches curated primary observations")
    observations = {item.id: item for item in curated.glucose_consumption_observations}
    if len(protocol.window_targets) != 16 or {item.observation_id for item in protocol.window_targets} != set(observations):
        raise ValueError("PHH spheroid window target matrix is incomplete")
    for target in protocol.window_targets:
        observation = observations[target.observation_id]
        expected_duration = observation.time_end_h - observation.time_start_h
        expected_values = (
            (target.duration_h, expected_duration),
            (target.observed_mean_fmol_per_cell_h, observation.mean_fmol_per_cell_h),
            (target.observed_sd_fmol_per_cell_h, observation.sd_fmol_per_cell_h),
            (target.cumulative_mean_increment_fmol_per_seeded_cell, observation.mean_fmol_per_cell_h * expected_duration),
            (target.cumulative_sd_increment_fmol_per_seeded_cell, observation.sd_fmol_per_cell_h * expected_duration),
        )
        if any(not isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12) for actual, expected in expected_values):
            raise ValueError(f"derived PHH target arithmetic changed for {target.observation_id}")
        if target.independent_trajectory_target == target.overlaps_subwindows:
            raise ValueError(f"overlap independence semantics changed for {target.observation_id}")
    if sum(item.independent_trajectory_target for item in protocol.window_targets) != 12:
        raise ValueError("PHH independent trajectory target count changed")
    if len(protocol.cumulative_target_trajectories) != 4:
        raise ValueError("PHH cumulative trajectory matrix is incomplete")
    targets_by_condition = {
        condition.id: sorted(
            (item for item in protocol.window_targets if item.condition_id == condition.id and item.independent_trajectory_target),
            key=lambda item: item.time_start_h,
        )
        for condition in protocol.conditions
    }
    for trajectory in protocol.cumulative_target_trajectories:
        windows = targets_by_condition[trajectory.condition_id]
        if [point.time_h for point in trajectory.points] != [0.0, 6.0, 24.0, 72.0]:
            raise ValueError(f"cumulative target timing changed for {trajectory.condition_id}")
        expected_cumulative = [0.0]
        for window in windows:
            expected_cumulative.append(expected_cumulative[-1] + window.cumulative_mean_increment_fmol_per_seeded_cell)
        actual_cumulative = [point.cumulative_mean_fmol_per_seeded_cell for point in trajectory.points]
        if any(not isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12) for actual, expected in zip(actual_cumulative, expected_cumulative)):
            raise ValueError(f"cumulative target arithmetic changed for {trajectory.condition_id}")
        if trajectory.combined_cumulative_uncertainty_available or any(point.cumulative_sd_fmol_per_seeded_cell is not None for point in trajectory.points):
            raise ValueError("unidentified PHH cumulative uncertainty was invented")
    if len(protocol.overlap_consistency_audits) != 4:
        raise ValueError("PHH overlap consistency audit matrix is incomplete")
    targets_by_id = {item.observation_id: item for item in protocol.window_targets}
    for audit in protocol.overlap_consistency_audits:
        subwindows = [targets_by_id[item] for item in audit.subwindow_observation_ids]
        overlap = targets_by_id[audit.reported_overlap_observation_id]
        derived_cumulative = sum(item.cumulative_mean_increment_fmol_per_seeded_cell for item in subwindows)
        reported_cumulative = overlap.cumulative_mean_increment_fmol_per_seeded_cell
        duration = sum(item.duration_h for item in subwindows)
        expected_values = (
            (audit.derived_subwindow_cumulative_mean_fmol_per_seeded_cell, derived_cumulative),
            (audit.reported_overlap_cumulative_mean_fmol_per_seeded_cell, reported_cumulative),
            (audit.cumulative_residual_reported_minus_derived_fmol_per_seeded_cell, reported_cumulative - derived_cumulative),
            (audit.derived_time_weighted_mean_fmol_per_cell_h, derived_cumulative / duration),
            (audit.reported_overlap_mean_fmol_per_cell_h, overlap.observed_mean_fmol_per_cell_h),
            (audit.rate_residual_reported_minus_derived_fmol_per_cell_h, overlap.observed_mean_fmol_per_cell_h - derived_cumulative / duration),
        )
        if any(not isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12) for actual, expected in expected_values):
            raise ValueError(f"PHH overlap audit arithmetic changed for {audit.condition_id}")
        if audit.acceptance_threshold is not None or audit.pass_fail_assigned:
            raise ValueError("descriptive overlap audit cannot assign pass/fail")
    if (
        protocol.medium_concentration_trajectory_reconstruction_ready
        or not protocol.cumulative_mean_trajectory_ready
        or protocol.combined_cumulative_uncertainty_ready
        or protocol.vectorial_flux_decomposition_ready
        or protocol.exact_protocol_prediction_loaded
        or protocol.acceptance_threshold is not None
        or protocol.automatic_state_coupling
        or protocol.predictive_ready
    ):
        raise ValueError("PHH spheroid protocol gates exceeded the evidence")


def _condition_matrix(conditions: tuple[PhhExposureCondition, ...]) -> set[tuple[object, ...]]:
    return {
        (item.id, item.label, item.glucose_mM, item.insulin_pM, item.glucagon_nM, item.glucagon_status)
        for item in conditions
    }


def match_phh_spheroid_prediction(
    protocol: PhhSpheroidValidationProtocol,
    prediction: PhhSpheroidModelPrediction,
) -> PhhPredictionProtocolMatchAudit:
    validate_phh_spheroid_validation_protocol(protocol)
    protocol_version_match = prediction.protocol_version == protocol.version
    biological_system_match = (
        prediction.species == protocol.method_contract.species
        and prediction.cell_format == protocol.method_contract.cell_format
        and prediction.health_context == "insulin_sensitive_non_steatotic_culture_group"
    )
    denominator_match = (
        prediction.seeded_viable_cells_per_spheroid == protocol.method_contract.seeded_viable_cells_per_well
        and prediction.denominator == protocol.output_contract.denominator
    )
    output_contract_match = (
        prediction.output_quantity == protocol.output_contract.quantity
        and prediction.positive_direction == protocol.output_contract.positive_direction
        and prediction.unit == protocol.output_contract.rate_unit
    )
    exposure_matrix_match = _condition_matrix(prediction.conditions) == _condition_matrix(protocol.conditions)
    expected_windows = {
        (item.condition_id, item.time_start_h, item.time_end_h)
        for item in protocol.window_targets
    }
    actual_window_keys = [
        (item.condition_id, item.time_start_h, item.time_end_h)
        for item in prediction.windows
    ]
    window_matrix_match = len(actual_window_keys) == len(set(actual_window_keys)) and set(actual_window_keys) == expected_windows
    prediction_values_finite = all(isfinite(item.predicted_mean_fmol_per_cell_h) for item in prediction.windows)
    artifact_provenance_present = bool(prediction.prediction_set_id and prediction.model_id) and bool(
        SHA256_PATTERN.fullmatch(prediction.model_artifact_sha256)
    )
    checks = {
        "prediction protocol version differs from the locked protocol": protocol_version_match,
        "species, PHH spheroid format or health context differs": biological_system_match,
        "seeded-cell denominator differs": denominator_match,
        "quantity, sign or unit differs": output_contract_match,
        "glucose/insulin/glucagon exposure matrix differs": exposure_matrix_match,
        "the exact 16-window matrix is incomplete, duplicated or changed": window_matrix_match,
        "one or more prediction values is non-finite": prediction_values_finite,
        "model/prediction identifier or SHA-256 provenance is missing": artifact_provenance_present,
    }
    blockers = tuple(message for message, passed in checks.items() if not passed)
    return PhhPredictionProtocolMatchAudit(
        protocol_version_match=protocol_version_match,
        biological_system_match=biological_system_match,
        denominator_match=denominator_match,
        output_contract_match=output_contract_match,
        exposure_matrix_match=exposure_matrix_match,
        window_matrix_match=window_matrix_match,
        prediction_values_finite=prediction_values_finite,
        artifact_provenance_present=artifact_provenance_present,
        exact_protocol_match=not blockers,
        blockers=blockers,
    )


def compare_phh_spheroid_prediction(
    protocol: PhhSpheroidValidationProtocol,
    prediction: PhhSpheroidModelPrediction,
) -> PhhSpheroidProtocolComparison:
    audit = match_phh_spheroid_prediction(protocol, prediction)
    if not audit.exact_protocol_match:
        raise ValueError("prediction does not exactly match the locked PHH protocol: " + "; ".join(audit.blockers))
    predictions = {
        (item.condition_id, item.time_start_h, item.time_end_h): item
        for item in prediction.windows
    }
    residuals: list[PhhPredictionResidual] = []
    for target in protocol.window_targets:
        predicted = predictions[(target.condition_id, target.time_start_h, target.time_end_h)].predicted_mean_fmol_per_cell_h
        residual = predicted - target.observed_mean_fmol_per_cell_h
        residuals.append(
            PhhPredictionResidual(
                observation_id=target.observation_id,
                condition_id=target.condition_id,
                time_start_h=target.time_start_h,
                time_end_h=target.time_end_h,
                observed_mean_fmol_per_cell_h=target.observed_mean_fmol_per_cell_h,
                observed_sd_fmol_per_cell_h=target.observed_sd_fmol_per_cell_h,
                predicted_mean_fmol_per_cell_h=predicted,
                predicted_minus_observed_fmol_per_cell_h=residual,
                relative_residual=(residual / target.observed_mean_fmol_per_cell_h if target.observed_mean_fmol_per_cell_h else None),
                sd_standardized_residual=residual / target.observed_sd_fmol_per_cell_h,
                sd_interpretation="Prediction-minus-observation divided by reported SD; descriptive only, not an acceptance test.",
                independent_trajectory_target=target.independent_trajectory_target,
                pass_fail_assigned=False,
            )
        )
    return PhhSpheroidProtocolComparison(
        prediction_set_id=prediction.prediction_set_id,
        status="descriptive_exact_protocol_residuals_no_pass_threshold",
        match_audit=audit,
        residuals=tuple(residuals),
        aggregate_score=None,
        acceptance_threshold=None,
        pass_fail_assigned=False,
        may_drive_cell_state=False,
    )


def phh_spheroid_validation_protocol_snapshot() -> dict[str, object]:
    protocol = build_phh_spheroid_validation_protocol()
    payload = protocol.to_dict()
    payload["summary"] = {
        "exposure_bundle_count": len(protocol.conditions),
        "measured_window_count": len(protocol.window_targets),
        "independent_trajectory_target_count": sum(item.independent_trajectory_target for item in protocol.window_targets),
        "overlap_consistency_audit_count": len(protocol.overlap_consistency_audits),
        "cumulative_trajectory_count": len(protocol.cumulative_target_trajectories),
        "cumulative_target_point_count": sum(len(item.points) for item in protocol.cumulative_target_trajectories),
        "submitted_model_prediction_count": 0,
        "exact_protocol_model_prediction_count": 0,
        "exact_protocol_comparison_count": 0,
        "pass_fail_count": 0,
        "medium_concentration_trajectory_count": 0,
    }
    return payload
