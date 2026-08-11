from __future__ import annotations

from copy import deepcopy

import pytest

from cell_engine.validation.completion_matrix import (
    build_hepatocyte_completion_matrix,
)
from cell_engine.validation.evidence_readiness import phh_evidence_readiness_snapshot
from cell_engine.validation.software_completion import (
    build_software_completion_boundary,
    validate_software_completion_boundary,
)


def test_every_nonclosed_repository_scope_has_an_explicit_external_disposition() -> None:
    matrix = build_hepatocyte_completion_matrix()
    boundary = matrix["software_completion_boundary"]
    validate_software_completion_boundary(boundary)

    assert boundary["status"] == (
        "engineering_handoff_complete_external_science_required"
    )
    assert boundary["current_repository_implementation_complete_for_available_evidence"] is True
    assert boundary["responsible_code_only_work_remaining"] is False
    assert boundary["scientific_model_complete"] is False
    assert boundary["biological_validation_complete"] is False
    assert boundary["digital_twin_predictive_authority"] is False
    assert boundary["biological_accuracy_pct"] is None
    assert boundary["summary"] == {
        "declared_scope_count": 56,
        "closed_scope_count": 31,
        "evidence_gated_scope_count": 23,
        "registered_evidence_gated_scope_count": 23,
        "unregistered_evidence_gated_scope_count": 0,
        "orphan_evidence_target_count": 0,
        "external_action_scope_count": 1,
        "inapplicable_scope_count": 1,
        "responsible_code_only_scope_count": 0,
        "automatic_parameter_activation_count": 0,
        "automatic_state_coupling_count": 0,
    }


def test_boundary_rejects_an_unregistered_evidence_gap() -> None:
    matrix = build_hepatocyte_completion_matrix()
    base_entries = tuple(
        entry
        for entry in matrix["entries"]
        if entry["id"] != "software_completion_boundary"
    )
    readiness = deepcopy(phh_evidence_readiness_snapshot())
    for entry in readiness["entries"]:
        if "healthy_phh_p53_ddr_dynamics" in entry["target_gap_ids"]:
            entry["target_gap_ids"] = tuple(
                gap_id
                for gap_id in entry["target_gap_ids"]
                if gap_id != "healthy_phh_p53_ddr_dynamics"
            )

    with pytest.raises(ValueError, match="unclassified code work"):
        build_software_completion_boundary(base_entries, readiness)


def test_boundary_rejects_a_scientific_completion_claim() -> None:
    boundary = deepcopy(
        build_hepatocyte_completion_matrix()["software_completion_boundary"]
    )
    boundary["scientific_model_complete"] = True

    with pytest.raises(ValueError, match="overclaims scientific completion"):
        validate_software_completion_boundary(boundary)
