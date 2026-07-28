from __future__ import annotations

import json

import pytest

from cell_engine.quantitative.human_gem_fbc_loader import DEFAULT_CACHE_PATH
from cell_engine.quantitative.human_gem_phh_fastcore_global_support_optimality import (
    DEFAULT_AUDIT_PATH,
    build_pinned_human_gem_phh_fastcore_global_support_optimality,
    load_committed_human_gem_phh_fastcore_global_support_optimality,
)


def test_committed_global_support_cardinality_is_exact_and_scoped() -> None:
    report = (
        load_committed_human_gem_phh_fastcore_global_support_optimality()
    )
    input_summary = report["input"]
    lower = report["lower_bound_certificate"]
    upper = report["upper_bound_certificate"]
    proof = report["proof"]
    boundary = report["scientific_boundary"]

    assert input_summary["global_candidate_reaction_count"] == 4_226
    assert input_summary["full_target_count"] == 17
    assert input_summary["lower_bound_target_count"] == 2
    assert lower["exact_minimum_added_reaction_count"] == 59
    assert lower["target_lp_certificate_count"] == 2
    assert upper["feasible_added_reaction_count"] == 59
    assert upper["all_target_lp_certificate_count"] == 17
    assert proof["bounds_match"] is True
    assert proof["global_minimum_added_reaction_count"] == 59
    assert proof["global_minimum_cardinality_proven"] is True
    assert proof["global_minimum_identity_sets_enumerated"] is False
    assert proof["global_minimum_support_set_unique"] is None
    assert (
        boundary["global_minimum_over_all_omitted_reactions_guaranteed"]
        is True
    )
    assert (
        boundary["all_global_minimum_identity_sets_enumerated"] is False
    )
    assert boundary["reaction_activity_in_phh_established"] is False
    assert boundary["context_model_accepted"] is False
    assert boundary["fba_execution_allowed"] is False
    assert boundary["runtime_flux_coupling_allowed"] is False


@pytest.mark.skipif(
    not DEFAULT_CACHE_PATH.is_file(),
    reason="checksum-pinned Human-GEM cache artifact is not present",
)
def test_real_global_support_optimality_regenerates_exactly() -> None:
    generated = (
        build_pinned_human_gem_phh_fastcore_global_support_optimality()
    )
    committed = json.loads(
        DEFAULT_AUDIT_PATH.read_text(encoding="utf-8")
    )

    assert generated == committed
