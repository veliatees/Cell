from __future__ import annotations

import json

import pytest

from cell_engine.quantitative.human_gem_fbc_loader import DEFAULT_CACHE_PATH
from cell_engine.quantitative.human_gem_phh_fastcore_global_support_identity_completeness import (
    DEFAULT_AUDIT_PATH,
    build_pinned_human_gem_phh_fastcore_global_support_identity_completeness,
    load_committed_human_gem_phh_fastcore_global_support_identity_completeness,
)


def test_committed_global_minimum_identity_enumeration_is_complete() -> None:
    report = (
        load_committed_human_gem_phh_fastcore_global_support_identity_completeness()
    )
    terminal = report["common_core_exclusion_terminal_result"]
    proof = report["proof"]
    boundary = report["scientific_boundary"]

    assert terminal["infeasibility_proven"] is True
    assert terminal["solver_attempt_count"] == 2
    assert terminal["accepted_solve_used_presolve"] is False
    assert terminal["infeasibility_confirmed_without_presolve"] is True
    assert proof["global_minimum_added_reaction_count"] == 59
    assert proof["global_minimum_support_set_count"] == 3
    assert (
        proof["global_minimum_support_identity_enumeration_complete"]
        is True
    )
    assert proof["global_minimum_support_set_unique"] is False
    assert proof[
        "global_universal_minimum_support_reaction_count"
    ] == 58
    assert proof[
        "global_optional_minimum_support_reaction_ids_in_model_order"
    ] == ["MAR00494", "MAR02308", "MAR10035"]
    assert proof[
        "every_global_minimum_contains_exactly_one_optional_identity"
    ] is True
    assert proof["multi_replacement_global_optima_excluded"] is True
    assert (
        proof["additional_global_minimum_identity_search_required"]
        is False
    )
    assert boundary["global_minimum_identity_enumeration_claimed"] is True
    assert boundary[
        "structural_essentiality_at_larger_support_sizes_established"
    ] is False
    assert boundary["reaction_activity_in_phh_established"] is False
    assert boundary["fba_execution_allowed"] is False


@pytest.mark.skipif(
    not DEFAULT_CACHE_PATH.is_file(),
    reason="checksum-pinned Human-GEM cache artifact is not present",
)
def test_real_global_identity_completeness_regenerates_exactly() -> None:
    generated = (
        build_pinned_human_gem_phh_fastcore_global_support_identity_completeness()
    )
    committed = json.loads(
        DEFAULT_AUDIT_PATH.read_text(encoding="utf-8")
    )

    assert generated == committed
