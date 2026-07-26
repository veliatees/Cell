from __future__ import annotations

import json

import pytest

from cell_engine.quantitative.phh_membrane_topology_event import (
    DEFAULT_CONTRACT_PATH,
    PhhMembraneTopologyEventIntakeError,
    REQUIRED_RECORD_FIELDS,
    phh_membrane_topology_event_intake_snapshot,
    validate_phh_membrane_topology_event_intake_snapshot,
)


def test_empty_membrane_topology_intake_is_explicit_and_fail_closed() -> None:
    snapshot = phh_membrane_topology_event_intake_snapshot()
    validate_phh_membrane_topology_event_intake_snapshot(snapshot)

    assert snapshot["record_count"] == 0
    assert snapshot["healthy_phh_context_record_count"] == 0
    assert snapshot["structurally_complete_record_count"] == 0
    assert snapshot["quantitatively_authorized_record_count"] == 0
    assert snapshot["runtime_topology_activation_allowed"] is False
    assert snapshot["automatic_missing_value_imputation"] is False
    assert snapshot["automatic_event_threshold_fitting"] is False
    assert snapshot["automatic_runtime_activation"] is False
    assert snapshot["required_field_count"] == len(REQUIRED_RECORD_FIELDS)
    assert len(REQUIRED_RECORD_FIELDS) == 57


def test_membrane_topology_intake_rejects_weakened_firewall(
    tmp_path,
) -> None:
    payload = json.loads(DEFAULT_CONTRACT_PATH.read_text(encoding="utf-8"))
    payload["authorization_rules"]["automatic_runtime_activation"] = True
    path = tmp_path / "weakened.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(
        PhhMembraneTopologyEventIntakeError,
        match="firewall was weakened",
    ):
        phh_membrane_topology_event_intake_snapshot(path)


def test_membrane_topology_intake_rejects_partial_record_shapes(
    tmp_path,
) -> None:
    payload = json.loads(DEFAULT_CONTRACT_PATH.read_text(encoding="utf-8"))
    payload["records"] = [
        {
            "record_id": "partial",
            "event_kind": "fission",
        }
    ]
    path = tmp_path / "partial.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(
        PhhMembraneTopologyEventIntakeError,
        match="invalid field set",
    ):
        phh_membrane_topology_event_intake_snapshot(path)
