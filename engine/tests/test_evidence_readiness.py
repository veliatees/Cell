from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from cell_engine.validation.completion_matrix import (
    build_hepatocyte_completion_matrix,
)
from cell_engine.validation.evidence_readiness import (
    REGISTRY_ENTRY_IDS,
    load_phh_evidence_readiness_registry,
    phh_evidence_readiness_snapshot,
    validate_phh_evidence_readiness_registry,
    validate_phh_evidence_readiness_snapshot,
)

ROOT = Path(__file__).resolve().parents[2]


def test_registry_verifies_every_contract_and_stays_fail_closed() -> None:
    snapshot = phh_evidence_readiness_snapshot()
    validate_phh_evidence_readiness_snapshot(snapshot)

    assert tuple(entry["id"] for entry in snapshot["entries"]) == REGISTRY_ENTRY_IDS
    assert snapshot["status"] == "contracts_verified_awaiting_external_evidence"
    assert snapshot["summary"] == {
        "registry_contract_count": 16,
        "contract_identity_verified_count": 16,
        "validator_surface_count": 16,
        "delivery_present_count": 0,
        "delivered_artifact_count": 0,
        "delivered_record_count": 0,
        "structurally_complete_item_count": 0,
        "quantitatively_authorized_item_count": 0,
        "rejected_intake_count": 0,
        "awaiting_intake_count": 16,
        "structurally_audited_intake_count": 0,
        "target_gap_count": 23,
        "automatic_parameter_activation_count": 0,
        "automatic_state_coupling_count": 0,
    }
    assert snapshot["scientific_authority"] is False
    assert snapshot["biological_parameter_activation"] is False


def test_every_registry_target_exists_in_the_completion_matrix() -> None:
    snapshot = phh_evidence_readiness_snapshot()
    completion = build_hepatocyte_completion_matrix()
    evidence_gated_ids = {
        entry["id"]
        for entry in completion["entries"]
        if entry["status"] in {"partial", "blocked_missing_evidence"}
    }

    assert set(snapshot["target_gap_ids"]) == evidence_gated_ids


def test_registry_rejects_contract_identity_drift() -> None:
    registry = deepcopy(load_phh_evidence_readiness_registry())
    registry["entries"][0]["contract_sha256"] = "0" * 64

    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        validate_phh_evidence_readiness_registry(registry)


def test_snapshot_rejects_target_gap_or_automatic_authority_drift() -> None:
    target_drift = deepcopy(phh_evidence_readiness_snapshot())
    target_drift["target_gap_ids"] = (*target_drift["target_gap_ids"], "invented_gap")
    with pytest.raises(ValueError, match="target-gap registry"):
        validate_phh_evidence_readiness_snapshot(target_drift)

    authority_drift = deepcopy(phh_evidence_readiness_snapshot())
    authority_drift["entries"][0]["automatic_parameter_activation"] = True
    with pytest.raises(ValueError, match="automatic model surface"):
        validate_phh_evidence_readiness_snapshot(authority_drift)


def test_one_malformed_delivery_is_quarantined_without_stopping_preflight(
    tmp_path,
) -> None:
    path = (
        tmp_path
        / "phh_energy_redox"
        / "latest"
        / "phh_energy_redox_trajectories.csv"
    )
    path.parent.mkdir(parents=True)
    path.write_text("not,a,valid,contract\n", encoding="utf-8")

    snapshot = phh_evidence_readiness_snapshot(tmp_path)
    by_id = {entry["id"]: entry for entry in snapshot["entries"]}

    assert snapshot["status"] == "delivery_quarantine_active"
    assert snapshot["summary"]["delivery_present_count"] == 1
    assert snapshot["summary"]["rejected_intake_count"] == 1
    assert snapshot["summary"]["awaiting_intake_count"] == 15
    assert by_id["energy_redox_trajectory"]["status"] == "rejected_invalid_delivery"
    assert by_id["energy_redox_trajectory"]["validation_error"]
    assert by_id["energy_redox_trajectory"]["quantitatively_authorized_item_count"] == 0


def test_external_topology_delivery_is_audited_without_repo_relative_path_failure(
    tmp_path,
) -> None:
    registry = load_phh_evidence_readiness_registry()
    topology_entry = next(
        entry
        for entry in registry["entries"]
        if entry["id"] == "membrane_topology_event"
    )
    source = json.loads(
        (ROOT / topology_entry["contract_path"]).read_text(encoding="utf-8")
    )
    delivery = tmp_path / topology_entry["delivery_relative_path"]
    delivery.parent.mkdir(parents=True)
    delivery.write_text(json.dumps(source), encoding="utf-8")

    snapshot = phh_evidence_readiness_snapshot(tmp_path)
    topology = next(
        entry
        for entry in snapshot["entries"]
        if entry["id"] == "membrane_topology_event"
    )

    assert topology["status"] == "delivery_structurally_audited"
    assert topology["delivery_present"] is True
    assert topology["validation_error"] is None
    assert snapshot["summary"]["rejected_intake_count"] == 0
    assert snapshot["summary"]["structurally_audited_intake_count"] == 1
