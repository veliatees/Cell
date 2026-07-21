from __future__ import annotations

import argparse
import json
from pathlib import Path

from cell_engine.validation.external_review import (
    build_external_validation_program,
    external_validation_snapshot,
    render_external_review_dossier,
    validate_external_validation_program,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export the machine-readable and human-readable external review packet."
    )
    parser.add_argument(
        "--json-out",
        default="data/validation/external_validation_program.v1.json",
    )
    parser.add_argument(
        "--markdown-out",
        default="docs/validation/external-review-dossier.md",
    )
    args = parser.parse_args()

    program = build_external_validation_program()
    validate_external_validation_program(program)

    json_out = Path(args.json_out)
    markdown_out = Path(args.markdown_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(external_validation_snapshot(), indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    markdown_out.write_text(
        render_external_review_dossier(program),
        encoding="utf-8",
    )
    print(json_out)
    print(markdown_out)


if __name__ == "__main__":
    main()
