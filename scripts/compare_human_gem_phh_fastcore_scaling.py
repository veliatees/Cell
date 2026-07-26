from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from cell_engine.quantitative.human_gem_phh_fastcore_scaling import (
    DEFAULT_AUDIT_PATH,
    build_pinned_human_gem_phh_fastcore_scaling_comparison,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Compare official fixed and adaptive LP-10 scaling on the pinned "
            "seven-donor PHH/Human-GEM FASTCORE trial."
        )
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_AUDIT_PATH)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    report = build_pinned_human_gem_phh_fastcore_scaling_comparison()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.out)


if __name__ == "__main__":
    main()
