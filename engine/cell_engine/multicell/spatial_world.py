"""Geometry-authoritative multicellular runtime.

The browser renders this state; it does not maintain a second causal world.
Contact is edge-driven (``enter``/``stay``/``exit``), and elapsed contact time is
not a biological input.  A closed convex surface can expose a real polygonal
contact patch, while force, adhesion, junction gating, and downstream kinetics
remain blocked until matched evidence is available.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from itertools import combinations, permutations, product
from math import atan2, cos, isfinite, pi, sin, sqrt
from typing import Literal

from cell_engine.core.provenance import SourceReference
from cell_engine.core.random import EngineRng
from cell_engine.core.serialization import to_plain
from cell_engine.core.state import (
    CellSpatialContactEvent,
    CellSpatialContactState,
    CellSpatialState,
    CellState,
)
from cell_engine.quantitative.geometry import (
    HEPATOCYTE_CANONICAL_CANALICULAR_DIRECTION,
    HEPATOCYTE_CANONICAL_SINUSOIDAL_DIRECTION,
    HEPATOCYTE_REFERENCE_EQUIVALENT_SPHERE_DIAMETER_UM,
)


DATE_VERIFIED = "2026-07-14"
NUMERIC_CONTACT_TOLERANCE_UM = 1.0e-8
NUMERIC_AXIS_TOLERANCE = 1.0e-10
HBV_CRYO_EM_OUTER_DIAMETER_UM = 0.045
# Evans et al. observed 2-4% lytic area expansion in intact human red-cell
# membranes.  One percent is an explicit engineering safety cap: half the lower
# reported lysis bound, not a measured hepatocyte failure threshold.
CONSERVATIVE_ELASTIC_AREA_STRAIN_CAP = 0.01

Vector2 = tuple[float, float]
Vector3 = tuple[float, float, float]
Quaternion = tuple[float, float, float, float]
BiologicalKind = Literal["hepatocyte", "cell", "bacterium", "virus", "other"]
MembraneDomain = Literal["apical", "lateral", "basolateral", "unknown"]
ShapeKind = Literal["sphere", "capsule", "convex_polyhedron"]
ContactEventKind = Literal["none", "enter", "stay", "exit"]
DomainAssignmentStatus = Literal[
    "resolved_unique_face",
    "resolved_shared_feature_same_domain",
    "ambiguous_shared_feature_multiple_domains",
    "not_applicable_or_unresolved",
]


SPATIAL_WORLD_SOURCES: dict[str, SourceReference] = {
    "singer_nicolson1972_fluid_mosaic": SourceReference(
        id="singer_nicolson1972_fluid_mosaic",
        title="The fluid mosaic model of the structure of cell membranes",
        url="https://doi.org/10.1126/science.175.4023.720",
        source_type="primary_paper",
        date_verified="2026-07-15",
        notes=(
            "Establishes the thermodynamically fluid lipid matrix with amphipathic "
            "integral proteins. It is an architecture reference, not a hepatocyte "
            "diffusion coefficient or mechanics calibration."
        ),
    ),
    "helfrich1973_bilayer_curvature": SourceReference(
        id="helfrich1973_bilayer_curvature",
        title="Elastic properties of lipid bilayers: theory and possible experiments",
        url="https://doi.org/10.1515/znc-1973-11-1209",
        source_type="primary_paper",
        date_verified="2026-07-15",
        notes=(
            "Separates stretching, tilt, and curvature and supplies the curvature-"
            "energy framework for closed fluid bilayers. The project uses the "
            "model topology, not an inferred PHH bending modulus."
        ),
    ),
    "olander2021_human_hepatocyte_size": SourceReference(
        id="olander2021_human_hepatocyte_size",
        title="Hepatocyte size fractionation allows dissection of human liver zonation",
        url="https://doi.org/10.1002/jcp.30273",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Direct isolated-human-hepatocyte measurements: median diameter 18.4 um "
            "across 54 cryopreserved batches; 88% of cells were 12-26 um. The value "
            "does not establish in-situ liver-plate geometry."
        ),
    ),
    "duarte1989_human_hepatocyte_volume": SourceReference(
        id="duarte1989_human_hepatocyte_volume",
        title="Baseline volume data of human liver parenchymal cell",
        url="https://pubmed.ncbi.nlm.nih.gov/2752360/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Normal-human in-situ intermediate-zone stereology reports mean "
            "hepatocyte volume 2850 +/- 99.9 um3 across five selected cases."
        ),
    ),
    "segovia_miranda2019_human_liver_3d_morphometry": SourceReference(
        id="segovia_miranda2019_human_liver_3d_morphometry",
        title=(
            "Three-dimensional spatially resolved geometrical and functional "
            "models of human liver tissue reveal new aspects of NAFLD progression"
        ),
        url="https://doi.org/10.1038/s41591-019-0660-7",
        source_type="primary_paper",
        date_verified="2026-07-17",
        notes=(
            "Normal-control human liver 3D reconstructions report median "
            "hepatocyte volume 5657.07116 um3 across five reconstructions. The "
            "runtime preserves this volume but does not claim a measured mesh."
        ),
    ),
    "fabyan2026_human_liver_3d": SourceReference(
        id="fabyan2026_human_liver_3d",
        title="3D reconstruction of human liver tissue at cellular resolution",
        url="https://doi.org/10.1126/sciadv.adz2299",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Human cleared-tissue 3D reconstruction supports tissue-scale spatial "
            "architecture. It does not provide a donor-general hepatocyte mechanics "
            "law or justify the canonical polyhedron used by this runtime."
        ),
    ),
    "evans1976_human_membrane_area_lysis": SourceReference(
        id="evans1976_human_membrane_area_lysis",
        title="Elastic area compressibility modulus of red cell membrane",
        url="https://doi.org/10.1016/S0006-3495(76)85713-X",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Human red-cell micropipette measurements reported 2-4% maximum "
            "fractional area expansion before lysis (3% mean). This is not a "
            "hepatocyte-specific failure measurement; the runtime uses half the "
            "lower bound as a conservative engineering cap."
        ),
    ),
    "rawicz2000_bilayer_elasticity": SourceReference(
        id="rawicz2000_bilayer_elasticity",
        title="Effect of chain length and unsaturation on elasticity of lipid bilayers",
        url="https://doi.org/10.1016/S0006-3495(00)76295-3",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Micropipette measurements separate low-tension undulation smoothing "
            "from direct high-tension bilayer area stretch and report a mean direct "
            "area-stretch modulus of 243 mN/m across the tested PC bilayers. The "
            "runtime does not treat that model-bilayer modulus as a PHH cortex law."
        ),
    ),
    "fujiwara2002_phospholipid_hop_diffusion": SourceReference(
        id="fujiwara2002_phospholipid_hop_diffusion",
        title="Phospholipids undergo hop diffusion in compartmentalized cell membrane",
        url="https://doi.org/10.1083/jcb.200202050",
        source_type="primary_paper",
        date_verified="2026-07-15",
        notes=(
            "Single-molecule tracking in NRK cells measured rapid DOPE motion "
            "inside approximately 230-nm compartments and slower macroscopic hop "
            "diffusion imposed by the actin-based membrane skeleton. These values "
            "are not transferred to human hepatocytes."
        ),
    ),
    "stuschke_bojar1985_rat_hepatocyte_membrane_diffusion": SourceReference(
        id="stuschke_bojar1985_rat_hepatocyte_membrane_diffusion",
        title="Insulin effect on translational diffusion of lipids and proteins in the plasma membrane of isolated rat hepatocytes",
        url="https://doi.org/10.1016/0167-4889(85)90209-5",
        source_type="primary_paper",
        date_verified="2026-07-15",
        notes=(
            "FRAP in intact isolated rat hepatocytes at 21 C reported probe- and "
            "condition-dependent lipid diffusion and an unselected-protein mean. "
            "It is retained only as hepatocyte-context evidence that both classes "
            "move laterally; it is not a healthy-human parameter."
        ),
    ),
    "mitra2004_rat_hepatocyte_bilayer_thickness": SourceReference(
        id="mitra2004_rat_hepatocyte_bilayer_thickness",
        title="A comparison of the membrane organization of apical and basolateral plasma membranes of rat hepatocytes",
        url="https://doi.org/10.1073/pnas.0307332101",
        source_type="primary_paper",
        date_verified="2026-07-15",
        notes=(
            "X-ray diffraction of purified rat-hepatocyte membranes reported "
            "domain-specific bilayer thicknesses: 35.6 +/- 0.6 A basolateral "
            "and 42.5 +/- 0.3 A apical. These are cross-species references and "
            "cannot parameterize a healthy adult human PHH."
        ),
    ),
    "guillou2016_membrane_surface_reservoirs": SourceReference(
        id="guillou2016_membrane_surface_reservoirs",
        title="T-lymphocyte passive deformation is controlled by unfolding of membrane surface reservoirs",
        url="https://doi.org/10.1091/mbc.E16-06-0414",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Micropipette aspiration shows that T lymphocytes can deform at "
            "constant volume while apparent surface area increases through "
            "membrane-reservoir unfolding. This supports only the kinematic "
            "constant-volume principle; no T-cell parameter is transferred to PHH."
        ),
    ),
    "seitz2007_hbv_cryo_em": SourceReference(
        id="seitz2007_hbv_cryo_em",
        title="Cryo-electron microscopy of hepatitis B virions reveals variability in envelope capsid interactions",
        url="https://doi.org/10.1038/sj.emboj.7601841",
        source_type="primary_paper",
        date_verified="2026-07-15",
        notes=(
            "Cryo-EM reports an approximately 45 nm outer diameter for complete "
            "HBV virions. The value may define an explicit HBV collision body; it "
            "does not authorize viral entry or a magnified collision radius."
        ),
    ),
}


@dataclass(frozen=True)
class MembraneReferenceMeasurement:
    """A measurement retained with its experimental system and transfer gate."""

    id: str
    observable: str
    value: float | None
    lower: float | None
    upper: float | None
    unit: str
    experimental_system: str
    conditions: str
    evidence_role: str
    may_parameterize_healthy_phh: bool
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class MembraneMaterialProfile:
    """Intrinsic plasma-membrane contract carried by every hepatocyte body.

    The profile distinguishes fluid-bilayer facts from whole-cell PHH mechanics.
    Cross-system measurements are visible reference evidence and cannot silently
    become human-hepatocyte force, diffusion, or rupture parameters.
    """

    version: Literal["intrinsic_fluid_bilayer_v1"]
    architecture: str
    intrinsic_fluidity_enabled: bool
    surface_representation: str
    area_constraint: str
    volume_constraint: str
    biologically_admissible_shape_modes: tuple[str, ...]
    implemented_geometry_modes: tuple[str, ...]
    unresolved_geometry_modes: tuple[str, ...]
    surface_tracer_advection_enabled: bool
    active_lateral_diffusion_enabled: bool
    lateral_transport_contract: str
    local_contact_gate_model: str
    engineering_area_strain_cap: float
    engineering_cap_is_phh_measurement: bool
    bilayer_thickness_nm: float | None
    area_compressibility_mN_per_m: float | None
    bending_rigidity_J: float | None
    membrane_tension_N_per_m: float | None
    cortex_adhesion_J_per_m2: float | None
    surface_viscosity_Pa_s_m: float | None
    lipid_lateral_diffusion_um2_s: float | None
    protein_lateral_diffusion_um2_s: float | None
    rupture_area_strain: float | None
    quantitative_phh_mechanics_enabled: bool
    reference_measurements: tuple[MembraneReferenceMeasurement, ...]
    blockers: tuple[str, ...]
    source_ids: tuple[str, ...]


def build_intrinsic_hepatocyte_membrane_profile() -> MembraneMaterialProfile:
    """Return the fail-closed fluid-bilayer profile for a healthy adult PHH."""

    references = (
        MembraneReferenceMeasurement(
            id="pc_bilayer_direct_area_stretch_modulus",
            observable="direct_area_stretch_modulus",
            value=243.0,
            lower=None,
            upper=None,
            unit="mN/m",
            experimental_system="twelve fluid-phase synthetic phosphatidylcholine bilayers",
            conditions="micropipette aspiration; high-tension direct stretch regime",
            evidence_role="cross_system_material_reference",
            may_parameterize_healthy_phh=False,
            source_ids=("rawicz2000_bilayer_elasticity",),
        ),
        MembraneReferenceMeasurement(
            id="pc_bilayer_bending_rigidity_span",
            observable="bending_rigidity",
            value=None,
            lower=0.4e-19,
            upper=1.2e-19,
            unit="J",
            experimental_system="fluid-phase synthetic phosphatidylcholine bilayers",
            conditions="composition-dependent span reported across tested lipids",
            evidence_role="cross_system_material_reference",
            may_parameterize_healthy_phh=False,
            source_ids=("rawicz2000_bilayer_elasticity",),
        ),
        MembraneReferenceMeasurement(
            id="human_rbc_lytic_area_expansion",
            observable="maximum_fractional_area_expansion_before_lysis",
            value=0.03,
            lower=0.02,
            upper=0.04,
            unit="fraction",
            experimental_system="intact human red-cell membrane",
            conditions="micropipette aspiration",
            evidence_role="cross_cell_type_failure_reference",
            may_parameterize_healthy_phh=False,
            source_ids=("evans1976_human_membrane_area_lysis",),
        ),
        MembraneReferenceMeasurement(
            id="nrk_dope_intracompartment_diffusion",
            observable="phospholipid_lateral_diffusion_inside_compartment",
            value=5.4,
            lower=None,
            upper=None,
            unit="um2/s",
            experimental_system="DOPE analogue in cultured NRK fibroblast plasma membrane",
            conditions="single-molecule tracking inside approximately 230-nm compartments",
            evidence_role="cross_cell_type_fluidity_reference",
            may_parameterize_healthy_phh=False,
            source_ids=("fujiwara2002_phospholipid_hop_diffusion",),
        ),
        MembraneReferenceMeasurement(
            id="rat_hepatocyte_nbd_pc_diffusion_21c",
            observable="lipid_probe_lateral_diffusion",
            value=0.25,
            lower=None,
            upper=None,
            unit="um2/s",
            experimental_system="NBD-PC in intact isolated rat hepatocytes",
            conditions="FRAP at 21 C; no insulin",
            evidence_role="cross_species_hepatocyte_context",
            may_parameterize_healthy_phh=False,
            source_ids=("stuschke_bojar1985_rat_hepatocyte_membrane_diffusion",),
        ),
        MembraneReferenceMeasurement(
            id="rat_hepatocyte_unselected_protein_diffusion_21c",
            observable="unselected_membrane_protein_lateral_diffusion",
            value=0.064,
            lower=None,
            upper=None,
            unit="um2/s",
            experimental_system="FITC-labelled proteins in intact isolated rat hepatocytes",
            conditions="FRAP at 21 C; mean across unselected proteins",
            evidence_role="cross_species_hepatocyte_context",
            may_parameterize_healthy_phh=False,
            source_ids=("stuschke_bojar1985_rat_hepatocyte_membrane_diffusion",),
        ),
        MembraneReferenceMeasurement(
            id="rat_hepatocyte_basolateral_bilayer_thickness",
            observable="basolateral_bilayer_thickness",
            value=3.56,
            lower=3.50,
            upper=3.62,
            unit="nm",
            experimental_system="purified basolateral plasma membranes from rat hepatocytes",
            conditions="X-ray diffraction; reported 35.6 +/- 0.6 A",
            evidence_role="cross_species_hepatocyte_domain_reference",
            may_parameterize_healthy_phh=False,
            source_ids=("mitra2004_rat_hepatocyte_bilayer_thickness",),
        ),
        MembraneReferenceMeasurement(
            id="rat_hepatocyte_apical_bilayer_thickness",
            observable="apical_bilayer_thickness",
            value=4.25,
            lower=4.22,
            upper=4.28,
            unit="nm",
            experimental_system="purified apical plasma membranes from rat hepatocytes",
            conditions="X-ray diffraction; reported 42.5 +/- 0.3 A",
            evidence_role="cross_species_hepatocyte_domain_reference",
            may_parameterize_healthy_phh=False,
            source_ids=("mitra2004_rat_hepatocyte_bilayer_thickness",),
        ),
    )
    source_ids = tuple(dict.fromkeys(
        source_id
        for measurement in references
        for source_id in measurement.source_ids
    ))
    return MembraneMaterialProfile(
        version="intrinsic_fluid_bilayer_v1",
        architecture="amphipathic_phospholipid_bilayer_with_mobile_integral_proteins_and_cortex_coupling",
        intrinsic_fluidity_enabled=True,
        surface_representation="deformable_area_constrained_mesh_plus_barycentric_surface_tracers",
        area_constraint="near_incompressible_direct_lipid_area; apparent_area_may_change_via_surface_reservoirs_and_traffic",
        volume_constraint="short_time_near_constant_cell_volume_until_water_flux_model_changes_volume",
        biologically_admissible_shape_modes=(
            "bending",
            "local_invagination",
            "local_protrusion",
            "reservoir_unfolding",
            "endocytosis",
            "exocytosis",
            "budding",
        ),
        implemented_geometry_modes=(
            "closed_area_and_volume_constrained_rest_surface",
            "engine_authoritative_global_affine_contact_bending",
            "rest_shape_restoration_after_contact_exit",
            "barycentric_surface_tracer_advection",
        ),
        unresolved_geometry_modes=(
            "local_contact_patch_curvature",
            "surface_remeshing_without_artificial_shear",
            "deep_fold_self_contact",
            "endocytic_or_exocytic_topology_change",
            "membrane_reservoir_area_exchange",
        ),
        surface_tracer_advection_enabled=True,
        active_lateral_diffusion_enabled=False,
        lateral_transport_contract=(
            "two_dimensional_surface-transport interface with domain and cortical-compartment gates; "
            "advection follows authoritative mesh deformation, while diffusion remains disabled until "
            "healthy-PHH species-specific coefficients are identified"
        ),
        local_contact_gate_model=(
            "contact_patch_overlap_is_necessary; local_receptor_or_junction_presence, ligand_match, orientation, "
            "and pathway_state_are_independent_required_gates"
        ),
        engineering_area_strain_cap=CONSERVATIVE_ELASTIC_AREA_STRAIN_CAP,
        engineering_cap_is_phh_measurement=False,
        bilayer_thickness_nm=None,
        area_compressibility_mN_per_m=None,
        bending_rigidity_J=None,
        membrane_tension_N_per_m=None,
        cortex_adhesion_J_per_m2=None,
        surface_viscosity_Pa_s_m=None,
        lipid_lateral_diffusion_um2_s=None,
        protein_lateral_diffusion_um2_s=None,
        rupture_area_strain=None,
        quantitative_phh_mechanics_enabled=False,
        reference_measurements=references,
        blockers=(
            "healthy adult human hepatocyte bilayer thickness is not directly measured in the loaded evidence; rat domain-specific measurements remain cross-species references only",
            "healthy adult human hepatocyte area-compressibility and bending moduli are not identified",
            "healthy adult human hepatocyte membrane tension and membrane-cortex adhesion are not identified",
            "healthy adult human hepatocyte lipid and protein lateral-diffusion distributions are not identified",
            "healthy adult human hepatocyte rupture strain and force-time response are not identified",
        ),
        source_ids=source_ids,
    )


@dataclass(frozen=True)
class SphereShape:
    radius_um: float
    kind: Literal["sphere"] = "sphere"


@dataclass(frozen=True)
class CapsuleShape:
    """Capsule defined by a center-line segment plus a radial shell."""

    radius_um: float
    half_segment_length_um: float
    axis: Vector3
    kind: Literal["capsule"] = "capsule"


@dataclass(frozen=True)
class ConvexFace:
    id: str
    vertex_indices: tuple[int, ...]
    membrane_domain: MembraneDomain
    topology_evidence: str


@dataclass(frozen=True)
class SurfaceDeformationState:
    """Auditable affine contact deformation attached to a convex surface.

    The deformation is kinematic: it resolves geometry while preserving volume
    and bounding surface-area strain.  It is not a force, stiffness, relaxation
    time, cortical rheology, or adhesion model.
    """

    model: Literal["volume_preserving_affine_contact_v1"]
    active: bool
    rest_vertices_local_um: tuple[Vector3, ...]
    normal_local: Vector3
    requested_axial_scale: float
    axial_scale: float
    tangential_scale: float
    volume_ratio: float
    surface_area_ratio: float
    elastic_area_strain: float
    elastic_area_strain_cap: float
    cap_basis: str
    status: str
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class ConvexPolyhedronShape:
    """Closed convex cell boundary with domain-labelled planar faces."""

    vertices_local_um: tuple[Vector3, ...]
    faces: tuple[ConvexFace, ...]
    equivalent_sphere_radius_um: float
    geometry_status: str
    deformation: SurfaceDeformationState | None = None
    kind: Literal["convex_polyhedron"] = "convex_polyhedron"


CollisionShape = SphereShape | CapsuleShape | ConvexPolyhedronShape


@dataclass(frozen=True)
class SpatialBody:
    id: str
    biological_kind: BiologicalKind
    center_um: Vector3
    shape: CollisionShape
    velocity_um_s: Vector3 = (0.0, 0.0, 0.0)
    orientation_xyzw: Quaternion = (0.0, 0.0, 0.0, 1.0)
    state_ref: str | None = None
    pose_authority: str = "engine_runtime"
    geometry_evidence: str = "unspecified"
    visual_profile: str = "generic"
    molecular_profile_id: str | None = None
    membrane_material: MembraneMaterialProfile | None = None
    source_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContactApproachPlacement:
    """Auditable stochastic placement for one explicitly supplied body.

    Randomness selects only an incoming direction. The caller must provide the
    body's measured or otherwise disclosed collision shape; no radius, contact
    area, adhesion state, or biological response is sampled here.
    """

    body: SpatialBody
    outward_direction: Vector3
    requested_surface_gap_um: float
    random_seed: int
    sampling_distribution: Literal["isotropic_solid_angle"] = "isotropic_solid_angle"


@dataclass(frozen=True)
class SpatialPairRelation:
    id: str
    body_a: str
    body_b: str
    body_a_kind: BiologicalKind
    body_b_kind: BiologicalKind
    world_time_s: float
    center_distance_um: float
    surface_gap_um: float
    overlap_depth_um: float
    relation: Literal["separated", "touching", "overlapping"]
    geometric_contact: bool
    contact_event: ContactEventKind
    contact_input_active: bool
    closest_point_a_um: Vector3
    closest_point_b_um: Vector3
    normal_a_to_b: Vector3
    relative_normal_velocity_um_s: float
    contact_face_a_id: str | None
    contact_face_b_id: str | None
    contact_face_candidates_a: tuple[str, ...]
    contact_face_candidates_b: tuple[str, ...]
    membrane_domain_a: MembraneDomain | None
    membrane_domain_b: MembraneDomain | None
    membrane_domain_candidates_a: tuple[MembraneDomain, ...]
    membrane_domain_candidates_b: tuple[MembraneDomain, ...]
    domain_assignment_status_a: DomainAssignmentStatus
    domain_assignment_status_b: DomainAssignmentStatus
    contact_patch_polygon_um: tuple[Vector3, ...]
    contact_patch_area_um2: float | None
    normal_load_nN: float | None
    contact_patch_status: str
    force_status: str
    quantitative_biological_effects_enabled: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class SpatialWorldState:
    version: str
    id: str
    scenario_kind: str
    time_s: float
    length_unit: Literal["um"]
    bodies: tuple[SpatialBody, ...]
    pair_relations: tuple[SpatialPairRelation, ...]
    geometry_authority: str
    contact_event_semantics: str
    surface_deformation_model: str
    conservative_elastic_area_strain_cap: float
    surface_deformation_scope: str
    evidence_status: str
    geometry_drives_runtime_state: bool
    quantitative_biological_effects_enabled: bool
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def _add(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _sub(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _scale(v: Vector3, scalar: float) -> Vector3:
    return (v[0] * scalar, v[1] * scalar, v[2] * scalar)


def _dot(a: Vector3, b: Vector3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: Vector3, b: Vector3) -> Vector3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _norm(v: Vector3) -> float:
    return sqrt(_dot(v, v))


def _unit(v: Vector3, fallback: Vector3 = (1.0, 0.0, 0.0)) -> Vector3:
    length = _norm(v)
    return fallback if length <= 1.0e-15 else _scale(v, 1.0 / length)


def _mean(points: tuple[Vector3, ...] | list[Vector3]) -> Vector3:
    if not points:
        return (0.0, 0.0, 0.0)
    inv = 1.0 / len(points)
    return (
        sum(point[0] for point in points) * inv,
        sum(point[1] for point in points) * inv,
        sum(point[2] for point in points) * inv,
    )


def _clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))


def _rotate(v: Vector3, quaternion: Quaternion) -> Vector3:
    qv = (quaternion[0], quaternion[1], quaternion[2])
    t = _scale(_cross(qv, v), 2.0)
    return _add(v, _add(_scale(t, quaternion[3]), _cross(qv, t)))


def _inverse_rotate(v: Vector3, quaternion: Quaternion) -> Vector3:
    return _rotate(v, (-quaternion[0], -quaternion[1], -quaternion[2], quaternion[3]))


def _shape_radius(shape: CollisionShape) -> float:
    if isinstance(shape, ConvexPolyhedronShape):
        return shape.equivalent_sphere_radius_um
    if isinstance(shape, CapsuleShape):
        return shape.radius_um + shape.half_segment_length_um
    return shape.radius_um


def _face_normal(vertices: tuple[Vector3, ...], face: ConvexFace) -> Vector3:
    points = [vertices[index] for index in face.vertex_indices]
    origin = points[0]
    for index in range(1, len(points) - 1):
        normal = _cross(_sub(points[index], origin), _sub(points[index + 1], origin))
        if _norm(normal) > NUMERIC_AXIS_TOLERANCE:
            return _unit(normal)
    raise ValueError(f"convex face {face.id} is degenerate")


def _polyhedron_surface_area(vertices: tuple[Vector3, ...], faces: tuple[ConvexFace, ...]) -> float:
    area = 0.0
    for face in faces:
        anchor = vertices[face.vertex_indices[0]]
        for index in range(1, len(face.vertex_indices) - 1):
            edge_a = _sub(vertices[face.vertex_indices[index]], anchor)
            edge_b = _sub(vertices[face.vertex_indices[index + 1]], anchor)
            area += 0.5 * _norm(_cross(edge_a, edge_b))
    return area


def _polyhedron_volume(vertices: tuple[Vector3, ...], faces: tuple[ConvexFace, ...]) -> float:
    signed_six_volume = 0.0
    for face in faces:
        anchor = vertices[face.vertex_indices[0]]
        for index in range(1, len(face.vertex_indices) - 1):
            b = vertices[face.vertex_indices[index]]
            c = vertices[face.vertex_indices[index + 1]]
            signed_six_volume += _dot(anchor, _cross(b, c))
    return abs(signed_six_volume) / 6.0


def _rest_vertices(shape: ConvexPolyhedronShape) -> tuple[Vector3, ...]:
    return shape.deformation.rest_vertices_local_um if shape.deformation is not None else shape.vertices_local_um


def _affine_contact_vertices(
    vertices: tuple[Vector3, ...],
    normal_local: Vector3,
    axial_scale: float,
) -> tuple[Vector3, ...]:
    """Compress along one axis and expand tangentially with determinant one."""

    normal = _unit(normal_local)
    tangential_scale = 1.0 / sqrt(axial_scale)
    center = _mean(vertices)
    transformed: list[Vector3] = []
    for vertex in vertices:
        relative = _sub(vertex, center)
        parallel = _scale(normal, _dot(relative, normal))
        tangent = _sub(relative, parallel)
        transformed.append(_add(center, _add(
            _scale(parallel, axial_scale),
            _scale(tangent, tangential_scale),
        )))
    return tuple(transformed)


def _minimum_axial_scale_for_area_cap(
    shape: ConvexPolyhedronShape,
    normal_local: Vector3,
    area_strain_cap: float,
) -> float:
    rest = _rest_vertices(shape)
    rest_area = _polyhedron_surface_area(rest, shape.faces)
    target_area = rest_area * (1.0 + area_strain_cap)
    low = 1.0e-3
    high = 1.0
    if _polyhedron_surface_area(_affine_contact_vertices(rest, normal_local, low), shape.faces) <= target_area:
        return low
    for _ in range(64):
        middle = (low + high) / 2.0
        area = _polyhedron_surface_area(_affine_contact_vertices(rest, normal_local, middle), shape.faces)
        if area > target_area:
            low = middle
        else:
            high = middle
    return high


def deform_convex_shape_for_contact(
    shape: ConvexPolyhedronShape,
    normal_local: Vector3,
    requested_axial_scale: float,
    *,
    area_strain_cap: float = CONSERVATIVE_ELASTIC_AREA_STRAIN_CAP,
) -> ConvexPolyhedronShape:
    """Return a volume-preserving contact shape bounded by actual mesh area.

    ``requested_axial_scale`` comes only from geometric overlap.  No elastic
    modulus or force is inferred.  If resolving the overlap would exceed the
    conservative cross-system area cap, the surface stops at the cap and the
    collision resolver must remove the remaining positional overlap.
    """

    if not isfinite(requested_axial_scale) or requested_axial_scale <= 0.0 or requested_axial_scale > 1.0:
        raise ValueError("requested_axial_scale must be in (0, 1]")
    if not isfinite(area_strain_cap) or area_strain_cap <= 0.0:
        raise ValueError("area_strain_cap must be positive")
    if requested_axial_scale >= 1.0 - 1.0e-10:
        return restore_convex_shape(shape)
    normal = _unit(normal_local)
    rest = _rest_vertices(shape)
    rest_area = _polyhedron_surface_area(rest, shape.faces)
    rest_volume = _polyhedron_volume(rest, shape.faces)
    minimum_safe_scale = _minimum_axial_scale_for_area_cap(shape, normal, area_strain_cap)
    axial_scale = max(requested_axial_scale, minimum_safe_scale)
    current = _affine_contact_vertices(rest, normal, axial_scale)
    area_ratio = _polyhedron_surface_area(current, shape.faces) / rest_area
    volume_ratio = _polyhedron_volume(current, shape.faces) / rest_volume
    status = (
        "resolved_within_conservative_area_cap"
        if axial_scale <= requested_axial_scale + 1.0e-10
        else "surface_cap_reached_remaining_overlap_requires_position_resolution"
    )
    deformation = SurfaceDeformationState(
        model="volume_preserving_affine_contact_v1",
        active=axial_scale < 1.0 - 1.0e-10,
        rest_vertices_local_um=rest,
        normal_local=normal,
        requested_axial_scale=requested_axial_scale,
        axial_scale=axial_scale,
        tangential_scale=1.0 / sqrt(axial_scale),
        volume_ratio=volume_ratio,
        surface_area_ratio=area_ratio,
        elastic_area_strain=area_ratio - 1.0,
        elastic_area_strain_cap=area_strain_cap,
        cap_basis="engineering_cap_half_of_lower_2_percent_human_rbc_lysis_bound_not_phh_specific",
        status=status,
        source_ids=(
            "evans1976_human_membrane_area_lysis",
            "rawicz2000_bilayer_elasticity",
            "guillou2016_membrane_surface_reservoirs",
        ),
    )
    deformed = replace(
        shape,
        vertices_local_um=current,
        geometry_status="volume_preserving_affine_contact_surface_cross_system_area_cap_not_phh_rheology",
        deformation=deformation,
    )
    _validate_shape(deformed)
    return deformed


def restore_convex_shape(shape: ConvexPolyhedronShape) -> ConvexPolyhedronShape:
    if shape.deformation is None:
        return shape
    restored = replace(
        shape,
        vertices_local_um=shape.deformation.rest_vertices_local_um,
        geometry_status="volume_equivalent_regular_truncated_octahedron_proxy_not_observed_cell_shape",
        deformation=None,
    )
    _validate_shape(restored)
    return restored


def _validate_shape(shape: CollisionShape) -> None:
    if isinstance(shape, (SphereShape, CapsuleShape)):
        if not isfinite(shape.radius_um) or shape.radius_um <= 0.0:
            raise ValueError("collision-shape radius_um must be positive")
        if isinstance(shape, CapsuleShape):
            if not isfinite(shape.half_segment_length_um) or shape.half_segment_length_um < 0.0:
                raise ValueError("capsule half_segment_length_um must be non-negative")
            if not all(isfinite(value) for value in shape.axis) or _norm(shape.axis) <= 1.0e-15:
                raise ValueError("capsule axis must be finite and non-zero")
        return

    if not isfinite(shape.equivalent_sphere_radius_um) or shape.equivalent_sphere_radius_um <= 0.0:
        raise ValueError("convex-polyhedron equivalent_sphere_radius_um must be positive")
    if len(shape.vertices_local_um) < 4 or len(shape.faces) < 4:
        raise ValueError("convex polyhedron requires at least four vertices and faces")
    if any(not all(isfinite(value) for value in vertex) for vertex in shape.vertices_local_um):
        raise ValueError("convex-polyhedron vertices must be finite")
    face_ids = [face.id for face in shape.faces]
    if len(face_ids) != len(set(face_ids)):
        raise ValueError("convex-polyhedron face ids must be unique")
    center = _mean(shape.vertices_local_um)
    edge_counts: dict[tuple[int, int], int] = {}
    for face in shape.faces:
        if len(face.vertex_indices) < 3 or len(set(face.vertex_indices)) != len(face.vertex_indices):
            raise ValueError(f"convex face {face.id} requires three distinct vertices")
        if any(index < 0 or index >= len(shape.vertices_local_um) for index in face.vertex_indices):
            raise ValueError(f"convex face {face.id} references an invalid vertex")
        normal = _face_normal(shape.vertices_local_um, face)
        face_center = _mean([shape.vertices_local_um[index] for index in face.vertex_indices])
        if _dot(normal, _sub(face_center, center)) <= 0.0:
            raise ValueError(f"convex face {face.id} must use outward winding")
        plane_point = shape.vertices_local_um[face.vertex_indices[0]]
        for vertex in shape.vertices_local_um:
            if _dot(normal, _sub(vertex, plane_point)) > NUMERIC_CONTACT_TOLERANCE_UM:
                raise ValueError(f"convex face {face.id} violates convexity")
        for i, start in enumerate(face.vertex_indices):
            end = face.vertex_indices[(i + 1) % len(face.vertex_indices)]
            edge = (min(start, end), max(start, end))
            edge_counts[edge] = edge_counts.get(edge, 0) + 1
    if any(count != 2 for count in edge_counts.values()):
        raise ValueError("convex-polyhedron boundary must be a closed two-manifold")
    deformation = shape.deformation
    if deformation is None:
        return
    if deformation.model != "volume_preserving_affine_contact_v1" or not deformation.active:
        raise ValueError("convex deformation must be an active supported model")
    if len(deformation.rest_vertices_local_um) != len(shape.vertices_local_um):
        raise ValueError("convex deformation rest/current vertex counts must match")
    if not all(isfinite(value) for vertex in deformation.rest_vertices_local_um for value in vertex):
        raise ValueError("convex deformation rest vertices must be finite")
    if not (0.0 < deformation.axial_scale <= 1.0 and deformation.tangential_scale >= 1.0):
        raise ValueError("convex deformation scales are invalid")
    if abs(deformation.tangential_scale - 1.0 / sqrt(deformation.axial_scale)) > 1.0e-9:
        raise ValueError("convex deformation must preserve affine volume")
    expected_vertices = _affine_contact_vertices(
        deformation.rest_vertices_local_um,
        deformation.normal_local,
        deformation.axial_scale,
    )
    if any(
        abs(actual - expected) > NUMERIC_CONTACT_TOLERANCE_UM
        for current, target in zip(shape.vertices_local_um, expected_vertices, strict=True)
        for actual, expected in zip(current, target, strict=True)
    ):
        raise ValueError("convex current vertices diverge from deformation state")
    rest_area = _polyhedron_surface_area(deformation.rest_vertices_local_um, shape.faces)
    current_area = _polyhedron_surface_area(shape.vertices_local_um, shape.faces)
    rest_volume = _polyhedron_volume(deformation.rest_vertices_local_um, shape.faces)
    current_volume = _polyhedron_volume(shape.vertices_local_um, shape.faces)
    if abs(current_volume / rest_volume - deformation.volume_ratio) > 1.0e-9:
        raise ValueError("convex deformation volume ratio is inconsistent")
    if abs(current_area / rest_area - deformation.surface_area_ratio) > 1.0e-9:
        raise ValueError("convex deformation area ratio is inconsistent")
    if abs(deformation.volume_ratio - 1.0) > 1.0e-9:
        raise ValueError("convex contact deformation must preserve volume")
    if deformation.elastic_area_strain > deformation.elastic_area_strain_cap + 1.0e-9:
        raise ValueError("convex contact deformation exceeds the elastic area cap")


def _validate_body(body: SpatialBody) -> None:
    if not body.id:
        raise ValueError("spatial body id must be non-empty")
    if not all(isfinite(value) for value in body.center_um):
        raise ValueError(f"{body.id} center_um must contain finite values")
    if not all(isfinite(value) for value in body.velocity_um_s):
        raise ValueError(f"{body.id} velocity_um_s must contain finite values")
    if not all(isfinite(value) for value in body.orientation_xyzw):
        raise ValueError(f"{body.id} orientation must contain finite values")
    if abs(sqrt(sum(value * value for value in body.orientation_xyzw)) - 1.0) > 1.0e-6:
        raise ValueError(f"{body.id} orientation must be a unit quaternion")
    if body.molecular_profile_id is not None and not body.molecular_profile_id:
        raise ValueError(f"{body.id} molecular_profile_id cannot be empty")
    if body.biological_kind == "hepatocyte":
        if body.membrane_material is None:
            raise ValueError(f"{body.id} hepatocyte requires an intrinsic membrane material")
        _validate_membrane_material(body.membrane_material)
    elif body.membrane_material is not None:
        _validate_membrane_material(body.membrane_material)
    _validate_shape(body.shape)


def _validate_membrane_material(profile: MembraneMaterialProfile) -> None:
    if profile.version != "intrinsic_fluid_bilayer_v1":
        raise ValueError("unsupported intrinsic membrane-material version")
    if not profile.intrinsic_fluidity_enabled:
        raise ValueError("hepatocyte membrane fluidity cannot be disabled")
    if profile.engineering_cap_is_phh_measurement:
        raise ValueError("the engineering area cap cannot be labelled as a PHH measurement")
    if not profile.biologically_admissible_shape_modes:
        raise ValueError("intrinsic membrane profile requires biologically admissible shape modes")
    if not profile.implemented_geometry_modes:
        raise ValueError("intrinsic membrane profile requires explicit implemented geometry modes")
    if not profile.unresolved_geometry_modes:
        raise ValueError("intrinsic membrane profile must expose unresolved geometry modes")
    if not profile.surface_tracer_advection_enabled:
        raise ValueError("surface tracers must follow authoritative membrane deformation")
    if profile.active_lateral_diffusion_enabled:
        raise ValueError("healthy-PHH lateral diffusion cannot be enabled without identified coefficients")
    if abs(profile.engineering_area_strain_cap - CONSERVATIVE_ELASTIC_AREA_STRAIN_CAP) > 1.0e-12:
        raise ValueError("intrinsic membrane engineering area cap is inconsistent")
    if profile.quantitative_phh_mechanics_enabled:
        raise ValueError("healthy-PHH quantitative membrane mechanics are not calibrated")
    phh_parameters = (
        profile.bilayer_thickness_nm,
        profile.area_compressibility_mN_per_m,
        profile.bending_rigidity_J,
        profile.membrane_tension_N_per_m,
        profile.cortex_adhesion_J_per_m2,
        profile.surface_viscosity_Pa_s_m,
        profile.lipid_lateral_diffusion_um2_s,
        profile.protein_lateral_diffusion_um2_s,
        profile.rupture_area_strain,
    )
    if any(value is not None for value in phh_parameters):
        raise ValueError("unidentified healthy-PHH membrane parameters must remain null")
    if not profile.reference_measurements:
        raise ValueError("intrinsic membrane profile requires scoped reference evidence")
    measurement_ids = [measurement.id for measurement in profile.reference_measurements]
    if len(measurement_ids) != len(set(measurement_ids)):
        raise ValueError("intrinsic membrane reference ids must be unique")
    for measurement in profile.reference_measurements:
        values = tuple(value for value in (measurement.value, measurement.lower, measurement.upper) if value is not None)
        if not values or any(not isfinite(value) or value < 0.0 for value in values):
            raise ValueError(f"invalid membrane reference measurement: {measurement.id}")
        if measurement.lower is not None and measurement.upper is not None and measurement.lower > measurement.upper:
            raise ValueError(f"invalid membrane reference interval: {measurement.id}")
        if measurement.may_parameterize_healthy_phh:
            raise ValueError(f"cross-system membrane reference cannot parameterize PHH: {measurement.id}")


def _shape_segment(body: SpatialBody) -> tuple[Vector3, Vector3, float]:
    _validate_body(body)
    if isinstance(body.shape, ConvexPolyhedronShape):
        raise TypeError("convex polyhedra do not have a swept-sphere segment")
    if isinstance(body.shape, SphereShape):
        return body.center_um, body.center_um, body.shape.radius_um
    axis = _unit(_rotate(body.shape.axis, body.orientation_xyzw))
    offset = _scale(axis, body.shape.half_segment_length_um)
    return _sub(body.center_um, offset), _add(body.center_um, offset), body.shape.radius_um


def _closest_points_on_segments(
    p1: Vector3,
    q1: Vector3,
    p2: Vector3,
    q2: Vector3,
) -> tuple[Vector3, Vector3]:
    d1 = _sub(q1, p1)
    d2 = _sub(q2, p2)
    r = _sub(p1, p2)
    a = _dot(d1, d1)
    e = _dot(d2, d2)
    epsilon = 1.0e-15
    if a <= epsilon and e <= epsilon:
        return p1, p2
    if a <= epsilon:
        s = 0.0
        t = _clamp(_dot(d2, r) / e, 0.0, 1.0)
    else:
        c = _dot(d1, r)
        if e <= epsilon:
            t = 0.0
            s = _clamp(-c / a, 0.0, 1.0)
        else:
            b = _dot(d1, d2)
            denominator = a * e - b * b
            s = _clamp((b * _dot(d2, r) - c * e) / denominator, 0.0, 1.0) if denominator else 0.0
            t = (b * s + _dot(d2, r)) / e
            if t < 0.0:
                t = 0.0
                s = _clamp(-c / a, 0.0, 1.0)
            elif t > 1.0:
                t = 1.0
                s = _clamp((b - c) / a, 0.0, 1.0)
    return _add(p1, _scale(d1, s)), _add(p2, _scale(d2, t))


def _world_polyhedron(body: SpatialBody) -> tuple[tuple[Vector3, ...], tuple[Vector3, ...]]:
    if not isinstance(body.shape, ConvexPolyhedronShape):
        raise TypeError("body is not a convex polyhedron")
    vertices = tuple(_add(body.center_um, _rotate(vertex, body.orientation_xyzw)) for vertex in body.shape.vertices_local_um)
    normals = tuple(_rotate(_face_normal(body.shape.vertices_local_um, face), body.orientation_xyzw) for face in body.shape.faces)
    return vertices, normals


def _poly_edges(shape: ConvexPolyhedronShape) -> tuple[tuple[int, int], ...]:
    edges: set[tuple[int, int]] = set()
    for face in shape.faces:
        for index, start in enumerate(face.vertex_indices):
            end = face.vertex_indices[(index + 1) % len(face.vertex_indices)]
            edges.add((min(start, end), max(start, end)))
    return tuple(sorted(edges))


def _triangle_faces(shape: ConvexPolyhedronShape) -> tuple[tuple[int, int, int], ...]:
    triangles: list[tuple[int, int, int]] = []
    for face in shape.faces:
        anchor = face.vertex_indices[0]
        triangles.extend(
            (anchor, face.vertex_indices[index], face.vertex_indices[index + 1])
            for index in range(1, len(face.vertex_indices) - 1)
        )
    return tuple(triangles)


def _closest_point_on_triangle(point: Vector3, a: Vector3, b: Vector3, c: Vector3) -> Vector3:
    ab = _sub(b, a)
    ac = _sub(c, a)
    ap = _sub(point, a)
    d1 = _dot(ab, ap)
    d2 = _dot(ac, ap)
    if d1 <= 0.0 and d2 <= 0.0:
        return a
    bp = _sub(point, b)
    d3 = _dot(ab, bp)
    d4 = _dot(ac, bp)
    if d3 >= 0.0 and d4 <= d3:
        return b
    vc = d1 * d4 - d3 * d2
    if vc <= 0.0 and d1 >= 0.0 and d3 <= 0.0:
        return _add(a, _scale(ab, d1 / (d1 - d3)))
    cp = _sub(point, c)
    d5 = _dot(ab, cp)
    d6 = _dot(ac, cp)
    if d6 >= 0.0 and d5 <= d6:
        return c
    vb = d5 * d2 - d1 * d6
    if vb <= 0.0 and d2 >= 0.0 and d6 <= 0.0:
        return _add(a, _scale(ac, d2 / (d2 - d6)))
    va = d3 * d6 - d5 * d4
    if va <= 0.0 and (d4 - d3) >= 0.0 and (d5 - d6) >= 0.0:
        edge = _sub(c, b)
        return _add(b, _scale(edge, (d4 - d3) / ((d4 - d3) + (d5 - d6))))
    denominator = 1.0 / (va + vb + vc)
    return _add(a, _add(_scale(ab, vb * denominator), _scale(ac, vc * denominator)))


def _segment_triangle_intersection(
    start: Vector3,
    end: Vector3,
    a: Vector3,
    b: Vector3,
    c: Vector3,
) -> Vector3 | None:
    """Return the segment/triangle intersection using Moller-Trumbore."""

    direction = _sub(end, start)
    edge_1 = _sub(b, a)
    edge_2 = _sub(c, a)
    p = _cross(direction, edge_2)
    determinant = _dot(edge_1, p)
    if abs(determinant) <= NUMERIC_AXIS_TOLERANCE:
        return None
    inverse = 1.0 / determinant
    t_vector = _sub(start, a)
    u = _dot(t_vector, p) * inverse
    if u < -NUMERIC_AXIS_TOLERANCE or u > 1.0 + NUMERIC_AXIS_TOLERANCE:
        return None
    q = _cross(t_vector, edge_1)
    v = _dot(direction, q) * inverse
    if v < -NUMERIC_AXIS_TOLERANCE or u + v > 1.0 + NUMERIC_AXIS_TOLERANCE:
        return None
    t = _dot(edge_2, q) * inverse
    if t < -NUMERIC_AXIS_TOLERANCE or t > 1.0 + NUMERIC_AXIS_TOLERANCE:
        return None
    return _add(start, _scale(direction, _clamp(t, 0.0, 1.0)))


def _closest_segment_to_face(
    segment_start: Vector3,
    segment_end: Vector3,
    face: ConvexFace,
    vertices: tuple[Vector3, ...],
) -> tuple[Vector3, Vector3, float]:
    """Closest axis/surface points for one convex polygonal face."""

    best_axis = segment_start
    best_surface = vertices[face.vertex_indices[0]]
    best_distance = float("inf")
    anchor = face.vertex_indices[0]
    for index in range(1, len(face.vertex_indices) - 1):
        ia, ib, ic = anchor, face.vertex_indices[index], face.vertex_indices[index + 1]
        a, b, c = vertices[ia], vertices[ib], vertices[ic]
        intersection = _segment_triangle_intersection(segment_start, segment_end, a, b, c)
        if intersection is not None:
            return intersection, intersection, 0.0
        for point in (segment_start, segment_end):
            surface = _closest_point_on_triangle(point, a, b, c)
            distance = _norm(_sub(point, surface))
            if distance < best_distance:
                best_axis, best_surface, best_distance = point, surface, distance
        for edge_start, edge_end in ((a, b), (b, c), (c, a)):
            axis_point, surface = _closest_points_on_segments(
                segment_start, segment_end, edge_start, edge_end
            )
            distance = _norm(_sub(axis_point, surface))
            if distance < best_distance:
                best_axis, best_surface, best_distance = axis_point, surface, distance
    return best_axis, best_surface, best_distance


def _closest_point_to_face(
    point: Vector3,
    face: ConvexFace,
    vertices: tuple[Vector3, ...],
) -> tuple[Vector3, float]:
    best_surface = vertices[face.vertex_indices[0]]
    best_distance = float("inf")
    anchor = face.vertex_indices[0]
    for index in range(1, len(face.vertex_indices) - 1):
        surface = _closest_point_on_triangle(
            point,
            vertices[anchor],
            vertices[face.vertex_indices[index]],
            vertices[face.vertex_indices[index + 1]],
        )
        distance = _norm(_sub(point, surface))
        if distance < best_distance:
            best_surface, best_distance = surface, distance
    return best_surface, best_distance


def _faces_at_surface_point(
    shape: ConvexPolyhedronShape,
    vertices: tuple[Vector3, ...],
    point: Vector3,
) -> tuple[ConvexFace, ...]:
    candidates = []
    for face in shape.faces:
        _, distance = _closest_point_to_face(point, face, vertices)
        if distance <= NUMERIC_CONTACT_TOLERANCE_UM:
            candidates.append(face)
    return tuple(candidates)


def _closest_polyhedron_points(
    shape_a: ConvexPolyhedronShape,
    vertices_a: tuple[Vector3, ...],
    shape_b: ConvexPolyhedronShape,
    vertices_b: tuple[Vector3, ...],
) -> tuple[Vector3, Vector3, float]:
    best_a = vertices_a[0]
    best_b = vertices_b[0]
    best_sq = float("inf")

    def consider(point_a: Vector3, point_b: Vector3) -> None:
        nonlocal best_a, best_b, best_sq
        delta = _sub(point_b, point_a)
        distance_sq = _dot(delta, delta)
        if distance_sq < best_sq:
            best_a, best_b, best_sq = point_a, point_b, distance_sq

    triangles_a = _triangle_faces(shape_a)
    triangles_b = _triangle_faces(shape_b)
    for point in vertices_a:
        for ia, ib, ic in triangles_b:
            consider(point, _closest_point_on_triangle(point, vertices_b[ia], vertices_b[ib], vertices_b[ic]))
    for point in vertices_b:
        for ia, ib, ic in triangles_a:
            consider(_closest_point_on_triangle(point, vertices_a[ia], vertices_a[ib], vertices_a[ic]), point)
    for edge_a in _poly_edges(shape_a):
        for edge_b in _poly_edges(shape_b):
            point_a, point_b = _closest_points_on_segments(
                vertices_a[edge_a[0]], vertices_a[edge_a[1]], vertices_b[edge_b[0]], vertices_b[edge_b[1]]
            )
            consider(point_a, point_b)
    return best_a, best_b, sqrt(best_sq)


def _canonical_axis(axis: Vector3) -> Vector3:
    unit = _unit(axis)
    for component in unit:
        if abs(component) > NUMERIC_AXIS_TOLERANCE:
            return _scale(unit, -1.0) if component < 0.0 else unit
    return unit


def _sat_axes(
    shape_a: ConvexPolyhedronShape,
    vertices_a: tuple[Vector3, ...],
    normals_a: tuple[Vector3, ...],
    shape_b: ConvexPolyhedronShape,
    vertices_b: tuple[Vector3, ...],
    normals_b: tuple[Vector3, ...],
) -> tuple[Vector3, ...]:
    axes: list[Vector3] = []
    seen: set[tuple[int, int, int]] = set()

    def add_axis(axis: Vector3) -> None:
        if _norm(axis) <= NUMERIC_AXIS_TOLERANCE:
            return
        canonical = _canonical_axis(axis)
        key = tuple(round(component * 1.0e8) for component in canonical)
        if key not in seen:
            seen.add(key)
            axes.append(canonical)

    for normal in (*normals_a, *normals_b):
        add_axis(normal)
    edges_a = tuple(_sub(vertices_a[end], vertices_a[start]) for start, end in _poly_edges(shape_a))
    edges_b = tuple(_sub(vertices_b[end], vertices_b[start]) for start, end in _poly_edges(shape_b))
    for edge_a in edges_a:
        for edge_b in edges_b:
            add_axis(_cross(edge_a, edge_b))
    return tuple(axes)


def _polygon_signed_area(points: list[Vector2]) -> float:
    return 0.5 * sum(
        points[index][0] * points[(index + 1) % len(points)][1]
        - points[(index + 1) % len(points)][0] * points[index][1]
        for index in range(len(points))
    ) if len(points) >= 3 else 0.0


def _clip_convex_polygon(subject: list[Vector2], clip: list[Vector2]) -> list[Vector2]:
    if _polygon_signed_area(subject) < 0.0:
        subject = list(reversed(subject))
    if _polygon_signed_area(clip) < 0.0:
        clip = list(reversed(clip))
    output = subject
    epsilon = 1.0e-10
    for index, edge_start in enumerate(clip):
        edge_end = clip[(index + 1) % len(clip)]
        edge = (edge_end[0] - edge_start[0], edge_end[1] - edge_start[1])

        def side(point: Vector2) -> float:
            return edge[0] * (point[1] - edge_start[1]) - edge[1] * (point[0] - edge_start[0])

        source = output
        output = []
        if not source:
            break
        previous = source[-1]
        previous_side = side(previous)
        for current in source:
            current_side = side(current)
            current_inside = current_side >= -epsilon
            previous_inside = previous_side >= -epsilon
            if current_inside != previous_inside:
                denominator = previous_side - current_side
                t = previous_side / denominator if abs(denominator) > epsilon else 0.0
                output.append((
                    previous[0] + (current[0] - previous[0]) * t,
                    previous[1] + (current[1] - previous[1]) * t,
                ))
            if current_inside:
                output.append(current)
            previous, previous_side = current, current_side
    return output


def _polygon_area_centroid(points: list[Vector2]) -> tuple[float, Vector2]:
    signed_area = _polygon_signed_area(points)
    if abs(signed_area) <= 1.0e-12:
        return 0.0, (0.0, 0.0)
    cx = 0.0
    cy = 0.0
    for index, point in enumerate(points):
        nxt = points[(index + 1) % len(points)]
        cross = point[0] * nxt[1] - nxt[0] * point[1]
        cx += (point[0] + nxt[0]) * cross
        cy += (point[1] + nxt[1]) * cross
    factor = 1.0 / (6.0 * signed_area)
    return abs(signed_area), (cx * factor, cy * factor)


@dataclass(frozen=True)
class _PatchIntersection:
    face_a: ConvexFace
    face_b: ConvexFace
    polygon: tuple[Vector3, ...]
    area_um2: float
    centroid: Vector3
    normal_a_to_b: Vector3


def _contact_patch_intersection(
    body_a: SpatialBody,
    vertices_a: tuple[Vector3, ...],
    normals_a: tuple[Vector3, ...],
    body_b: SpatialBody,
    vertices_b: tuple[Vector3, ...],
    normals_b: tuple[Vector3, ...],
) -> _PatchIntersection | None:
    assert isinstance(body_a.shape, ConvexPolyhedronShape)
    assert isinstance(body_b.shape, ConvexPolyhedronShape)
    center_delta = _sub(body_b.center_um, body_a.center_um)
    best: _PatchIntersection | None = None
    for index_a, face_a in enumerate(body_a.shape.faces):
        normal_a = _unit(normals_a[index_a])
        if _dot(normal_a, center_delta) <= 0.0:
            continue
        points_a = [vertices_a[index] for index in face_a.vertex_indices]
        origin = points_a[0]
        edge = next((_sub(point, origin) for point in points_a[1:] if _norm(_sub(point, origin)) > NUMERIC_AXIS_TOLERANCE), None)
        if edge is None:
            continue
        basis_u = _unit(edge)
        basis_v = _unit(_cross(normal_a, basis_u))
        polygon_a = [(_dot(_sub(point, origin), basis_u), _dot(_sub(point, origin), basis_v)) for point in points_a]
        for index_b, face_b in enumerate(body_b.shape.faces):
            normal_b = _unit(normals_b[index_b])
            if _dot(normal_a, normal_b) > -1.0 + 1.0e-7:
                continue
            points_b = [vertices_b[index] for index in face_b.vertex_indices]
            plane_offsets = [_dot(_sub(point, origin), normal_a) for point in points_b]
            if max(abs(value) for value in plane_offsets) > NUMERIC_CONTACT_TOLERANCE_UM:
                continue
            polygon_b = [(_dot(_sub(point, origin), basis_u), _dot(_sub(point, origin), basis_v)) for point in points_b]
            clipped = _clip_convex_polygon(polygon_a, polygon_b)
            area, centroid_2d = _polygon_area_centroid(clipped)
            if area <= 1.0e-10 or (best is not None and area <= best.area_um2):
                continue
            polygon_3d = tuple(
                _add(origin, _add(_scale(basis_u, point[0]), _scale(basis_v, point[1])))
                for point in clipped
            )
            centroid = _add(origin, _add(_scale(basis_u, centroid_2d[0]), _scale(basis_v, centroid_2d[1])))
            best = _PatchIntersection(face_a, face_b, polygon_3d, area, centroid, normal_a)
    return best


@dataclass(frozen=True)
class _GeometryResult:
    surface_gap_um: float
    overlap_depth_um: float
    relation: Literal["separated", "touching", "overlapping"]
    geometric_contact: bool
    closest_point_a_um: Vector3
    closest_point_b_um: Vector3
    normal_a_to_b: Vector3
    contact_face_a_id: str | None = None
    contact_face_b_id: str | None = None
    contact_face_candidates_a: tuple[str, ...] = ()
    contact_face_candidates_b: tuple[str, ...] = ()
    membrane_domain_a: MembraneDomain | None = None
    membrane_domain_b: MembraneDomain | None = None
    membrane_domain_candidates_a: tuple[MembraneDomain, ...] = ()
    membrane_domain_candidates_b: tuple[MembraneDomain, ...] = ()
    domain_assignment_status_a: DomainAssignmentStatus = "not_applicable_or_unresolved"
    domain_assignment_status_b: DomainAssignmentStatus = "not_applicable_or_unresolved"
    contact_patch_polygon_um: tuple[Vector3, ...] = ()
    contact_patch_area_um2: float | None = None
    contact_patch_status: str = "unknown_requires_resolved_surface_contact"


@dataclass(frozen=True)
class _SurfaceFeatureResolution:
    face_id: str | None
    membrane_domain: MembraneDomain | None
    face_candidates: tuple[str, ...]
    membrane_domain_candidates: tuple[MembraneDomain, ...]
    status: DomainAssignmentStatus


def _resolve_surface_feature(faces: tuple[ConvexFace, ...] | list[ConvexFace]) -> _SurfaceFeatureResolution:
    unique_faces = tuple(dict.fromkeys(face.id for face in faces))
    if not unique_faces:
        return _SurfaceFeatureResolution(None, None, (), (), "not_applicable_or_unresolved")
    face_by_id = {face.id: face for face in faces}
    domains = tuple(dict.fromkeys(face_by_id[face_id].membrane_domain for face_id in unique_faces))
    if len(unique_faces) == 1 and len(domains) == 1 and domains[0] != "unknown":
        return _SurfaceFeatureResolution(
            unique_faces[0], domains[0], unique_faces, domains, "resolved_unique_face"
        )
    if len(domains) == 1 and domains[0] != "unknown":
        return _SurfaceFeatureResolution(
            None, domains[0], unique_faces, domains, "resolved_shared_feature_same_domain"
        )
    return _SurfaceFeatureResolution(
        None, None, unique_faces, domains, "ambiguous_shared_feature_multiple_domains"
    )


def _polyhedron_pair_geometry(body_a: SpatialBody, body_b: SpatialBody) -> _GeometryResult:
    assert isinstance(body_a.shape, ConvexPolyhedronShape)
    assert isinstance(body_b.shape, ConvexPolyhedronShape)
    vertices_a, normals_a = _world_polyhedron(body_a)
    vertices_b, normals_b = _world_polyhedron(body_b)
    axes = _sat_axes(body_a.shape, vertices_a, normals_a, body_b.shape, vertices_b, normals_b)
    separated = False
    minimum_overlap = float("inf")
    minimum_axis = _unit(_sub(body_b.center_um, body_a.center_um))
    for axis in axes:
        projection_a = tuple(_dot(vertex, axis) for vertex in vertices_a)
        projection_b = tuple(_dot(vertex, axis) for vertex in vertices_b)
        min_a, max_a = min(projection_a), max(projection_a)
        min_b, max_b = min(projection_b), max(projection_b)
        if min_b - max_a > NUMERIC_CONTACT_TOLERANCE_UM or min_a - max_b > NUMERIC_CONTACT_TOLERANCE_UM:
            separated = True
            continue
        overlap = min(max_a - min_b, max_b - min_a)
        if overlap < minimum_overlap:
            minimum_overlap = max(0.0, overlap)
            minimum_axis = axis
    center_delta = _sub(body_b.center_um, body_a.center_um)
    if _dot(minimum_axis, center_delta) < 0.0:
        minimum_axis = _scale(minimum_axis, -1.0)

    if separated:
        point_a, point_b, distance = _closest_polyhedron_points(body_a.shape, vertices_a, body_b.shape, vertices_b)
        normal = _unit(_sub(point_b, point_a), _unit(center_delta))
        relation: Literal["separated", "touching", "overlapping"] = (
            "separated" if distance > NUMERIC_CONTACT_TOLERANCE_UM else "touching"
        )
        return _GeometryResult(
            surface_gap_um=distance if relation == "separated" else 0.0,
            overlap_depth_um=0.0,
            relation=relation,
            geometric_contact=relation != "separated",
            closest_point_a_um=point_a,
            closest_point_b_um=point_b,
            normal_a_to_b=normal,
        )

    patch = _contact_patch_intersection(body_a, vertices_a, normals_a, body_b, vertices_b, normals_b)
    touching = minimum_overlap <= NUMERIC_CONTACT_TOLERANCE_UM
    relation = "touching" if touching else "overlapping"
    overlap = 0.0 if touching else minimum_overlap
    if patch is not None:
        feature_a = _resolve_surface_feature((patch.face_a,))
        feature_b = _resolve_surface_feature((patch.face_b,))
        return _GeometryResult(
            surface_gap_um=0.0 if touching else -overlap,
            overlap_depth_um=overlap,
            relation=relation,
            geometric_contact=True,
            closest_point_a_um=patch.centroid,
            closest_point_b_um=patch.centroid,
            normal_a_to_b=patch.normal_a_to_b,
            contact_face_a_id=feature_a.face_id,
            contact_face_b_id=feature_b.face_id,
            contact_face_candidates_a=feature_a.face_candidates,
            contact_face_candidates_b=feature_b.face_candidates,
            membrane_domain_a=feature_a.membrane_domain,
            membrane_domain_b=feature_b.membrane_domain,
            membrane_domain_candidates_a=feature_a.membrane_domain_candidates,
            membrane_domain_candidates_b=feature_b.membrane_domain_candidates,
            domain_assignment_status_a=feature_a.status,
            domain_assignment_status_b=feature_b.status,
            contact_patch_polygon_um=patch.polygon,
            contact_patch_area_um2=patch.area_um2,
            contact_patch_status="derived_from_coplanar_convex_face_intersection_geometry_only",
        )
    support_a = max(vertices_a, key=lambda vertex: _dot(vertex, minimum_axis))
    support_b = min(vertices_b, key=lambda vertex: _dot(vertex, minimum_axis))
    feature_a = _resolve_surface_feature(_faces_at_surface_point(body_a.shape, vertices_a, support_a))
    feature_b = _resolve_surface_feature(_faces_at_surface_point(body_b.shape, vertices_b, support_b))
    return _GeometryResult(
        surface_gap_um=0.0 if touching else -overlap,
        overlap_depth_um=overlap,
        relation=relation,
        geometric_contact=True,
        closest_point_a_um=support_a,
        closest_point_b_um=support_b,
        normal_a_to_b=minimum_axis,
        contact_face_a_id=feature_a.face_id,
        contact_face_b_id=feature_b.face_id,
        contact_face_candidates_a=feature_a.face_candidates,
        contact_face_candidates_b=feature_b.face_candidates,
        membrane_domain_a=feature_a.membrane_domain,
        membrane_domain_b=feature_b.membrane_domain,
        membrane_domain_candidates_a=feature_a.membrane_domain_candidates,
        membrane_domain_candidates_b=feature_b.membrane_domain_candidates,
        domain_assignment_status_a=feature_a.status,
        domain_assignment_status_b=feature_b.status,
        contact_patch_status="unknown_non_coplanar_or_edge_contact",
    )


def _round_pair_geometry(body_a: SpatialBody, body_b: SpatialBody) -> _GeometryResult:
    a0, a1, radius_a = _shape_segment(body_a)
    b0, b1, radius_b = _shape_segment(body_b)
    line_a, line_b = _closest_points_on_segments(a0, a1, b0, b1)
    center_line_delta = _sub(line_b, line_a)
    center_line_distance = _norm(center_line_delta)
    fallback = _unit(_sub(body_b.center_um, body_a.center_um))
    normal = _unit(center_line_delta, fallback)
    surface_gap = center_line_distance - radius_a - radius_b
    overlap = max(0.0, -surface_gap)
    if surface_gap > NUMERIC_CONTACT_TOLERANCE_UM:
        relation: Literal["separated", "touching", "overlapping"] = "separated"
    elif overlap <= NUMERIC_CONTACT_TOLERANCE_UM:
        relation = "touching"
    else:
        relation = "overlapping"
    return _GeometryResult(
        surface_gap_um=surface_gap,
        overlap_depth_um=overlap,
        relation=relation,
        geometric_contact=relation != "separated",
        closest_point_a_um=_add(line_a, _scale(normal, radius_a)),
        closest_point_b_um=_sub(line_b, _scale(normal, radius_b)),
        normal_a_to_b=normal,
        contact_patch_status="unknown_point_or_line_contact_requires_resolved_surface",
    )


def _point_inside_polyhedron(point: Vector3, body: SpatialBody, vertices: tuple[Vector3, ...], normals: tuple[Vector3, ...]) -> bool:
    assert isinstance(body.shape, ConvexPolyhedronShape)
    return all(
        _dot(normals[index], _sub(point, vertices[face.vertex_indices[0]])) <= NUMERIC_CONTACT_TOLERANCE_UM
        for index, face in enumerate(body.shape.faces)
    )


def _polyhedron_round_geometry(poly_body: SpatialBody, round_body: SpatialBody) -> _GeometryResult:
    assert isinstance(poly_body.shape, ConvexPolyhedronShape)
    segment_start, segment_end, radius = _shape_segment(round_body)
    vertices, normals = _world_polyhedron(poly_body)
    sample_points = (segment_start, segment_end, _scale(_add(segment_start, segment_end), 0.5))
    inside_point = next((point for point in sample_points if _point_inside_polyhedron(point, poly_body, vertices, normals)), None)
    if inside_point is not None:
        face_results = tuple(
            (face, *_closest_point_to_face(inside_point, face, vertices))
            for face in poly_body.shape.faces
        )
        nearest_face, nearest_boundary, nearest_distance = min(face_results, key=lambda item: item[2])
        candidate_faces = tuple(
            face for face, _, distance in face_results
            if distance <= nearest_distance + NUMERIC_CONTACT_TOLERANCE_UM
        )
        feature = _resolve_surface_feature(candidate_faces)
        normal_poly_to_round = _unit(_sub(inside_point, nearest_boundary), _unit(_sub(round_body.center_um, poly_body.center_um)))
        return _GeometryResult(
            surface_gap_um=-(radius + nearest_distance),
            overlap_depth_um=radius + nearest_distance,
            relation="overlapping",
            geometric_contact=True,
            closest_point_a_um=nearest_boundary,
            closest_point_b_um=_sub(inside_point, _scale(normal_poly_to_round, radius)),
            normal_a_to_b=normal_poly_to_round,
            contact_face_a_id=feature.face_id,
            contact_face_candidates_a=feature.face_candidates,
            membrane_domain_a=feature.membrane_domain,
            membrane_domain_candidates_a=feature.membrane_domain_candidates,
            domain_assignment_status_a=feature.status,
            contact_patch_status="unknown_mixed_shape_penetration",
        )

    face_results = tuple(
        (face, *_closest_segment_to_face(segment_start, segment_end, face, vertices))
        for face in poly_body.shape.faces
    )
    best_face, best_axis, best_surface, best_distance = min(face_results, key=lambda item: item[3])
    candidate_faces = tuple(
        face for face, _, _, distance in face_results
        if distance <= best_distance + NUMERIC_CONTACT_TOLERANCE_UM
    )
    feature = _resolve_surface_feature(candidate_faces)
    normal = _unit(_sub(best_axis, best_surface), _unit(_sub(round_body.center_um, poly_body.center_um)))
    gap = best_distance - radius
    overlap = max(0.0, -gap)
    relation: Literal["separated", "touching", "overlapping"] = (
        "separated" if gap > NUMERIC_CONTACT_TOLERANCE_UM else "touching" if overlap <= NUMERIC_CONTACT_TOLERANCE_UM else "overlapping"
    )
    return _GeometryResult(
        surface_gap_um=gap,
        overlap_depth_um=overlap,
        relation=relation,
        geometric_contact=relation != "separated",
        closest_point_a_um=best_surface,
        closest_point_b_um=_sub(best_axis, _scale(normal, radius)),
        normal_a_to_b=normal,
        contact_face_a_id=feature.face_id,
        contact_face_candidates_a=feature.face_candidates,
        membrane_domain_a=feature.membrane_domain,
        membrane_domain_candidates_a=feature.membrane_domain_candidates,
        domain_assignment_status_a=feature.status,
        contact_patch_status="unknown_mixed_shape_contact_requires_deformable_surface",
    )


def _compute_geometry(body_a: SpatialBody, body_b: SpatialBody) -> _GeometryResult:
    a_poly = isinstance(body_a.shape, ConvexPolyhedronShape)
    b_poly = isinstance(body_b.shape, ConvexPolyhedronShape)
    if a_poly and b_poly:
        return _polyhedron_pair_geometry(body_a, body_b)
    if not a_poly and not b_poly:
        return _round_pair_geometry(body_a, body_b)
    if a_poly:
        return _polyhedron_round_geometry(body_a, body_b)
    result = _polyhedron_round_geometry(body_b, body_a)
    return replace(
        result,
        closest_point_a_um=result.closest_point_b_um,
        closest_point_b_um=result.closest_point_a_um,
        normal_a_to_b=_scale(result.normal_a_to_b, -1.0),
        contact_face_a_id=result.contact_face_b_id,
        contact_face_b_id=result.contact_face_a_id,
        contact_face_candidates_a=result.contact_face_candidates_b,
        contact_face_candidates_b=result.contact_face_candidates_a,
        membrane_domain_a=result.membrane_domain_b,
        membrane_domain_b=result.membrane_domain_a,
        membrane_domain_candidates_a=result.membrane_domain_candidates_b,
        membrane_domain_candidates_b=result.membrane_domain_candidates_a,
        domain_assignment_status_a=result.domain_assignment_status_b,
        domain_assignment_status_b=result.domain_assignment_status_a,
    )


def compute_pair_relation(
    body_a: SpatialBody,
    body_b: SpatialBody,
    *,
    world_time_s: float = 0.0,
    previous: SpatialPairRelation | None = None,
) -> SpatialPairRelation:
    """Compute geometry plus an edge-triggered contact input state."""

    if body_a.id == body_b.id:
        raise ValueError("pair relation requires two distinct body ids")
    if not isfinite(world_time_s) or world_time_s < 0.0:
        raise ValueError("world_time_s must be non-negative")
    _validate_body(body_a)
    _validate_body(body_b)
    geometry = _compute_geometry(body_a, body_b)
    was_active = previous.contact_input_active if previous is not None else False
    if geometry.geometric_contact:
        contact_event: ContactEventKind = "stay" if was_active else "enter"
    else:
        contact_event = "exit" if was_active else "none"
    carry_previous_domains = contact_event == "exit" and previous is not None
    relative_velocity = _sub(body_b.velocity_um_s, body_a.velocity_um_s)
    area_blocker = (
        "contact patch area is simulated geometry, not measured tissue morphometry"
        if geometry.contact_patch_area_um2 is not None
        else "contact patch area is unavailable for this contact topology"
    )
    return SpatialPairRelation(
        id="__".join(sorted((body_a.id, body_b.id))),
        body_a=body_a.id,
        body_b=body_b.id,
        body_a_kind=body_a.biological_kind,
        body_b_kind=body_b.biological_kind,
        world_time_s=world_time_s,
        center_distance_um=_norm(_sub(body_b.center_um, body_a.center_um)),
        surface_gap_um=geometry.surface_gap_um,
        overlap_depth_um=geometry.overlap_depth_um,
        relation=geometry.relation,
        geometric_contact=geometry.geometric_contact,
        contact_event=contact_event,
        contact_input_active=geometry.geometric_contact,
        closest_point_a_um=geometry.closest_point_a_um,
        closest_point_b_um=geometry.closest_point_b_um,
        normal_a_to_b=geometry.normal_a_to_b,
        relative_normal_velocity_um_s=_dot(relative_velocity, geometry.normal_a_to_b),
        contact_face_a_id=previous.contact_face_a_id if carry_previous_domains else geometry.contact_face_a_id,
        contact_face_b_id=previous.contact_face_b_id if carry_previous_domains else geometry.contact_face_b_id,
        contact_face_candidates_a=(
            previous.contact_face_candidates_a if carry_previous_domains else geometry.contact_face_candidates_a
        ),
        contact_face_candidates_b=(
            previous.contact_face_candidates_b if carry_previous_domains else geometry.contact_face_candidates_b
        ),
        membrane_domain_a=previous.membrane_domain_a if carry_previous_domains else geometry.membrane_domain_a,
        membrane_domain_b=previous.membrane_domain_b if carry_previous_domains else geometry.membrane_domain_b,
        membrane_domain_candidates_a=(
            previous.membrane_domain_candidates_a if carry_previous_domains else geometry.membrane_domain_candidates_a
        ),
        membrane_domain_candidates_b=(
            previous.membrane_domain_candidates_b if carry_previous_domains else geometry.membrane_domain_candidates_b
        ),
        domain_assignment_status_a=(
            previous.domain_assignment_status_a if carry_previous_domains else geometry.domain_assignment_status_a
        ),
        domain_assignment_status_b=(
            previous.domain_assignment_status_b if carry_previous_domains else geometry.domain_assignment_status_b
        ),
        contact_patch_polygon_um=geometry.contact_patch_polygon_um,
        contact_patch_area_um2=geometry.contact_patch_area_um2,
        normal_load_nN=None,
        contact_patch_status=geometry.contact_patch_status,
        force_status="unknown_requires_source_backed_material_and_adhesion_law",
        quantitative_biological_effects_enabled=False,
        blockers=(
            area_blocker,
            "normal force and adhesion bond state are unavailable",
            "no source-backed receptor, junction, or mechanotransduction law is attached",
        ),
    )


def _restore_body_surface(body: SpatialBody) -> SpatialBody:
    if not isinstance(body.shape, ConvexPolyhedronShape) or body.shape.deformation is None:
        return body
    return replace(body, shape=restore_convex_shape(body.shape))


def _support_from_center(shape: ConvexPolyhedronShape, direction: Vector3) -> float:
    vertices = _rest_vertices(shape)
    center = _mean(vertices)
    return max(_dot(_sub(vertex, center), direction) for vertex in vertices)


def resolve_deformable_contact_surfaces(bodies: tuple[SpatialBody, ...]) -> tuple[SpatialBody, ...]:
    """Resolve isolated hepatocyte-hepatocyte overlap without a force law.

    This is deliberately narrow. A single overlapping convex hepatocyte pair is
    compressed along the SAT contact normal, expanded tangentially to preserve
    volume, and capped by actual triangulated surface area. Any overlap that
    would exceed the cap is removed by symmetric positional projection. Mixed
    materials and multi-neighbour contacts remain rigid until their mechanics
    are identified.
    """

    restored = tuple(_restore_body_surface(body) for body in bodies)
    raw_relations = tuple(compute_pair_relation(a, b) for a, b in combinations(restored, 2))
    overlapping = [relation for relation in raw_relations if relation.overlap_depth_um > NUMERIC_CONTACT_TOLERANCE_UM]
    contact_counts: dict[str, int] = {}
    for relation in overlapping:
        contact_counts[relation.body_a] = contact_counts.get(relation.body_a, 0) + 1
        contact_counts[relation.body_b] = contact_counts.get(relation.body_b, 0) + 1
    by_id = {body.id: index for index, body in enumerate(restored)}
    resolved = list(restored)
    mechanics_sources = (
        "evans1976_human_membrane_area_lysis",
        "rawicz2000_bilayer_elasticity",
        "guillou2016_membrane_surface_reservoirs",
    )

    for relation in overlapping:
        if contact_counts.get(relation.body_a) != 1 or contact_counts.get(relation.body_b) != 1:
            continue
        index_a = by_id[relation.body_a]
        index_b = by_id[relation.body_b]
        body_a = restored[index_a]
        body_b = restored[index_b]
        if body_a.biological_kind != "hepatocyte" or body_b.biological_kind != "hepatocyte":
            continue
        if not isinstance(body_a.shape, ConvexPolyhedronShape) or not isinstance(body_b.shape, ConvexPolyhedronShape):
            continue
        if (
            len(body_a.shape.vertices_local_um) != len(body_b.shape.vertices_local_um)
            or tuple(face.vertex_indices for face in body_a.shape.faces)
            != tuple(face.vertex_indices for face in body_b.shape.faces)
        ):
            continue

        normal_world = _unit(relation.normal_a_to_b)
        normal_a_local = _unit(_inverse_rotate(normal_world, body_a.orientation_xyzw))
        normal_b_local = _unit(_inverse_rotate(_scale(normal_world, -1.0), body_b.orientation_xyzw))
        support_a = _support_from_center(body_a.shape, normal_a_local)
        support_b = _support_from_center(body_b.shape, normal_b_local)
        total_support = support_a + support_b
        if total_support <= NUMERIC_CONTACT_TOLERANCE_UM:
            continue
        requested_scale = _clamp(1.0 - relation.overlap_depth_um / total_support, 1.0e-3, 1.0)
        trial_a = deform_convex_shape_for_contact(body_a.shape, normal_a_local, requested_scale)
        trial_b = deform_convex_shape_for_contact(body_b.shape, normal_b_local, requested_scale)
        axial_scale = max(
            trial_a.deformation.axial_scale if trial_a.deformation is not None else 1.0,
            trial_b.deformation.axial_scale if trial_b.deformation is not None else 1.0,
        )
        deformed_a = deform_convex_shape_for_contact(body_a.shape, normal_a_local, axial_scale)
        deformed_b = deform_convex_shape_for_contact(body_b.shape, normal_b_local, axial_scale)
        if axial_scale > requested_scale + 1.0e-10:
            cap_status = "surface_cap_reached_remaining_overlap_requires_position_resolution"
            assert deformed_a.deformation is not None and deformed_b.deformation is not None
            deformed_a = replace(
                deformed_a,
                deformation=replace(
                    deformed_a.deformation,
                    requested_axial_scale=requested_scale,
                    status=cap_status,
                ),
            )
            deformed_b = replace(
                deformed_b,
                deformation=replace(
                    deformed_b.deformation,
                    requested_axial_scale=requested_scale,
                    status=cap_status,
                ),
            )
            _validate_shape(deformed_a)
            _validate_shape(deformed_b)
        remaining_overlap = max(0.0, (axial_scale - requested_scale) * total_support)
        shift = remaining_overlap / 2.0
        resolved[index_a] = replace(
            body_a,
            center_um=_sub(body_a.center_um, _scale(normal_world, shift)),
            shape=deformed_a,
            geometry_evidence="kinematic_volume_preserving_contact_surface_cross_system_area_cap",
            source_ids=tuple(dict.fromkeys((*body_a.source_ids, *mechanics_sources))),
        )
        resolved[index_b] = replace(
            body_b,
            center_um=_add(body_b.center_um, _scale(normal_world, shift)),
            shape=deformed_b,
            geometry_evidence="kinematic_volume_preserving_contact_surface_cross_system_area_cap",
            source_ids=tuple(dict.fromkeys((*body_b.source_ids, *mechanics_sources))),
        )

    return tuple(resolved)


def initialize_spatial_world(
    bodies: tuple[SpatialBody, ...],
    *,
    world_id: str = "spatial_world",
    scenario_kind: str = "unspecified",
    time_s: float = 0.0,
    evidence_status: str = "runtime_geometry_not_biological_observation",
) -> SpatialWorldState:
    if not isfinite(time_s) or time_s < 0.0:
        raise ValueError("time_s must be non-negative")
    ids = [body.id for body in bodies]
    if len(ids) != len(set(ids)):
        raise ValueError("spatial body ids must be unique")
    for body in bodies:
        _validate_body(body)
    resolved_bodies = resolve_deformable_contact_surfaces(bodies)
    relations = tuple(compute_pair_relation(a, b, world_time_s=time_s) for a, b in combinations(resolved_bodies, 2))
    source_ids = tuple(dict.fromkeys(source for body in resolved_bodies for source in body.source_ids))
    return SpatialWorldState(
        version="geometry_authoritative_deformable_spatial_world_v3",
        id=world_id,
        scenario_kind=scenario_kind,
        time_s=time_s,
        length_unit="um",
        bodies=resolved_bodies,
        pair_relations=relations,
        geometry_authority="authoritative_for_runtime_surface_geometry_and_contact_events",
        contact_event_semantics=(
            "enter_or_stay_sets_geometric_input_on; exit_sets_input_off; downstream persistence belongs_to_pathway_model"
        ),
        surface_deformation_model="volume_preserving_affine_contact_v1",
        conservative_elastic_area_strain_cap=CONSERVATIVE_ELASTIC_AREA_STRAIN_CAP,
        surface_deformation_scope=(
            "isolated_equal-topology_convex_hepatocyte_pair; kinematic geometry only; no force, stiffness, or time law"
        ),
        evidence_status=evidence_status,
        geometry_drives_runtime_state=True,
        quantitative_biological_effects_enabled=False,
        source_ids=source_ids,
        limitations=(
            "Convex-polyhedron patches are runtime geometry, not reconstructed donor tissue morphometry.",
            "Contact event state is causal; elapsed contact duration is not computed as a biological parameter.",
            "The 1% elastic-area cap is an engineering safety bound derived from half the lower human-RBC lysis strain, not a PHH measurement.",
            "Affine deformation currently resolves one isolated equal-topology hepatocyte pair; multi-neighbour and mixed-material mechanics remain blocked.",
            "Force, adhesion, junction gating and downstream kinetics remain blocked without matched evidence.",
        ),
    )


def step_spatial_world(
    world: SpatialWorldState,
    dt_s: float,
    *,
    bodies: tuple[SpatialBody, ...] | None = None,
) -> SpatialWorldState:
    if not isfinite(dt_s) or dt_s <= 0.0:
        raise ValueError("dt_s must be positive")
    requested_bodies = bodies if bodies is not None else world.bodies
    next_bodies = resolve_deformable_contact_surfaces(requested_bodies)
    ids = [body.id for body in next_bodies]
    if len(ids) != len(set(ids)):
        raise ValueError("spatial body ids must be unique")
    previous = {relation.id: relation for relation in world.pair_relations}
    next_time = world.time_s + dt_s
    relations = tuple(
        compute_pair_relation(
            a,
            b,
            world_time_s=next_time,
            previous=previous.get("__".join(sorted((a.id, b.id)))),
        )
        for a, b in combinations(next_bodies, 2)
    )
    source_ids = tuple(dict.fromkeys(source for body in next_bodies for source in body.source_ids))
    return replace(world, time_s=next_time, bodies=next_bodies, pair_relations=relations, source_ids=source_ids)


def move_body(
    body: SpatialBody,
    center_um: Vector3,
    *,
    velocity_um_s: Vector3 | None = None,
    orientation_xyzw: Quaternion | None = None,
) -> SpatialBody:
    moved = replace(
        body,
        center_um=center_um,
        velocity_um_s=body.velocity_um_s if velocity_um_s is None else velocity_um_s,
        orientation_xyzw=body.orientation_xyzw if orientation_xyzw is None else orientation_xyzw,
    )
    _validate_body(moved)
    return moved


def sample_isotropic_approach_direction(rng: EngineRng) -> Vector3:
    """Sample an incoming direction uniformly over solid angle.

    This optional sampler is suitable for an explicitly isotropic diagnostic
    environment. Tissue, sinusoidal-flow, chemotactic, or attachment-biased
    scenarios must supply their own trajectories instead of using this helper.
    """

    z = 2.0 * rng.random() - 1.0
    azimuth = 2.0 * pi * rng.random()
    radial = sqrt(max(0.0, 1.0 - z * z))
    return (radial * cos(azimuth), radial * sin(azimuth), z)


def body_support_distance_um(body: SpatialBody, outward_direction: Vector3) -> float:
    """Return the body's directional extent from its declared center in um."""

    direction, offset = _body_support_offset_um(body, outward_direction)
    return _dot(offset, direction)


