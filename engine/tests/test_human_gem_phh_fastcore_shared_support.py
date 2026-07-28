from __future__ import annotations

import json

import pytest

from cell_engine.quantitative.human_gem_fbc_loader import DEFAULT_CACHE_PATH
from cell_engine.quantitative.human_gem_phh_fastcore_shared_support import (
    DEFAULT_AUDIT_PATH,
    build_pinned_human_gem_phh_fastcore_shared_support,
    load_committed_human_gem_phh_fastcore_shared_support,
)


def test_committed_shared_support_is_exact_structural_and_fail_closed() -> None:
    report = load_committed_human_gem_phh_fastcore_shared_support()
    summary = report["summary"]
    method = report["method"]
    boundary = report["scientific_boundary"]

    assert summary["input_candidate_union_count"] == 65
    assert summary["target_blocker_count"] == 17
    assert summary["minimum_shared_added_reaction_count"] == 59
    assert summary["removed_from_per_target_union_count"] == 6
    assert summary["repaired_candidate_reaction_count"] == 7_474
    assert summary["target_lp_certificate_count"] == 17
    assert summary["strict_fastcc_blocked_reaction_count"] == 0
    assert summary["selected_reaction_without_gpr_count"] == 4
    assert summary["selected_reaction_zero_donor_gpr_count"] == 55
    assert method["broader_omitted_reaction_universe_searched"] is False
    assert method["simultaneous_target_coactivity_claimed"] is False
    assert (
        method[
            "selected_candidate_reaches_epsilon_in_at_least_one_scenario"
        ]
        is True
    )
    assert method["subthreshold_candidate_activation_allowed"] is False
    assert (
        boundary["minimum_cardinality_within_65_reaction_union_proven"]
        is True
    )
    assert boundary["selected_subset_strictly_flux_consistent"] is True
    assert (
        boundary["global_minimum_over_all_omitted_reactions_guaranteed"]
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
def test_real_shared_support_regenerates_exactly() -> None:
    generated = build_pinned_human_gem_phh_fastcore_shared_support()
    committed = json.loads(
        DEFAULT_AUDIT_PATH.read_text(encoding="utf-8")
    )

    assert generated == committed
