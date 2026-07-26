"""Fail-closed PHH cellular-memory trajectory intake.

The intake recognizes a candidate memory law only when one donor-resolved
trajectory contains a directly measured physical carrier before, during, and
after a verified trigger removal plus matched first-challenge and rechallenge
response measurements. Structural completeness is not quantitative authority:
manual source review, a frozen model, and donor/study-disjoint validation remain
external gates.
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


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "evidence_intake"
    / "phh_cellular_memory_trajectory_contract.v1.json"
)
DEFAULT_TRAJECTORY_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "evidence_intake"
    / "incoming"
    / "phh_cellular_memory"
    / "latest"
    / "phh_cellular_memory_trajectories.csv"
)
CONTRACT_SCHEMA_VERSION = "cell.phh-cellular-memory-trajectory-contract.v1"
INTAKE_VERSION = "phh_cellular_memory_trajectory_intake_v1"
LAW_GATE_VERSION = "phh_memory_write_persist_rechallenge_gate_v1"

_NULL_TOKEN = "null"
_NUMBER_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
_ALLOWED_SPLIT_ROLES = frozenset(
    {"calibration", "internal_validation", "independent_heldout"}
)
_ALLOWED_PHASES = frozenset(
    {
        "baseline",
        "write",
        "washout",
        "persistence_followup",
        "first_challenge_response",
        "rechallenge_response",
        "division_followup",
        "erasure_followup",
    }
)
_ALLOWED_MEASUREMENT_ROLES = frozenset(
    {"physical_substrate", "future_response", "inheritance", "erasure"}
)
_REQUIRED_PHYSICAL_PHASES = frozenset(
    {"baseline", "write", "persistence_followup"}
)
_REQUIRED_RESPONSE_PHASES = frozenset(
    {"first_challenge_response", "rechallenge_response"}
)


class CellularMemoryTrajectoryError(ValueError):
    """Raised when a memory-trajectory delivery violates its evidence contract."""


@dataclass(frozen=True)
class CellularMemoryTrajectoryRecord:
    record_id: str
    donor_id: str
    split_role: str
    source_study_id: str
    source_locator: str
    species: str
    biological_system: str
    culture_format: str
    substrate_contract_id: str
    compartment: str
    locus_or_entity: str
    trajectory_id: str
    trajectory_phase: str
    measurement_role: str
    trigger_identity: str
    elapsed_from_trigger_start_h: float
    assay: str
    readout: str
    raw_value: float
    raw_unit: str
    biological_replicate_id: str
    normalization_denominator: str
    trigger_value: float | None
    trigger_unit: str | None
    trigger_removal_time_h: float | None
    elapsed_from_trigger_removal_h: float | None
    rechallenge_identity: str | None
    rechallenge_value: float | None
    rechallenge_unit: str | None
    cell_generation: int | None
    parent_cell_id: str | None
    uncertainty_type: str | None
    uncertainty_value: float | None
    censoring_flag: str | None

    @property
    def donor_key(self) -> tuple[str, str]:
        return self.source_study_id, self.donor_id

    @property
    def candidate_key(self) -> tuple[str, ...]:
        return (
            self.source_study_id,
            self.donor_id,
            self.trajectory_id,
            self.substrate_contract_id,
            self.compartment,
            self.locus_or_entity,
        )


@dataclass(frozen=True)
class MemoryLawCandidateAssessment:
    candidate_key: tuple[str, ...]
    record_count: int
    physical_substrate_phases: tuple[str, ...]
    future_response_phases: tuple[str, ...]
    verified_trigger_removal: bool
    same_physical_carrier_assay: bool
    same_response_assay: bool
    structurally_complete: bool
    quantitative_activation_allowed: bool
    automatic_memory_trace_creation: bool
    automatic_future_response_coupling: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class CellularMemoryTrajectoryDataset:
    version: str
    contract_id: str
    delivery_path: str
    artifact_sha256: str
    contract_sha256: str
    records: tuple[CellularMemoryTrajectoryRecord, ...]


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


def load_cellular_memory_trajectory_contract(
    path: Path = CONTRACT_PATH,
    *,
    allowed_substrate_ids: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CellularMemoryTrajectoryError("memory trajectory contract must be one object")
    if payload.get("schema_version") != CONTRACT_SCHEMA_VERSION:
        raise CellularMemoryTrajectoryError("unsupported memory trajectory contract schema")
    required = payload.get("required_columns")
    conditional = payload.get("conditional_columns")
    gate = payload.get("candidate_law_gate")
    policy = payload.get("policy")
    if not all(
        (
            isinstance(required, list),
            isinstance(conditional, list),
            isinstance(gate, dict),
            isinstance(policy, dict),
        )
    ):
        raise CellularMemoryTrajectoryError("memory trajectory contract is malformed")
    required_ids = tuple(
        str(item.get("id", "")) for item in required if isinstance(item, dict)
    )
    conditional_ids = tuple(
        str(item.get("id", "")) for item in conditional if isinstance(item, dict)
    )
    if (
        len(required_ids) != 22
        or len(set(required_ids)) != 22
        or not all(required_ids)
        or len(conditional_ids) != 12
        or len(set(conditional_ids)) != 12
        or not all(conditional_ids)
    ):
        raise CellularMemoryTrajectoryError("memory trajectory field contract changed")
    if set(payload.get("allowed_split_roles", ())) != _ALLOWED_SPLIT_ROLES:
        raise CellularMemoryTrajectoryError("memory trajectory split roles changed")
    if set(payload.get("allowed_trajectory_phases", ())) != _ALLOWED_PHASES:
        raise CellularMemoryTrajectoryError("memory trajectory phases changed")
    if set(payload.get("allowed_measurement_roles", ())) != _ALLOWED_MEASUREMENT_ROLES:
        raise CellularMemoryTrajectoryError("memory trajectory measurement roles changed")
    if payload.get("canonical_null_token") != _NULL_TOKEN:
        raise CellularMemoryTrajectoryError("memory trajectory null policy changed")
    if gate.get("version") != LAW_GATE_VERSION:
        raise CellularMemoryTrajectoryError("memory trajectory law gate changed")
    if set(gate.get("required_physical_substrate_phases", ())) != _REQUIRED_PHYSICAL_PHASES:
        raise CellularMemoryTrajectoryError("physical-substrate phase gate changed")
    if set(gate.get("required_future_response_phases", ())) != _REQUIRED_RESPONSE_PHASES:
        raise CellularMemoryTrajectoryError("future-response phase gate changed")
    required_true = {
        "same_donor_required",
        "same_trajectory_required",
        "same_physical_carrier_assay_required",
        "same_response_assay_required",
        "verified_trigger_removal_required",
        "donor_disjoint_validation_required",
        "independent_heldout_study_required",
        "frozen_model_before_heldout_access_required",
    }
    required_false = {
        "automatic_parameter_fitting",
        "automatic_memory_trace_creation",
        "automatic_future_response_coupling",
        "automatic_cell_state_coupling",
    }
    if any(gate.get(key) is not True for key in required_true) or any(
        gate.get(key) is not False for key in required_false
    ):
        raise CellularMemoryTrajectoryError("memory trajectory law gate escaped fail-closed policy")
    policy_false = {
        "event_duration_alone_is_memory",
        "post_trigger_measurement_without_verified_removal_is_persistence",
        "different_donors_may_form_one_memory_trajectory",
        "whole_liver_average_may_initialize_single_cell_memory",
        "cross_species_rate_transfer_allowed",
        "unit_conversion_without_explicit_provenance",
        "interpolation_for_validation",
        "missing_phase_means_no_memory",
        "universal_memory_decay_law_allowed",
        "automatic_parameter_activation",
        "automatic_cell_state_coupling",
    }
    if policy.get("manual_primary_source_review_required") is not True or any(
        policy.get(key) is not False for key in policy_false
    ):
        raise CellularMemoryTrajectoryError("memory trajectory policy escaped fail-closed state")
    if allowed_substrate_ids is not None and (
        len(set(allowed_substrate_ids)) != len(allowed_substrate_ids)
        or not all(allowed_substrate_ids)
    ):
        raise CellularMemoryTrajectoryError("declared substrate ids must be unique and non-empty")
    return payload


def _required_text(row: dict[str, str], field: str, row_number: int) -> str:
    value = row[field].strip()
    if not value or value.lower() == _NULL_TOKEN:
        raise CellularMemoryTrajectoryError(f"row {row_number}: {field} is required")
    return value


def _optional_text(row: dict[str, str], field: str) -> str | None:
    value = row[field].strip()
    return None if not value or value.lower() == _NULL_TOKEN else value


def _number(
    row: dict[str, str],
    field: str,
    row_number: int,
    *,
    optional: bool = False,
) -> float | None:
    token = row[field].strip()
    if optional and (not token or token.lower() == _NULL_TOKEN):
        return None
    if not _NUMBER_RE.fullmatch(token):
        raise CellularMemoryTrajectoryError(
            f"row {row_number}: {field} must be one finite number"
        )
    value = float(token)
    if not math.isfinite(value):
        raise CellularMemoryTrajectoryError(f"row {row_number}: {field} must be finite")
    return value


def _nonnegative_number(
    row: dict[str, str],
    field: str,
    row_number: int,
    *,
    optional: bool = False,
) -> float | None:
    value = _number(row, field, row_number, optional=optional)
    if value is not None and value < 0:
        raise CellularMemoryTrajectoryError(
            f"row {row_number}: {field} must be non-negative"
        )
    return value


def _paired_optional_number_and_unit(
    row: dict[str, str],
    value_field: str,
    unit_field: str,
    row_number: int,
) -> tuple[float | None, str | None]:
    value = _number(row, value_field, row_number, optional=True)
    unit = _optional_text(row, unit_field)
    if (value is None) != (unit is None):
        raise CellularMemoryTrajectoryError(
            f"row {row_number}: {value_field} and {unit_field} must be supplied together"
        )
    return value, unit


def _record(
    row: dict[str, str],
    row_number: int,
    allowed_substrate_ids: frozenset[str],
) -> CellularMemoryTrajectoryRecord:
    split_role = _required_text(row, "split_role", row_number)
    if split_role not in _ALLOWED_SPLIT_ROLES:
        raise CellularMemoryTrajectoryError(
            f"row {row_number}: unsupported split_role {split_role!r}"
        )
    species = _required_text(row, "species", row_number)
    if species != "Homo sapiens":
        raise CellularMemoryTrajectoryError(
            f"row {row_number}: non-human record cannot enter the PHH memory set"
        )
    biological_system = _required_text(row, "biological_system", row_number)
    if "primary_human_hepatocyte" not in biological_system.lower():
        raise CellularMemoryTrajectoryError(
            f"row {row_number}: biological_system is outside primary human hepatocytes"
        )
    substrate_id = _required_text(row, "substrate_contract_id", row_number)
    if substrate_id not in allowed_substrate_ids:
        raise CellularMemoryTrajectoryError(
            f"row {row_number}: unknown substrate_contract_id {substrate_id!r}"
        )
    phase = _required_text(row, "trajectory_phase", row_number)
    if phase not in _ALLOWED_PHASES:
        raise CellularMemoryTrajectoryError(
            f"row {row_number}: unsupported trajectory_phase {phase!r}"
        )
    role = _required_text(row, "measurement_role", row_number)
    if role not in _ALLOWED_MEASUREMENT_ROLES:
        raise CellularMemoryTrajectoryError(
            f"row {row_number}: unsupported measurement_role {role!r}"
        )
    trigger_value, trigger_unit = _paired_optional_number_and_unit(
        row, "trigger_value", "trigger_unit", row_number
    )
    rechallenge_value, rechallenge_unit = _paired_optional_number_and_unit(
        row, "rechallenge_value", "rechallenge_unit", row_number
    )
    uncertainty_value = _nonnegative_number(
        row, "uncertainty_value", row_number, optional=True
    )
    uncertainty_type = _optional_text(row, "uncertainty_type")
    if (uncertainty_value is None) != (uncertainty_type is None):
        raise CellularMemoryTrajectoryError(
            f"row {row_number}: uncertainty_type and uncertainty_value must be supplied together"
        )
    trigger_removal = _nonnegative_number(
        row, "trigger_removal_time_h", row_number, optional=True
    )
    after_removal = _nonnegative_number(
        row, "elapsed_from_trigger_removal_h", row_number, optional=True
    )
    rechallenge_identity = _optional_text(row, "rechallenge_identity")
    generation_value = _nonnegative_number(
        row, "cell_generation", row_number, optional=True
    )
    if generation_value is not None and not generation_value.is_integer():
        raise CellularMemoryTrajectoryError(
            f"row {row_number}: cell_generation must be an integer"
        )
    if phase == "persistence_followup" and (
        trigger_removal is None or after_removal is None
    ):
        raise CellularMemoryTrajectoryError(
            f"row {row_number}: persistence requires verified trigger-removal timing"
        )
    if phase == "rechallenge_response" and rechallenge_identity is None:
        raise CellularMemoryTrajectoryError(
            f"row {row_number}: rechallenge_response requires rechallenge_identity"
        )
    if phase == "division_followup" and generation_value is None:
        raise CellularMemoryTrajectoryError(
            f"row {row_number}: division_followup requires cell_generation"
        )
    raw_value = _number(row, "raw_value", row_number)
    elapsed = _nonnegative_number(
        row, "elapsed_from_trigger_start_h", row_number
    )
    assert raw_value is not None and elapsed is not None
    return CellularMemoryTrajectoryRecord(
        record_id=_required_text(row, "record_id", row_number),
        donor_id=_required_text(row, "donor_id", row_number),
        split_role=split_role,
        source_study_id=_required_text(row, "source_study_id", row_number),
        source_locator=_required_text(row, "source_locator", row_number),
        species=species,
        biological_system=biological_system,
        culture_format=_required_text(row, "culture_format", row_number),
        substrate_contract_id=substrate_id,
        compartment=_required_text(row, "compartment", row_number),
        locus_or_entity=_required_text(row, "locus_or_entity", row_number),
        trajectory_id=_required_text(row, "trajectory_id", row_number),
        trajectory_phase=phase,
        measurement_role=role,
        trigger_identity=_required_text(row, "trigger_identity", row_number),
        elapsed_from_trigger_start_h=elapsed,
        assay=_required_text(row, "assay", row_number),
        readout=_required_text(row, "readout", row_number),
        raw_value=raw_value,
        raw_unit=_required_text(row, "raw_unit", row_number),
        biological_replicate_id=_required_text(
            row, "biological_replicate_id", row_number
        ),
        normalization_denominator=_required_text(
            row, "normalization_denominator", row_number
        ),
        trigger_value=trigger_value,
        trigger_unit=trigger_unit,
        trigger_removal_time_h=trigger_removal,
        elapsed_from_trigger_removal_h=after_removal,
        rechallenge_identity=rechallenge_identity,
        rechallenge_value=rechallenge_value,
        rechallenge_unit=rechallenge_unit,
        cell_generation=int(generation_value) if generation_value is not None else None,
        parent_cell_id=_optional_text(row, "parent_cell_id"),
        uncertainty_type=uncertainty_type,
        uncertainty_value=uncertainty_value,
        censoring_flag=_optional_text(row, "censoring_flag"),
    )


def load_cellular_memory_trajectory_dataset(
    path: Path,
    *,
    allowed_substrate_ids: tuple[str, ...],
    contract_path: Path = CONTRACT_PATH,
) -> CellularMemoryTrajectoryDataset:
    contract = load_cellular_memory_trajectory_contract(
        contract_path,
        allowed_substrate_ids=allowed_substrate_ids,
    )
    expected_columns = tuple(
        item["id"]
        for section in ("required_columns", "conditional_columns")
        for item in contract[section]
    )
    allowed = frozenset(allowed_substrate_ids)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != expected_columns:
            raise CellularMemoryTrajectoryError(
                "memory trajectory header must exactly match the versioned contract"
            )
        records = tuple(
            _record(row, row_number, allowed)
            for row_number, row in enumerate(reader, start=2)
        )
    if not records:
        raise CellularMemoryTrajectoryError("memory trajectory delivery is empty")
    record_ids = [record.record_id for record in records]
    if len(record_ids) != len(set(record_ids)):
        raise CellularMemoryTrajectoryError("memory trajectory record ids must be unique")
    donor_roles: dict[tuple[str, str], set[str]] = defaultdict(set)
    study_roles: dict[str, set[str]] = defaultdict(set)
    for record in records:
        donor_roles[record.donor_key].add(record.split_role)
        study_roles[record.source_study_id].add(record.split_role)
    leaked_donors = sorted(key for key, roles in donor_roles.items() if len(roles) > 1)
    if leaked_donors:
        raise CellularMemoryTrajectoryError(
            f"donor identity crosses split roles: {leaked_donors[0]!r}"
        )
    leaked_heldout_studies = sorted(
        study
        for study, roles in study_roles.items()
        if "independent_heldout" in roles and len(roles) > 1
    )
    if leaked_heldout_studies:
        raise CellularMemoryTrajectoryError(
            "independent-heldout source study crosses non-heldout split roles"
        )
    return CellularMemoryTrajectoryDataset(
        version=INTAKE_VERSION,
        contract_id=str(contract["contract_id"]),
        delivery_path=_display_path(path),
        artifact_sha256=_sha256(path),
        contract_sha256=_sha256(contract_path),
        records=records,
    )


def assess_memory_law_candidate(
    records: tuple[CellularMemoryTrajectoryRecord, ...],
) -> MemoryLawCandidateAssessment:
    if not records:
        raise CellularMemoryTrajectoryError("memory-law candidate cannot be empty")
    keys = {record.candidate_key for record in records}
    if len(keys) != 1:
        raise CellularMemoryTrajectoryError(
            "memory-law candidate records must share donor, trajectory, carrier, and entity"
        )
    trigger_identities = {record.trigger_identity for record in records}
    physical = tuple(
        record for record in records if record.measurement_role == "physical_substrate"
    )
    responses = tuple(
        record for record in records if record.measurement_role == "future_response"
    )
    physical_phases = frozenset(record.trajectory_phase for record in physical)
    response_phases = frozenset(record.trajectory_phase for record in responses)
    physical_assay_keys = {
        (
            record.assay,
            record.readout,
            record.raw_unit,
            record.normalization_denominator,
        )
        for record in physical
    }
    response_assay_keys = {
        (
            record.assay,
            record.readout,
            record.raw_unit,
            record.normalization_denominator,
        )
        for record in responses
    }
    verified_removal = any(
        record.trajectory_phase == "persistence_followup"
        and record.trigger_removal_time_h is not None
        and record.elapsed_from_trigger_removal_h is not None
        for record in physical
    )
    blockers: list[str] = []
    missing_physical = sorted(_REQUIRED_PHYSICAL_PHASES - physical_phases)
    missing_responses = sorted(_REQUIRED_RESPONSE_PHASES - response_phases)
    if missing_physical:
        blockers.append(
            f"missing physical-substrate phases: {', '.join(missing_physical)}"
        )
    if missing_responses:
        blockers.append(
            f"missing future-response phases: {', '.join(missing_responses)}"
        )
    if len(trigger_identities) != 1:
        blockers.append("trigger identity changes within one candidate trajectory")
    if not verified_removal:
        blockers.append("verified trigger-removal persistence observation is absent")
    if len(physical_assay_keys) != 1:
        blockers.append("physical carrier assay/readout/unit/denominator is not matched")
    if len(response_assay_keys) != 1:
        blockers.append("first-challenge and rechallenge response assays are not matched")
    structurally_complete = not blockers
    if structurally_complete:
        blockers.extend(
            (
                "manual primary-source review attestation is absent",
                "frozen write/read/decay model artifact is absent",
                "donor- and study-disjoint held-out result is absent",
            )
        )
    return MemoryLawCandidateAssessment(
        candidate_key=next(iter(keys)),
        record_count=len(records),
        physical_substrate_phases=tuple(sorted(physical_phases)),
        future_response_phases=tuple(sorted(response_phases)),
        verified_trigger_removal=verified_removal,
        same_physical_carrier_assay=len(physical_assay_keys) == 1,
        same_response_assay=len(response_assay_keys) == 1,
        structurally_complete=structurally_complete,
        quantitative_activation_allowed=False,
        automatic_memory_trace_creation=False,
        automatic_future_response_coupling=False,
        blockers=tuple(blockers),
    )


def cellular_memory_trajectory_intake_snapshot(
    *,
    allowed_substrate_ids: tuple[str, ...],
    path: Path = DEFAULT_TRAJECTORY_PATH,
) -> dict[str, object]:
    contract = load_cellular_memory_trajectory_contract(
        allowed_substrate_ids=allowed_substrate_ids
    )
    expected_header_count = len(contract["required_columns"]) + len(
        contract["conditional_columns"]
    )
    base = {
        "version": INTAKE_VERSION,
        "contract_id": contract["contract_id"],
        "contract_path": _display_path(CONTRACT_PATH),
        "contract_sha256": _sha256(CONTRACT_PATH),
        "delivery_path": _display_path(path),
        "expected_header_count": expected_header_count,
        "required_column_count": len(contract["required_columns"]),
        "conditional_column_count": len(contract["conditional_columns"]),
        "declared_substrate_count": len(allowed_substrate_ids),
        "write_persist_rechallenge_gate_count": 1,
        "split_leakage_guard_count": 1,
        "independent_heldout_study_guard_count": 1,
        "automatic_memory_trace_creation": False,
        "automatic_future_response_coupling": False,
        "automatic_parameter_activation": False,
    }
    if not path.exists():
        return {
            **base,
            "status": "awaiting_donor_resolved_phh_memory_trajectories",
            "artifact_sha256": None,
            "record_count": 0,
            "donor_count": 0,
            "source_study_count": 0,
            "candidate_trajectory_count": 0,
            "structurally_complete_candidate_count": 0,
            "quantitatively_authorized_memory_law_count": 0,
            "record_count_by_split": {},
            "blockers": (
                "No donor-resolved primary-human-hepatocyte memory trajectory file was delivered.",
                "Manual primary-source review, frozen model identity, and independent held-out results are absent.",
            ),
        }
    dataset = load_cellular_memory_trajectory_dataset(
        path,
        allowed_substrate_ids=allowed_substrate_ids,
    )
    groups: dict[
        tuple[str, ...], list[CellularMemoryTrajectoryRecord]
    ] = defaultdict(list)
    for record in dataset.records:
        groups[record.candidate_key].append(record)
    assessments = tuple(
        assess_memory_law_candidate(tuple(group))
        for _, group in sorted(groups.items())
    )
    return {
        **base,
        "status": "data_structurally_audited_quantitative_memory_activation_blocked",
        "artifact_sha256": dataset.artifact_sha256,
        "record_count": len(dataset.records),
        "donor_count": len({record.donor_key for record in dataset.records}),
        "source_study_count": len(
            {record.source_study_id for record in dataset.records}
        ),
        "candidate_trajectory_count": len(assessments),
        "structurally_complete_candidate_count": sum(
            assessment.structurally_complete for assessment in assessments
        ),
        "quantitatively_authorized_memory_law_count": 0,
        "record_count_by_split": dict(
            sorted(Counter(record.split_role for record in dataset.records).items())
        ),
        "candidate_assessments": tuple(to_plain(item) for item in assessments),
        "blockers": (
            "Structural completeness is not source review or model calibration.",
            "A frozen write/read/decay operator and donor/study-disjoint result are required.",
        ),
    }
