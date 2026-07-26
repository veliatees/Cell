from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from cell_engine.quantitative.phh_3d_mesh_boundary import (
    PHHMeshBoundaryError,
    audit_canonical_triangle_mesh_artifact,
    load_phh_3d_mesh_boundary_contract,
    load_phh_3d_mesh_manifest,
    phh_3d_mesh_boundary_intake_snapshot,
)


TETRAHEDRON = {
    "schema_version": "cell.triangle-mesh-boundary-artifact.v1",
    "coordinate_unit": "um",
    "vertices_um": [
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ],
    "triangles": [
        [1, 2, 3],
        [0, 3, 2],
        [0, 1, 3],
        [0, 2, 1],
    ],
}


def _write_json(path: Path, payload: object) -> str:
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_manifest(
    path: Path,
    *,
    mesh_path: Path,
    mesh_sha256: str,
    self_report_path: Path,
    self_report_sha256: str,
    grid_report_path: Path,
    grid_report_sha256: str,
) -> None:
    contract = load_phh_3d_mesh_boundary_contract()
    header = [
        item["id"]
        for group in ("required_columns", "conditional_columns")
        for item in contract[group]
    ]
    row = {field: "null" for field in header}
    row.update(
        {
            "record_id": "mesh-001",
            "donor_id": "donor-heldout",
            "source_study_id": "study-heldout",
            "source_locator": "volume-1/cell-1",
            "split_role": "independent_heldout",
            "species": "Homo sapiens",
            "tissue_health_state": "healthy adult donor liver",
            "liver_zone": "midlobular",
            "preparation_context": "in-situ tissue",
            "fixation_and_processing": "fixed; shrinkage correction reported",
            "imaging_modality": "software fixture tomography",
            "voxel_size_x_um": "0.2",
            "voxel_size_y_um": "0.2",
            "voxel_size_z_um": "0.2",
            "segmentation_method": "software fixture manual segmentation",
            "structure_id": "cell_outer_membrane",
            "instance_id": "cell-1",
            "biological_replicate_id": "replicate-1",
            "mesh_artifact_path": str(mesh_path),
            "mesh_artifact_sha256": mesh_sha256,
            "coordinate_unit": "um",
            "coordinate_frame": "cell-fixed",
            "registration_transform_id": "transform-frozen-1",
            "registration_target": "measured cell centroid and polarity axis",
            "topology_qc_status": "pass",
            "self_intersection_qc_status": "pass",
            "self_intersection_tool_version": "fixture-auditor 1.0",
            "self_intersection_report_path": str(self_report_path),
            "self_intersection_report_sha256": self_report_sha256,
            "uncertainty_description": "software fixture only",
            "manual_primary_source_review_status": "pass",
            "grid_convergence_report_path": str(grid_report_path),
            "grid_convergence_report_sha256": grid_report_sha256,
        }
    )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerow(row)


def test_empty_mesh_intake_keeps_biological_registration_disabled(tmp_path: Path) -> None:
    snapshot = phh_3d_mesh_boundary_intake_snapshot(tmp_path / "missing.csv")
    assert snapshot["summary"]["target_structure_count"] == 11
    assert snapshot["summary"]["required_field_count"] == 31
    assert snapshot["summary"]["manifest_record_count"] == 0
    assert snapshot["summary"]["registered_biological_mesh_boundary_count"] == 0
    assert snapshot["gates"]["generic_watertight_triangle_mesh_numerical_kernel_available"] is True
    assert snapshot["gates"]["self_intersection_audit_implemented_in_repository"] is False
    assert snapshot["gates"]["biological_mesh_registration_allowed"] is False


def test_canonical_mesh_topology_audit_accepts_closed_tetrahedron(tmp_path: Path) -> None:
    mesh_path = tmp_path / "tetrahedron.json"
    _write_json(mesh_path, TETRAHEDRON)
    audit = audit_canonical_triangle_mesh_artifact(mesh_path)
    assert audit.topologically_watertight is True
    assert audit.boundary_edge_count == 0
    assert audit.non_manifold_edge_count == 0
    assert audit.inconsistent_winding_edge_count == 0
    assert audit.connected_component_count == 1
    assert audit.enclosed_volume_um3 == pytest.approx(1.0 / 6.0)
    assert audit.self_intersection_tested is False


def test_canonical_mesh_topology_audit_rejects_open_surface(tmp_path: Path) -> None:
    mesh_path = tmp_path / "open.json"
    payload = dict(TETRAHEDRON)
    payload["triangles"] = TETRAHEDRON["triangles"][:-1]
    _write_json(mesh_path, payload)
    audit = audit_canonical_triangle_mesh_artifact(mesh_path)
    assert audit.topologically_watertight is False
    assert audit.boundary_edge_count == 3


def test_exact_manifest_header_is_required(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("record_id,donor_id\n1,d1\n", encoding="utf-8")
    with pytest.raises(PHHMeshBoundaryError, match="header changed"):
        load_phh_3d_mesh_manifest(path)


def test_complete_software_fixture_never_auto_registers_mesh(tmp_path: Path) -> None:
    mesh_path = tmp_path / "mesh.json"
    mesh_sha = _write_json(mesh_path, TETRAHEDRON)
    self_report = tmp_path / "self-intersection.txt"
    self_report.write_text("fixture pass", encoding="utf-8")
    self_sha = hashlib.sha256(self_report.read_bytes()).hexdigest()
    grid_report = tmp_path / "grid.txt"
    grid_report.write_text("fixture convergence pass", encoding="utf-8")
    grid_sha = hashlib.sha256(grid_report.read_bytes()).hexdigest()
    manifest = tmp_path / "manifest.csv"
    _write_manifest(
        manifest,
        mesh_path=mesh_path,
        mesh_sha256=mesh_sha,
        self_report_path=self_report,
        self_report_sha256=self_sha,
        grid_report_path=grid_report,
        grid_report_sha256=grid_sha,
    )

    snapshot = phh_3d_mesh_boundary_intake_snapshot(manifest)
    assert snapshot["summary"]["manifest_record_count"] == 1
    assert snapshot["summary"]["topologically_watertight_artifact_count"] == 1
    assert snapshot["summary"]["structurally_ready_mesh_count"] == 1
    assert snapshot["summary"]["registered_biological_mesh_boundary_count"] == 0
    assert snapshot["summary"]["mechanics_coupled_mesh_count"] == 0
    assessment = snapshot["assessments"][0]
    assert assessment["runtime_boundary_registration_allowed"] is False
    assert assessment["mechanics_coupling_allowed"] is False


def test_mesh_checksum_mismatch_fails_closed(tmp_path: Path) -> None:
    mesh_path = tmp_path / "mesh.json"
    _write_json(mesh_path, TETRAHEDRON)
    self_report = tmp_path / "self-intersection.txt"
    self_report.write_text("fixture pass", encoding="utf-8")
    self_sha = hashlib.sha256(self_report.read_bytes()).hexdigest()
    grid_report = tmp_path / "grid.txt"
    grid_report.write_text("fixture convergence pass", encoding="utf-8")
    grid_sha = hashlib.sha256(grid_report.read_bytes()).hexdigest()
    manifest = tmp_path / "manifest.csv"
    _write_manifest(
        manifest,
        mesh_path=mesh_path,
        mesh_sha256="0" * 64,
        self_report_path=self_report,
        self_report_sha256=self_sha,
        grid_report_path=grid_report,
        grid_report_sha256=grid_sha,
    )
    with pytest.raises(PHHMeshBoundaryError, match="SHA-256 mismatch"):
        phh_3d_mesh_boundary_intake_snapshot(manifest)
