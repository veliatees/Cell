from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
ENGINE_ROOT = ROOT / "engine"
EXPORTER = ROOT / "scripts" / "export_engine_snapshot.py"
PUBLIC_ROOT = ROOT / "public"
if str(ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(ENGINE_ROOT))

from cell_engine.io.context_overlays import (  # noqa: E402
    CONTEXT_OVERLAY_ARTIFACT_COUNT,
    CONTEXT_OVERLAY_EXPERIMENT_COUNT,
    CONTEXT_OVERLAY_MANIFEST_SCHEMA_VERSION,
    CONTEXT_OVERLAY_NUTRITION_PROFILE_COUNT,
    CONTEXT_OVERLAY_ZONE_COUNT,
    apply_context_overlay,
    build_context_overlay,
    snapshot_identity,
)


ZONES = ("periportal", "midlobular", "pericentral")
PROFILES = ("fed_peak", "postabsorptive", "prolonged_fasted")
EXPERIMENTS = ("baseline", "bsep_loss", "mrp2_loss", "canalicular_export_loss")


@dataclass(frozen=True)
class SnapshotTask:
    zone: str
    profile: str
    experiment: str
    relative_output: Path


def snapshot_tasks() -> tuple[SnapshotTask, ...]:
    tasks = [
        SnapshotTask(
            zone="midlobular",
            profile="postabsorptive",
            experiment=experiment,
            relative_output=Path("experiments") / f"{experiment}.json",
        )
        for experiment in EXPERIMENTS
    ]
    for zone in ZONES:
        for profile in PROFILES:
            for experiment in EXPERIMENTS:
                if profile == "postabsorptive":
                    relative = Path("contexts") / zone / f"{experiment}.json"
                else:
                    relative = (
                        Path("contexts")
                        / zone
                        / profile
                        / f"{experiment}.json"
                    )
                tasks.append(
                    SnapshotTask(
                        zone=zone,
                        profile=profile,
                        experiment=experiment,
                        relative_output=relative,
                    )
                )
    return tuple(tasks)


def export_snapshot(
    *,
    zone: str,
    profile: str,
    experiment: str,
    out: Path,
) -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ENGINE_ROOT)
    result = subprocess.run(
        (
            sys.executable,
            str(EXPORTER),
            "--zone",
            zone,
            "--nutrition-profile",
            profile,
            "--experiment",
            experiment,
            "--out",
            str(out),
        ),
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"context snapshot export failed for {zone}/{profile}/{experiment}\n"
            f"{result.stdout}\n{result.stderr}"
        )


