from __future__ import annotations

import argparse
import json
from pathlib import Path

from cell_engine.quantitative.published_glucose_model import (
    RUNTIME_VALIDATION_PATH,
    generate_runtime_validation,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Regenerate the pinned Koenig 2012 shadow-model validation artifact.")
    parser.add_argument("--out", type=Path, default=RUNTIME_VALIDATION_PATH)
    args = parser.parse_args()
    artifact = generate_runtime_validation()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