def _body_support_offset_um(body: SpatialBody, outward_direction: Vector3) -> tuple[Vector3, Vector3]:
    """Return a normalized direction and its support-point center offset."""

    _validate_body(body)
    if any(not isfinite(component) for component in outward_direction):
        raise ValueError("support direction must be finite")
    length = _norm(outward_direction)
    if length <= NUMERIC_AXIS_TOLERANCE:
        raise ValueError("support direction must be non-zero")
    direction = _scale(outward_direction, 1.0 / length)
    if isinstance(body.shape, SphereShape):
        return direction, _scale(direction, body.shape.radius_um)
    if isinstance(body.shape, CapsuleShape):
        axis_world = _unit(_rotate(body.shape.axis, body.orientation_xyzw))
        endpoint_sign = 1.0 if _dot(axis_world, direction) >= 0.0 else -1.0
        endpoint = _scale(axis_world, endpoint_sign * body.shape.half_segment_length_um)
        return direction, _add(endpoint, _scale(direction, body.shape.radius_um))
    offsets = tuple(_rotate(vertex, body.orientation_xyzw) for vertex in body.shape.vertices_local_um)
    maximum = max(_dot(offset, direction) for offset in offsets)
    support_offsets = tuple(
        offset
        for offset in offsets
        if maximum - _dot(offset, direction) <= NUMERIC_AXIS_TOLERANCE
    )
    return direction, _mean(support_offsets)


