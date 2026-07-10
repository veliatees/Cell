from __future__ import annotations

"""Build the browser-selectable, evidence-bound experiment snapshots."""

from pathlib import Path
import subprocess
import sys

from cell_engine.validation.experiments import CURATED_EXPERIMENTS


def main() -> None:
    output_dir = Path("public/experiments")
    output_dir.mkdir(parents=True, exist_ok=True)
    exporter = Path(__file__).with_name("export_engine_snapshot.py")
    for experiment_id in CURATED_EXPERIMENTS:
        output = output_dir / f"{experiment_id}.json"
        subprocess.run(
            [sys.executable, str(exporter), "--experiment", experiment_id, "--out", str(output)],
            check=True,
        )


if __name__ == "__main__":
    main()
