from __future__ import annotations

import argparse
import json
from pathlib import Path

from cell_engine.quantitative.human_gem_phh_fastcore_support_optimality import (
    DEFAULT_AUDIT_PATH,
    build_pinned_human_gem_phh_fastcore_support_optimality,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Exclude the committed minimum shared FASTCORE repair and prove "
            "uniqueness or record one alternate optimum."
        )
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_AUDIT_PATH)
    args = parser.parse_args()

    report = build_pinned_human_gem_phh_fastcore_support_optimality()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.out)


if __name__ == "__main__":
    main()
