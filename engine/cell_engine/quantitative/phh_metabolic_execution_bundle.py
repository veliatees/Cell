"""Fail-closed intake for a healthy-PHH Human-GEM execution package.

The package binds a context-extracted model, measured exchange bounds, an
explicit scale operator, objective, pinned solver reports and independent
validation by checksum. Structural completeness never runs FBA automatically
and never makes the resulting fluxes authoritative for cell state.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cell_engine.quantitative.constraint_numerics import (
    DUAL_FEASIBILITY_TOLERANCE,
    OBJECTIVE_ABSOLUTE_TOLERANCE,
    PINNED_SCIPY_VERSION,
    PRIMAL_FEASIBILITY_TOLERANCE,
    SOLVER_METHOD,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "evidence_intake"
    / "phh_metabolic_execution_bundle_contract.v1.json"
)
DEFAULT_BUNDLE_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "evidence_intake"
    / "incoming"
    / "phh_metabolic_execution"
    / "latest"
    / "phh_metabolic_execution_bundle.json"
)
CONTRACT_SCHEMA_VERSION = "cell.phh-metabolic-execution-bundle-contract.v1"
BUNDLE_SCHEMA_VERSION = "cell.phh-metabolic-execution-bundle.v1"
INTAKE_VERSION = "phh_metabolic_execution_bundle_intake_v1"
EXECUTION_GATE_VERSION = "phh_metabolic_execution_gate_v1"
HUMAN_GEM_RELEASE_COMMIT = "635f533152dc5f7290ce04d12700eaa882273c3e"
HUMAN_GEM_SHA256 = "cc5a4383c6116b0c91f4db089cc640f29aec7e840249b573b74d3792c9ca4a7a"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_NUMBER_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
_DEVELOPMENT_SPLITS = frozenset({"calibration", "internal_validation"})
_HELDOUT_SPLIT = "independent_heldout"
_REQUIRED_ARTIFACTS = (
    "context_model",
    "context_extraction_report",
    "exchange_bounds",
    "objective_specification",
    "scale_conversion_report",
    "solver_manifest",
    "fba_result",
    "fva_result",
    "infeasibility_report",
    "independent_validation",
)
_REQUIRED_CONTEXT_FIELDS = (
    "species",
    "biological_system",
    "tissue_health_state",
    "donor_or_cohort_id",
    "preparation_context",
    "culture_format",
    "nutritional_state",
    "liver_zone",
    "oxygen_context",
    "temperature_c",
    "sampling_timepoint",
)
_REQUIRED_SPLIT_FIELDS = (
    "development_donor_ids",
    "development_study_ids",
    "heldout_donor_ids",
    "heldout_study_ids",
)


class PHHMetabolicExecutionBundleError(ValueError):
    """Raised when a PHH metabolic execution package violates the contract."""


@dataclass(frozen=True)
class ArtifactReference:
    path: str
    sha256: str


@dataclass(frozen=True)
class PHHMetabolicExecutionBundle:
    bundle_id: str
    bundle_path: str
    bundle_sha256: str
    contract_sha256: str
    artifacts: dict[str, ArtifactReference]
    context: dict[str, object]
    splits: dict[str, tuple[str, ...]]
    exchange_bound_count: int
    independent_validation_record_count: int
    target_model_flux_unit: str
    structurally_complete: bool
    fba_execution_allowed: bool
    runtime_flux_coupling_allowed: bool


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
    if not raw:
        raise PHHMetabolicExecutionBundleError(f"{label} path is required")
    path = Path(raw)
    resolved = path.resolve() if path.is_absolute() else (REPOSITORY_ROOT / path).resolve()
    if not resolved.is_file():
        raise PHHMetabolicExecutionBundleError(f"{label} does not exist: {raw}")
    return resolved


def _artifact_reference(raw: object, *, label: str) -> tuple[ArtifactReference, Path]:
    if not isinstance(raw, dict) or set(raw) != {"path", "sha256"}:
        raise PHHMetabolicExecutionBundleError(
            f"{label} must contain only path and sha256"
        )
    path_token = raw.get("path")
    sha_token = raw.get("sha256")
    if not isinstance(path_token, str) or not isinstance(sha_token, str):
        raise PHHMetabolicExecutionBundleError(f"{label} reference is malformed")
    expected = sha_token.lower()
    if not _SHA256_RE.fullmatch(expected):
        raise PHHMetabolicExecutionBundleError(f"{label} SHA-256 is malformed")
    path = _artifact_path(path_token, label=label)
    if _sha256(path) != expected:
        raise PHHMetabolicExecutionBundleError(f"{label} SHA-256 mismatch")
    return ArtifactReference(path=_display_path(path), sha256=expected), path


def _json_artifact(path: Path, *, schema: str, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != schema:
        raise PHHMetabolicExecutionBundleError(f"{label} schema is unsupported")
    return payload


def _finite(raw: object, *, label: str) -> float:
    if isinstance(raw, bool):
        raise PHHMetabolicExecutionBundleError(f"{label} must be finite")
    try:
        value = float(raw)
    except (TypeError, ValueError) as error:
        raise PHHMetabolicExecutionBundleError(f"{label} must be finite") from error
    if not math.isfinite(value):
        raise PHHMetabolicExecutionBundleError(f"{label} must be finite")
    return value


def _csv_number(row: dict[str, str], field: str, row_number: int) -> float:
    token = row[field].strip()
    if not _NUMBER_RE.fullmatch(token):
        raise PHHMetabolicExecutionBundleError(
            f"row {row_number}: {field} must be one finite number"
        )
    return _finite(token, label=f"row {row_number}: {field}")


def _required_csv_text(row: dict[str, str], field: str, row_number: int) -> str:
    token = row[field].strip()
    if not token or token.lower() == "null":
        raise PHHMetabolicExecutionBundleError(
            f"row {row_number}: {field} is required"
        )
    return token


def load_phh_metabolic_execution_bundle_contract(
    path: Path = CONTRACT_PATH,
) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != CONTRACT_SCHEMA_VERSION:
        raise PHHMetabolicExecutionBundleError(
            "unsupported PHH metabolic execution contract"
        )
    candidate = payload.get("candidate_reconstruction")
    gate = payload.get("execution_gate")
    policy = payload.get("policy")
    if not all(isinstance(item, dict) for item in (candidate, gate, policy)):
        raise PHHMetabolicExecutionBundleError(
            "PHH metabolic execution contract is malformed"
        )
    if (
        payload.get("bundle_schema_version") != BUNDLE_SCHEMA_VERSION
        or tuple(payload.get("required_context_fields", ())) != _REQUIRED_CONTEXT_FIELDS
        or tuple(payload.get("required_split_fields", ())) != _REQUIRED_SPLIT_FIELDS
        or tuple(payload.get("required_artifacts", ())) != _REQUIRED_ARTIFACTS
    ):
        raise PHHMetabolicExecutionBundleError(
            "PHH metabolic execution contract fields changed"
        )
    if (
        candidate.get("model_family") != "Human-GEM"
        or candidate.get("model_version") != "2.0.0"
        or candidate.get("release_commit") != HUMAN_GEM_RELEASE_COMMIT
        or candidate.get("artifact_sha256") != HUMAN_GEM_SHA256
    ):
        raise PHHMetabolicExecutionBundleError("Human-GEM identity changed")
    if len(payload.get("exchange_bounds_header", ())) != 14:
        raise PHHMetabolicExecutionBundleError("exchange-bound header changed")
    if len(payload.get("independent_validation_header", ())) != 13:
        raise PHHMetabolicExecutionBundleError("validation-flux header changed")
    if gate.get("version") != EXECUTION_GATE_VERSION:
        raise PHHMetabolicExecutionBundleError("PHH metabolic execution gate changed")
    required_true = {
        "exact_human_gem_identity_required",
        "checksum_for_every_artifact_required",
        "healthy_primary_human_hepatocyte_context_required",
        "deterministic_context_extraction_required",
        "reaction_identity_audit_required",
        "structural_exception_resolution_required",
        "measured_exchange_bounds_required",
        "explicit_scale_conversion_operator_required",
        "directly_measured_objective_required",
        "pinned_solver_required",
        "fba_and_fva_reports_required",
        "infeasibility_report_required",
        "donor_disjoint_validation_required",
        "study_disjoint_heldout_validation_required",
        "bundle_frozen_before_heldout_access_required",
    }
    required_false = {
        "automatic_context_extraction",
        "automatic_bound_imputation",
        "automatic_objective_selection",
        "automatic_unit_conversion",
        "automatic_fba_execution",
        "automatic_runtime_flux_coupling",
    }
    if any(gate.get(key) is not True for key in required_true) or any(
        gate.get(key) is not False for key in required_false
    ):
        raise PHHMetabolicExecutionBundleError(
            "PHH metabolic execution gate escaped fail-closed policy"
        )
    policy_false = {
        "generic_human_gem_is_healthy_phh_model",
        "transcript_abundance_is_flux",
        "proteome_abundance_is_flux",
        "objective_optimum_is_measurement",
        "fba_supplies_time_dynamics",
        "reported_exchange_mean_may_replace_uncertainty_bound",
        "development_study_may_serve_as_independent_validation",
        "structural_bundle_completeness_implies_biological_validity",
        "automatic_parameter_activation",
        "automatic_cell_state_coupling",
    }
    if policy.get("manual_primary_source_review_required") is not True or any(
        policy.get(key) is not False for key in policy_false
    ):
        raise PHHMetabolicExecutionBundleError(
            "PHH metabolic execution policy escaped fail-closed state"
        )
    return payload


def _validate_context(raw: object) -> dict[str, object]:
    if not isinstance(raw, dict) or set(raw) != set(_REQUIRED_CONTEXT_FIELDS):
        raise PHHMetabolicExecutionBundleError("PHH metabolic context fields changed")
    if raw.get("species") != "Homo sapiens":
        raise PHHMetabolicExecutionBundleError("metabolic bundle must be human")
    biological_system = raw.get("biological_system")
    if not isinstance(biological_system, str) or "primary_human_hepatocyte" not in biological_system.lower():
        raise PHHMetabolicExecutionBundleError(
            "metabolic bundle is outside primary human hepatocytes"
        )
    health = raw.get("tissue_health_state")
    if not isinstance(health, str) or (
        "healthy" not in health.lower() and "non_diseased" not in health.lower()
    ):
        raise PHHMetabolicExecutionBundleError(
            "metabolic bundle requires healthy/non-diseased context"
        )
    for field in _REQUIRED_CONTEXT_FIELDS:
        if field == "temperature_c":
            temperature = _finite(raw[field], label="context.temperature_c")
            if not 0 < temperature < 100:
                raise PHHMetabolicExecutionBundleError(
                    "context.temperature_c is outside a physical assay range"
                )
        elif not isinstance(raw[field], str) or not str(raw[field]).strip():
            raise PHHMetabolicExecutionBundleError(
                f"context.{field} is required"
            )
    return dict(raw)


def _identifier_tuple(raw: object, *, label: str) -> tuple[str, ...]:
    if (
        not isinstance(raw, list)
        or not raw
        or any(not isinstance(item, str) or not item.strip() for item in raw)
        or len(set(raw)) != len(raw)
    ):
        raise PHHMetabolicExecutionBundleError(
            f"{label} must be a non-empty unique identifier list"
        )
    return tuple(raw)


def _validate_splits(raw: object) -> dict[str, tuple[str, ...]]:
    if not isinstance(raw, dict) or set(raw) != set(_REQUIRED_SPLIT_FIELDS):
        raise PHHMetabolicExecutionBundleError("PHH metabolic split fields changed")
    splits = {
        field: _identifier_tuple(raw[field], label=f"splits.{field}")
        for field in _REQUIRED_SPLIT_FIELDS
    }
    if set(splits["development_donor_ids"]).intersection(splits["heldout_donor_ids"]):
        raise PHHMetabolicExecutionBundleError(
            "development and held-out donors overlap"
        )
    if set(splits["development_study_ids"]).intersection(splits["heldout_study_ids"]):
        raise PHHMetabolicExecutionBundleError(
            "development and held-out studies overlap"
        )
    return splits


def _validate_exchange_bounds(
    path: Path,
    expected_header: tuple[str, ...],
    splits: dict[str, tuple[str, ...]],
    target_unit: str,
) -> int:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != expected_header:
            raise PHHMetabolicExecutionBundleError(
                "exchange-bound CSV header must exactly match the contract"
            )
        rows = list(reader)
    if not rows:
        raise PHHMetabolicExecutionBundleError("exchange-bound artifact is empty")
    reaction_ids: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        reaction_id = _required_csv_text(row, "reaction_id", row_number)
        if reaction_id in reaction_ids:
            raise PHHMetabolicExecutionBundleError(
                f"exchange reaction {reaction_id!r} is duplicated"
            )
        reaction_ids.add(reaction_id)
        study = _required_csv_text(row, "source_study_id", row_number)
        donor = _required_csv_text(row, "donor_or_cohort_id", row_number)
        split = _required_csv_text(row, "split_role", row_number)
        if (
            split not in _DEVELOPMENT_SPLITS
            or study not in splits["development_study_ids"]
            or donor not in splits["development_donor_ids"]
        ):
            raise PHHMetabolicExecutionBundleError(
                f"row {row_number}: exchange bound is outside development splits"
            )
        raw_lower = _csv_number(row, "raw_lower", row_number)
        raw_upper = _csv_number(row, "raw_upper", row_number)
        model_lower = _csv_number(row, "model_lower", row_number)
        model_upper = _csv_number(row, "model_upper", row_number)
        if raw_lower > raw_upper or model_lower > model_upper:
            raise PHHMetabolicExecutionBundleError(
                f"row {row_number}: exchange lower bound exceeds upper bound"
            )
        if _required_csv_text(row, "model_unit", row_number) != target_unit:
            raise PHHMetabolicExecutionBundleError(
                f"row {row_number}: exchange model unit disagrees with scale operator"
            )
        for field in (
            "raw_unit",
            "measurement_operator_id",
            "assay",
            "uncertainty_description",
        ):
            _required_csv_text(row, field, row_number)
        if _required_csv_text(
            row, "manual_primary_source_review_status", row_number
        ).lower() != "pass":
            raise PHHMetabolicExecutionBundleError(
                f"row {row_number}: exchange-bound source review must be pass"
            )
    return len(rows)


def _validate_independent_validation(
    path: Path,
    expected_header: tuple[str, ...],
    splits: dict[str, tuple[str, ...]],
) -> int:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != expected_header:
            raise PHHMetabolicExecutionBundleError(
                "independent-validation CSV header must exactly match the contract"
            )
        rows = list(reader)
    if not rows:
        raise PHHMetabolicExecutionBundleError(
            "independent-validation artifact is empty"
        )
    for row_number, row in enumerate(rows, start=2):
        study = _required_csv_text(row, "source_study_id", row_number)
        donor = _required_csv_text(row, "donor_or_cohort_id", row_number)
        split = _required_csv_text(row, "split_role", row_number)
        if (
            split != _HELDOUT_SPLIT
            or study not in splits["heldout_study_ids"]
            or donor not in splits["heldout_donor_ids"]
        ):
            raise PHHMetabolicExecutionBundleError(
                f"row {row_number}: validation record is not donor/study-disjoint heldout"
            )
        observed = _csv_number(row, "observed_value", row_number)
        predicted = _csv_number(row, "predicted_value", row_number)
        uncertainty = _csv_number(row, "uncertainty_value", row_number)
        if uncertainty < 0 or not math.isfinite(observed + predicted):
            raise PHHMetabolicExecutionBundleError(
                f"row {row_number}: validation values are invalid"
            )
        observed_unit = _required_csv_text(row, "observed_unit", row_number)
        predicted_unit = _required_csv_text(row, "predicted_unit", row_number)
        if observed_unit != predicted_unit:
            raise PHHMetabolicExecutionBundleError(
                f"row {row_number}: observed and predicted units differ"
            )
        for field in (
            "reaction_id",
            "uncertainty_type",
            "measurement_operator_id",
            "assay",
        ):
            _required_csv_text(row, field, row_number)
        if _required_csv_text(
            row, "manual_primary_source_review_status", row_number
        ).lower() != "pass":
            raise PHHMetabolicExecutionBundleError(
                f"row {row_number}: validation source review must be pass"
            )
    return len(rows)


def load_phh_metabolic_execution_bundle(
    path: Path = DEFAULT_BUNDLE_PATH,
) -> PHHMetabolicExecutionBundle:
    contract = load_phh_metabolic_execution_bundle_contract()
    if not path.exists():
        raise PHHMetabolicExecutionBundleError(
            f"PHH metabolic execution bundle not found: {_display_path(path)}"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    required_bundle_keys = {
        "schema_version",
        "bundle_id",
        "candidate_reconstruction",
        "context",
        "splits",
        "artifacts",
        "frozen_before_heldout_access",
        "manual_primary_source_review_status",
        "permissions",
    }
    if not isinstance(payload, dict) or set(payload) != required_bundle_keys:
        raise PHHMetabolicExecutionBundleError(
            "PHH metabolic execution bundle fields changed"
        )
    if payload.get("schema_version") != BUNDLE_SCHEMA_VERSION:
        raise PHHMetabolicExecutionBundleError(
            "unsupported PHH metabolic execution bundle schema"
        )
    bundle_id = payload.get("bundle_id")
    if not isinstance(bundle_id, str) or not bundle_id:
        raise PHHMetabolicExecutionBundleError("bundle_id is required")
    candidate = payload.get("candidate_reconstruction")
    if not isinstance(candidate, dict) or candidate != contract["candidate_reconstruction"]:
        raise PHHMetabolicExecutionBundleError(
            "bundle Human-GEM reconstruction identity changed"
        )
    context = _validate_context(payload.get("context"))
    splits = _validate_splits(payload.get("splits"))
    if payload.get("frozen_before_heldout_access") is not True:
        raise PHHMetabolicExecutionBundleError(
            "bundle must be frozen before heldout access"
        )
    if str(payload.get("manual_primary_source_review_status", "")).lower() != "pass":
        raise PHHMetabolicExecutionBundleError(
            "bundle manual primary-source review must be pass"
        )
    permissions = payload.get("permissions")
    if not isinstance(permissions, dict) or permissions != {
        "automatic_fba_execution": False,
        "automatic_runtime_flux_coupling": False,
        "automatic_dynamic_rate_initialization": False,
    }:
        raise PHHMetabolicExecutionBundleError(
            "bundle permissions escaped fail-closed state"
        )
    raw_artifacts = payload.get("artifacts")
    if not isinstance(raw_artifacts, dict) or set(raw_artifacts) != set(_REQUIRED_ARTIFACTS):
        raise PHHMetabolicExecutionBundleError(
            "bundle artifact set changed"
        )
    artifacts: dict[str, ArtifactReference] = {}
    artifact_paths: dict[str, Path] = {}
    for artifact_id in _REQUIRED_ARTIFACTS:
        reference, artifact_path = _artifact_reference(
            raw_artifacts[artifact_id], label=artifact_id
        )
        artifacts[artifact_id] = reference
        artifact_paths[artifact_id] = artifact_path

    extraction = _json_artifact(
        artifact_paths["context_extraction_report"],
        schema="cell.phh-context-extraction-report.v1",
        label="context extraction report",
    )
    required_extraction = {
        "schema_version",
        "algorithm_name",
        "algorithm_version",
        "algorithm_code_sha256",
        "input_artifact_sha256s",
        "generated_context_model_sha256",
        "included_reaction_count",
        "excluded_reaction_count",
        "deterministic_reproduction_pass",
        "reaction_identity_audit_pass",
        "structural_exception_resolution_complete",
        "automatic_imputation_used",
    }
    if set(extraction) != required_extraction:
        raise PHHMetabolicExecutionBundleError(
            "context extraction report fields changed"
        )
    if (
        extraction.get("generated_context_model_sha256")
        != artifacts["context_model"].sha256
        or extraction.get("deterministic_reproduction_pass") is not True
        or extraction.get("reaction_identity_audit_pass") is not True
        or extraction.get("structural_exception_resolution_complete") is not True
        or extraction.get("automatic_imputation_used") is not False
        or int(extraction.get("included_reaction_count", 0)) <= 0
        or int(extraction.get("excluded_reaction_count", -1)) < 0
        or not _SHA256_RE.fullmatch(str(extraction.get("algorithm_code_sha256", "")))
    ):
        raise PHHMetabolicExecutionBundleError(
            "context extraction report does not pass the execution gate"
        )
    input_hashes = extraction.get("input_artifact_sha256s")
    if (
        not isinstance(input_hashes, list)
        or not input_hashes
        or any(not isinstance(item, str) or not _SHA256_RE.fullmatch(item) for item in input_hashes)
    ):
        raise PHHMetabolicExecutionBundleError(
            "context extraction omics input checksums are incomplete"
        )

    scale = _json_artifact(
        artifact_paths["scale_conversion_report"],
        schema="cell.phh-flux-scale-operator.v1",
        label="scale conversion report",
    )
    required_scale = {
        "schema_version",
        "operator_id",
        "source_units",
        "target_model_unit",
        "equation",
        "denominator_definition",
        "uncertainty_propagation",
        "same_context_validation_pass",
        "automatic_unit_conversion",
    }
    if set(scale) != required_scale:
        raise PHHMetabolicExecutionBundleError("scale operator fields changed")
    target_unit = scale.get("target_model_unit")
    if (
        not isinstance(target_unit, str)
        or not target_unit
        or scale.get("same_context_validation_pass") is not True
        or scale.get("automatic_unit_conversion") is not False
        or not isinstance(scale.get("source_units"), list)
        or not scale["source_units"]
    ):
        raise PHHMetabolicExecutionBundleError(
            "scale operator does not pass the execution gate"
        )
    for field in ("operator_id", "equation", "denominator_definition", "uncertainty_propagation"):
        if not isinstance(scale.get(field), str) or not scale[field]:
            raise PHHMetabolicExecutionBundleError(
                f"scale operator {field} is required"
            )

    objective = _json_artifact(
        artifact_paths["objective_specification"],
        schema="cell.phh-fba-objective.v1",
        label="objective specification",
    )
    required_objective = {
        "schema_version",
        "objective_id",
        "reaction_coefficients",
        "model_flux_unit",
        "measurement_source_ids",
        "measurement_operator_id",
        "directly_measured_in_matched_phh_context",
        "automatic_objective_selection",
    }
    if set(objective) != required_objective:
        raise PHHMetabolicExecutionBundleError("objective specification fields changed")
    coefficients = objective.get("reaction_coefficients")
    if (
        not isinstance(coefficients, dict)
        or not coefficients
        or any(
            not isinstance(reaction_id, str)
            or not reaction_id
            or not math.isfinite(_finite(value, label="objective coefficient"))
            for reaction_id, value in coefficients.items()
        )
        or objective.get("model_flux_unit") != target_unit
        or objective.get("directly_measured_in_matched_phh_context") is not True
        or objective.get("automatic_objective_selection") is not False
        or not isinstance(objective.get("measurement_source_ids"), list)
        or not objective["measurement_source_ids"]
        or not isinstance(objective.get("measurement_operator_id"), str)
        or not objective["measurement_operator_id"]
    ):
        raise PHHMetabolicExecutionBundleError(
            "objective specification does not pass the execution gate"
        )

    solver = _json_artifact(
        artifact_paths["solver_manifest"],
        schema="cell.constraint-solver-manifest.v1",
        label="solver manifest",
    )
    if solver != {
        "schema_version": "cell.constraint-solver-manifest.v1",
        "backend": "scipy.optimize.linprog",
        "backend_version": PINNED_SCIPY_VERSION,
        "method": SOLVER_METHOD,
        "primal_feasibility_tolerance": PRIMAL_FEASIBILITY_TOLERANCE,
        "dual_feasibility_tolerance": DUAL_FEASIBILITY_TOLERANCE,
        "objective_absolute_tolerance": OBJECTIVE_ABSOLUTE_TOLERANCE,
    }:
        raise PHHMetabolicExecutionBundleError("solver manifest is not pinned")

    model_sha = artifacts["context_model"].sha256
    fba = _json_artifact(
        artifact_paths["fba_result"],
        schema="cell.phh-fba-result.v1",
        label="FBA result",
    )
    required_fba = {
        "schema_version",
        "context_model_sha256",
        "solver_manifest_sha256",
        "status",
        "objective_value",
        "max_mass_balance_residual",
        "max_bound_violation",
    }
    if (
        set(fba) != required_fba
        or fba.get("context_model_sha256") != model_sha
        or fba.get("solver_manifest_sha256") != artifacts["solver_manifest"].sha256
        or fba.get("status") != "optimal"
        or abs(_finite(fba.get("max_mass_balance_residual"), label="FBA mass residual"))
        > PRIMAL_FEASIBILITY_TOLERANCE * 10
        or abs(_finite(fba.get("max_bound_violation"), label="FBA bound violation"))
        > PRIMAL_FEASIBILITY_TOLERANCE * 10
    ):
        raise PHHMetabolicExecutionBundleError("FBA report does not pass numerical gates")
    _finite(fba.get("objective_value"), label="FBA objective")

    fva = _json_artifact(
        artifact_paths["fva_result"],
        schema="cell.phh-fva-result.v1",
        label="FVA result",
    )
    required_fva = {
        "schema_version",
        "context_model_sha256",
        "solver_manifest_sha256",
        "fraction_of_optimum",
        "reaction_range_count",
        "all_ranges_finite",
    }
    if (
        set(fva) != required_fva
        or fva.get("context_model_sha256") != model_sha
        or fva.get("solver_manifest_sha256") != artifacts["solver_manifest"].sha256
        or not 0 < _finite(fva.get("fraction_of_optimum"), label="FVA fraction") <= 1
        or int(fva.get("reaction_range_count", 0))
        != int(extraction["included_reaction_count"])
        or fva.get("all_ranges_finite") is not True
    ):
        raise PHHMetabolicExecutionBundleError("FVA report does not pass numerical gates")

    infeasibility = _json_artifact(
        artifact_paths["infeasibility_report"],
        schema="cell.phh-infeasibility-report.v1",
        label="infeasibility report",
    )
    if infeasibility != {
        "schema_version": "cell.phh-infeasibility-report.v1",
        "context_model_sha256": model_sha,
        "status": "feasible_no_relaxation_required",
        "minimum_total_mass_balance_slack": 0.0,
        "bound_relaxation_used": False,
        "reaction_or_metabolite_deletion_used": False,
    }:
        raise PHHMetabolicExecutionBundleError(
            "infeasibility report indicates an altered or relaxed model"
        )

    exchange_bound_count = _validate_exchange_bounds(
        artifact_paths["exchange_bounds"],
        tuple(contract["exchange_bounds_header"]),
        splits,
        target_unit,
    )
    validation_count = _validate_independent_validation(
        artifact_paths["independent_validation"],
        tuple(contract["independent_validation_header"]),
        splits,
    )
    return PHHMetabolicExecutionBundle(
        bundle_id=bundle_id,
        bundle_path=_display_path(path),
        bundle_sha256=_sha256(path),
        contract_sha256=_sha256(CONTRACT_PATH),
        artifacts=artifacts,
        context=context,
        splits=splits,
        exchange_bound_count=exchange_bound_count,
        independent_validation_record_count=validation_count,
        target_model_flux_unit=target_unit,
        structurally_complete=True,
        fba_execution_allowed=False,
        runtime_flux_coupling_allowed=False,
    )


def phh_metabolic_execution_bundle_intake_snapshot(
    path: Path = DEFAULT_BUNDLE_PATH,
) -> dict[str, object]:
    contract = load_phh_metabolic_execution_bundle_contract()
    if not path.exists():
        return {
            "version": INTAKE_VERSION,
            "contract_id": contract["contract_id"],
            "status": "awaiting_checksum_frozen_phh_metabolic_execution_bundle",
            "delivery_path": _display_path(path),
            "contract_sha256": _sha256(CONTRACT_PATH),
            "required_artifact_count": len(_REQUIRED_ARTIFACTS),
            "delivered_bundle_count": 0,
            "verified_artifact_count": 0,
            "measured_exchange_bound_count": 0,
            "independent_validation_record_count": 0,
            "structurally_complete_bundle_count": 0,
            "generic_solver_fixture_pass_count": 5,
            "fba_execution_allowed": False,
            "fva_execution_allowed": False,
            "runtime_flux_coupling_allowed": False,
            "automatic_context_extraction": False,
            "automatic_bound_imputation": False,
            "automatic_objective_selection": False,
            "automatic_unit_conversion": False,
            "blockers": (
                "checksum-frozen healthy-PHH context bundle is absent",
                "measured exchange bounds, objective and scale operator are absent",
                "donor- and study-disjoint independent flux validation is absent",
            ),
        }
    bundle = load_phh_metabolic_execution_bundle(path)
    return {
        "version": INTAKE_VERSION,
        "contract_id": contract["contract_id"],
        "status": "bundle_structurally_verified_pending_scientific_authorization",
        "delivery_path": bundle.bundle_path,
        "bundle_id": bundle.bundle_id,
        "bundle_sha256": bundle.bundle_sha256,
        "contract_sha256": bundle.contract_sha256,
        "required_artifact_count": len(_REQUIRED_ARTIFACTS),
        "delivered_bundle_count": 1,
        "verified_artifact_count": len(bundle.artifacts),
        "measured_exchange_bound_count": bundle.exchange_bound_count,
        "independent_validation_record_count": bundle.independent_validation_record_count,
        "structurally_complete_bundle_count": int(bundle.structurally_complete),
        "generic_solver_fixture_pass_count": 5,
        "fba_execution_allowed": False,
        "fva_execution_allowed": False,
        "runtime_flux_coupling_allowed": False,
        "automatic_context_extraction": False,
        "automatic_bound_imputation": False,
        "automatic_objective_selection": False,
        "automatic_unit_conversion": False,
        "blockers": (
            "structural bundle review does not imply biological validity",
            "independent scientific authorization has not been recorded",
            "runtime flux coupling remains disabled",
        ),
    }


def validate_phh_metabolic_execution_bundle_intake_snapshot(
    payload: dict[str, object],
) -> None:
    if payload.get("version") != INTAKE_VERSION:
        raise ValueError("unexpected PHH metabolic bundle intake version")
    if payload.get("required_artifact_count") != 10:
        raise ValueError("PHH metabolic bundle artifact count changed")
    if payload.get("generic_solver_fixture_pass_count") != 5:
        raise ValueError("generic constraint solver verification changed")
    if any(
        payload.get(key) is not False
        for key in (
            "fba_execution_allowed",
            "fva_execution_allowed",
            "runtime_flux_coupling_allowed",
            "automatic_context_extraction",
            "automatic_bound_imputation",
            "automatic_objective_selection",
            "automatic_unit_conversion",
        )
    ):
        raise ValueError("PHH metabolic bundle intake escaped fail-closed state")
