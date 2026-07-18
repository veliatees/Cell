from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from cell_engine.quantitative.phh_spheroid_protocol import (
    PhhSpheroidModelPrediction,
    PhhSpheroidPredictionWindow,
    build_phh_spheroid_validation_protocol,
    compare_phh_spheroid_prediction,
    match_phh_spheroid_prediction,
    phh_spheroid_validation_protocol_snapshot,
    validate_phh_spheroid_validation_protocol,
)


def _exact_software_fixture_prediction() -> PhhSpheroidModelPrediction:
    protocol = build_phh_spheroid_validation_protocol()
    return PhhSpheroidModelPrediction(
        prediction_set_id="unit_test_only_exact_protocol_fixture",
        model_id="software_contract_test_not_a_scientific_model",
        model_artifact_sha256=hashlib.sha256(b"software contract test fixture").hexdigest(),
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
            PhhSpheroidPredictionWindow(
                condition_id=target.condition_id,
                time_start_h=target.time_start_h,
                time_end_h=target.time_end_h,
                predicted_mean_fmol_per_cell_h=target.observed_mean_fmol_per_cell_h,
            )
            for target in protocol.window_targets
        ),
    )


def test_method_contract_preserves_reported_values_and_unknowns() -> None:
    protocol = build_phh_spheroid_validation_protocol()
    method = protocol.method_contract

    assert method.seeded_viable_cells_per_well == 1500
    assert method.culture_seeding_medium_volume_uL == 100.0
    assert method.assay_sample_supernatant_volume_uL == 10.0
    assert method.assay_replication_count == 2
    assert method.glucose_challenge_initial_medium_volume_uL is None
    assert method.remaining_medium_volume_schedule_uL is None
    assert method.volumetric_factor_VF is None
    assert method.viable_cell_count_at_each_observation_window is None
    assert not protocol.medium_concentration_trajectory_reconstruction_ready
    assert not protocol.vectorial_flux_decomposition_ready


def test_nonoverlapping_windows_form_cumulative_mean_targets_without_invented_sd() -> None:
    protocol = build_phh_spheroid_validation_protocol()
    trajectories = {item.condition_id: item for item in protocol.cumulative_target_trajectories}

    assert [point.time_h for point in trajectories["hi_hg"].points] == [0.0, 6.0, 24.0, 72.0]
    assert [point.cumulative_mean_fmol_per_seeded_cell for point in trajectories["hi_hg"].points] == pytest.approx(
        [0.0, 60.0, 123.0, 190.2]
    )
    assert [point.cumulative_mean_fmol_per_seeded_cell for point in trajectories["li_hg"].points] == pytest.approx(
        [0.0, 59.4, 122.4, 184.8]
    )
    assert [point.cumulative_mean_fmol_per_seeded_cell for point in trajectories["hi_lg"].points] == pytest.approx(
        [0.0, 36.6, 79.8, 123.0]
    )
    assert [point.cumulative_mean_fmol_per_seeded_cell for point in trajectories["li_lg"].points] == pytest.approx(
        [0.0, 18.0, 39.6, 58.8]
    )
    assert all(point.cumulative_sd_fmol_per_seeded_cell is None for item in trajectories.values() for point in item.points)
    assert all(not item.combined_cumulative_uncertainty_available for item in trajectories.values())


def test_overlapping_rows_are_descriptive_consistency_audits_not_extra_scores() -> None:
    protocol = build_phh_spheroid_validation_protocol()
    audits = {item.condition_id: item for item in protocol.overlap_consistency_audits}

    assert audits["hi_hg"].derived_time_weighted_mean_fmol_per_cell_h == pytest.approx(2.6416666666666666)
    assert audits["hi_hg"].rate_residual_reported_minus_derived_fmol_per_cell_h == pytest.approx(-0.0416666666666665)
    assert audits["hi_hg"].cumulative_residual_reported_minus_derived_fmol_per_seeded_cell == pytest.approx(-3.0)
    assert audits["li_hg"].cumulative_residual_reported_minus_derived_fmol_per_seeded_cell == pytest.approx(2.4)
    assert audits["hi_lg"].cumulative_residual_reported_minus_derived_fmol_per_seeded_cell == pytest.approx(-0.6)
    assert audits["li_lg"].cumulative_residual_reported_minus_derived_fmol_per_seeded_cell == pytest.approx(-1.2)
    assert all(item.acceptance_threshold is None and not item.pass_fail_assigned for item in audits.values())


