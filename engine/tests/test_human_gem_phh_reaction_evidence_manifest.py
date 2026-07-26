from __future__ import annotations

import json

import pytest

from cell_engine.quantitative.human_gem_fbc_loader import DEFAULT_CACHE_PATH
from cell_engine.quantitative.human_gem_phh_reaction_evidence_manifest import (
    DEFAULT_MANIFEST_PATH,
    build_pinned_human_gem_phh_reaction_evidence_manifest,
    load_committed_human_gem_phh_reaction_evidence_manifest,
)


def test_reaction_evidence_manifest_has_no_synthetic_priority_or_execution() -> None:
    report = load_committed_human_gem_phh_reaction_evidence_manifest()
    method = report["method"]
    groups = report["evidence_gap_groups"]
    gates = report["execution_gates"]

    assert method["priority_score_used"] is False
    assert method["biological_threshold_added"] is False
    assert groups["adaptive_fastcore_output_blocked"]["reaction_count"] == 17
    assert (
        groups["all_donor_gpr_generic_fastcc_conflict"]["reaction_count"]
        == 527
    )
    assert (
        groups["six_of_seven_donor_total_proteome_support"][
            "reaction_count"
        ]
        == 150
    )
    assert all(value is False for value in gates.values())


@pytest.mark.skipif(
    not DEFAULT_CACHE_PATH.is_file(),
    reason="checksum-pinned Human-GEM cache artifact is not present",
)
def test_real_reaction_evidence_manifest_regenerates_exactly() -> None:
    generated = build_pinned_human_gem_phh_reaction_evidence_manifest()
    committed = json.loads(
        DEFAULT_MANIFEST_PATH.read_text(encoding="utf-8")
    )

    assert generated == committed
