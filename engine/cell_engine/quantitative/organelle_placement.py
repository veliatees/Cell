"""Mixed-species seeded organelle placement for runtime geometry only.

The outer-cell volume is an aggregate normal-control human-liver reference,
whereas the discrete organelle counts, volume fractions and coarse location
categories in ``hepatocyte_counts.ORGANELLES`` are predominantly rat
stereology or order-of-magnitude context. Combining them produces a useful,
deterministic collision and renderer proxy. It does not produce a measured
healthy-PHH organelle population, a donor cell, or human organelle morphometry.

The exact (x, y, z) coordinates are rejection-sampled from a fixed seed. The
same seed reproduces the same non-overlapping numerical scaffold, but neither
the coordinates nor the equivalent-volume spheres are microscopy observations.

Because of that, this module does **not** flip the existing
``may_parameterize_organelle_shapes_from_human_3d`` firewall (which requires a
measured human 3D EM organelle mesh). It exposes its own scoped status.

Organelles whose source gives **no discrete count** (rough/smooth ER, Golgi,
glycogen, lipid droplets) are networks/aggregates, not countable spheres. They
are returned as flagged *regions* (target proxy volume + centroid), never
converted into N spheres. Ribosomes (no volume fraction) are reported as
unplaced.

Bodies are packed with no interpenetration: no body overlaps another, none
enters the nucleus, and every body stays inside an equivalent-sphere cell
envelope. The star-shaped membrane mesh and organelle-vs-membrane contact are a
later refinement; the equivalent-sphere envelope is a conservative inner bound.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import floor, sqrt

from cell_engine.core.provenance import SourceReference
from cell_engine.core.random import EngineRng
from cell_engine.core.serialization import to_plain
from cell_engine.quantitative.geometry import (
    HEPATOCYTE_CANONICAL_CANALICULAR_DIRECTION,
    HEPATOCYTE_REFERENCE_EQUIVALENT_SPHERE_DIAMETER_UM,
    sphere_diameter_um_from_volume,
    sphere_volume_um3_from_diameter,
)
from cell_engine.quantitative.hepatocyte_counts import (
    CELL_VOLUME_UM3,
    ORGANELLES,
    OrganelleQuantity,
)
from cell_engine.quantitative.human_hepatocyte_3d_morphometry import (
    HUMAN_HEPATOCYTE_3D_MORPHOMETRY_SOURCES,
)

Vector3 = tuple[float, float, float]

DATE_VERIFIED = "2026-08-08"
VERSION = "organelle_placement_v2"
STATUS = "mixed_species_seeded_organelle_geometry_proxy"
RUNTIME_GEOMETRY_ROLE = "engine_collision_and_renderer_proxy_only"

PLACEMENT_SOURCES: dict[str, SourceReference] = dict(
    HUMAN_HEPATOCYTE_3D_MORPHOMETRY_SOURCES
)
PLACEMENT_SOURCES.update({
    "weibel1969_rat_liver_stereology": SourceReference(
        id="weibel1969_rat_liver_stereology",
        title=(
            "Correlated morphometric and biochemical studies on the liver "
            "cell. I. Morphometric model, stereologic methods, and normal "
            "morphometric data for rat liver"
        ),
        url="https://pubmed.ncbi.nlm.nih.gov/4891915/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Rat hepatocyte stereology retained only as explicitly "
            "cross-species organelle context."
        ),
    ),
    "blouin1977_rat_liver_stereology": SourceReference(
        id="blouin1977_rat_liver_stereology",
        title=(
            "Distribution of organelles and membranes between hepatocytes "
            "and nonhepatocytes in the rat liver parenchyma"
        ),
        url="https://pubmed.ncbi.nlm.nih.gov/833203/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Rat liver stereology retained only as explicitly cross-species "
            "organelle and membrane-domain context."
        ),
    ),
    "loud1968_rat_liver_stereology": SourceReference(
        id="loud1968_rat_liver_stereology",
        title=(
            "A quantitative stereological description of the ultrastructure "
            "of normal rat liver parenchymal cells"
        ),
        url="https://pubmed.ncbi.nlm.nih.gov/5645844/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Rat liver ultrastructure retained only as explicitly "
            "cross-species organelle context."
        ),
    ),
    "organelle_placement_method": SourceReference(
        id="organelle_placement_method",
        title="Seeded solid-body packing of mixed-species organelle proxy inputs",
        url="https://en.wikipedia.org/wiki/Random_sequential_adsorption",
        source_type="project_assumption",
        date_verified=DATE_VERIFIED,
        notes=(
            "Positions are a deterministic rejection-sampled realization "
            "of predominantly rat organelle counts, volume fractions and "
            "location categories inside an aggregate-human-volume cell proxy. "
            "It is not a measured human organelle population or coordinate set."
        ),
    ),
})

# Coarse location categories are the only spatial information the sources give.
CENTRAL = "central"
DISPERSED = "dispersed cytoplasm"
NEAR_CANALICULAR = "near canalicular pole"

# Location categories that name a discrete, countable, roughly-spherical body we
# are willing to place as individual spheres.
_DISCRETE_LOCATIONS = {CENTRAL, DISPERSED, NEAR_CANALICULAR}

# Keep individual-sphere placement to sane population sizes; anything larger
# (e.g. ribosomes at 1e7) is not a per-body renderable population.
MAX_DISCRETE_COUNT = 100_000

# Minimum centre-to-centre clearance beyond touching, as a fraction of the
# smaller radius. Zero would allow exact tangency; a small positive value keeps
# solid bodies strictly separated.
_SEPARATION_EPS_FRACTION = 1.0e-6


@dataclass(frozen=True)
class OrganelleBody:
    """One discrete organelle placed as a solid sphere."""

    organelle_id: str
    index: int
    center_um: Vector3
    radius_um: float
    volume_um3: float
    organism: str
    quality: str
    source: str


@dataclass(frozen=True)
class OrganelleRegion:
    """A network/aggregate organelle with no source-backed discrete count."""

    organelle_id: str
    name: str
    location: str
    volume_fraction_pct: float
    target_volume_um3: float
    centroid_um: Vector3
    organism: str
    quality: str
    source: str
    discrete: bool = False
    reason: str = "no source-backed discrete count; represented as a network/region"


@dataclass(frozen=True)
class UnplacedOrganelle:
    organelle_id: str
    name: str
    reason: str


@dataclass(frozen=True)
class OrganellePlacement:
    version: str
    status: str
    runtime_geometry_role: str
    healthy_phh_biological_authority: bool
    quantitative_contact_force_authority: bool
    uses_cross_species_organelle_parameters: bool
    healthy_phh_discrete_count_parameter_count: int
    healthy_phh_discrete_volume_fraction_parameter_count: int
    cross_species_proxy_body_count: int
    human_aggregate_region_count: int
    measured_per_organelle_coordinate_count: int
    donor_resolved_mesh_count: int
    seed: int
    cell_volume_um3: float
    cell_envelope_radius_um: float
    nucleus_radius_um: float
    bodies: tuple[OrganelleBody, ...]
    regions: tuple[OrganelleRegion, ...]
    unplaced: tuple[UnplacedOrganelle, ...]
    body_count_by_organelle: dict[str, int]
    placed_body_volume_um3: float
    discrete_volume_fraction_pct: float
    source_bound_inputs: tuple[str, ...]
    not_biologically_identified: tuple[str, ...]
    blockers: tuple[str, ...]
    source_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


# --- vector helpers (stdlib only; mirrors spatial_world conventions) ---------


def _sub(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _norm(v: Vector3) -> float:
    return sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


# --- spatial hash so packing stays ~O(n) rather than O(n^2) ------------------


class _SpatialHash:
    """Uniform-grid neighbour index over placed body centres."""

    def __init__(self, cell_size_um: float) -> None:
        self._cell = max(cell_size_um, 1.0e-6)
        self._grid: dict[tuple[int, int, int], list[tuple[Vector3, float]]] = {}

    def _key(self, p: Vector3) -> tuple[int, int, int]:
        c = self._cell
        return (floor(p[0] / c), floor(p[1] / c), floor(p[2] / c))

    def insert(self, center: Vector3, radius: float) -> None:
        self._grid.setdefault(self._key(center), []).append((center, radius))

    def overlaps(self, center: Vector3, radius: float) -> bool:
        kx, ky, kz = self._key(center)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    bucket = self._grid.get((kx + dx, ky + dy, kz + dz))
                    if not bucket:
                        continue
                    for other_center, other_radius in bucket:
                        min_sep = radius + other_radius
                        min_sep += _SEPARATION_EPS_FRACTION * min(radius, other_radius)
                        if _norm(_sub(center, other_center)) < min_sep:
                            return True
        return False


# --- sizing ------------------------------------------------------------------


def _body_radius_um(organelle: OrganelleQuantity, cell_volume_um3: float) -> float:
    """Equivalent-sphere radius of one organelle from its volume fraction/count."""
    assert organelle.volume_fraction_pct is not None
    assert organelle.count_typical is not None
    total_volume = (organelle.volume_fraction_pct / 100.0) * cell_volume_um3
    per_body_volume = total_volume / organelle.count_typical
    return sphere_diameter_um_from_volume(per_body_volume) / 2.0


def _classify(organelle: OrganelleQuantity) -> str:
    """discrete | region | unplaced."""
    if (
        organelle.count_typical is not None
        and organelle.volume_fraction_pct is not None
        and organelle.renderable
        and organelle.location in _DISCRETE_LOCATIONS
        and organelle.count_typical <= MAX_DISCRETE_COUNT
    ):
        return "discrete"
    if organelle.volume_fraction_pct is not None and organelle.renderable:
        return "region"
    return "unplaced"


# --- cell shape: volume-matched truncated octahedron -------------------------
# The rendered plasma membrane is the canonical space-filling hepatocyte
# polyhedron (a truncated octahedron: |x|<=2s, |x|+|y|+|z|<=3s, volume 32 s^3).
# Organelles are placed to FILL this actual cell shape and reach the membrane,
# not confined to an inscribed sphere (which left the polyhedral corners empty
# and made organelles look like they avoid the membrane).


def truncated_octahedron_scale_um(cell_volume_um3: float) -> float:
    """The scale ``s`` of the volume-matched truncated octahedron (volume 32 s^3)."""
    return (cell_volume_um3 / 32.0) ** (1.0 / 3.0)


def _fits_in_cell(center: Vector3, scale_um: float, radius_um: float) -> bool:
    """True if a sphere of ``radius_um`` at ``center`` fits inside the truncated
    octahedron with clearance to every face (6 square + 8 hexagonal faces)."""
    ax, ay, az = abs(center[0]), abs(center[1]), abs(center[2])
    if 2.0 * scale_um - ax < radius_um:
        return False
    if 2.0 * scale_um - ay < radius_um:
        return False
    if 2.0 * scale_um - az < radius_um:
        return False
    if (3.0 * scale_um - (ax + ay + az)) / SQRT3 < radius_um:
        return False
    return True


# --- location-biased sampling ------------------------------------------------

SQRT3 = 3.0 ** 0.5
SQRT5 = 5.0 ** 0.5  # circumradius of the truncated octahedron is sqrt(5) * s


def _sample_direction(rng: EngineRng) -> Vector3:
    """Isotropic unit vector via normalized Gaussian."""
    while True:
        v = (rng.gauss(), rng.gauss(), rng.gauss())
        n = _norm(v)
        if n > 1.0e-9:
            return (v[0] / n, v[1] / n, v[2] / n)


def _sample_point(rng: EngineRng, max_radius_um: float, location: str) -> Vector3:
    """Uniform point in a ball of ``max_radius_um``.

    For ``central`` the radius is contracted toward the origin; the canalicular
    bias is applied separately as an acceptance weight (see ``_accept_location``).
    """
    u = rng.random()
    if location == CENTRAL:
        # Concentrate near the centre (r ~ u instead of u^(1/3)).
        radius = max_radius_um * u
    else:
        radius = max_radius_um * (u ** (1.0 / 3.0))
    direction = _sample_direction(rng)
    return (direction[0] * radius, direction[1] * radius, direction[2] * radius)


def _accept_location(rng: EngineRng, center: Vector3, envelope_radius_um: float, location: str) -> bool:
    """Soft location bias as a transparent acceptance probability.

    ``near canalicular pole`` accepts more readily toward +x (the canonical
    canalicular direction); other categories accept everywhere.
    """
    if location != NEAR_CANALICULAR:
        return True
    axis = HEPATOCYTE_CANONICAL_CANALICULAR_DIRECTION
    projection = center[0] * axis[0] + center[1] * axis[1] + center[2] * axis[2]
    # Map projection in [-R, R] -> probability in [0.15, 1.0]; never a hard cut.
    weight = 0.575 + 0.425 * (projection / envelope_radius_um)
    return rng.random() < max(0.0, min(1.0, weight))


# --- placement ---------------------------------------------------------------


def _place_bodies(
    organelle: OrganelleQuantity,
    radius_um: float,
    envelope_radius_um: float,
    scale_um: float,
    nucleus_radius_um: float,
    index: _SpatialHash,
    rng: EngineRng,
    *,
    max_attempts_per_body: int = 400,
) -> tuple[list[OrganelleBody], int]:
    """Rejection-sample non-overlapping positions for one organelle type.

    Bodies fill the truncated-octahedron cell shape (so they reach the membrane),
    stay outside the nucleus, and never overlap.
    """
    bodies: list[OrganelleBody] = []
    volume = sphere_volume_um3_from_diameter(radius_um * 2.0)
    # Sample the whole polyhedron by covering its circumscribing ball, then
    # rejecting points that do not fit inside the cell shape.
    reach = SQRT5 * scale_um
    nucleus_clearance = nucleus_radius_um + radius_um
    count = int(round(organelle.count_typical))
    placed = 0
    for i in range(count):
        for _ in range(max_attempts_per_body):
            center = _sample_point(rng, reach, organelle.location)
            if not _fits_in_cell(center, scale_um, radius_um):
                continue
            if _norm(center) < nucleus_clearance:
                continue
            if not _accept_location(rng, center, envelope_radius_um, organelle.location):
                continue
            if index.overlaps(center, radius_um):
                continue
            index.insert(center, radius_um)
            bodies.append(
                OrganelleBody(
                    organelle_id=organelle.id,
                    index=i,
                    center_um=center,
                    radius_um=radius_um,
                    volume_um3=volume,
                    organism=organelle.organism,
                    quality=organelle.quality,
                    source=organelle.source,
                )
            )
            placed += 1
            break
    return bodies, count - placed


def build_organelle_placement(
    *,
    seed: int = 0,
    cell_volume_um3: float = CELL_VOLUME_UM3,
) -> OrganellePlacement:
    """Build a deterministic, non-overlapping organelle population.

    Nucleus first (central, one body), then the discrete cytoplasmic organelles
    packed around it; networks/aggregates are returned as flagged regions.
    """
    rng = EngineRng(seed)
    envelope_radius_um = HEPATOCYTE_REFERENCE_EQUIVALENT_SPHERE_DIAMETER_UM / 2.0
    # Cell shape is the volume-matched truncated octahedron (the rendered membrane).
    scale_um = truncated_octahedron_scale_um(cell_volume_um3)

    by_class: dict[str, list[OrganelleQuantity]] = {"discrete": [], "region": [], "unplaced": []}
    for organelle in ORGANELLES:
        by_class[_classify(organelle)].append(organelle)

    # Nucleus (if present as a discrete central body) defines the excluded core.
    nucleus = next((o for o in by_class["discrete"] if o.id == "nucleus"), None)
    nucleus_radius_um = _body_radius_um(nucleus, cell_volume_um3) if nucleus is not None else 0.0

    # Largest non-nucleus body sets the spatial-hash cell size.
    other_discrete = [o for o in by_class["discrete"] if o.id != "nucleus"]
    max_other_radius = max(
        (_body_radius_um(o, cell_volume_um3) for o in other_discrete),
        default=nucleus_radius_um,
    )
    index = _SpatialHash(cell_size_um=max(max_other_radius, nucleus_radius_um) * 2.0)

    bodies: list[OrganelleBody] = []
    body_shortfall: dict[str, int] = {}

    if nucleus is not None:
        bodies.append(
            OrganelleBody(
                organelle_id=nucleus.id,
                index=0,
                center_um=(0.0, 0.0, 0.0),
                radius_um=nucleus_radius_um,
                volume_um3=sphere_volume_um3_from_diameter(nucleus_radius_um * 2.0),
                organism=nucleus.organism,
                quality=nucleus.quality,
                source=nucleus.source,
            )
        )
        index.insert((0.0, 0.0, 0.0), nucleus_radius_um)

    # Place larger bodies first so small ones fill the gaps (denser feasible pack).
    for organelle in sorted(other_discrete, key=lambda o: _body_radius_um(o, cell_volume_um3), reverse=True):
        radius = _body_radius_um(organelle, cell_volume_um3)
        placed, shortfall = _place_bodies(
            organelle, radius, envelope_radius_um, scale_um, nucleus_radius_um, index, rng
        )
        bodies.extend(placed)
        if shortfall:
            body_shortfall[organelle.id] = shortfall

    regions = tuple(
        OrganelleRegion(
            organelle_id=o.id,
            name=o.name,
            location=o.location,
            volume_fraction_pct=o.volume_fraction_pct,  # type: ignore[arg-type]
            target_volume_um3=(o.volume_fraction_pct / 100.0) * cell_volume_um3,  # type: ignore[operator]
            centroid_um=(0.0, 0.0, 0.0),
            organism=o.organism,
            quality=o.quality,
            source=o.source,
        )
        for o in by_class["region"]
    )
    unplaced = tuple(
        UnplacedOrganelle(
            organelle_id=o.id,
            name=o.name,
            reason=(
                "no volume fraction to size individual bodies"
                if o.volume_fraction_pct is None
                else "not individually renderable at source population size"
            ),
        )
        for o in by_class["unplaced"]
    )

    placed_volume = sum(b.volume_um3 for b in bodies)
    body_counts: dict[str, int] = {}
    for b in bodies:
        body_counts[b.organelle_id] = body_counts.get(b.organelle_id, 0) + 1

    cross_species_proxy_body_count = sum(
        body.organism != "human" for body in bodies
    )
    human_aggregate_region_count = sum(
        region.organism == "human" for region in regions
    )
    blockers = [
        "discrete organelle counts, fractions and location categories are predominantly rat proxies, not healthy-PHH parameters",
        "rat organelle fractions are combined with an aggregate human cell volume and therefore form a mixed-species synthetic geometry",
        "individual organelle (x,y,z) is a seeded realization, not measured per-organelle coordinates",
        "cell shape is the volume-matched canonical hepatocyte polyhedron (space-filling proxy), not a donor membrane mesh",
        "ER/Golgi/glycogen/lipid are volume-only regions; no source-backed discrete count or mesh",
    ]
    for organelle_id, shortfall in sorted(body_shortfall.items()):
        blockers.append(
            f"{organelle_id}: {shortfall} bodies could not be packed without overlap at this envelope/seed"
        )

    placement = OrganellePlacement(
        version=VERSION,
        status=STATUS,
        runtime_geometry_role=RUNTIME_GEOMETRY_ROLE,
        healthy_phh_biological_authority=False,
        quantitative_contact_force_authority=False,
        uses_cross_species_organelle_parameters=True,
        healthy_phh_discrete_count_parameter_count=0,
        healthy_phh_discrete_volume_fraction_parameter_count=0,
        cross_species_proxy_body_count=cross_species_proxy_body_count,
        human_aggregate_region_count=human_aggregate_region_count,
        measured_per_organelle_coordinate_count=0,
        donor_resolved_mesh_count=0,
        seed=seed,
        cell_volume_um3=cell_volume_um3,
        cell_envelope_radius_um=envelope_radius_um,
        nucleus_radius_um=nucleus_radius_um,
        bodies=tuple(bodies),
        regions=regions,
        unplaced=unplaced,
        body_count_by_organelle=body_counts,
        placed_body_volume_um3=placed_volume,
        discrete_volume_fraction_pct=100.0 * placed_volume / cell_volume_um3,
        source_bound_inputs=(
            "aggregate normal-control human cell-volume reference",
            "rat and consensus organelle records retained with organism and quality tags",
            "aggregate normal-control human lipid-droplet volume-fraction reference",
            "deterministic non-overlap packing algorithm",
        ),
        not_biologically_identified=(
            "healthy-PHH discrete organelle counts and volume fractions",
            "exact per-organelle coordinates",
            "organelle mesh shape (spheres are equivalent-volume stand-ins)",
            "network organelle geometry (ER, Golgi, glycogen, lipid droplets)",
            "contact force, stiffness or mechanotransduction",
        ),
        blockers=tuple(blockers),
        source_ids=tuple(PLACEMENT_SOURCES),
    )
    validate_organelle_placement(placement)
    return placement


def validate_organelle_placement(placement: OrganellePlacement) -> None:
    """Reject any promotion of the mixed-species scaffold to PHH authority."""

    if (
        placement.version != VERSION
        or placement.status != STATUS
        or placement.runtime_geometry_role != RUNTIME_GEOMETRY_ROLE
    ):
        raise ValueError("organelle placement authority contract changed")
    if (
        placement.healthy_phh_biological_authority
        or placement.quantitative_contact_force_authority
        or not placement.uses_cross_species_organelle_parameters
        or placement.healthy_phh_discrete_count_parameter_count != 0
        or placement.healthy_phh_discrete_volume_fraction_parameter_count != 0
        or placement.measured_per_organelle_coordinate_count != 0
        or placement.donor_resolved_mesh_count != 0
    ):
        raise ValueError("mixed-species organelle proxy gained healthy-PHH authority")
    if placement.cross_species_proxy_body_count != sum(
        body.organism != "human" for body in placement.bodies
    ):
        raise ValueError("cross-species organelle body count is inconsistent")
    if placement.human_aggregate_region_count != sum(
        region.organism == "human" for region in placement.regions
    ):
        raise ValueError("human aggregate organelle-region count is inconsistent")
    if sum(placement.body_count_by_organelle.values()) != len(placement.bodies):
        raise ValueError("organelle body-count ledger is inconsistent")
    if not placement.source_bound_inputs or not placement.not_biologically_identified:
        raise ValueError("organelle placement evidence boundary is incomplete")
    if (
        len(placement.source_ids) != len(PLACEMENT_SOURCES)
        or set(placement.source_ids) != set(PLACEMENT_SOURCES)
    ):
        raise ValueError("organelle placement source ledger is incomplete")


def organelle_placement_snapshot(*, seed: int = 0) -> dict[str, object]:
    """JSON-ready placement payload for the engine snapshot / renderer."""
    return build_organelle_placement(seed=seed).to_dict()
