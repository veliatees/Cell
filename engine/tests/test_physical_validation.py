from __future__ import annotations

import json
from pathlib import Path

import pytest

from cell_engine.validation.physical_validation import (
    PHYSICAL_VALIDATION_SOURCES,
    build_physical_validation_report,
    physical_validation_snapshot,
    validate_physical_validation_report,
)


_PUBLIC_SNAPSHOT = Path(__file__).resolve().parents[2] / "public" / "engine-snapshot.json"


def test_three_physical_layers_have_95_percent_verification_coverage_without_fake_accuracy() -> None:
    report = build_physical_validation_report()
    validate_physical_validation_report(report)

    assert {layer.id for layer in report.layers} == {
        "scale_geometry",
        "membrane_physics",
        "contact_domain",
    }
    for layer in report.layers:
        assert layer.criterion_count == 20
        assert layer.verified_count == 19
        assert layer.verification_coverage_pct == 95.0
        assert layer.predictive_accuracy_pct is None
        assert len([criterion for criterion in layer.criteria if criterion.status == "blocked"]) == 1
        assert layer.blockers


def test_physical_validation_sources_and_snapshot_are_self_consistent() -> None:
    report = build_physical_validation_report()
    assert set(report.source_ids) <= PHYSICAL_VALIDATION_SOURCES.keys()
    snapshot = physical_validation_snapshot()
    assert snapshot["score_semantics"].startswith("verification_coverage_pct")
    assert all(layer["predictive_accuracy_pct"] is None for layer in snapshot["layers"])


def test_public_snapshot_keeps_scale_polarity_and_domain_map_aligned() -> None:
    snapshot = json.loads(_PUBLIC_SNAPSHOT.read_text(encoding="utf-8"))
    definition_geometry = snapshot["definition"]["geometry"]
    assert snapshot["state"]["quantitative_state"]["geometry_reference"]["canonical_reference"]["cell_volume_um3"] == 5657.07116
    assert definition_geometry["radius_um"] * 2.0 == pytest.approx(22.107060841416555)
    assert definition_geometry["polarity_axis"] == [1.0, 0.0, 0.0]

    faces = {
        face["id"]: face["membrane_domain"]
        for face in snapshot["state"]["spatial_world"]["bodies"][0]["shape"]["faces"]
    }
    assert faces["sinusoidal_neg_x"] == "basolateral"
    assert faces["canalicular_pos_x"] == "apical"
