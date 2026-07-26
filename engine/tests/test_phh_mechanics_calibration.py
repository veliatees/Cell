from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from cell_engine.quantitative.phh_mechanics_calibration import (
    CONTRACT_PATH,
    PHHMechanicsCalibrationError,
    assess_phh_mechanics_trajectory,
    load_phh_mechanics_calibration_contract,
    load_phh_mechanics_calibration_dataset,
    phh_mechanics_calibration_intake_snapshot,
    validate_phh_mechanics_calibration_intake_snapshot,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _header() -> list[str]:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    return [
        item["id"]
        for group in ("required_columns", "conditional_columns")
        for item in contract[group]
    ]


def _base_row(
    raw_path: Path,
    *,
    index: int,
    stage: str,
    time_s: float,
    study: str = "study-cal",
    donor: str = "donor-1",
    split: str = "calibration",
    trajectory: str = "trajectory-1",
) -> dict[str, str]:
    row = {field: "null" for field in _header()}
    row.update(
        {
            "record_id": f"{study}-{donor}-{trajectory}-{index}",
            "donor_id": donor,
            "source_study_id": study,
            "source_locator": "supplementary-data:row-1",
            "split_role": split,
            "species": "Homo sapiens",
            "biological_system": "primary_human_hepatocyte_freshly_isolated",
            "tissue_health_state": "healthy_non_diseased",
            "preparation_context": "freshly_isolated",
            "culture_format": "single_cell_suspension_assayed_immediately",
            "liver_zone": "unresolved",
            "nutritional_state": "source_reported_fed_state",
            "temperature_c": "37",
            "medium_composition": "source-defined buffer; osmolarity reported",
            "biological_replicate_id": f"{donor}-rep-1",
            "cell_id": f"{donor}-cell-1",
            "assay_id": f"{study}-assay-1",
            "trajectory_id": trajectory,
            "record_kind": "raw_observation",
            "assay_type": "pressure_relaxation",
            "stage": stage,
            "timepoint_index": str(index),
            "time_from_assay_start_s": str(time_s),
            "measured_quantity_id": "normal_displacement",
            "value": str(0.1 * index),
            "unit": "um",
            "measurement_method": "source-calibrated imaging displacement",
            "coordinate_frame": "cell_fixed_xyz",
            "membrane_domain": "whole_cell",
            "uncertainty_value": "0.01",
            "uncertainty_type": "instrument_error",
            "raw_artifact_path": str(raw_path),
            "raw_artifact_sha256": _sha256(raw_path),
            "cell_viability_context": "membrane integrity reported before and after assay",
            "manual_primary_source_review_status": "pass",
            "stimulus_identity": "pressure_step",
            "stimulus_value": "10",
            "stimulus_unit": "Pa",
            "loading_axis": "positive_x",
            "boundary_condition_description": "source-declared pressure and free surface",
            "paired_mesh_record_id": f"{donor}-cell-1-mesh",
        }
    )
    return row


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=_header())
        writer.writeheader()
        writer.writerows(rows)


def test_contract_and_empty_snapshot_remain_fail_closed(tmp_path: Path) -> None:
    contract = load_phh_mechanics_calibration_contract()
    assert contract["contract_id"] == "phh_mechanics_calibration_contract_v1"
    assert len(contract["required_columns"]) == 35
    assert len(contract["conditional_columns"]) == 13

    snapshot = phh_mechanics_calibration_intake_snapshot(tmp_path / "missing.csv")
    validate_phh_mechanics_calibration_intake_snapshot(snapshot)
    assert snapshot["expected_header_count"] == 48
    assert snapshot["target_quantity_count"] == 15
    assert snapshot["record_count"] == 0
    assert snapshot["mechanics_coupling_allowed"] is False


