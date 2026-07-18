"""Executable scope ledger for physical geometry and membrane contracts.

The percentages here measure explicit verification-criterion coverage. They are
not biological realism, donor agreement, or predictive accuracy. Missing
healthy-human calibration remains visible and keeps predictive accuracy null.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain
from cell_engine.multicell.spatial_world import SPATIAL_WORLD_SOURCES


VerificationStatus = Literal["verified", "blocked"]


PHYSICAL_VALIDATION_SOURCES: dict[str, SourceReference] = {
    source_id: SPATIAL_WORLD_SOURCES[source_id]
    for source_id in (
        "segovia_miranda2019_human_liver_3d_morphometry",
        "duarte1989_human_hepatocyte_volume",
        "olander2021_human_hepatocyte_size",
        "fabyan2026_human_liver_3d",
        "singer_nicolson1972_fluid_mosaic",
        "helfrich1973_bilayer_curvature",
        "evans1976_human_membrane_area_lysis",
        "rawicz2000_bilayer_elasticity",
        "guillou2016_membrane_surface_reservoirs",
        "mitra2004_rat_hepatocyte_bilayer_thickness",
    )
}


@dataclass(frozen=True)
class PhysicalVerificationCriterion:
    id: str
    description: str
    status: VerificationStatus
    evidence_scope: str
    verification_contract: str
    source_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class PhysicalVerificationLayer:
    id: Literal["scale_geometry", "membrane_physics", "contact_domain"]
    title: str
    verified_count: int
    criterion_count: int
    verification_coverage_pct: float
    predictive_accuracy_pct: float | None
    human_calibration_status: str
    criteria: tuple[PhysicalVerificationCriterion, ...]
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class PhysicalValidationReport:
    version: Literal["physical_integrity_verification_v1"]
    score_semantics: str
    layers: tuple[PhysicalVerificationLayer, ...]
    source_ids: tuple[str, ...]


def _criterion(
    id: str,
    description: str,
    verification_contract: str,
    *,
    evidence_scope: str = "mathematical_or_runtime_contract",
    source_ids: tuple[str, ...] = (),
    status: VerificationStatus = "verified",
) -> PhysicalVerificationCriterion:
    return PhysicalVerificationCriterion(
        id=id,
        description=description,
        status=status,
        evidence_scope=evidence_scope,
        verification_contract=verification_contract,
        source_ids=source_ids,
    )


def _layer(
    id: Literal["scale_geometry", "membrane_physics", "contact_domain"],
    title: str,
    criteria: tuple[PhysicalVerificationCriterion, ...],
    human_calibration_status: str,
    blockers: tuple[str, ...],
) -> PhysicalVerificationLayer:
    verified_count = sum(criterion.status == "verified" for criterion in criteria)
    criterion_count = len(criteria)
    coverage = 100.0 * verified_count / criterion_count if criterion_count else 0.0
    return PhysicalVerificationLayer(
        id=id,
        title=title,
        verified_count=verified_count,
        criterion_count=criterion_count,
        verification_coverage_pct=coverage,
        predictive_accuracy_pct=None,
        human_calibration_status=human_calibration_status,
        criteria=criteria,
        blockers=blockers,
    )


def build_physical_validation_report() -> PhysicalValidationReport:
    scale = _layer(
        "scale_geometry",
        "Scale and base geometry",
        (
            _criterion("length-unit", "Runtime length unit is micrometre", "SpatialWorldState.length_unit guard"),
            _criterion("volume-unit", "One cubic micrometre converts to 1e-15 litre", "geometry conversion unit test"),
            _criterion("phh-in-situ-volume", "Normal-control human hepatocyte 3D median volume is 5657.07116 um3", "checksummed source bundle, single imported constant and mirror tests", evidence_scope="measured_3d_normal_control_human_hepatocyte", source_ids=("segovia_miranda2019_human_liver_3d_morphometry",)),
            _criterion("phh-isolated-cross-check", "Independent isolated-PHH median 18.4 um and 12-26 um interval are retained", "scale registry test", evidence_scope="measured_isolated_human_phh", source_ids=("olander2021_human_hepatocyte_size",)),
            _criterion("sample-context", "Five-reconstruction 3D, five-case stereology and 54-batch isolated contexts remain separate", "provenance snapshot contract", evidence_scope="measured_human_context_separation", source_ids=("segovia_miranda2019_human_liver_3d_morphometry", "duarte1989_human_hepatocyte_volume", "olander2021_human_hepatocyte_size")),
            _criterion("derived-radius", "Equivalent-sphere radius is derived from measured in-situ volume", "analytic geometry test"),
            _criterion("derived-volume", "Equivalent diameter reproduces 5657.07116 um3 exactly", "analytic inverse-geometry test"),
            _criterion("derived-area", "Equivalent-sphere area is pi*d^2", "analytic geometry test"),
            _criterion("definition-scale", "Cell definition consumes the shared PHH scale", "cross-module equality test"),
            _criterion("quantitative-scale", "Concentration-count geometry consumes the shared volume", "quantitative geometry test"),
            _criterion("rdme-scale", "Default RDME lattice consumes the shared diameter", "RDME lattice test"),
            _criterion("renderer-scale", "Renderer radius consumes the shared in-situ volume-equivalent scale", "TypeScript scale test"),
            _criterion("public-mirror", "Public quantitative inventory mirrors engine diameter and volume", "JSON mirror test"),
            _criterion("proxy-volume", "Canonical polyhedron is volume-equivalent to the reference sphere", "polyhedron volume test"),
            _criterion("closed-manifold", "Canonical boundary is a closed two-manifold", "runtime edge-incidence guard"),
            _criterion("convexity", "Every canonical vertex lies inside every outward face plane", "runtime convexity guard"),
            _criterion("finite-pose", "Positions and unit quaternions are finite and normalized", "runtime body validation"),
            _criterion("transform-invariance", "Rigid rotation and body-order swaps preserve signed geometry", "spatial symmetry tests"),
            _criterion("serialization-integrity", "Serialized pair geometry is recomputed and compared", "validate_spatial_world guard"),
            _criterion("donor-in-situ-mesh", "Donor-resolved in-situ PHH boundary mesh validation", "blocked pending matched healthy-human 3D cell-boundary data", evidence_scope="healthy_human_in_situ_required", source_ids=("fabyan2026_human_liver_3d",), status="blocked"),
        ),
        "partial_isolated_human_scale_no_donor_resolved_in_situ_shape",
        ("Matched donor-resolved healthy-human hepatocyte boundary meshes are unavailable.",),
    )
    membrane = _layer(
        "membrane_physics",
        "Membrane numerical and evidence integrity",
        (
            _criterion("fluid-mosaic", "Bilayer architecture is a fluid lipid-protein mosaic", "source-scoped architecture contract", evidence_scope="general_membrane_architecture", source_ids=("singer_nicolson1972_fluid_mosaic",)),
            _criterion("curvature-model", "Bending is represented separately from direct area stretch", "Helfrich topology contract", evidence_scope="general_bilayer_theory", source_ids=("helfrich1973_bilayer_curvature",)),
            _criterion("closed-mesh", "Membrane surface remains closed", "two-manifold runtime guard"),
            _criterion("finite-area", "Triangulated surface area remains finite and positive", "mesh area guard"),
            _criterion("finite-volume", "Enclosed mesh volume remains finite and positive", "mesh volume guard"),
            _criterion("orientation", "Face winding remains outward without inverted surface elements", "convex face guard"),
            _criterion("volume-preserving-map", "Contact affine map has unit determinant", "axial/tangential scale identity test"),
            _criterion("volume-ratio", "Contact deformation preserves volume to numerical tolerance", "runtime ratio guard"),
            _criterion("area-ratio", "Area strain is computed from the actual deformed mesh", "mesh area-ratio test"),
            _criterion("engineering-cap", "A conservative 1% numerical cap is enforced", "deformation cap guard", evidence_scope="cross_cell_type_engineering_bound", source_ids=("evans1976_human_membrane_area_lysis", "rawicz2000_bilayer_elasticity")),
            _criterion("cap-disclosure", "The 1% cap is never labelled a PHH rupture threshold", "membrane profile fail-closed guard"),
            _criterion("restoration", "Contact exit deterministically restores rest topology", "contact lifecycle test"),
            _criterion("surface-advection", "Embedded tracers use barycentric surface advection", "TypeScript membrane test"),
            _criterion("no-macro-noise", "Uncalibrated thermal forcing cannot move the collision-scale cell surface", "renderer contract test"),
            _criterion("lateral-diffusion-gate", "Active lateral diffusion is disabled without PHH coefficients", "profile validation guard"),
            _criterion("phh-null-parameters", "Unknown PHH thickness, moduli, tension, viscosity and rupture strain remain null", "profile validation guard"),
            _criterion("cross-system-scope", "Model-bilayer and red-cell values cannot parameterize PHH", "reference transfer-gate test"),
            _criterion("domain-thickness-scope", "Rat apical/basolateral thickness is retained only as cross-species context", "reference measurement test", evidence_scope="rat_hepatocyte_cross_species", source_ids=("mitra2004_rat_hepatocyte_bilayer_thickness",)),
            _criterion("unresolved-modes", "Topology change, remeshing and membrane-reservoir exchange are explicitly listed unresolved", "profile completeness guard", evidence_scope="cross_cell_type_context", source_ids=("guillou2016_membrane_surface_reservoirs",)),
            _criterion("human-phh-mechanics", "Healthy-human PHH membrane/cortex mechanics calibration", "blocked pending matched PHH tension, bending, cortex, viscosity and failure measurements", evidence_scope="healthy_human_phh_required", status="blocked"),
        ),
        "blocked_missing_matched_healthy_adult_human_phh_mechanics",
        ("No complete healthy-adult-human-PHH membrane/cortex mechanical parameter set is available.",),
    )
    contact = _layer(
        "contact_domain",
        "Contact surface and membrane-domain detection",
        (
            _criterion("pair-identity", "Every unordered body pair has one stable relation id", "world pair-coverage guard"),
            _criterion("signed-gap", "Positive separation, zero tangency and negative overlap are distinguished", "sphere and polyhedron tests"),
            _criterion("sphere-pair", "Sphere-sphere closest geometry is supported", "analytic fixture test"),
            _criterion("capsule-pair", "Capsule-sphere and capsule-capsule geometry is supported", "finite-segment tests"),
            _criterion("poly-round", "Convex-polyhedron to sphere/capsule geometry is supported", "mixed-shape contact tests"),
            _criterion("poly-poly", "Convex-polyhedron overlap uses SAT face and edge axes", "broad-face fixture test"),
            _criterion("closest-points", "Closest point is reported on both surfaces", "analytic and symmetry tests"),
            _criterion("normal", "A-to-B unit normal is body-order antisymmetric", "body-order symmetry test"),
            _criterion("patch-polygon", "Coplanar broad-face contact returns a clipped convex polygon", "patch fixture test"),
            _criterion("patch-area", "Contact-patch area is computed in um2 from that polygon", "polygon area test"),
            _criterion("face-id", "Unique surface-face contact returns a face id", "face-centre test"),
            _criterion("face-candidates", "Shared edge/vertex contact returns every candidate face", "cross-domain edge test"),
            _criterion("domain-map", "Cell definition, engine and renderer use the same canonical +x apical/-x basolateral map", "definition, Python and TypeScript axis/domain tests"),
            _criterion("domain-ambiguity", "Cross-domain shared features return null domain and an ambiguity status", "fail-closed edge test"),
            _criterion("same-domain-feature", "Shared features within one domain remain domain-resolvable", "surface-feature resolver test"),
            _criterion("rotation", "Domain assignment follows local faces through quaternion rotation", "rotation test"),
            _criterion("order-symmetry", "Swapping body order swaps points and domains without changing gap", "mixed-shape symmetry test"),
            _criterion("event-lifecycle", "Contact enter/stay/exit follows current geometry", "lifecycle test"),
            _criterion("biological-gate", "Geometry alone cannot activate signal, transport, force or adhesion", "fail-closed communication tests"),
            _criterion("donor-contact-validation", "Contact patches validated against matched healthy-human cell interfaces", "blocked pending donor-resolved membrane and interface reconstructions", evidence_scope="healthy_human_in_situ_required", source_ids=("fabyan2026_human_liver_3d",), status="blocked"),
        ),
        "runtime_geometry_verified_no_donor_resolved_contact_ground_truth",
        ("No matched healthy-human cell-pair contact mesh and receptor-domain ground truth is available.",),
    )
    layers = (scale, membrane, contact)
    source_ids = tuple(dict.fromkeys(
        source_id
        for layer in layers
        for criterion in layer.criteria
        for source_id in criterion.source_ids
    ))
    return PhysicalValidationReport(
        version="physical_integrity_verification_v1",
        score_semantics=(
            "verification_coverage_pct is the fraction of explicit software/numerical/evidence-contract "
            "criteria marked verified; it is not biological realism or predictive accuracy. "
            "predictive_accuracy_pct remains null until matched healthy-human validation exists."
        ),
        layers=layers,
        source_ids=source_ids,
    )


def validate_physical_validation_report(report: PhysicalValidationReport) -> None:
    if report.version != "physical_integrity_verification_v1":
        raise ValueError("unexpected physical-validation version")
    if len(report.layers) != 3 or len({layer.id for layer in report.layers}) != 3:
        raise ValueError("physical validation requires exactly three unique layers")
    for layer in report.layers:
        if layer.criterion_count != len(layer.criteria) or layer.verified_count != sum(
            criterion.status == "verified" for criterion in layer.criteria
        ):
            raise ValueError(f"{layer.id} criterion counts are inconsistent")
        expected = 100.0 * layer.verified_count / layer.criterion_count
        if abs(layer.verification_coverage_pct - expected) > 1.0e-12:
            raise ValueError(f"{layer.id} verification coverage is inconsistent")
        if layer.predictive_accuracy_pct is not None:
            raise ValueError(f"{layer.id} predictive accuracy is not identifiable")
        if not layer.blockers or not any(criterion.status == "blocked" for criterion in layer.criteria):
            raise ValueError(f"{layer.id} must expose unresolved human-validation blockers")
        for criterion in layer.criteria:
            unknown_sources = set(criterion.source_ids) - PHYSICAL_VALIDATION_SOURCES.keys()
            if unknown_sources:
                raise ValueError(f"{criterion.id} references unknown sources: {sorted(unknown_sources)}")
    expected_sources = tuple(dict.fromkeys(
        source_id
        for layer in report.layers
        for criterion in layer.criteria
        for source_id in criterion.source_ids
    ))
    if report.source_ids != expected_sources:
        raise ValueError("physical validation source ids are inconsistent")


def physical_validation_snapshot() -> dict[str, object]:
    report = build_physical_validation_report()
    validate_physical_validation_report(report)
    return to_plain(report)
