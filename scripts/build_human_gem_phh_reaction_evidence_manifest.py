from __future__ import annotations

import argparse
import json
from pathlib import Path

from cell_engine.quantitative.human_gem_phh_reaction_evidence_manifest import (
    DEFAULT_MANIFEST_PATH,
    build_pinned_human_gem_phh_reaction_evidence_manifest,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build the reaction-level Human-GEM/PHH evidence-gap research "
            "manifest without inferred biological values."
        )
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_MANIFEST_PATH)
    args = parser.parse_args()

    report = build_pinned_human_gem_phh_reaction_evidence_manifest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.out)


if __name__ == "__main__":
    main()
