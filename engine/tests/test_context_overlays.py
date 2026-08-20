from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

import pytest

from cell_engine.io.context_overlays import (
    CONTEXT_OVERLAY_MANIFEST_SCHEMA_VERSION,
    CONTEXT_OVERLAY_SCHEMA_VERSION,
    ContextOverlayError,
    apply_context_overlay,
    build_context_overlay,
    snapshot_identity,
)


def _snapshot(
    *,
    created_at: str,
    definition_id: str,
    zone: str,
    nutrition_profile: str,
    experiment: str,
    marker: int,
) -> dict[str, object]:
    return {
        "schema_version": "cell-engine.snapshot.v1",
        "definition": {
            "cell_type": "hepatocyte",
            "id": definition_id,
            "zone": zone,
        },
        "state": {
            "elapsed_s": 960.0,
            "status": "healthy",
            "pools": {},
            "marker": marker,
            "nutritional_context": {"profile_id": nutrition_profile},
            "experiment": {"id": experiment},
        },
        "metadata": {
            "engine": "cell-engine-python",
            "created_at_utc": created_at,
            "definition_id": definition_id,
        },
    }


def test_context_overlay_exactly_reconstructs_target_snapshot() -> None:
    base = _snapshot(
        created_at="2026-07-29T00:00:00+00:00",
        definition_id="human_hepatocyte_midlobular_v1",
        zone="midlobular",
        nutrition_profile="postabsorptive",
        experiment="baseline",
        marker=1,
    )
    target = _snapshot(
        created_at="2026-07-29T00:00:01+00:00",
        definition_id="human_hepatocyte_periportal_v1",
        zone="periportal",
        nutrition_profile="fed_peak",
        experiment="bsep_loss",
        marker=2,
    )
    overlay = build_context_overlay(
        base,
        target,
        zone="periportal",
        nutrition_profile="fed_peak",
        experiment="bsep_loss",
    )

    assert overlay["schema_version"] == CONTEXT_OVERLAY_SCHEMA_VERSION
    assert overlay["base_identity"] == snapshot_identity(base)
    assert overlay["state_overrides"] == {
        "experiment": {"id": "bsep_loss"},
        "marker": 2,
        "nutritional_context": {"profile_id": "fed_peak"},
    }
    assert apply_context_overlay(base, overlay) == target


def test_context_overlay_rejects_a_different_canonical_snapshot() -> None:
    base = _snapshot(
        created_at="2026-07-29T00:00:00+00:00",
        definition_id="human_hepatocyte_midlobular_v1",
        zone="midlobular",
        nutrition_profile="postabsorptive",
        experiment="baseline",
        marker=1,
    )
    target = _snapshot(
        created_at="2026-07-29T00:00:01+00:00",
        definition_id="human_hepatocyte_pericentral_v1",
        zone="pericentral",
        nutrition_profile="prolonged_fasted",
        experiment="mrp2_loss",
        marker=3,
    )
    overlay = build_context_overlay(
        base,
        target,
        zone="pericentral",
        nutrition_profile="prolonged_fasted",
        experiment="mrp2_loss",
    )
    stale_base = deepcopy(base)
    stale_base["metadata"]["created_at_utc"] = "2026-07-28T00:00:00+00:00"  # type: ignore[index]

    with pytest.raises(ContextOverlayError, match="base identity"):
        apply_context_overlay(stale_base, overlay)


def test_context_overlay_rejects_tampered_state_payload() -> None:
    base = _snapshot(
        created_at="2026-07-29T00:00:00+00:00",
        definition_id="human_hepatocyte_midlobular_v1",
        zone="midlobular",
        nutrition_profile="postabsorptive",
        experiment="baseline",
        marker=1,
    )
    target = _snapshot(
        created_at="2026-07-29T00:00:01+00:00",
        definition_id="human_hepatocyte_periportal_v1",
        zone="periportal",
        nutrition_profile="fed_peak",
        experiment="canalicular_export_loss",
        marker=4,
    )
    overlay = build_context_overlay(
        base,
        target,
        zone="periportal",
        nutrition_profile="fed_peak",
        experiment="canalicular_export_loss",
    )
    overlay["state_overrides"]["marker"] = 999  # type: ignore[index]

    with pytest.raises(ContextOverlayError, match="snapshot checksum"):
        apply_context_overlay(base, overlay)


def test_checked_in_context_overlay_matrix_reconstructs_current_engine_contract() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    public_root = repository_root / "public"
    manifest_path = public_root / "context-snapshot-manifest.v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    base_path = public_root / manifest["base_artifact"]["path"]
    base = json.loads(base_path.read_text(encoding="utf-8"))

    assert (
        manifest["schema_version"]
        == CONTEXT_OVERLAY_MANIFEST_SCHEMA_VERSION
    )
    assert manifest["overlay_count"] == 40
    assert manifest["base_artifact"]["byte_count"] == base_path.stat().st_size
    assert manifest["base_artifact"]["sha256"] == sha256(
        base_path.read_bytes()
    ).hexdigest()
    assert manifest["base_artifact"]["identity"] == snapshot_identity(base)

    expected_paths = {
        f"experiments/{experiment}.json"
        for experiment in (
            "baseline",
            "bsep_loss",
            "mrp2_loss",
            "canalicular_export_loss",
        )
    }
    for zone in ("periportal", "midlobular", "pericentral"):
        for profile in ("fed_peak", "postabsorptive", "prolonged_fasted"):
            for experiment in (
                "baseline",
                "bsep_loss",
                "mrp2_loss",
                "canalicular_export_loss",
            ):
                if profile == "postabsorptive":
                    expected_paths.add(f"contexts/{zone}/{experiment}.json")
                else:
                    expected_paths.add(
                        f"contexts/{zone}/{profile}/{experiment}.json"
                    )

    observed_paths = {record["path"] for record in manifest["artifacts"]}
    assert observed_paths == expected_paths
    assert {
        str(path.relative_to(public_root))
        for directory in ("contexts", "experiments")
        for path in (public_root / directory).rglob("*.json")
    } == expected_paths

    overlay_bytes = base_path.stat().st_size
    for record in manifest["artifacts"]:
        path = public_root / record["path"]
        overlay = json.loads(path.read_text(encoding="utf-8"))
        assert path.stat().st_size == record["byte_count"]
        assert sha256(path.read_bytes()).hexdigest() == record["sha256"]
        assert overlay["target_context"] == {
            "zone": record["zone"],
            "nutrition_profile": record["nutrition_profile"],
            "experiment": record["experiment"],
        }
        assert (
            overlay["audit"]["state_override_count"]
            == record["state_override_count"]
        )
        assert (
            overlay["audit"]["target_snapshot_sha256"]
            == record["target_snapshot_sha256"]
        )
        reconstructed = apply_context_overlay(base, overlay)
        state = reconstructed["state"]
        assert state["metabolic_constraint_shell"]["version"] == (
            "metabolic_constraint_shell_v15"
        )
        assert state["whole_cell_runtime_authority"]["version"] == (
            "whole_cell_runtime_authority_v1"
        )
        assert state["legacy_calibration_authority"]["version"] == (
            "legacy_calibration_authority_v1"
        )
        overlay_bytes += path.stat().st_size

    assert overlay_bytes == manifest["canonical_plus_overlay_byte_count"]
    assert manifest["byte_reduction_fraction"] > 0.8
    assert manifest["canonical_plus_overlay_byte_count"] < (
        manifest["full_snapshot_matrix_byte_count"]
    )
