from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from cell_engine.quantitative.glucose_open_system import (
    PhhSignedWindowFlux,
    PhhWindowFluxPredictionSet,
    audit_phh_window_flux_prediction,
    build_glucose_open_system_program,
    cumulative_trajectory_from_window_fluxes,
    glucose_open_system_snapshot,
    project_window_fluxes_to_phh_assay,
    validate_glucose_open_system_program,
)
from cell_engine.quantitative.phh_spheroid_protocol import (
    build_phh_spheroid_validation_protocol,
    compare_phh_spheroid_prediction,
)


def _software_fixture_submission() -> PhhWindowFluxPredictionSet:
    protocol = build_phh_spheroid_validation_protocol()
    return PhhWindowFluxPredictionSet(
        prediction_set_id="unit_test_only_window_fluxes",
        model_id="software_bridge_test_not_a_scientific_model",
        model_artifact_sha256=hashlib.sha256(b"open-system software fixture").hexdigest(),
        protocol_version=protocol.version,
        species=protocol.method_contract.species,
        cell_format=protocol.method_contract.cell_format,
        health_context="insulin_sensitive_non_steatotic_culture_group",
        seeded_viable_cells_per_spheroid=protocol.method_contract.seeded_viable_cells_per_well,
        denominator=protocol.output_contract.denominator,
        output_quantity=protocol.output_contract.quantity,
        positive_direction=protocol.output_contract.positive_direction,
        unit=protocol.output_contract.rate_unit,
        conditions=protocol.conditions,
        windows=tuple(
            PhhSignedWindowFlux(
                condition_id=item.condition_id,
                time_start_h=item.time_start_h,
                time_end_h=item.time_end_h,
                net_medium_glucose_disappearance_fmol_per_cell_h=item.observed_mean_fmol_per_cell_h,
            )
            for item in protocol.window_targets
            if item.independent_trajectory_target
        ),
    )


def test_physiological_sinusoid_and_phh_batch_assay_remain_distinct() -> None:
    state = build_glucose_open_system_program()
    validate_glucose_open_system_program(state)

    assert state.physiological_sinusoid.biological_system == "healthy_adult_human_liver_blood_boundary_reference"
    assert state.phh_batch_assay.topology == "finite_batch_culture_not_perfusion_not_sinusoid"
    assert state.physiological_sinusoid.anatomical_sinusoid_volume_l is None
    assert state.physiological_sinusoid.hepatocyte_exchange_flux_fmol_per_cell_h is None
    assert not state.physiological_sinusoid.hepatocyte_transport_coupling_ready
    assert not state.cross_context_parameter_transfer_allowed


def test_batch_assay_preserves_unknown_volume_and_unmeasured_glucagon() -> None:
    assay = build_glucose_open_system_program().phh_batch_assay
    exposures = {item.condition_id: item for item in assay.exposures}

    assert assay.challenge_initial_medium_volume_uL is None
    assert assay.remaining_medium_volume_schedule_uL is None
    assert assay.volumetric_factor is None
    assert assay.viable_cell_count_schedule is None
    assert exposures["hi_hg"].initial_glucose_mM == 11.0
    assert exposures["hi_lg"].initial_glucose_mM == 5.5
    assert exposures["hi_hg"].initial_glucagon_nM is None
    assert exposures["li_hg"].initial_glucagon_nM == 100.0
    assert all(
        item.concentration_control_mode == "reported_initial_medium_composition_not_clamped"
        for item in assay.exposures
    )


def test_exact_window_fluxes_integrate_to_the_existing_measurement_operator() -> None:
    protocol = build_phh_spheroid_validation_protocol()
    submission = _software_fixture_submission()
    audit = audit_phh_window_flux_prediction(submission)
    trajectory = cumulative_trajectory_from_window_fluxes(submission)
    projection = project_window_fluxes_to_phh_assay(submission)
    comparison = compare_phh_spheroid_prediction(protocol, projection.prediction)

    assert audit.exact_input_match
    assert len(trajectory.points) == 16
    assert projection.derived_window_count == 16
    assert not projection.pass_fail_assigned
    assert not projection.may_drive_cell_state
    independent = [item for item in comparison.residuals if item.independent_trajectory_target]
    assert len(independent) == 12
    assert all(item.predicted_minus_observed_fmol_per_cell_h == pytest.approx(0.0) for item in independent)


def test_signed_window_flux_preserves_net_production() -> None:
    submission = _software_fixture_submission()
    first = submission.windows[0]
    windows = (
        replace(first, net_medium_glucose_disappearance_fmol_per_cell_h=-2.0),
        *submission.windows[1:],
    )
    projection = project_window_fluxes_to_phh_assay(replace(submission, windows=windows))
    projected = next(
        item
        for item in projection.prediction.windows
        if item.condition_id == first.condition_id
        and item.time_start_h == first.time_start_h
        and item.time_end_h == first.time_end_h
    )
    assert projected.predicted_mean_fmol_per_cell_h == pytest.approx(-2.0)


def test_window_bridge_rejects_missing_overlap_and_unprovenanced_inputs() -> None:
    submission = _software_fixture_submission()
    missing = audit_phh_window_flux_prediction(replace(submission, windows=submission.windows[:-1]))
    assert not missing.independent_window_matrix_match
    bad_hash = audit_phh_window_flux_prediction(replace(submission, model_artifact_sha256="missing"))
    assert not bad_hash.artifact_provenance_present

    protocol = build_phh_spheroid_validation_protocol()
    overlap = next(item for item in protocol.window_targets if not item.independent_trajectory_target)
    extra = PhhSignedWindowFlux(
        overlap.condition_id,
        overlap.time_start_h,
        overlap.time_end_h,
        overlap.observed_mean_fmol_per_cell_h,
    )
    overlap_audit = audit_phh_window_flux_prediction(
        replace(submission, windows=(*submission.windows, extra))
    )
    assert not overlap_audit.independent_window_matrix_match
    with pytest.raises(ValueError, match="does not match"):
        cumulative_trajectory_from_window_fluxes(replace(submission, windows=submission.windows[:-1]))


def test_open_system_snapshot_discloses_zero_flux_and_prediction_activation() -> None:
    summary = glucose_open_system_snapshot()["summary"]

    assert summary["physical_context_count"] == 2
    assert summary["phh_exposure_condition_count"] == 4
    assert summary["reported_assay_volume_value_count"] == 0
    assert summary["active_hepatocyte_exchange_flux_count"] == 0
    assert summary["loaded_exact_protocol_prediction_count"] == 0
    assert summary["automatic_state_coupling_count"] == 0
