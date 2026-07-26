from __future__ import annotations

import json

import pytest

from cell_engine.quantitative.human_gem_fbc_loader import DEFAULT_CACHE_PATH
from cell_engine.quantitative.human_gem_phh_proteome_context import (
    DEFAULT_AUDIT_PATH,
    build_pinned_human_gem_phh_proteome_gpr_audit,
    load_committed_human_gem_phh_proteome_gpr_audit,
)


def test_committed_phh_proteome_gpr_audit_is_conservative_and_gated() -> None:
    report = load_committed_human_gem_phh_proteome_gpr_audit()
    mapping = report["protein_group_mapping"]
    consensus = report["all_donor_support"]
    boundary = report["scientific_boundary"]

    assert mapping["source_quantified_group_count"] == 8_689
    assert mapping["multi_gene_ambiguous_group_count"] == 241
    assert mapping["empty_gene_group_count"] == 338
    assert mapping["non_single_gene_excluded_group_count"] == 579
    assert consensus["reaction_support_intersection_count"] == 5_082
    assert consensus["generic_fastcc_blocked_conflict_count"] == 527
    assert consensus["flux_consistent_core_candidate_count"] == 4_555
    assert boundary["flux_consistent_core_candidate_created"] is True
    assert boundary["protein_detection_interpreted_as_active_enzyme"] is False
    assert boundary["flux_magnitude_inferred"] is False
    assert boundary["healthy_phh_context_model_claimed"] is False


@pytest.mark.skipif(
    not DEFAULT_CACHE_PATH.is_file(),
    reason="checksum-pinned Human-GEM cache artifact is not present",
)
def test_real_phh_proteome_gpr_audit_regenerates_exactly() -> None:
    generated = build_pinned_human_gem_phh_proteome_gpr_audit()
    committed = json.loads(DEFAULT_AUDIT_PATH.read_text(encoding="utf-8"))

    assert generated == committed
