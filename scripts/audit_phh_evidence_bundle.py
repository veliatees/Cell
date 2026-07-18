from __future__ import annotations

import argparse
import json
from pathlib import Path

from cell_engine.validation.evidence_intake import validate_evidence_bundle


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit a nine-file healthy-human/PHH evidence delivery.")
    parser.add_argument("bundle", type=Path, help="Directory containing the Claude Science delivery")
    parser.add_argument("--out", type=Path, default=None, help="Optional path for the immutable JSON audit")
    args = parser.parse_args()

    audit = validate_evidence_bundle(args.bundle).to_dict()
    rendered = json.dumps(audit, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(rendered, end="")
        return
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(rendered, encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
