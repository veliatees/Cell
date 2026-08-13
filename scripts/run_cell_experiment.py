from __future__ import annotations

import argparse
import json
from pathlib import Path

from cell_engine.core.engine import run_cell
from cell_engine.core.experiment_archive import ExperimentArchive
from cell_engine.core.random import EngineRng
from cell_engine.processes.hepatocyte import (
    build_hepatocyte_definition,
    initial_hepatocyte_state,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run or resume an explicitly exploratory hepatocyte fixture while "
            "persisting hash-chained full-state checkpoints."
        )
    )
    parser.add_argument("archive", type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--steps", type=int, required=True)
    parser.add_argument("--dt-s", type=float, default=0.5)
    parser.add_argument("--checkpoint-every", type=int, default=100)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--purpose",
        choices=("exploratory_execution", "schematic_visualization"),
        default="exploratory_execution",
    )
    args = parser.parse_args()
    if args.steps < 1:
        parser.error("--steps must be >= 1")
    if args.dt_s <= 0:
        parser.error("--dt-s must be positive")
    if args.checkpoint_every < 1:
        parser.error("--checkpoint-every must be >= 1")

    definition = build_hepatocyte_definition()
    with ExperimentArchive(args.archive) as archive:
        if args.resume:
            run = archive.get_run(args.run_id)
            if run.definition_id != definition.id:
                raise ValueError("archived run uses a different cell definition")
            if run.purpose != args.purpose:
                raise ValueError("--purpose does not match the archived run")
            state, rng = archive.resume(args.run_id)
        else:
            state = initial_hepatocyte_state(definition)
            rng = EngineRng(args.seed)
            archive.start_run(
                run_id=args.run_id,
                definition_id=definition.id,
                cell_state=state,
                rng=rng,
                purpose=args.purpose,
            )

        remaining = args.steps
        while remaining:
            chunk = min(remaining, args.checkpoint_every)
            state = run_cell(
                definition,
                state,
                dt_s=args.dt_s,
                steps=chunk,
                purpose=args.purpose,
                rng=rng,
            )
            archive.append_checkpoint(
                run_id=args.run_id, cell_state=state, rng=rng
            )
            remaining -= chunk

        verification = archive.verify_integrity(args.run_id)
        print(
            json.dumps(
                {
                    "archive": str(args.archive),
                    "run_id": args.run_id,
                    "definition_id": definition.id,
                    "purpose": args.purpose,
                    "elapsed_s": state.elapsed_s,
                    "status": state.status,
                    "record_count": verification.record_count,
                    "checkpoint_count": verification.checkpoint_count,
                    "integrity_verified": verification.integrity_verified,
                    "predictive_authority": verification.predictive_authority,
                },
                indent=2,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
