"""Fail-closed intake for the active network's 36 x 12 evidence matrix.

Rows preserve source-reported values and context. They can establish structural
coverage, but they never mutate the reaction atlas, convert units, fit a rate
law, or authorize quantitative execution.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cell_engine.core.serialization import to_plain
from cell_engine.stochastic.integrated_cell import build_integrated_hepatocyte_network
from cell_engine.stochastic.signaling import HormoneState
from cell_engine.validation.reaction_evidence_atlas import (
    REACTION_EVIDENCE_SLOT_SPECS,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "evidence_intake"
    / "phh_reaction_evidence_contract.v1.json"
)
DEFAULT_EVIDENCE_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "evidence_intake"
    / "incoming"
    / "phh_reaction_evidence"
    / "latest"
    / "phh_reaction_evidence.csv"
)
CONTRACT_SCHEMA_VERSION = "cell.phh-reaction-evidence-contract.v1"
INTAKE_VERSION = "phh_reaction_evidence_intake_v1"
REACTION_GATE_VERSION = "phh_reaction_evidence_gate_v1"

_NULL_TOKEN = "null"
_NUMBER_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
_INTEGER_RE = re.compile(r"^\d+$")
_ALLOWED_SPLITS = frozenset(
    {"calibration", "internal_validation", "independent_heldout"}
)
_ALLOWED_SOURCE_TYPES = frozenset(
    {
        "primary_experiment",
        "primary_kinetic_database_record",
        "primary_model_with_traceable_measurement",
        "curated_database_with_primary_locator",
    }
)
_ALLOWED_CONTEXT_ROLES = frozenset(
    {
        "direct_healthy_phh",
        "human_liver_bridge",
        "purified_human_enzyme_candidate",
        "independent_healthy_phh_validation",
    }
)
_ALLOWED_VALUE_KINDS = frozenset(
    {
        "identity",
        "location",
        "equation",
        "numeric",
        "regulatory_model",
        "validation_result",
    }
)
_ALLOWED_REVIEW_STATUSES = frozenset({"pending", "verified"})
_SLOT_BY_ID = {
    slot_id: {"quantity": quantity, "unit": unit, "context": context}
    for slot_id, quantity, unit, context in REACTION_EVIDENCE_SLOT_SPECS
}
_NUMERIC_SLOTS = frozenset(
    {
        "km",
        "kcat",
        "vmax",
        "active_enzyme_abundance",
        "assay_temperature",
        "assay_ph",
        "intracellular_flux",
    }
)
_KINETIC_ASSAY_SLOTS = frozenset({"km", "kcat", "ki_or_allostery", "vmax"})
_DIRECT_PHH_SLOTS = frozenset(
    {"vmax", "active_enzyme_abundance", "intracellular_flux"}
)
_VALUE_KINDS_BY_SLOT = {
    "biochemical_identity": frozenset({"identity"}),
    "biological_compartment": frozenset({"location"}),
    "symbolic_rate_law": frozenset({"equation"}),
    "km": frozenset({"numeric"}),
    "kcat": frozenset({"numeric"}),
    "ki_or_allostery": frozenset({"numeric", "regulatory_model"}),
    "vmax": frozenset({"numeric"}),
    "active_enzyme_abundance": frozenset({"numeric"}),
    "assay_temperature": frozenset({"numeric"}),
    "assay_ph": frozenset({"numeric"}),
    "intracellular_flux": frozenset({"numeric"}),
    "heldout_validation": frozenset({"validation_result"}),
}


class ReactionEvidenceIntakeError(ValueError):
    """Raised when reaction evidence violates the versioned intake contract."""


@dataclass(frozen=True)
class ReactionEvidenceIntakeRecord:
    record_id: str
    reaction_id: str
    slot_id: str
    parameter_or_entity_id: str
    split_role: str
    donor_id: str
    source_study_id: str
    source_locator: str
    source_type: str
    species: str
    biological_system: str
    culture_format: str
    health_state: str
    biological_replicate_id: str
    assay: str
    biological_compartment: str
    membrane_side: str
    enzyme_gene_symbol: str
    protein_isoform: str
    reaction_direction: str
    substrate_product_effector_context: str
    cofactor_context: str
    active_state_context: str
    value_kind: str
    reported_value: str
    reported_unit: str
    canonical_unit_target: str
    reported_statistic: str
    sample_size: int
    manual_primary_source_review_status: str
    context_role: str
    notes: str
    assay_temperature_c: float | None
    assay_ph: float | None
    uncertainty_lower: float | None
    uncertainty_upper: float | None
    uncertainty_unit: str | None
    uncertainty_type: str | None
    equation_machine_readable: str | None
    raw_to_canonical_conversion_reference: str | None
    validation_model_artifact_sha256: str | None
    validation_prediction_id: str | None
    validation_observation_id: str | None
    frozen_before_heldout_access: bool | None
    censoring_or_missingness: str | None

    @property
    def donor_key(self) -> tuple[str, str]:
        return self.source_study_id, self.donor_id


@dataclass(frozen=True)
class ReactionEvidenceAssessment:
    reaction_id: str
    record_count: int
    covered_slot_ids: tuple[str, ...]
    structurally_ready_slot_ids: tuple[str, ...]
    missing_slot_ids: tuple[str, ...]
    structurally_complete: bool
    atlas_mutation_allowed: bool
    quantitative_execution_allowed: bool
    predictive_execution_allowed: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class ReactionEvidenceDataset:
    version: str
    contract_id: str
    delivery_path: str
    artifact_sha256: str
    contract_sha256: str
    records: tuple[ReactionEvidenceIntakeRecord, ...]


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


def _active_reaction_ids() -> frozenset[str]:
    network = build_integrated_hepatocyte_network(HormoneState())
    return frozenset(reaction.id for reaction in network.reactions)


def load_reaction_evidence_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ReactionEvidenceIntakeError("reaction-evidence contract must be one object")
    if payload.get("schema_version") != CONTRACT_SCHEMA_VERSION:
        raise ReactionEvidenceIntakeError("unsupported reaction-evidence contract schema")
    required = payload.get("required_columns")
    conditional = payload.get("conditional_columns")
    gate = payload.get("reaction_gate")
    policy = payload.get("policy")
    if not all(
        (
            isinstance(required, list),
            isinstance(conditional, list),
            isinstance(gate, dict),
            isinstance(policy, dict),
        )
    ):
        raise ReactionEvidenceIntakeError("reaction-evidence contract is malformed")
    required_ids = tuple(
        str(item.get("id", "")) for item in required if isinstance(item, dict)
    )
    conditional_ids = tuple(
        str(item.get("id", "")) for item in conditional if isinstance(item, dict)
    )
    if (
        len(required_ids) != 32
        or len(set(required_ids)) != 32
        or not all(required_ids)
        or len(conditional_ids) != 13
        or len(set(conditional_ids)) != 13
        or not all(conditional_ids)
    ):
        raise ReactionEvidenceIntakeError("reaction-evidence field contract changed")
    if payload.get("active_reaction_count") != 36:
        raise ReactionEvidenceIntakeError("reaction count contract changed")
    if payload.get("slot_count_per_reaction") != 12:
        raise ReactionEvidenceIntakeError("reaction slot-count contract changed")
    if payload.get("canonical_null_token") != _NULL_TOKEN:
        raise ReactionEvidenceIntakeError("reaction-evidence null policy changed")
    if set(payload.get("allowed_split_roles", ())) != _ALLOWED_SPLITS:
        raise ReactionEvidenceIntakeError("reaction-evidence split roles changed")
    if set(payload.get("allowed_source_types", ())) != _ALLOWED_SOURCE_TYPES:
        raise ReactionEvidenceIntakeError("reaction-evidence source types changed")
    if set(payload.get("allowed_context_roles", ())) != _ALLOWED_CONTEXT_ROLES:
        raise ReactionEvidenceIntakeError("reaction-evidence context roles changed")
    if set(payload.get("allowed_value_kinds", ())) != _ALLOWED_VALUE_KINDS:
        raise ReactionEvidenceIntakeError("reaction-evidence value kinds changed")
    if (
        set(payload.get("allowed_manual_review_statuses", ()))
        != _ALLOWED_REVIEW_STATUSES
    ):
        raise ReactionEvidenceIntakeError("reaction-evidence review states changed")
    required_true = {
        "all_twelve_slot_ids_required",
        "slot_specific_context_required",
        "exact_active_reaction_id_required",
        "donor_disjoint_validation_required",
        "independent_heldout_study_required",
        "frozen_model_before_heldout_access_required",
        "manual_semantic_adjudication_required",
    }
    required_false = {
        "automatic_unit_conversion",
        "automatic_parameter_fitting",
        "automatic_atlas_mutation",
        "automatic_reaction_activation",
        "automatic_cell_state_coupling",
    }
    if (
        gate.get("version") != REACTION_GATE_VERSION
        or any(gate.get(key) is not True for key in required_true)
        or any(gate.get(key) is not False for key in required_false)
    ):
        raise ReactionEvidenceIntakeError("reaction gate escaped fail-closed policy")
    if policy.get("manual_primary_source_review_required") is not True or any(
        policy.get(key) is not False
        for key in (
            "cross_species_transfer_allowed",
            "cell_line_to_healthy_phh_transfer_allowed",
            "reported_mean_may_replace_raw_donor_records",
            "missing_slot_means_zero",
            "database_presence_is_authority",
            "visual_or_legacy_runtime_value_is_measurement",
            "automatic_parameter_activation",
            "automatic_predictive_execution",
        )
    ):
        raise ReactionEvidenceIntakeError("reaction-evidence policy escaped fail-closed state")
    return payload


def _required_text(row: dict[str, str], field: str, row_number: int) -> str:
    value = row[field].strip()
    if not value or value.lower() == _NULL_TOKEN:
        raise ReactionEvidenceIntakeError(f"row {row_number}: {field} is required")
    return value


def _optional_text(row: dict[str, str], field: str) -> str | None:
    value = row[field].strip()
    return None if not value or value.lower() == _NULL_TOKEN else value


def _optional_number(row: dict[str, str], field: str, row_number: int) -> float | None:
    token = row[field].strip()
    if not token or token.lower() == _NULL_TOKEN:
        return None
    if not _NUMBER_RE.fullmatch(token):
        raise ReactionEvidenceIntakeError(
            f"row {row_number}: {field} must be one finite number"
        )
    value = float(token)
    if not math.isfinite(value):
        raise ReactionEvidenceIntakeError(f"row {row_number}: {field} must be finite")
    return value


def _optional_boolean(row: dict[str, str], field: str, row_number: int) -> bool | None:
    token = row[field].strip().lower()
    if not token or token == _NULL_TOKEN:
        return None
    if token not in {"true", "false"}:
        raise ReactionEvidenceIntakeError(
            f"row {row_number}: {field} must be true, false, or null"
        )
    return token == "true"


def _record(
    row: dict[str, str],
    row_number: int,
    active_reaction_ids: frozenset[str],
) -> ReactionEvidenceIntakeRecord:
    reaction_id = _required_text(row, "reaction_id", row_number)
    if reaction_id not in active_reaction_ids:
        raise ReactionEvidenceIntakeError(
            f"row {row_number}: reaction_id is not in the active network"
        )
    slot_id = _required_text(row, "slot_id", row_number)
    if slot_id not in _SLOT_BY_ID:
        raise ReactionEvidenceIntakeError(
            f"row {row_number}: unknown reaction evidence slot {slot_id!r}"
        )
    split_role = _required_text(row, "split_role", row_number)
    if split_role not in _ALLOWED_SPLITS:
        raise ReactionEvidenceIntakeError(
            f"row {row_number}: unsupported split_role {split_role!r}"
        )
    source_type = _required_text(row, "source_type", row_number)
    if source_type not in _ALLOWED_SOURCE_TYPES:
        raise ReactionEvidenceIntakeError(
            f"row {row_number}: unsupported source_type {source_type!r}"
        )
    if _required_text(row, "species", row_number) != "Homo sapiens":
        raise ReactionEvidenceIntakeError(
            f"row {row_number}: non-human evidence cannot enter PHH reaction intake"
        )
    context_role = _required_text(row, "context_role", row_number)
    if context_role not in _ALLOWED_CONTEXT_ROLES:
        raise ReactionEvidenceIntakeError(
            f"row {row_number}: unsupported context_role {context_role!r}"
        )
    biological_system = _required_text(row, "biological_system", row_number)
    normalized_system = biological_system.lower()
    if "cell_line" in normalized_system:
        raise ReactionEvidenceIntakeError(
            f"row {row_number}: cell-line evidence cannot enter PHH reaction intake"
        )
    if context_role in {"direct_healthy_phh", "independent_healthy_phh_validation"}:
        if "primary_human_hepatocyte" not in normalized_system:
            raise ReactionEvidenceIntakeError(
                f"row {row_number}: direct PHH context lacks primary human hepatocytes"
            )
    elif context_role == "human_liver_bridge" and "human_liver" not in normalized_system:
        raise ReactionEvidenceIntakeError(
            f"row {row_number}: human-liver bridge context is inconsistent"
        )
    elif context_role == "purified_human_enzyme_candidate" and not any(
        token in normalized_system
        for token in ("purified_human_enzyme", "recombinant_human_enzyme")
    ):
        raise ReactionEvidenceIntakeError(
            f"row {row_number}: purified-human-enzyme context is inconsistent"
        )
    value_kind = _required_text(row, "value_kind", row_number)
    if value_kind not in _ALLOWED_VALUE_KINDS:
        raise ReactionEvidenceIntakeError(
            f"row {row_number}: unsupported value_kind {value_kind!r}"
        )
    if value_kind not in _VALUE_KINDS_BY_SLOT[slot_id]:
        raise ReactionEvidenceIntakeError(
            f"row {row_number}: value_kind is incompatible with {slot_id}"
        )
    reported_value = _required_text(row, "reported_value", row_number)
    if slot_id in _NUMERIC_SLOTS:
        if not _NUMBER_RE.fullmatch(reported_value) or not math.isfinite(
            float(reported_value)
        ):
            raise ReactionEvidenceIntakeError(
                f"row {row_number}: {slot_id} requires a finite numeric reported_value"
            )
    canonical_unit = _required_text(row, "canonical_unit_target", row_number)
    if canonical_unit != _SLOT_BY_ID[slot_id]["unit"]:
        raise ReactionEvidenceIntakeError(
            f"row {row_number}: canonical unit target does not match {slot_id}"
        )
    sample_size_token = _required_text(row, "sample_size", row_number)
    if not _INTEGER_RE.fullmatch(sample_size_token):
        raise ReactionEvidenceIntakeError(
            f"row {row_number}: sample_size must be a non-negative integer"
        )
    review_status = _required_text(
        row, "manual_primary_source_review_status", row_number
    )
    if review_status not in _ALLOWED_REVIEW_STATUSES:
        raise ReactionEvidenceIntakeError(
            f"row {row_number}: unsupported manual review status"
        )
    uncertainty_lower = _optional_number(row, "uncertainty_lower", row_number)
    uncertainty_upper = _optional_number(row, "uncertainty_upper", row_number)
    uncertainty_unit = _optional_text(row, "uncertainty_unit")
    uncertainty_type = _optional_text(row, "uncertainty_type")
    uncertainty_values_present = (
        uncertainty_lower is not None or uncertainty_upper is not None
    )
    if uncertainty_values_present and not all(
        value is not None
        for value in (
            uncertainty_lower,
            uncertainty_upper,
            uncertainty_unit,
            uncertainty_type,
        )
    ):
        raise ReactionEvidenceIntakeError(
            f"row {row_number}: uncertainty bounds, unit, and type must be supplied together"
        )
    if (
        uncertainty_lower is not None
        and uncertainty_upper is not None
        and uncertainty_lower > uncertainty_upper
    ):
        raise ReactionEvidenceIntakeError(
            f"row {row_number}: uncertainty lower bound exceeds upper bound"
        )
    equation = _optional_text(row, "equation_machine_readable")
    if slot_id == "symbolic_rate_law" and equation is None:
        raise ReactionEvidenceIntakeError(
            f"row {row_number}: symbolic_rate_law requires a machine-readable equation"
        )
    frozen = _optional_boolean(row, "frozen_before_heldout_access", row_number)
    validation_digest = _optional_text(row, "validation_model_artifact_sha256")
    validation_prediction = _optional_text(row, "validation_prediction_id")
    validation_observation = _optional_text(row, "validation_observation_id")
    if slot_id == "heldout_validation":
        if (
            split_role != "independent_heldout"
            or context_role != "independent_healthy_phh_validation"
            or frozen is not True
            or not validation_digest
            or not re.fullmatch(r"[0-9a-f]{64}", validation_digest)
            or not validation_prediction
            or not validation_observation
        ):
            raise ReactionEvidenceIntakeError(
                f"row {row_number}: heldout validation lacks a frozen independent PHH artifact"
            )
    elif split_role == "independent_heldout":
        raise ReactionEvidenceIntakeError(
            f"row {row_number}: independent_heldout is reserved for heldout_validation"
        )
    return ReactionEvidenceIntakeRecord(
        record_id=_required_text(row, "record_id", row_number),
        reaction_id=reaction_id,
        slot_id=slot_id,
        parameter_or_entity_id=_required_text(
            row, "parameter_or_entity_id", row_number
        ),
        split_role=split_role,
        donor_id=_required_text(row, "donor_id", row_number),
        source_study_id=_required_text(row, "source_study_id", row_number),
        source_locator=_required_text(row, "source_locator", row_number),
        source_type=source_type,
        species="Homo sapiens",
        biological_system=biological_system,
        culture_format=_required_text(row, "culture_format", row_number),
        health_state=_required_text(row, "health_state", row_number),
        biological_replicate_id=_required_text(
            row, "biological_replicate_id", row_number
        ),
        assay=_required_text(row, "assay", row_number),
        biological_compartment=_required_text(
            row, "biological_compartment", row_number
        ),
        membrane_side=_required_text(row, "membrane_side", row_number),
        enzyme_gene_symbol=_required_text(
            row, "enzyme_gene_symbol", row_number
        ),
        protein_isoform=_required_text(row, "protein_isoform", row_number),
        reaction_direction=_required_text(
            row, "reaction_direction", row_number
        ),
        substrate_product_effector_context=_required_text(
            row, "substrate_product_effector_context", row_number
        ),
        cofactor_context=_required_text(row, "cofactor_context", row_number),
        active_state_context=_required_text(
            row, "active_state_context", row_number
        ),
        value_kind=value_kind,
        reported_value=reported_value,
        reported_unit=_required_text(row, "reported_unit", row_number),
        canonical_unit_target=canonical_unit,
        reported_statistic=_required_text(
            row, "reported_statistic", row_number
        ),
        sample_size=int(sample_size_token),
        manual_primary_source_review_status=review_status,
        context_role=context_role,
        notes=_required_text(row, "notes", row_number),
        assay_temperature_c=_optional_number(
            row, "assay_temperature_c", row_number
        ),
        assay_ph=_optional_number(row, "assay_ph", row_number),
        uncertainty_lower=uncertainty_lower,
        uncertainty_upper=uncertainty_upper,
        uncertainty_unit=uncertainty_unit,
        uncertainty_type=uncertainty_type,
        equation_machine_readable=equation,
        raw_to_canonical_conversion_reference=_optional_text(
            row, "raw_to_canonical_conversion_reference"
        ),
        validation_model_artifact_sha256=validation_digest,
        validation_prediction_id=validation_prediction,
        validation_observation_id=validation_observation,
        frozen_before_heldout_access=frozen,
        censoring_or_missingness=_optional_text(row, "censoring_or_missingness"),
    )


def load_reaction_evidence_dataset(
    path: Path = DEFAULT_EVIDENCE_PATH,
) -> ReactionEvidenceDataset:
    contract = load_reaction_evidence_contract()
    expected_fields = tuple(
        item["id"]
        for group in ("required_columns", "conditional_columns")
        for item in contract[group]
    )
    if not path.exists():
        raise ReactionEvidenceIntakeError(
            f"reaction-evidence delivery not found: {_display_path(path)}"
        )
    active_reaction_ids = _active_reaction_ids()
    if len(active_reaction_ids) != 36:
        raise ReactionEvidenceIntakeError("active reaction network changed")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != expected_fields:
            raise ReactionEvidenceIntakeError(
                "reaction-evidence CSV header must exactly match the versioned contract"
            )
        records = tuple(
            _record(row, index, active_reaction_ids)
            for index, row in enumerate(reader, start=2)
        )
    if not records:
        raise ReactionEvidenceIntakeError("reaction-evidence delivery contains no records")
    record_ids = [record.record_id for record in records]
    if len(set(record_ids)) != len(record_ids):
        raise ReactionEvidenceIntakeError(
            "reaction-evidence record_id values must be unique"
        )
    donor_splits: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    study_splits: defaultdict[str, set[str]] = defaultdict(set)
    for record in records:
        donor_splits[record.donor_key].add(record.split_role)
        study_splits[record.source_study_id].add(record.split_role)
    leaking_donors = [key for key, splits in donor_splits.items() if len(splits) > 1]
    if leaking_donors:
        raise ReactionEvidenceIntakeError(
            f"reaction-evidence donor crosses split roles: {leaking_donors!r}"
        )
    leaking_studies = [
        study
        for study, splits in study_splits.items()
        if "independent_heldout" in splits and len(splits) > 1
    ]
    if leaking_studies:
        raise ReactionEvidenceIntakeError(
            f"independent-heldout study crosses development splits: {leaking_studies!r}"
        )
    return ReactionEvidenceDataset(
        version=INTAKE_VERSION,
        contract_id=str(contract["contract_id"]),
        delivery_path=_display_path(path),
        artifact_sha256=_sha256(path),
        contract_sha256=_sha256(CONTRACT_PATH),
        records=records,
    )


def _record_is_structurally_ready(record: ReactionEvidenceIntakeRecord) -> bool:
    if record.manual_primary_source_review_status != "verified":
        return False
    if record.slot_id in _KINETIC_ASSAY_SLOTS and (
        record.assay_temperature_c is None or record.assay_ph is None
    ):
        return False
    if record.slot_id in _DIRECT_PHH_SLOTS and record.context_role != "direct_healthy_phh":
        return False
    if record.slot_id == "heldout_validation":
        return (
            record.context_role == "independent_healthy_phh_validation"
            and record.split_role == "independent_heldout"
            and record.frozen_before_heldout_access is True
        )
    return True


def assess_reaction_evidence(
    reaction_id: str,
    records: tuple[ReactionEvidenceIntakeRecord, ...],
) -> ReactionEvidenceAssessment:
    if reaction_id not in _active_reaction_ids():
        raise ReactionEvidenceIntakeError(f"unknown active reaction id: {reaction_id}")
    selected = tuple(record for record in records if record.reaction_id == reaction_id)
    covered = frozenset(record.slot_id for record in selected)
    ready = frozenset(
        record.slot_id for record in selected if _record_is_structurally_ready(record)
    )
    missing = frozenset(_SLOT_BY_ID) - ready
    blockers: list[str] = []
    if missing:
        blockers.append("one or more of the twelve evidence slots lacks a reviewed context-qualified record")
    if "heldout_validation" not in ready:
        blockers.append("frozen donor- and study-disjoint PHH held-out validation is absent")
    structurally_complete = not missing
    blockers.extend(
        (
            "cross-record biochemical identity and unit conversions require manual semantic adjudication",
            "the immutable reaction atlas has not been rebuilt from an approved evidence bundle",
            "quantitative and predictive execution remain disabled",
        )
    )
    return ReactionEvidenceAssessment(
        reaction_id=reaction_id,
        record_count=len(selected),
        covered_slot_ids=tuple(sorted(covered)),
        structurally_ready_slot_ids=tuple(sorted(ready)),
        missing_slot_ids=tuple(sorted(missing)),
        structurally_complete=structurally_complete,
        atlas_mutation_allowed=False,
        quantitative_execution_allowed=False,
        predictive_execution_allowed=False,
        blockers=tuple(blockers),
    )


def reaction_evidence_intake_snapshot(
    path: Path = DEFAULT_EVIDENCE_PATH,
) -> dict[str, object]:
    contract = load_reaction_evidence_contract()
    active_reaction_ids = tuple(sorted(_active_reaction_ids()))
    expected_header_count = len(contract["required_columns"]) + len(
        contract["conditional_columns"]
    )
    if not path.exists():
        return {
            "version": INTAKE_VERSION,
            "contract_id": contract["contract_id"],
            "network_id": contract["network_id"],
            "status": "awaiting_reaction_evidence_bundle",
            "delivery_path": _display_path(path),
            "contract_sha256": _sha256(CONTRACT_PATH),
            "expected_header_count": expected_header_count,
            "active_reaction_count": len(active_reaction_ids),
            "required_slot_count": len(active_reaction_ids) * len(_SLOT_BY_ID),
            "record_count": 0,
            "covered_slot_count": 0,
            "structurally_ready_slot_count": 0,
            "structurally_complete_reaction_count": 0,
            "atlas_mutation_allowed_count": 0,
            "quantitative_execution_allowed_count": 0,
            "predictive_execution_allowed_count": 0,
            "automatic_unit_conversion": False,
            "automatic_parameter_fitting": False,
            "automatic_cell_state_coupling": False,
            "blockers": (
                "versioned reaction-evidence delivery is absent",
                "all 432 typed reaction-evidence slots remain unfilled",
                "manual semantic adjudication and independent held-out validation are absent",
            ),
        }
    dataset = load_reaction_evidence_dataset(path)
    assessments = tuple(
        assess_reaction_evidence(reaction_id, dataset.records)
        for reaction_id in active_reaction_ids
    )
    covered = {
        (record.reaction_id, record.slot_id) for record in dataset.records
    }
    ready = {
        (record.reaction_id, record.slot_id)
        for record in dataset.records
        if _record_is_structurally_ready(record)
    }
    return {
        "version": INTAKE_VERSION,
        "contract_id": dataset.contract_id,
        "network_id": contract["network_id"],
        "status": "reaction_evidence_structurally_audited_not_authoritative",
        "delivery_path": dataset.delivery_path,
        "artifact_sha256": dataset.artifact_sha256,
        "contract_sha256": dataset.contract_sha256,
        "expected_header_count": expected_header_count,
        "active_reaction_count": len(active_reaction_ids),
        "required_slot_count": len(active_reaction_ids) * len(_SLOT_BY_ID),
        "record_count": len(dataset.records),
        "record_count_by_split": dict(
            sorted(Counter(record.split_role for record in dataset.records).items())
        ),
        "covered_slot_count": len(covered),
        "structurally_ready_slot_count": len(ready),
        "structurally_complete_reaction_count": sum(
            assessment.structurally_complete for assessment in assessments
        ),
        "atlas_mutation_allowed_count": 0,
        "quantitative_execution_allowed_count": 0,
        "predictive_execution_allowed_count": 0,
        "automatic_unit_conversion": False,
        "automatic_parameter_fitting": False,
        "automatic_cell_state_coupling": False,
        "reaction_assessments": tuple(to_plain(item) for item in assessments),
        "blockers": (
            "cross-record semantic adjudication is not encoded as automatic authority",
            "the immutable reaction atlas has not been rebuilt from an approved bundle",
            "quantitative and predictive execution remain disabled",
        ),
    }
