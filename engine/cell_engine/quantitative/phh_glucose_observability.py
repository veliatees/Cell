"""Observation-space operator and identifiability gate for Kemas PHH glucose data.

The Kemas assay measures a signed net glucose balance in culture medium.  This
module defines the exact mathematical operator that maps a model's cumulative
net-disappearance output to the paper's reporting windows.  It deliberately
does not infer bidirectional transport, intracellular pathway fluxes or kinetic
parameters from that single aggregate endpoint.
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
from cell_engine.quantitative.phh_glucose_validation import (
    PHH_GLUCOSE_VALIDATION_SOURCES,
    PhhExposureCondition,
)
from cell_engine.quantitative.phh_spheroid_protocol import (
    PhhSpheroidModelPrediction,
    PhhSpheroidPredictionWindow,
    build_phh_spheroid_validation_protocol,
    match_phh_spheroid_prediction,
)


DATE_VERIFIED = "2026-07-14"
VERSION = "phh_glucose_observability_v1"
SCHEMA_VERSION = "cell.phh-glucose-observability.v1"
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = REPOSITORY_ROOT / "data" / "phh_baseline" / "curated" / "kemas2021_phh_glucose_observability.v1.json"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


PHH_GLUCOSE_OBSERVABILITY_SOURCES: dict[str, SourceReference] = {
    "grankvist2024_human_liver_fluxomics": SourceReference(
        id="grankvist2024_human_liver_fluxomics",
        title="Global 13C tracing and metabolic flux analysis of intact human liver tissue ex vivo",
        url="https://www.nature.com/articles/s42255-024-01119-3",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Primary human intact-liver-tissue study combining 13C tracing, spent-medium measurements, "
            "mass spectrometry and model-based flux analysis. It supports the required measurement strategy, "
            "not numeric transfer into PHH spheroids."
        ),
    ),
}


QuantityClass = Literal["aggregate_output", "mechanistic_flux", "donor_effect", "causal_effect", "normalization"]


@dataclass(frozen=True)
class PhhGlucoseMeasurementContract:
    input_quantity: str
    input_unit: str
    input_positive_direction: str
    required_timepoints_h: tuple[float, ...]
    required_condition_ids: tuple[str, ...]
    output_quantity: str
    output_unit: str
    output_denominator: str
    operator_formula: str


@dataclass(frozen=True)
class PhhSupplementalConstraint:
    id: str
    source_locator: str
    finding: str
    reported_n: int | None
    numeric_trajectory_available: bool
    model_consequence: str


@dataclass(frozen=True)
class PhhQuantityIdentifiabilityAudit:
    id: str
    quantity_class: QuantityClass
    identified_from_current_protocol: bool
    numeric_value_available: bool
    may_fit_kinetic_parameter: bool
    reason: str
    required_measurement_ids: tuple[str, ...]
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class PhhRequiredMeasurement:
    id: str
    label: str
    requirements: tuple[str, ...]
    purpose: str


@dataclass(frozen=True)
class PhhGlucoseObservabilityState:
    version: str
    status: str
    protocol_version: str
    measurement_contract: PhhGlucoseMeasurementContract
    supplemental_constraints: tuple[PhhSupplementalConstraint, ...]
    quantity_audit: tuple[PhhQuantityIdentifiabilityAudit, ...]
    required_measurements: tuple[PhhRequiredMeasurement, ...]
    cumulative_measurement_operator_ready: bool
    signed_output_required: bool
    donor_specific_numeric_trajectory_ready: bool
    mechanistic_flux_decomposition_ready: bool
    kinetic_parameter_fit_ready: bool
    exact_protocol_model_trajectory_loaded: bool
    automatic_state_coupling: bool
    predictive_ready: bool
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


@dataclass(frozen=True)
class PhhCumulativeModelPoint:
    condition_id: str
    time_h: float
    cumulative_net_disappearance_fmol_per_seeded_cell: float


@dataclass(frozen=True)
class PhhCumulativeModelTrajectorySet:
    prediction_set_id: str
    model_id: str
    model_artifact_sha256: str
    protocol_version: str
    species: str
    cell_format: str
    health_context: str
    seeded_viable_cells_per_spheroid: int
    denominator: str
    input_quantity: str
    input_positive_direction: str
    unit: str
    conditions: tuple[PhhExposureCondition, ...]
    points: tuple[PhhCumulativeModelPoint, ...]


@dataclass(frozen=True)
class PhhCumulativeInputAudit:
    protocol_version_match: bool
    biological_system_match: bool
    denominator_match: bool
    input_contract_match: bool
    exposure_matrix_match: bool
    point_matrix_match: bool
    initial_values_zero: bool
    values_finite: bool
    artifact_provenance_present: bool
    exact_input_match: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class PhhGlucoseMeasurementProjection:
    status: str
    input_audit: PhhCumulativeInputAudit
    prediction: PhhSpheroidModelPrediction
    operator_formula: str
    derived_window_count: int
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


def build_phh_glucose_observability(
    data_path: Path = DATA_PATH,
) -> PhhGlucoseObservabilityState:
    payload = _load_json(data_path)
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported PHH glucose observability schema")
    contract_raw = payload.get("measurement_contract")
    constraints_raw = payload.get("supplemental_constraints")
    quantities_raw = payload.get("quantity_audit")
    measurements_raw = payload.get("required_measurements")
    gates = payload.get("gates")
    if (
        not isinstance(contract_raw, dict)
        or not isinstance(constraints_raw, list)
        or not isinstance(quantities_raw, list)
        or not isinstance(measurements_raw, list)
        or not isinstance(gates, dict)
    ):
        raise ValueError("PHH glucose observability payload is malformed")
    contract = PhhGlucoseMeasurementContract(
        input_quantity=str(contract_raw["input_quantity"]),
        input_unit=str(contract_raw["input_unit"]),
        input_positive_direction=str(contract_raw["input_positive_direction"]),
        required_timepoints_h=tuple(float(item) for item in contract_raw["required_timepoints_h"]),  # type: ignore[index]
        required_condition_ids=tuple(str(item) for item in contract_raw["required_condition_ids"]),  # type: ignore[index]
        output_quantity=str(contract_raw["output_quantity"]),
        output_unit=str(contract_raw["output_unit"]),
        output_denominator=str(contract_raw["output_denominator"]),
        operator_formula=str(contract_raw["operator_formula"]),
    )
    constraints = tuple(
        PhhSupplementalConstraint(
            id=str(item["id"]),
            source_locator=str(item["source_locator"]),
            finding=str(item["finding"]),
            reported_n=None if item["reported_n"] is None else int(item["reported_n"]),
            numeric_trajectory_available=bool(item["numeric_trajectory_available"]),
            model_consequence=str(item["model_consequence"]),
        )
        for item in constraints_raw
        if isinstance(item, dict)
    )
    quantities = tuple(
        PhhQuantityIdentifiabilityAudit(
            id=str(item["id"]),
            quantity_class=str(item["quantity_class"]),  # type: ignore[arg-type]
            identified_from_current_protocol=bool(item["identified_from_current_protocol"]),
            numeric_value_available=bool(item["numeric_value_available"]),
            may_fit_kinetic_parameter=bool(item["may_fit_kinetic_parameter"]),
            reason=str(item["reason"]),
            required_measurement_ids=tuple(str(value) for value in item["required_measurement_ids"]),  # type: ignore[index]
            source_ids=tuple(str(value) for value in item["source_ids"]),  # type: ignore[index]
        )
        for item in quantities_raw
        if isinstance(item, dict)
    )
    measurements = tuple(
        PhhRequiredMeasurement(
            id=str(item["id"]),
            label=str(item["label"]),
            requirements=tuple(str(value) for value in item["requirements"]),  # type: ignore[index]
            purpose=str(item["purpose"]),
        )
        for item in measurements_raw
        if isinstance(item, dict)
    )
    state = PhhGlucoseObservabilityState(
        version=VERSION,
        status=str(payload["status"]),
        protocol_version=str(payload["protocol_version"]),
        measurement_contract=contract,
        supplemental_constraints=constraints,
        quantity_audit=quantities,
        required_measurements=measurements,
        cumulative_measurement_operator_ready=bool(gates["cumulative_measurement_operator_ready"]),
        signed_output_required=bool(gates["signed_output_required"]),
        donor_specific_numeric_trajectory_ready=bool(gates["donor_specific_numeric_trajectory_ready"]),
        mechanistic_flux_decomposition_ready=bool(gates["mechanistic_flux_decomposition_ready"]),
        kinetic_parameter_fit_ready=bool(gates["kinetic_parameter_fit_ready"]),
        exact_protocol_model_trajectory_loaded=bool(gates["exact_protocol_model_trajectory_loaded"]),
        automatic_state_coupling=bool(gates["automatic_state_coupling"]),
        predictive_ready=bool(gates["predictive_ready"]),
        source_ids=tuple(str(item) for item in payload["source_ids"]),  # type: ignore[index]
        limitations=tuple(str(item) for item in payload["limitations"]),  # type: ignore[index]
    )
    validate_phh_glucose_observability(state)
    return state


def validate_phh_glucose_observability(state: PhhGlucoseObservabilityState) -> None:
    protocol = build_phh_spheroid_validation_protocol()
    contract = state.measurement_contract
    if state.version != VERSION or state.protocol_version != protocol.version:
        raise ValueError("PHH glucose observability version or protocol link changed")
    if (
        contract.input_quantity != "cumulative_net_medium_glucose_disappearance"
        or contract.input_unit != "fmol_per_seeded_cell"
        or contract.input_positive_direction != "positive_is_net_disappearance_negative_is_net_production"
        or contract.required_timepoints_h != (0.0, 6.0, 24.0, 72.0)
        or contract.required_condition_ids != ("hi_hg", "li_hg", "hi_lg", "li_lg")
        or contract.output_quantity != protocol.output_contract.quantity
        or contract.output_unit != protocol.output_contract.rate_unit
        or contract.output_denominator != protocol.output_contract.denominator
        or contract.operator_formula != "(cumulative_end - cumulative_start) / (time_end_h - time_start_h)"
    ):
        raise ValueError("PHH glucose measurement-operator contract changed")
    constraints = {item.id: item for item in state.supplemental_constraints}
    if set(constraints) != {"donor_resolved_signed_net_flux", "short_term_challenge_viability"}:
        raise ValueError("PHH supplemental constraint set is incomplete")
    if (
        constraints["donor_resolved_signed_net_flux"].reported_n is not None
        or constraints["donor_resolved_signed_net_flux"].numeric_trajectory_available
        or constraints["short_term_challenge_viability"].reported_n != 8
        or constraints["short_term_challenge_viability"].numeric_trajectory_available
    ):
        raise ValueError("qualitative PHH supplement findings were promoted to numeric trajectories")
    quantity_ids = {item.id for item in state.quantity_audit}
    expected_quantity_ids = {
        "net_medium_glucose_disappearance_window",
        "glucose_transport_influx",
        "glucose_transport_efflux",
        "glucokinase_flux",
        "glucose_6_phosphatase_flux",
        "glycogen_synthesis_flux",
        "glycogenolysis_flux",
        "glycolysis_flux",
        "gluconeogenesis_flux",
        "pentose_phosphate_pathway_flux",
        "donor_specific_signed_net_flux",
        "pure_insulin_causal_effect",
        "viable_cell_normalized_flux",
    }
    if quantity_ids != expected_quantity_ids:
        raise ValueError("PHH glucose identifiability audit is incomplete")
    identified = tuple(item for item in state.quantity_audit if item.identified_from_current_protocol)
    if len(identified) != 1 or identified[0].id != "net_medium_glucose_disappearance_window":
        raise ValueError("an unobserved PHH glucose quantity was marked identified")
    mechanistic = tuple(item for item in state.quantity_audit if item.quantity_class == "mechanistic_flux")
    if len(mechanistic) != 9 or any(item.identified_from_current_protocol for item in mechanistic):
        raise ValueError("mechanistic PHH glucose flux was identified from an aggregate endpoint")
    if any(item.may_fit_kinetic_parameter for item in state.quantity_audit):
        raise ValueError("PHH aggregate endpoint cannot identify a kinetic parameter")
    required_ids = {item.id for item in state.required_measurements}
    expected_required_ids = {
        "signed_donor_resolved_medium_mass_balance",
        "isotope_resolved_fluxomics",
        "intracellular_metabolite_timecourse",
        "transporter_and_enzyme_abundance",
        "orthogonal_hormone_perturbation_timecourse",
    }
    if required_ids != expected_required_ids:
        raise ValueError("PHH glucose required-measurement set is incomplete")
    for item in state.quantity_audit:
        if not set(item.required_measurement_ids) <= required_ids:
            raise ValueError(f"unknown required measurement in {item.id}")
    registered_sources = (
        set(PHH_GLUCOSE_VALIDATION_SOURCES)
        | {"koenig2012_hepatic_glucose_model"}
        | set(PHH_GLUCOSE_OBSERVABILITY_SOURCES)
    )
    if set(state.source_ids) != {
        "kemas2021_phh_glucose",
        "koenig2012_hepatic_glucose_model",
        "grankvist2024_human_liver_fluxomics",
    }:
        raise ValueError("PHH glucose observability provenance changed")
    if any(not set(item.source_ids) <= registered_sources for item in state.quantity_audit):
        raise ValueError("PHH glucose quantity audit has unregistered provenance")
    if (
        not state.cumulative_measurement_operator_ready
        or not state.signed_output_required
        or state.donor_specific_numeric_trajectory_ready
        or state.mechanistic_flux_decomposition_ready
        or state.kinetic_parameter_fit_ready
        or state.exact_protocol_model_trajectory_loaded
        or state.automatic_state_coupling
        or state.predictive_ready
    ):
        raise ValueError("PHH glucose observability gates exceeded the evidence")


def _condition_matrix(conditions: tuple[PhhExposureCondition, ...]) -> set[tuple[object, ...]]:
    return {
        (item.id, item.label, item.glucose_mM, item.insulin_pM, item.glucagon_nM, item.glucagon_status)
        for item in conditions
    }


def audit_phh_cumulative_model_input(
    state: PhhGlucoseObservabilityState,
    trajectory: PhhCumulativeModelTrajectorySet,
) -> PhhCumulativeInputAudit:
    validate_phh_glucose_observability(state)
    protocol = build_phh_spheroid_validation_protocol()
    contract = state.measurement_contract
    protocol_version_match = trajectory.protocol_version == state.protocol_version
    biological_system_match = (
        trajectory.species == protocol.method_contract.species
        and trajectory.cell_format == protocol.method_contract.cell_format
        and trajectory.health_context == "insulin_sensitive_non_steatotic_culture_group"
    )
    denominator_match = (
        trajectory.seeded_viable_cells_per_spheroid == protocol.method_contract.seeded_viable_cells_per_well
        and trajectory.denominator == contract.output_denominator
    )
    input_contract_match = (
        trajectory.input_quantity == contract.input_quantity
        and trajectory.input_positive_direction == contract.input_positive_direction
        and trajectory.unit == contract.input_unit
    )
    exposure_matrix_match = _condition_matrix(trajectory.conditions) == _condition_matrix(protocol.conditions)
    expected_keys = {
        (condition_id, time_h)
        for condition_id in contract.required_condition_ids
        for time_h in contract.required_timepoints_h
    }
    actual_keys = [(item.condition_id, item.time_h) for item in trajectory.points]
    point_matrix_match = len(actual_keys) == len(set(actual_keys)) and set(actual_keys) == expected_keys
    initial_values_zero = all(
        item.time_h != 0.0
        or isclose(item.cumulative_net_disappearance_fmol_per_seeded_cell, 0.0, rel_tol=0.0, abs_tol=1e-12)
        for item in trajectory.points
    )
    values_finite = all(
        isfinite(item.time_h) and isfinite(item.cumulative_net_disappearance_fmol_per_seeded_cell)
        for item in trajectory.points
    )
    artifact_provenance_present = bool(trajectory.prediction_set_id and trajectory.model_id) and bool(
        SHA256_PATTERN.fullmatch(trajectory.model_artifact_sha256)
    )
    checks = {
        "trajectory protocol version differs from the locked protocol": protocol_version_match,
        "species, PHH spheroid format or health context differs": biological_system_match,
        "seeded-cell denominator differs": denominator_match,
        "cumulative quantity, sign or unit differs": input_contract_match,
        "glucose/insulin/glucagon exposure matrix differs": exposure_matrix_match,
        "the exact 16-point cumulative matrix is incomplete, duplicated or changed": point_matrix_match,
        "one or more cumulative trajectories does not start at zero": initial_values_zero,
        "one or more trajectory values is non-finite": values_finite,
        "model/prediction identifier or SHA-256 provenance is missing": artifact_provenance_present,
    }
    blockers = tuple(message for message, passed in checks.items() if not passed)
    return PhhCumulativeInputAudit(
        protocol_version_match=protocol_version_match,
        biological_system_match=biological_system_match,
        denominator_match=denominator_match,
        input_contract_match=input_contract_match,
        exposure_matrix_match=exposure_matrix_match,
        point_matrix_match=point_matrix_match,
        initial_values_zero=initial_values_zero,
        values_finite=values_finite,
        artifact_provenance_present=artifact_provenance_present,
        exact_input_match=not blockers,
        blockers=blockers,
    )


def project_cumulative_trajectory_to_phh_windows(
    state: PhhGlucoseObservabilityState,
    trajectory: PhhCumulativeModelTrajectorySet,
) -> PhhGlucoseMeasurementProjection:
    audit = audit_phh_cumulative_model_input(state, trajectory)
    if not audit.exact_input_match:
        raise ValueError("cumulative trajectory does not match the PHH measurement operator: " + "; ".join(audit.blockers))
    protocol = build_phh_spheroid_validation_protocol()
    point_values = {
        (item.condition_id, item.time_h): item.cumulative_net_disappearance_fmol_per_seeded_cell
        for item in trajectory.points
    }
    windows = tuple(
        PhhSpheroidPredictionWindow(
            condition_id=target.condition_id,
            time_start_h=target.time_start_h,
            time_end_h=target.time_end_h,
            predicted_mean_fmol_per_cell_h=(
                point_values[(target.condition_id, target.time_end_h)]
                - point_values[(target.condition_id, target.time_start_h)]
            )
            / target.duration_h,
        )
        for target in protocol.window_targets
    )
    prediction = PhhSpheroidModelPrediction(
        prediction_set_id=trajectory.prediction_set_id,
        model_id=trajectory.model_id,
        model_artifact_sha256=trajectory.model_artifact_sha256,
        protocol_version=trajectory.protocol_version,
        species=trajectory.species,
        cell_format=trajectory.cell_format,
        health_context=trajectory.health_context,
        seeded_viable_cells_per_spheroid=trajectory.seeded_viable_cells_per_spheroid,
        denominator=trajectory.denominator,
        output_quantity=protocol.output_contract.quantity,
        positive_direction=protocol.output_contract.positive_direction,
        unit=protocol.output_contract.rate_unit,
        conditions=trajectory.conditions,
        windows=windows,
    )
    if not match_phh_spheroid_prediction(protocol, prediction).exact_protocol_match:
        raise ValueError("measurement-operator output failed the exact PHH protocol matcher")
    return PhhGlucoseMeasurementProjection(
        status="exact_protocol_window_projection_no_fit_no_pass_threshold",
        input_audit=audit,
        prediction=prediction,
        operator_formula=state.measurement_contract.operator_formula,
        derived_window_count=len(windows),
        fitted_parameter_count=0,
        pass_fail_assigned=False,
        may_drive_cell_state=False,
    )


def phh_glucose_observability_snapshot() -> dict[str, object]:
    state = build_phh_glucose_observability()
    payload = state.to_dict()
    mechanism_quantities = tuple(item for item in state.quantity_audit if item.quantity_class == "mechanistic_flux")
    payload["summary"] = {
        "operator_expected_input_point_count": (
            len(state.measurement_contract.required_condition_ids)
            * len(state.measurement_contract.required_timepoints_h)
        ),
        "operator_projected_window_count": 16,
        "aggregate_observable_count": sum(
            item.quantity_class == "aggregate_output" and item.identified_from_current_protocol
            for item in state.quantity_audit
        ),
        "mechanism_specific_quantity_count": len(mechanism_quantities),
        "mechanism_specific_quantity_identified_count": sum(
            item.identified_from_current_protocol for item in mechanism_quantities
        ),
        "kinetic_parameter_identified_count": sum(item.may_fit_kinetic_parameter for item in state.quantity_audit),
        "source_backed_supplemental_constraint_count": len(state.supplemental_constraints),
        "required_measurement_class_count": len(state.required_measurements),
        "donor_specific_numeric_trajectory_count": int(state.donor_specific_numeric_trajectory_ready),
        "exact_protocol_model_trajectory_count": int(state.exact_protocol_model_trajectory_loaded),
        "pass_fail_count": 0,
    }
    return payload
