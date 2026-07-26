from __future__ import annotations

import csv
from pathlib import Path

import pytest

from cell_engine.quantitative.reaction_evidence_intake import (
    ReactionEvidenceIntakeError,
    assess_reaction_evidence,
    load_reaction_evidence_contract,
    load_reaction_evidence_dataset,
    reaction_evidence_intake_snapshot,
)
from cell_engine.stochastic.integrated_cell import build_integrated_hepatocyte_network
from cell_engine.stochastic.signaling import HormoneState
from cell_engine.validation.reaction_evidence_atlas import (
    REACTION_EVIDENCE_SLOT_SPECS,
)


ACTIVE_REACTION_ID = build_integrated_hepatocyte_network(
    HormoneState()
).reactions[0].id
SLOT_UNITS = {
    slot_id: unit for slot_id, _quantity, unit, _context in REACTION_EVIDENCE_SLOT_SPECS
}


# Software-only records exercise intake behavior and are not measurements.
def _software_row(slot_id: str = "biochemical_identity", **updates: str) -> dict[str, str]:
    value_kind = {
        "biochemical_identity": "identity",
        "biological_compartment": "location",
        "symbolic_rate_law": "equation",
        "ki_or_allostery": "regulatory_model",
        "heldout_validation": "validation_result",
    }.get(slot_id, "numeric")
    reported_value = {
        "biochemical_identity": "software-identity",
        "biological_compartment": "software-cytosol",
        "symbolic_rate_law": "v = software_rate_law",
        "ki_or_allostery": "software-regulation",
        "heldout_validation": "software-validation-result",
        "assay_temperature": "37",
        "assay_ph": "7.4",
    }.get(slot_id, "1")
    heldout = slot_id == "heldout_validation"
    row = {
        "record_id": f"software-{slot_id}",
        "reaction_id": ACTIVE_REACTION_ID,
        "slot_id": slot_id,
        "parameter_or_entity_id": f"software-{slot_id}-entity",
        "split_role": "independent_heldout" if heldout else "calibration",
        "donor_id": "software-heldout-donor" if heldout else "software-dev-donor",
        "source_study_id": "software-heldout-study" if heldout else "software-dev-study",
        "source_locator": f"software-table-{slot_id}",
        "source_type": "primary_experiment",
        "species": "Homo sapiens",
        "biological_system": "primary_human_hepatocyte_software_fixture",
        "culture_format": "software-culture",
        "health_state": "software-healthy",
        "biological_replicate_id": "software-replicate",
        "assay": "software-assay",
        "biological_compartment": "software-cytosol",
        "membrane_side": "not_applicable",
        "enzyme_gene_symbol": "SOFTWARE",
        "protein_isoform": "software-isoform",
        "reaction_direction": "forward",
        "substrate_product_effector_context": "software-context",
        "cofactor_context": "software-cofactor-context",
        "active_state_context": "software-active-state",
        "value_kind": value_kind,
        "reported_value": reported_value,
        "reported_unit": SLOT_UNITS[slot_id],
        "canonical_unit_target": SLOT_UNITS[slot_id],
        "reported_statistic": "software-raw",
        "sample_size": "1",
        "manual_primary_source_review_status": "verified",
        "context_role": (
            "independent_healthy_phh_validation"
            if heldout
            else "direct_healthy_phh"
        ),
        "notes": "software-only",
        "assay_temperature_c": "37" if slot_id in {"km", "kcat", "ki_or_allostery", "vmax"} else "null",
        "assay_ph": "7.4" if slot_id in {"km", "kcat", "ki_or_allostery", "vmax"} else "null",
        "uncertainty_lower": "null",
        "uncertainty_upper": "null",
        "uncertainty_unit": "null",
        "uncertainty_type": "null",
        "equation_machine_readable": "v=software_rate_law" if slot_id == "symbolic_rate_law" else "null",
        "raw_to_canonical_conversion_reference": "not_required_same_unit",
        "validation_model_artifact_sha256": "a" * 64 if heldout else "null",
        "validation_prediction_id": "software-prediction" if heldout else "null",
        "validation_observation_id": "software-observation" if heldout else "null",
        "frozen_before_heldout_access": "true" if heldout else "null",
        "censoring_or_missingness": "none",
    }
    row.update(updates)
    return row


def _complete_rows() -> list[dict[str, str]]:
    return [_software_row(slot_id) for slot_id in SLOT_UNITS]


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    contract = load_reaction_evidence_contract()
    fields = [
        *(item["id"] for item in contract["required_columns"]),
        *(item["id"] for item in contract["conditional_columns"]),
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_absent_reaction_delivery_exposes_all_432_missing_slots(
    tmp_path: Path,
) -> None:
    snapshot = reaction_evidence_intake_snapshot(tmp_path / "missing.csv")
    assert snapshot["expected_header_count"] == 45
    assert snapshot["active_reaction_count"] == 36
    assert snapshot["required_slot_count"] == 432
    assert snapshot["covered_slot_count"] == 0
    assert snapshot["quantitative_execution_allowed_count"] == 0


def test_all_twelve_software_slots_are_structural_but_never_authority(
    tmp_path: Path,
) -> None:
    path = tmp_path / "reaction-evidence.csv"
    _write_rows(path, _complete_rows())
    dataset = load_reaction_evidence_dataset(path)
    assessment = assess_reaction_evidence(ACTIVE_REACTION_ID, dataset.records)
    assert assessment.structurally_complete is True
    assert len(assessment.structurally_ready_slot_ids) == 12
    assert assessment.atlas_mutation_allowed is False
    assert assessment.quantitative_execution_allowed is False
    snapshot = reaction_evidence_intake_snapshot(path)
    assert snapshot["covered_slot_count"] == 12
    assert snapshot["structurally_complete_reaction_count"] == 1
    assert snapshot["quantitative_execution_allowed_count"] == 0


def test_unknown_reactions_units_and_nonhuman_records_are_rejected(
    tmp_path: Path,
) -> None:
    path = tmp_path / "invalid.csv"
    _write_rows(path, [_software_row(reaction_id="not-an-active-reaction")])
    with pytest.raises(ReactionEvidenceIntakeError, match="active network"):
        load_reaction_evidence_dataset(path)

    _write_rows(path, [_software_row(canonical_unit_target="wrong-unit")])
    with pytest.raises(ReactionEvidenceIntakeError, match="canonical unit"):
        load_reaction_evidence_dataset(path)

    _write_rows(path, [_software_row(species="Mus musculus")])
    with pytest.raises(ReactionEvidenceIntakeError, match="non-human"):
        load_reaction_evidence_dataset(path)


def test_heldout_rows_require_frozen_independent_phh_artifacts(
    tmp_path: Path,
) -> None:
    path = tmp_path / "heldout.csv"
    _write_rows(
        path,
        [_software_row("heldout_validation", frozen_before_heldout_access="false")],
    )
    with pytest.raises(ReactionEvidenceIntakeError, match="frozen independent"):
        load_reaction_evidence_dataset(path)

    rows = _complete_rows()
    rows[-1]["source_study_id"] = "software-dev-study"
    rows[-1]["donor_id"] = "software-dev-donor"
    _write_rows(path, rows)
    with pytest.raises(ReactionEvidenceIntakeError, match="donor crosses split"):
        load_reaction_evidence_dataset(path)
