from __future__ import annotations

import argparse
import json
from pathlib import Path

from cell_engine.quantitative.human_gem_fbc_loader import (
    DEFAULT_CACHE_PATH,
    DEFAULT_LOADER_AUDIT_PATH,
    build_fbc_loader_audit,
    load_pinned_human_gem,
    validate_fbc_loader_audit,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Load the checksum-pinned Human-GEM SBML/FBC artifact and write a "
            "small deterministic loader-integrity audit."
        )
    )
    parser.add_argument("--artifact", type=Path, default=DEFAULT_CACHE_PATH)
    parser.add_argument("--out", type=Path, default=DEFAULT_LOADER_AUDIT_PATH)
    args = parser.parse_args()

    model = load_pinned_human_gem(args.artifact)
    report = build_fbc_loader_audit(model)
    validate_fbc_loader_audit(report)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.out)


if __name__ == "__main__":
    main()
