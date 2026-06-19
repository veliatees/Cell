from __future__ import annotations

import argparse
from pathlib import Path

from cell_engine import EngineRng, build_hepatocyte_definition, initial_hepatocyte_state, run_cell
from cell_engine.io.snapshots import snapshot_to_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a Python engine snapshot for the TypeScript visualizer.")
    parser.add_argument("--out", default="public/engine-snapshot.json")
    parser.add_argument("--steps", type=int, default=8)
    parser.add_argument("--dt", type=float, default=120.0)
    args = parser.parse_args()

    definition = build_hepatocyte_definition()
    state = initial_hepatocyte_state(definition)
    state = run_cell(definition, state, dt_s=args.dt, steps=args.steps, rng=EngineRng(definition.stochastic_policy.seed))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(snapshot_to_json(definition, state), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
