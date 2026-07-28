from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from cell_engine.quantitative.human_gem_phh_fastcore_context import (
    DEFAULT_AUDIT_PATH,
    build_pinned_human_gem_phh_fastcore_context_audit,
)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(
        description=(
            "Extract and audit the seven-donor resection-PHH total-proteome "
            "supported structural Human-GEM context candidate."
        )
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_AUDIT_PATH)
    args = parser.parse_args()

    report = build_pinned_human_gem_phh_fastcore_context_audit()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.out)


if __name__ == "__main__":
    main()
