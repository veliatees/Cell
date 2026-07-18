from dataclasses import replace

import pytest

from cell_engine.io.brian2 import BRIAN2_PINNED_VERSION, Brian2Adapter
from cell_engine.ml.generative import (
    DatasetSplit,
    GenerativeDatasetManifest,
    GenerativeModelCard,
    SyntheticCellCandidate,
    build_generative_modeling_boundary,
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
