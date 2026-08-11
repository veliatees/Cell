from __future__ import annotations

import csv
from pathlib import Path

import pytest

from cell_engine.quantitative.completion_evidence import (
    CAPABILITY_COLUMNS,
    CLONAL_COLUMNS,
    P53_COLUMNS,
    CompletionEvidenceError,
    completion_evidence_bundle_intake_snapshot,
    load_completion_evidence_contract,
    validate_completion_evidence_bundle_intake_snapshot,
)
from cell_engine.validation.capability_atlas import HEPATOCYTE_CAPABILITIES


def _write(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _common(record_id: str) -> dict[str, str]:
    return {
        "record_id": record_id,
        "donor_id": "donor-001",
        "split_role": "calibration",
        "source_study_id": "study-001",
        "source_locator": "raw/table.csv",
        "species": "Homo sapiens",
        "biological_system": "plated_primary_human_hepatocyte",
        "biological_replicate_id": "bio-001",
    }


def _p53_rows() -> list[dict[str, str]]:
    observations = (
        ("TP53", "total_protein", "damage", "0"),
        ("MDM2", "total_protein", "arrest_or_senescence", "1"),
        ("phospho_TP53", "phosphoprotein", "apoptosis_or_survival", "2"),
        ("recovery_readout", "fate_or_recovery_readout", "recovery", "3"),
    )
    rows: list[dict[str, str]] = []
    for index, (analyte, level, endpoint, time_h) in enumerate(observations):
        row = {
            **_common(f"p53-{index}"),
            "culture_format": "collagen_sandwich",
            "protocol_id": "cisplatin-protocol-1",
            "damage_agent": "cisplatin",
            "damage_dose_value": "1.0",
            "damage_dose_unit": "umol/L",
            "exposure_start_h": "0",
            "washout_time_h": "2",
            "time_h": time_h,
            "analyte_id": analyte,
            "analyte_level": level,
            "compartment": "whole_cell",
            "endpoint_class": endpoint,
            "assay": "quantitative_assay",
            "raw_value": str(index + 1),
            "raw_unit": "arbitrary_source_unit",
            "normalization_denominator": "per_viable_cell",
            "uncertainty_type": "null",
            "uncertainty_value": "null",
            "sample_size": "1",
            "recovery_followup_h": "24",
            "independent_review_id": "null",
            "limitations": "software-test fixture only",
        }
        rows.append(row)
    return rows


def _clonal_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index, endpoint in enumerate(
        ("proliferation_or_clone_size", "arrest_senescence_death_or_clearance")
    ):
        row = {
            **_common(f"clone-{index}"),
            "culture_or_tissue_context": "adult_liver_section",
            "clone_id": "clone-001",
            "lineage_marker": "mtDNA_variant_1",
            "genotype": "reported_genotype",
            "ploidy": "2N",
            "injury_context": "none_reported",
            "nutrient_context": "physiological_unspecified",
            "zonation_context": "periportal",
            "niche_context": "portal_central_coordinates_recorded",
            "spatial_reference_frame": "registered_tissue_um",
            "position_x_um": str(index),
            "position_y_um": "0",
            "position_z_um": "0",
            "time_h": str(index * 24),
            "endpoint": endpoint,
            "raw_value": str(index + 1),
            "raw_unit": "cells",
            "measurement_operator": "direct_clone_count",
            "uncertainty_type": "null",
            "uncertainty_value": "null",
            "independent_review_id": "null",
            "limitations": "software-test fixture only",
        }
        rows.append(row)
    return rows


def _capability_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index, feature in enumerate(HEPATOCYTE_CAPABILITIES):
        for slot in feature.parameter_slots:
            row = {
                **_common(f"slot-{index}-{slot.id}"),
                "capability_id": feature.id,
                "parameter_slot_id": slot.id,
                "doi": "10.0000/software-test",
                "culture_format": "collagen_sandwich",
                "compartment": feature.compartments[0],
                "assay": "source_specific_assay",
                "quantity": slot.quantity,
                "raw_value": "1.0",
                "raw_unit": slot.unit,
                "normalization_denominator": "source_defined",
                "measurement_time": "baseline",
                "perturbation_context": "none",
                "uncertainty_type": "null",
                "uncertainty_value": "null",
                "independent_validation_id": "null",
                "limitations": "software-test fixture only",
            }
            rows.append(row)
    return rows


def _write_bundle(path: Path) -> None:
    _write(path / "phh_p53_ddr_trajectories.csv", P53_COLUMNS, _p53_rows())
    _write(
        path / "phh_clonal_population_trajectories.csv",
        CLONAL_COLUMNS,
        _clonal_rows(),
    )
    _write(
        path / "phh_capability_parameter_observations.csv",
        CAPABILITY_COLUMNS,
        _capability_rows(),
    )


def test_contract_and_absent_delivery_are_explicitly_fail_closed(tmp_path: Path) -> None:
    contract = load_completion_evidence_contract()
    assert contract["contract_id"] == "phh_completion_evidence_bundle_contract_v1"

    snapshot = completion_evidence_bundle_intake_snapshot(tmp_path / "absent")
    validate_completion_evidence_bundle_intake_snapshot(snapshot)

    assert snapshot["status"] == "awaiting_external_completion_evidence_bundle"
    assert snapshot["summary"]["required_table_count"] == 3
    assert snapshot["summary"]["required_capability_slot_count"] == 44
    assert snapshot["summary"]["quantitatively_authorized_item_count"] == 0
    assert snapshot["automatic_parameter_activation"] is False
    assert snapshot["automatic_state_coupling"] is False
    assert snapshot["predictive_authority"] is False


def test_complete_software_fixture_is_structurally_audited_without_activation(
    tmp_path: Path,
) -> None:
    _write_bundle(tmp_path)
    snapshot = completion_evidence_bundle_intake_snapshot(tmp_path)

    assert snapshot["status"] == "delivery_structurally_audited_manual_review_required"
    assert snapshot["summary"] == {
        "required_table_count": 3,
        "delivered_table_count": 3,
        "record_count": 50,
        "structurally_complete_item_count": 46,
        "covered_capability_slot_count": 44,
        "required_capability_slot_count": 44,
        "heldout_capability_slot_count": 0,
        "quantitatively_authorized_item_count": 0,
    }
    assert snapshot["automatic_parameter_activation"] is False
    assert snapshot["automatic_state_coupling"] is False


def test_wrong_capability_unit_and_cross_split_donor_are_rejected(
    tmp_path: Path,
) -> None:
    _write_bundle(tmp_path)
    capability_path = tmp_path / "phh_capability_parameter_observations.csv"
    rows = _capability_rows()
    rows[0]["raw_unit"] = "invented-unit"
    _write(capability_path, CAPABILITY_COLUMNS, rows)
    with pytest.raises(CompletionEvidenceError, match="unit does not match"):
        completion_evidence_bundle_intake_snapshot(tmp_path)

    rows[0]["raw_unit"] = next(
        slot.unit
        for feature in HEPATOCYTE_CAPABILITIES
        for slot in feature.parameter_slots
        if feature.id == rows[0]["capability_id"]
        and slot.id == rows[0]["parameter_slot_id"]
    )
    rows[0]["split_role"] = "independent_heldout"
    _write(capability_path, CAPABILITY_COLUMNS, rows)
    with pytest.raises(CompletionEvidenceError, match="donor crossed"):
        completion_evidence_bundle_intake_snapshot(tmp_path)
