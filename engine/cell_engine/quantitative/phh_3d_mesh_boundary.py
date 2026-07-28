"""Fail-closed intake and topology audit for donor-resolved PHH meshes.

The numerical renderer can consume a validated triangle boundary, but this
module keeps biological registration disabled until the mesh, imaging context,
registration, external self-intersection audit, grid convergence and
donor-disjoint validation all exist. Aggregate morphometry and renderer proxy
geometry never satisfy this contract.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "evidence_intake"
    / "phh_3d_mesh_boundary_contract.v1.json"
)
DEFAULT_MANIFEST_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "evidence_intake"
    / "incoming"
    / "phh_3d_mesh_boundary"
    / "latest"
    / "phh_3d_mesh_manifest.csv"
)
CONTRACT_SCHEMA_VERSION = "cell.phh-3d-mesh-boundary-contract.v1"
CANONICAL_MESH_SCHEMA_VERSION = "cell.triangle-mesh-boundary-artifact.v1"
INTAKE_VERSION = "phh_3d_mesh_boundary_intake_v1"
MESH_GATE_VERSION = "phh_3d_mesh_boundary_gate_v1"

_NULL_TOKEN = "null"
_ALLOWED_SPLIT_ROLES = frozenset(
    {"calibration", "internal_validation", "independent_heldout"}
)
_TARGET_STRUCTURE_IDS = (
    "cell_outer_membrane",
    "nuclear_envelope",
    "bile_canaliculus",
    "rough_er_cisternae",
    "rough_er_branches",
    "smooth_er_branches",
    "golgi_stacks",
    "lipid_droplets",
    "mitochondria",
    "peroxisomes",
    "lysosomes",
)


class PHHMeshBoundaryError(ValueError):
    """Raised when a mesh artifact or manifest violates the intake contract."""


@dataclass(frozen=True)
class TriangleMeshTopologyAudit:
    vertex_count: int
    triangle_count: int
    isolated_vertex_count: int
    degenerate_triangle_count: int
    boundary_edge_count: int
    non_manifold_edge_count: int
    inconsistent_winding_edge_count: int
    connected_component_count: int
    surface_area_um2: float
    signed_volume_um3: float
    enclosed_volume_um3: float
    topologically_watertight: bool
    consistently_oriented: bool
    single_connected_component: bool
    self_intersection_tested: bool
    self_intersecting_triangle_pair_count: int
    self_intersection_free: bool
    valid_closed_boundary: bool


@dataclass(frozen=True)
class PHHMeshManifestRecord:
    record_id: str
    donor_id: str
    source_study_id: str
    source_locator: str
    split_role: str
    species: str
    tissue_health_state: str
    liver_zone: str
    preparation_context: str
    fixation_and_processing: str
    imaging_modality: str
    voxel_size_x_um: float
    voxel_size_y_um: float
    voxel_size_z_um: float
    segmentation_method: str
    structure_id: str
    instance_id: str
    biological_replicate_id: str
    mesh_artifact_path: str
    mesh_artifact_sha256: str
    coordinate_unit: str
    coordinate_frame: str
    registration_transform_id: str
    registration_target: str
    topology_qc_status: str
    self_intersection_qc_status: str
    self_intersection_tool_version: str
    self_intersection_report_path: str
    self_intersection_report_sha256: str
    uncertainty_description: str
    manual_primary_source_review_status: str
    parent_structure_instance_id: str | None
    polarity_annotation_method: str | None
    membrane_domain_annotation_path: str | None
    membrane_domain_annotation_sha256: str | None
    contact_interface_annotation_path: str | None
    contact_interface_annotation_sha256: str | None
    paired_mechanics_record_id: str | None
    grid_convergence_report_path: str | None
    grid_convergence_report_sha256: str | None
    censoring_or_missingness: str | None


@dataclass(frozen=True)
class PHHMeshAssessment:
    record_id: str
    structure_id: str
    split_role: str
    topology: TriangleMeshTopologyAudit
    artifact_checksum_verified: bool
    repository_self_intersection_free: bool
    external_self_intersection_report_verified: bool
    grid_convergence_report_verified: bool
    structurally_ready: bool
    runtime_boundary_registration_allowed: bool
    mechanics_coupling_allowed: bool
    blockers: tuple[str, ...]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPOSITORY_ROOT.resolve()))
    except ValueError:
        return str(path)


def _artifact_path(raw: str, *, label: str) -> Path:
    value = raw.strip()
    if not value or value.lower() == _NULL_TOKEN:
        raise PHHMeshBoundaryError(f"{label} is required")
    path = Path(value)
    resolved = path.resolve() if path.is_absolute() else (REPOSITORY_ROOT / path).resolve()
    if not resolved.is_file():
        raise PHHMeshBoundaryError(f"{label} does not exist: {value}")
    return resolved


def _verify_artifact(raw_path: str, expected_sha256: str, *, label: str) -> Path:
    path = _artifact_path(raw_path, label=label)
    expected = expected_sha256.strip().lower()
    if len(expected) != 64 or any(character not in "0123456789abcdef" for character in expected):
        raise PHHMeshBoundaryError(f"{label} SHA-256 must contain 64 lowercase hex characters")
    if _sha256(path) != expected:
        raise PHHMeshBoundaryError(f"{label} SHA-256 mismatch")
    return path


def load_phh_3d_mesh_boundary_contract(
    path: Path = CONTRACT_PATH,
) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != CONTRACT_SCHEMA_VERSION:
        raise PHHMeshBoundaryError("unsupported PHH mesh-boundary contract schema")
    required = payload.get("required_columns")
    conditional = payload.get("conditional_columns")
    gate = payload.get("mesh_gate")
    policy = payload.get("policy")
    required_ids = tuple(
        str(item.get("id", "")) for item in required or () if isinstance(item, dict)
    )
    conditional_ids = tuple(
        str(item.get("id", "")) for item in conditional or () if isinstance(item, dict)
    )
    if (
        len(required_ids) != 31
        or len(set(required_ids)) != 31
        or len(conditional_ids) != 10
        or len(set(conditional_ids)) != 10
        or not all(required_ids + conditional_ids)
    ):
        raise PHHMeshBoundaryError("PHH mesh manifest field contract changed")
    if payload.get("canonical_mesh_artifact_schema") != CANONICAL_MESH_SCHEMA_VERSION:
        raise PHHMeshBoundaryError("canonical mesh artifact schema changed")
    if tuple(payload.get("target_structure_ids", ())) != _TARGET_STRUCTURE_IDS:
        raise PHHMeshBoundaryError("PHH mesh target structures changed")
    if set(payload.get("allowed_split_roles", ())) != _ALLOWED_SPLIT_ROLES:
        raise PHHMeshBoundaryError("PHH mesh split roles changed")
    if payload.get("canonical_null_token") != _NULL_TOKEN:
        raise PHHMeshBoundaryError("PHH mesh null policy changed")
    if not isinstance(gate, dict) or gate.get("version") != MESH_GATE_VERSION:
        raise PHHMeshBoundaryError("PHH mesh gate changed")
    required_true = {
        "finite_vertices_required",
        "valid_triangle_indices_required",
        "nondegenerate_triangles_required",
        "exactly_two_faces_per_edge_required",
        "consistent_half_edge_winding_required",
        "single_connected_component_required",
        "nonzero_enclosed_volume_required",
        "external_self_intersection_pass_required",
        "micrometre_coordinate_unit_required",
        "healthy_human_context_required",
        "frozen_registration_required",
        "grid_convergence_required_for_runtime_boundary",
        "donor_disjoint_validation_required",
        "independent_heldout_study_required",
    }
    required_false = {
        "automatic_mesh_repair",
        "automatic_unit_conversion",
        "automatic_proxy_substitution",
        "automatic_runtime_activation",
        "automatic_mechanics_coupling",
    }
    if any(gate.get(key) is not True for key in required_true) or any(
        gate.get(key) is not False for key in required_false
    ):
        raise PHHMeshBoundaryError("PHH mesh gate escaped fail-closed policy")
    if not isinstance(policy, dict) or policy.get("manual_primary_source_review_required") is not True:
        raise PHHMeshBoundaryError("PHH mesh review policy changed")
    if any(
        policy.get(key) is not False
        for key in (
            "aggregate_volume_may_replace_individual_mesh",
            "cell_line_mesh_may_initialize_healthy_phh",
            "nonhuman_mesh_may_initialize_healthy_phh",
            "renderer_proxy_is_measurement",
            "topological_watertightness_implies_no_self_intersection",
            "mesh_implies_mechanical_parameters",
            "missing_structure_means_absent",
            "automatic_parameter_activation",
        )
    ):
        raise PHHMeshBoundaryError("PHH mesh policy escaped fail-closed state")
    return payload


def _point(raw: object, *, label: str) -> tuple[float, float, float]:
    if not isinstance(raw, list) or len(raw) != 3:
        raise PHHMeshBoundaryError(f"{label} must contain three coordinates")
    values = tuple(float(value) for value in raw)
    if not all(math.isfinite(value) for value in values):
        raise PHHMeshBoundaryError(f"{label} contains a non-finite coordinate")
    return values  # type: ignore[return-value]


def _triangle(raw: object, *, label: str, vertex_count: int) -> tuple[int, int, int]:
    if not isinstance(raw, list) or len(raw) != 3:
        raise PHHMeshBoundaryError(f"{label} must contain three indices")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in raw):
        raise PHHMeshBoundaryError(f"{label} indices must be integers")
    values = tuple(int(value) for value in raw)
    if any(value < 0 or value >= vertex_count for value in values):
        raise PHHMeshBoundaryError(f"{label} index is outside the vertex array")
    return values  # type: ignore[return-value]


def _double_area_squared(
    a: Sequence[float],
    b: Sequence[float],
    c: Sequence[float],
) -> float:
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    cross = (
        ab[1] * ac[2] - ab[2] * ac[1],
        ab[2] * ac[0] - ab[0] * ac[2],
        ab[0] * ac[1] - ab[1] * ac[0],
    )
    return sum(value * value for value in cross)


def _bounds_overlap(
    first: tuple[tuple[float, float, float], tuple[float, float, float]],
    second: tuple[tuple[float, float, float], tuple[float, float, float]],
    tolerance: float,
) -> bool:
    return all(
        first[0][axis] <= second[1][axis] + tolerance
        and first[1][axis] + tolerance >= second[0][axis]
        for axis in range(3)
    )


def _orient_2d(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _point_on_segment_2d(
    point: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
    tolerance: float,
) -> bool:
    return (
        abs(_orient_2d(start, end, point)) <= tolerance
        and min(start[0], end[0]) - tolerance
        <= point[0]
        <= max(start[0], end[0]) + tolerance
        and min(start[1], end[1]) - tolerance
        <= point[1]
        <= max(start[1], end[1]) + tolerance
    )


def _segments_intersect_2d(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
    d: tuple[float, float],
    tolerance: float,
) -> bool:
    ab_c = _orient_2d(a, b, c)
    ab_d = _orient_2d(a, b, d)
    cd_a = _orient_2d(c, d, a)
    cd_b = _orient_2d(c, d, b)
    if (
        ((ab_c > tolerance and ab_d < -tolerance) or
         (ab_c < -tolerance and ab_d > tolerance))
        and ((cd_a > tolerance and cd_b < -tolerance) or
             (cd_a < -tolerance and cd_b > tolerance))
    ):
        return True
    return any(
        (
            _point_on_segment_2d(c, a, b, tolerance),
            _point_on_segment_2d(d, a, b, tolerance),
            _point_on_segment_2d(a, c, d, tolerance),
            _point_on_segment_2d(b, c, d, tolerance),
        )
    )


def _point_in_triangle_2d(
    point: tuple[float, float],
    triangle: Sequence[tuple[float, float]],
    tolerance: float,
) -> bool:
    orientations = (
        _orient_2d(triangle[0], triangle[1], point),
        _orient_2d(triangle[1], triangle[2], point),
        _orient_2d(triangle[2], triangle[0], point),
    )
    has_negative = any(value < -tolerance for value in orientations)
    has_positive = any(value > tolerance for value in orientations)
    return not (has_negative and has_positive)


def _segment_triangle_intersects(
    start: Sequence[float],
    end: Sequence[float],
    triangle: Sequence[Sequence[float]],
    tolerance: float,
) -> bool:
    direction = tuple(end[axis] - start[axis] for axis in range(3))
    edge1 = tuple(triangle[1][axis] - triangle[0][axis] for axis in range(3))
    edge2 = tuple(triangle[2][axis] - triangle[0][axis] for axis in range(3))
    p = (
        direction[1] * edge2[2] - direction[2] * edge2[1],
        direction[2] * edge2[0] - direction[0] * edge2[2],
        direction[0] * edge2[1] - direction[1] * edge2[0],
    )
    determinant = sum(edge1[axis] * p[axis] for axis in range(3))
    if abs(determinant) <= tolerance:
        return False
    inverse = 1.0 / determinant
    relative = tuple(start[axis] - triangle[0][axis] for axis in range(3))
    u = sum(relative[axis] * p[axis] for axis in range(3)) * inverse
    if u < -tolerance or u > 1.0 + tolerance:
        return False
    q = (
        relative[1] * edge1[2] - relative[2] * edge1[1],
        relative[2] * edge1[0] - relative[0] * edge1[2],
        relative[0] * edge1[1] - relative[1] * edge1[0],
    )
    v = sum(direction[axis] * q[axis] for axis in range(3)) * inverse
    if v < -tolerance or u + v > 1.0 + tolerance:
        return False
    parameter = sum(edge2[axis] * q[axis] for axis in range(3)) * inverse
    return -tolerance <= parameter <= 1.0 + tolerance


def _triangles_intersect(
    first: Sequence[Sequence[float]],
    second: Sequence[Sequence[float]],
    tolerance: float,
) -> bool:
    first_edge1 = tuple(first[1][axis] - first[0][axis] for axis in range(3))
    first_edge2 = tuple(first[2][axis] - first[0][axis] for axis in range(3))
    first_normal = (
        first_edge1[1] * first_edge2[2] - first_edge1[2] * first_edge2[1],
        first_edge1[2] * first_edge2[0] - first_edge1[0] * first_edge2[2],
        first_edge1[0] * first_edge2[1] - first_edge1[1] * first_edge2[0],
    )
    second_edge1 = tuple(second[1][axis] - second[0][axis] for axis in range(3))
    second_edge2 = tuple(second[2][axis] - second[0][axis] for axis in range(3))
    second_normal = (
        second_edge1[1] * second_edge2[2] - second_edge1[2] * second_edge2[1],
        second_edge1[2] * second_edge2[0] - second_edge1[0] * second_edge2[2],
        second_edge1[0] * second_edge2[1] - second_edge1[1] * second_edge2[0],
    )
    first_normal_length = math.sqrt(sum(value * value for value in first_normal))
    second_normal_length = math.sqrt(sum(value * value for value in second_normal))
    plane_distance = max(
        abs(sum(
            first_normal[axis] * (point[axis] - first[0][axis])
            for axis in range(3)
        )) / first_normal_length
        for point in second
    )
    normal_cross = (
        first_normal[1] * second_normal[2] - first_normal[2] * second_normal[1],
        first_normal[2] * second_normal[0] - first_normal[0] * second_normal[2],
        first_normal[0] * second_normal[1] - first_normal[1] * second_normal[0],
    )
    coplanar = (
        plane_distance <= tolerance
        and math.sqrt(sum(value * value for value in normal_cross))
        <= max(1e-12, first_normal_length * second_normal_length * 1e-10)
    )
    if coplanar:
        dropped_axis = max(range(3), key=lambda axis: abs(first_normal[axis]))

        def project(point: Sequence[float]) -> tuple[float, float]:
            axes = [axis for axis in range(3) if axis != dropped_axis]
            return (point[axes[0]], point[axes[1]])

        first_2d = tuple(project(point) for point in first)
        second_2d = tuple(project(point) for point in second)
        tolerance_2d = max(1e-12, tolerance * tolerance)
        for first_edge in range(3):
            for second_edge in range(3):
                if _segments_intersect_2d(
                    first_2d[first_edge],
                    first_2d[(first_edge + 1) % 3],
                    second_2d[second_edge],
                    second_2d[(second_edge + 1) % 3],
                    tolerance_2d,
                ):
                    return True
        return (
            _point_in_triangle_2d(first_2d[0], second_2d, tolerance_2d)
            or _point_in_triangle_2d(second_2d[0], first_2d, tolerance_2d)
        )
    return any(
        _segment_triangle_intersects(
            first[edge],
            first[(edge + 1) % 3],
            second,
            tolerance,
        )
        or _segment_triangle_intersects(
            second[edge],
            second[(edge + 1) % 3],
            first,
            tolerance,
        )
        for edge in range(3)
    )


def _self_intersecting_triangle_pair_count(
    vertices: Sequence[Sequence[float]],
    triangles: Sequence[tuple[int, int, int]],
    tolerance: float,
) -> int:
    bounds = []
    for triangle_index, indices in enumerate(triangles):
        points = tuple(vertices[index] for index in indices)
        minimum = tuple(min(point[axis] for point in points) for axis in range(3))
        maximum = tuple(max(point[axis] for point in points) for axis in range(3))
        bounds.append((minimum[0], triangle_index, indices, (minimum, maximum)))
    bounds.sort(key=lambda item: item[0])
    count = 0
    for first_index, (_, first_triangle, first_indices, first_bounds) in enumerate(bounds):
        for _, second_triangle, second_indices, second_bounds in bounds[first_index + 1:]:
            if second_bounds[0][0] > first_bounds[1][0] + tolerance:
                break
            if not _bounds_overlap(first_bounds, second_bounds, tolerance):
                continue
            if set(first_indices) & set(second_indices):
                continue
            first_points = tuple(vertices[index] for index in triangles[first_triangle])
            second_points = tuple(vertices[index] for index in triangles[second_triangle])
            if _triangles_intersect(first_points, second_points, tolerance):
                count += 1
    return count


def audit_canonical_triangle_mesh_artifact(
    path: Path,
) -> TriangleMeshTopologyAudit:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != CANONICAL_MESH_SCHEMA_VERSION
        or payload.get("coordinate_unit") != "um"
    ):
        raise PHHMeshBoundaryError("unsupported canonical triangle-mesh artifact")
    raw_vertices = payload.get("vertices_um")
    raw_triangles = payload.get("triangles")
    if not isinstance(raw_vertices, list) or len(raw_vertices) < 4:
        raise PHHMeshBoundaryError("canonical mesh needs at least four vertices")
    vertices = tuple(
        _point(value, label=f"vertex {index}")
        for index, value in enumerate(raw_vertices)
    )
    if not isinstance(raw_triangles, list) or len(raw_triangles) < 1:
        raise PHHMeshBoundaryError("canonical mesh needs at least one triangle")
    triangles = tuple(
        _triangle(value, label=f"triangle {index}", vertex_count=len(vertices))
        for index, value in enumerate(raw_triangles)
    )
    minimum = tuple(min(point[axis] for point in vertices) for axis in range(3))
    maximum = tuple(max(point[axis] for point in vertices) for axis in range(3))
    diagonal = math.sqrt(sum((maximum[axis] - minimum[axis]) ** 2 for axis in range(3)))
    area_tolerance_squared = max(1e-24, diagonal**4 * 1e-24)
    volume_tolerance = max(1e-12, diagonal**3 * 1e-12)
    intersection_tolerance = max(1e-10, diagonal * 1e-10)
    used: set[int] = set()
    edge_uses: dict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
    surface_area = 0.0
    signed_volume = 0.0
    degenerate = 0
    for triangle_index, (ia, ib, ic) in enumerate(triangles):
        used.update((ia, ib, ic))
        a, b, c = vertices[ia], vertices[ib], vertices[ic]
        double_area_squared = _double_area_squared(a, b, c)
        if len({ia, ib, ic}) < 3 or double_area_squared <= area_tolerance_squared:
            degenerate += 1
        surface_area += 0.5 * math.sqrt(max(0.0, double_area_squared))
        signed_volume += (
            a[0] * (b[1] * c[2] - b[2] * c[1])
            - a[1] * (b[0] * c[2] - b[2] * c[0])
            + a[2] * (b[0] * c[1] - b[1] * c[0])
        ) / 6.0
        for first, second in ((ia, ib), (ib, ic), (ic, ia)):
            edge = (min(first, second), max(first, second))
            direction = 1 if first < second else -1
            edge_uses[edge].append((triangle_index, direction))
    boundary_edges = sum(len(uses) == 1 for uses in edge_uses.values())
    non_manifold_edges = sum(len(uses) > 2 for uses in edge_uses.values())
    inconsistent_winding = sum(
        len(uses) == 2 and uses[0][1] == uses[1][1]
        for uses in edge_uses.values()
    )
    adjacency: list[set[int]] = [set() for _ in triangles]
    for uses in edge_uses.values():
        if len(uses) == 2:
            adjacency[uses[0][0]].add(uses[1][0])
            adjacency[uses[1][0]].add(uses[0][0])
    pending = set(range(len(triangles)))
    components = 0
    while pending:
        components += 1
        stack = [pending.pop()]
        while stack:
            current = stack.pop()
            for neighbor in adjacency[current] & pending:
                pending.remove(neighbor)
                stack.append(neighbor)
    consistently_oriented = inconsistent_winding == 0
    one_component = components == 1
    watertight = (
        degenerate == 0
        and len(vertices) - len(used) == 0
        and boundary_edges == 0
        and non_manifold_edges == 0
        and consistently_oriented
        and one_component
        and abs(signed_volume) > volume_tolerance
    )
    self_intersecting_pair_count = _self_intersecting_triangle_pair_count(
        vertices,
        triangles,
        intersection_tolerance,
    )
    self_intersection_free = self_intersecting_pair_count == 0
    return TriangleMeshTopologyAudit(
        vertex_count=len(vertices),
        triangle_count=len(triangles),
        isolated_vertex_count=len(vertices) - len(used),
        degenerate_triangle_count=degenerate,
        boundary_edge_count=boundary_edges,
        non_manifold_edge_count=non_manifold_edges,
        inconsistent_winding_edge_count=inconsistent_winding,
        connected_component_count=components,
        surface_area_um2=surface_area,
        signed_volume_um3=signed_volume,
        enclosed_volume_um3=abs(signed_volume),
        topologically_watertight=watertight,
        consistently_oriented=consistently_oriented,
        single_connected_component=one_component,
        self_intersection_tested=True,
        self_intersecting_triangle_pair_count=self_intersecting_pair_count,
        self_intersection_free=self_intersection_free,
        valid_closed_boundary=watertight and self_intersection_free,
    )


def _required_text(row: dict[str, str], field: str, row_number: int) -> str:
    value = row[field].strip()
    if not value or value.lower() == _NULL_TOKEN:
        raise PHHMeshBoundaryError(f"row {row_number}: {field} is required")
    return value


def _optional_text(row: dict[str, str], field: str) -> str | None:
    value = row[field].strip()
    return None if not value or value.lower() == _NULL_TOKEN else value


def _positive_float(row: dict[str, str], field: str, row_number: int) -> float:
    raw = _required_text(row, field, row_number)
    try:
        value = float(raw)
    except ValueError as error:
        raise PHHMeshBoundaryError(f"row {row_number}: {field} must be numeric") from error
    if not math.isfinite(value) or value <= 0:
        raise PHHMeshBoundaryError(f"row {row_number}: {field} must be positive")
    return value


def _record_from_row(row: dict[str, str], row_number: int) -> PHHMeshManifestRecord:
    values: dict[str, Any] = {
        field: _required_text(row, field, row_number)
        for field in (
            "record_id", "donor_id", "source_study_id", "source_locator",
            "split_role", "species", "tissue_health_state", "liver_zone",
            "preparation_context", "fixation_and_processing", "imaging_modality",
            "segmentation_method", "structure_id", "instance_id",
            "biological_replicate_id", "mesh_artifact_path",
            "mesh_artifact_sha256", "coordinate_unit", "coordinate_frame",
            "registration_transform_id", "registration_target",
            "topology_qc_status", "self_intersection_qc_status",
            "self_intersection_tool_version", "self_intersection_report_path",
            "self_intersection_report_sha256", "uncertainty_description",
            "manual_primary_source_review_status",
        )
    }
    values.update(
        {
            field: _positive_float(row, field, row_number)
            for field in ("voxel_size_x_um", "voxel_size_y_um", "voxel_size_z_um")
        }
    )
    values.update(
        {
            field: _optional_text(row, field)
            for field in (
                "parent_structure_instance_id", "polarity_annotation_method",
                "membrane_domain_annotation_path",
                "membrane_domain_annotation_sha256",
                "contact_interface_annotation_path",
                "contact_interface_annotation_sha256",
                "paired_mechanics_record_id", "grid_convergence_report_path",
                "grid_convergence_report_sha256", "censoring_or_missingness",
            )
        }
    )
    if values["split_role"] not in _ALLOWED_SPLIT_ROLES:
        raise PHHMeshBoundaryError(f"row {row_number}: unsupported split_role")
    if values["species"] != "Homo sapiens":
        raise PHHMeshBoundaryError(f"row {row_number}: species must be Homo sapiens")
    if values["structure_id"] not in _TARGET_STRUCTURE_IDS:
        raise PHHMeshBoundaryError(f"row {row_number}: unsupported structure_id")
    if values["coordinate_unit"] != "um":
        raise PHHMeshBoundaryError(f"row {row_number}: coordinate_unit must be um")
    for path_field, checksum_field in (
        ("membrane_domain_annotation_path", "membrane_domain_annotation_sha256"),
        ("contact_interface_annotation_path", "contact_interface_annotation_sha256"),
        ("grid_convergence_report_path", "grid_convergence_report_sha256"),
    ):
        if (values[path_field] is None) != (values[checksum_field] is None):
            raise PHHMeshBoundaryError(
                f"row {row_number}: {path_field} and {checksum_field} must be paired"
            )
    return PHHMeshManifestRecord(**values)


def load_phh_3d_mesh_manifest(
    path: Path = DEFAULT_MANIFEST_PATH,
) -> tuple[PHHMeshManifestRecord, ...]:
    contract = load_phh_3d_mesh_boundary_contract()
    if not path.exists():
        return ()
    expected_header = tuple(
        item["id"]
        for group in ("required_columns", "conditional_columns")
        for item in contract[group]
    )
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != expected_header:
            raise PHHMeshBoundaryError("PHH mesh manifest header changed")
        records = tuple(
            _record_from_row(row, row_number)
            for row_number, row in enumerate(reader, start=2)
        )
    record_ids = [record.record_id for record in records]
    if len(record_ids) != len(set(record_ids)):
        raise PHHMeshBoundaryError("PHH mesh manifest record_id values must be unique")
    donor_splits: dict[tuple[str, str], set[str]] = defaultdict(set)
    for record in records:
        donor_splits[(record.source_study_id, record.donor_id)].add(record.split_role)
    if any(len(splits) > 1 for splits in donor_splits.values()):
        raise PHHMeshBoundaryError("PHH mesh donor leaks across dataset splits")
    return records


def assess_phh_mesh_record(record: PHHMeshManifestRecord) -> PHHMeshAssessment:
    mesh_path = _verify_artifact(
        record.mesh_artifact_path,
        record.mesh_artifact_sha256,
        label=f"mesh artifact {record.record_id}",
    )
    topology = audit_canonical_triangle_mesh_artifact(mesh_path)
    report_path = _verify_artifact(
        record.self_intersection_report_path,
        record.self_intersection_report_sha256,
        label=f"self-intersection report {record.record_id}",
    )
    blockers: list[str] = []
    if not topology.topologically_watertight:
        blockers.append("canonical mesh fails the repository topology audit")
    if not topology.self_intersection_free:
        blockers.append("canonical mesh fails the repository self-intersection audit")
    if record.topology_qc_status != "pass":
        blockers.append("supplying topology QC is not pass")
    if record.self_intersection_qc_status != "pass":
        blockers.append("external geometric self-intersection QC is not pass")
    if report_path.stat().st_size <= 0:
        blockers.append("external self-intersection report is empty")
    if record.manual_primary_source_review_status != "pass":
        blockers.append("manual primary-source review is not pass")
    if "healthy" not in record.tissue_health_state.lower() and "non-diseased" not in record.tissue_health_state.lower():
        blockers.append("healthy/non-diseased tissue context is not explicit")
    grid_verified = False
    if record.grid_convergence_report_path and record.grid_convergence_report_sha256:
        grid_path = _verify_artifact(
            record.grid_convergence_report_path,
            record.grid_convergence_report_sha256,
            label=f"grid-convergence report {record.record_id}",
        )
        grid_verified = grid_path.stat().st_size > 0
    if not grid_verified:
        blockers.append("registered mesh has no checksum-frozen grid-convergence report")
    if record.split_role != "independent_heldout":
        blockers.append("record is not an independent held-out validation specimen")
    structurally_ready = not blockers
    return PHHMeshAssessment(
        record_id=record.record_id,
        structure_id=record.structure_id,
        split_role=record.split_role,
        topology=topology,
        artifact_checksum_verified=True,
        repository_self_intersection_free=topology.self_intersection_free,
        external_self_intersection_report_verified=report_path.stat().st_size > 0,
        grid_convergence_report_verified=grid_verified,
        structurally_ready=structurally_ready,
        runtime_boundary_registration_allowed=False,
        mechanics_coupling_allowed=False,
        blockers=tuple(blockers)
        + ("explicit reviewed promotion into the runtime boundary registry is required",),
    )


def phh_3d_mesh_boundary_intake_snapshot(
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
) -> dict[str, object]:
    contract = load_phh_3d_mesh_boundary_contract()
    records = load_phh_3d_mesh_manifest(manifest_path)
    assessments = tuple(assess_phh_mesh_record(record) for record in records)
    contract_sha256 = _sha256(CONTRACT_PATH)
    manifest_sha256 = _sha256(manifest_path) if manifest_path.exists() else None
    return {
        "version": INTAKE_VERSION,
        "status": "contract_ready_no_runtime_biological_mesh_registered",
        "contract_id": contract["contract_id"],
        "contract_path": _display_path(CONTRACT_PATH),
        "contract_sha256": contract_sha256,
        "delivery_path": _display_path(manifest_path),
        "delivery_sha256": manifest_sha256,
        "expected_headers": [
            item["id"]
            for group in ("required_columns", "conditional_columns")
            for item in contract[group]
        ],
        "target_structure_ids": list(_TARGET_STRUCTURE_IDS),
        "canonical_mesh_artifact_schema": CANONICAL_MESH_SCHEMA_VERSION,
        "records": [asdict(record) for record in records],
        "assessments": [asdict(assessment) for assessment in assessments],
        "summary": {
            "required_field_count": len(contract["required_columns"]),
            "conditional_field_count": len(contract["conditional_columns"]),
            "target_structure_count": len(_TARGET_STRUCTURE_IDS),
            "manifest_record_count": len(records),
            "mesh_artifact_count": len(assessments),
            "topologically_watertight_artifact_count": sum(
                assessment.topology.topologically_watertight
                for assessment in assessments
            ),
            "self_intersection_audited_artifact_count": sum(
                assessment.external_self_intersection_report_verified
                for assessment in assessments
            ),
            "repository_self_intersection_audited_artifact_count": len(assessments),
            "repository_self_intersection_free_artifact_count": sum(
                assessment.repository_self_intersection_free
                for assessment in assessments
            ),
            "grid_convergence_verified_artifact_count": sum(
                assessment.grid_convergence_report_verified
                for assessment in assessments
            ),
            "structurally_ready_mesh_count": sum(
                assessment.structurally_ready for assessment in assessments
            ),
            "registered_biological_mesh_boundary_count": 0,
            "contact_ground_truth_mesh_count": sum(
                record.contact_interface_annotation_path is not None
                for record in records
            ),
            "mechanics_coupled_mesh_count": 0,
            "automatic_runtime_activation_count": 0,
        },
        "gates": {
            "generic_watertight_triangle_mesh_numerical_kernel_available": True,
            "topology_audit_available": True,
            "self_intersection_audit_implemented_in_repository": True,
            "biological_mesh_registration_allowed": False,
            "mechanics_coupling_allowed": False,
            "automatic_runtime_activation": False,
        },
        "limitations": [
            "The repository topology audit does not detect geometric self-intersections.",
            "A topologically closed mesh is not automatically a valid microscopy-derived PHH boundary.",
            "Aggregate human morphometry and renderer proxy geometry cannot satisfy this intake.",
            "No delivered mesh is promoted into the renderer or numerical fluid domain.",
            "Mesh geometry never implies membrane, cortex, adhesion or hydraulic mechanics.",
        ],
    }


__all__ = [
    "CANONICAL_MESH_SCHEMA_VERSION",
    "CONTRACT_PATH",
    "DEFAULT_MANIFEST_PATH",
    "PHHMeshBoundaryError",
    "PHHMeshManifestRecord",
    "PHHMeshAssessment",
    "TriangleMeshTopologyAudit",
    "assess_phh_mesh_record",
    "audit_canonical_triangle_mesh_artifact",
    "load_phh_3d_mesh_boundary_contract",
    "load_phh_3d_mesh_manifest",
    "phh_3d_mesh_boundary_intake_snapshot",
]
