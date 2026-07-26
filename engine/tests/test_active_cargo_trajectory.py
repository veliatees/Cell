from __future__ import annotations

import csv
from pathlib import Path

import pytest

from cell_engine.quantitative.active_cargo_trajectory import (
    ActiveCargoTrajectoryError,
    active_cargo_trajectory_intake_snapshot,
    assess_active_cargo_route,
    load_active_cargo_trajectory_contract,
    load_active_cargo_trajectory_dataset,
)


# Software-only rows exercise the intake gates and are not measurements.
def _software_row(**updates: str) -> dict[str, str]:
    row = {
        "record_id": "software-frame-0",
        "donor_id": "software-donor-1",
        "split_role": "calibration",
        "source_study_id": "software-study-1",
        "source_locator": "software-movie-frame-0",
        "species": "Homo sapiens",
        "biological_system": "primary_human_hepatocyte_software_fixture",
        "culture_format": "software-culture",
        "trajectory_id": "software-route-1",
        "biological_replicate_id": "software-replicate-1",
        "cargo_identity": "software-vesicle",
        "cargo_labeling_method": "software-label",
        "origin_compartment": "software-origin",
        "destination_compartment": "software-destination",
        "cytoskeletal_track": "microtubule",
        "motor_identity": "not_resolved",
        "frame_index": "0",
        "time_from_trajectory_start_s": "0",
        "position_x_um": "0",
        "position_y_um": "0",
        "position_z_um": "0",
        "position_reference_frame": "software-cell-fixed",
        "localization_uncertainty_um": "0.01",
        "trajectory_sampling_interval_s": "0.1",
        "event_label": "departure",
        "assay": "software-3d-microscopy",
        "cell_viability_context": "software-viable",
        "track_polarity": "null",
        "atp_value": "null",
        "atp_unit": "null",
        "atp_assay": "null",
        "motor_occupancy_value": "null",
        "motor_occupancy_unit": "null",
        "perturbation_identity": "null",
        "perturbation_value": "null",
        "perturbation_unit": "null",
        "fusion_or_fission_partner_id": "null",
        "uncertainty_type": "software-bound",
        "censoring_flag": "none",
    }
    row.update(updates)
    return row


def _complete_rows() -> list[dict[str, str]]:
    return [
        _software_row(),
        _software_row(
            record_id="software-frame-1",
            source_locator="software-movie-frame-1",
            frame_index="1",
            time_from_trajectory_start_s="0.1",
            position_x_um="0.1",
            event_label="in_transit",
        ),
        _software_row(
            record_id="software-frame-2",
            source_locator="software-movie-frame-2",
            frame_index="2",
            time_from_trajectory_start_s="0.2",
            position_x_um="0.2",
            event_label="arrival",
        ),
    ]


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    contract = load_active_cargo_trajectory_contract()
    fields = [
        *(item["id"] for item in contract["required_columns"]),
        *(item["id"] for item in contract["conditional_columns"]),
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_absent_delivery_exposes_gate_without_activating_transport(
    tmp_path: Path,
) -> None:
    snapshot = active_cargo_trajectory_intake_snapshot(tmp_path / "missing.csv")
    assert snapshot["expected_header_count"] == 39
    assert snapshot["record_count"] == 0
    assert snapshot["quantitatively_authorized_route_count"] == 0
    assert snapshot["automatic_velocity_inference"] is False
    assert snapshot["automatic_route_activation"] is False


def test_complete_software_route_is_structural_not_biological_authority(
    tmp_path: Path,
) -> None:
    path = tmp_path / "cargo.csv"
    _write_rows(path, _complete_rows())
    dataset = load_active_cargo_trajectory_dataset(path)
    assessment = assess_active_cargo_route(dataset.records)
    assert assessment.structurally_complete is True
    assert assessment.strictly_increasing_time is True
    assert assessment.quantitative_activation_allowed is False
    assert assessment.automatic_velocity_inference is False
    snapshot = active_cargo_trajectory_intake_snapshot(path)
    assert snapshot["record_count"] == 3
    assert snapshot["structurally_complete_route_count"] == 1
    assert snapshot["quantitatively_authorized_route_count"] == 0


def test_time_and_coordinate_contracts_reject_invalid_3d_routes(
    tmp_path: Path,
) -> None:
    rows = _complete_rows()
    rows[1]["time_from_trajectory_start_s"] = "0"
    path = tmp_path / "time.csv"
    _write_rows(path, rows)
    dataset = load_active_cargo_trajectory_dataset(path)
    assert assess_active_cargo_route(dataset.records).structurally_complete is False

    rows = _complete_rows()
    rows[1]["position_z_um"] = "null"
    _write_rows(path, rows)
    with pytest.raises(ActiveCargoTrajectoryError, match="position_z_um"):
        load_active_cargo_trajectory_dataset(path)


def test_donor_and_independent_study_split_leakage_is_rejected(
    tmp_path: Path,
) -> None:
    rows = _complete_rows()
    rows[-1]["split_role"] = "independent_heldout"
    path = tmp_path / "donor-leak.csv"
    _write_rows(path, rows)
    with pytest.raises(ActiveCargoTrajectoryError, match="donor crosses split"):
        load_active_cargo_trajectory_dataset(path)

    rows = _complete_rows()
    heldout = [
        _software_row(
            record_id=f"heldout-{index}",
            donor_id="software-donor-2",
            trajectory_id="software-route-2",
            split_role="independent_heldout",
            frame_index=str(index),
            time_from_trajectory_start_s=str(index * 0.1),
            event_label=event,
        )
        for index, event in enumerate(("departure", "in_transit", "arrival"))
    ]
    _write_rows(path, [*rows, *heldout])
    with pytest.raises(ActiveCargoTrajectoryError, match="study crosses"):
        load_active_cargo_trajectory_dataset(path)


def test_non_human_or_cell_line_records_cannot_enter_phh_intake(
    tmp_path: Path,
) -> None:
    path = tmp_path / "wrong-context.csv"
    _write_rows(path, [_software_row(species="Rattus norvegicus")])
    with pytest.raises(ActiveCargoTrajectoryError, match="non-human"):
        load_active_cargo_trajectory_dataset(path)
    _write_rows(path, [_software_row(biological_system="HepG2_cell_line")])
    with pytest.raises(ActiveCargoTrajectoryError, match="outside primary human"):
        load_active_cargo_trajectory_dataset(path)
