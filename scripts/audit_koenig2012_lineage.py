from __future__ import annotations

import argparse
import json
from pathlib import Path

from cell_engine.quantitative.published_glucose_lineage import (
    LINEAGE_REPRODUCTION_PATH,
    generate_lineage_reproduction,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Regenerate the pinned Koenig model-lineage audit.")
    parser.add_argument("--legacy-model", type=Path, required=True)
    parser.add_argument("--tracked-result", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=LINEAGE_REPRODUCTION_PATH)
    args = parser.parse_args()
    artifact = generate_lineage_reproduction(args.legacy_model, args.tracked_result)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