def place_external_body_at_surface_gap(
    primary: SpatialBody,
    external: SpatialBody,
    outward_direction: Vector3,
    *,
    surface_gap_um: float = 0.0,
) -> SpatialBody:
    """Place a supplied external body at a requested directional surface gap.

    The placement uses support distances from both declared collision shapes, so
    a virus, bacterium, capsule, or cell changes the center position according to
    its own dimensions. A missing or invalid size fails validation; the engine
    never substitutes a generic contact radius.
    """

    if primary.id == external.id:
        raise ValueError("external contact body must have a distinct id")
    if not isfinite(surface_gap_um) or surface_gap_um < 0.0:
        raise ValueError("surface_gap_um must be finite and non-negative")
    if any(not isfinite(component) for component in outward_direction):
        raise ValueError("approach direction must be finite")
    length = _norm(outward_direction)
    if length <= NUMERIC_AXIS_TOLERANCE:
        raise ValueError("approach direction must be non-zero")
    direction = _scale(outward_direction, 1.0 / length)
    _, primary_support = _body_support_offset_um(primary, direction)
    _, external_support = _body_support_offset_um(external, _scale(direction, -1.0))
    contact_point = _add(primary.center_um, primary_support)
    center = _add(_sub(contact_point, external_support), _scale(direction, surface_gap_um))
    return move_body(external, center)


