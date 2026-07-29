"""Fail-closed intake for event-resolved healthy-PHH membrane topology data."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTRACT_PATH = (
    ROOT
    / "data/evidence_intake"
    / "phh_membrane_topology_event_contract.v1.json"
)
SCHEMA_VERSION = "cell.phh-membrane-topology-event-intake.v1"
VERSION = "phh_membrane_topology_event_intake_v1"
TARGET_EVENT_KINDS = (
    "bud_growth",
    "neck_formation",
    "fission",
    "fusion",
)
REQUIRED_RECORD_FIELDS = (
    "record_id",
    "source_id",
    "source_doi_or_accession",
    "source_url",
    "citation",
    "species",
    "donor_id",
    "donor_age_years",
    "donor_sex",
    "donor_health_status",
    "primary_cell_status",
    "culture_configuration",
    "medium_and_supplements",
    "temperature_c",
    "event_kind",
    "membrane_domain",
    "cargo_identity",
    "surface_protein_identities",
    "pre_mesh_path",
    "pre_mesh_sha256",
    "post_mesh_path",
    "post_mesh_sha256",
    "mesh_coordinate_unit",
    "acquisition_modality",
    "voxel_size_x_um",
    "voxel_size_y_um",
    "voxel_size_z_um",
    "time_unit",
    "timepoint_values",
    "event_time_value",
    "neck_radius_trajectory",
    "neck_radius_unit",
    "surface_area_trajectory",
    "surface_area_unit",
    "enclosed_volume_trajectory",
    "enclosed_volume_unit",
    "membrane_tension_trajectory",
    "membrane_tension_unit",
    "cortical_traction_trajectory",
    "cortical_traction_unit",
    "pressure_trajectory",
    "pressure_unit",
    "membrane_reservoir_measurement",
    "lipid_addition_or_removal_measurement",
    "cargo_partition_before_after",
    "surface_protein_partition_before_after",
    "fusion_or_fission_partner_identity",
    "topology_qc_report_path",
    "topology_qc_report_sha256",
    "self_intersection_qc_status",
    "repository_transition_audit_path",
    "repository_transition_audit_sha256",
    "repository_transition_audit_status",
    "uncertainty_method",
    "validation_split",
    "independent_validation_source_id",
    "notes",
)


class PhhMembraneTopologyEventIntakeError(ValueError):
    """Raised when the topology-event evidence contract is malformed."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def _has_value(record: dict[str, Any], field: str) -> bool:
    value = record[field]
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict)):
        return bool(value)
    return True


