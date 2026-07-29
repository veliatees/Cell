from __future__ import annotations

import json
from pathlib import Path

from cell_engine.validation.baseline_lifecycle_timing import (
    BASELINE_DIVISION_TIMING_PROFILE_ID,
    baseline_lifecycle_timing_snapshot,
    validate_baseline_lifecycle_timing,
)


ROOT = Path(__file__).resolve().parents[2]
PUBLIC_SNAPSHOT = ROOT / "public" / "engine-snapshot.json"


def test_baseline_lifecycle_policy_is_human_and_fail_closed() -> None:
    policy = baseline_lifecycle_timing_snapshot()
    validate_baseline_lifecycle_timing(policy)
    division = policy["baseline_division_timing_profile"]
    regeneration = policy["baseline_regeneration_timing_profile"]

    assert policy["canonical_cell_species"] == "human"
    assert policy["baseline_regeneration_species"] == "human"
    assert division["id"] == BASELINE_DIVISION_TIMING_PROFILE_ID
    assert division["execution_authorized"] is False
    assert division["biological_reference"] is False
    assert "s_duration_s" not in division
    assert regeneration["species"] == "human"
    assert regeneration["trigger"] == "none"
    assert policy["regeneration_timing_reference_available"] is False
    assert policy["cross_species_default_count"] == 0


def test_canonical_snapshot_does_not_claim_cross_species_baseline_timing() -> None:
    snapshot = json.loads(PUBLIC_SNAPSHOT.read_text(encoding="utf-8"))
    state = snapshot["state"]
    division_timing = state["division"]["timing_profile"]
    regeneration = state["regeneration_context"]

    assert division_timing["id"] == BASELINE_DIVISION_TIMING_PROFILE_ID
    assert division_timing["execution_authorized"] is False
    assert division_timing["biological_reference"] is False
    assert "g1_min_duration_s" not in division_timing
    assert "s_duration_s" not in division_timing
    assert regeneration["timing_profile"]["species"] == "human"
    assert regeneration["timing_profile"]["trigger"] == "none"
    assert regeneration["timing_is_real_world_reference"] is False
    assert regeneration["division_demo_is_time_compressed"] is False
