from __future__ import annotations

import json

import pytest

from cell_engine.quantitative.human_gem_fbc_loader import DEFAULT_CACHE_PATH
from cell_engine.quantitative.human_gem_phh_fastcore_support_repair import (
    DEFAULT_AUDIT_PATH,
    build_pinned_human_gem_phh_fastcore_support_repair,
    load_committed_human_gem_phh_fastcore_support_repair,
)


def test_committed_support_repair_is_exact_structural_and_fail_closed() -> None:
    report = load_committed_human_gem_phh_fastcore_support_repair()
    summary = report["summary"]
    boundary = report["scientific_boundary"]

    assert summary["target_blocker_count"] == 17
    assert summary["direction_milp_solve_count"] == 34
    assert summary["targets_with_proven_minimum_count"] == 17
    assert summary["strict_fastcc_blocked_reaction_count"] == 0
    assert boundary["per_target_minimum_cardinality_proven"] is True
    assert boundary["union_strictly_flux_consistent"] is True
    assert boundary["union_global_minimum_guaranteed"] is False
    assert boundary["reaction_activity_in_phh_established"] is False
    assert boundary["context_model_accepted"] is False
    assert boundary["fba_execution_allowed"] is False
    assert boundary["runtime_flux_coupling_allowed"] is False


@pytest.mark.skipif(
    not DEFAULT_CACHE_PATH.is_file(),
    reason="checksum-pinned Human-GEM cache artifact is not present",
)
def test_real_support_repair_regenerates_exactly() -> None:
    generated = build_pinned_human_gem_phh_fastcore_support_repair()
    committed = json.loads(
        DEFAULT_AUDIT_PATH.read_text(encoding="utf-8")
    )

    assert generated == committed
