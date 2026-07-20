from __future__ import annotations

import pytest

from cell_engine.validation.external_review import (
    EXTERNAL_REVIEW_SOURCES,
    ExternalValidationError,
    assert_claim_validation_level,
    build_external_validation_program,
    external_validation_snapshot,
    render_external_review_dossier,
    validate_external_validation_program,
)
from cell_engine.validation.model_audit import MODEL_SURFACE_AUDIT


def test_external_validation_program_is_scoped_and_fail_closed() -> None:
    program = build_external_validation_program()
    validate_external_validation_program(program)

    assert program.summary.context_count == 4
    assert program.summary.scoped_claim_count == 10
    assert program.summary.reviewer_role_count == 6
    assert program.summary.internal_contract_ready_claim_count == 10
    assert program.summary.externally_reviewed_claim_count == 0
    assert program.summary.same_assay_validated_claim_count == 0
    assert program.summary.prospectively_validated_claim_count == 0
    assert program.summary.predictive_claim_count == 0
    assert program.summary.biological_accuracy_pct is None
    assert not any(context.predictive_claim_allowed for context in program.contexts)
    assert all(context.biological_accuracy_pct is None for context in program.contexts)


def test_every_claim_maps_to_known_surfaces_contexts_and_reviewers() -> None:
    program = build_external_validation_program()
    surface_ids = {item.id for item in MODEL_SURFACE_AUDIT}
    context_ids = {item.id for item in program.contexts}
    reviewer_ids = {item.id for item in program.reviewer_roles}

    for claim in program.claims:
        assert set(claim.model_surface_ids) <= surface_ids
        assert set(claim.context_ids) <= context_ids
        assert set(claim.required_reviewer_role_ids) <= reviewer_ids
        assert claim.current_level == "internal_contract_ready"
        assert claim.internal_contract_ready
        assert claim.external_review_result_count == 0
        assert claim.same_assay_validation_result_count == 0
        assert claim.prospective_validation_result_count == 0
        assert claim.biological_accuracy_pct is None
        assert claim.blockers
        assert claim.falsification_questions


def test_external_validation_level_guard_blocks_unearned_claims() -> None:
    assert_claim_validation_level(
        "whole_cell_predictive_hepatocyte",
        "internal_contract_ready",
    )
    with pytest.raises(ExternalValidationError, match="external_domain_reviewed is blocked"):
        assert_claim_validation_level(
            "whole_cell_predictive_hepatocyte",
            "external_domain_reviewed",
        )
    with pytest.raises(ExternalValidationError, match="prospectively_validated is blocked"):
        assert_claim_validation_level(
            "glucose_measurement_and_model_bridge",
            "prospectively_validated",
        )
    with pytest.raises(KeyError):
        assert_claim_validation_level("not_a_claim", "internal_contract_ready")


def test_only_red_team_round_is_ready() -> None:
    program = build_external_validation_program()
    assert [item.status for item in program.review_rounds] == [
        "ready",
        "blocked",
        "blocked",
        "blocked",
    ]
    assert program.review_rounds[0].pass_criterion is not None
    assert all(item.pass_criterion is None for item in program.review_rounds[1:])
    assert program.independence.validation_donors_must_be_disjoint_from_calibration
    assert program.independence.predictions_must_be_frozen_before_prospective_measurement
    assert program.independence.current_independent_external_review_count == 0
    assert program.independence.current_independent_wet_lab_result_count == 0
    assert program.independence.current_independent_reproduction_count == 0


def test_snapshot_and_dossier_do_not_claim_a_realism_percentage() -> None:
    snapshot = external_validation_snapshot()
    dossier = render_external_review_dossier()

    assert snapshot["summary"]["biological_accuracy_pct"] is None
    assert snapshot["source_ids"] == list(EXTERNAL_REVIEW_SOURCES)
    assert "Whole-cell biological accuracy: not identifiable" in dossier
    assert "95%" not in dossier
    assert "Prospectively validated claims: 0" in dossier
    assert "Round 1" not in dossier
    assert "Claim, source and scope red-team review" in dossier
