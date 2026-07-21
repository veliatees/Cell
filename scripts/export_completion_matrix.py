from __future__ import annotations

import argparse
import json
from pathlib import Path

from cell_engine.validation.completion_matrix import (
    build_hepatocyte_completion_matrix,
    validate_hepatocyte_completion_matrix,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the scoped hepatocyte completion ledger.")
    parser.add_argument(
        "--out",
        default="data/validation/hepatocyte_completion_matrix.v1.json",
    )
    args = parser.parse_args()
    matrix = build_hepatocyte_completion_matrix()
    validate_hepatocyte_completion_matrix(matrix)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(matrix, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
