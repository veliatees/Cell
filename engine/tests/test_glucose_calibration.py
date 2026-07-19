from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from cell_engine.quantitative.glucose_open_system import (
    PhhSignedWindowFlux,
    PhhWindowFluxPredictionSet,
)
from cell_engine.quantitative.phh_spheroid_protocol import build_phh_spheroid_validation_protocol
from cell_engine.validation.glucose_calibration import (
    GlucoseCalibrationError,
    assert_glucose_predictive_activation,
    assert_glucose_reaction_fit_allowed,
    build_glucose_calibration_validation_gate,
    evaluate_descriptive_phh_glucose_submission,
    glucose_calibration_validation_snapshot,
    validate_glucose_calibration_validation_gate,
)


def _software_fixture_submission() -> PhhWindowFluxPredictionSet:
    protocol = build_phh_spheroid_validation_protocol()
    return PhhWindowFluxPredictionSet(
        prediction_set_id="unit_test_only_descriptive_submission",
        model_id="software_validation_test_not_a_scientific_model",
        model_artifact_sha256=hashlib.sha256(b"calibration gate software fixture").hexdigest(),
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
                item.condition_id,
                item.time_start_h,
                item.time_end_h,
                item.observed_mean_fmol_per_cell_h,
            )
            for item in protocol.window_targets
            if item.independent_trajectory_target
        ),
    )


def test_every_active_reaction_is_audited_and_none_is_fit_eligible() -> None:
    gate = build_glucose_calibration_validation_gate()
    validate_glucose_calibration_validation_gate(gate)

    assert len(gate.reaction_fit_eligibility) == 36
    assert sum(item.published_candidate_present for item in gate.reaction_fit_eligibility) == 12
    assert sum(item.exact_stoichiometry_match for item in gate.reaction_fit_eligibility) == 3
    assert not any(item.aggregate_endpoint_identifies_rate for item in gate.reaction_fit_eligibility)
    assert not any(item.source_parameter_transfer_allowed for item in gate.reaction_fit_eligibility)
    assert not any(item.fit_allowed for item in gate.reaction_fit_eligibility)


def test_observation_roles_do_not_turn_overlap_or_pooled_data_into_holdout() -> None:
    gate = build_glucose_calibration_validation_gate()
    independent = [
        item
        for item in gate.observation_use_audit
        if item.role == "same_format_nonoverlapping_validation_target"
    ]
    overlaps = [
        item
        for item in gate.observation_use_audit
        if item.role == "descriptive_overlapping_consistency_audit"
    ]

    assert len(independent) == 12
    assert len(overlaps) == 4
    assert all(item.same_format_comparison_allowed for item in gate.observation_use_audit)
    assert not any(item.may_fit_kinetic_parameter for item in gate.observation_use_audit)
    assert not any(item.independent_heldout_eligible for item in gate.observation_use_audit)


def test_all_predictive_requirements_remain_explicit_and_unsatisfied() -> None:
    gate = build_glucose_calibration_validation_gate()
    requirements = {item.id: item for item in gate.validation_requirements}

    assert set(requirements) == {
        "exact_protocol_model_prediction",
        "donor_resolved_numeric_trajectories",
        "donor_disjoint_partition",
        "mechanism_identifying_measurements",
        "window_specific_normalization",
        "uncertainty_and_covariance",
        "independent_heldout_result",
    }
    assert not any(item.satisfied for item in requirements.values())
    assert gate.same_format_descriptive_comparison_ready
    assert not gate.kinetic_parameter_calibration_ready
    assert not gate.independent_heldout_validation_ready
    assert not gate.predictive_parameter_activation_allowed
    assert not gate.predictive_ready


def test_exact_submission_receives_descriptive_residuals_only() -> None:
    evaluation = evaluate_descriptive_phh_glucose_submission(_software_fixture_submission())

    assert evaluation.evaluated_window_count == 16
    assert evaluation.independent_target_count == 12
    assert evaluation.descriptive_overlap_count == 4
    assert evaluation.fitted_parameter_count == 0
    assert evaluation.heldout_result_count == 0
    assert evaluation.aggregate_score is None
    assert evaluation.acceptance_threshold is None
    assert not evaluation.pass_fail_assigned
    assert not evaluation.may_drive_cell_state


def test_fit_and_predictive_activation_fail_closed() -> None:
    gate = build_glucose_calibration_validation_gate()

    with pytest.raises(GlucoseCalibrationError, match="aggregate PHH medium endpoint"):
        assert_glucose_reaction_fit_allowed("glucose_export", gate)
    with pytest.raises(GlucoseCalibrationError, match="predictive glucose activation blocked"):
        assert_glucose_predictive_activation(gate)
    with pytest.raises(KeyError):
        assert_glucose_reaction_fit_allowed("not_a_reaction", gate)


def test_descriptive_evaluation_rejects_protocol_mismatch() -> None:
    submission = _software_fixture_submission()
    with pytest.raises(GlucoseCalibrationError, match="does not match"):
        evaluate_descriptive_phh_glucose_submission(
            replace(submission, seeded_viable_cells_per_spheroid=1499)
        )


def test_calibration_snapshot_reports_zero_fit_holdout_and_activation() -> None:
    summary = glucose_calibration_validation_snapshot()["summary"]

    assert summary["audited_reaction_count"] == 36
    assert summary["fit_eligible_reaction_count"] == 0
    assert summary["reported_observation_count"] == 16
    assert summary["same_format_nonoverlapping_target_count"] == 12
    assert summary["descriptive_overlap_count"] == 4
    assert summary["satisfied_validation_requirement_count"] == 0
    assert summary["independent_heldout_result_count"] == 0
    assert summary["activated_parameter_count"] == 0
    assert summary["pass_fail_count"] == 0
