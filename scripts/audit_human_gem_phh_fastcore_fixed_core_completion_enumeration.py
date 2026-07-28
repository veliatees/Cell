from __future__ import annotations

import argparse
import json
from pathlib import Path

from cell_engine.quantitative.human_gem_phh_fastcore_fixed_core_completion_enumeration import (
    DEFAULT_AUDIT_PATH,
    build_pinned_human_gem_phh_fastcore_fixed_core_completion_enumeration,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Enumerate all one-reaction completions conditional on the "
            "58-reaction core shared by known global FASTCORE optima."
        )
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_AUDIT_PATH)
    args = parser.parse_args()

    report = (
        build_pinned_human_gem_phh_fastcore_fixed_core_completion_enumeration()
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.out)


if __name__ == "__main__":
    main()
