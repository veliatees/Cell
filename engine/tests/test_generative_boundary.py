import json
from dataclasses import replace
from pathlib import Path

import pytest

from cell_engine.io.brian2 import BRIAN2_PINNED_VERSION, Brian2Adapter
from cell_engine.ml.generative import (
    DatasetSplit,
    GenerativeDonorManifestError,
    GenerativeDatasetManifest,
    GenerativeModelCard,
    SyntheticCellCandidate,
    audit_generative_donor_manifest,
    build_generative_modeling_boundary,
    generative_donor_manifest_intake_snapshot,
    sha256_text,
    validate_dataset_manifest,
    validate_model_card,
    validate_synthetic_candidate,
)


def _manifest() -> GenerativeDatasetManifest:
    return GenerativeDatasetManifest(
        id="measured_phh_scRNA_v1",
        species="Homo sapiens",
        cell_type="adult primary human hepatocyte",
        modality="raw_single_cell_rna_counts",
        data_artifact_sha256=sha256_text("measured-data-artifact"),
        feature_schema_sha256=sha256_text("feature-schema"),
        splits=(
            DatasetSplit("train", ("donor_A", "donor_B"), 200),
            DatasetSplit("validation", ("donor_C",), 40),
            DatasetSplit("test", ("donor_D",), 50),
        ),
        source_ids=("primary_dataset_doi",),
        measured_records_only=True,
        donor_level_split=True,
        batch_metadata_available=True,
    )


def test_generative_boundary_is_ready_for_infrastructure_not_training() -> None:
    boundary = build_generative_modeling_boundary()
    assert boundary.status == "infrastructure_ready_training_data_absent"
    assert not boundary.training_ready
    assert not boundary.inference_ready
    assert not boundary.automatic_state_coupling
    assert "donor-disjoint" in boundary.split_policy
    assert len(boundary.backends) == 2
    assert any("scVI" in family for family in boundary.candidate_model_families)


def _donor_manifest_payload() -> dict[str, object]:
    feature = {
        "feature_id": "software_ALB",
        "modality": "raw_single_cell_rna_counts",
        "biological_entity": "software gene feature",
        "value_semantics": "raw integer count",
        "original_unit": "count",
        "assay": "software assay",
        "missingness_semantics": "observed_value_only_no_imputation",
        "source_id": "software-study-train",
        "may_initialize_engine": False,
    }
    samples = []
    for split, suffix in (
        ("train", "train"),
        ("validation", "validation"),
        ("test", "test"),
    ):
        study = f"software-study-{suffix}"
        samples.append(
            {
                "sample_id": f"software-sample-{suffix}",
                "donor_id": f"software-donor-{suffix}",
                "split_role": split,
                "source_study_id": study,
                "source_locator": "software fixture",
                "assay_batch_id": f"software-batch-{suffix}",
                "modality": "raw_single_cell_rna_counts",
                "biological_system": "primary_human_hepatocyte_software_fixture",
                "culture_format": "software culture",
                "health_context": "software healthy context",
                "nutrition_or_exposure_context": "software context",
                "measured_record_count": 10,
                "donor_covariates": {"sex": "software reported"},
                "missing_donor_covariates": [
                    "age",
                    "genotype",
                    "zonation",
                    "nutrition_state",
                    "disease_history",
                ],
                "technical_covariates": {"software_depth": 10},
                "missing_feature_ids": [],
            }
        )
    return {
        "schema_version": "cell.phh-generative-donor-manifest.v1",
        "dataset_id": "software-donor-manifest",
        "species": "Homo sapiens",
        "cell_type": "adult primary human hepatocyte",
        "measurement_artifact_sha256": sha256_text("software-measurements"),
        "feature_matrix_sha256": sha256_text("software-feature-matrix"),
        "source_ids": [
            "software-study-train",
            "software-study-validation",
            "software-study-test",
        ],
        "samples": samples,
        "features": [feature],
        "manual_primary_source_review_complete": False,
        "generated_record_count": 0,
        "automatic_training": False,
        "automatic_engine_coupling": False,
    }


