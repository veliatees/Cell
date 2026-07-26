from __future__ import annotations

import argparse
import json
from pathlib import Path

from cell_engine.quantitative.human_gem_phh_fastcore_blocker_diagnostics import (
    DEFAULT_AUDIT_PATH,
    build_pinned_human_gem_phh_fastcore_blocker_diagnostics,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Diagnose the adaptive PHH FASTCORE output blockers against the "
            "checksum-pinned generic Human-GEM network."
        )
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_AUDIT_PATH)
    args = parser.parse_args()

    report = build_pinned_human_gem_phh_fastcore_blocker_diagnostics()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.out)


if __name__ == "__main__":
    main()
