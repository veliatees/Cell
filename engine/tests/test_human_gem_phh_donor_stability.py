from __future__ import annotations

import json

import pytest

from cell_engine.quantitative.human_gem_fbc_loader import DEFAULT_CACHE_PATH
from cell_engine.quantitative.human_gem_phh_donor_stability import (
    DEFAULT_AUDIT_PATH,
    build_pinned_human_gem_phh_donor_stability_audit,
    load_committed_human_gem_phh_donor_stability_audit,
)


def test_committed_donor_stability_audit_preserves_missingness_boundary() -> None:
    report = load_committed_human_gem_phh_donor_stability_audit()
    summary = report["summary"]
    frequency = report["support_frequency_by_donor_count"]
    boundary = report["scientific_boundary"]

    assert summary["gpr_reaction_count"] == 7_782
    assert summary["seven_donor_supported_reaction_count"] == 5_082
    assert summary["seven_donor_flux_consistent_core_count"] == 4_555
    assert sum(
        section["gpr_reaction_count"] for section in frequency.values()
    ) == 7_782
    assert len(report["pairwise_donor_support"]) == 21
    assert len(report["leave_one_donor_out"]) == 7
    assert boundary["donor_support_stability_quantified"] is True
    assert boundary["missing_detection_interpreted_as_inactivity"] is False
    assert boundary["between_donor_difference_interpreted_as_biology"] is False
    assert boundary["context_model_accepted"] is False


@pytest.mark.skipif(
    not DEFAULT_CACHE_PATH.is_file(),
    reason="checksum-pinned Human-GEM cache artifact is not present",
)
def test_real_donor_stability_audit_regenerates_exactly() -> None:
    generated = build_pinned_human_gem_phh_donor_stability_audit()
    committed = json.loads(DEFAULT_AUDIT_PATH.read_text(encoding="utf-8"))

    assert generated == committed
