from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
POLICY_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "validation"
    / "scientific_snapshot_export_policy.v1.json"
)
POLICY_SCHEMA_VERSION = "cell.scientific-snapshot-export-policy.v1"
CACHE_SURFACE_IDS = (
    "sbml_document_inspection",
    "sbml_reaction_fingerprints",
    "phh_proteome_gene_accession_indexes",
    "compartmental_energy_redox_contract",
    "kinetic_transfer_audit",
    "reaction_evidence_atlas",
    "metabolic_constraint_shell",
)
RETURN_POLICIES = {
    "defensive_deepcopy",
    "immutable_tuple_graph",
    "source_record_identity_preserved",
    "immutable_frozen_dataclass_graph",
}


def scientific_snapshot_export_policy_snapshot() -> dict[str, object]:
    payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    validate_scientific_snapshot_export_policy(payload)
    return payload


def validate_scientific_snapshot_export_policy(payload: object) -> None:
    if not isinstance(payload, dict):
        raise ValueError("scientific snapshot export policy must be an object")
    if payload.get("schema_version") != POLICY_SCHEMA_VERSION:
        raise ValueError("unsupported scientific snapshot export policy schema")
    if (
        payload.get("scientific_authority") is not False
        or payload.get("biological_parameter_activation") is not False
    ):
        raise ValueError("snapshot export policy cannot carry biological authority")

    raw_surfaces = payload.get("cache_surfaces")
    if not isinstance(raw_surfaces, list):
        raise ValueError("snapshot cache surfaces are required")
    surfaces: list[Mapping[str, object]] = []
    for item in raw_surfaces:
        if not isinstance(item, Mapping):
            raise ValueError("snapshot cache surface must be an object")
        surfaces.append(item)
    if tuple(item.get("id") for item in surfaces) != CACHE_SURFACE_IDS:
        raise ValueError("snapshot cache surface registry changed")

    by_id = {str(item["id"]): item for item in surfaces}
    for surface in surfaces:
        if (
            not isinstance(surface.get("scope"), str)
            or not surface.get("scope")
            or surface.get("cache_lifetime")
            not in {"process_local", "stat_invalidated_process_local"}
            or not isinstance(surface.get("invalidation_keys"), list)
            or not isinstance(surface.get("custom_arguments_bypass_cache"), bool)
            or surface.get("return_policy") not in RETURN_POLICIES
        ):
            raise ValueError("snapshot cache surface contract is malformed")

    for surface_id in ("sbml_document_inspection", "sbml_reaction_fingerprints"):
        surface = by_id[surface_id]
        if (
            surface.get("cache_lifetime") != "stat_invalidated_process_local"
            or surface.get("invalidation_keys")
            != ["resolved_path", "mtime_ns", "size_bytes"]
        ):
            raise ValueError("SBML cache lost file-stat invalidation")

    for surface_id in (
        "phh_proteome_gene_accession_indexes",
        "kinetic_transfer_audit",
        "reaction_evidence_atlas",
    ):
        if by_id[surface_id].get("custom_arguments_bypass_cache") is not True:
            raise ValueError("custom scientific input no longer bypasses the default cache")

    equivalence = payload.get("scientific_output_equivalence")
    if not isinstance(equivalence, Mapping):
        raise ValueError("snapshot scientific-output equivalence policy is required")
    if (
        equivalence.get("required") is not True
        or equivalence.get("excluded_volatile_paths")
        != ["metadata.created_at_utc"]
        or equivalence.get("automatic_biological_parameter_activation_count")
        != 0
    ):
        raise ValueError("snapshot scientific-output equivalence policy changed")
