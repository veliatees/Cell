from __future__ import annotations

import json

import pytest

from cell_engine.quantitative.human_gem_fbc_loader import DEFAULT_CACHE_PATH
from cell_engine.quantitative.human_gem_phh_fastcore_fixed_core_completion_enumeration import (
    DEFAULT_AUDIT_PATH,
    build_pinned_human_gem_phh_fastcore_fixed_core_completion_enumeration,
    load_committed_human_gem_phh_fastcore_fixed_core_completion_enumeration,
)


def test_committed_fixed_core_completion_enumeration_is_conditional() -> None:
    report = (
        load_committed_human_gem_phh_fastcore_fixed_core_completion_enumeration()
    )
    space = report["conditioned_space"]
    terminal = report["terminal_no_good_result"]
    proof = report["proof"]
    boundary = report["scientific_boundary"]

    assert space["fixed_common_reaction_count"] == 58
    assert space["remaining_candidate_reaction_count"] == 4168
    assert space["known_singleton_completion_ids_in_model_order"] == [
        "MAR00494",
        "MAR02308",
        "MAR10035",
    ]
    assert terminal["infeasibility_proven"] is True
    assert terminal["solver_attempt_count"] == 2
    assert terminal["accepted_solve_used_presolve"] is False
    assert terminal["infeasibility_confirmed_without_presolve"] is True
    assert (
        proof["exact_singleton_completion_count_given_fixed_core"] == 3
    )
    assert (
        proof["fixed_core_singleton_completion_enumeration_complete"]
        is True
    )
    assert (
        proof["fourth_singleton_completion_with_same_fixed_core_exists"]
        is False
    )
    assert proof["global_minimum_identity_enumeration_complete"] is False
    assert proof["multi_replacement_global_optima_excluded"] is False
    assert boundary["conditioned_structural_completion_claimed"] is True
    assert (
        boundary["unconditioned_global_identity_enumeration_claimed"]
        is False
    )
    assert boundary["reaction_activity_in_phh_established"] is False
    assert boundary["fba_execution_allowed"] is False


@pytest.mark.skipif(
    not DEFAULT_CACHE_PATH.is_file(),
    reason="checksum-pinned Human-GEM cache artifact is not present",
)
def test_real_fixed_core_completion_enumeration_regenerates_exactly() -> None:
    generated = (
        build_pinned_human_gem_phh_fastcore_fixed_core_completion_enumeration()
    )
    committed = json.loads(
        DEFAULT_AUDIT_PATH.read_text(encoding="utf-8")
    )

    assert generated == committed
