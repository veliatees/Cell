from __future__ import annotations

import argparse
import json
from pathlib import Path

from cell_engine.validation.evidence_readiness import (
    DEFAULT_INCOMING_ROOT,
    phh_evidence_readiness_snapshot,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Audit every registered PHH evidence delivery without activating "
            "parameters or cell-state coupling."
        )
    )
    parser.add_argument(
        "--incoming-root",
        type=Path,
        default=DEFAULT_INCOMING_ROOT,
        help="Root containing versioned evidence-delivery subdirectories",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional output path for the normalized JSON preflight report",
    )
    args = parser.parse_args()

    payload = phh_evidence_readiness_snapshot(args.incoming_root)
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(rendered, end="")
        return
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(rendered, encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
