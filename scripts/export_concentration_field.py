"""Export per-voxel steady-state concentration fields for the renderer.

This is the spatial *concentration* companion to ``export_voxel_field.py`` (which
exports static protein populations). It shows what the RDME's diffusion produces
as a spatial gradient across a polarized hepatocyte:

  * ``glucose`` — a sinusoid -> canaliculus gradient. Glucose enters from the
    blood-facing (basolateral, -x) membrane at the physiological blood level and
    is consumed as it diffuses across the cytosol (glucokinase / glycolysis), so
    its concentration is highest near the sinusoid and falls toward the bile pole.
  * ``atp`` — mitochondrial micro-domains. ATP is produced in the dispersed
    mitochondrial voxels and consumed everywhere by ATPases, so it forms bright
    halos around mitochondria that decay over a short diffusion length.

**What is grounded, what is schematic.** The lattice geometry, compartment
masks and diffusion coefficients are the same real hepatocyte lattice used by the
population export (``build_hepatocyte_lattice``). The field itself is the
*deterministic mean-field steady state* of the very same reaction-diffusion the
RDME samples stochastically: solving ``D nabla^2 C - k C + S = 0`` on the lattice
by relaxation. We solve the mean field (not the per-molecule SSA) purely for
speed and smoothness of a static export -- the physics, geometry and coefficients
are identical to the stochastic engine. Diffusion coefficients are effective
crowded-cytosol values (order-of-magnitude); the absolute glucose scale is pinned
to the physiological blood level (~5 mM). Everything is flagged below.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cell_engine.stochastic.hepatocyte_rdme import (
    EXTERIOR,
    MEMBRANE_BASOLATERAL,
    MITOCHONDRIA,
    build_hepatocyte_lattice,
)
from cell_engine.stochastic.rdme import VoxelLattice

_DEFAULT_OUT = (
    Path(__file__).resolve().parents[1] / "public" / "cell_concentration_field.json"
)

# --- Effective diffusion coefficients (um^2/s), crowded cytosol, order-of-mag.
#     Free-solution values are ~5-10x larger; the cytosol slows small solutes to
#     roughly these effective values (Kuehn 2011; Verkman 2002 reviews).
D_GLUCOSE = 100.0
D_ATP = 150.0

# --- First-order consumption (1/s). Chosen so the diffusion length
#     lambda = sqrt(D/k) is physiologically sensible: ~14 um for glucose (a gentle
#     cell-spanning gradient) and ~1 um for ATP (tight peri-mitochondrial
#     micro-domains that decay sharply between the dispersed sources).
#     Order-of-magnitude, flagged.
K_GLUCOSE = 0.5
K_ATP = 150.0

# --- Boundary / source levels (mM).
GLUCOSE_BLOOD_MM = 5.0  # physiological fed blood glucose, HMDB range 3.9-5.8
ATP_MITO_MM = 5.0  # mitochondrial ATP source level (order-of-magnitude)


def _interior(lattice: VoxelLattice) -> list[int]:
    return [
        idx for idx in range(lattice.size) if lattice.compartment_of(idx) != EXTERIOR
    ]


def relax_steady_state(
    lattice: VoxelLattice,
    *,
    diffusion: float,
    consumption: float,
    fixed: dict[int, float],
    produce: dict[int, float],
    iterations: int,
    tol: float = 1e-6,
) -> dict[int, float]:
    """Gauss-Seidel relaxation of ``D nabla^2 C - k C + S = 0`` on the lattice.

    Exterior voxels are excluded and treated as zero-flux (Neumann) walls -- they
    are simply not counted as neighbours. ``fixed`` voxels are held at a Dirichlet
    value (sources/boundaries); ``produce`` adds a per-voxel zeroth-order source
    term ``S`` (mM/s) to interior voxels. Returns concentration (mM) per voxel.
    """
    dx2 = lattice.dx_um ** 2
    coef = diffusion / dx2  # 1/s per neighbour
    conc: dict[int, float] = {idx: 0.0 for idx in _interior(lattice)}
    for idx, value in fixed.items():
        conc[idx] = value
    # Precompute the non-exterior neighbours of each free voxel.
    free = [idx for idx in conc if idx not in fixed]
    neighbours = {
        idx: [n for n in lattice.neighbors(idx) if n in conc] for idx in free
    }
    for _ in range(iterations):
        max_delta = 0.0
        for idx in free:
            nbs = neighbours[idx]
            if not nbs:
                continue
            flux = coef * sum(conc[n] for n in nbs)
            denom = coef * len(nbs) + consumption
            new = (flux + produce.get(idx, 0.0)) / denom
            max_delta = max(max_delta, abs(new - conc[idx]))
            conc[idx] = new
        if max_delta < tol:
            break
    return conc


def glucose_field(lattice: VoxelLattice, iterations: int) -> dict[int, float]:
    """Sinusoid -> canaliculus glucose gradient (basolateral source + cytosolic
    consumption)."""
    fixed = {
        idx: GLUCOSE_BLOOD_MM
        for idx in range(lattice.size)
        if lattice.compartment_of(idx) == MEMBRANE_BASOLATERAL
    }
    return relax_steady_state(
        lattice,
        diffusion=D_GLUCOSE,
        consumption=K_GLUCOSE,
        fixed=fixed,
        produce={},
        iterations=iterations,
    )


def atp_field(lattice: VoxelLattice, iterations: int) -> dict[int, float]:
    """Peri-mitochondrial ATP micro-domains (mitochondrial production + ubiquitous
    consumption). Mitochondrial voxels are held at the source level; ATP diffuses
    out and is consumed, decaying over lambda = sqrt(D/k) ~ 2.7 um."""
    fixed = {
        idx: ATP_MITO_MM
        for idx in range(lattice.size)
        if lattice.compartment_of(idx) == MITOCHONDRIA
    }
    return relax_steady_state(
        lattice,
        diffusion=D_ATP,
        consumption=K_ATP,
        fixed=fixed,
        produce={},
        iterations=iterations,
    )


def build_payload(n: int, iterations: int) -> dict:
    lattice = build_hepatocyte_lattice(n=n)
    glucose = glucose_field(lattice, iterations)
    atp = atp_field(lattice, iterations)

    center = (lattice.nx - 1) / 2.0
    half = lattice.nx / 2.0
    voxels: list[dict] = []
    for idx in _interior(lattice):
        x, y, z = lattice.coords(idx)
        voxels.append(
            {
                "p": [
                    (x - center) / half,
                    (y - center) / half,
                    (z - center) / half,
                ],
                "c": lattice.compartment_of(idx),
                "g": round(glucose.get(idx, 0.0), 4),
                "a": round(atp.get(idx, 0.0), 4),
            }
        )

    def _range(key: str) -> list[float]:
        vals = [v[key] for v in voxels]
        return [min(vals), max(vals)] if vals else [0.0, 0.0]

    return {
        "_note": "Per-voxel steady-state concentration fields for the polarized "
        "hepatocyte. Deterministic mean-field steady state of the RDME diffusion "
        "(same lattice/geometry/coefficients): D*laplacian(C) - k*C + S = 0 solved "
        "by relaxation. glucose = sinusoid->canaliculus gradient (basolateral "
        "source 5 mM + cytosolic consumption); atp = peri-mitochondrial "
        "micro-domains. Concentrations in mM. Diffusion coefficients and "
        "consumption rates are effective crowded-cytosol, order-of-magnitude; the "
        "glucose scale is pinned to physiological blood glucose. Positions are "
        "normalised cell coordinates in [-1,1].",
        "lattice": {"n": lattice.nx, "dxUm": lattice.dx_um},
        "params": {
            "glucose": {
                "diffusionUm2PerS": D_GLUCOSE,
                "consumptionPerS": K_GLUCOSE,
                "bloodMM": GLUCOSE_BLOOD_MM,
                "unit": "mM",
                "quality": "order-of-magnitude (D,k); scale pinned to blood glucose",
            },
            "atp": {
                "diffusionUm2PerS": D_ATP,
                "consumptionPerS": K_ATP,
                "sourceMM": ATP_MITO_MM,
                "unit": "mM",
                "quality": "order-of-magnitude",
            },
        },
        "species": {
            "g": {"label": "Glucose", "range": _range("g"), "unit": "mM"},
            "a": {"label": "ATP", "range": _range("a"), "unit": "mM"},
        },
        "voxels": voxels,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=20, help="lattice voxels per axis")
    parser.add_argument(
        "--iterations", type=int, default=4000, help="max relaxation sweeps"
    )
    parser.add_argument("--out", type=Path, default=_DEFAULT_OUT)
    args = parser.parse_args()

    payload = build_payload(args.n, args.iterations)
    args.out.write_text(json.dumps(payload))
    g = payload["species"]["g"]["range"]
    a = payload["species"]["a"]["range"]
    print(
        f"wrote {args.out} | {len(payload['voxels'])} interior voxels | "
        f"glucose {g[0]:.2f}-{g[1]:.2f} mM | atp {a[0]:.2f}-{a[1]:.2f} mM"
    )


if __name__ == "__main__":
    main()
