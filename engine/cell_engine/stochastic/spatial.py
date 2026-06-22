from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable, Literal

# A reaction callback gets (voxel_index, {species: field value}) and returns the
# per-species rate of change in the same units per second at that voxel.
ReactionFn = Callable[[int, dict[str, float]], dict[str, float]]
SpatialQuantity = Literal["concentration_mM", "molecule_count"]

_VALID_QUANTITIES: set[str] = {"concentration_mM", "molecule_count"}


@dataclass(frozen=True)
class SpatialField:
    """A 1-D row of voxels holding per-species scalar fields.

    This replaces the well-mixed assumption: a value varies along space.
    ``quantity`` makes the unit contract explicit:

    - ``"concentration_mM"``: values are concentrations and reaction rates are
      mM/s.
    - ``"molecule_count"``: values are molecule counts and reaction rates are
      molecules/s.

    The explicit diffusion update is linear, so it can advance either quantity
    as long as a field and its reaction callback use the same quantity. ``dx_um``
    is the voxel width; ``conc[species]`` is a tuple of length ``n``.
    """

    species: tuple[str, ...]
    dx_um: float
    conc: dict[str, tuple[float, ...]]
    quantity: SpatialQuantity = "concentration_mM"

    def __post_init__(self) -> None:
        if self.quantity not in _VALID_QUANTITIES:
            raise ValueError("quantity must be 'concentration_mM' or 'molecule_count'")
        if not self.species:
            raise ValueError("species must not be empty")
        missing = tuple(s for s in self.species if s not in self.conc)
        if missing:
            raise ValueError(f"missing spatial profile for species: {missing!r}")
        lengths = {len(self.conc[s]) for s in self.species}
        if len(lengths) != 1:
            raise ValueError("all species profiles must have the same voxel count")
        if next(iter(lengths)) <= 0:
            raise ValueError("spatial fields must contain at least one voxel")

    @property
    def n(self) -> int:
        return len(next(iter(self.conc.values())))

    def total(self, species: str) -> float:
        return sum(self.conc[species])

    def profile(self, species: str) -> tuple[float, ...]:
        return self.conc[species]


def uniform_field(
    species: tuple[str, ...],
    n: int,
    dx_um: float,
    value: float = 0.0,
    *,
    quantity: SpatialQuantity = "concentration_mM",
) -> SpatialField:
    return SpatialField(
        species=species,
        dx_um=dx_um,
        conc={s: tuple(value for _ in range(n)) for s in species},
        quantity=quantity,
    )


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
    reaction (if given) is applied per voxel and must use the same quantity as
    ``field``. Requires ``dt_s <= cfl_limit_dt(diffusion, dx)`` for stability.
    """
    if dt_s <= 0:
        raise ValueError("dt_s must be positive")
    if dt_s > cfl_limit_dt(diffusion, field.dx_um) + 1e-15:
        raise ValueError("dt_s exceeds the diffusion CFL stability limit")
    reaction_quantity = _reaction_quantity(reaction)
    if reaction_quantity is not None and reaction_quantity != field.quantity:
        raise ValueError(
            f"reaction expects {reaction_quantity} field values, got {field.quantity}"
        )

    species = field.species
    n = field.n
    dx2 = field.dx_um * field.dx_um
    values = {s: list(field.conc[s]) for s in species}

    for _ in range(steps):
        new = {s: list(values[s]) for s in species}
        for s in species:
            d = diffusion.get(s, 0.0)
            if d <= 0:
                continue
            c = values[s]
            coeff = d * dt_s / dx2
            for i in range(n):
                left = c[i - 1] if i > 0 else c[i]        # reflecting boundary
                right = c[i + 1] if i < n - 1 else c[i]    # reflecting boundary
                new[s][i] = c[i] + coeff * (left - 2.0 * c[i] + right)
        if reaction is not None:
            for i in range(n):
                voxel = {s: values[s][i] for s in species}
                ddt = reaction(i, voxel)
                for s, rate in ddt.items():
                    value = new[s][i] + rate * dt_s
                    new[s][i] = value if value > 0.0 else 0.0
        values = new

    return replace(field, conc={s: tuple(values[s]) for s in species})


def _reaction_quantity(reaction: ReactionFn | None) -> SpatialQuantity | None:
    if reaction is None:
        return None
    quantity = getattr(reaction, "quantity", None)
    if quantity is None:
        return None
    if quantity not in _VALID_QUANTITIES:
        raise ValueError("reaction quantity must be 'concentration_mM' or 'molecule_count'")
    return quantity


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
    each voxel field value must be a molecule count in a sub-volume, the
    network's own propensities drive the local count-rate of change, and
    diffusion moves species between voxels at their grounded diffusion
    coefficients. Use with ``SpatialField(quantity="molecule_count")``; passing
    the returned callback to a concentration field is rejected by
    :func:`react_diffuse`.
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

    reaction.quantity = "molecule_count"  # type: ignore[attr-defined]
    return reaction
