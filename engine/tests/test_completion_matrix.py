from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from cell_engine.validation.completion_matrix import (
    build_hepatocyte_completion_matrix,
    validate_hepatocyte_completion_matrix,
)


ROOT = Path(__file__).resolve().parents[2]


def test_completion_matrix_reports_scoped_progress_without_a_realism_percentage() -> None:
    matrix = build_hepatocyte_completion_matrix()
    validate_hepatocyte_completion_matrix(matrix)
    summary = matrix["summary"]
    assert summary["entry_count"] == 27
    assert summary["closed_count"] == 4
    assert summary["partial_count"] == 8
    assert summary["blocked_missing_evidence_count"] == 13
    assert summary["external_action_required_count"] == 1
    assert summary["not_applicable_at_model_scale_count"] == 1
    assert summary["biological_accuracy_pct"] is None


def test_artifact_pin_is_closed_while_fba_and_reaction_activation_remain_blocked() -> None:
    matrix = build_hepatocyte_completion_matrix()
    entries = {entry["id"]: entry for entry in matrix["entries"]}
    assert entries["human_gem_artifact_identity"]["status"] == "closed"
    assert entries["human_gem_artifact_identity"]["observed_metrics"]["runtime_loaded"] is False
    assert entries["hepatocyte_fba_execution"]["status"] == "blocked_missing_evidence"
    assert entries["hepatocyte_fba_execution"]["observed_metrics"]["enabled_execution_gate_count"] == 0
    assert entries["quantitative_reaction_core"]["observed_metrics"]["filled_evidence_slot_count"] == 0


def test_tracers_are_not_misrepresented_as_water_molecules() -> None:
    matrix = build_hepatocyte_completion_matrix()
    entries = {entry["id"]: entry for entry in matrix["entries"]}
    water = entries["explicit_water_molecules"]
    assert water["status"] == "not_applicable_at_model_scale"
    assert water["observed_metrics"]["biological_species_bound_count"] == 0


def test_quantity_harvest_and_injury_evidence_remain_fail_closed() -> None:
    matrix = build_hepatocyte_completion_matrix()
    entries = {entry["id"]: entry for entry in matrix["entries"]}
    harvest = entries["hepatocyte_quantity_harvest"]
    assert harvest["status"] == "partial"
    assert harvest["observed_metrics"]["raw_record_count"] == 168
    assert harvest["observed_metrics"]["promoted_context_bound_claim_count"] == 16
    assert harvest["observed_metrics"]["healthy_phh_runtime_parameter_count"] == 0
    injury = entries["damage_fate_recovery_calibration"]
    assert injury["status"] == "partial"
    assert injury["observed_metrics"]["matching_protocol_observation_count"] == 9
    assert injury["observed_metrics"]["calibrated_fate_commitment_laws"] == 0
    assert injury["observed_metrics"]["runtime_coupled_observation_count"] == 0


def test_completion_matrix_rejects_an_unearned_reaction_promotion() -> None:
    matrix = deepcopy(build_hepatocyte_completion_matrix())
    reaction = next(entry for entry in matrix["entries"] if entry["id"] == "quantitative_reaction_core")
    reaction["observed_metrics"]["filled_evidence_slot_count"] = 1
    with pytest.raises(ValueError, match="reaction evidence"):
        validate_hepatocyte_completion_matrix(matrix)


def test_exported_completion_matrix_is_current() -> None:
    exported = json.loads(
        (ROOT / "data/validation/hepatocyte_completion_matrix.v1.json").read_text(
            encoding="utf-8"
        )
    )
    generated = json.loads(json.dumps(build_hepatocyte_completion_matrix()))
    assert exported == generated