def test_exact_protocol_prediction_can_be_compared_without_assigning_pass_fail() -> None:
    protocol = build_phh_spheroid_validation_protocol()
    prediction = _exact_software_fixture_prediction()
    audit = match_phh_spheroid_prediction(protocol, prediction)
    comparison = compare_phh_spheroid_prediction(protocol, prediction)

    assert audit.exact_protocol_match
    assert len(comparison.residuals) == 16
    assert sum(item.independent_trajectory_target for item in comparison.residuals) == 12
    assert all(item.predicted_minus_observed_fmol_per_cell_h == 0 for item in comparison.residuals)
    assert comparison.aggregate_score is None
    assert comparison.acceptance_threshold is None
    assert not comparison.pass_fail_assigned
    assert not comparison.may_drive_cell_state


@pytest.mark.parametrize(
    ("field", "value", "blocker"),
    (
        ("unit", "umol_per_kg_body_mass_per_min", "quantity, sign or unit differs"),
        ("cell_format", "whole_liver_in_vivo", "species, PHH spheroid format or health context differs"),
        ("denominator", "viable_cells_measured_at_each_window", "seeded-cell denominator differs"),
    ),
)
def test_wrong_scale_unit_or_denominator_fails_closed(field: str, value: str, blocker: str) -> None:
    protocol = build_phh_spheroid_validation_protocol()
    prediction = replace(_exact_software_fixture_prediction(), **{field: value})
    audit = match_phh_spheroid_prediction(protocol, prediction)

    assert not audit.exact_protocol_match
    assert blocker in audit.blockers
    with pytest.raises(ValueError, match="does not exactly match"):
        compare_phh_spheroid_prediction(protocol, prediction)


def test_transcribed_25_mM_or_zero_glucagon_condition_is_rejected() -> None:
    protocol = build_phh_spheroid_validation_protocol()
    prediction = _exact_software_fixture_prediction()
    altered_conditions = tuple(
        replace(condition, glucose_mM=25.0) if condition.id == "hi_hg" else condition
        for condition in prediction.conditions
    )
    audit = match_phh_spheroid_prediction(protocol, replace(prediction, conditions=altered_conditions))
    assert not audit.exposure_matrix_match

    zeroed_glucagon = tuple(
        replace(condition, glucagon_nM=0.0, glucagon_status="assumed_zero") if condition.id == "hi_hg" else condition
        for condition in prediction.conditions
    )
    audit = match_phh_spheroid_prediction(protocol, replace(prediction, conditions=zeroed_glucagon))
    assert not audit.exposure_matrix_match


def test_missing_or_duplicate_window_is_rejected() -> None:
    protocol = build_phh_spheroid_validation_protocol()
    prediction = _exact_software_fixture_prediction()

    assert not match_phh_spheroid_prediction(protocol, replace(prediction, windows=prediction.windows[:-1])).window_matrix_match
    duplicated = prediction.windows[:-1] + (prediction.windows[0],)
    assert not match_phh_spheroid_prediction(protocol, replace(prediction, windows=duplicated)).window_matrix_match


def test_protocol_validation_rejects_invented_reconstruction_or_threshold() -> None:
    protocol = build_phh_spheroid_validation_protocol()

    with pytest.raises(ValueError, match="gates exceeded"):
        validate_phh_spheroid_validation_protocol(
            replace(protocol, medium_concentration_trajectory_reconstruction_ready=True)
        )
    with pytest.raises(ValueError, match="gates exceeded"):
        validate_phh_spheroid_validation_protocol(replace(protocol, acceptance_threshold=1.0))  # type: ignore[arg-type]


def test_snapshot_discloses_zero_predictions_and_zero_pass_fail_results() -> None:
    snapshot = phh_spheroid_validation_protocol_snapshot()
    summary = snapshot["summary"]

    assert summary["measured_window_count"] == 16
    assert summary["independent_trajectory_target_count"] == 12
    assert summary["overlap_consistency_audit_count"] == 4
    assert summary["submitted_model_prediction_count"] == 0
    assert summary["exact_protocol_comparison_count"] == 0
    assert summary["pass_fail_count"] == 0
    assert summary["medium_concentration_trajectory_count"] == 0
