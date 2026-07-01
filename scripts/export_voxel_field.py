"""Export the per-voxel protein population field for the renderer.

Builds the hepatocyte voxel lattice, seeds every protein at its real per-cell
copy number into its correct compartment, and writes the sparse per-voxel field
to public/cell_voxel_field.json. The renderer draws this as a population density
(real numbers, in the right place) rather than atomic structures.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cell_engine.core.random import EngineRng
from cell_engine.quantitative.hepatocyte_counts import PROTEINS
from cell_engine.stochastic.hepatocyte_rdme import (
    build_hepatocyte_lattice,
    seed_proteins,
    voxel_field,
)

_DEFAULT_OUT = Path(__file__).resolve().parents[1] / "public" / "cell_voxel_field.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=20, help="lattice voxels per axis")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="multiply real copy numbers (1.0 = true counts)",
    )
    parser.add_argument("--out", type=Path, default=_DEFAULT_OUT)
    args = parser.parse_args()

    lattice = build_hepatocyte_lattice(n=args.n)
    rng = EngineRng(seed=args.seed)
    state = seed_proteins(lattice, rng, scale=args.scale)
    field = voxel_field(lattice, state)

    proteins_meta = [
        {
            "id": p.id,
            "gene": p.gene,
            "location": p.location,
            "copiesPerCell": int(round(p.copies_typical * args.scale)),
            "quality": p.quality,
            "footprintNm": p.footprint_nm,
        }
        for p in PROTEINS
    ]
    totals = {p.id: state.total(p.id) for p in PROTEINS}

    payload = {
        "_note": "Per-voxel protein population for the hepatocyte. Real per-cell "
        "copy numbers (order-of-magnitude; see docs/12-hepatocyte-quantitative.md) "
        "seeded into their correct compartment voxels. Positions are normalised "
        "cell coordinates in [-1,1]; counts are populations, not atoms. Geometry "
        "(membrane split by x-sign, ~20% hashed mitochondrial fraction) is "
        "schematic; the copy numbers and compartment assignments are grounded.",
        "lattice": {"n": args.n, "dxUm": lattice.dx_um, "scale": args.scale},
        "proteins": proteins_meta,
        "totals": totals,
        "voxels": field,
    }
    args.out.write_text(json.dumps(payload))
    print(f"wrote {args.out} | {len(field)} occupied voxels | totals: {totals}")


if __name__ == "__main__":
    main()
