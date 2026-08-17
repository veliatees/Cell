from __future__ import annotations

import csv
from pathlib import Path

import pytest

from cell_engine.quantitative.energy_redox_trajectory import (
    EnergyRedoxTrajectoryError,
    assess_energy_redox_trajectory,
    energy_redox_trajectory_intake_snapshot,
    load_energy_redox_trajectory_contract,
    load_energy_redox_trajectory_dataset,
)
from cell_engine.validation.evidence_review import EMPTY_FILE_SHA256


# Software-only records exercise intake behavior and are not measurements.
def _software_row(**updates: str) -> dict[str, str]:
    row = {
        "record_id": "software-energy-0",
        "donor_id": "software-dev-donor",
        "split_role": "calibration",
        "source_study_id": "software-dev-study",
        "source_locator": "software-raw-row-0",
        "raw_artifact_sha256": "a" * 64,
        "predeclared_split_manifest_sha256": "b" * 64,
        "data_access_state": "development_open",
        "species": "Homo sapiens",
        "biological_system": "primary_human_hepatocyte_software_fixture",
        "culture_format": "software-sandwich",
        "health_state": "software-healthy",
        "biological_replicate_id": "software-replicate",
        "trajectory_id": "software-atp-dev",
        "pool_id": "atp_cytosol",
        "molecule": "ATP",
        "compartment_id": "cytosol",
        "compartment_targeting_method": "genetically_encoded_compartment_sensor",
        "compartment_targeting_validation": "directly_validated",
        "assay": "software-live-cell-assay",
        "sensor_or_probe": "software-atp-sensor",
        "sensor_calibration_status": "same_assay_calibrated",
        "time_from_trajectory_start_s": "0",
        "reported_value": "1",
        "reported_unit": "software-unit",
        "measurement_kind": "calibrated_ratio",
        "reported_statistic": "software-raw",
        "uncertainty_value": "0.1",
        "uncertainty_unit": "software-unit",
        "uncertainty_type": "software-bound",
        "sample_size": "1",
        "extracellular_oxygen_value": "10",
        "extracellular_oxygen_unit": "software-oxygen-unit",
        "nutrient_context": "software-complete-medium",
        "cell_viability_context": "software-viable",
        "position_or_region_context": "software-cell-region",
        "assay_temperature_c": "37",
        "assay_ph": "7.4",
        "perturbation_identity": "null",
        "perturbation_value": "null",
        "perturbation_unit": "null",
        "baseline_definition": "software-baseline",
        "censoring_or_missingness": "none",
        "simultaneous_measurement_group_id": "software-group",
        "intracellular_volume_value": "null",
        "intracellular_volume_unit": "null",
        "notes": "software-only",
    }
    row.update(updates)
    return row


def _trajectory_rows(*, heldout: bool = False) -> list[dict[str, str]]:
    common = {
        "donor_id": "software-heldout-donor" if heldout else "software-dev-donor",
        "split_role": "independent_heldout" if heldout else "calibration",
        "source_study_id": "software-heldout-study" if heldout else "software-dev-study",
        "data_access_state": "sealed_heldout" if heldout else "development_open",
        "trajectory_id": "software-atp-heldout" if heldout else "software-atp-dev",
    }
    return [
        _software_row(
            **common,
            record_id=f"{'heldout' if heldout else 'dev'}-energy-{index}",
            source_locator=f"software-raw-row-{index}",
            time_from_trajectory_start_s=str(index),
            reported_value=str(1 + index * 0.1),
        )
        for index in range(3)
    ]


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    contract = load_energy_redox_trajectory_contract()
    fields = [
        *(item["id"] for item in contract["required_columns"]),
        *(item["id"] for item in contract["conditional_columns"]),
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_absent_delivery_keeps_all_38_pools_null(tmp_path: Path) -> None:
    snapshot = energy_redox_trajectory_intake_snapshot(tmp_path / "missing.csv")
    assert snapshot["expected_header_count"] == 47
    assert snapshot["registered_pool_count"] == 38
    assert snapshot["record_count"] == 0
    assert snapshot["compartment_initialization_allowed_count"] == 0
    assert snapshot["rate_fitting_allowed_count"] == 0


def test_calibration_and_heldout_software_trajectories_are_structural_only(
    tmp_path: Path,
) -> None:
    path = tmp_path / "energy-redox.csv"
    _write_rows(path, [*_trajectory_rows(), *_trajectory_rows(heldout=True)])
    dataset = load_energy_redox_trajectory_dataset(path)
    development = tuple(
        record for record in dataset.records if record.split_role == "calibration"
    )
    assessment = assess_energy_redox_trajectory(development)
    assert assessment.structurally_complete is True
    assert assessment.compartment_initialization_allowed is False
    assert assessment.rate_fitting_allowed is False
    snapshot = energy_redox_trajectory_intake_snapshot(path)
    assert snapshot["trajectory_count"] == 2
    assert snapshot["structurally_complete_trajectory_count"] == 0
    assert snapshot["calibration_and_heldout_complete_pool_count"] == 0
    assert snapshot["delivery_review"]["approved_for_structural_credit"] is False
    assert snapshot["compartment_initialization_allowed_count"] == 0


def test_pool_mapping_and_phh_context_are_strict(tmp_path: Path) -> None:
    path = tmp_path / "invalid.csv"
    _write_rows(path, [_software_row(molecule="ADP")])
    with pytest.raises(EnergyRedoxTrajectoryError, match="do not match"):
        load_energy_redox_trajectory_dataset(path)

    _write_rows(path, [_software_row(biological_system="HepG2_cell_line")])
    with pytest.raises(EnergyRedoxTrajectoryError, match="outside primary human"):
        load_energy_redox_trajectory_dataset(path)


def test_empty_raw_artifact_digest_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "empty-artifact.csv"
    rows = _trajectory_rows()
    rows[0]["raw_artifact_sha256"] = EMPTY_FILE_SHA256
    _write_rows(path, rows)

    with pytest.raises(EnergyRedoxTrajectoryError, match="non-empty artifact"):
        load_energy_redox_trajectory_dataset(path)


def test_split_manifest_and_heldout_sealing_prevent_leakage(
    tmp_path: Path,
) -> None:
    path = tmp_path / "leak.csv"
    _write_rows(
        path,
        [_software_row(split_role="independent_heldout", data_access_state="development_open")],
    )
    with pytest.raises(EnergyRedoxTrajectoryError, match="access state"):
        load_energy_redox_trajectory_dataset(path)

    heldout = _trajectory_rows(heldout=True)
    for row in heldout:
        row["source_study_id"] = "software-dev-study"
        row["donor_id"] = "software-dev-donor"
    _write_rows(path, [*_trajectory_rows(), *heldout])
    with pytest.raises(EnergyRedoxTrajectoryError, match="donor crosses split"):
        load_energy_redox_trajectory_dataset(path)


def test_uncalibrated_or_unvalidated_trajectory_never_becomes_structural(
    tmp_path: Path,
) -> None:
    rows = _trajectory_rows()
    for row in rows:
        row["sensor_calibration_status"] = "uncalibrated"
        row["compartment_targeting_validation"] = "reported_not_independently_validated"
    path = tmp_path / "unready.csv"
    _write_rows(path, rows)
    dataset = load_energy_redox_trajectory_dataset(path)
    assessment = assess_energy_redox_trajectory(dataset.records)
    assert assessment.structurally_complete is False
    assert assessment.same_assay_calibrated is False
    assert assessment.compartment_targeting_ready is False
