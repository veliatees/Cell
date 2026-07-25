"""Donor-disjoint PHH injury trajectory intake and frozen assay projection.

This module validates data structure, split independence and exact measurement
context. It does not supply biological values, fit a fate law or mutate cell
state. Numeric evaluation becomes possible only for an externally delivered,
manually reviewed trajectory file and a checksum-frozen model submission.
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
from typing import Any, Literal

from cell_engine.core.serialization import to_plain


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "evidence_intake"
    / "phh_injury_trajectory_contract.v1.json"
)
DEFAULT_TRAJECTORY_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "evidence_intake"
    / "incoming"
    / "phh_injury"
    / "latest"
    / "phh_injury_trajectories.csv"
)
CONTRACT_SCHEMA_VERSION = "cell.phh-injury-trajectory-contract.v1"
INTAKE_VERSION = "donor_disjoint_phh_injury_trajectory_intake_v1"
MEASUREMENT_OPERATOR_VERSION = "exact_phh_injury_assay_projection_v1"
FROZEN_EVALUATION_VERSION = "donor_disjoint_phh_injury_frozen_evaluation_v1"

_NUMBER_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_SPLIT_ROLES = frozenset(
    {"calibration", "internal_validation", "independent_heldout"}
)
_NULL_TOKEN = "null"


class PhhInjuryTrajectoryError(ValueError):
    """Raised when injury evidence or a model submission escapes its contract."""


@dataclass(frozen=True)
class PhhInjuryTrajectoryRecord:
    record_id: str
    donor_id: str
    split_role: str
    source_study_id: str
    source_locator: str
    species: str
    biological_system: str
    culture_format: str
    challenge: str
    challenge_concentration: float
    challenge_concentration_unit: str
    exposure_time_h: float
    endpoint: str
    assay: str
    raw_value: float
    raw_unit: str
    biological_replicate_id: str
    normalization_denominator: str
    censoring_flag: str
    intervention: str | None
    intervention_start_h: float | None
    washout_time_h: float | None
    recovery_followup_h: float | None
    technical_replicate_id: str | None
    uncertainty_type: str | None
    uncertainty_value: float | None
    limit_of_quantification: float | None
    viable_cell_count_at_measurement: float | None
    fate_label: str | None

    @property
    def donor_key(self) -> tuple[str, str]:
        return self.source_study_id, self.donor_id

    @property
    def observation_key(self) -> tuple[object, ...]:
        return (
            self.source_study_id,
            self.donor_id,
            self.biological_replicate_id,
            self.technical_replicate_id,
            self.biological_system,
            self.culture_format,
            self.challenge,
            self.challenge_concentration,
            self.challenge_concentration_unit,
            self.exposure_time_h,
            self.endpoint,
            self.assay,
            self.intervention,
            self.intervention_start_h,
            self.washout_time_h,
            self.recovery_followup_h,
        )


@dataclass(frozen=True)
class PhhInjuryTrajectoryDataset:
    version: str
    contract_id: str
    delivery_path: str
    artifact_sha256: str
    contract_sha256: str
    records: tuple[PhhInjuryTrajectoryRecord, ...]


@dataclass(frozen=True)
class PhhInjuryTrajectoryAudit:
    version: str
    contract_id: str
    status: str
    delivery_path: str
    artifact_sha256: str
    contract_sha256: str
    record_count: int
    donor_count: int
    biological_replicate_count: int
    source_study_count: int
    endpoint_count: int
    assay_count: int
    split_roles_present: tuple[str, ...]
    record_count_by_split: dict[str, int]
    donor_count_by_split: dict[str, int]
    donor_disjoint_split: bool
    independent_heldout_study_disjoint: bool
    donor_identity_scope: str
    cross_study_donor_linkage_verified: bool
    manual_primary_source_review_required: bool
    manual_primary_source_review_complete: bool
    automatic_parameter_activation: bool
    automatic_cell_state_coupling: bool
    blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


@dataclass(frozen=True)
class PhhInjuryPredictionPoint:
    record_id: str
    donor_id: str
    source_study_id: str
    split_role: Literal["independent_heldout"]
    species: str
    biological_system: str
    culture_format: str
    challenge: str
    challenge_concentration: float
    challenge_concentration_unit: str
    exposure_time_h: float
    endpoint: str
    assay: str
    biological_replicate_id: str
    technical_replicate_id: str | None
    normalization_denominator: str
    intervention: str | None
    intervention_start_h: float | None
    washout_time_h: float | None
    recovery_followup_h: float | None
    predicted_value: float
    predicted_unit: str


@dataclass(frozen=True)
class PhhInjuryFrozenSubmission:
    submission_id: str
    model_id: str
    model_artifact_sha256: str
    parameter_manifest_sha256: str
    dataset_artifact_sha256: str
    trajectory_contract_sha256: str
    source_review_artifact_sha256: str
    acceptance_criteria_artifact_sha256: str
    measurement_operator_version: str
    split_role: Literal["independent_heldout"]
    frozen_before_heldout_outcome_access: bool
    parameter_refit_count_after_freeze: int
    points: tuple[PhhInjuryPredictionPoint, ...]


@dataclass(frozen=True)
class PhhInjuryEvaluationAttestation:
    manual_primary_source_review_complete: bool
    donor_identity_scope_review_complete: bool
    independent_heldout_study_review_complete: bool
    independent_reviewer_attested: bool


@dataclass(frozen=True)
class PhhInjuryAssayResidual:
    record_id: str
    donor_id: str
    source_study_id: str
    endpoint: str
    assay: str
    observed_value: float
    predicted_value: float
    residual: float
    unit: str
    normalization_denominator: str


@dataclass(frozen=True)
class PhhInjuryFrozenEvaluation:
    version: str
    status: str
    submission_id: str
    evaluated_record_count: int
    residuals: tuple[PhhInjuryAssayResidual, ...]
    unit_conversion_performed: bool
    dose_interpolation_performed: bool
    time_interpolation_performed: bool
    fitted_parameter_count: int
    aggregate_score: None
    acceptance_threshold: None
    pass_fail_assigned: bool
    predictive_claim_assigned: bool
    may_drive_cell_state: bool

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


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


def load_phh_injury_trajectory_contract(
    path: Path = CONTRACT_PATH,
) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PhhInjuryTrajectoryError("PHH injury trajectory contract must be one object")
    if payload.get("schema_version") != CONTRACT_SCHEMA_VERSION:
        raise PhhInjuryTrajectoryError("Unsupported PHH injury trajectory contract schema")
    required = payload.get("required_columns")
    conditional = payload.get("conditional_columns")
    split_roles = payload.get("allowed_split_roles")
    measurement = payload.get("measurement_operator")
    frozen = payload.get("frozen_evaluation")
    policy = payload.get("policy")
    if not all(
        (
            isinstance(required, list),
            isinstance(conditional, list),
            isinstance(split_roles, list),
            isinstance(measurement, dict),
            isinstance(frozen, dict),
            isinstance(policy, dict),
        )
    ):
        raise PhhInjuryTrajectoryError("PHH injury trajectory contract is malformed")
    required_ids = tuple(
        str(item.get("id", "")) for item in required if isinstance(item, dict)
    )
    conditional_ids = tuple(
        str(item.get("id", "")) for item in conditional if isinstance(item, dict)
    )
    if (
        len(required_ids) != 19
        or len(set(required_ids)) != 19
        or not all(required_ids)
        or len(conditional_ids) != 10
        or len(set(conditional_ids)) != 10
        or not all(conditional_ids)
    ):
        raise PhhInjuryTrajectoryError("PHH injury trajectory field contract changed")
    if set(split_roles) != _ALLOWED_SPLIT_ROLES:
        raise PhhInjuryTrajectoryError("PHH injury trajectory split roles changed")
    if payload.get("canonical_null_token") != _NULL_TOKEN:
        raise PhhInjuryTrajectoryError("PHH injury trajectory null policy changed")
    if measurement.get("version") != MEASUREMENT_OPERATOR_VERSION:
        raise PhhInjuryTrajectoryError("PHH injury measurement operator version changed")
    if len(measurement.get("exact_match_dimensions", ())) != 20:
        raise PhhInjuryTrajectoryError("PHH injury exact-match dimensions changed")
    measurement_false = {
        "unit_conversion_enabled",
        "dose_interpolation_enabled",
        "time_interpolation_enabled",
        "censored_scalar_residual_enabled",
        "aggregate_score_enabled",
        "pass_fail_assignment_enabled",
        "automatic_cell_state_coupling",
    }
    if any(measurement.get(key) is not False for key in measurement_false):
        raise PhhInjuryTrajectoryError("PHH injury measurement operator escaped fail-closed policy")
    if frozen.get("version") != FROZEN_EVALUATION_VERSION:
        raise PhhInjuryTrajectoryError("PHH injury frozen-evaluation version changed")
    if len(frozen.get("required_submission_fields", ())) != 12:
        raise PhhInjuryTrajectoryError("PHH injury frozen submission contract changed")
    frozen_true = {
        "source_study_disjoint_from_nonheldout_required",
        "manual_primary_source_review_required",
        "donor_identity_scope_review_required",
        "independent_review_attestation_required",
        "frozen_model_required",
        "descriptive_exact_assay_residuals_allowed",
    }
    frozen_false = {
        "post_freeze_parameter_refit_allowed",
        "aggregate_score_enabled",
        "pass_fail_assignment_enabled",
        "automatic_parameter_activation",
        "automatic_cell_state_coupling",
    }
    if any(frozen.get(key) is not True for key in frozen_true) or any(
        frozen.get(key) is not False for key in frozen_false
    ):
        raise PhhInjuryTrajectoryError("PHH injury frozen evaluation escaped policy")
    policy_false = {
        "donor_id_may_cross_split_roles",
        "biological_replicate_is_independent_donor",
        "aggregate_donor_count_may_reconstruct_donor_ids",
        "unit_conversion_without_explicit_conversion_provenance",
        "time_interpolation_for_validation",
        "unknown_endpoint_means_no_effect",
        "automatic_parameter_activation",
        "automatic_cell_state_coupling",
    }
    if any(policy.get(key) is not False for key in policy_false):
        raise PhhInjuryTrajectoryError("PHH injury trajectory policy escaped fail-closed state")
    if (
        policy.get("manual_primary_source_review_required") is not True
        or policy.get("frozen_model_required_before_independent_heldout_evaluation")
        is not True
    ):
        raise PhhInjuryTrajectoryError("PHH injury trajectory review policy changed")
    return payload


def _required_text(row: dict[str, str], field: str, row_number: int) -> str:
    value = row[field].strip()
    if not value or value.lower() == _NULL_TOKEN:
        raise PhhInjuryTrajectoryError(f"row {row_number}: {field} is required")
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
        raise PhhInjuryTrajectoryError(
            f"row {row_number}: {field} must be one finite number"
        )
    value = float(token)
    if not math.isfinite(value):
        raise PhhInjuryTrajectoryError(f"row {row_number}: {field} must be finite")
    return value


def _nonnegative_optional(
    row: dict[str, str],
    field: str,
    row_number: int,
) -> float | None:
    value = _number(row, field, row_number, optional=True)
    if value is not None and value < 0.0:
        raise PhhInjuryTrajectoryError(
            f"row {row_number}: {field} must be non-negative"
        )
    return value


def _record(row: dict[str, str], row_number: int) -> PhhInjuryTrajectoryRecord:
    split_role = _required_text(row, "split_role", row_number)
    if split_role not in _ALLOWED_SPLIT_ROLES:
        raise PhhInjuryTrajectoryError(
            f"row {row_number}: unsupported split_role {split_role!r}"
        )
    species = _required_text(row, "species", row_number)
    if species != "Homo sapiens":
        raise PhhInjuryTrajectoryError(
            f"row {row_number}: non-human record cannot enter the PHH trajectory set"
        )
    biological_system = _required_text(row, "biological_system", row_number)
    if "primary_human_hepatocyte" not in biological_system.lower():
        raise PhhInjuryTrajectoryError(
            f"row {row_number}: biological_system is outside primary human hepatocytes"
        )
    concentration = _number(row, "challenge_concentration", row_number)
    exposure = _number(row, "exposure_time_h", row_number)
    raw_value = _number(row, "raw_value", row_number)
    assert concentration is not None and exposure is not None and raw_value is not None
    if concentration < 0.0 or exposure < 0.0:
        raise PhhInjuryTrajectoryError(
            f"row {row_number}: challenge concentration and exposure time must be non-negative"
        )

    intervention = _optional_text(row, "intervention")
    intervention_start = _nonnegative_optional(
        row, "intervention_start_h", row_number
    )
    if (intervention is None) != (intervention_start is None):
        raise PhhInjuryTrajectoryError(
            f"row {row_number}: intervention and intervention_start_h must appear together"
        )
    uncertainty_type = _optional_text(row, "uncertainty_type")
    uncertainty_value = _nonnegative_optional(row, "uncertainty_value", row_number)
    if (uncertainty_type is None) != (uncertainty_value is None):
        raise PhhInjuryTrajectoryError(
            f"row {row_number}: uncertainty_type and uncertainty_value must appear together"
        )
    censoring_flag = _required_text(row, "censoring_flag", row_number)
    limit_of_quantification = _nonnegative_optional(
        row, "limit_of_quantification", row_number
    )
    if (
        censoring_flag.strip().lower() not in {"none", "uncensored"}
        and limit_of_quantification is None
    ):
        raise PhhInjuryTrajectoryError(
            f"row {row_number}: censored record requires limit_of_quantification"
        )
    denominator = _required_text(row, "normalization_denominator", row_number)
    viable_count = _nonnegative_optional(
        row, "viable_cell_count_at_measurement", row_number
    )
    if (
        "cell" in denominator.lower()
        and viable_count is None
    ):
        raise PhhInjuryTrajectoryError(
            f"row {row_number}: cell-normalized record requires viable_cell_count_at_measurement"
        )
    if viable_count == 0.0:
        raise PhhInjuryTrajectoryError(
            f"row {row_number}: viable_cell_count_at_measurement must be positive"
        )

    return PhhInjuryTrajectoryRecord(
        record_id=_required_text(row, "record_id", row_number),
        donor_id=_required_text(row, "donor_id", row_number),
        split_role=split_role,
        source_study_id=_required_text(row, "source_study_id", row_number),
        source_locator=_required_text(row, "source_locator", row_number),
        species=species,
        biological_system=biological_system,
        culture_format=_required_text(row, "culture_format", row_number),
        challenge=_required_text(row, "challenge", row_number),
        challenge_concentration=concentration,
        challenge_concentration_unit=_required_text(
            row, "challenge_concentration_unit", row_number
        ),
        exposure_time_h=exposure,
        endpoint=_required_text(row, "endpoint", row_number),
        assay=_required_text(row, "assay", row_number),
        raw_value=raw_value,
        raw_unit=_required_text(row, "raw_unit", row_number),
        biological_replicate_id=_required_text(
            row, "biological_replicate_id", row_number
        ),
        normalization_denominator=denominator,
        censoring_flag=censoring_flag,
        intervention=intervention,
        intervention_start_h=intervention_start,
        washout_time_h=_nonnegative_optional(row, "washout_time_h", row_number),
        recovery_followup_h=_nonnegative_optional(
            row, "recovery_followup_h", row_number
        ),
        technical_replicate_id=_optional_text(row, "technical_replicate_id"),
        uncertainty_type=uncertainty_type,
        uncertainty_value=uncertainty_value,
        limit_of_quantification=limit_of_quantification,
        viable_cell_count_at_measurement=viable_count,
        fate_label=_optional_text(row, "fate_label"),
    )


def load_phh_injury_trajectory_dataset(
    path: Path = DEFAULT_TRAJECTORY_PATH,
    *,
    contract_path: Path = CONTRACT_PATH,
) -> PhhInjuryTrajectoryDataset:
    contract = load_phh_injury_trajectory_contract(contract_path)
    if not path.is_file():
        raise PhhInjuryTrajectoryError(f"PHH injury trajectory file is absent: {path}")
    required = tuple(str(item["id"]) for item in contract["required_columns"])
    conditional = tuple(str(item["id"]) for item in contract["conditional_columns"])
    expected_headers = required + conditional
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fieldnames = tuple(reader.fieldnames or ())
        if not fieldnames or len(fieldnames) != len(set(fieldnames)):
            raise PhhInjuryTrajectoryError("trajectory CSV has missing or duplicate headers")
        missing = tuple(field for field in expected_headers if field not in fieldnames)
        extra = tuple(field for field in fieldnames if field not in expected_headers)
        if missing or extra:
            details = []
            if missing:
                details.append("missing: " + ", ".join(missing))
            if extra:
                details.append("unversioned extra: " + ", ".join(extra))
            raise PhhInjuryTrajectoryError(
                "trajectory CSV header does not match the versioned contract ("
                + "; ".join(details)
                + ")"
            )
        records: list[PhhInjuryTrajectoryRecord] = []
        for row_number, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise PhhInjuryTrajectoryError(
                    f"row {row_number}: malformed CSV record"
                )
            records.append(_record(row, row_number))
    if not records:
        raise PhhInjuryTrajectoryError("trajectory CSV contains no records")

    record_ids = [record.record_id for record in records]
    duplicate_record_ids = tuple(
        item for item, count in Counter(record_ids).items() if count > 1
    )
    if duplicate_record_ids:
        raise PhhInjuryTrajectoryError(
            "duplicate record_id values: " + ", ".join(sorted(duplicate_record_ids))
        )
    observation_keys = [record.observation_key for record in records]
    if len(observation_keys) != len(set(observation_keys)):
        raise PhhInjuryTrajectoryError(
            "duplicate donor/replicate/condition/time/endpoint/assay observation"
        )

    donor_roles: dict[tuple[str, str], set[str]] = defaultdict(set)
    study_roles: dict[str, set[str]] = defaultdict(set)
    for record in records:
        donor_roles[record.donor_key].add(record.split_role)
        study_roles[record.source_study_id].add(record.split_role)
    leaking_donors = tuple(
        donor_key for donor_key, roles in donor_roles.items() if len(roles) > 1
    )
    if leaking_donors:
        labels = tuple(f"{study}:{donor}" for study, donor in leaking_donors)
        raise PhhInjuryTrajectoryError(
            "donor leakage across split roles: " + ", ".join(sorted(labels))
        )
    leaking_heldout_studies = tuple(
        study
        for study, roles in study_roles.items()
        if "independent_heldout" in roles and len(roles) > 1
    )
    if leaking_heldout_studies:
        raise PhhInjuryTrajectoryError(
            "independent-heldout source study also appears in a non-heldout split: "
            + ", ".join(sorted(leaking_heldout_studies))
        )
    return PhhInjuryTrajectoryDataset(
        version=INTAKE_VERSION,
        contract_id=str(contract["contract_id"]),
        delivery_path=_display_path(path),
        artifact_sha256=_sha256(path),
        contract_sha256=_sha256(contract_path),
        records=tuple(records),
    )


def audit_phh_injury_trajectory_dataset(
    dataset: PhhInjuryTrajectoryDataset,
) -> PhhInjuryTrajectoryAudit:
    records_by_split = Counter(record.split_role for record in dataset.records)
    donors_by_split: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for record in dataset.records:
        donors_by_split[record.split_role].add(record.donor_key)
    roles = tuple(sorted(records_by_split))
    blockers = (
        "Structural validity does not replace manual review against every primary-source row.",
        "Anonymous donor labels are scoped to source_study_id; cross-study donor linkage is not verified by the CSV.",
        "No model parameter, fate law or cell state is activated by trajectory intake.",
    )
    return PhhInjuryTrajectoryAudit(
        version=dataset.version,
        contract_id=dataset.contract_id,
        status="structurally_valid_manual_primary_source_review_required",
        delivery_path=dataset.delivery_path,
        artifact_sha256=dataset.artifact_sha256,
        contract_sha256=dataset.contract_sha256,
        record_count=len(dataset.records),
        donor_count=len({record.donor_key for record in dataset.records}),
        biological_replicate_count=len(
            {
                (
                    record.source_study_id,
                    record.donor_id,
                    record.biological_replicate_id,
                )
                for record in dataset.records
            }
        ),
        source_study_count=len(
            {record.source_study_id for record in dataset.records}
        ),
        endpoint_count=len({record.endpoint for record in dataset.records}),
        assay_count=len({record.assay for record in dataset.records}),
        split_roles_present=roles,
        record_count_by_split={
            role: records_by_split.get(role, 0) for role in sorted(_ALLOWED_SPLIT_ROLES)
        },
        donor_count_by_split={
            role: len(donors_by_split.get(role, set()))
            for role in sorted(_ALLOWED_SPLIT_ROLES)
        },
        donor_disjoint_split=True,
        independent_heldout_study_disjoint=True,
        donor_identity_scope="source_study_id_plus_donor_id",
        cross_study_donor_linkage_verified=False,
        manual_primary_source_review_required=True,
        manual_primary_source_review_complete=False,
        automatic_parameter_activation=False,
        automatic_cell_state_coupling=False,
        blockers=blockers,
    )


def _validate_sha256(value: str, label: str) -> None:
    if not _SHA256_RE.fullmatch(value):
        raise PhhInjuryTrajectoryError(f"{label} must be lowercase SHA-256")


def _prediction_context(point: PhhInjuryPredictionPoint) -> tuple[object, ...]:
    return (
        point.record_id,
        point.donor_id,
        point.source_study_id,
        point.split_role,
        point.species,
        point.biological_system,
        point.culture_format,
        point.challenge,
        point.challenge_concentration,
        point.challenge_concentration_unit,
        point.exposure_time_h,
        point.endpoint,
        point.assay,
        point.biological_replicate_id,
        point.technical_replicate_id,
        point.normalization_denominator,
        point.intervention,
        point.intervention_start_h,
        point.washout_time_h,
        point.recovery_followup_h,
    )


def _record_prediction_context(
    record: PhhInjuryTrajectoryRecord,
) -> tuple[object, ...]:
    return (
        record.record_id,
        record.donor_id,
        record.source_study_id,
        record.split_role,
        record.species,
        record.biological_system,
        record.culture_format,
        record.challenge,
        record.challenge_concentration,
        record.challenge_concentration_unit,
        record.exposure_time_h,
        record.endpoint,
        record.assay,
        record.biological_replicate_id,
        record.technical_replicate_id,
        record.normalization_denominator,
        record.intervention,
        record.intervention_start_h,
        record.washout_time_h,
        record.recovery_followup_h,
    )


def evaluate_frozen_phh_injury_submission(
    dataset: PhhInjuryTrajectoryDataset,
    submission: PhhInjuryFrozenSubmission,
    attestation: PhhInjuryEvaluationAttestation,
) -> PhhInjuryFrozenEvaluation:
    """Project a frozen model into exact uncensored held-out assay records."""

    audit = audit_phh_injury_trajectory_dataset(dataset)
    if not all(
        (
            attestation.manual_primary_source_review_complete,
            attestation.donor_identity_scope_review_complete,
            attestation.independent_heldout_study_review_complete,
            attestation.independent_reviewer_attested,
        )
    ):
        raise PhhInjuryTrajectoryError(
            "manual source, donor identity, heldout-study and independent-review attestations are all required"
        )
    for label, checksum in (
        ("model artifact", submission.model_artifact_sha256),
        ("parameter manifest", submission.parameter_manifest_sha256),
        ("dataset artifact", submission.dataset_artifact_sha256),
        ("trajectory contract", submission.trajectory_contract_sha256),
        ("source review artifact", submission.source_review_artifact_sha256),
        ("acceptance criteria artifact", submission.acceptance_criteria_artifact_sha256),
    ):
        _validate_sha256(checksum, label)
    if (
        submission.dataset_artifact_sha256 != dataset.artifact_sha256
        or submission.trajectory_contract_sha256 != dataset.contract_sha256
    ):
        raise PhhInjuryTrajectoryError(
            "submission checksums do not identify the audited dataset and contract"
        )
    if (
        submission.measurement_operator_version != MEASUREMENT_OPERATOR_VERSION
        or submission.split_role != "independent_heldout"
        or not submission.frozen_before_heldout_outcome_access
        or submission.parameter_refit_count_after_freeze != 0
    ):
        raise PhhInjuryTrajectoryError(
            "submission is not a pre-outcome frozen independent-heldout model"
        )
    if (
        not submission.submission_id
        or not submission.model_id
        or not audit.donor_disjoint_split
        or not audit.independent_heldout_study_disjoint
    ):
        raise PhhInjuryTrajectoryError("submission identity or split audit is incomplete")

    heldout = tuple(
        record
        for record in dataset.records
        if record.split_role == "independent_heldout"
    )
    if not heldout:
        raise PhhInjuryTrajectoryError(
            "dataset contains no independent-heldout injury records"
        )
    censored = tuple(
        record
        for record in heldout
        if record.censoring_flag.strip().lower() not in {"none", "uncensored"}
    )
    if censored:
        raise PhhInjuryTrajectoryError(
            "censored heldout records require a separately validated censored-data operator"
        )
    points_by_id = {point.record_id: point for point in submission.points}
    if len(points_by_id) != len(submission.points):
        raise PhhInjuryTrajectoryError("submission contains duplicate prediction record IDs")
    heldout_by_id = {record.record_id: record for record in heldout}
    if set(points_by_id) != set(heldout_by_id):
        raise PhhInjuryTrajectoryError(
            "submission must predict every and only independent-heldout record"
        )

    residuals: list[PhhInjuryAssayResidual] = []
    for record_id in sorted(heldout_by_id):
        record = heldout_by_id[record_id]
        point = points_by_id[record_id]
        if _prediction_context(point) != _record_prediction_context(record):
            raise PhhInjuryTrajectoryError(
                f"{record_id}: prediction context does not exactly match the heldout record"
            )
        if point.predicted_unit != record.raw_unit:
            raise PhhInjuryTrajectoryError(
                f"{record_id}: prediction unit differs from the source assay unit"
            )
        if not math.isfinite(point.predicted_value):
            raise PhhInjuryTrajectoryError(
                f"{record_id}: predicted value must be finite"
            )
        residuals.append(
            PhhInjuryAssayResidual(
                record_id=record.record_id,
                donor_id=record.donor_id,
                source_study_id=record.source_study_id,
                endpoint=record.endpoint,
                assay=record.assay,
                observed_value=record.raw_value,
                predicted_value=point.predicted_value,
                residual=point.predicted_value - record.raw_value,
                unit=record.raw_unit,
                normalization_denominator=record.normalization_denominator,
            )
        )
    return PhhInjuryFrozenEvaluation(
        version=FROZEN_EVALUATION_VERSION,
        status="exact_heldout_assay_residuals_no_score_no_pass_no_activation",
        submission_id=submission.submission_id,
        evaluated_record_count=len(residuals),
        residuals=tuple(residuals),
        unit_conversion_performed=False,
        dose_interpolation_performed=False,
        time_interpolation_performed=False,
        fitted_parameter_count=0,
        aggregate_score=None,
        acceptance_threshold=None,
        pass_fail_assigned=False,
        predictive_claim_assigned=False,
        may_drive_cell_state=False,
    )


def phh_injury_trajectory_intake_snapshot(
    path: Path = DEFAULT_TRAJECTORY_PATH,
) -> dict[str, object]:
    contract = load_phh_injury_trajectory_contract()
    contract_sha256 = _sha256(CONTRACT_PATH)
    measurement = contract["measurement_operator"]
    frozen = contract["frozen_evaluation"]
    if not path.is_file():
        return {
            "version": INTAKE_VERSION,
            "contract_id": contract["contract_id"],
            "status": "awaiting_donor_resolved_phh_injury_trajectories",
            "delivery_path": str(contract["expected_delivery_path"]),
            "file_present": False,
            "contract_sha256": contract_sha256,
            "expected_header_count": len(contract["required_columns"])
            + len(contract["conditional_columns"]),
            "split_leakage_guard_enabled": True,
            "independent_heldout_study_guard_enabled": True,
            "measurement_operator": {
                **measurement,
                "structure_ready": True,
                "numeric_projection_ready": False,
                "projectable_record_count": 0,
            },
            "frozen_evaluation": {
                **frozen,
                "contract_ready": True,
                "evaluation_ready": False,
                "independent_heldout_result_count": 0,
            },
            "current_delivery": {
                "donor_resolved_raw_record_count": 0,
                "donor_count": 0,
                "biological_replicate_count": 0,
                "source_study_count": 0,
                "endpoint_count": 0,
                "assay_count": 0,
                "donor_disjoint_split_count": 0,
                "independent_heldout_donor_count": 0,
                "independent_heldout_trajectory_count": 0,
                "numeric_measurement_projection_count": 0,
                "independent_heldout_result_count": 0,
                "general_fate_law_count": 0,
                "automatic_parameter_activation": False,
                "automatic_cell_state_coupling": False,
            },
            "blockers": [
                "No donor-resolved PHH injury trajectory file has been delivered at the versioned path.",
                "Manual primary-source review and donor-identity review have not occurred.",
                "No frozen independent-heldout model submission exists.",
            ],
        }
    try:
        dataset = load_phh_injury_trajectory_dataset(path)
        audit = audit_phh_injury_trajectory_dataset(dataset)
    except (
        PhhInjuryTrajectoryError,
        OSError,
        UnicodeError,
        csv.Error,
        json.JSONDecodeError,
    ) as exc:
        return {
            "version": INTAKE_VERSION,
            "contract_id": contract["contract_id"],
            "status": "rejected_invalid_phh_injury_trajectory_delivery",
            "delivery_path": _display_path(path),
            "file_present": True,
            "contract_sha256": contract_sha256,
            "expected_header_count": len(contract["required_columns"])
            + len(contract["conditional_columns"]),
            "split_leakage_guard_enabled": True,
            "independent_heldout_study_guard_enabled": True,
            "measurement_operator": {
                **measurement,
                "structure_ready": True,
                "numeric_projection_ready": False,
                "projectable_record_count": 0,
            },
            "frozen_evaluation": {
                **frozen,
                "contract_ready": True,
                "evaluation_ready": False,
                "independent_heldout_result_count": 0,
            },
            "current_delivery": {
                "donor_resolved_raw_record_count": 0,
                "donor_count": 0,
                "biological_replicate_count": 0,
                "source_study_count": 0,
                "endpoint_count": 0,
                "assay_count": 0,
                "donor_disjoint_split_count": 0,
                "independent_heldout_donor_count": 0,
                "independent_heldout_trajectory_count": 0,
                "numeric_measurement_projection_count": 0,
                "independent_heldout_result_count": 0,
                "general_fate_law_count": 0,
                "automatic_parameter_activation": False,
                "automatic_cell_state_coupling": False,
            },
            "blockers": [str(exc)],
        }
    heldout_records = tuple(
        record for record in dataset.records if record.split_role == "independent_heldout"
    )
    heldout_donors = {record.donor_key for record in heldout_records}
    delivery = {
        "donor_resolved_raw_record_count": audit.record_count,
        "donor_count": audit.donor_count,
        "biological_replicate_count": audit.biological_replicate_count,
        "source_study_count": audit.source_study_count,
        "endpoint_count": audit.endpoint_count,
        "assay_count": audit.assay_count,
        "donor_disjoint_split_count": len(audit.split_roles_present),
        "independent_heldout_donor_count": len(heldout_donors),
        "independent_heldout_trajectory_count": len(heldout_records),
        "numeric_measurement_projection_count": 0,
        "independent_heldout_result_count": 0,
        "general_fate_law_count": 0,
        "automatic_parameter_activation": False,
        "automatic_cell_state_coupling": False,
    }
    return {
        **audit.to_dict(),
        "file_present": True,
        "expected_header_count": len(contract["required_columns"])
        + len(contract["conditional_columns"]),
        "split_leakage_guard_enabled": True,
        "independent_heldout_study_guard_enabled": True,
        "measurement_operator": {
            **measurement,
            "structure_ready": True,
            "numeric_projection_ready": False,
            "projectable_record_count": 0,
        },
        "frozen_evaluation": {
            **frozen,
            "contract_ready": True,
            "evaluation_ready": False,
            "independent_heldout_result_count": 0,
        },
        "current_delivery": delivery,
    }
