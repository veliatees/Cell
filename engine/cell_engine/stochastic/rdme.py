"""Spatial population engine: the reaction-diffusion master equation (RDME).

The well-mixed core (``cell_model`` / ``integrators``) holds the whole cell as
*counts* with no spatial information. This module adds the spatial layer the
user's "put the protein in the right place" requires, at the *population* level
that all whole-cell models use: space is divided into voxels, each voxel holds a
copy-number per species (well-mixed *within* the voxel), reactions fire locally
per voxel, and movement is modelled as stochastic diffusion *hops* of whole
molecules between neighbouring voxels.

Design choices (all stdlib, no numpy):

* **Population, not particles.** We never instantiate a molecule. State is a
  *sparse* ``dict[voxel -> {species: count}]`` -- a voxel with no molecules is
  simply absent, so most of a 3-D lattice costs nothing because most species are
  zero in most voxels.
* **Integer voxel IDs.** Voxels are addressed by a single ``int`` index; the
  lattice geometry (per-voxel compartment label) is stored in a compact
  ``array('i')`` rather than a list of objects.
* **Tau-leaping.** Both the reaction and the diffusion phase use Poisson
  tau-leaps, so cost is independent of flux/abundance -- the spatial analogue of
  the SSA<->CLE hybrid: abundant species stay cheap as counts/fields.
* **Compartment confinement.** A species can be restricted to a set of
  compartments; hops into a disallowed voxel are reflected. This is what keeps a
  membrane transporter in membrane voxels and a matrix enzyme inside the
  mitochondrion -- the structurally correct location, enforced by the dynamics.

A diffusion hop rate per molecule to one neighbour is ``D / dx^2`` (1/s) with
``D`` in um^2/s and ``dx`` the voxel edge in um. Keep ``tau`` below
``rdme_stable_tau`` so the per-molecule hop probability stays well under one.
"""

from __future__ import annotations

from array import array
from collections.abc import Mapping
from dataclasses import dataclass, field

from cell_engine.core.random import EngineRng
from cell_engine.stochastic.reactions import ReactionNetwork

# 1 um^3 = 1e-15 L (1 L = 1e15 um^3).
_UM3_TO_L = 1.0e-15


