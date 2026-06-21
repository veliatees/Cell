from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable

# A reaction callback gets (voxel_index, {species: concentration}) and returns the
# per-species rate of change (concentration / second) at that voxel.
ReactionFn = Callable[[int, dict[str, float]], dict[str, float]]


@dataclass(frozen=True)
class SpatialField:
    """A 1-D row of voxels holding per-species concentrations.

    This replaces the well-mixed assumption: concentration varies along space.
    ``dx_um`` is the voxel width; ``conc[species]`` is a tuple of length ``n``
    (one value per voxel, in mM).
    """

    species: tuple[str, ...]
    dx_um: float
    conc: dict[str, tuple[float, ...]]

    @property
    def n(self) -> int:
        return len(next(iter(self.conc.values())))

    def total(self, species: str) -> float:
        return sum(self.conc[species])

    def profile(self, species: str) -> tuple[float, ...]:
        return self.conc[species]


def uniform_field(species: tuple[str, ...], n: int, dx_um: float, value: float = 0.0) -> SpatialField:
    return SpatialField(species=species, dx_um=dx_um, conc={s: tuple(value for _ in range(n)) for s in species})


def cfl_limit_dt(diffusion: dict[str, float], dx_um: float) -> float:
    """Largest stable explicit-diffusion timestep (D*dt/dx^2 <= 1/2)."""
    d_max = max(diffusion.values(), default=0.0)
    if d_max <= 0:
        return float("inf")
    return 0.5 * dx_um * dx_um / d_max


def react_diffuse(
    field: SpatialField,
    *,
    diffusion: dict[str, float],
    dt_s: float,
    steps: int,
    reaction: ReactionFn | None = None,
) -> SpatialField:
    """Advance the field by explicit reaction-diffusion.

    Diffusion is the discretized Laplacian with reflecting (zero-flux) boundaries;
    reaction (if given) is applied per voxel. Requires
    ``dt_s <= cfl_limit_dt(diffusion, dx)`` for stability.
    """
    if dt_s <= 0:
        raise ValueError("dt_s must be positive")
    if dt_s > cfl_limit_dt(diffusion, field.dx_um) + 1e-15:
        raise ValueError("dt_s exceeds the diffusion CFL stability limit")

    species = field.species
    n = field.n
    dx2 = field.dx_um * field.dx_um
    conc = {s: list(field.conc[s]) for s in species}

    for _ in range(steps):
        new = {s: list(conc[s]) for s in species}
        for s in species:
            d = diffusion.get(s, 0.0)
            if d <= 0:
                continue
            c = conc[s]
            coeff = d * dt_s / dx2
            for i in range(n):
                left = c[i - 1] if i > 0 else c[i]        # reflecting boundary
                right = c[i + 1] if i < n - 1 else c[i]    # reflecting boundary
                new[s][i] = c[i] + coeff * (left - 2.0 * c[i] + right)
        if reaction is not None:
            for i in range(n):
                voxel = {s: conc[s][i] for s in species}
                ddt = reaction(i, voxel)
                for s, rate in ddt.items():
                    value = new[s][i] + rate * dt_s
                    new[s][i] = value if value > 0.0 else 0.0
        conc = new

    return replace(field, conc={s: tuple(conc[s]) for s in species})


def decay_length_um(diffusion_coeff: float, degradation_rate: float) -> float:
    """Reaction-diffusion gradient length scale lambda = sqrt(D / k)."""
    if degradation_rate <= 0:
        raise ValueError("degradation_rate must be positive")
    return (diffusion_coeff / degradation_rate) ** 0.5


# Grounded cytoplasmic diffusion coefficients (um^2/s). Crowding makes these much
# lower than in dilute water. Sources: ATP ~150 (commonly cited); small
# metabolites ~100-300; proteins ~7-12 in mammalian cytoplasm; free Ca2+ heavily
# buffered (~13-65). See "Protein Diffusion in Mammalian Cell Cytoplasm" (PLoS One
# 2011) and cytosolic-diffusion literature.
CYTOPLASMIC_DIFFUSION_UM2_PER_S: dict[str, float] = {
    "ATP": 150.0,
    "ADP": 150.0,
    "glucose": 250.0,
    "pyruvate": 250.0,
    "protein": 10.0,
    "Ca2+": 30.0,
}


def network_voxel_reaction(network, voxel_volume_l: float) -> ReactionFn:
    """Turn a count-based ReactionNetwork into a per-voxel reaction callback.

    This is what wires the real stochastic-engine reaction network into space:
    each voxel holds molecule counts in a sub-volume, the network's own
    propensities drive the local rate of change, and diffusion (below) moves
    species between voxels at their grounded diffusion coefficients.
    """
    reactions = network.reactions

    def reaction(_voxel_index: int, voxel_counts: dict[str, float]) -> dict[str, float]:
        ddt: dict[str, float] = {}
        for r in reactions:
            a = r.propensity(voxel_counts, voxel_volume_l)  # molecules / s
            if a == 0.0:
                continue
            for species, stoich in r.net_change().items():
                ddt[species] = ddt.get(species, 0.0) + stoich * a
        return ddt

    return reaction
