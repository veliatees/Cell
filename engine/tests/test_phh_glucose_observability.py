from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from cell_engine.quantitative.phh_glucose_observability import (
    PhhCumulativeModelPoint,
    PhhCumulativeModelTrajectorySet,
    audit_phh_cumulative_model_input,
    build_phh_glucose_observability,
    phh_glucose_observability_snapshot,
    project_cumulative_trajectory_to_phh_windows,
    validate_phh_glucose_observability,
)
from cell_engine.quantitative.phh_spheroid_protocol import (
    build_phh_spheroid_validation_protocol,
    compare_phh_spheroid_prediction,
)


def _software_fixture_trajectory() -> PhhCumulativeModelTrajectorySet:
    state = build_phh_glucose_observability()
    protocol = build_phh_spheroid_validation_protocol()
    return PhhCumulativeModelTrajectorySet(
        prediction_set_id="unit_test_only_cumulative_trajectory",
        model_id="software_operator_test_not_a_scientific_model",
        model_artifact_sha256=hashlib.sha256(b"PHH cumulative software fixture").hexdigest(),
        protocol_version=state.protocol_version,
        species=protocol.method_contract.species,
        cell_format=protocol.method_contract.cell_format,
        health_context="insulin_sensitive_non_steatotic_culture_group",
        seeded_viable_cells_per_spheroid=protocol.method_contract.seeded_viable_cells_per_well,
        denominator=state.measurement_contract.output_denominator,
        input_quantity=state.measurement_contract.input_quantity,
        input_positive_direction=state.measurement_contract.input_positive_direction,
        unit=state.measurement_contract.input_unit,
        conditions=protocol.conditions,
        points=tuple(
            PhhCumulativeModelPoint(
                condition_id=trajectory.condition_id,
                time_h=point.time_h,
                cumulative_net_disappearance_fmol_per_seeded_cell=point.cumulative_mean_fmol_per_seeded_cell,
            )
            for trajectory in protocol.cumulative_target_trajectories
            for point in trajectory.points
        ),
    )


def test_observability_gate_identifies_only_the_aggregate_medium_endpoint() -> None:
    state = build_phh_glucose_observability()
    validate_phh_glucose_observability(state)

    identified = [item.id for item in state.quantity_audit if item.identified_from_current_protocol]
    mechanism_quantities = [item for item in state.quantity_audit if item.quantity_class == "mechanistic_flux"]
    assert identified == ["net_medium_glucose_disappearance_window"]
    assert len(mechanism_quantities) == 9
    assert not any(item.identified_from_current_protocol for item in mechanism_quantities)
    assert not any(item.may_fit_kinetic_parameter for item in state.quantity_audit)
    assert not state.mechanistic_flux_decomposition_ready
    assert not state.kinetic_parameter_fit_ready
    assert not state.automatic_state_coupling


def test_supplement_preserves_negative_donor_flux_without_inventing_trajectory() -> None:
    state = build_phh_glucose_observability()
    constraints = {item.id: item for item in state.supplemental_constraints}

    donor = constraints["donor_resolved_signed_net_flux"]
    viability = constraints["short_term_challenge_viability"]
    assert "Donor 1 showed net glucose production" in donor.finding
    assert not donor.numeric_trajectory_available
    assert donor.reported_n is None
    assert viability.reported_n == 8
    assert not viability.numeric_trajectory_available
    assert not state.donor_specific_numeric_trajectory_ready


def test_exact_cumulative_output_projects_to_all_protocol_windows() -> None:
    state = build_phh_glucose_observability()
    protocol = build_phh_spheroid_validation_protocol()
    projection = project_cumulative_trajectory_to_phh_windows(state, _software_fixture_trajectory())
    comparison = compare_phh_spheroid_prediction(protocol, projection.prediction)

    assert projection.input_audit.exact_input_match
    assert projection.derived_window_count == 16
    assert projection.fitted_parameter_count == 0
    assert not projection.pass_fail_assigned
    assert not projection.may_drive_cell_state
    independent = [item for item in comparison.residuals if item.independent_trajectory_target]
    overlaps = {item.condition_id: item for item in comparison.residuals if not item.independent_trajectory_target}
    assert len(independent) == 12
    assert all(item.predicted_minus_observed_fmol_per_cell_h == pytest.approx(0.0) for item in independent)
    assert overlaps["hi_hg"].predicted_minus_observed_fmol_per_cell_h == pytest.approx(0.0416666666666665)
    assert overlaps["li_hg"].predicted_minus_observed_fmol_per_cell_h == pytest.approx(-0.0333333333333332)


def test_operator_allows_signed_net_production() -> None:
    state = build_phh_glucose_observability()
    trajectory = _software_fixture_trajectory()
    points = tuple(
        replace(point, cumulative_net_disappearance_fmol_per_seeded_cell=-12.0)
        if point.condition_id == "hi_hg" and point.time_h == 6.0
        else point
        for point in trajectory.points
    )
    projection = project_cumulative_trajectory_to_phh_windows(state, replace(trajectory, points=points))
    first_window = next(
        item
        for item in projection.prediction.windows
        if item.condition_id == "hi_hg" and item.time_start_h == 0.0 and item.time_end_h == 6.0
    )
    assert first_window.predicted_mean_fmol_per_cell_h == pytest.approx(-2.0)


def test_operator_rejects_missing_point_nonzero_origin_and_missing_provenance() -> None:
    state = build_phh_glucose_observability()
    trajectory = _software_fixture_trajectory()

    missing = audit_phh_cumulative_model_input(state, replace(trajectory, points=trajectory.points[:-1]))
    assert not missing.point_matrix_match
    nonzero_origin = tuple(
        replace(point, cumulative_net_disappearance_fmol_per_seeded_cell=1.0)
        if point.condition_id == "hi_hg" and point.time_h == 0.0
        else point
        for point in trajectory.points
    )
    origin_audit = audit_phh_cumulative_model_input(state, replace(trajectory, points=nonzero_origin))
    assert not origin_audit.initial_values_zero
    provenance = audit_phh_cumulative_model_input(state, replace(trajectory, model_artifact_sha256="missing"))
    assert not provenance.artifact_provenance_present
    with pytest.raises(ValueError, match="does not match"):
        project_cumulative_trajectory_to_phh_windows(state, replace(trajectory, points=trajectory.points[:-1]))


def test_snapshot_discloses_zero_mechanistic_identification_and_zero_model_runs() -> None:
    snapshot = phh_glucose_observability_snapshot()
    summary = snapshot["summary"]

    assert summary["operator_expected_input_point_count"] == 16
    assert summary["operator_projected_window_count"] == 16
    assert summary["aggregate_observable_count"] == 1
    assert summary["mechanism_specific_quantity_count"] == 9
    assert summary["mechanism_specific_quantity_identified_count"] == 0
    assert summary["kinetic_parameter_identified_count"] == 0
    assert summary["exact_protocol_model_trajectory_count"] == 0
    assert summary["pass_fail_count"] == 0