def place_external_body_at_isotropic_approach(
    primary: SpatialBody,
    external: SpatialBody,
    *,
    random_seed: int,
    surface_gap_um: float = 0.0,
) -> ContactApproachPlacement:
    """Place one explicit body using a reproducible isotropic approach draw."""

    if isinstance(random_seed, bool) or not isinstance(random_seed, int):
        raise ValueError("random_seed must be an integer")
    direction = sample_isotropic_approach_direction(EngineRng(random_seed))
    placed = place_external_body_at_surface_gap(
        primary,
        external,
        direction,
        surface_gap_um=surface_gap_um,
    )
    return ContactApproachPlacement(
        body=placed,
        outward_direction=direction,
        requested_surface_gap_um=surface_gap_um,
        random_seed=random_seed,
    )


def validate_spatial_world(world: SpatialWorldState) -> None:
    """Fail closed if serialized geometry diverges from the body definitions."""

    if world.version != "geometry_authoritative_deformable_spatial_world_v3":
        raise ValueError("unexpected spatial-world version")
    if world.length_unit != "um":
        raise ValueError("spatial-world length unit must be um")
    if not isfinite(world.time_s) or world.time_s < 0.0:
        raise ValueError("spatial-world time must be finite and non-negative")
    if not world.geometry_drives_runtime_state:
        raise ValueError("spatial-world geometry must drive runtime spatial state")
    if world.quantitative_biological_effects_enabled:
        raise ValueError("spatial geometry cannot enable unvalidated biological effects")
    if world.surface_deformation_model != "volume_preserving_affine_contact_v1":
        raise ValueError("unexpected surface-deformation model")
    if abs(world.conservative_elastic_area_strain_cap - CONSERVATIVE_ELASTIC_AREA_STRAIN_CAP) > 1.0e-12:
        raise ValueError("surface-deformation area cap is inconsistent")

    body_by_id = {body.id: body for body in world.bodies}
    if len(body_by_id) != len(world.bodies):
        raise ValueError("spatial body ids must be unique")
    for body in world.bodies:
        _validate_body(body)
    expected_relations = {
        "__".join(sorted((a.id, b.id))): compute_pair_relation(a, b, world_time_s=world.time_s)
        for a, b in combinations(world.bodies, 2)
    }
    actual_relations = {relation.id: relation for relation in world.pair_relations}
    if len(actual_relations) != len(world.pair_relations) or actual_relations.keys() != expected_relations.keys():
        raise ValueError("spatial pair relations must cover every body pair exactly once")
    for relation_id, relation in actual_relations.items():
        expected = expected_relations[relation_id]
        if relation.body_a not in body_by_id or relation.body_b not in body_by_id:
            raise ValueError(f"{relation_id} references an unknown body")
        if relation.world_time_s != world.time_s:
            raise ValueError(f"{relation_id} world time is inconsistent")
        for field_name in ("center_distance_um", "surface_gap_um", "overlap_depth_um", "relative_normal_velocity_um_s"):
            actual_value = getattr(relation, field_name)
            expected_value = getattr(expected, field_name)
            if not isfinite(actual_value) or abs(actual_value - expected_value) > NUMERIC_CONTACT_TOLERANCE_UM:
                raise ValueError(f"{relation_id}.{field_name} diverges from authoritative body geometry")
        for field_name in ("closest_point_a_um", "closest_point_b_um", "normal_a_to_b"):
            actual_vector = getattr(relation, field_name)
            expected_vector = getattr(expected, field_name)
            if any(abs(actual - target) > NUMERIC_CONTACT_TOLERANCE_UM for actual, target in zip(actual_vector, expected_vector, strict=True)):
                raise ValueError(f"{relation_id}.{field_name} diverges from authoritative body geometry")
        if relation.relation != expected.relation or relation.geometric_contact != expected.geometric_contact:
            raise ValueError(f"{relation_id} contact classification diverges from authoritative body geometry")
        for field_name in (
            "contact_face_a_id",
            "contact_face_b_id",
            "contact_face_candidates_a",
            "contact_face_candidates_b",
            "membrane_domain_a",
            "membrane_domain_b",
            "membrane_domain_candidates_a",
            "membrane_domain_candidates_b",
            "domain_assignment_status_a",
            "domain_assignment_status_b",
        ):
            if getattr(relation, field_name) != getattr(expected, field_name):
                raise ValueError(f"{relation_id}.{field_name} diverges from authoritative surface geometry")
        if relation.contact_input_active != relation.geometric_contact:
            raise ValueError(f"{relation_id} contact input must mirror current geometry")
        valid_event = relation.contact_event in (("enter", "stay") if relation.geometric_contact else ("none", "exit"))
        if not valid_event:
            raise ValueError(f"{relation_id} has an invalid contact event transition")
        if relation.contact_patch_area_um2 != expected.contact_patch_area_um2:
            raise ValueError(f"{relation_id} contact patch area diverges from surface geometry")
        if relation.contact_patch_polygon_um != expected.contact_patch_polygon_um:
            raise ValueError(f"{relation_id} contact patch polygon diverges from surface geometry")
        if relation.normal_load_nN is not None or relation.quantitative_biological_effects_enabled:
            raise ValueError(f"{relation_id} exceeds the validated mechanics/biology boundary")
    source_ids = tuple(dict.fromkeys(source for body in world.bodies for source in body.source_ids))
    if world.source_ids != source_ids:
        raise ValueError("spatial-world source ids must be the ordered union of body source ids")