def _repository_artifact_matches(
    raw_path: Any,
    raw_sha256: Any,
) -> bool:
    if (
        not isinstance(raw_path, str)
        or not raw_path.strip()
        or not isinstance(raw_sha256, str)
        or len(raw_sha256) != 64
        or any(character not in "0123456789abcdefABCDEF" for character in raw_sha256)
    ):
        return False
    root = ROOT.resolve()
    candidate = (ROOT / raw_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return (
        candidate.is_file()
        and _sha256(candidate) == raw_sha256.lower()
    )


def _numeric_series(value: Any) -> tuple[float, ...] | None:
    if not isinstance(value, (list, tuple)) or len(value) < 2:
        return None
    if any(
        isinstance(item, bool)
        or not isinstance(item, (int, float))
        or not math.isfinite(float(item))
        for item in value
    ):
        return None
    return tuple(float(item) for item in value)


def _assess_record(record: dict[str, Any]) -> dict[str, Any]:
    optional_value_fields = {
        "notes",
        "membrane_tension_trajectory",
        "membrane_tension_unit",
        "cortical_traction_trajectory",
        "cortical_traction_unit",
        "fusion_or_fission_partner_identity",
    }
    required_value_fields = set(REQUIRED_RECORD_FIELDS) - optional_value_fields
    if record["event_kind"] in {"fission", "fusion"}:
        required_value_fields.add("fusion_or_fission_partner_identity")
    filled_fields = tuple(
        field for field in REQUIRED_RECORD_FIELDS if _has_value(record, field)
    )
    missing_fields = tuple(
        field
        for field in REQUIRED_RECORD_FIELDS
        if field in required_value_fields and field not in filled_fields
    )
    healthy_phh_context = (
        record["species"] == "Homo sapiens"
        and record["donor_health_status"] == "healthy"
        and record["primary_cell_status"]
        == "primary_human_hepatocyte"
    )
    geometry_metadata_complete = all(
        _has_value(record, field)
        for field in (
            "pre_mesh_path",
            "pre_mesh_sha256",
            "post_mesh_path",
            "post_mesh_sha256",
            "mesh_coordinate_unit",
            "voxel_size_x_um",
            "voxel_size_y_um",
            "voxel_size_z_um",
            "timepoint_values",
            "event_time_value",
            "topology_qc_report_path",
            "topology_qc_report_sha256",
            "self_intersection_qc_status",
            "repository_transition_audit_path",
            "repository_transition_audit_sha256",
            "repository_transition_audit_status",
        )
    )
    geometry_artifacts_verified = all(
        (
            _repository_artifact_matches(
                record["pre_mesh_path"],
                record["pre_mesh_sha256"],
            ),
            _repository_artifact_matches(
                record["post_mesh_path"],
                record["post_mesh_sha256"],
            ),
            _repository_artifact_matches(
                record["topology_qc_report_path"],
                record["topology_qc_report_sha256"],
            ),
            _repository_artifact_matches(
                record["repository_transition_audit_path"],
                record["repository_transition_audit_sha256"],
            ),
            record["self_intersection_qc_status"] == "passed",
            record["repository_transition_audit_status"] == "passed",
        )
    )
    geometry_complete = (
        geometry_metadata_complete and geometry_artifacts_verified
    )
    timepoints = _numeric_series(record["timepoint_values"])
    neck_radius = _numeric_series(record["neck_radius_trajectory"])
    surface_area = _numeric_series(record["surface_area_trajectory"])
    enclosed_volume = _numeric_series(record["enclosed_volume_trajectory"])
    pressure = _numeric_series(record["pressure_trajectory"])
    required_series = (
        timepoints,
        neck_radius,
        surface_area,
        enclosed_volume,
        pressure,
    )
    trajectory_complete = (
        all(series is not None for series in required_series)
        and len({len(series) for series in required_series if series is not None})
        == 1
        and isinstance(record["event_time_value"], (int, float))
        and not isinstance(record["event_time_value"], bool)
        and math.isfinite(float(record["event_time_value"]))
    )
    tension = _numeric_series(record["membrane_tension_trajectory"])
    traction = _numeric_series(record["cortical_traction_trajectory"])
    mechanics_complete = (
        timepoints is not None
        and (
            (
                tension is not None
                and len(tension) == len(timepoints)
                and _has_value(record, "membrane_tension_unit")
            )
            or (
                traction is not None
                and len(traction) == len(timepoints)
                and _has_value(record, "cortical_traction_unit")
            )
        )
    )
    partition_complete = all(
        _has_value(record, field)
        for field in (
            "cargo_partition_before_after",
            "surface_protein_partition_before_after",
        )
    )
    independent_heldout = (
        record["validation_split"] == "heldout"
        and _has_value(record, "independent_validation_source_id")
    )
    structurally_complete = (
        len(missing_fields) == 0 and mechanics_complete
    )
    quantitatively_authorized = all(
        (
            structurally_complete,
            healthy_phh_context,
            geometry_complete,
            trajectory_complete,
            mechanics_complete,
            partition_complete,
            independent_heldout,
        )
    )
    return {
        "record_id": record["record_id"],
        "event_kind": record["event_kind"],
        "filled_field_count": len(filled_fields),
        "missing_fields": missing_fields,
        "healthy_phh_context": healthy_phh_context,
        "geometry_metadata_complete": geometry_metadata_complete,
        "geometry_artifacts_verified": geometry_artifacts_verified,
        "geometry_complete": geometry_complete,
        "trajectory_complete": trajectory_complete,
        "mechanics_complete": mechanics_complete,
        "partition_complete": partition_complete,
        "independent_heldout_validation": independent_heldout,
        "structurally_complete": structurally_complete,
        "quantitatively_authorized": quantitatively_authorized,
    }


def phh_membrane_topology_event_intake_snapshot(
    path: Path = DEFAULT_CONTRACT_PATH,
) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise PhhMembraneTopologyEventIntakeError(
            "unexpected membrane topology event intake schema"
        )
    if payload.get("contract_id") != "healthy_phh_membrane_topology_event_intake_v1":
        raise PhhMembraneTopologyEventIntakeError(
            "unexpected membrane topology event contract id"
        )
    if tuple(payload.get("target_event_kinds", ())) != TARGET_EVENT_KINDS:
        raise PhhMembraneTopologyEventIntakeError(
            "membrane topology target event kinds changed"
        )
    if tuple(payload.get("required_record_fields", ())) != REQUIRED_RECORD_FIELDS:
        raise PhhMembraneTopologyEventIntakeError(
            "membrane topology required record fields changed"
        )
    rules = payload.get("authorization_rules")
    records = payload.get("records")
    if not isinstance(rules, dict) or not isinstance(records, list):
        raise PhhMembraneTopologyEventIntakeError(
            "membrane topology evidence contract is malformed"
        )
    required_true_rules = (
        "healthy_phh_context_required",
        "event_resolved_pre_and_post_meshes_required",
        "checksum_frozen_geometry_required",
        "neck_and_area_trajectory_required",
        "membrane_or_cortex_mechanics_required",
        "cargo_and_surface_partition_required",
        "repository_topology_audit_required",
        "independent_heldout_validation_required",
    )
    required_false_rules = (
        "cross_species_parameter_transfer_allowed",
        "automatic_missing_value_imputation",
        "automatic_event_threshold_fitting",
        "automatic_runtime_activation",
    )
    if any(rules.get(rule) is not True for rule in required_true_rules):
        raise PhhMembraneTopologyEventIntakeError(
            "membrane topology evidence requirement was weakened"
        )
    if any(rules.get(rule) is not False for rule in required_false_rules):
        raise PhhMembraneTopologyEventIntakeError(
            "membrane topology evidence firewall was weakened"
        )

    record_ids: set[str] = set()
    assessments: list[dict[str, Any]] = []
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise PhhMembraneTopologyEventIntakeError(
                f"membrane topology record {index} is not an object"
            )
        missing_keys = set(REQUIRED_RECORD_FIELDS) - set(record)
        unexpected_keys = set(record) - set(REQUIRED_RECORD_FIELDS)
        if missing_keys or unexpected_keys:
            raise PhhMembraneTopologyEventIntakeError(
                f"membrane topology record {index} has an invalid field set"
            )
        record_id = record["record_id"]
        if not isinstance(record_id, str) or not record_id.strip():
            raise PhhMembraneTopologyEventIntakeError(
                f"membrane topology record {index} has an invalid id"
            )
        if record_id in record_ids:
            raise PhhMembraneTopologyEventIntakeError(
                f"duplicate membrane topology record id {record_id}"
            )
        record_ids.add(record_id)
        if record["event_kind"] not in TARGET_EVENT_KINDS:
            raise PhhMembraneTopologyEventIntakeError(
                f"membrane topology record {record_id} has an invalid event kind"
            )
        assessments.append(_assess_record(record))

    structurally_complete_count = sum(
        assessment["structurally_complete"] for assessment in assessments
    )
    healthy_phh_count = sum(
        assessment["healthy_phh_context"] for assessment in assessments
    )
    authorized_count = sum(
        assessment["quantitatively_authorized"] for assessment in assessments
    )
    return {
        "version": VERSION,
        "contract_id": payload["contract_id"],
        "schema_version": payload["schema_version"],
        "status": (
            "empty_intake_runtime_topology_activation_blocked"
            if not records
            else "records_audited_runtime_activation_requires_authorized_record"
        ),
        "delivery_path": _display_path(path),
        "contract_sha256": _sha256(path),
        "target_event_kinds": TARGET_EVENT_KINDS,
        "required_record_fields": REQUIRED_RECORD_FIELDS,
        "required_field_count": len(REQUIRED_RECORD_FIELDS),
        "record_count": len(records),
        "healthy_phh_context_record_count": healthy_phh_count,
        "structurally_complete_record_count": structurally_complete_count,
        "quantitatively_authorized_record_count": authorized_count,
        "runtime_topology_activation_allowed": False,
        "automatic_missing_value_imputation": False,
        "automatic_event_threshold_fitting": False,
        "automatic_runtime_activation": False,
        "record_assessments": assessments,
        "blockers": (
            (
                "No event-resolved healthy-PHH membrane topology record is "
                "delivered."
            )
            if not records
            else (
                "Only independently validated, structurally complete healthy-PHH "
                "records may authorize a future explicit runtime integration."
            ),
        ),
    }


def validate_phh_membrane_topology_event_intake_snapshot(
    payload: dict[str, Any],
) -> None:
    if payload.get("version") != VERSION:
        raise PhhMembraneTopologyEventIntakeError(
            "unexpected membrane topology event intake version"
        )
    if payload.get("required_field_count") != len(REQUIRED_RECORD_FIELDS):
        raise PhhMembraneTopologyEventIntakeError(
            "membrane topology required field count changed"
        )
    if payload.get("runtime_topology_activation_allowed") is not False:
        raise PhhMembraneTopologyEventIntakeError(
            "membrane topology evidence automatically authorized runtime activation"
        )
    if (
        payload.get("automatic_missing_value_imputation") is not False
        or payload.get("automatic_event_threshold_fitting") is not False
        or payload.get("automatic_runtime_activation") is not False
    ):
        raise PhhMembraneTopologyEventIntakeError(
            "membrane topology evidence firewall was bypassed"
        )
