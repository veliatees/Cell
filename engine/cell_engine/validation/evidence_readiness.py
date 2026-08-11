"""Unified fail-closed preflight for PHH evidence-intake contracts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Callable, Mapping

from cell_engine.ml.generative import generative_donor_manifest_intake_snapshot
from cell_engine.processes.cellular_memory import MEMORY_SUBSTRATE_CONTRACTS
from cell_engine.quantitative.active_cargo_trajectory import (
    active_cargo_trajectory_intake_snapshot,
)
from cell_engine.quantitative.active_protein_localization import (
    active_protein_localization_snapshot,
)
from cell_engine.quantitative.cellular_memory_trajectory import (
    cellular_memory_trajectory_intake_snapshot,
)
from cell_engine.quantitative.completion_evidence import (
    completion_evidence_bundle_intake_snapshot,
)
from cell_engine.quantitative.energy_redox_trajectory import (
    energy_redox_trajectory_intake_snapshot,
)
from cell_engine.quantitative.intracellular_mobility import (
    intracellular_mobility_intake_snapshot,
)
from cell_engine.quantitative.phh_3d_mesh_boundary import (
    phh_3d_mesh_boundary_intake_snapshot,
)
from cell_engine.quantitative.phh_injury_trajectory import (
    phh_injury_trajectory_intake_snapshot,
)
from cell_engine.quantitative.phh_mechanics_calibration import (
    phh_mechanics_calibration_intake_snapshot,
)
from cell_engine.quantitative.phh_membrane_topology_event import (
    DEFAULT_CONTRACT_PATH as MEMBRANE_TOPOLOGY_CONTRACT_PATH,
    phh_membrane_topology_event_intake_snapshot,
)
from cell_engine.quantitative.phh_metabolic_execution_bundle import (
    phh_metabolic_execution_bundle_intake_snapshot,
)
from cell_engine.quantitative.reaction_evidence_intake import (
    reaction_evidence_intake_snapshot,
)
from cell_engine.quantitative.reaction_transport_coupling import (
    reaction_transport_coupling_intake_snapshot,
)
from cell_engine.quantitative.receptor_signaling_trajectory import (
    receptor_signaling_trajectory_snapshot,
)
from cell_engine.validation.evidence_intake import evidence_intake_snapshot


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "evidence_intake"
    / "phh_evidence_readiness_registry.v1.json"
)
DEFAULT_INCOMING_ROOT = (
    REPOSITORY_ROOT / "data" / "evidence_intake" / "incoming"
)
REGISTRY_SCHEMA_VERSION = "cell.phh-evidence-readiness-registry.v1"
REGISTRY_ID = "phh_evidence_readiness_registry_v1"
VERSION = "phh_evidence_readiness_v1"

REGISTRY_ENTRY_IDS = (
    "legacy_scale_bridge_bundle",
    "reaction_evidence",
    "energy_redox_trajectory",
    "receptor_signaling_trajectory",
    "active_protein_localization",
    "phh_3d_mesh_boundary",
    "intracellular_mobility",
    "reaction_transport_coupling",
    "active_cargo_trajectory",
    "cellular_memory_trajectory",
    "phh_injury_trajectory",
    "generative_donor_manifest",
    "phh_mechanics_calibration",
    "membrane_topology_event",
    "metabolic_execution_bundle",
    "completion_evidence_bundle",
)

VALIDATOR_SURFACES = {
    "legacy_scale_bridge_bundle": (
        "cell_engine.validation.evidence_intake.evidence_intake_snapshot"
    ),
    "reaction_evidence": (
        "cell_engine.quantitative.reaction_evidence_intake."
        "reaction_evidence_intake_snapshot"
    ),
    "energy_redox_trajectory": (
        "cell_engine.quantitative.energy_redox_trajectory."
        "energy_redox_trajectory_intake_snapshot"
    ),
    "receptor_signaling_trajectory": (
        "cell_engine.quantitative.receptor_signaling_trajectory."
        "receptor_signaling_trajectory_snapshot"
    ),
    "active_protein_localization": (
        "cell_engine.quantitative.active_protein_localization."
        "active_protein_localization_snapshot"
    ),
    "phh_3d_mesh_boundary": (
        "cell_engine.quantitative.phh_3d_mesh_boundary."
        "phh_3d_mesh_boundary_intake_snapshot"
    ),
    "intracellular_mobility": (
        "cell_engine.quantitative.intracellular_mobility."
        "intracellular_mobility_intake_snapshot"
    ),
    "reaction_transport_coupling": (
        "cell_engine.quantitative.reaction_transport_coupling."
        "reaction_transport_coupling_intake_snapshot"
    ),
    "active_cargo_trajectory": (
        "cell_engine.quantitative.active_cargo_trajectory."
        "active_cargo_trajectory_intake_snapshot"
    ),
    "cellular_memory_trajectory": (
        "cell_engine.quantitative.cellular_memory_trajectory."
        "cellular_memory_trajectory_intake_snapshot"
    ),
    "phh_injury_trajectory": (
        "cell_engine.quantitative.phh_injury_trajectory."
        "phh_injury_trajectory_intake_snapshot"
    ),
    "generative_donor_manifest": (
        "cell_engine.ml.generative.generative_donor_manifest_intake_snapshot"
    ),
    "phh_mechanics_calibration": (
        "cell_engine.quantitative.phh_mechanics_calibration."
        "phh_mechanics_calibration_intake_snapshot"
    ),
    "membrane_topology_event": (
        "cell_engine.quantitative.phh_membrane_topology_event."
        "phh_membrane_topology_event_intake_snapshot"
    ),
    "metabolic_execution_bundle": (
        "cell_engine.quantitative.phh_metabolic_execution_bundle."
        "phh_metabolic_execution_bundle_intake_snapshot"
    ),
    "completion_evidence_bundle": (
        "cell_engine.quantitative.completion_evidence."
        "completion_evidence_bundle_intake_snapshot"
    ),
}

_POLICY = {
    "manual_primary_source_review_required": True,
    "invalid_delivery_quarantined": True,
    "automatic_parameter_activation": False,
    "automatic_state_coupling": False,
    "predictive_authority": False,
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPOSITORY_ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def _safe_relative_path(value: object, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty relative path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{field} must stay inside its declared root")
    return path


def load_phh_evidence_readiness_registry(
    path: Path = REGISTRY_PATH,
) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    validate_phh_evidence_readiness_registry(payload)
    return payload


def validate_phh_evidence_readiness_registry(payload: object) -> None:
    if not isinstance(payload, dict):
        raise ValueError("PHH evidence readiness registry must be an object")
    if (
        payload.get("schema_version") != REGISTRY_SCHEMA_VERSION
        or payload.get("registry_id") != REGISTRY_ID
    ):
        raise ValueError("unsupported PHH evidence readiness registry identity")
    if (
        payload.get("scientific_authority") is not False
        or payload.get("biological_parameter_activation") is not False
    ):
        raise ValueError("PHH evidence registry cannot carry scientific authority")
    _safe_relative_path(payload.get("incoming_root"), "incoming_root")
    if payload.get("policy") != _POLICY:
        raise ValueError("PHH evidence readiness policy changed")

    raw_entries = payload.get("entries")
    if not isinstance(raw_entries, list):
        raise ValueError("PHH evidence readiness entries are required")
    if tuple(
        item.get("id") if isinstance(item, Mapping) else None
        for item in raw_entries
    ) != REGISTRY_ENTRY_IDS:
        raise ValueError("PHH evidence readiness registry order or ids changed")

    for raw_entry in raw_entries:
        if not isinstance(raw_entry, Mapping):
            raise ValueError("PHH evidence readiness entry must be an object")
        entry_id = str(raw_entry["id"])
        contract_relative = _safe_relative_path(
            raw_entry.get("contract_path"), "contract_path"
        )
        _safe_relative_path(
            raw_entry.get("delivery_relative_path"), "delivery_relative_path"
        )
        if raw_entry.get("delivery_kind") not in {
            "directory_bundle",
            "csv",
            "json",
        }:
            raise ValueError(f"{entry_id}: unsupported delivery kind")
        if raw_entry.get("validator_surface") != VALIDATOR_SURFACES[entry_id]:
            raise ValueError(f"{entry_id}: validator surface changed")
        target_gap_ids = raw_entry.get("target_gap_ids")
        if (
            not isinstance(target_gap_ids, list)
            or not target_gap_ids
            or any(
                not isinstance(gap_id, str) or not gap_id
                for gap_id in target_gap_ids
            )
            or len(target_gap_ids) != len(set(target_gap_ids))
        ):
            raise ValueError(f"{entry_id}: target gap registry is malformed")

        contract_path = REPOSITORY_ROOT / contract_relative
        if not contract_path.is_file():
            raise ValueError(f"{entry_id}: canonical contract is absent")
        contract_sha256 = _sha256(contract_path)
        if raw_entry.get("contract_sha256") != contract_sha256:
            raise ValueError(f"{entry_id}: canonical contract SHA-256 mismatch")
        contract_payload = json.loads(contract_path.read_text(encoding="utf-8"))
        if not isinstance(contract_payload, Mapping):
            raise ValueError(f"{entry_id}: canonical contract must be an object")
        if (
            contract_payload.get("schema_version")
            != raw_entry.get("contract_schema_version")
            or contract_payload.get("contract_id") != raw_entry.get("contract_id")
        ):
            raise ValueError(f"{entry_id}: canonical contract identity mismatch")


def _record_ids(snapshot: Mapping[str, object]) -> set[str]:
    records = snapshot.get("records")
    if not isinstance(records, (list, tuple)):
        return set()
    return {
        str(record["record_id"])
        for record in records
        if isinstance(record, Mapping)
        and isinstance(record.get("record_id"), str)
        and record["record_id"]
    }


def _run_adapter(
    entry_id: str,
    delivery_path: Path,
    prior_snapshots: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    adapters: dict[str, Callable[[], dict[str, object]]] = {
        "legacy_scale_bridge_bundle": lambda: evidence_intake_snapshot(
            delivery_path
        ),
        "reaction_evidence": lambda: reaction_evidence_intake_snapshot(
            delivery_path
        ),
        "energy_redox_trajectory": lambda: energy_redox_trajectory_intake_snapshot(
            delivery_path
        ),
        "receptor_signaling_trajectory": lambda: receptor_signaling_trajectory_snapshot(
            delivery_path
        ),
        "active_protein_localization": lambda: active_protein_localization_snapshot(
            delivery_path
        ),
        "phh_3d_mesh_boundary": lambda: phh_3d_mesh_boundary_intake_snapshot(
            delivery_path
        ),
        "intracellular_mobility": lambda: intracellular_mobility_intake_snapshot(
            delivery_path
        ),
        "reaction_transport_coupling": lambda: (
            reaction_transport_coupling_intake_snapshot(
                delivery_path,
                available_mobility_record_ids=_record_ids(
                    prior_snapshots.get("intracellular_mobility", {})
                ),
                available_geometry_record_ids=_record_ids(
                    prior_snapshots.get("phh_3d_mesh_boundary", {})
                ),
            )
        ),
        "active_cargo_trajectory": lambda: active_cargo_trajectory_intake_snapshot(
            delivery_path
        ),
        "cellular_memory_trajectory": lambda: (
            cellular_memory_trajectory_intake_snapshot(
                allowed_substrate_ids=tuple(
                    item.id for item in MEMORY_SUBSTRATE_CONTRACTS
                ),
                path=delivery_path,
            )
        ),
        "phh_injury_trajectory": lambda: phh_injury_trajectory_intake_snapshot(
            delivery_path
        ),
        "generative_donor_manifest": lambda: (
            generative_donor_manifest_intake_snapshot(delivery_path)
        ),
        "phh_mechanics_calibration": lambda: (
            phh_mechanics_calibration_intake_snapshot(delivery_path)
        ),
        "membrane_topology_event": lambda: (
            phh_membrane_topology_event_intake_snapshot(
                delivery_path
                if delivery_path.is_file()
                else MEMBRANE_TOPOLOGY_CONTRACT_PATH
            )
        ),
        "metabolic_execution_bundle": lambda: (
            phh_metabolic_execution_bundle_intake_snapshot(delivery_path)
        ),
        "completion_evidence_bundle": lambda: (
            completion_evidence_bundle_intake_snapshot(delivery_path)
        ),
    }
    return adapters[entry_id]()


def _int_value(mapping: Mapping[str, object], key: str) -> int:
    value = mapping.get(key, 0)
    return int(value) if isinstance(value, (bool, int)) else 0


def _summary(snapshot: Mapping[str, object]) -> Mapping[str, object]:
    value = snapshot.get("summary")
    return value if isinstance(value, Mapping) else {}


def _current_delivery(snapshot: Mapping[str, object]) -> Mapping[str, object]:
    value = snapshot.get("current_delivery")
    return value if isinstance(value, Mapping) else {}


def _table_record_count(snapshot: Mapping[str, object]) -> int:
    tables = snapshot.get("tables")
    if not isinstance(tables, (list, tuple)):
        return 0
    return sum(
        _int_value(table, "record_count")
        for table in tables
        if isinstance(table, Mapping)
    )


def _metric_counts(
    entry_id: str,
    snapshot: Mapping[str, object],
    delivery_present: bool,
) -> tuple[int, int, int, int]:
    summary = _summary(snapshot)
    current_delivery = _current_delivery(snapshot)
    one_artifact = int(delivery_present)
    if entry_id == "legacy_scale_bridge_bundle":
        return (
            _int_value(snapshot, "present_file_count"),
            _table_record_count(snapshot),
            _int_value(snapshot, "curation_candidate_count"),
            0,
        )
    if entry_id == "reaction_evidence":
        return (
            one_artifact,
            _int_value(snapshot, "record_count"),
            _int_value(snapshot, "structurally_complete_reaction_count"),
            sum(
                _int_value(snapshot, key)
                for key in (
                    "atlas_mutation_allowed_count",
                    "quantitative_execution_allowed_count",
                    "predictive_execution_allowed_count",
                )
            ),
        )
    if entry_id == "energy_redox_trajectory":
        return (
            one_artifact,
            _int_value(snapshot, "record_count"),
            _int_value(snapshot, "structurally_complete_trajectory_count"),
            _int_value(snapshot, "compartment_initialization_allowed_count")
            + _int_value(snapshot, "rate_fitting_allowed_count"),
        )
    if entry_id == "receptor_signaling_trajectory":
        return (
            one_artifact,
            _int_value(snapshot, "record_count"),
            _int_value(snapshot, "structurally_complete_pathway_count"),
            sum(
                _int_value(snapshot, key)
                for key in (
                    "receptor_activation_allowed_count",
                    "signal_execution_allowed_count",
                    "cell_state_coupling_allowed_count",
                )
            ),
        )
    if entry_id == "active_protein_localization":
        return (
            one_artifact,
            _int_value(snapshot, "record_count"),
            _int_value(snapshot, "structurally_complete_protein_count"),
            sum(
                _int_value(snapshot, key)
                for key in (
                    "active_copy_or_concentration_authorized_count",
                    "functional_rate_authorized_count",
                    "cell_state_coupling_allowed_count",
                )
            ),
        )
    if entry_id == "phh_3d_mesh_boundary":
        return (
            one_artifact,
            _int_value(summary, "manifest_record_count"),
            _int_value(summary, "structurally_ready_mesh_count"),
            _int_value(summary, "registered_biological_mesh_boundary_count")
            + _int_value(summary, "mechanics_coupled_mesh_count"),
        )
    if entry_id == "intracellular_mobility":
        return (
            one_artifact,
            _int_value(summary, "record_count"),
            _int_value(summary, "structurally_complete_species_count"),
            sum(
                _int_value(summary, key)
                for key in (
                    "apparent_diffusivity_authorized_species_count",
                    "crowding_law_authorized_species_count",
                    "reaction_coupled_species_count",
                )
            ),
        )
    if entry_id == "reaction_transport_coupling":
        return (
            one_artifact,
            _int_value(summary, "record_count"),
            _int_value(summary, "structurally_complete_reaction_count"),
            sum(
                _int_value(summary, key)
                for key in (
                    "local_concentration_coupled_reaction_count",
                    "direct_rate_corrected_reaction_count",
                    "runtime_activated_reaction_count",
                )
            ),
        )
    if entry_id == "active_cargo_trajectory":
        return (
            one_artifact,
            _int_value(snapshot, "record_count"),
            _int_value(snapshot, "structurally_complete_route_count"),
            _int_value(snapshot, "quantitatively_authorized_route_count"),
        )
    if entry_id == "cellular_memory_trajectory":
        return (
            one_artifact,
            _int_value(snapshot, "record_count"),
            _int_value(snapshot, "structurally_complete_candidate_count"),
            _int_value(snapshot, "quantitatively_authorized_memory_law_count"),
        )
    if entry_id == "phh_injury_trajectory":
        record_count = _int_value(
            current_delivery, "donor_resolved_raw_record_count"
        )
        return (
            one_artifact,
            record_count,
            record_count,
            _int_value(current_delivery, "general_fate_law_count"),
        )
    if entry_id == "generative_donor_manifest":
        return (
            one_artifact,
            _int_value(snapshot, "sample_count"),
            int(bool(snapshot.get("structurally_training_data_ready"))),
            _int_value(snapshot, "validated_generative_donor_model_count"),
        )
    if entry_id == "phh_mechanics_calibration":
        return (
            one_artifact,
            _int_value(snapshot, "record_count"),
            _int_value(snapshot, "structurally_complete_trajectory_count"),
            _int_value(snapshot, "quantitatively_authorized_parameter_count"),
        )
    if entry_id == "membrane_topology_event":
        return (
            one_artifact,
            _int_value(snapshot, "record_count"),
            _int_value(snapshot, "structurally_complete_record_count"),
            _int_value(snapshot, "quantitatively_authorized_record_count"),
        )
    if entry_id == "metabolic_execution_bundle":
        return (
            _int_value(snapshot, "delivered_bundle_count"),
            _int_value(snapshot, "measured_exchange_bound_count")
            + _int_value(snapshot, "independent_validation_record_count"),
            _int_value(snapshot, "structurally_complete_bundle_count"),
            sum(
                int(bool(snapshot.get(key)))
                for key in (
                    "fba_execution_allowed",
                    "fva_execution_allowed",
                    "runtime_flux_coupling_allowed",
                )
            ),
        )
    if entry_id == "completion_evidence_bundle":
        return (
            _int_value(summary, "delivered_table_count"),
            _int_value(summary, "record_count"),
            _int_value(summary, "structurally_complete_item_count"),
            _int_value(summary, "quantitatively_authorized_item_count"),
        )
    raise ValueError(f"unsupported evidence-readiness entry {entry_id}")


def _automatic_true_keys(value: object) -> tuple[str, ...]:
    found: list[str] = []

    def visit(node: object) -> None:
        if isinstance(node, Mapping):
            for key, child in node.items():
                if (
                    isinstance(key, str)
                    and key.startswith("automatic_")
                    and child is True
                ):
                    found.append(key)
                visit(child)
        elif isinstance(node, (list, tuple)):
            for child in node:
                visit(child)

    visit(value)
    return tuple(sorted(set(found)))


def _blockers(snapshot: Mapping[str, object]) -> tuple[str, ...]:
    value = snapshot.get("blockers")
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(str(item) for item in value)


def _delivery_kind_valid(path: Path, delivery_kind: str) -> bool:
    if delivery_kind == "directory_bundle":
        return path.is_dir()
    return path.is_file()


def phh_evidence_readiness_snapshot(
    incoming_root: Path = DEFAULT_INCOMING_ROOT,
) -> dict[str, object]:
    registry = load_phh_evidence_readiness_registry()
    raw_entries = registry["entries"]
    if not isinstance(raw_entries, list):
        raise ValueError("validated registry lost its entry list")

    snapshots: dict[str, Mapping[str, object]] = {}
    entries: list[dict[str, object]] = []
    for raw_entry in raw_entries:
        if not isinstance(raw_entry, Mapping):
            raise ValueError("validated registry contains a malformed entry")
        entry_id = str(raw_entry["id"])
        relative_delivery = _safe_relative_path(
            raw_entry["delivery_relative_path"], "delivery_relative_path"
        )
        delivery_path = incoming_root / relative_delivery
        delivery_exists = delivery_path.exists()
        validation_error: str | None = None
        snapshot: Mapping[str, object] = {}
        try:
            if delivery_exists and not _delivery_kind_valid(
                delivery_path, str(raw_entry["delivery_kind"])
            ):
                raise ValueError(
                    "delivery exists but does not match the declared file or directory kind"
                )
            snapshot = _run_adapter(entry_id, delivery_path, snapshots)
            if not isinstance(snapshot, Mapping):
                raise ValueError("validator did not return an intake snapshot")
        except (ValueError, OSError, UnicodeError, json.JSONDecodeError) as exc:
            validation_error = str(exc)

        intake_status = str(
            snapshot.get("status", "rejected_invalid_delivery")
        )
        blockers = _blockers(snapshot)
        if intake_status.startswith("rejected_") and validation_error is None:
            validation_error = (
                blockers[0] if blockers else "delivery failed structural validation"
            )
        automatic_true_keys = _automatic_true_keys(snapshot)
        if automatic_true_keys and validation_error is None:
            validation_error = (
                "intake attempted automatic authority through "
                + ", ".join(automatic_true_keys)
            )
        rejected = validation_error is not None
        if rejected:
            registry_status = "rejected_invalid_delivery"
        elif not delivery_exists:
            registry_status = "awaiting_delivery"
        else:
            registry_status = "delivery_structurally_audited"

        if rejected:
            delivered_artifact_count = 0
            delivered_record_count = 0
            structurally_complete_item_count = 0
            quantitatively_authorized_item_count = 0
        else:
            (
                delivered_artifact_count,
                delivered_record_count,
                structurally_complete_item_count,
                quantitatively_authorized_item_count,
            ) = _metric_counts(entry_id, snapshot, delivery_exists)

        entry = {
            "id": entry_id,
            "status": registry_status,
            "contract_path": raw_entry["contract_path"],
            "contract_sha256": raw_entry["contract_sha256"],
            "contract_schema_version": raw_entry["contract_schema_version"],
            "contract_id": raw_entry["contract_id"],
            "contract_identity_verified": True,
            "validator_surface": raw_entry["validator_surface"],
            "validator_surface_registered": True,
            "delivery_kind": raw_entry["delivery_kind"],
            "delivery_path": _display_path(delivery_path),
            "delivery_present": delivery_exists,
            "intake_snapshot_version": snapshot.get("version"),
            "intake_status": intake_status,
            "delivered_artifact_count": delivered_artifact_count,
            "delivered_record_count": delivered_record_count,
            "structurally_complete_item_count": structurally_complete_item_count,
            "quantitatively_authorized_item_count": (
                quantitatively_authorized_item_count
            ),
            "target_gap_ids": tuple(raw_entry["target_gap_ids"]),
            "blocker_count": max(len(blockers), int(rejected)),
            "validation_error": validation_error,
            "automatic_parameter_activation": bool(automatic_true_keys),
            "automatic_state_coupling": any(
                "coupling" in key for key in automatic_true_keys
            ),
        }
        entries.append(entry)
        snapshots[entry_id] = snapshot

    target_gap_ids = tuple(
        sorted(
            {
                str(gap_id)
                for entry in entries
                for gap_id in entry["target_gap_ids"]
            }
        )
    )
    summary = {
        "registry_contract_count": len(entries),
        "contract_identity_verified_count": sum(
            bool(entry["contract_identity_verified"]) for entry in entries
        ),
        "validator_surface_count": sum(
            bool(entry["validator_surface_registered"]) for entry in entries
        ),
        "delivery_present_count": sum(
            bool(entry["delivery_present"]) for entry in entries
        ),
        "delivered_artifact_count": sum(
            int(entry["delivered_artifact_count"]) for entry in entries
        ),
        "delivered_record_count": sum(
            int(entry["delivered_record_count"]) for entry in entries
        ),
        "structurally_complete_item_count": sum(
            int(entry["structurally_complete_item_count"]) for entry in entries
        ),
        "quantitatively_authorized_item_count": sum(
            int(entry["quantitatively_authorized_item_count"])
            for entry in entries
        ),
        "rejected_intake_count": sum(
            entry["status"] == "rejected_invalid_delivery" for entry in entries
        ),
        "awaiting_intake_count": sum(
            entry["status"] == "awaiting_delivery" for entry in entries
        ),
        "structurally_audited_intake_count": sum(
            entry["status"] == "delivery_structurally_audited"
            for entry in entries
        ),
        "target_gap_count": len(target_gap_ids),
        "automatic_parameter_activation_count": sum(
            bool(entry["automatic_parameter_activation"]) for entry in entries
        ),
        "automatic_state_coupling_count": sum(
            bool(entry["automatic_state_coupling"]) for entry in entries
        ),
    }
    if summary["rejected_intake_count"]:
        status = "delivery_quarantine_active"
    elif summary["delivery_present_count"]:
        status = "deliveries_structurally_audited_manual_review_required"
    else:
        status = "contracts_verified_awaiting_external_evidence"
    payload = {
        "version": VERSION,
        "registry_id": registry["registry_id"],
        "status": status,
        "registry_path": _display_path(REGISTRY_PATH),
        "registry_sha256": _sha256(REGISTRY_PATH),
        "incoming_root": _display_path(incoming_root),
        "scientific_authority": False,
        "biological_parameter_activation": False,
        "entries": tuple(entries),
        "target_gap_ids": target_gap_ids,
        "policy": dict(_POLICY),
        "summary": summary,
    }
    validate_phh_evidence_readiness_snapshot(payload)
    return payload


def validate_phh_evidence_readiness_snapshot(payload: object) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError("PHH evidence readiness snapshot must be an object")
    if payload.get("version") != VERSION or payload.get("registry_id") != REGISTRY_ID:
        raise ValueError("unexpected PHH evidence readiness snapshot identity")
    if (
        payload.get("scientific_authority") is not False
        or payload.get("biological_parameter_activation") is not False
        or payload.get("policy") != _POLICY
    ):
        raise ValueError("PHH evidence readiness snapshot escaped fail-closed policy")
    entries = payload.get("entries")
    summary = payload.get("summary")
    target_gap_ids = payload.get("target_gap_ids")
    if (
        not isinstance(entries, (list, tuple))
        or not isinstance(summary, Mapping)
        or not isinstance(target_gap_ids, (list, tuple))
    ):
        raise ValueError("PHH evidence readiness snapshot is malformed")
    if tuple(
        entry.get("id") if isinstance(entry, Mapping) else None
        for entry in entries
    ) != REGISTRY_ENTRY_IDS:
        raise ValueError("PHH evidence readiness snapshot entries changed")
    if any(
        not isinstance(entry, Mapping)
        or entry.get("contract_identity_verified") is not True
        or entry.get("validator_surface_registered") is not True
        or not isinstance(entry.get("target_gap_ids"), (list, tuple))
        for entry in entries
    ):
        raise ValueError("PHH evidence contract identity or validator is unresolved")
    expected_target_gap_ids = tuple(
        sorted(
            {
                str(gap_id)
                for entry in entries
                if isinstance(entry, Mapping)
                for gap_id in entry.get("target_gap_ids", ())
            }
        )
    )
    if tuple(target_gap_ids) != expected_target_gap_ids:
        raise ValueError("PHH evidence readiness target-gap registry is stale")
    if any(
        bool(entry.get("automatic_parameter_activation"))
        or bool(entry.get("automatic_state_coupling"))
        for entry in entries
        if isinstance(entry, Mapping)
    ):
        raise ValueError("PHH evidence intake activated an automatic model surface")

    expected_counts = {
        "registry_contract_count": len(entries),
        "contract_identity_verified_count": sum(
            bool(entry["contract_identity_verified"]) for entry in entries
        ),
        "validator_surface_count": sum(
            bool(entry["validator_surface_registered"]) for entry in entries
        ),
        "delivery_present_count": sum(
            bool(entry["delivery_present"]) for entry in entries
        ),
        "delivered_artifact_count": sum(
            int(entry["delivered_artifact_count"]) for entry in entries
        ),
        "delivered_record_count": sum(
            int(entry["delivered_record_count"]) for entry in entries
        ),
        "structurally_complete_item_count": sum(
            int(entry["structurally_complete_item_count"]) for entry in entries
        ),
        "quantitatively_authorized_item_count": sum(
            int(entry["quantitatively_authorized_item_count"])
            for entry in entries
        ),
        "rejected_intake_count": sum(
            entry["status"] == "rejected_invalid_delivery" for entry in entries
        ),
        "awaiting_intake_count": sum(
            entry["status"] == "awaiting_delivery" for entry in entries
        ),
        "structurally_audited_intake_count": sum(
            entry["status"] == "delivery_structurally_audited"
            for entry in entries
        ),
        "target_gap_count": len(set(target_gap_ids)),
        "automatic_parameter_activation_count": 0,
        "automatic_state_coupling_count": 0,
    }
    for key, expected in expected_counts.items():
        if summary.get(key) != expected:
            raise ValueError(f"PHH evidence readiness summary is stale: {key}")


__all__ = [
    "DEFAULT_INCOMING_ROOT",
    "REGISTRY_ENTRY_IDS",
    "REGISTRY_PATH",
    "VERSION",
    "load_phh_evidence_readiness_registry",
    "phh_evidence_readiness_snapshot",
    "validate_phh_evidence_readiness_registry",
    "validate_phh_evidence_readiness_snapshot",
]
