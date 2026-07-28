from __future__ import annotations

import argparse
import json
from pathlib import Path

from cell_engine.quantitative.human_gem_flux_consistency import (
    DEFAULT_FASTCC_AUDIT_PATH,
    PAPER_EXPERIMENT_EPSILON,
    build_pinned_human_gem_fastcc_audit,
)
from cell_engine.quantitative.human_gem_fbc_loader import DEFAULT_CACHE_PATH


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run sign-definite pruning plus source-defined FASTCC on the "
            "checksum-pinned generic Human-GEM artifact."
        )
    )
    parser.add_argument("--artifact", type=Path, default=DEFAULT_CACHE_PATH)
    parser.add_argument("--out", type=Path, default=DEFAULT_FASTCC_AUDIT_PATH)
    parser.add_argument(
        "--epsilon",
        type=float,
        required=False,
        default=PAPER_EXPERIMENT_EPSILON,
        help=(
            "Explicit consistency threshold. The default is the 1e-4 value "
            "reported for the primary FASTCC paper's experiments."
        ),
    )
    args = parser.parse_args()

    report = build_pinned_human_gem_fastcc_audit(
        args.artifact,
        epsilon=args.epsilon,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.out)


if __name__ == "__main__":
    main()