def _read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"snapshot artifact must contain an object: {path}")
    return payload


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _export_target(
    task_and_path: tuple[SnapshotTask, Path],
) -> tuple[SnapshotTask, Path]:
    task, output = task_and_path
    export_snapshot(
        zone=task.zone,
        profile=task.profile,
        experiment=task.experiment,
        out=output,
    )
    return task, output


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Export one canonical engine snapshot plus exact context overlays. "
            "Artifacts are published only after every target reconstructs exactly."
        )
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=int(os.environ.get("CELL_CONTEXT_EXPORT_WORKERS", "2")),
        help="parallel exporter process count (default: 2)",
    )
    args = parser.parse_args()
    if args.workers < 1 or args.workers > 8:
        raise SystemExit("--workers must be between 1 and 8")

    tasks = snapshot_tasks()
    if (
        len(ZONES) != CONTEXT_OVERLAY_ZONE_COUNT
        or len(PROFILES) != CONTEXT_OVERLAY_NUTRITION_PROFILE_COUNT
        or len(EXPERIMENTS) != CONTEXT_OVERLAY_EXPERIMENT_COUNT
        or len(tasks) != CONTEXT_OVERLAY_ARTIFACT_COUNT
    ):
        raise RuntimeError(
            "context matrix dimensions drifted from the published overlay contract"
        )
    with TemporaryDirectory(prefix="cell-context-export-") as temporary:
        temporary_root = Path(temporary)
        canonical_path = temporary_root / "engine-snapshot.json"
        export_snapshot(
            zone="midlobular",
            profile="postabsorptive",
            experiment="baseline",
            out=canonical_path,
        )
        base_snapshot = _read_json(canonical_path)
        base_identity = snapshot_identity(base_snapshot)

        target_jobs = tuple(
            (task, temporary_root / "targets" / f"{index:02d}.json")
            for index, task in enumerate(tasks)
        )
        for _, path in target_jobs:
            path.parent.mkdir(parents=True, exist_ok=True)
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            exported_targets = tuple(executor.map(_export_target, target_jobs))

        artifact_records: list[dict[str, object]] = []
        staged_overlays: list[tuple[Path, Path]] = []
        full_snapshot_matrix_bytes = canonical_path.stat().st_size
        overlay_matrix_bytes = canonical_path.stat().st_size
        for task, target_path in exported_targets:
            target_snapshot = _read_json(target_path)
            overlay = build_context_overlay(
                base_snapshot,
                target_snapshot,
                zone=task.zone,
                nutrition_profile=task.profile,
                experiment=task.experiment,
            )
            if apply_context_overlay(base_snapshot, overlay) != target_snapshot:
                raise RuntimeError(
                    f"overlay reconstruction mismatch: {task.relative_output}"
                )
            staged_path = temporary_root / "overlays" / task.relative_output
            _write_json(staged_path, overlay)
            full_snapshot_matrix_bytes += target_path.stat().st_size
            overlay_matrix_bytes += staged_path.stat().st_size
            staged_overlays.append(
                (staged_path, PUBLIC_ROOT / task.relative_output)
            )
            audit = overlay["audit"]
            artifact_records.append(
                {
                    "path": str(task.relative_output),
                    "zone": task.zone,
                    "nutrition_profile": task.profile,
                    "experiment": task.experiment,
                    "byte_count": staged_path.stat().st_size,
                    "sha256": _file_sha256(staged_path),
                    "state_override_count": audit["state_override_count"],
                    "target_snapshot_sha256": audit["target_snapshot_sha256"],
                }
            )

        manifest = {
            "schema_version": CONTEXT_OVERLAY_MANIFEST_SCHEMA_VERSION,
            "base_artifact": {
                "path": "engine-snapshot.json",
                "byte_count": canonical_path.stat().st_size,
                "sha256": _file_sha256(canonical_path),
                "identity": base_identity,
            },
            "overlay_count": CONTEXT_OVERLAY_ARTIFACT_COUNT,
            "expected_zone_count": CONTEXT_OVERLAY_ZONE_COUNT,
            "expected_nutrition_profile_count": (
                CONTEXT_OVERLAY_NUTRITION_PROFILE_COUNT
            ),
            "expected_experiment_count": CONTEXT_OVERLAY_EXPERIMENT_COUNT,
            "full_snapshot_matrix_byte_count": full_snapshot_matrix_bytes,
            "canonical_plus_overlay_byte_count": overlay_matrix_bytes,
            "byte_reduction_fraction": (
                1 - overlay_matrix_bytes / full_snapshot_matrix_bytes
            ),
            "artifacts": sorted(
                artifact_records,
                key=lambda item: str(item["path"]),
            ),
            "policy": (
                "Every browser context is reconstructed from the checksummed "
                "canonical snapshot plus exact top-level state overrides. A base "
                "identity mismatch fails closed; overlays introduce no biological "
                "parameter, interpolation or model output."
            ),
        }
        staged_manifest = temporary_root / "context-snapshot-manifest.v1.json"
        _write_json(staged_manifest, manifest)

        # Publish overlays first and the canonical base last. During the brief
        # replacement window, an old base can only cause a fail-closed identity
        # mismatch; it can never be silently paired with a new overlay.
        for staged_path, destination in staged_overlays:
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staged_path, destination)
        os.replace(
            staged_manifest,
            PUBLIC_ROOT / "context-snapshot-manifest.v1.json",
        )
        os.replace(canonical_path, PUBLIC_ROOT / "engine-snapshot.json")

    reduction_percent = 100 * (
        1 - overlay_matrix_bytes / full_snapshot_matrix_bytes
    )
    print(
        f"published 1 canonical snapshot + {len(tasks)} exact overlays; "
        f"artifact bytes reduced by {reduction_percent:.1f}%"
    )


if __name__ == "__main__":
    main()
