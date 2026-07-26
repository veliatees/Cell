"""Provenance and safety boundary for future hepatocyte generative models."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from hashlib import sha256
from importlib import metadata, util
from pathlib import Path
from typing import Literal

from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain


DATE_VERIFIED = "2026-07-14"
SHA256_LENGTH = 64
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DONOR_MANIFEST_CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "evidence_intake"
    / "phh_generative_donor_manifest_contract.v1.json"
)
DEFAULT_DONOR_MANIFEST_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "evidence_intake"
    / "incoming"
    / "phh_generative_donor"
    / "latest"
    / "phh_generative_donor_manifest.json"
)
DONOR_MANIFEST_CONTRACT_SCHEMA_VERSION = (
    "cell.phh-generative-donor-manifest-contract.v1"
)
DONOR_MANIFEST_DELIVERY_SCHEMA_VERSION = "cell.phh-generative-donor-manifest.v1"
DONOR_MANIFEST_INTAKE_VERSION = "phh_generative_donor_manifest_intake_v1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

GENERATIVE_SOURCES: dict[str, SourceReference] = {
    "autoencoding_variational_bayes": SourceReference(
        id="autoencoding_variational_bayes",
        title="Auto-Encoding Variational Bayes",
        url="https://arxiv.org/abs/1312.6114",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Original reparameterized variational lower-bound framework underlying VAEs.",
    ),
    "scvi_single_cell_generative_model": SourceReference(
        id="scvi_single_cell_generative_model",
        title="Deep generative modeling for single-cell transcriptomics",
        url="https://www.nature.com/articles/s41592-018-0229-2",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="scVI models single-cell expression probabilistically while accounting for count noise and batch effects.",
    ),
    "scgen_perturbation_model": SourceReference(
        id="scgen_perturbation_model",
        title="scGen predicts single-cell perturbation responses",
        url="https://www.nature.com/articles/s41592-019-0494-8",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="VAE-based perturbation-response modeling with explicit out-of-sample evaluation.",
    ),
    "scvi_tools_documentation": SourceReference(
        id="scvi_tools_documentation",
        title="scvi-tools documentation",
        url="https://docs.scvi-tools.org/en/stable/",
        source_type="tool_doc",
        date_verified=DATE_VERIFIED,
        notes="Current probabilistic single-cell modeling software boundary; not installed as a core dependency.",
    ),
}


@dataclass(frozen=True)
class OptionalMlBackend:
    module_name: str
    available: bool
    package_version: str | None
    role: str
    error: str = ""


@dataclass(frozen=True)
class DatasetSplit:
    id: Literal["train", "validation", "test"]
    donor_ids: tuple[str, ...]
    record_count: int


@dataclass(frozen=True)
class GenerativeDatasetManifest:
    id: str
    species: str
    cell_type: str
    modality: str
    data_artifact_sha256: str
    feature_schema_sha256: str
    splits: tuple[DatasetSplit, ...]
    source_ids: tuple[str, ...]
    measured_records_only: bool
    donor_level_split: bool
    batch_metadata_available: bool


@dataclass(frozen=True)
class GenerativeModelCard:
    id: str
    model_family: Literal["vae", "conditional_vae", "scvi", "scgen"]
    backend: str
    dataset_manifest_sha256: str
    model_artifact_sha256: str | None
    latent_dimension: int | None
    training_seed: int | None
    heldout_donor_evaluation: bool
    posterior_predictive_checks: bool
    status: Literal["design_only", "trained_unvalidated", "heldout_validated"]
    may_drive_cell_engine: bool
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class SyntheticCellCandidate:
    id: str
    model_card_sha256: str
    latent_seed: int
    conditions: dict[str, str]
    decoded_features: dict[str, float]
    origin: Literal["generated"] = "generated"
    validation_status: Literal["synthetic_candidate_unvalidated"] = "synthetic_candidate_unvalidated"
    may_drive_cell_engine: bool = False


@dataclass(frozen=True)
class GenerativeModelingBoundary:
    version: str
    status: str
    target_species: str
    target_cell_type: str
    allowed_input_modalities: tuple[str, ...]
    required_metadata: tuple[str, ...]
    prohibited_training_inputs: tuple[str, ...]
    split_policy: str
    candidate_model_families: tuple[str, ...]
    backends: tuple[OptionalMlBackend, ...]
    training_ready: bool
    inference_ready: bool
    automatic_state_coupling: bool
    blockers: tuple[str, ...]
    source_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


class GenerativeDonorManifestError(ValueError):
    """Raised when a donor-generative data delivery violates its contract."""


@dataclass(frozen=True)
class GenerativeDonorManifestAudit:
    version: str
    contract_id: str
    status: str
    delivery_path: str
    artifact_sha256: str
    contract_sha256: str
    dataset_id: str
    sample_count: int
    donor_count: int
    source_study_count: int
    assay_batch_count: int
    feature_count: int
    modality_count: int
    record_count_by_split: dict[str, int]
    donor_count_by_split: dict[str, int]
    explicit_missing_donor_covariate_count: int
    explicit_missing_feature_reference_count: int
    donor_disjoint_split: bool
    test_study_disjoint: bool
    generated_record_count: int
    structurally_training_data_ready: bool
    validated_generative_donor_model_count: int
    manual_primary_source_review_complete: bool
    automatic_training: bool
    automatic_engine_coupling: bool
    blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def _detect_backend(module_name: str, distribution: str, role: str) -> OptionalMlBackend:
    if util.find_spec(module_name) is None:
        return OptionalMlBackend(module_name, False, None, role, "module_not_installed")
    try:
        package_version = metadata.version(distribution)
    except metadata.PackageNotFoundError:
        package_version = None
    return OptionalMlBackend(module_name, True, package_version, role)


def build_generative_modeling_boundary() -> GenerativeModelingBoundary:
    donor_intake = generative_donor_manifest_intake_snapshot()
    structurally_ready = bool(
        donor_intake.get("structurally_training_data_ready", False)
    )
    boundary = GenerativeModelingBoundary(
        version="hepatocyte_generative_modeling_boundary_v2",
        status=(
            "donor_manifest_structurally_ready_training_still_disabled"
            if structurally_ready
            else "infrastructure_ready_training_data_absent"
        ),
        target_species="Homo sapiens",
        target_cell_type="adult primary human hepatocyte",
        allowed_input_modalities=(
            "raw_single_cell_rna_counts",
            "single_cell_protein_counts_with_assay_model",
            "matched_multimodal_single_cell_measurements",
            "source_backed_engine_observation_vectors",
        ),
        required_metadata=(
            "donor_id",
            "sample_id",
            "assay_batch_id",
            "cell_type_annotation",
            "health_or_disease_context",
            "nutrition_or_exposure_context",
            "measurement_modality",
            "primary_source_id",
        ),
        prohibited_training_inputs=(
            "legacy_relative_0_1_schematic_pools_as_measured_biology",
            "browser_only_visual_state",
            "generated_records_relabelled_as_measured",
            "records_without_donor_or_batch_identity",
            "train_test_splits_made_at_cell_level_across_the_same_donor",
        ),
        split_policy="donor-disjoint train/validation/test split before preprocessing or model fitting",
        candidate_model_families=(
            "scVI-like count-aware latent model for scRNA-seq",
            "conditional VAE only for explicitly conditioned measured modalities",
            "scGen-like perturbation model only with held-out donor/context evaluation",
        ),
        backends=(
            _detect_backend("torch", "torch", "tensor and autograd backend"),
            _detect_backend("scvi", "scvi-tools", "count-aware single-cell generative models"),
        ),
        training_ready=False,
        inference_ready=False,
        automatic_state_coupling=False,
        blockers=(
            *(
                ()
                if structurally_ready
                else ("no audited donor-resolved training dataset manifest is loaded",)
            ),
            "no frozen feature schema artifact is loaded",
            "no trained weight artifact and checksum are loaded",
            "no donor-held-out evaluation or posterior predictive check is available",
            "generated samples have no authority to initialize or modify the mechanistic cell engine",
        ),
        source_ids=tuple(GENERATIVE_SOURCES),
    )
    validate_generative_modeling_boundary(boundary)
    return boundary


def validate_dataset_manifest(manifest: GenerativeDatasetManifest) -> None:
    if manifest.species != "Homo sapiens" or "hepatocyte" not in manifest.cell_type.lower():
        raise ValueError("generative dataset must preserve human hepatocyte scope")
    _validate_sha256(manifest.data_artifact_sha256, "data artifact")
    _validate_sha256(manifest.feature_schema_sha256, "feature schema")
    if not manifest.measured_records_only:
        raise ValueError("training dataset cannot mix generated records with measured records")
    if not manifest.donor_level_split:
        raise ValueError("dataset split must be donor-level")
    split_by_id = {split.id: split for split in manifest.splits}
    if set(split_by_id) != {"train", "validation", "test"}:
        raise ValueError("train, validation and test splits are all required")
    seen: set[str] = set()
    for split in manifest.splits:
        if split.record_count <= 0 or not split.donor_ids:
            raise ValueError(f"split {split.id} must contain donors and records")
        overlap = seen.intersection(split.donor_ids)
        if overlap:
            raise ValueError(f"donor leakage across dataset splits: {sorted(overlap)!r}")
        seen.update(split.donor_ids)
    if not manifest.batch_metadata_available:
        raise ValueError("assay batch metadata is required")
    if not manifest.source_ids:
        raise ValueError("dataset manifest requires primary-source provenance")


def validate_model_card(card: GenerativeModelCard) -> None:
    _validate_sha256(card.dataset_manifest_sha256, "dataset manifest")
    if card.may_drive_cell_engine:
        raise ValueError("generative model output cannot directly drive the mechanistic engine")
    if not card.source_ids or not set(card.source_ids) <= set(GENERATIVE_SOURCES):
        raise ValueError("model card lacks registered method provenance")
    if card.status == "design_only":
        if card.model_artifact_sha256 is not None:
            raise ValueError("design-only model cannot claim a weight artifact")
        return
    if card.model_artifact_sha256 is None:
        raise ValueError("trained model requires a weight artifact checksum")
    _validate_sha256(card.model_artifact_sha256, "model artifact")
    if card.latent_dimension is None or card.latent_dimension <= 0 or card.training_seed is None:
        raise ValueError("trained model requires latent dimension and training seed")
    if card.status == "heldout_validated" and not (
        card.heldout_donor_evaluation and card.posterior_predictive_checks
    ):
        raise ValueError("heldout-validated model requires donor-held-out and posterior-predictive evaluation")


def validate_synthetic_candidate(candidate: SyntheticCellCandidate) -> None:
    _validate_sha256(candidate.model_card_sha256, "model card")
    if candidate.origin != "generated" or candidate.validation_status != "synthetic_candidate_unvalidated":
        raise ValueError("synthetic candidate identity cannot be promoted")
    if candidate.may_drive_cell_engine:
        raise ValueError("unvalidated synthetic candidate cannot drive cell state")
    if not candidate.decoded_features:
        raise ValueError("synthetic candidate must contain decoded features")


def validate_generative_modeling_boundary(boundary: GenerativeModelingBoundary) -> None:
    if boundary.target_species != "Homo sapiens":
        raise ValueError("generative boundary must preserve human target species")
    if boundary.training_ready or boundary.inference_ready or boundary.automatic_state_coupling:
        raise ValueError("generative execution cannot be enabled before data, weights and validation exist")
    if not boundary.required_metadata or not boundary.prohibited_training_inputs:
        raise ValueError("generative data governance contract is incomplete")
    if not boundary.blockers:
        raise ValueError("untrained generative boundary must report blockers")
    if not set(boundary.source_ids) <= set(GENERATIVE_SOURCES):
        raise ValueError("generative boundary contains unknown provenance")


def generative_modeling_snapshot() -> dict[str, object]:
    payload = build_generative_modeling_boundary().to_dict()
    payload["donor_manifest_intake"] = generative_donor_manifest_intake_snapshot()
    return payload


def sha256_text(value: str) -> str:
    """Stable helper for tests and future manifest tooling."""

    return sha256(value.encode("utf-8")).hexdigest()


def _validate_sha256(value: str, label: str) -> None:
    if len(value) != SHA256_LENGTH or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{label} checksum must be lowercase SHA-256")


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPOSITORY_ROOT.resolve()))
    except ValueError:
        return str(path)


def load_generative_donor_manifest_contract(
    path: Path = DONOR_MANIFEST_CONTRACT_PATH,
) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise GenerativeDonorManifestError("generative donor contract must be one object")
    if payload.get("schema_version") != DONOR_MANIFEST_CONTRACT_SCHEMA_VERSION:
        raise GenerativeDonorManifestError("unsupported generative donor contract schema")
    if payload.get("delivery_schema_version") != DONOR_MANIFEST_DELIVERY_SCHEMA_VERSION:
        raise GenerativeDonorManifestError("generative donor delivery schema changed")
    list_fields = (
        "allowed_split_roles",
        "allowed_modalities",
        "required_root_fields",
        "required_sample_fields",
        "required_donor_covariate_keys",
        "required_feature_fields",
        "allowed_missingness_semantics",
    )
    if any(
        not isinstance(payload.get(field), list)
        or not payload[field]
        or len(payload[field]) != len(set(payload[field]))
        for field in list_fields
    ):
        raise GenerativeDonorManifestError("generative donor field contract is malformed")
    split_policy = payload.get("split_policy")
    evaluation = payload.get("evaluation_contract")
    policy = payload.get("policy")
    if not all(isinstance(item, dict) for item in (split_policy, evaluation, policy)):
        raise GenerativeDonorManifestError("generative donor governance contract is malformed")
    if set(payload["allowed_split_roles"]) != {"train", "validation", "test"}:
        raise GenerativeDonorManifestError("generative donor split roles changed")
    required_true = {
        "split_before_preprocessing_required",
        "donor_disjoint_required",
        "test_study_disjoint_required",
        "batch_covariates_required",
        "explicit_missingness_required",
    }
    if any(split_policy.get(key) is not True for key in required_true):
        raise GenerativeDonorManifestError("generative donor split policy weakened")
    if split_policy.get("generated_records_in_training_allowed") is not False:
        raise GenerativeDonorManifestError("generated records escaped into training")
    evaluation_true = {
        "frozen_model_before_test_access_required",
        "donor_heldout_evaluation_required",
        "posterior_predictive_checks_required",
        "batch_effect_diagnostic_required",
        "within_donor_variance_preservation_required",
        "mechanistic_constraint_violation_report_required",
        "synthetic_to_measured_provenance_required",
    }
    if any(evaluation.get(key) is not True for key in evaluation_true):
        raise GenerativeDonorManifestError("generative donor evaluation contract weakened")
    if (
        evaluation.get("single_aggregate_accuracy_score_allowed") is not False
        or evaluation.get("automatic_engine_coupling") is not False
        or any(value is not False for value in policy.values())
    ):
        raise GenerativeDonorManifestError("generative donor policy escaped fail-closed state")
    return payload


def _require_exact_fields(
    payload: dict[str, object],
    required_fields: set[str],
    label: str,
) -> None:
    missing = required_fields - set(payload)
    extra = set(payload) - required_fields
    if missing or extra:
        raise GenerativeDonorManifestError(
            f"{label} fields must exactly match contract; missing={sorted(missing)!r}, "
            f"extra={sorted(extra)!r}"
        )


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GenerativeDonorManifestError(f"{label} must be non-empty text")
    return value.strip()


def _require_sha256(value: object, label: str) -> str:
    text_value = _require_text(value, label)
    if not _SHA256_RE.fullmatch(text_value):
        raise GenerativeDonorManifestError(f"{label} must be lowercase SHA-256")
    return text_value


def audit_generative_donor_manifest(
    path: Path = DEFAULT_DONOR_MANIFEST_PATH,
) -> GenerativeDonorManifestAudit:
    contract = load_generative_donor_manifest_contract()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise GenerativeDonorManifestError("generative donor delivery must be one object")
    required_root_fields = set(contract["required_root_fields"])
    _require_exact_fields(payload, required_root_fields, "generative donor root")
    if payload["schema_version"] != DONOR_MANIFEST_DELIVERY_SCHEMA_VERSION:
        raise GenerativeDonorManifestError("unsupported generative donor delivery schema")
    if payload["species"] != "Homo sapiens":
        raise GenerativeDonorManifestError("generative donor delivery must remain human")
    cell_type = _require_text(payload["cell_type"], "cell_type")
    if "primary human hepatocyte" not in cell_type.lower():
        raise GenerativeDonorManifestError("generative donor delivery must remain adult PHH")
    _require_sha256(payload["measurement_artifact_sha256"], "measurement artifact")
    _require_sha256(payload["feature_matrix_sha256"], "feature matrix")
    source_ids = payload["source_ids"]
    samples = payload["samples"]
    features = payload["features"]
    if (
        not isinstance(source_ids, list)
        or not source_ids
        or not all(isinstance(item, str) and item for item in source_ids)
        or len(source_ids) != len(set(source_ids))
    ):
        raise GenerativeDonorManifestError("source_ids must be unique non-empty identifiers")
    if not isinstance(samples, list) or not samples:
        raise GenerativeDonorManifestError("generative donor delivery requires samples")
    if not isinstance(features, list) or not features:
        raise GenerativeDonorManifestError("generative donor delivery requires features")
    if (
        not isinstance(payload["generated_record_count"], int)
        or payload["generated_record_count"] != 0
        or payload["automatic_training"] is not False
        or payload["automatic_engine_coupling"] is not False
    ):
        raise GenerativeDonorManifestError("generative delivery escaped measured-only fail-closed policy")
    if not isinstance(payload["manual_primary_source_review_complete"], bool):
        raise GenerativeDonorManifestError("manual review status must be boolean")

    allowed_modalities = set(contract["allowed_modalities"])
    allowed_missingness = set(contract["allowed_missingness_semantics"])
    feature_fields = set(contract["required_feature_fields"])
    sample_fields = set(contract["required_sample_fields"])
    feature_ids: set[str] = set()
    feature_modalities: dict[str, str] = {}
    for index, feature in enumerate(features):
        if not isinstance(feature, dict):
            raise GenerativeDonorManifestError(f"feature {index} must be one object")
        _require_exact_fields(feature, feature_fields, f"feature {index}")
        feature_id = _require_text(feature["feature_id"], f"feature {index} id")
        if feature_id in feature_ids:
            raise GenerativeDonorManifestError(f"duplicate feature_id {feature_id!r}")
        modality = _require_text(feature["modality"], f"feature {index} modality")
        if modality not in allowed_modalities:
            raise GenerativeDonorManifestError(f"unsupported feature modality {modality!r}")
        if feature["missingness_semantics"] not in allowed_missingness:
            raise GenerativeDonorManifestError(
                f"feature {feature_id!r} lacks explicit missingness semantics"
            )
        if feature["source_id"] not in source_ids:
            raise GenerativeDonorManifestError(
                f"feature {feature_id!r} references an unknown source"
            )
        if feature["may_initialize_engine"] is not False:
            raise GenerativeDonorManifestError(
                f"feature {feature_id!r} cannot initialize the mechanistic engine"
            )
        for field in (
            "biological_entity",
            "value_semantics",
            "original_unit",
            "assay",
        ):
            _require_text(feature[field], f"feature {feature_id} {field}")
        feature_ids.add(feature_id)
        feature_modalities[feature_id] = modality

    required_covariates = set(contract["required_donor_covariate_keys"])
    allowed_splits = set(contract["allowed_split_roles"])
    sample_ids: set[str] = set()
    donor_splits: dict[str, set[str]] = {}
    study_splits: dict[str, set[str]] = {}
    split_record_counts = {split: 0 for split in allowed_splits}
    split_donors = {split: set() for split in allowed_splits}
    batches: set[str] = set()
    modalities: set[str] = set()
    explicit_missing_covariates = 0
    explicit_missing_features = 0
    for index, sample in enumerate(samples):
        if not isinstance(sample, dict):
            raise GenerativeDonorManifestError(f"sample {index} must be one object")
        _require_exact_fields(sample, sample_fields, f"sample {index}")
        sample_id = _require_text(sample["sample_id"], f"sample {index} id")
        if sample_id in sample_ids:
            raise GenerativeDonorManifestError(f"duplicate sample_id {sample_id!r}")
        donor_id = _require_text(sample["donor_id"], f"sample {sample_id} donor")
        split = _require_text(sample["split_role"], f"sample {sample_id} split")
        if split not in allowed_splits:
            raise GenerativeDonorManifestError(f"unsupported split_role {split!r}")
        study = _require_text(
            sample["source_study_id"], f"sample {sample_id} source study"
        )
        if study not in source_ids:
            raise GenerativeDonorManifestError(
                f"sample {sample_id!r} references an unknown source study"
            )
        modality = _require_text(sample["modality"], f"sample {sample_id} modality")
        if modality not in allowed_modalities:
            raise GenerativeDonorManifestError(f"unsupported sample modality {modality!r}")
        if not any(value == modality for value in feature_modalities.values()):
            raise GenerativeDonorManifestError(
                f"sample modality {modality!r} has no declared features"
            )
        biological_system = _require_text(
            sample["biological_system"], f"sample {sample_id} biological system"
        )
        if "primary_human_hepatocyte" not in biological_system.lower():
            raise GenerativeDonorManifestError(
                f"sample {sample_id!r} is outside primary human hepatocytes"
            )
        record_count = sample["measured_record_count"]
        if not isinstance(record_count, int) or record_count <= 0:
            raise GenerativeDonorManifestError(
                f"sample {sample_id!r} measured_record_count must be positive"
            )
        covariates = sample["donor_covariates"]
        missing_covariates = sample["missing_donor_covariates"]
        technical_covariates = sample["technical_covariates"]
        missing_feature_ids = sample["missing_feature_ids"]
        if (
            not isinstance(covariates, dict)
            or not isinstance(missing_covariates, list)
            or not all(isinstance(item, str) for item in missing_covariates)
            or not isinstance(technical_covariates, dict)
            or not technical_covariates
            or not isinstance(missing_feature_ids, list)
            or not all(isinstance(item, str) for item in missing_feature_ids)
        ):
            raise GenerativeDonorManifestError(
                f"sample {sample_id!r} covariate/missingness metadata is malformed"
            )
        observed_covariates = set(covariates)
        missing_covariate_set = set(missing_covariates)
        if (
            observed_covariates & missing_covariate_set
            or observed_covariates | missing_covariate_set != required_covariates
        ):
            raise GenerativeDonorManifestError(
                f"sample {sample_id!r} must explicitly account for every donor covariate"
            )
        if not all(value is not None for value in covariates.values()):
            raise GenerativeDonorManifestError(
                f"sample {sample_id!r} observed covariates cannot contain null"
            )
        missing_feature_set = set(missing_feature_ids)
        if len(missing_feature_set) != len(missing_feature_ids):
            raise GenerativeDonorManifestError(
                f"sample {sample_id!r} repeats missing feature ids"
            )
        unknown_missing = missing_feature_set - feature_ids
        if unknown_missing:
            raise GenerativeDonorManifestError(
                f"sample {sample_id!r} references unknown missing features"
            )
        if any(feature_modalities[item] != modality for item in missing_feature_set):
            raise GenerativeDonorManifestError(
                f"sample {sample_id!r} missing feature belongs to another modality"
            )
        for field in (
            "source_locator",
            "assay_batch_id",
            "culture_format",
            "health_context",
            "nutrition_or_exposure_context",
        ):
            _require_text(sample[field], f"sample {sample_id} {field}")
        sample_ids.add(sample_id)
        donor_splits.setdefault(donor_id, set()).add(split)
        study_splits.setdefault(study, set()).add(split)
        split_record_counts[split] += record_count
        split_donors[split].add(donor_id)
        batches.add(str(sample["assay_batch_id"]))
        modalities.add(modality)
        explicit_missing_covariates += len(missing_covariate_set)
        explicit_missing_features += len(missing_feature_set)

    leaking_donors = [
        donor for donor, splits in donor_splits.items() if len(splits) > 1
    ]
    if leaking_donors:
        raise GenerativeDonorManifestError(
            f"donor leakage across generative splits: {sorted(leaking_donors)!r}"
        )
    if any(not split_donors[split] for split in allowed_splits):
        raise GenerativeDonorManifestError(
            "train, validation and test each require at least one donor"
        )
    leaking_test_studies = [
        study
        for study, splits in study_splits.items()
        if "test" in splits and len(splits) > 1
    ]
    if leaking_test_studies:
        raise GenerativeDonorManifestError(
            f"test study leakage across development splits: {sorted(leaking_test_studies)!r}"
        )
    manual_review = bool(payload["manual_primary_source_review_complete"])
    blockers = [
        "frozen preprocessing and feature-schema artifacts are not independently attested",
        "no trained weight artifact exists",
        "no donor-heldout posterior-predictive and mechanistic-constraint evaluation exists",
    ]
    if not manual_review:
        blockers.insert(0, "manual primary-source review is incomplete")
    return GenerativeDonorManifestAudit(
        version=DONOR_MANIFEST_INTAKE_VERSION,
        contract_id=str(contract["contract_id"]),
        status="structurally_audited_measured_donor_manifest_not_training_authority",
        delivery_path=_display_path(path),
        artifact_sha256=_file_sha256(path),
        contract_sha256=_file_sha256(DONOR_MANIFEST_CONTRACT_PATH),
        dataset_id=_require_text(payload["dataset_id"], "dataset_id"),
        sample_count=len(samples),
        donor_count=len(donor_splits),
        source_study_count=len(study_splits),
        assay_batch_count=len(batches),
        feature_count=len(features),
        modality_count=len(modalities),
        record_count_by_split=dict(sorted(split_record_counts.items())),
        donor_count_by_split={
            split: len(donors) for split, donors in sorted(split_donors.items())
        },
        explicit_missing_donor_covariate_count=explicit_missing_covariates,
        explicit_missing_feature_reference_count=explicit_missing_features,
        donor_disjoint_split=True,
        test_study_disjoint=True,
        generated_record_count=0,
        structurally_training_data_ready=True,
        validated_generative_donor_model_count=0,
        manual_primary_source_review_complete=manual_review,
        automatic_training=False,
        automatic_engine_coupling=False,
        blockers=tuple(blockers),
    )


def generative_donor_manifest_intake_snapshot(
    path: Path = DEFAULT_DONOR_MANIFEST_PATH,
) -> dict[str, object]:
    contract = load_generative_donor_manifest_contract()
    if not path.exists():
        return {
            "version": DONOR_MANIFEST_INTAKE_VERSION,
            "contract_id": contract["contract_id"],
            "status": "awaiting_donor_linked_multimodal_phh_manifest",
            "delivery_path": _display_path(path),
            "contract_sha256": _file_sha256(DONOR_MANIFEST_CONTRACT_PATH),
            "sample_count": 0,
            "donor_count": 0,
            "feature_count": 0,
            "structurally_training_data_ready": False,
            "validated_generative_donor_model_count": 0,
            "automatic_training": False,
            "automatic_engine_coupling": False,
            "blockers": (
                "donor-linked measured data manifest is absent",
                "donor-disjoint train, validation and test cohorts are absent",
                "batch, technical-covariate and explicit-missingness metadata are absent",
                "frozen model and donor-heldout evaluation are absent",
            ),
        }
    return audit_generative_donor_manifest(path).to_dict()
