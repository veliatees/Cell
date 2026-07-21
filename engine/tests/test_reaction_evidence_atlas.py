from __future__ import annotations

from cell_engine.validation.reaction_evidence_atlas import (
    build_reaction_evidence_atlas,
    validate_reaction_evidence_atlas,
)


def test_reaction_evidence_atlas_covers_all_36_active_reactions() -> None:
    snapshot = build_reaction_evidence_atlas()
    validate_reaction_evidence_atlas(snapshot)
    summary = snapshot["summary"]
    assert summary["active_reaction_count"] == 36
    assert summary["evidence_slot_count"] == 432
    assert summary["published_candidate_mapping_count"] == 12


def test_reaction_evidence_is_fail_closed_and_fluid_coupling_is_per_reaction() -> None:
    snapshot = build_reaction_evidence_atlas()
    for reaction in snapshot["reactions"]:
        assert reaction["legacy_runtime_compartment_is_biological_assignment"] is False
        assert reaction["quantitative_execution_allowed"] is False
        assert reaction["predictive_execution_allowed"] is False
        assert all(slot["value"] is None for slot in reaction["evidence_slots"])
        gate = reaction["transport_coupling"]
        assert gate["direct_fluid_rate_multiplier"] is None
        assert gate["local_concentration_coupling_allowed"] is False
        assert gate["direct_rate_correction_allowed"] is False
