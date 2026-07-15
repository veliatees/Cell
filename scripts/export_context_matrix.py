from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPORTER = ROOT / "scripts" / "export_engine_snapshot.py"
ZONES = ("periportal", "midlobular", "pericentral")
PROFILES = ("fed_peak", "postabsorptive", "prolonged_fasted")
EXPERIMENTS = ("baseline", "bsep_loss", "mrp2_loss", "canalicular_export_loss")


def export_snapshot(
    *,
    zone: str,
    profile: str,
    experiment: str,
    out: Path,
) -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "engine")
    subprocess.run(
        (
            sys.executable,
            str(EXPORTER),
            "--zone", zone,
            "--nutrition-profile", profile,
            "--experiment", experiment,
            "--out", str(out),
        ),
        cwd=ROOT,
        env=env,
        check=True,
    )


def main() -> None:
    export_snapshot(
        zone="midlobular", profile="postabsorptive", experiment="baseline",
        out=ROOT / "public" / "engine-snapshot.json",
    )
    for experiment in EXPERIMENTS:
        export_snapshot(
            zone="midlobular", profile="postabsorptive", experiment=experiment,
            out=ROOT / "public" / "experiments" / f"{experiment}.json",
        )
    for zone in ZONES:
        for profile in PROFILES:
            for experiment in EXPERIMENTS:
                if profile == "postabsorptive":
                    out = ROOT / "public" / "contexts" / zone / f"{experiment}.json"
                else:
                    out = ROOT / "public" / "contexts" / zone / profile / f"{experiment}.json"
                export_snapshot(zone=zone, profile=profile, experiment=experiment, out=out)


if __name__ == "__main__":
    main()