def cell_spatial_state_from_world(world: SpatialWorldState, body_id: str) -> CellSpatialState:
    body_by_id = {body.id: body for body in world.bodies}
    if body_id not in body_by_id:
        raise ValueError(f"unknown spatial body: {body_id}")
    body = body_by_id[body_id]
    related = [relation for relation in world.pair_relations if relation.body_a == body_id or relation.body_b == body_id]
    nearest = min(related, key=lambda relation: relation.surface_gap_um, default=None)
    contacts: list[CellSpatialContactState] = []
    events: list[CellSpatialContactEvent] = []
    for relation in related:
        is_a = relation.body_a == body_id
        other_id = relation.body_b if is_a else relation.body_a
        domain_self = relation.membrane_domain_a if is_a else relation.membrane_domain_b
        domain_other = relation.membrane_domain_b if is_a else relation.membrane_domain_a
        face_candidates_self = relation.contact_face_candidates_a if is_a else relation.contact_face_candidates_b
        face_candidates_other = relation.contact_face_candidates_b if is_a else relation.contact_face_candidates_a
        domain_candidates_self = relation.membrane_domain_candidates_a if is_a else relation.membrane_domain_candidates_b
        domain_candidates_other = relation.membrane_domain_candidates_b if is_a else relation.membrane_domain_candidates_a
        domain_status_self = relation.domain_assignment_status_a if is_a else relation.domain_assignment_status_b
        domain_status_other = relation.domain_assignment_status_b if is_a else relation.domain_assignment_status_a
        if relation.contact_event != "none":
            events.append(CellSpatialContactEvent(
                other_body_id=other_id,
                event=relation.contact_event,
                t_s=relation.world_time_s,
                contact_input_active=relation.contact_input_active,
                membrane_domain_self=domain_self,
                membrane_domain_other=domain_other,
                membrane_domain_candidates_self=domain_candidates_self,
                membrane_domain_candidates_other=domain_candidates_other,
                domain_assignment_status_self=domain_status_self,
                domain_assignment_status_other=domain_status_other,
            ))
        if not relation.geometric_contact:
            continue
        contacts.append(CellSpatialContactState(
            other_body_id=other_id,
            other_biological_kind=body_by_id[other_id].biological_kind,
            relation=relation.relation,
            contact_event=relation.contact_event,
            contact_input_active=relation.contact_input_active,
            surface_gap_um=relation.surface_gap_um,
            overlap_depth_um=relation.overlap_depth_um,
            closest_point_self_um=relation.closest_point_a_um if is_a else relation.closest_point_b_um,
            closest_point_other_um=relation.closest_point_b_um if is_a else relation.closest_point_a_um,
            outward_normal_to_other=relation.normal_a_to_b if is_a else _scale(relation.normal_a_to_b, -1.0),
            contact_face_candidates_self=face_candidates_self,
            contact_face_candidates_other=face_candidates_other,
            membrane_domain_self=domain_self,
            membrane_domain_other=domain_other,
            membrane_domain_candidates_self=domain_candidates_self,
            membrane_domain_candidates_other=domain_candidates_other,
            domain_assignment_status_self=domain_status_self,
            domain_assignment_status_other=domain_status_other,
            contact_patch_polygon_um=relation.contact_patch_polygon_um,
            contact_patch_area_um2=relation.contact_patch_area_um2,
            normal_load_nN=relation.normal_load_nN,
            quantitative_effect_enabled=relation.quantitative_biological_effects_enabled,
            blockers=relation.blockers,
        ))
    patch_available = any(contact.contact_patch_area_um2 is not None for contact in contacts)
    return CellSpatialState(
        world_id=world.id,
        body_id=body_id,
        world_time_s=world.time_s,
        center_um=body.center_um,
        collision_shape=body.shape.kind,
        nearest_body_id=nearest.body_b if nearest and nearest.body_a == body_id else nearest.body_a if nearest else None,
        nearest_surface_gap_um=nearest.surface_gap_um if nearest else None,
        active_contact_count=len(contacts),
        maximum_overlap_depth_um=max((contact.overlap_depth_um for contact in contacts), default=0.0),
        contacts=tuple(contacts),
        contact_events=tuple(events),
        geometry_coupling_status="active_authoritative_surface_geometry_and_contact_events",
        mechanical_coupling_status=(
            "contact_patch_geometry_available_material_law_blocked" if patch_available
            else "blocked_missing_resolved_patch_or_material_law"
        ),
        biochemical_coupling_status="blocked_missing_validated_junction_or_receptor_law",
        geometry_drives_runtime_state=True,
        quantitative_biological_effects_enabled=False,
        source_ids=body.source_ids,
        limitations=world.limitations,
    )


