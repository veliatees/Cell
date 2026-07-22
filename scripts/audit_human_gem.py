from __future__ import annotations

import argparse
import json
from pathlib import Path

from cell_engine.quantitative.human_gem_structural_audit import (
    DEFAULT_MANIFEST_PATH,
    DEFAULT_REPORT_PATH,
    ROOT,
    audit_pinned_human_gem,
    load_human_gem_manifest,
    validate_committed_human_gem_audit,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit pinned Human-GEM SBML structure, elemental balance and charge balance."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--artifact", type=Path)
    parser.add_argument("--out", type=Path, default=DEFAULT_REPORT_PATH)
    args = parser.parse_args()

    manifest = load_human_gem_manifest(args.manifest)
    artifact = args.artifact or ROOT / manifest["expected_local_cache_path"]
    report = audit_pinned_human_gem(artifact, args.manifest)
    validate_committed_human_gem_audit(report, manifest)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(args.out)


if __name__ == "__main__":
    main()
