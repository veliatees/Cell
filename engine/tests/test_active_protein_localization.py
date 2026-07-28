from __future__ import annotations

import csv
from pathlib import Path

import pytest

from cell_engine.quantitative.active_protein_localization import (
    ActiveProteinLocalizationError,
    active_protein_localization_snapshot,
    assess_active_protein_localization,
    load_active_protein_localization_contract,
    load_active_protein_localization_dataset,
)


def _fields() -> list[str]:
    contract = load_active_protein_localization_contract()
    return [
        item["id"]
        for group in ("required_columns", "conditional_columns")
        for item in contract[group]
    ]


def _row(record_id: str, slot: str, time: float, **updates: str) -> dict[str, str]:
    row = {field: "null" for field in _fields()}
    row.update(
        {
            "record_id": record_id,
            "protein_id": "bsep",
            "gene": "ABCB11",
            "slot_id": slot,
            "series_id": f"{slot}-series",
            "observable_id": slot,
            "observable_kind": "amount",
            "split_role": "calibration",
            "donor_id": "donor-cal",
            "source_study_id": "study-cal",
            "source_locator": "doi:test#fixture",
            "source_type": "primary_experiment",
            "species": "Homo sapiens",
            "cell_type": "primary human hepatocyte",
            "biological_system": "sandwich-cultured PHH",
            "culture_format": "sandwich",
            "health_state": "healthy",
            "polarity_state": "polarized_canalicular_network",
            "biological_replicate_id": "replicate-cal",
            "assay": "fixture assay",
            "compartment": "plasma_membrane",
            "membrane_domain": "canalicular_apical",
            "time_value": str(time),
            "time_unit": "min",
            "reported_value": "10",
            "reported_unit": "fmol",
            "reported_statistic": "raw",
            "sample_size": "1",
            "denominator_type": "per_cell",
            "manual_primary_source_review_status": "verified",
            "context_role": "direct_healthy_phh",
            "notes": "software fixture only",
        }
    )
    row.update(updates)
    return row


def _complete_rows() -> list[dict[str, str]]:
    rows = [
        _row("total", "total_abundance", 0),
        _row("membrane", "plasma_membrane_localized_abundance", 0),
        _row("domain", "membrane_domain_localized_abundance", 0),
        _row(
            "active-fraction",
            "active_fraction",
            0,
            observable_kind="fraction",
            reported_value="0.4",
            reported_unit="dimensionless",
            active_state_definition="ATP-dependent taurocholate transport competent",
        ),
        _row(
            "area",
            "domain_surface_area",
            0,
            observable_kind="area",
            reported_value="35",
            reported_unit="um2",
            surface_area_value="35",
            surface_area_unit="um2",
            denominator_type="canalicular_domain_area",
        ),
        _row(
            "active-domain",
            "active_domain_copy_or_density",
            0,
            observable_kind="density",
            reported_value="12",
            reported_unit="copies_per_um2",
            surface_area_value="35",
            surface_area_unit="um2",
            active_state_definition="ATP-dependent taurocholate transport competent",
            denominator_type="canalicular_domain_area",
        ),
    ]
    for index, time in enumerate((0, 10, 30)):
        rows.append(
            _row(
                f"function-{index}",
                "same_assay_functional_readout",
                time,
                observable_kind="functional_response",
                reported_unit="pmol_per_cell_per_min",
                activity_probe_or_substrate="taurocholate",
                probe_or_substrate_concentration="1",
                probe_or_substrate_concentration_unit="uM",
            )
        )
    digest = "b" * 64
    for index, time in enumerate((0, 10, 30)):
        rows.append(
            _row(
                f"heldout-{index}",
                "independent_heldout_validation",
                time,
                observable_kind="validation_result",
                split_role="independent_heldout",
                donor_id="donor-heldout",
                source_study_id="study-heldout",
                biological_replicate_id="replicate-heldout",
                context_role="independent_healthy_phh_validation",
                validation_model_artifact_sha256=digest,
                validation_prediction_id=f"prediction-{index}",
                validation_observation_id=f"observation-{index}",
                frozen_before_heldout_access="true",
            )
        )
    return rows


def _write(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=_fields())
        writer.writeheader()
        writer.writerows(rows)


def test_empty_active_protein_intake_is_explicitly_non_authoritative() -> None:
    snapshot = active_protein_localization_snapshot()
    assert snapshot["expected_header_count"] == 52
    assert snapshot["target_protein_count"] == 8
    assert snapshot["required_protein_slot_count"] == 63
    assert snapshot["record_count"] == 0
    assert snapshot["active_copy_or_concentration_authorized_count"] == 0
    assert snapshot["functional_rate_authorized_count"] == 0
    assert snapshot["cell_state_coupling_allowed_count"] == 0


def test_active_protein_header_is_exact(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("protein_id,value\nbsep,1\n", encoding="utf-8")
    with pytest.raises(ActiveProteinLocalizationError):
        load_active_protein_localization_dataset(path)


def test_active_protein_donor_cannot_cross_split_roles(tmp_path: Path) -> None:
    rows = _complete_rows()
    for row in rows:
        if row["split_role"] == "independent_heldout":
            row["donor_id"] = "donor-cal"
            row["source_study_id"] = "study-cal"
    path = tmp_path / "leak.csv"
    _write(path, rows)
    with pytest.raises(ActiveProteinLocalizationError):
        load_active_protein_localization_dataset(path)


def test_structurally_complete_active_protein_still_has_zero_runtime_authority(
    tmp_path: Path,
) -> None:
    path = tmp_path / "complete.csv"
    _write(path, _complete_rows())
    dataset = load_active_protein_localization_dataset(path)
    assessment = assess_active_protein_localization("bsep", dataset.records)
    assert assessment.complete_calibration_donor_count == 1
    assert assessment.structurally_complete is True
    assert assessment.active_copy_or_concentration_authorized is False
    assert assessment.functional_rate_authorized is False
    assert assessment.cell_state_coupling_allowed is False
