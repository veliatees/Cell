"""Provenance and safety boundary for future hepatocyte generative models."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from importlib import metadata, util
from typing import Literal

from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain


DATE_VERIFIED = "2026-07-14"
SHA256_LENGTH = 64

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


def _detect_backend(module_name: str, distribution: str, role: str) -> OptionalMlBackend:
    if util.find_spec(module_name) is None:
        return OptionalMlBackend(module_name, False, None, role, "module_not_installed")
    try:
        package_version = metadata.version(distribution)
    except metadata.PackageNotFoundError:
        package_version = None
    return OptionalMlBackend(module_name, True, package_version, role)


def build_generative_modeling_boundary() -> GenerativeModelingBoundary:
    boundary = GenerativeModelingBoundary(
        version="hepatocyte_generative_modeling_boundary_v1",
        status="infrastructure_ready_training_data_absent",
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
            "no audited donor-resolved training dataset manifest is loaded",
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
    return build_generative_modeling_boundary().to_dict()


def sha256_text(value: str) -> str:
    """Stable helper for tests and future manifest tooling."""

    return sha256(value.encode("utf-8")).hexdigest()


def _validate_sha256(value: str, label: str) -> None:
    if len(value) != SHA256_LENGTH or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{label} checksum must be lowercase SHA-256")
