"""Wire the RDME voxel engine to real hepatocyte geometry and seed each protein
at its true per-cell copy number, in the correct compartment.

This is the spatial realisation of "put the real number of proteins in the right
place": a cubic lattice is carved into a hepatocyte (an exterior, a thin plasma-
membrane shell split into basolateral/canalicular domains, a cytosol interior,
and a dispersed mitochondrial fraction), and every protein from the grounded
quantitative dataset is distributed across only the voxels of its compartment,
summing to its real copy number. Counts are populations (integers per voxel),
never molecule objects, so even ~5x10^7 CPS1 copies cost nothing to store.

Geometry is deliberately coarse and is flagged as such: the membrane split by
x-sign and the hash-based ~20% mitochondrial fraction are schematic stand-ins
for true organelle masks, chosen to match the renderer's domain convention
(basolateral = blood/-x, canalicular = bile/+x). The copy numbers and
compartment assignments are the grounded, honest part.
"""

from __future__ import annotations

from math import sqrt

from cell_engine.core.random import EngineRng
from cell_engine.quantitative.hepatocyte_counts import (
    CELL_DIAMETER_UM,
    PROTEINS,
    ProteinAbundance,
)
from cell_engine.stochastic.rdme import RdmeState, VoxelLattice

EXTERIOR = "exterior"
MEMBRANE_BASOLATERAL = "membrane-basolateral"
MEMBRANE_CANALICULAR = "membrane-canalicular"
CYTOSOL = "cytosol"
MITOCHONDRIA = "mitochondria"

# Which voxel compartments each protein localisation may occupy.
LOCATION_TO_COMPARTMENTS: dict[str, set[str]] = {
    "membrane-basolateral": {MEMBRANE_BASOLATERAL},
    "membrane-canalicular": {MEMBRANE_CANALICULAR},
    "cytosol": {CYTOSOL},
    "mitochondria": {MITOCHONDRIA},
}

# Mitochondrial volume fraction of the cytoplasm (rat stereology, ~20%).
_MITO_FRACTION = 0.20


def _mito_hash(x: int, y: int, z: int) -> bool:
    """Deterministic, reproducible ~20% interior voxels flagged mitochondrial."""
    h = ((x * 73856093) ^ (y * 19349663) ^ (z * 83492791)) & 0xFFFFFFFF
    return (h % 1000) < int(_MITO_FRACTION * 1000)


def build_hepatocyte_lattice(n: int = 20, diameter_um: float = CELL_DIAMETER_UM) -> VoxelLattice:
    """A cubic n^3 lattice carved into a hepatocyte with labelled compartments."""
    if n < 4:
        raise ValueError("n must be >= 4 to resolve a membrane shell")
    dx = diameter_um / n
    center = (n - 1) / 2.0
    radius = n / 2.0

    def compartment_of(x: int, y: int, z: int) -> str:
        r = sqrt((x - center) ** 2 + (y - center) ** 2 + (z - center) ** 2)
        if r > radius:
            return EXTERIOR
        if r > radius - 1.0:  # ~1-voxel-thick plasma-membrane shell
            return MEMBRANE_CANALICULAR if (x - center) > 0 else MEMBRANE_BASOLATERAL
        return MITOCHONDRIA if _mito_hash(x, y, z) else CYTOSOL

    return VoxelLattice.build(n, n, n, dx, compartment_of)


def _compartment_voxels(lattice: VoxelLattice) -> dict[str, list[int]]:
    out: dict[str, list[int]] = {}
    for idx in range(lattice.size):
        out.setdefault(lattice.compartment_of(idx), []).append(idx)
    return out


def allowed_compartments_for_proteins(
    proteins: tuple[ProteinAbundance, ...] = PROTEINS,
) -> dict[str, set[str]]:
    """Map each protein id -> the set of voxel compartments it may occupy."""
    return {p.id: LOCATION_TO_COMPARTMENTS[p.location] for p in proteins}


def seed_proteins(
    lattice: VoxelLattice,
    rng: EngineRng,
    *,
    scale: float = 1.0,
    proteins: tuple[ProteinAbundance, ...] = PROTEINS,
) -> RdmeState:
    """Distribute each protein's true copy number across its compartment voxels.

    Population is conserved exactly: every voxel of the compartment gets the even
    share, and the remainder is scattered one-per-random-voxel. ``scale`` lets a
    caller thin the absolute numbers (e.g. for export) while keeping the spatial
    structure and relative abundances. Species are keyed by protein id.
    """
    if scale <= 0:
        raise ValueError("scale must be positive")
    comp_voxels = _compartment_voxels(lattice)
    state = RdmeState()
    for p in proteins:
        voxels = sorted(
            v for comp in LOCATION_TO_COMPARTMENTS[p.location] for v in comp_voxels.get(comp, [])
        )
        if not voxels:
            continue
        total = int(round(p.copies_typical * scale))
        if total <= 0:
            continue
        base, rem = divmod(total, len(voxels))
        if base:
            for v in voxels:
                state.add(v, p.id, base)
        for _ in range(rem):
            v = voxels[int(rng.random() * len(voxels)) % len(voxels)]
            state.add(v, p.id, 1)
    return state


def voxel_field(lattice: VoxelLattice, state: RdmeState) -> list[dict]:
    """Export occupied voxels as renderer-friendly records.

    Each record: normalised cell coordinates in [-1, 1], the voxel compartment,
    and per-protein counts. Only non-empty voxels are emitted (sparse).
    """
    center = (lattice.nx - 1) / 2.0
    half = lattice.nx / 2.0
    records: list[dict] = []
    for voxel in state.occupied_voxels():
        counts = state.voxel_counts(voxel)
        if not counts:
            continue
        x, y, z = lattice.coords(voxel)
        records.append(
            {
                "p": [(x - center) / half, (y - center) / half, (z - center) / half],
                "c": lattice.compartment_of(voxel),
                "n": counts,
            }
        )
    return records
