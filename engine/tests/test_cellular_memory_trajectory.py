from __future__ import annotations

import csv
from pathlib import Path

import pytest

from cell_engine.processes.cellular_memory import MEMORY_SUBSTRATE_CONTRACTS
from cell_engine.quantitative.cellular_memory_trajectory import (
    CellularMemoryTrajectoryError,
    assess_memory_law_candidate,
    cellular_memory_trajectory_intake_snapshot,
    load_cellular_memory_trajectory_contract,
    load_cellular_memory_trajectory_dataset,
)


SUBSTRATE_IDS = tuple(item.id for item in MEMORY_SUBSTRATE_CONTRACTS)


# These rows exercise software gates and are not biological measurements.
def _software_row(**updates: str) -> dict[str, str]:
    row = {
        "record_id": "software-baseline",
        "donor_id": "software-donor-1",
        "split_role": "calibration",
        "source_study_id": "software-study-1",
        "source_locator": "software-fixture",
        "species": "Homo sapiens",
        "biological_system": "primary_human_hepatocyte_software_fixture",
        "culture_format": "software-culture",
        "substrate_contract_id": "histone_or_chromatin",
        "compartment": "nucleus",
        "locus_or_entity": "software-locus",
        "trajectory_id": "software-trajectory-1",
        "trajectory_phase": "baseline",
        "measurement_role": "physical_substrate",
        "trigger_identity": "software-trigger",
        "elapsed_from_trigger_start_h": "0",
        "assay": "software-substrate-assay",
        "readout": "software-substrate-readout",
        "raw_value": "1",
        "raw_unit": "software-substrate-unit",
        "biological_replicate_id": "software-replicate-1",
        "normalization_denominator": "software-denominator",
        "trigger_value": "null",
        "trigger_unit": "null",
        "trigger_removal_time_h": "null",
        "elapsed_from_trigger_removal_h": "null",
        "rechallenge_identity": "null",
        "rechallenge_value": "null",
        "rechallenge_unit": "null",
        "cell_generation": "null",
        "parent_cell_id": "null",
        "uncertainty_type": "null",
        "uncertainty_value": "null",
        "censoring_flag": "none",
    }
    row.update(updates)
    return row


def _complete_candidate_rows() -> list[dict[str, str]]:
    return [
        _software_row(),
        _software_row(
            record_id="software-write",
            trajectory_phase="write",
            elapsed_from_trigger_start_h="2",
            raw_value="2",
        ),
        _software_row(
            record_id="software-persistence",
            trajectory_phase="persistence_followup",
            elapsed_from_trigger_start_h="8",
            trigger_removal_time_h="4",
            elapsed_from_trigger_removal_h="4",
            raw_value="1.8",
        ),
        _software_row(
            record_id="software-first-response",
            trajectory_phase="first_challenge_response",
            measurement_role="future_response",
            elapsed_from_trigger_start_h="3",
            assay="software-response-assay",
            readout="software-response-readout",
            raw_unit="software-response-unit",
            raw_value="5",
        ),
        _software_row(
            record_id="software-rechallenge-response",
            trajectory_phase="rechallenge_response",
            measurement_role="future_response",
            elapsed_from_trigger_start_h="10",
            assay="software-response-assay",
            readout="software-response-readout",
            raw_unit="software-response-unit",
            raw_value="7",
            rechallenge_identity="software-trigger",
        ),
    ]


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    contract = load_cellular_memory_trajectory_contract(
        allowed_substrate_ids=SUBSTRATE_IDS
    )
    fields = [
        *(item["id"] for item in contract["required_columns"]),
        *(item["id"] for item in contract["conditional_columns"]),
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_absent_delivery_exposes_the_complete_gate_without_activating_memory(
    tmp_path: Path,
) -> None:
    snapshot = cellular_memory_trajectory_intake_snapshot(
        allowed_substrate_ids=SUBSTRATE_IDS,
        path=tmp_path / "missing.csv",
    )
    assert snapshot["status"] == "awaiting_donor_resolved_phh_memory_trajectories"
    assert snapshot["expected_header_count"] == 34
    assert snapshot["write_persist_rechallenge_gate_count"] == 1
    assert snapshot["record_count"] == 0
    assert snapshot["quantitatively_authorized_memory_law_count"] == 0
    assert snapshot["automatic_memory_trace_creation"] is False
    assert snapshot["automatic_future_response_coupling"] is False


def test_complete_software_trajectory_is_structural_not_biological_authority(
    tmp_path: Path,
) -> None:
    path = tmp_path / "memory.csv"
    _write_rows(path, _complete_candidate_rows())
    dataset = load_cellular_memory_trajectory_dataset(
        path,
        allowed_substrate_ids=SUBSTRATE_IDS,
    )
    assessment = assess_memory_law_candidate(dataset.records)
    assert assessment.structurally_complete is True
    assert assessment.verified_trigger_removal is True
    assert assessment.same_physical_carrier_assay is True
    assert assessment.same_response_assay is True
    assert assessment.quantitative_activation_allowed is False
    assert assessment.automatic_memory_trace_creation is False
    assert assessment.automatic_future_response_coupling is False
    assert "frozen write/read/decay model artifact is absent" in assessment.blockers

    snapshot = cellular_memory_trajectory_intake_snapshot(
        allowed_substrate_ids=SUBSTRATE_IDS,
        path=path,
    )
    assert snapshot["record_count"] == 5
    assert snapshot["structurally_complete_candidate_count"] == 1
    assert snapshot["quantitatively_authorized_memory_law_count"] == 0


def test_persistence_phase_without_verified_trigger_removal_is_rejected(
    tmp_path: Path,
) -> None:
    rows = _complete_candidate_rows()
    rows[2]["trigger_removal_time_h"] = "null"
    path = tmp_path / "missing-removal.csv"
    _write_rows(path, rows)
    with pytest.raises(
        CellularMemoryTrajectoryError,
        match="persistence requires verified trigger-removal timing",
    ):
        load_cellular_memory_trajectory_dataset(
            path,
            allowed_substrate_ids=SUBSTRATE_IDS,
        )


def test_one_donor_cannot_cross_calibration_and_heldout_splits(
    tmp_path: Path,
) -> None:
    rows = _complete_candidate_rows()
    rows[-1]["split_role"] = "independent_heldout"
    path = tmp_path / "leakage.csv"
    _write_rows(path, rows)
    with pytest.raises(CellularMemoryTrajectoryError, match="crosses split roles"):
        load_cellular_memory_trajectory_dataset(
            path,
            allowed_substrate_ids=SUBSTRATE_IDS,
        )


def test_non_phh_and_unknown_substrate_rows_are_rejected(tmp_path: Path) -> None:
    wrong_system = _software_row(biological_system="whole_liver_bulk")
    path = tmp_path / "wrong-system.csv"
    _write_rows(path, [wrong_system])
    with pytest.raises(CellularMemoryTrajectoryError, match="outside primary human"):
        load_cellular_memory_trajectory_dataset(
            path,
            allowed_substrate_ids=SUBSTRATE_IDS,
        )

    wrong_substrate = _software_row(substrate_contract_id="generic_stress_score")
    _write_rows(path, [wrong_substrate])
    with pytest.raises(CellularMemoryTrajectoryError, match="unknown substrate"):
        load_cellular_memory_trajectory_dataset(
            path,
            allowed_substrate_ids=SUBSTRATE_IDS,
        )
