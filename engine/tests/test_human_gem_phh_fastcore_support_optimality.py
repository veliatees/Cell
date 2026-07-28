from __future__ import annotations

import json

import pytest

from cell_engine.quantitative.human_gem_fbc_loader import DEFAULT_CACHE_PATH
from cell_engine.quantitative.human_gem_phh_fastcore_support_optimality import (
    DEFAULT_AUDIT_PATH,
    build_pinned_human_gem_phh_fastcore_support_optimality,
    load_committed_human_gem_phh_fastcore_support_optimality,
)


def test_committed_optimality_audit_resolves_only_the_scoped_question() -> None:
    report = load_committed_human_gem_phh_fastcore_support_optimality()
    summary = report["summary"]
    boundary = report["scientific_boundary"]

    assert summary["input_candidate_union_count"] == 65
    assert summary["target_blocker_count"] == 17
    assert summary["primary_minimum_added_reaction_count"] == 59
    assert summary["minimum_support_set_count"] == 2
    assert summary["minimum_support_identity_enumeration_complete"] is True
    assert summary["no_good_milp_solve_count"] == 2
    assert summary["enumeration_terminal_infeasibility_proven"] is True
    assert summary["enumeration_terminal_solver_attempt_count"] == 2
    assert summary["enumeration_terminal_presolve"] is False
    assert (
        summary[
            "enumeration_terminal_infeasibility_confirmed_without_presolve"
        ]
        is True
    )
    assert (
        summary[
            "reactions_proven_present_in_every_minimum_support_count"
        ]
        == 58
    )
    assert summary["minimum_support_optional_reaction_count"] == 2
    assert summary[
        "minimum_support_optional_reaction_ids_in_input_order"
    ] == ["MAR02308", "MAR10035"]
    assert (
        boundary["alternate_optimum_question_resolved_within_65_pool"]
        is True
    )
    assert (
        boundary[
            "all_minimum_support_identities_enumerated_within_65_pool"
        ]
        is True
    )
    assert (
        boundary["universal_minimum_support_membership_established"]
        is True
    )
    assert (
        boundary["global_minimum_over_all_omitted_reactions_guaranteed"]
        is False
    )
    assert (
        boundary["structural_essentiality_at_larger_support_sizes_established"]
        is False
    )
    assert boundary["reaction_activity_in_phh_established"] is False
    assert boundary["context_model_accepted"] is False
    assert boundary["fba_execution_allowed"] is False
    assert boundary["runtime_flux_coupling_allowed"] is False


@pytest.mark.skipif(
    not DEFAULT_CACHE_PATH.is_file(),
    reason="checksum-pinned Human-GEM cache artifact is not present",
)
def test_real_support_optimality_regenerates_exactly() -> None:
    generated = build_pinned_human_gem_phh_fastcore_support_optimality()
    committed = json.loads(
        DEFAULT_AUDIT_PATH.read_text(encoding="utf-8")
    )

    assert generated == committed
