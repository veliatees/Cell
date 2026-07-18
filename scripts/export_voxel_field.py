"""Export the per-voxel reference-nucleus protein field for the renderer.

Builds the hepatocyte voxel lattice, seeds selected groups at the seven-donor
median copies per nucleus into their coarse compartment, and writes the sparse field
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
        help="multiply reference-nucleus counts (1.0 = source medians)",
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
            "copiesPerReferenceNucleus": int(round(p.copies_typical * args.scale)),
            "copyNumberDenominator": p.copy_number_denominator,
            "aggregation": p.aggregation,
            "quality": p.quality,
            "footprintNm": p.footprint_nm,
        }
        for p in PROTEINS
    ]
    totals = {p.id: state.total(p.id) for p in PROTEINS}

    payload = {
        "_note": "Per-voxel protein-group population for one reference nucleus. "
        "Seven-donor median copy numbers from Wisniewski 2016 Supplementary Table 2 "
        "seeded into their correct compartment voxels. Positions are normalised "
        "cell coordinates in [-1,1]; counts are populations, not atoms. Geometry "
        "(membrane split by x-sign, ~20% hashed mitochondrial fraction) is "
        "schematic; total abundance is measured but surface/active fractions are unknown.",
        "lattice": {"n": args.n, "dxUm": round(lattice.dx_um, 12), "scale": args.scale},
        "proteins": proteins_meta,
        "totals": totals,
        "voxels": field,
    }
    args.out.write_text(json.dumps(payload))
    print(f"wrote {args.out} | {len(field)} occupied voxels | totals: {totals}")


if __name__ == "__main__":
    main()
