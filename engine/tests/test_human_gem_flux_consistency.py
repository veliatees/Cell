from __future__ import annotations

from copy import deepcopy

import pytest

from cell_engine.quantitative.human_gem_flux_consistency import (
    HumanGemFastccError,
    load_committed_human_gem_fastcc_audit,
    validate_human_gem_fastcc_audit,
)


def test_committed_human_gem_fastcc_audit_is_complete_and_fail_closed() -> None:
    report = load_committed_human_gem_fastcc_audit()
    classification = report["classification"]
    fastcc = report["fastcc_reduced_network"]
    prepass = report["sign_definite_prepass"]

    assert classification["consistent_reaction_count"] == 11_641
    assert classification["blocked_reaction_count"] == 1_290
    assert (
        classification["consistent_reaction_count"]
        + classification["blocked_reaction_count"]
        == report["input_network"]["reaction_count"]
    )
    assert prepass["blocked_reaction_count"] == 1_133
    assert fastcc["blocked_reaction_count"] == 157
    assert fastcc["lp7_solve_count"] == 6
    assert fastcc["lp3_solve_count"] == 247
    assert fastcc["complete_consistency_classification"] is True
    assert report["scientific_boundary"]["healthy_phh_context_extracted"] is False
    assert report["scientific_boundary"]["biological_flux_authority"] is False

    escaped = deepcopy(report)
    escaped["scientific_boundary"]["biological_flux_authority"] = True
    with pytest.raises(HumanGemFastccError, match="biological execution"):
        validate_human_gem_fastcc_audit(escaped)
