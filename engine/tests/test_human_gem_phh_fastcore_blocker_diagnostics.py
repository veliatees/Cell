from __future__ import annotations

import json

import pytest

from cell_engine.quantitative.human_gem_fbc_loader import DEFAULT_CACHE_PATH
from cell_engine.quantitative.human_gem_phh_fastcore_blocker_diagnostics import (
    DEFAULT_AUDIT_PATH,
    build_pinned_human_gem_phh_fastcore_blocker_diagnostics,
    load_committed_human_gem_phh_fastcore_blocker_diagnostics,
)


def test_committed_blocker_diagnostics_are_structural_and_fail_closed() -> None:
    report = load_committed_human_gem_phh_fastcore_blocker_diagnostics()
    summary = report["summary"]
    boundary = report["scientific_boundary"]

    assert summary["diagnosed_blocker_count"] == 17
    assert summary["full_network_active_blocker_count"] == 17
    assert summary["candidate_blocked_reaction_count"] == 17
    assert boundary["reaction_level_failure_diagnosed"] is True
    assert boundary["minimum_reaction_support_proven"] is False
    assert boundary["healthy_phh_context_established"] is False
    assert boundary["context_model_accepted"] is False
    assert boundary["fba_execution_allowed"] is False
    assert boundary["runtime_flux_coupling_allowed"] is False


@pytest.mark.skipif(
    not DEFAULT_CACHE_PATH.is_file(),
    reason="checksum-pinned Human-GEM cache artifact is not present",
)
def test_real_blocker_diagnostics_regenerate_exactly() -> None:
    generated = build_pinned_human_gem_phh_fastcore_blocker_diagnostics()
    committed = json.loads(
        DEFAULT_AUDIT_PATH.read_text(encoding="utf-8")
    )

    assert generated == committed