def apply_spatial_world_to_cell(state: CellState, world: SpatialWorldState, body_id: str) -> CellState:
    """Attach geometry-derived state without altering biochemical pools."""

    return replace(state, spatial_state=cell_spatial_state_from_world(world, body_id))


def _ordered_face_indices(vertices: tuple[Vector3, ...], indices: list[int], normal: Vector3) -> tuple[int, ...]:
    center = _mean([vertices[index] for index in indices])
    reference = (1.0, 0.0, 0.0) if abs(normal[0]) < 0.8 else (0.0, 1.0, 0.0)
    basis_u = _unit(_cross(normal, reference))
    basis_v = _unit(_cross(normal, basis_u))
    ordered = sorted(
        indices,
        key=lambda index: atan2(
            _dot(_sub(vertices[index], center), basis_v),
            _dot(_sub(vertices[index], center), basis_u),
        ),
    )
    trial = ConvexFace("trial", tuple(ordered), "unknown", "mathematical")
    if _dot(_face_normal(vertices, trial), normal) < 0.0:
        ordered.reverse()
    return tuple(ordered)


def build_canonical_hepatocyte_shape(
    *, equivalent_sphere_diameter_um: float = HEPATOCYTE_REFERENCE_EQUIVALENT_SPHERE_DIAMETER_UM,
) -> ConvexPolyhedronShape:
    """Return a volume-equivalent regular truncated-octahedron proxy.

    The truncated octahedron is a parameter-free, space-filling mathematical
    proxy once scale is chosen. It is not asserted to be a reconstructed human
    hepatocyte. The measured in-situ midlobular human hepatocyte volume sets
    the equivalent-sphere scale; the resulting diameter is derived.
    """

    if not isfinite(equivalent_sphere_diameter_um) or equivalent_sphere_diameter_um <= 0.0:
        raise ValueError("equivalent_sphere_diameter_um must be positive")
    radius = equivalent_sphere_diameter_um / 2.0
    sphere_volume = (4.0 / 3.0) * pi * radius**3
    scale = (sphere_volume / 32.0) ** (1.0 / 3.0)
    raw_vertices: set[Vector3] = set()
    for values in set(permutations((0.0, 1.0, 2.0))):
        nonzero = [index for index, value in enumerate(values) if value != 0.0]
        for signs in product((-1.0, 1.0), repeat=len(nonzero)):
            vertex = list(values)
            for index, sign in zip(nonzero, signs, strict=True):
                vertex[index] *= sign
            raw_vertices.add((vertex[0] * scale, vertex[1] * scale, vertex[2] * scale))
    vertices = tuple(sorted(raw_vertices))
    constraints: list[tuple[str, Vector3, float, MembraneDomain]] = [
        (
            "sinusoidal_neg_x",
            HEPATOCYTE_CANONICAL_SINUSOIDAL_DIRECTION,
            2.0 * scale,
            "basolateral",
        ),
        (
            "canalicular_pos_x",
            HEPATOCYTE_CANONICAL_CANALICULAR_DIRECTION,
            2.0 * scale,
            "apical",
        ),
        ("lateral_neg_y", (0.0, -1.0, 0.0), 2.0 * scale, "lateral"),
        ("lateral_pos_y", (0.0, 1.0, 0.0), 2.0 * scale, "lateral"),
        ("lateral_neg_z", (0.0, 0.0, -1.0), 2.0 * scale, "lateral"),
        ("lateral_pos_z", (0.0, 0.0, 1.0), 2.0 * scale, "lateral"),
    ]
    for sx, sy, sz in product((-1.0, 1.0), repeat=3):
        label = "".join("p" if value > 0.0 else "n" for value in (sx, sy, sz))
        constraints.append((f"lateral_hex_{label}", (sx, sy, sz), 3.0 * scale, "lateral"))
    faces: list[ConvexFace] = []
    for face_id, raw_normal, offset, domain in constraints:
        normal = _unit(raw_normal)
        plane_offset = offset / _norm(raw_normal)
        indices = [
            index for index, vertex in enumerate(vertices)
            if abs(_dot(vertex, normal) - plane_offset) <= NUMERIC_CONTACT_TOLERANCE_UM
        ]
        faces.append(ConvexFace(
            id=face_id,
            vertex_indices=_ordered_face_indices(vertices, indices, normal),
            membrane_domain=domain,
            topology_evidence="canonical_space_filling_proxy_not_observed_face_morphometry",
        ))
    shape = ConvexPolyhedronShape(
        vertices_local_um=vertices,
        faces=tuple(faces),
        equivalent_sphere_radius_um=radius,
        geometry_status="volume_equivalent_regular_truncated_octahedron_proxy_not_observed_cell_shape",
    )
    _validate_shape(shape)
    return shape