def test_complete_raw_trajectory_is_structurally_ready_but_not_authoritative(
    tmp_path: Path,
) -> None:
    raw = tmp_path / "raw.csv"
    raw.write_text("time,displacement\n0,0\n1,0.2\n2,0.1\n", encoding="utf-8")
    delivery = tmp_path / "mechanics.csv"
    rows = [
        _base_row(raw, index=0, stage="baseline", time_s=0),
        _base_row(raw, index=1, stage="loading", time_s=1),
        _base_row(raw, index=2, stage="relaxation", time_s=2),
    ]
    _write_csv(delivery, rows)

    dataset = load_phh_mechanics_calibration_dataset(delivery)
    assessment = assess_phh_mechanics_trajectory(dataset.records)
    snapshot = phh_mechanics_calibration_intake_snapshot(delivery)
    validate_phh_mechanics_calibration_intake_snapshot(snapshot)

    assert assessment.structurally_complete is True
    assert assessment.spatial_fsi_ready is True
    assert assessment.quantitative_activation_allowed is False
    assert snapshot["structurally_complete_trajectory_count"] == 1
    assert snapshot["spatial_fsi_ready_trajectory_count"] == 1
    assert snapshot["quantitatively_authorized_parameter_count"] == 0
    assert snapshot["automatic_runtime_coupling"] is False


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("species", "Mus musculus", "non-human mechanics"),
        ("biological_system", "HepG2", "outside primary human hepatocytes"),
        ("unit", "nm", "must use canonical unit"),
        ("manual_primary_source_review_status", "pending", "must be pass"),
    ),
)
def test_context_and_unit_mismatches_are_rejected(
    tmp_path: Path,
    field: str,
    value: str,
    message: str,
) -> None:
    raw = tmp_path / "raw.csv"
    raw.write_text("raw\n", encoding="utf-8")
    row = _base_row(raw, index=0, stage="baseline", time_s=0)
    row[field] = value
    delivery = tmp_path / "invalid.csv"
    _write_csv(delivery, [row])

    with pytest.raises(PHHMechanicsCalibrationError, match=message):
        load_phh_mechanics_calibration_dataset(delivery)


def test_artifact_checksum_and_parameter_provenance_are_required(
    tmp_path: Path,
) -> None:
    raw = tmp_path / "raw.csv"
    raw.write_text("raw\n", encoding="utf-8")
    checksum_row = _base_row(raw, index=0, stage="baseline", time_s=0)
    checksum_row["raw_artifact_sha256"] = "0" * 64
    checksum_delivery = tmp_path / "bad-checksum.csv"
    _write_csv(checksum_delivery, [checksum_row])
    with pytest.raises(PHHMechanicsCalibrationError, match="SHA-256 mismatch"):
        load_phh_mechanics_calibration_dataset(checksum_delivery)

    parameter_row = _base_row(raw, index=0, stage="baseline", time_s=0)
    parameter_row.update(
        {
            "record_kind": "reported_parameter",
            "stage": "derived_parameter",
            "measured_quantity_id": "membrane_tension",
            "unit": "N/m",
        }
    )
    parameter_delivery = tmp_path / "bad-parameter.csv"
    _write_csv(parameter_delivery, [parameter_row])
    with pytest.raises(PHHMechanicsCalibrationError, match="provenance is incomplete"):
        load_phh_mechanics_calibration_dataset(parameter_delivery)


def test_donor_and_independent_study_split_leakage_are_rejected(
    tmp_path: Path,
) -> None:
    raw = tmp_path / "raw.csv"
    raw.write_text("raw\n", encoding="utf-8")
    donor_rows = [
        _base_row(raw, index=0, stage="baseline", time_s=0),
        _base_row(
            raw,
            index=0,
            stage="baseline",
            time_s=0,
            split="internal_validation",
            trajectory="trajectory-2",
        ),
    ]
    donor_delivery = tmp_path / "donor-leak.csv"
    _write_csv(donor_delivery, donor_rows)
    with pytest.raises(PHHMechanicsCalibrationError, match="donor crosses split"):
        load_phh_mechanics_calibration_dataset(donor_delivery)

    study_rows = [
        _base_row(raw, index=0, stage="baseline", time_s=0),
        _base_row(
            raw,
            index=0,
            stage="baseline",
            time_s=0,
            donor="donor-2",
            split="independent_heldout",
            trajectory="trajectory-2",
        ),
    ]
    study_delivery = tmp_path / "study-leak.csv"
    _write_csv(study_delivery, study_rows)
    with pytest.raises(PHHMechanicsCalibrationError, match="study crosses development"):
        load_phh_mechanics_calibration_dataset(study_delivery)