@dataclass(frozen=True)
class VoxelLattice:
    """A 3-D grid of cubic voxels, each tagged with a compartment label.

    ``compartments`` is a per-voxel label in (z*ny + y)*nx + x order. It is held
    as small integer codes in a compact ``array`` plus a code<->name table.
    """

    nx: int
    ny: int
    nz: int
    dx_um: float
    _codes: array = field(repr=False)
    _names: tuple[str, ...] = field(repr=False)

    @classmethod
    def build(
        cls, nx: int, ny: int, nz: int, dx_um: float, compartment_of=lambda x, y, z: "cytosol"
    ) -> "VoxelLattice":
        if min(nx, ny, nz) < 1:
            raise ValueError("lattice needs at least one voxel per axis")
        if dx_um <= 0:
            raise ValueError("dx_um must be positive")
        name_to_code: dict[str, int] = {}
        names: list[str] = []
        codes = array("i", bytes(4 * nx * ny * nz))
        for z in range(nz):
            for y in range(ny):
                for x in range(nx):
                    label = compartment_of(x, y, z)
                    code = name_to_code.get(label)
                    if code is None:
                        code = len(names)
                        name_to_code[label] = code
                        names.append(label)
                    codes[(z * ny + y) * nx + x] = code
        return cls(nx, ny, nz, dx_um, codes, tuple(names))

    @property
    def size(self) -> int:
        return self.nx * self.ny * self.nz

    @property
    def voxel_volume_l(self) -> float:
        return (self.dx_um ** 3) * _UM3_TO_L

    def index(self, x: int, y: int, z: int) -> int:
        return (z * self.ny + y) * self.nx + x

    def coords(self, idx: int) -> tuple[int, int, int]:
        x = idx % self.nx
        y = (idx // self.nx) % self.ny
        z = idx // (self.nx * self.ny)
        return x, y, z

    def compartment_of(self, idx: int) -> str:
        return self._names[self._codes[idx]]

    def neighbors(self, idx: int) -> list[int]:
        x, y, z = self.coords(idx)
        out: list[int] = []
        if x > 0:
            out.append(self.index(x - 1, y, z))
        if x < self.nx - 1:
            out.append(self.index(x + 1, y, z))
        if y > 0:
            out.append(self.index(x, y - 1, z))
        if y < self.ny - 1:
            out.append(self.index(x, y + 1, z))
        if z > 0:
            out.append(self.index(x, y, z - 1))
        if z < self.nz - 1:
            out.append(self.index(x, y, z + 1))
        return out


class RdmeState:
    """Sparse per-voxel population: ``{voxel_index: {species: count}}``.

    Only non-empty (species, voxel) entries are stored, so an almost-empty
    lattice costs almost nothing.
    """

    __slots__ = ("_v",)

    def __init__(self) -> None:
        self._v: dict[int, dict[str, int]] = {}

    def get(self, voxel: int, species: str) -> int:
        return self._v.get(voxel, {}).get(species, 0)

    def add(self, voxel: int, species: str, delta: int) -> None:
        if delta == 0:
            return
        cell = self._v.get(voxel)
        if cell is None:
            if delta <= 0:
                return
            self._v[voxel] = {species: delta}
            return
        new = cell.get(species, 0) + delta
        if new <= 0:
            cell.pop(species, None)
            if not cell:
                self._v.pop(voxel, None)
        else:
            cell[species] = new

    def set(self, voxel: int, species: str, count: int) -> None:
        self.add(voxel, species, count - self.get(voxel, species))

    def total(self, species: str) -> int:
        return sum(cell.get(species, 0) for cell in self._v.values())

    def occupied_voxels(self) -> list[int]:
        return list(self._v.keys())

    def voxel_counts(self, voxel: int) -> dict[str, int]:
        return dict(self._v.get(voxel, {}))

    def n_occupied(self) -> int:
        return len(self._v)

    def copy(self) -> "RdmeState":
        clone = RdmeState()
        clone._v = {v: dict(c) for v, c in self._v.items()}
        return clone


def rdme_stable_tau(diffusion: Mapping[str, float], dx_um: float, *, safety: float = 0.1) -> float:
    """A conservative tau so the per-molecule hop probability stays small.

    Per neighbour the hop rate is ``D/dx^2``; with up to 6 neighbours the total
    leaving rate per molecule is ``6*D/dx^2``. We return ``safety / (6*Dmax/dx^2)``
    so a molecule's chance of moving in one tau is ~``safety``.
    """
    d_max = max(diffusion.values(), default=0.0)
    if d_max <= 0.0:
        return float("inf")
    return safety / (6.0 * d_max / (dx_um ** 2))


def rdme_tau_leap_step(
    lattice: VoxelLattice,
    network: ReactionNetwork,
    diffusion: Mapping[str, float],
    state: RdmeState,
    tau: float,
    rng: EngineRng,
    *,
    allowed_compartments: Mapping[str, set[str]] | None = None,
) -> RdmeState:
    """Advance the spatial population by one Poisson tau-leap of length ``tau``.

    Two phases, both leaped:

    1. **Reaction** -- in every occupied voxel, fire each reaction
       ``Poisson(propensity(local_counts, voxel_volume) * tau)`` times and apply
       the net stoichiometry locally.
    2. **Diffusion** -- each molecule may hop to a uniformly chosen *allowed*
       neighbour with rate ``D/dx^2``. The number leaving a voxel is Poisson,
       capped at the molecules present, so counts are conserved exactly.

    Returns a new ``RdmeState`` (the input is not mutated).
    """
    if tau <= 0:
        raise ValueError("tau must be positive")

    vol_l = lattice.voxel_volume_l
    dx2 = lattice.dx_um ** 2

    def species_allowed(species: str, voxel: int) -> bool:
        if allowed_compartments is None:
            return True
        allow = allowed_compartments.get(species)
        if allow is None:
            return True
        return lattice.compartment_of(voxel) in allow

    # ---- Phase 1: local reactions (mutate a working copy in place) ----
    # Propensities must use the *voxel* volume (second-order rates depend on it),
    # so evaluate the same reactions on a network bound to the voxel volume.
    voxel_network = ReactionNetwork(network.species, network.reactions, vol_l)
    work = state.copy()
    for voxel in state.occupied_voxels():
        local = {s: float(c) for s, c in state.voxel_counts(voxel).items()}
        if not local:
            continue
        props = voxel_network.propensities(local)
        for reaction, a in zip(voxel_network.reactions, props):
            if a <= 0.0:
                continue
            fires = rng.poisson(a * tau)
            if fires == 0:
                continue
            for species, delta in reaction.net_change().items():
                work.add(voxel, species, delta * fires)

    # ---- Phase 2: diffusion hops (read post-reaction, write to fresh state) ----
    post = work.copy()
    result = work.copy()
    for voxel in post.occupied_voxels():
        neigh = lattice.neighbors(voxel)
        for species, count in post.voxel_counts(voxel).items():
            d = diffusion.get(species, 0.0)
            if d <= 0.0 or count <= 0:
                continue
            valid = [n for n in neigh if species_allowed(species, n)]
            if not valid:
                continue
            p_total = (d / dx2) * tau * len(valid)
            leaving = rng.poisson(p_total * count)
            if leaving <= 0:
                continue
            if leaving > count:
                leaving = count
            result.add(voxel, species, -leaving)
            for _ in range(leaving):
                target = valid[int(rng.random() * len(valid)) % len(valid)]
                result.add(target, species, 1)

    return result


def simulate_rdme(
    lattice: VoxelLattice,
    network: ReactionNetwork,
    diffusion: Mapping[str, float],
    initial: RdmeState,
    t_end: float,
    tau: float,
    rng: EngineRng,
    *,
    allowed_compartments: Mapping[str, set[str]] | None = None,
) -> RdmeState:
    """Run the RDME to ``t_end`` in fixed Poisson tau-leaps of size ``tau``."""
    if tau <= 0:
        raise ValueError("tau must be positive")
    state = initial.copy()
    t = 0.0
    while t < t_end - 1e-12:
        step = min(tau, t_end - t)
        state = rdme_tau_leap_step(
            lattice, network, diffusion, state, step, rng,
            allowed_compartments=allowed_compartments,
        )
        t += step
    return state
