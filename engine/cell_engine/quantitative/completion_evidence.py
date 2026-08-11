"""Fail-closed intake for the remaining PHH evidence-only completion gaps.

This bundle covers three data surfaces that were previously named in the
completion matrix but had no machine-readable delivery path: p53/MDM2 damage
response, clonal population dynamics, and the quantitative slots in the
capability atlas. Structural acceptance never activates a parameter or model.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "evidence_intake"
    / "phh_completion_evidence_bundle_contract.v1.json"
)
DEFAULT_DELIVERY_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "evidence_intake"
    / "incoming"
    / "phh_completion_evidence"
    / "latest"
)
CONTRACT_SCHEMA_VERSION = "cell.phh-completion-evidence-bundle-contract.v1"
CONTRACT_ID = "phh_completion_evidence_bundle_contract_v1"
INTAKE_VERSION = "phh_completion_evidence_bundle_intake_v1"

TABLE_IDS = (
    "p53_ddr_trajectory",
    "clonal_population_trajectory",
    "capability_parameter_observation",
)
TABLE_FILES = {
    "p53_ddr_trajectory": "phh_p53_ddr_trajectories.csv",
    "clonal_population_trajectory": "phh_clonal_population_trajectories.csv",
    "capability_parameter_observation": "phh_capability_parameter_observations.csv",
}
TABLE_TARGETS = {
    "p53_ddr_trajectory": ("healthy_phh_p53_ddr_dynamics",),
    "clonal_population_trajectory": ("healthy_phh_clonal_population_dynamics",),
    "capability_parameter_observation": ("capability_template_quantitation",),
}

P53_COLUMNS = (
    "record_id",
    "donor_id",
    "split_role",
    "source_study_id",
    "source_locator",
    "species",
    "biological_system",
    "culture_format",
    "biological_replicate_id",
    "protocol_id",
    "damage_agent",
    "damage_dose_value",
    "damage_dose_unit",
    "exposure_start_h",
    "washout_time_h",
    "time_h",
    "analyte_id",
    "analyte_level",
    "compartment",
    "endpoint_class",
    "assay",
    "raw_value",
    "raw_unit",
    "normalization_denominator",
    "uncertainty_type",
    "uncertainty_value",
    "sample_size",
    "recovery_followup_h",
    "independent_review_id",
    "limitations",
)
CLONAL_COLUMNS = (
    "record_id",
    "donor_id",
    "split_role",
    "source_study_id",
    "source_locator",
    "species",
    "biological_system",
    "culture_or_tissue_context",
    "biological_replicate_id",
    "clone_id",
    "lineage_marker",
    "genotype",
    "ploidy",
    "injury_context",
    "nutrient_context",
    "zonation_context",
    "niche_context",
    "spatial_reference_frame",
    "position_x_um",
    "position_y_um",
    "position_z_um",
    "time_h",
    "endpoint",
    "raw_value",
    "raw_unit",
    "measurement_operator",
    "uncertainty_type",
    "uncertainty_value",
    "independent_review_id",
    "limitations",
)
CAPABILITY_COLUMNS = (
    "record_id",
    "capability_id",
    "parameter_slot_id",
    "donor_id",
    "split_role",
    "source_study_id",
    "source_locator",
    "doi",
    "species",
    "biological_system",
    "culture_format",
    "biological_replicate_id",
    "compartment",
    "assay",
    "quantity",
    "raw_value",
    "raw_unit",
    "normalization_denominator",
    "measurement_time",
    "perturbation_context",
    "uncertainty_type",
    "uncertainty_value",
    "independent_validation_id",
    "limitations",
)
TABLE_COLUMNS = {
    "p53_ddr_trajectory": P53_COLUMNS,
    "clonal_population_trajectory": CLONAL_COLUMNS,
    "capability_parameter_observation": CAPABILITY_COLUMNS,
}

_NULL_TOKEN = "null"
_ALLOWED_SPLIT_ROLES = frozenset(
    {"calibration", "internal_validation", "independent_heldout"}
)
_ALLOWED_SPECIES = frozenset({"Homo sapiens"})
_ALLOWED_SYSTEMS = frozenset(
    {
        "fresh_primary_human_hepatocyte",
        "plated_primary_human_hepatocyte",
        "primary_human_hepatocyte_spheroid",
        "adult_human_liver_in_situ",
    }
)
_P53_ANALYTES = frozenset({"TP53", "phospho_TP53", "MDM2"})
_P53_ENDPOINTS = frozenset(
    {"damage", "arrest_or_senescence", "apoptosis_or_survival", "recovery"}
)
_P53_LEVELS = frozenset(
    {"total_protein", "phosphoprotein", "fate_or_recovery_readout"}
)
_CLONAL_ENDPOINTS = frozenset(
    {"proliferation_or_clone_size", "arrest_senescence_death_or_clearance"}
)

class CompletionEvidenceError(ValueError):
    """Raised when a completion-evidence delivery violates its contract."""


@lru_cache(maxsize=1)
def _capability_slots() -> dict[tuple[str, str], tuple[str, str]]:
    # Lazy import avoids validation package initialization cycling back through
    # evidence_readiness while this quantitative intake module is imported.
    from cell_engine.validation.capability_atlas import HEPATOCYTE_CAPABILITIES

    return {
        (feature.id, slot.id): (slot.quantity, slot.unit)
        for feature in HEPATOCYTE_CAPABILITIES
        for slot in feature.parameter_slots
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


def _table_contracts(payload: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    tables = payload.get("tables")
    if not isinstance(tables, list) or any(not isinstance(item, Mapping) for item in tables):
        raise CompletionEvidenceError("completion-evidence table contracts are malformed")
    return tuple(tables)


def load_completion_evidence_contract(
    path: Path = CONTRACT_PATH,
) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CompletionEvidenceError("completion-evidence contract must be an object")
    if (
        payload.get("schema_version") != CONTRACT_SCHEMA_VERSION
        or payload.get("contract_id") != CONTRACT_ID
        or payload.get("canonical_null_token") != _NULL_TOKEN
    ):
        raise CompletionEvidenceError("unsupported completion-evidence contract identity")
    tables = _table_contracts(payload)
    if tuple(str(table.get("id")) for table in tables) != TABLE_IDS:
        raise CompletionEvidenceError("completion-evidence table order or identity changed")
    for table in tables:
        table_id = str(table["id"])
        if table.get("file") != TABLE_FILES[table_id]:
            raise CompletionEvidenceError(f"{table_id}: delivery filename changed")
        if tuple(table.get("target_gap_ids", ())) != TABLE_TARGETS[table_id]:
            raise CompletionEvidenceError(f"{table_id}: target-gap contract changed")
        if tuple(table.get("required_columns", ())) != TABLE_COLUMNS[table_id]:
            raise CompletionEvidenceError(f"{table_id}: required columns changed")
    if set(payload.get("allowed_split_roles", ())) != _ALLOWED_SPLIT_ROLES:
        raise CompletionEvidenceError("completion-evidence split roles changed")
    if set(payload.get("allowed_species", ())) != _ALLOWED_SPECIES:
        raise CompletionEvidenceError("completion-evidence species scope changed")
    if set(payload.get("allowed_biological_systems", ())) != _ALLOWED_SYSTEMS:
        raise CompletionEvidenceError("completion-evidence biological systems changed")
    policy = payload.get("policy")
    frozen = payload.get("frozen_evaluation")
    if not isinstance(policy, Mapping) or not isinstance(frozen, Mapping):
        raise CompletionEvidenceError("completion-evidence policy is malformed")
    forbidden_true = (
        "automatic_parameter_activation",
        "automatic_state_coupling",
        "predictive_authority",
    )
    if any(policy.get(key) is not False for key in forbidden_true):
        raise CompletionEvidenceError("completion-evidence contract escaped fail-closed policy")
    if (
        frozen.get("donor_id_may_cross_split_roles") is not False
        or frozen.get("post_freeze_parameter_refit_allowed") is not False
        or frozen.get("automatic_pass_fail_assignment") is not False
    ):
        raise CompletionEvidenceError("completion-evidence frozen evaluation changed")
    return payload


def _required(row: Mapping[str, str], field: str, *, label: str) -> str:
    value = row.get(field)
    if value is None or not value.strip() or value.strip().lower() == _NULL_TOKEN:
        raise CompletionEvidenceError(f"{label}: {field} must be explicit")
    return value.strip()


def _nullable(row: Mapping[str, str], field: str, *, label: str) -> str | None:
    value = row.get(field)
    if value is None or not value.strip():
        raise CompletionEvidenceError(
            f"{label}: missing optional values must use canonical null"
        )
    clean = value.strip()
    return None if clean.lower() == _NULL_TOKEN else clean


def _number(
    row: Mapping[str, str],
    field: str,
    *,
    label: str,
    nonnegative: bool = False,
) -> float:
    raw = _required(row, field, label=label)
    try:
        value = float(raw)
    except ValueError as exc:
        raise CompletionEvidenceError(f"{label}: {field} must be numeric") from exc
    if not math.isfinite(value) or (nonnegative and value < 0.0):
        raise CompletionEvidenceError(f"{label}: {field} is outside its numeric domain")
    return value


def _nullable_number(
    row: Mapping[str, str],
    field: str,
    *,
    label: str,
    nonnegative: bool = False,
) -> float | None:
    raw = _nullable(row, field, label=label)
    if raw is None:
        return None
    try:
        value = float(raw)
    except ValueError as exc:
        raise CompletionEvidenceError(f"{label}: {field} must be numeric or null") from exc
    if not math.isfinite(value) or (nonnegative and value < 0.0):
        raise CompletionEvidenceError(f"{label}: {field} is outside its numeric domain")
    return value


def _read_table(path: Path, table_id: str) -> tuple[dict[str, str], ...]:
    if not path.is_file():
        raise CompletionEvidenceError(f"{table_id}: required delivery file is absent")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != TABLE_COLUMNS[table_id]:
            raise CompletionEvidenceError(f"{table_id}: CSV header does not match contract")
        rows = tuple(dict(row) for row in reader)
    if not rows:
        raise CompletionEvidenceError(f"{table_id}: delivery must contain raw records")
    return rows


def _common(row: Mapping[str, str], *, label: str) -> tuple[str, str, str, str]:
    record_id = _required(row, "record_id", label=label)
    donor_id = _required(row, "donor_id", label=label)
    split_role = _required(row, "split_role", label=label)
    source_study_id = _required(row, "source_study_id", label=label)
    species = _required(row, "species", label=label)
    biological_system = _required(row, "biological_system", label=label)
    if split_role not in _ALLOWED_SPLIT_ROLES:
        raise CompletionEvidenceError(f"{label}: unsupported split_role")
    if species not in _ALLOWED_SPECIES:
        raise CompletionEvidenceError(f"{label}: non-human evidence is not eligible")
    if biological_system not in _ALLOWED_SYSTEMS:
        raise CompletionEvidenceError(f"{label}: biological_system is outside PHH scope")
    _required(row, "source_locator", label=label)
    _required(row, "biological_replicate_id", label=label)
    return record_id, source_study_id, donor_id, split_role


def _assess_p53(rows: tuple[dict[str, str], ...]) -> tuple[int, int]:
    groups: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for index, row in enumerate(rows, start=2):
        label = f"p53_ddr_trajectory row {index}"
        _, source, donor, _ = _common(row, label=label)
        protocol = _required(row, "protocol_id", label=label)
        replicate = _required(row, "biological_replicate_id", label=label)
        _required(row, "culture_format", label=label)
        _required(row, "damage_agent", label=label)
        _number(row, "damage_dose_value", label=label, nonnegative=True)
        _required(row, "damage_dose_unit", label=label)
        _number(row, "exposure_start_h", label=label, nonnegative=True)
        _nullable_number(row, "washout_time_h", label=label, nonnegative=True)
        _number(row, "time_h", label=label, nonnegative=True)
        analyte = _required(row, "analyte_id", label=label)
        level = _required(row, "analyte_level", label=label)
        endpoint = _required(row, "endpoint_class", label=label)
        if analyte not in _P53_ANALYTES and level != "fate_or_recovery_readout":
            raise CompletionEvidenceError(f"{label}: unsupported p53 analyte")
        if level not in _P53_LEVELS or endpoint not in _P53_ENDPOINTS:
            raise CompletionEvidenceError(f"{label}: p53 evidence class changed")
        for field in (
            "compartment",
            "assay",
            "raw_unit",
            "normalization_denominator",
        ):
            _required(row, field, label=label)
        _number(row, "raw_value", label=label)
        uncertainty_type = _nullable(row, "uncertainty_type", label=label)
        uncertainty_value = _nullable_number(
            row, "uncertainty_value", label=label, nonnegative=True
        )
        if (uncertainty_type is None) != (uncertainty_value is None):
            raise CompletionEvidenceError(f"{label}: uncertainty fields must be paired")
        sample_size = _number(row, "sample_size", label=label, nonnegative=True)
        if not sample_size.is_integer() or sample_size < 1:
            raise CompletionEvidenceError(f"{label}: sample_size must be a positive integer")
        _nullable_number(row, "recovery_followup_h", label=label, nonnegative=True)
        _nullable(row, "independent_review_id", label=label)
        _nullable(row, "limitations", label=label)
        groups[(source, donor, replicate, protocol)].append(row)

    complete = 0
    for group in groups.values():
        times = {float(row["time_h"]) for row in group}
        analytes = {row["analyte_id"] for row in group}
        endpoints = {row["endpoint_class"] for row in group}
        if len(times) >= 3 and _P53_ANALYTES <= analytes and _P53_ENDPOINTS <= endpoints:
            complete += 1
    return len(groups), complete


def _assess_clonal(rows: tuple[dict[str, str], ...]) -> tuple[int, int]:
    groups: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for index, row in enumerate(rows, start=2):
        label = f"clonal_population_trajectory row {index}"
        _, source, donor, _ = _common(row, label=label)
        clone_id = _required(row, "clone_id", label=label)
        replicate = _required(row, "biological_replicate_id", label=label)
        for field in (
            "culture_or_tissue_context",
            "lineage_marker",
            "genotype",
            "ploidy",
            "injury_context",
            "nutrient_context",
            "zonation_context",
            "niche_context",
            "spatial_reference_frame",
            "raw_unit",
            "measurement_operator",
        ):
            _required(row, field, label=label)
        for field in ("position_x_um", "position_y_um", "position_z_um"):
            _number(row, field, label=label)
        _number(row, "time_h", label=label, nonnegative=True)
        endpoint = _required(row, "endpoint", label=label)
        if endpoint not in _CLONAL_ENDPOINTS:
            raise CompletionEvidenceError(f"{label}: unsupported clonal endpoint")
        _number(row, "raw_value", label=label)
        uncertainty_type = _nullable(row, "uncertainty_type", label=label)
        uncertainty_value = _nullable_number(
            row, "uncertainty_value", label=label, nonnegative=True
        )
        if (uncertainty_type is None) != (uncertainty_value is None):
            raise CompletionEvidenceError(f"{label}: uncertainty fields must be paired")
        _nullable(row, "independent_review_id", label=label)
        _nullable(row, "limitations", label=label)
        groups[(source, donor, replicate, clone_id)].append(row)

    complete = 0
    for group in groups.values():
        times = {float(row["time_h"]) for row in group}
        endpoints = {row["endpoint"] for row in group}
        if len(times) >= 2 and _CLONAL_ENDPOINTS <= endpoints:
            complete += 1
    return len(groups), complete


def _assess_capability(rows: tuple[dict[str, str], ...]) -> tuple[int, int]:
    capability_slots = _capability_slots()
    covered: set[tuple[str, str]] = set()
    heldout: set[tuple[str, str]] = set()
    for index, row in enumerate(rows, start=2):
        label = f"capability_parameter_observation row {index}"
        _, _, _, split_role = _common(row, label=label)
        key = (
            _required(row, "capability_id", label=label),
            _required(row, "parameter_slot_id", label=label),
        )
        if key not in capability_slots:
            raise CompletionEvidenceError(f"{label}: unknown capability parameter slot")
        expected_quantity, expected_unit = capability_slots[key]
        if _required(row, "quantity", label=label) != expected_quantity:
            raise CompletionEvidenceError(f"{label}: quantity does not match capability atlas")
        if _required(row, "raw_unit", label=label) != expected_unit:
            raise CompletionEvidenceError(f"{label}: unit does not match capability atlas")
        for field in (
            "doi",
            "culture_format",
            "compartment",
            "assay",
            "normalization_denominator",
            "measurement_time",
            "perturbation_context",
        ):
            _required(row, field, label=label)
        _number(row, "raw_value", label=label)
        uncertainty_type = _nullable(row, "uncertainty_type", label=label)
        uncertainty_value = _nullable_number(
            row, "uncertainty_value", label=label, nonnegative=True
        )
        if (uncertainty_type is None) != (uncertainty_value is None):
            raise CompletionEvidenceError(f"{label}: uncertainty fields must be paired")
        independent_validation_id = _nullable(
            row, "independent_validation_id", label=label
        )
        _nullable(row, "limitations", label=label)
        covered.add(key)
        if split_role == "independent_heldout" and independent_validation_id:
            heldout.add(key)
    return len(covered), len(covered & heldout)


def completion_evidence_bundle_intake_snapshot(
    path: Path = DEFAULT_DELIVERY_PATH,
) -> dict[str, object]:
    contract = load_completion_evidence_contract()
    capability_slots = _capability_slots()
    contract_sha256 = _sha256(CONTRACT_PATH)
    if not path.exists():
        payload = {
            "version": INTAKE_VERSION,
            "contract_id": CONTRACT_ID,
            "status": "awaiting_external_completion_evidence_bundle",
            "delivery_path": _display_path(path),
            "delivery_present": False,
            "contract_path": _display_path(CONTRACT_PATH),
            "contract_sha256": contract_sha256,
            "target_gap_ids": tuple(
                gap_id for table_id in TABLE_IDS for gap_id in TABLE_TARGETS[table_id]
            ),
            "tables": tuple(
                {
                    "id": table_id,
                    "file": TABLE_FILES[table_id],
                    "record_count": 0,
                    "structurally_complete_item_count": 0,
                }
                for table_id in TABLE_IDS
            ),
            "summary": {
                "required_table_count": len(TABLE_IDS),
                "delivered_table_count": 0,
                "record_count": 0,
                "structurally_complete_item_count": 0,
                "covered_capability_slot_count": 0,
                "required_capability_slot_count": len(capability_slots),
                "heldout_capability_slot_count": 0,
                "quantitatively_authorized_item_count": 0,
            },
            "automatic_parameter_activation": False,
            "automatic_state_coupling": False,
            "predictive_authority": False,
            "blockers": (
                "No donor-resolved completion-evidence bundle has been delivered.",
                "Structural intake cannot activate parameters, cell state, or prediction.",
            ),
        }
        validate_completion_evidence_bundle_intake_snapshot(payload)
        return payload

    if not path.is_dir():
        raise CompletionEvidenceError("completion-evidence delivery must be a directory")

    table_rows = {
        table_id: _read_table(path / TABLE_FILES[table_id], table_id)
        for table_id in TABLE_IDS
    }
    seen_record_ids: set[str] = set()
    donor_splits: dict[tuple[str, str], set[str]] = defaultdict(set)
    for table_id, rows in table_rows.items():
        for index, row in enumerate(rows, start=2):
            label = f"{table_id} row {index}"
            record_id, source, donor, split = _common(row, label=label)
            if record_id in seen_record_ids:
                raise CompletionEvidenceError(
                    f"{label}: record_id must be unique across the bundle"
                )
            seen_record_ids.add(record_id)
            donor_splits[(source, donor)].add(split)
    if any(len(splits) != 1 for splits in donor_splits.values()):
        raise CompletionEvidenceError("a donor crossed calibration or validation splits")

    p53_group_count, p53_complete_count = _assess_p53(
        table_rows["p53_ddr_trajectory"]
    )
    clone_group_count, clone_complete_count = _assess_clonal(
        table_rows["clonal_population_trajectory"]
    )
    capability_covered, capability_heldout = _assess_capability(
        table_rows["capability_parameter_observation"]
    )
    tables = (
        {
            "id": "p53_ddr_trajectory",
            "file": TABLE_FILES["p53_ddr_trajectory"],
            "artifact_sha256": _sha256(path / TABLE_FILES["p53_ddr_trajectory"]),
            "record_count": len(table_rows["p53_ddr_trajectory"]),
            "trajectory_group_count": p53_group_count,
            "structurally_complete_item_count": p53_complete_count,
        },
        {
            "id": "clonal_population_trajectory",
            "file": TABLE_FILES["clonal_population_trajectory"],
            "artifact_sha256": _sha256(
                path / TABLE_FILES["clonal_population_trajectory"]
            ),
            "record_count": len(table_rows["clonal_population_trajectory"]),
            "trajectory_group_count": clone_group_count,
            "structurally_complete_item_count": clone_complete_count,
        },
        {
            "id": "capability_parameter_observation",
            "file": TABLE_FILES["capability_parameter_observation"],
            "artifact_sha256": _sha256(
                path / TABLE_FILES["capability_parameter_observation"]
            ),
            "record_count": len(table_rows["capability_parameter_observation"]),
            "structurally_complete_item_count": capability_covered,
            "heldout_supported_item_count": capability_heldout,
        },
    )
    blockers = [
        "Every accepted record still requires manual primary-source review.",
        "No structurally accepted record automatically activates a parameter, state coupling, or prediction.",
    ]
    if p53_complete_count == 0:
        blockers.append("No p53 protocol covers the required analytes, fates, and time points.")
    if clone_complete_count == 0:
        blockers.append("No clone trajectory covers both population and fate endpoints over time.")
    if capability_covered != len(capability_slots):
        blockers.append("The capability atlas is not fully covered by exact-slot observations.")
    payload = {
        "version": INTAKE_VERSION,
        "contract_id": CONTRACT_ID,
        "status": "delivery_structurally_audited_manual_review_required",
        "delivery_path": _display_path(path),
        "delivery_present": True,
        "contract_path": _display_path(CONTRACT_PATH),
        "contract_sha256": contract_sha256,
        "target_gap_ids": tuple(
            gap_id for table_id in TABLE_IDS for gap_id in TABLE_TARGETS[table_id]
        ),
        "tables": tables,
        "summary": {
            "required_table_count": len(TABLE_IDS),
            "delivered_table_count": len(TABLE_IDS),
            "record_count": sum(len(rows) for rows in table_rows.values()),
            "structurally_complete_item_count": (
                p53_complete_count + clone_complete_count + capability_covered
            ),
            "covered_capability_slot_count": capability_covered,
            "required_capability_slot_count": len(capability_slots),
            "heldout_capability_slot_count": capability_heldout,
            "quantitatively_authorized_item_count": 0,
        },
        "automatic_parameter_activation": False,
        "automatic_state_coupling": False,
        "predictive_authority": False,
        "blockers": tuple(blockers),
    }
    validate_completion_evidence_bundle_intake_snapshot(payload)
    return payload


def validate_completion_evidence_bundle_intake_snapshot(
    payload: Mapping[str, object],
) -> None:
    capability_slots = _capability_slots()
    if (
        payload.get("version") != INTAKE_VERSION
        or payload.get("contract_id") != CONTRACT_ID
    ):
        raise CompletionEvidenceError("completion-evidence intake identity changed")
    if (
        payload.get("automatic_parameter_activation") is not False
        or payload.get("automatic_state_coupling") is not False
        or payload.get("predictive_authority") is not False
    ):
        raise CompletionEvidenceError("completion evidence escaped fail-closed policy")
    if tuple(payload.get("target_gap_ids", ())) != tuple(
        gap_id for table_id in TABLE_IDS for gap_id in TABLE_TARGETS[table_id]
    ):
        raise CompletionEvidenceError("completion-evidence target gaps changed")
    tables = payload.get("tables")
    summary = payload.get("summary")
    if not isinstance(tables, (list, tuple)) or not isinstance(summary, Mapping):
        raise CompletionEvidenceError("completion-evidence snapshot is malformed")
    if tuple(
        table.get("id") if isinstance(table, Mapping) else None for table in tables
    ) != TABLE_IDS:
        raise CompletionEvidenceError("completion-evidence snapshot tables changed")
    if summary.get("required_table_count") != len(TABLE_IDS):
        raise CompletionEvidenceError("completion-evidence table count is stale")
    if summary.get("required_capability_slot_count") != len(capability_slots):
        raise CompletionEvidenceError("capability slot count is stale")
    if summary.get("quantitatively_authorized_item_count") != 0:
        raise CompletionEvidenceError("completion evidence gained numerical authority")
