"""Fail-closed intake for externally researched healthy-human/PHH evidence.

The intake layer validates structure and provenance metadata.  It never promotes
an external record into an authoritative parameter automatically; primary-source
review and a separate, versioned curation step remain mandatory.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from cell_engine.core.serialization import to_plain


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = REPOSITORY_ROOT / "data" / "evidence_intake" / "phh_evidence_bundle_contract.v1.json"
DEFAULT_INCOMING_BUNDLE_ROOT = REPOSITORY_ROOT / "data" / "evidence_intake" / "incoming" / "latest"
CONTRACT_SCHEMA_VERSION = "cell.phh-evidence-bundle-contract.v1"
INTAKE_VERSION = "human_phh_evidence_intake_v1"

_DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$", re.IGNORECASE)
_NUMBER_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
_POSITIVE_FLAGS = frozenset(
    {
        "automatic_parameter_activation",
        "automatic_coupling",
        "auto_activate",
        "authoritative_coupling_enabled",
        "predictive_ready",
    }
)


class EvidenceIntakeError(ValueError):
    pass


@dataclass(frozen=True)
class EvidenceTableAudit:
    file: str
    record_count: int
    numeric_record_count: int
    missing_value_record_count: int
    human_target_record_count: int
    curation_candidate_count: int
    model_output_record_count: int
    column_mapping: Mapping[str, str]


@dataclass(frozen=True)
class EvidenceBundleAudit:
    version: str
    contract_id: str
    status: str
    delivery_path: str | None
    required_file_count: int
    present_file_count: int
    sha256_by_file: Mapping[str, str]
    tables: tuple[EvidenceTableAudit, ...]
    curation_candidate_count: int
    manual_primary_source_review_required: bool
    automatic_parameter_activation: bool
    authoritative_coupling_enabled: bool
    blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def _load_contract(path: Path = CONTRACT_PATH) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != CONTRACT_SCHEMA_VERSION:
        raise EvidenceIntakeError("Unsupported PHH evidence-intake contract schema")
    required = payload.get("required_files")
    csv_files = payload.get("csv_files")
    markdown_files = payload.get("markdown_files")
    if not isinstance(required, list) or not isinstance(csv_files, list) or not isinstance(markdown_files, list):
        raise EvidenceIntakeError("Evidence-intake contract file lists are malformed")
    if len(required) != len(set(required)) or not set(csv_files + markdown_files + ["integration_contract.json"]) <= set(required):
        raise EvidenceIntakeError("Evidence-intake contract file lists are inconsistent")
    policy = payload.get("policy")
    if not isinstance(policy, dict):
        raise EvidenceIntakeError("Evidence-intake contract policy is missing")
    if policy.get("automatic_parameter_activation") is not False or policy.get("authoritative_coupling_enabled") is not False:
        raise EvidenceIntakeError("Evidence-intake contract must fail closed")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalise_token(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _column_mapping(fieldnames: tuple[str, ...], aliases: Mapping[str, object], file_name: str) -> dict[str, str]:
    normalised = {_normalise_token(column): column for column in fieldnames}
    mapping: dict[str, str] = {}
    for semantic_name, raw_aliases in aliases.items():
        if not isinstance(raw_aliases, list):
            raise EvidenceIntakeError(f"Invalid semantic aliases for {semantic_name}")
        matches = [normalised[_normalise_token(str(alias))] for alias in raw_aliases if _normalise_token(str(alias)) in normalised]
        if not matches:
            raise EvidenceIntakeError(f"{file_name} has no column for required semantic field {semantic_name}")
        mapping[str(semantic_name)] = matches[0]
    return mapping


def _is_null(value: str, null_tokens: set[str]) -> bool:
    return value.strip().lower() in null_tokens


def _optional_number(value: str, *, field: str, row_number: int, file_name: str, null_tokens: set[str]) -> float | None:
    token = value.strip()
    if token.lower() in null_tokens:
        return None
    if not _NUMBER_RE.fullmatch(token):
        raise EvidenceIntakeError(f"{file_name}:{row_number} {field} must be one finite number or null")
    number = float(token)
    if not math.isfinite(number):
        raise EvidenceIntakeError(f"{file_name}:{row_number} {field} must be finite")
    return number


def _optional_column(fieldnames: tuple[str, ...], *aliases: str) -> str | None:
    normalised = {_normalise_token(column): column for column in fieldnames}
    return next((normalised[_normalise_token(alias)] for alias in aliases if _normalise_token(alias) in normalised), None)


def _audit_csv(path: Path, contract: Mapping[str, object]) -> EvidenceTableAudit:
    aliases = contract["semantic_column_aliases"]
    if not isinstance(aliases, dict):
        raise EvidenceIntakeError("Semantic column aliases are malformed")
    null_tokens = {str(item).lower() for item in contract["null_tokens"]}  # type: ignore[index]
    forbidden_missing = {str(item).lower() for item in contract["forbidden_missing_tokens"]}  # type: ignore[index]
    eligible_species = {str(item).lower() for item in contract["eligible_target_species"]}  # type: ignore[index]
    eligible_systems = {str(item).lower() for item in contract["eligible_target_systems"]}  # type: ignore[index]
    eligible_directness = {str(item).lower() for item in contract["eligible_directness"]}  # type: ignore[index]
    eligible_record_types = {str(item).lower() for item in contract["eligible_record_types"]}  # type: ignore[index]
    eligible_source_kinds = {str(item).lower() for item in contract["eligible_source_kinds"]}  # type: ignore[index]

    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fieldnames = tuple(reader.fieldnames or ())
        if not fieldnames or len(fieldnames) != len(set(fieldnames)):
            raise EvidenceIntakeError(f"{path.name} has missing or duplicate headers")
        mapping = _column_mapping(fieldnames, aliases, path.name)
        lower_column = _optional_column(fieldnames, "lower", "low", "ci_low")
        upper_column = _optional_column(fieldnames, "upper", "high", "ci_high")
        uncertainty_column = _optional_column(fieldnames, "uncertainty_value", "sem", "sd", "error")
        seen_ids: set[str] = set()
        record_count = 0
        numeric_count = 0
        missing_count = 0
        human_count = 0
        candidate_count = 0
        model_output_count = 0

        for row_number, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise EvidenceIntakeError(f"Malformed CSV record at {path.name}:{row_number}")
            record_count += 1
            record_id = row[mapping["record_id"]].strip()
            if not record_id or record_id.lower() == "null":
                raise EvidenceIntakeError(f"{path.name}:{row_number} record_id is required")
            if record_id in seen_ids:
                raise EvidenceIntakeError(f"{path.name} contains duplicate record_id {record_id}")
            seen_ids.add(record_id)

            for column, raw_value in row.items():
                if raw_value.strip().lower() in forbidden_missing:
                    raise EvidenceIntakeError(
                        f"{path.name}:{row_number} uses forbidden missing token {raw_value!r} in {column}; use null"
                    )

            value = _optional_number(
                row[mapping["value"]], field="value", row_number=row_number,
                file_name=path.name, null_tokens=null_tokens,
            )
            lower = _optional_number(row[lower_column], field="lower", row_number=row_number, file_name=path.name, null_tokens=null_tokens) if lower_column else None
            upper = _optional_number(row[upper_column], field="upper", row_number=row_number, file_name=path.name, null_tokens=null_tokens) if upper_column else None
            uncertainty = _optional_number(row[uncertainty_column], field="uncertainty", row_number=row_number, file_name=path.name, null_tokens=null_tokens) if uncertainty_column else None
            if lower is not None and upper is not None and lower > upper:
                raise EvidenceIntakeError(f"{path.name}:{row_number} has descending bounds")
            if value is not None and lower is not None and value < lower:
                raise EvidenceIntakeError(f"{path.name}:{row_number} value is below its lower bound")
            if value is not None and upper is not None and value > upper:
                raise EvidenceIntakeError(f"{path.name}:{row_number} value is above its upper bound")
            if uncertainty is not None and uncertainty < 0:
                raise EvidenceIntakeError(f"{path.name}:{row_number} uncertainty is negative")

            unit = row[mapping["unit"]].strip()
            if value is not None and _is_null(unit, null_tokens):
                raise EvidenceIntakeError(f"{path.name}:{row_number} numeric value has no unit")
            doi = row[mapping["doi"]].strip()
            if doi.lower().startswith("https://doi.org/"):
                doi = doi[len("https://doi.org/"):]
            if not _is_null(doi, null_tokens) and not _DOI_RE.fullmatch(doi):
                raise EvidenceIntakeError(f"{path.name}:{row_number} DOI is malformed")

            record_type = _normalise_token(row[mapping["record_type"]])
            directness = _normalise_token(row[mapping["directness"]])
            source_kind = _normalise_token(row[mapping["source_kind"]])
            if "model" in directness or record_type in {"model_output", "model_prediction"}:
                model_output_count += 1
                if record_type == "measured":
                    raise EvidenceIntakeError(f"{path.name}:{row_number} labels model output as measured")

            human_target = (
                row[mapping["species"]].strip().lower() in eligible_species
                and _normalise_token(row[mapping["biological_system"]]) in eligible_systems
            )
            if human_target:
                human_count += 1
            if value is None:
                missing_count += 1
            else:
                numeric_count += 1

            source_complete = not _is_null(doi, null_tokens) and not _is_null(row[mapping["source_locator"]], null_tokens)
            candidate = (
                value is not None
                and human_target
                and directness in eligible_directness
                and record_type in eligible_record_types
                and source_kind in eligible_source_kinds
                and source_complete
                and not _is_null(row[mapping["source_title"]], null_tokens)
                and not _is_null(row[mapping["applicability"]], null_tokens)
                and not _is_null(row[mapping["limitations"]], null_tokens)
            )
            candidate_count += int(candidate)

    return EvidenceTableAudit(
        file=path.name,
        record_count=record_count,
        numeric_record_count=numeric_count,
        missing_value_record_count=missing_count,
        human_target_record_count=human_count,
        curation_candidate_count=candidate_count,
        model_output_record_count=model_output_count,
        column_mapping=mapping,
    )


def _assert_no_positive_activation_flags(payload: object, path: str = "integration_contract") -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            normalised_key = _normalise_token(str(key))
            if normalised_key in _POSITIVE_FLAGS and value is True:
                raise EvidenceIntakeError(f"{path}.{key} attempts to activate an unreviewed model surface")
            _assert_no_positive_activation_flags(value, f"{path}.{key}")
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            _assert_no_positive_activation_flags(value, f"{path}[{index}]")


def validate_evidence_bundle(root: Path) -> EvidenceBundleAudit:
    contract = _load_contract()
    if not root.is_dir():
        raise EvidenceIntakeError(f"Evidence bundle directory does not exist: {root}")
    required_files = tuple(str(item) for item in contract["required_files"])  # type: ignore[index]
    missing = tuple(file_name for file_name in required_files if not (root / file_name).is_file())
    if missing:
        raise EvidenceIntakeError("Evidence bundle is incomplete: " + ", ".join(missing))

    for file_name in contract["markdown_files"]:  # type: ignore[index]
        text = (root / str(file_name)).read_text(encoding="utf-8").strip()
        if not text:
            raise EvidenceIntakeError(f"{file_name} is empty")

    integration_contract = json.loads((root / "integration_contract.json").read_text(encoding="utf-8"))
    if not isinstance(integration_contract, dict):
        raise EvidenceIntakeError("integration_contract.json must contain one JSON object")
    _assert_no_positive_activation_flags(integration_contract)

    tables = tuple(_audit_csv(root / str(file_name), contract) for file_name in contract["csv_files"])  # type: ignore[index]
    sha256_by_file = {file_name: _sha256(root / file_name) for file_name in required_files}
    candidate_count = sum(table.curation_candidate_count for table in tables)
    blockers = (
        "External research records have not received manual primary-source review inside Cell.",
        "No candidate has been promoted into a versioned curated parameter registry.",
        "No scale bridge, endocrine rate law or held-out validation result is activated automatically.",
    )
    return EvidenceBundleAudit(
        version=INTAKE_VERSION,
        contract_id=str(contract["contract_id"]),
        status="structurally_valid_manual_review_required",
        delivery_path=str(root),
        required_file_count=len(required_files),
        present_file_count=len(required_files),
        sha256_by_file=sha256_by_file,
        tables=tables,
        curation_candidate_count=candidate_count,
        manual_primary_source_review_required=True,
        automatic_parameter_activation=False,
        authoritative_coupling_enabled=False,
        blockers=blockers,
    )


def evidence_intake_snapshot(root: Path = DEFAULT_INCOMING_BUNDLE_ROOT) -> dict[str, object]:
    contract = _load_contract()
    required_files = tuple(str(item) for item in contract["required_files"])  # type: ignore[index]
    work_packages = contract["work_packages"]
    if not root.is_dir():
        return {
            "version": INTAKE_VERSION,
            "contract_id": contract["contract_id"],
            "status": "awaiting_external_evidence_bundle",
            "delivery_path": None,
            "required_file_count": len(required_files),
            "present_file_count": 0,
            "work_packages": work_packages,
            "tables": [],
            "curation_candidate_count": 0,
            "manual_primary_source_review_required": True,
            "automatic_parameter_activation": False,
            "authoritative_coupling_enabled": False,
            "blockers": [
                "The requested nine-file Claude Science bundle has not been delivered.",
                "External evidence cannot alter parameters before structural audit and manual primary-source review.",
            ],
        }
    try:
        audit = validate_evidence_bundle(root).to_dict()
    except (EvidenceIntakeError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {
            "version": INTAKE_VERSION,
            "contract_id": contract["contract_id"],
            "status": "rejected_invalid_external_evidence_bundle",
            "delivery_path": str(root),
            "required_file_count": len(required_files),
            "present_file_count": sum((root / name).is_file() for name in required_files),
            "work_packages": work_packages,
            "tables": [],
            "curation_candidate_count": 0,
            "manual_primary_source_review_required": True,
            "automatic_parameter_activation": False,
            "authoritative_coupling_enabled": False,
            "blockers": [str(exc)],
        }
    audit["work_packages"] = work_packages
    return audit