def _primary_hepatocyte_body() -> SpatialBody:
    membrane_material = build_intrinsic_hepatocyte_membrane_profile()
    source_ids = tuple(dict.fromkeys((
        "duarte1989_human_hepatocyte_volume",
        "olander2021_human_hepatocyte_size",
        "fabyan2026_human_liver_3d",
        *membrane_material.source_ids,
        "singer_nicolson1972_fluid_mosaic",
        "helfrich1973_bilayer_curvature",
        "guillou2016_membrane_surface_reservoirs",
    )))
    return SpatialBody(
        id="hepatocyte_primary",
        biological_kind="hepatocyte",
        center_um=(0.0, 0.0, 0.0),
        shape=build_canonical_hepatocyte_shape(),
        state_ref="adult_human_hepatocyte",
        geometry_evidence="measured_in_situ_human_volume_equivalent_canonical_polyhedral_proxy",
        visual_profile="source_backed_hepatocyte_cutaway_polyhedral",
        molecular_profile_id="adult_human_hepatocyte_surface_v1",
        membrane_material=membrane_material,
        source_ids=source_ids,
    )


def build_single_hepatocyte_world(*, time_s: float = 0.0) -> SpatialWorldState:
    """Normal production scenario: one hepatocyte and no invented neighbour."""

    return initialize_spatial_world(
        (_primary_hepatocyte_body(),),
        world_id="single_hepatocyte_runtime",
        scenario_kind="single_hepatocyte",
        time_s=time_s,
        evidence_status="measured_in_situ_human_volume_canonical_polyhedral_proxy_no_external_body",
    )


