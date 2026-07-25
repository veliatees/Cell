from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path

import pytest

from cell_engine.quantitative.phh_injury_trajectory import (
    MEASUREMENT_OPERATOR_VERSION,
    PhhInjuryEvaluationAttestation,
    PhhInjuryFrozenSubmission,
    PhhInjuryPredictionPoint,
    PhhInjuryTrajectoryError,
    audit_phh_injury_trajectory_dataset,
    evaluate_frozen_phh_injury_submission,
    load_phh_injury_trajectory_contract,
    load_phh_injury_trajectory_dataset,
    phh_injury_trajectory_intake_snapshot,
)


# These rows are software-integrity probes, not biological measurements.
def _software_row(**updates: str) -> dict[str, str]:
    row = {
        "record_id": "software_record_1",
        "donor_id": "software_donor_1",
        "split_role": "calibration",
        "source_study_id": "software_study_1",
        "source_locator": "software_fixture",
        "species": "Homo sapiens",
        "biological_system": "primary_human_hepatocytes_software_fixture",
        "culture_format": "software_culture",
        "challenge": "software_challenge",
        "challenge_concentration": "1",
        "challenge_concentration_unit": "software_dose_unit",
        "exposure_time_h": "1",
        "endpoint": "software_endpoint",
        "assay": "software_assay",
        "raw_value": "2",
        "raw_unit": "software_readout_unit",
        "biological_replicate_id": "software_replicate_1",
        "normalization_denominator": "software_well",
        "censoring_flag": "none",
        "intervention": "null",
        "intervention_start_h": "null",
        "washout_time_h": "null",
        "recovery_followup_h": "null",
        "technical_replicate_id": "null",
        "uncertainty_type": "null",
        "uncertainty_value": "null",
        "limit_of_quantification": "null",
        "viable_cell_count_at_measurement": "null",
        "fate_label": "null",
    }
    row.update(updates)
    return row


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    contract = load_phh_injury_trajectory_contract()
    fields = [
        *(item["id"] for item in contract["required_columns"]),
        *(item["id"] for item in contract["conditional_columns"]),
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _valid_rows() -> list[dict[str, str]]:
    return [
        _software_row(),
        _software_row(
            record_id="software_record_2",
            donor_id="software_donor_2",
            split_role="internal_validation",
            biological_replicate_id="software_replicate_2",
            exposure_time_h="2",
        ),
        _software_row(
            record_id="software_record_3",
            donor_id="software_donor_3",
            split_role="independent_heldout",
            source_study_id="software_study_heldout",
            biological_replicate_id="software_replicate_3",
            exposure_time_h="3",
            raw_value="2.5",
        ),
    ]


def _prediction_for_heldout(record) -> PhhInjuryPredictionPoint:
    return PhhInjuryPredictionPoint(
        record_id=record.record_id,
        donor_id=record.donor_id,
        source_study_id=record.source_study_id,
        split_role="independent_heldout",
        species=record.species,
        biological_system=record.biological_system,
        culture_format=record.culture_format,
        challenge=record.challenge,
        challenge_concentration=record.challenge_concentration,
        challenge_concentration_unit=record.challenge_concentration_unit,
        exposure_time_h=record.exposure_time_h,
        endpoint=record.endpoint,
        assay=record.assay,
        biological_replicate_id=record.biological_replicate_id,
        technical_replicate_id=record.technical_replicate_id,
        normalization_denominator=record.normalization_denominator,
        intervention=record.intervention,
        intervention_start_h=record.intervention_start_h,
        washout_time_h=record.washout_time_h,
        recovery_followup_h=record.recovery_followup_h,
        predicted_value=3.0,
        predicted_unit=record.raw_unit,
    )


def _submission(dataset, point) -> PhhInjuryFrozenSubmission:
    return PhhInjuryFrozenSubmission(
        submission_id="software_submission",
        model_id="software_model",
        model_artifact_sha256="a" * 64,
        parameter_manifest_sha256="b" * 64,
        dataset_artifact_sha256=dataset.artifact_sha256,
        trajectory_contract_sha256=dataset.contract_sha256,
        source_review_artifact_sha256="c" * 64,
        acceptance_criteria_artifact_sha256="d" * 64,
        measurement_operator_version=MEASUREMENT_OPERATOR_VERSION,
        split_role="independent_heldout",
        frozen_before_heldout_outcome_access=True,
        parameter_refit_count_after_freeze=0,
        points=(point,),
    )


def _attestation() -> PhhInjuryEvaluationAttestation:
    return PhhInjuryEvaluationAttestation(
        manual_primary_source_review_complete=True,
        donor_identity_scope_review_complete=True,
        independent_heldout_study_review_complete=True,
        independent_reviewer_attested=True,
    )


def test_absent_delivery_exposes_ready_guards_without_biological_values(
    tmp_path: Path,
) -> None:
    snapshot = phh_injury_trajectory_intake_snapshot(tmp_path / "missing.csv")
    assert snapshot["status"] == "awaiting_donor_resolved_phh_injury_trajectories"
    assert snapshot["expected_header_count"] == 29
    assert snapshot["split_leakage_guard_enabled"] is True
    assert snapshot["measurement_operator"]["structure_ready"] is True
    assert snapshot["measurement_operator"]["numeric_projection_ready"] is False
    assert snapshot["current_delivery"]["donor_resolved_raw_record_count"] == 0
    assert snapshot["current_delivery"]["independent_heldout_result_count"] == 0


def test_structurally_valid_rows_remain_manual_review_only(tmp_path: Path) -> None:
    path = tmp_path / "phh_injury_trajectories.csv"
    _write_rows(path, _valid_rows())
    dataset = load_phh_injury_trajectory_dataset(path)
    audit = audit_phh_injury_trajectory_dataset(dataset)
    assert audit.status == "structurally_valid_manual_primary_source_review_required"
    assert audit.record_count == 3
    assert audit.donor_count == 3
    assert audit.donor_disjoint_split is True
    assert audit.independent_heldout_study_disjoint is True
    assert audit.manual_primary_source_review_complete is False
    assert audit.automatic_parameter_activation is False
    assert audit.automatic_cell_state_coupling is False


def test_donor_and_heldout_study_leakage_are_rejected(tmp_path: Path) -> None:
    donor_path = tmp_path / "donor_leak.csv"
    donor_rows = _valid_rows()
    donor_rows[1].update(donor_id="software_donor_1")
    _write_rows(donor_path, donor_rows)
    with pytest.raises(PhhInjuryTrajectoryError, match="donor leakage"):
        load_phh_injury_trajectory_dataset(donor_path)

    study_path = tmp_path / "study_leak.csv"
    study_rows = _valid_rows()
    study_rows[2].update(source_study_id="software_study_1")
    _write_rows(study_path, study_rows)
    with pytest.raises(PhhInjuryTrajectoryError, match="source study"):
        load_phh_injury_trajectory_dataset(study_path)


def test_duplicate_observations_and_incomplete_conditionals_are_rejected(
    tmp_path: Path,
) -> None:
    duplicate_path = tmp_path / "duplicate.csv"
    duplicate_rows = _valid_rows()
    duplicate_rows.append(
        {
            **duplicate_rows[0],
            "record_id": "software_record_duplicate",
        }
    )
    _write_rows(duplicate_path, duplicate_rows)
    with pytest.raises(PhhInjuryTrajectoryError, match="duplicate donor"):
        load_phh_injury_trajectory_dataset(duplicate_path)

    conditional_path = tmp_path / "conditional.csv"
    conditional_rows = _valid_rows()
    conditional_rows[0].update(intervention="software_intervention")
    _write_rows(conditional_path, conditional_rows)
    with pytest.raises(PhhInjuryTrajectoryError, match="must appear together"):
        load_phh_injury_trajectory_dataset(conditional_path)


def test_exact_frozen_heldout_projection_returns_residuals_without_a_claim(
    tmp_path: Path,
) -> None:
    path = tmp_path / "phh_injury_trajectories.csv"
    _write_rows(path, _valid_rows())
    dataset = load_phh_injury_trajectory_dataset(path)
    heldout = next(
        record
        for record in dataset.records
        if record.split_role == "independent_heldout"
    )
    result = evaluate_frozen_phh_injury_submission(
        dataset,
        _submission(dataset, _prediction_for_heldout(heldout)),
        _attestation(),
    )
    assert result.evaluated_record_count == 1
    assert result.residuals[0].residual == pytest.approx(0.5)
    assert result.unit_conversion_performed is False
    assert result.time_interpolation_performed is False
    assert result.fitted_parameter_count == 0
    assert result.aggregate_score is None
    assert result.pass_fail_assigned is False
    assert result.predictive_claim_assigned is False
    assert result.may_drive_cell_state is False


def test_projection_rejects_context_drift_and_missing_review(
    tmp_path: Path,
) -> None:
    path = tmp_path / "phh_injury_trajectories.csv"
    _write_rows(path, _valid_rows())
    dataset = load_phh_injury_trajectory_dataset(path)
    heldout = next(
        record
        for record in dataset.records
        if record.split_role == "independent_heldout"
    )
    point = _prediction_for_heldout(heldout)
    mismatched = replace(point, exposure_time_h=point.exposure_time_h + 1.0)
    with pytest.raises(PhhInjuryTrajectoryError, match="context"):
        evaluate_frozen_phh_injury_submission(
            dataset,
            _submission(dataset, mismatched),
            _attestation(),
        )
    incomplete_review = replace(
        _attestation(),
        manual_primary_source_review_complete=False,
    )
    with pytest.raises(PhhInjuryTrajectoryError, match="attestations"):
        evaluate_frozen_phh_injury_submission(
            dataset,
            _submission(dataset, point),
            incomplete_review,
        )
