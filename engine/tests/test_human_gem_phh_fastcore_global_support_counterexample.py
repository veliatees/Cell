from __future__ import annotations

import json

import pytest

from cell_engine.quantitative.human_gem_fbc_loader import DEFAULT_CACHE_PATH
from cell_engine.quantitative.human_gem_phh_fastcore_global_support_counterexample import (
    DEFAULT_AUDIT_PATH,
    build_pinned_human_gem_phh_fastcore_global_support_counterexample,
    load_committed_human_gem_phh_fastcore_global_support_counterexample,
)


def test_committed_global_counterexample_is_exact_and_incomplete() -> None:
    report = (
        load_committed_human_gem_phh_fastcore_global_support_counterexample()
    )
    cross_check = report["presolve_cross_check"]
    counterexample = report["counterexample"]
    conclusion = report["conclusion"]
    boundary = report["scientific_boundary"]

    assert cross_check["initial_presolve_reported_infeasible"] is True
    assert (
        cross_check["no_presolve_confirmation_found_feasible_optimum"]
        is True
    )
    assert cross_check["solver_attempt_count"] == 2
    assert cross_check["presolve_infeasibility_disagreed"] is True
    assert counterexample["added_reaction_count"] == 59
    assert counterexample[
        "primary_only_reaction_ids_in_input_order"
    ] == ["MAR10035"]
    assert counterexample[
        "counterexample_only_reaction_ids_in_input_order"
    ] == ["MAR00494"]
    assert counterexample[
        "outside_scoped_pool_reaction_ids_in_input_order"
    ] == ["MAR00494"]
    assert counterexample["all_target_lp_certificate_count"] == 17
    assert counterexample["strict_fastcc_blocked_reaction_count"] == 0
    assert conclusion[
        "known_distinct_global_minimum_support_set_count_lower_bound"
    ] == 3
    assert (
        conclusion["global_minimum_identity_enumeration_complete"]
        is False
    )
    assert conclusion["additional_global_minimum_search_required"] is True
    assert boundary["new_all_target_global_minimum_identity_certified"] is True
    assert boundary["complete_global_identity_enumeration_claimed"] is False
    assert boundary["reaction_activity_in_phh_established"] is False
    assert boundary["fba_execution_allowed"] is False


@pytest.mark.skipif(
    not DEFAULT_CACHE_PATH.is_file(),
    reason="checksum-pinned Human-GEM cache artifact is not present",
)
def test_real_global_counterexample_regenerates_exactly() -> None:
    generated = (
        build_pinned_human_gem_phh_fastcore_global_support_counterexample()
    )
    committed = json.loads(
        DEFAULT_AUDIT_PATH.read_text(encoding="utf-8")
    )

    assert generated == committed
