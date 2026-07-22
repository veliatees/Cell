"""Guard the fail-closed quantitative concentration-field exporter."""

from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

from cell_engine.stochastic.hepatocyte_rdme import (
    MEMBRANE_BASOLATERAL,
    build_hepatocyte_lattice,
)


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "export_concentration_field.py"
PUBLIC_ARTIFACT = ROOT / "public" / "cell_concentration_field.json"


def _load_exporter():
    spec = importlib.util.spec_from_file_location("export_concentration_field", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _complete_contract() -> dict:
    return {
        "schema_version": "cell.concentration-field-evidence.v1",
        "context": {
            "organism": "Homo sapiens",
            "cell_type": "primary human hepatocyte",
            "health_state": "healthy",
            "compartment": "cytosol",
            "donor_count": 3,
            "assay_id": "contract-test-assay",
            "temperature_k": 310.0,
        },
        "sources": [
            {
                "id": "parameter-source",
                "source_type": "primary_measurement",
                "identifier": "https://example.test/parameter-source",
                "locator": "contract test fixture",
            },
            {
                "id": "model-source",
                "source_type": "primary_model_paper",
                "identifier": "https://example.test/model-source",
                "locator": "contract test fixture",
            },
            {
                "id": "validation-source",
                "source_type": "author_dataset",
                "identifier": "https://example.test/validation-source",
                "locator": "contract test fixture",
            },
        ],
        "species": [
            {
                "id": "contract-test-solute",
                "key": "test",
                "label": "Contract test solute",
                "unit": "mM",
                "model": "basolateral_dirichlet_first_order_sink",
                "model_evidence": {
                    "source_id": "model-source",
                    "locator": "contract test equation",
                },
                "parameters": {
                    "diffusion_um2_per_s": {
                        "value": 1.0,
                        "unit": "um^2/s",
                        "source_id": "parameter-source",
                        "locator": "contract test value",
                    },
                    "first_order_consumption_per_s": {
                        "value": 0.1,
                        "unit": "1/s",
                        "source_id": "parameter-source",
                        "locator": "contract test value",
                    },
                    "boundary_concentration_mM": {
                        "value": 1.0,
                        "unit": "mM",
                        "source_id": "parameter-source",
                        "locator": "contract test value",
                    },
                },
            }
        ],
        "validation": {
            "source_id": "validation-source",
            "dataset_id": "contract-test-held-out",
            "held_out": True,
            "same_context": True,
            "acceptance_criterion": "contract test only",
        },
        "independent_review": {
            "complete": True,
            "quantitative_rendering_approved": True,
            "review_record_id": "contract-test-review",
            "reviewer_role": "contract test reviewer",
            "scope": "schema mechanics only; no biological claim",
        },
    }


def test_unit_agnostic_relaxation_produces_a_bounded_gradient() -> None:
    exporter = _load_exporter()
    lattice = build_hepatocyte_lattice(n=10)
    fixed = {
        index: 1.0
        for index in range(lattice.size)
        if lattice.compartment_of(index) == MEMBRANE_BASOLATERAL
    }
    field = exporter.relax_steady_state(
        lattice,
        diffusion=1.0,
        consumption=0.1,
        fixed=fixed,
        produce={},
        iterations=1000,
    )

    assert field
    assert min(field.values()) >= 0
    assert max(field.values()) <= 1.0 + 1e-12
    assert max(field[index] for index in fixed) == 1.0


def test_authorized_contract_can_build_a_traceable_candidate() -> None:
    exporter = _load_exporter()
    payload = exporter.build_payload(_complete_contract(), n=8, iterations=500)

    assert payload["schema_version"] == "cell.quantitative-concentration-field.v1"
    assert payload["quantitative_rendering_allowed"] is True
    assert len(payload["evidence_sha256"]) == 64
    assert set(payload["species"]) == {"test"}
    assert payload["voxels"]


def test_missing_independent_review_fails_closed() -> None:
    exporter = _load_exporter()
    contract = _complete_contract()
    contract["independent_review"]["complete"] = False

    with pytest.raises(ValueError, match="independent scientific review"):
        exporter.validate_evidence_package(contract)


def test_validation_source_cannot_reuse_calibration_source() -> None:
    exporter = _load_exporter()
    contract = _complete_contract()
    contract["validation"]["source_id"] = "parameter-source"

    with pytest.raises(ValueError, match="independent of calibration"):
        exporter.validate_evidence_package(contract)


def test_wrong_cell_context_fails_closed() -> None:
    exporter = _load_exporter()
    contract = deepcopy(_complete_contract())
    contract["context"]["cell_type"] = "immortalized liver cell line"

    with pytest.raises(ValueError, match="primary human hepatocyte"):
        exporter.validate_evidence_package(contract)


def test_no_unreviewed_concentration_artifact_is_publicly_served() -> None:
    assert not PUBLIC_ARTIFACT.exists()
    source = SCRIPT.read_text(encoding="utf-8")
    for retired_name in (
        "D_GLUCOSE",
        "D_ATP",
        "K_GLUCOSE",
        "K_ATP",
        "GLUCOSE_BLOOD_MM",
        "ATP_MITO_MM",
    ):
        assert retired_name not in source
