from __future__ import annotations

import argparse
import json
from pathlib import Path

from cell_engine.quantitative.human_gem_fbc_loader import DEFAULT_CACHE_PATH
from cell_engine.quantitative.human_gem_generic_fba import (
    DEFAULT_GENERIC_FBA_AUDIT_PATH,
    build_pinned_human_gem_generic_fba_audit,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Solve the exact native objective of the checksum-pinned generic "
            "Human-GEM reconstruction and write a fail-closed audit."
        )
    )
    parser.add_argument("--artifact", type=Path, default=DEFAULT_CACHE_PATH)
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_GENERIC_FBA_AUDIT_PATH,
    )
    args = parser.parse_args()

    report = build_pinned_human_gem_generic_fba_audit(args.artifact)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.out)


if __name__ == "__main__":
    main()
