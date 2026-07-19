"""Open-boundary and exact-assay bridge for hepatocyte glucose models.

Physiological sinusoidal blood flow and the Kemas PHH spheroid assay are
different physical systems. This module keeps them separate, preserves every
reported missing value, and provides one exact bridge from model-generated
signed window fluxes to the existing cumulative PHH measurement operator.

No glucose transport law or kinetic magnitude is defined here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from math import isfinite

from cell_engine.core.serialization import to_plain
from cell_engine.quantitative.phh_glucose_observability import (
    PhhCumulativeModelPoint,
    PhhCumulativeModelTrajectorySet,
    PhhGlucoseMeasurementProjection,
    build_phh_glucose_observability,
    project_cumulative_trajectory_to_phh_windows,
)
from cell_engine.quantitative.phh_glucose_validation import PhhExposureCondition
from cell_engine.quantitative.phh_spheroid_protocol import (
    PhhSpheroidValidationProtocol,
    build_phh_spheroid_validation_protocol,
)
from cell_engine.stochastic.sinusoid import build_sinusoid_coupled_homeostasis


VERSION = "glucose_open_system_exact_assay_v1"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class PhysiologicalSinusoidBoundaryContract:
    biological_system: str
    nutritional_profile: str
    glucose_target_mM: float
    glucose_reference_low_mM: float
    glucose_reference_high_mM: float
    whole_liver_mean_transit_time_s: float
    anatomical_sinusoid_volume_l: None
    hepatocyte_exchange_flux_fmol_per_cell_h: None
    concentration_boundary_ready: bool
    single_sinusoid_flow_geometry_ready: bool
    hepatocyte_transport_coupling_ready: bool
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class PhhBatchExposureBoundary:
    condition_id: str
    label: str
    initial_glucose_mM: float
    initial_insulin_pM: float
    initial_glucagon_nM: float | None
    glucagon_status: str
    concentration_control_mode: str


@dataclass(frozen=True)
class PhhBatchAssayBoundaryContract:
    biological_system: str
    topology: str
    seeded_viable_cells_per_spheroid: int
    required_timepoints_h: tuple[float, ...]
    exposures: tuple[PhhBatchExposureBoundary, ...]
    challenge_initial_medium_volume_uL: None
    remaining_medium_volume_schedule_uL: None
    volumetric_factor: None
    viable_cell_count_schedule: None
    initial_exposure_matrix_ready: bool
    concentration_trajectory_reconstruction_ready: bool
    cumulative_amount_operator_ready: bool
    intracellular_transport_coupling_ready: bool
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class GlucoseOpenSystemProgram:
    version: str
    status: str
    physiological_sinusoid: PhysiologicalSinusoidBoundaryContract
    phh_batch_assay: PhhBatchAssayBoundaryContract
    cross_context_parameter_transfer_allowed: bool
    automatic_state_coupling: bool
    predictive_ready: bool
    source_ids: tuple[str, ...]
    policy: str

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


@dataclass(frozen=True)
class PhhSignedWindowFlux:
    condition_id: str
    time_start_h: float
    time_end_h: float
    net_medium_glucose_disappearance_fmol_per_cell_h: float


@dataclass(frozen=True)
class PhhWindowFluxPredictionSet:
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
    windows: tuple[PhhSignedWindowFlux, ...]


@dataclass(frozen=True)
class PhhWindowFluxInputAudit:
    protocol_version_match: bool
    biological_system_match: bool
    denominator_match: bool
    output_contract_match: bool
    exposure_matrix_match: bool
    independent_window_matrix_match: bool
    values_finite: bool
    artifact_provenance_present: bool
    exact_input_match: bool
    blockers: tuple[str, ...]


def _condition_matrix(conditions: tuple[PhhExposureCondition, ...]) -> set[tuple[object, ...]]:
    return {
        (item.id, item.label, item.glucose_mM, item.insulin_pM, item.glucagon_nM, item.glucagon_status)
        for item in conditions
    }


def build_glucose_open_system_program() -> GlucoseOpenSystemProgram:
    sinusoid = build_sinusoid_coupled_homeostasis("midlobular", "postabsorptive")
    protocol = build_phh_spheroid_validation_protocol()
    method = protocol.method_contract
    observer = build_phh_glucose_observability()
    state = GlucoseOpenSystemProgram(
        version=VERSION,
        status="boundaries_structurally_ready_cell_exchange_and_prediction_blocked",
        physiological_sinusoid=PhysiologicalSinusoidBoundaryContract(
            biological_system="healthy_adult_human_liver_blood_boundary_reference",
            nutritional_profile=sinusoid.nutritional_profile,
            glucose_target_mM=sinusoid.target_glucose_mM,
            glucose_reference_low_mM=sinusoid.reference_low_mM,
            glucose_reference_high_mM=sinusoid.reference_high_mM,
            whole_liver_mean_transit_time_s=sinusoid.mean_transit_time_s,
            anatomical_sinusoid_volume_l=None,
            hepatocyte_exchange_flux_fmol_per_cell_h=None,
            concentration_boundary_ready=True,
            single_sinusoid_flow_geometry_ready=False,
            hepatocyte_transport_coupling_ready=False,
            source_ids=sinusoid.source_ids,
            limitations=sinusoid.limitations,
        ),
        phh_batch_assay=PhhBatchAssayBoundaryContract(
            biological_system=method.cell_format,
            topology="finite_batch_culture_not_perfusion_not_sinusoid",
            seeded_viable_cells_per_spheroid=method.seeded_viable_cells_per_well,
            required_timepoints_h=observer.measurement_contract.required_timepoints_h,
            exposures=tuple(
                PhhBatchExposureBoundary(
                    condition_id=item.id,
                    label=item.label,
                    initial_glucose_mM=item.glucose_mM,
                    initial_insulin_pM=item.insulin_pM,
                    initial_glucagon_nM=item.glucagon_nM,
                    glucagon_status=item.glucagon_status,
                    concentration_control_mode="reported_initial_medium_composition_not_clamped",
                )
                for item in protocol.conditions
            ),
            challenge_initial_medium_volume_uL=method.glucose_challenge_initial_medium_volume_uL,
            remaining_medium_volume_schedule_uL=method.remaining_medium_volume_schedule_uL,
            volumetric_factor=method.volumetric_factor_VF,
            viable_cell_count_schedule=method.viable_cell_count_at_each_observation_window,
            initial_exposure_matrix_ready=True,
            concentration_trajectory_reconstruction_ready=False,
            cumulative_amount_operator_ready=observer.cumulative_measurement_operator_ready,
            intracellular_transport_coupling_ready=False,
            source_ids=("kemas2021_phh_glucose",),
            limitations=(
                "The challenge-medium initial volume, remaining-volume schedule and volumetric factor are not reported.",
                "The reported endpoint is signed net medium glucose disappearance, not GLUT2 influx or intracellular pathway flux.",
                "High-insulin conditions do not report a measured zero glucagon concentration.",
            ),
        ),
        cross_context_parameter_transfer_allowed=False,
        automatic_state_coupling=False,
        predictive_ready=False,
        source_ids=("hmdb_2022", "human_hepatic_transit_1996", "kemas2021_phh_glucose"),
        policy=(
            "A physiological sinusoid and a finite PHH spheroid culture are non-interchangeable. "
            "Only exact model-generated signed outputs may be projected into the assay; missing "
            "volumes, transport rates and concentration trajectories remain null."
        ),
    )
    validate_glucose_open_system_program(state)
    return state


def validate_glucose_open_system_program(state: GlucoseOpenSystemProgram) -> None:
    protocol = build_phh_spheroid_validation_protocol()
    if state.version != VERSION:
        raise ValueError("glucose open-system program version changed")
    sinusoid = state.physiological_sinusoid
    if (
        sinusoid.anatomical_sinusoid_volume_l is not None
        or sinusoid.hepatocyte_exchange_flux_fmol_per_cell_h is not None
        or not sinusoid.concentration_boundary_ready
        or sinusoid.single_sinusoid_flow_geometry_ready
        or sinusoid.hepatocyte_transport_coupling_ready
    ):
        raise ValueError("unidentified single-sinusoid geometry or hepatocyte flux was activated")
    assay = state.phh_batch_assay
    method = protocol.method_contract
    if (
        assay.topology != "finite_batch_culture_not_perfusion_not_sinusoid"
        or assay.seeded_viable_cells_per_spheroid != method.seeded_viable_cells_per_well
        or assay.required_timepoints_h != (0.0, 6.0, 24.0, 72.0)
        or assay.challenge_initial_medium_volume_uL is not None
        or assay.remaining_medium_volume_schedule_uL is not None
        or assay.volumetric_factor is not None
        or assay.viable_cell_count_schedule is not None
        or not assay.initial_exposure_matrix_ready
        or assay.concentration_trajectory_reconstruction_ready
        or not assay.cumulative_amount_operator_ready
        or assay.intracellular_transport_coupling_ready
    ):
        raise ValueError("PHH batch-assay boundary exceeded the reported protocol")
    exposure_matrix = {
        (
            item.condition_id,
            item.initial_glucose_mM,
            item.initial_insulin_pM,
            item.initial_glucagon_nM,
            item.glucagon_status,
        )
        for item in assay.exposures
    }
    expected = {
        (item.id, item.glucose_mM, item.insulin_pM, item.glucagon_nM, item.glucagon_status)
        for item in protocol.conditions
    }
    if exposure_matrix != expected:
        raise ValueError("PHH batch-assay exposure matrix changed")
    if any(item.concentration_control_mode != "reported_initial_medium_composition_not_clamped" for item in assay.exposures):
        raise ValueError("PHH initial medium concentration was promoted to an unreported clamp")
    if state.cross_context_parameter_transfer_allowed or state.automatic_state_coupling or state.predictive_ready:
        raise ValueError("open-system context crossed a blocked scientific gate")


def audit_phh_window_flux_prediction(
    submission: PhhWindowFluxPredictionSet,
    protocol: PhhSpheroidValidationProtocol | None = None,
) -> PhhWindowFluxInputAudit:
    locked = protocol or build_phh_spheroid_validation_protocol()
    output = locked.output_contract
    protocol_version_match = submission.protocol_version == locked.version
    biological_system_match = (
        submission.species == locked.method_contract.species
        and submission.cell_format == locked.method_contract.cell_format
        and submission.health_context == "insulin_sensitive_non_steatotic_culture_group"
    )
    denominator_match = (
        submission.seeded_viable_cells_per_spheroid == locked.method_contract.seeded_viable_cells_per_well
        and submission.denominator == output.denominator
    )
    output_contract_match = (
        submission.output_quantity == output.quantity
        and submission.positive_direction == output.positive_direction
        and submission.unit == output.rate_unit
    )
    exposure_matrix_match = _condition_matrix(submission.conditions) == _condition_matrix(locked.conditions)
    expected_windows = {
        (item.condition_id, item.time_start_h, item.time_end_h)
        for item in locked.window_targets
        if item.independent_trajectory_target
    }
    actual_windows = [
        (item.condition_id, item.time_start_h, item.time_end_h)
        for item in submission.windows
    ]
    independent_window_matrix_match = (
        len(actual_windows) == len(set(actual_windows))
        and set(actual_windows) == expected_windows
    )
    values_finite = all(
        isfinite(item.time_start_h)
        and isfinite(item.time_end_h)
        and item.time_end_h > item.time_start_h
        and isfinite(item.net_medium_glucose_disappearance_fmol_per_cell_h)
        for item in submission.windows
    )
    artifact_provenance_present = bool(submission.prediction_set_id and submission.model_id) and bool(
        SHA256_PATTERN.fullmatch(submission.model_artifact_sha256)
    )
    checks = {
        "prediction protocol version differs from the locked PHH protocol": protocol_version_match,
        "species, PHH spheroid format or health context differs": biological_system_match,
        "seeded-cell denominator differs": denominator_match,
        "quantity, sign or unit differs": output_contract_match,
        "glucose/insulin/glucagon exposure matrix differs": exposure_matrix_match,
        "the exact 12 independent-window matrix is incomplete, duplicated or includes overlap rows": independent_window_matrix_match,
        "one or more signed window flux values is invalid": values_finite,
        "model/prediction identifier or SHA-256 provenance is missing": artifact_provenance_present,
    }
    blockers = tuple(message for message, passed in checks.items() if not passed)
    return PhhWindowFluxInputAudit(
        protocol_version_match=protocol_version_match,
        biological_system_match=biological_system_match,
        denominator_match=denominator_match,
        output_contract_match=output_contract_match,
        exposure_matrix_match=exposure_matrix_match,
        independent_window_matrix_match=independent_window_matrix_match,
        values_finite=values_finite,
        artifact_provenance_present=artifact_provenance_present,
        exact_input_match=not blockers,
        blockers=blockers,
    )


def cumulative_trajectory_from_window_fluxes(
    submission: PhhWindowFluxPredictionSet,
) -> PhhCumulativeModelTrajectorySet:
    protocol = build_phh_spheroid_validation_protocol()
    audit = audit_phh_window_flux_prediction(submission, protocol)
    if not audit.exact_input_match:
        raise ValueError("window-flux prediction does not match the PHH protocol: " + "; ".join(audit.blockers))
    windows_by_condition = {
        condition.id: sorted(
            (item for item in submission.windows if item.condition_id == condition.id),
            key=lambda item: item.time_start_h,
        )
        for condition in protocol.conditions
    }
    points: list[PhhCumulativeModelPoint] = []
    for condition in protocol.conditions:
        cumulative = 0.0
        points.append(PhhCumulativeModelPoint(condition.id, 0.0, 0.0))
        for window in windows_by_condition[condition.id]:
            cumulative += (
                window.net_medium_glucose_disappearance_fmol_per_cell_h
                * (window.time_end_h - window.time_start_h)
            )
            points.append(
                PhhCumulativeModelPoint(
                    condition.id,
                    window.time_end_h,
                    cumulative,
                )
            )
    observer = build_phh_glucose_observability()
    return PhhCumulativeModelTrajectorySet(
        prediction_set_id=submission.prediction_set_id,
        model_id=submission.model_id,
        model_artifact_sha256=submission.model_artifact_sha256,
        protocol_version=submission.protocol_version,
        species=submission.species,
        cell_format=submission.cell_format,
        health_context=submission.health_context,
        seeded_viable_cells_per_spheroid=submission.seeded_viable_cells_per_spheroid,
        denominator=submission.denominator,
        input_quantity=observer.measurement_contract.input_quantity,
        input_positive_direction=observer.measurement_contract.input_positive_direction,
        unit=observer.measurement_contract.input_unit,
        conditions=submission.conditions,
        points=tuple(points),
    )


def project_window_fluxes_to_phh_assay(
    submission: PhhWindowFluxPredictionSet,
) -> PhhGlucoseMeasurementProjection:
    return project_cumulative_trajectory_to_phh_windows(
        build_phh_glucose_observability(),
        cumulative_trajectory_from_window_fluxes(submission),
    )


def glucose_open_system_snapshot() -> dict[str, object]:
    state = build_glucose_open_system_program()
    payload = state.to_dict()
    payload["summary"] = {
        "physical_context_count": 2,
        "phh_exposure_condition_count": len(state.phh_batch_assay.exposures),
        "phh_required_timepoint_count": len(state.phh_batch_assay.required_timepoints_h),
        "reported_assay_volume_value_count": 0,
        "active_hepatocyte_exchange_flux_count": 0,
        "loaded_exact_protocol_prediction_count": 0,
        "automatic_state_coupling_count": 0,
    }
    return payload