def build_hepatocyte_contact_diagnostic_world(*, time_s: float = 0.0) -> SpatialWorldState:
    """Two-cell deformation-at-cap fixture for geometry tests only."""

    primary = _primary_hepatocyte_body()
    assert isinstance(primary.shape, ConvexPolyhedronShape)
    normal = (0.0, 1.0, 0.0)
    axial_scale = _minimum_axial_scale_for_area_cap(
        primary.shape,
        normal,
        CONSERVATIVE_ELASTIC_AREA_STRAIN_CAP,
    )
    support = _support_from_center(primary.shape, normal)
    neighbor = replace(
        primary,
        id="hepatocyte_neighbor",
        # Rest surfaces overlap by exactly the amount that the symmetric,
        # volume-preserving deformation can resolve at the conservative area cap.
        center_um=(0.0, 2.0 * support * axial_scale, 0.0),
        state_ref="adult_human_hepatocyte_neighbor_geometry_only",
        geometry_evidence="canonical_polyhedral_contact_deformation_diagnostic_not_observed_arrangement",
    )
    return initialize_spatial_world(
        (primary, neighbor),
        world_id="hepatocyte_broad_face_contact_diagnostic",
        scenario_kind="geometry_diagnostic_pair_contact",
        time_s=time_s,
        evidence_status="measured_size_deformable_polyhedral_contact_fixture_not_tissue_observation",
    )


def build_hbv_contact_diagnostic_world(*, time_s: float = 0.0) -> SpatialWorldState:
    """Exact-scale tangent HBV fixture for molecular-gate tests only.

    The virion is present because this explicit diagnostic requests it. The
    normal production world remains a single hepatocyte. Tangency opens only
    the geometry gate; receptor binding and entry remain independently gated.
    """

    primary = _primary_hepatocyte_body()
    assert isinstance(primary.shape, ConvexPolyhedronShape)
    outward = (-1.0, 0.0, 0.0)
    support = _support_from_center(primary.shape, outward)
    radius_um = HBV_CRYO_EM_OUTER_DIAMETER_UM / 2.0
    virion = SpatialBody(
        id="hbv_virion_reference",
        biological_kind="virus",
        center_um=(-(support + radius_um), 0.0, 0.0),
        shape=SphereShape(radius_um=radius_um),
        state_ref="complete_hbv_virion_geometry_diagnostic",
        geometry_evidence="human_serum_hbv_cryo_em_outer_diameter_tangent_fixture",
        visual_profile="exact_scale_hbv_virion",
        molecular_profile_id="hbv_virion_surface_v1",
        source_ids=("seitz2007_hbv_cryo_em",),
    )
    return initialize_spatial_world(
        (primary, virion),
        world_id="hepatocyte_hbv_contact_diagnostic",
        scenario_kind="geometry_molecular_gate_diagnostic_hbv",
        time_s=time_s,
        evidence_status="exact_scale_hbv_tangent_fixture_not_infection_observation",
    )


def build_reference_hepatocyte_pair_world(*, time_s: float = 0.0) -> SpatialWorldState:
    """Backward-compatible alias for the explicit diagnostic pair fixture."""

    return build_hepatocyte_contact_diagnostic_world(time_s=time_s)


def spatial_world_snapshot(world: SpatialWorldState | None = None) -> dict[str, object]:
    return (world or build_single_hepatocyte_world()).to_dict()