def _write_donor_manifest(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_absent_donor_manifest_keeps_training_and_coupling_disabled(
    tmp_path: Path,
) -> None:
    snapshot = generative_donor_manifest_intake_snapshot(tmp_path / "missing.json")
    assert snapshot["structurally_training_data_ready"] is False
    assert snapshot["validated_generative_donor_model_count"] == 0
    assert snapshot["automatic_training"] is False
    assert snapshot["automatic_engine_coupling"] is False


def test_structural_donor_manifest_tracks_missingness_without_training_authority(
    tmp_path: Path,
) -> None:
    path = tmp_path / "manifest.json"
    _write_donor_manifest(path, _donor_manifest_payload())
    audit = audit_generative_donor_manifest(path)
    assert audit.donor_count == 3
    assert audit.donor_disjoint_split is True
    assert audit.test_study_disjoint is True
    assert audit.explicit_missing_donor_covariate_count == 15
    assert audit.structurally_training_data_ready is True
    assert audit.automatic_training is False
    assert audit.automatic_engine_coupling is False


def test_donor_manifest_rejects_leakage_and_silent_missingness(
    tmp_path: Path,
) -> None:
    path = tmp_path / "manifest.json"
    payload = _donor_manifest_payload()
    payload["samples"][2]["donor_id"] = payload["samples"][0]["donor_id"]
    _write_donor_manifest(path, payload)
    with pytest.raises(GenerativeDonorManifestError, match="donor leakage"):
        audit_generative_donor_manifest(path)

    payload = _donor_manifest_payload()
    payload["samples"][0]["missing_donor_covariates"].remove("age")
    _write_donor_manifest(path, payload)
    with pytest.raises(GenerativeDonorManifestError, match="account for every"):
        audit_generative_donor_manifest(path)


def test_donor_manifest_features_cannot_initialize_engine(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    payload = _donor_manifest_payload()
    payload["features"][0]["may_initialize_engine"] = True
    _write_donor_manifest(path, payload)
    with pytest.raises(GenerativeDonorManifestError, match="cannot initialize"):
        audit_generative_donor_manifest(path)


def test_dataset_manifest_accepts_donor_disjoint_measured_splits() -> None:
    validate_dataset_manifest(_manifest())


def test_dataset_manifest_rejects_donor_leakage() -> None:
    manifest = _manifest()
    leaking = replace(
        manifest,
        splits=(
            DatasetSplit("train", ("donor_A",), 100),
            DatasetSplit("validation", ("donor_B",), 30),
            DatasetSplit("test", ("donor_A",), 20),
        ),
    )
    with pytest.raises(ValueError, match="donor leakage"):
        validate_dataset_manifest(leaking)


def test_model_card_and_synthetic_candidate_cannot_drive_engine() -> None:
    card = GenerativeModelCard(
        id="design_only_scvi",
        model_family="scvi",
        backend="scvi-tools",
        dataset_manifest_sha256=sha256_text("dataset-manifest"),
        model_artifact_sha256=None,
        latent_dimension=None,
        training_seed=None,
        heldout_donor_evaluation=False,
        posterior_predictive_checks=False,
        status="design_only",
        may_drive_cell_engine=False,
        source_ids=("scvi_single_cell_generative_model",),
    )
    validate_model_card(card)

    candidate = SyntheticCellCandidate(
        id="candidate_0001",
        model_card_sha256=sha256_text("model-card"),
        latent_seed=7,
        conditions={"zone": "midlobular"},
        decoded_features={"ALB_count": 1.0},
    )
    validate_synthetic_candidate(candidate)
    with pytest.raises(ValueError, match="cannot drive cell state"):
        validate_synthetic_candidate(replace(candidate, may_drive_cell_engine=True))


def test_brian2_gate_requires_backend_pin_and_calibrated_model() -> None:
    adapter = Brian2Adapter.detect()
    gate = adapter.assess_communication_model()
    assert gate.package_version == adapter.package_version
    assert not gate.model_attached
    assert not gate.execution_ready
    assert any("no calibrated intercellular" in blocker for blocker in gate.blockers)
    if adapter.available:
        assert gate.version_matches_project_pin == (adapter.package_version == BRIAN2_PINNED_VERSION)
