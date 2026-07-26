from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import pytest

from cell_engine.quantitative.intracellular_mobility import (
    IntracellularMobilityError,
    intracellular_mobility_intake_snapshot,
    load_intracellular_mobility_contract,
    load_intracellular_mobility_observations,
)


def _header() -> list[str]:
    contract = load_intracellular_mobility_contract()
    return [
        item["id"]
        for group in ("required_columns", "conditional_columns")
        for item in contract[group]
    ]


def _raw_artifact(tmp_path: Path) -> tuple[Path, str]:
    path = tmp_path / "raw-observations.txt"
    path.write_text("software fixture raw observations", encoding="utf-8")
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def _base_row(
    *,
    raw_path: Path,
    raw_sha256: str,
    record_id: str,
    stage_id: str,
    series_id: str,
    observation_index: int = 0,
    independent_value: float = 0.0,
    split_role: str = "calibration",
    donor_id: str = "donor-calibration",
    source_study_id: str = "study-calibration",
    probe_radius: float = 1.0,
) -> dict[str, str]:
    row = {field: "null" for field in _header()}
    row.update(
        {
            "record_id": record_id,
            "target_species_id": "ATP",
            "stage_id": stage_id,
            "series_id": series_id,
            "observation_index": str(observation_index),
            "donor_id": donor_id,
            "split_role": split_role,
            "source_study_id": source_study_id,
            "source_locator": f"fixture/{record_id}",
            "species": "Homo sapiens",
            "biological_system": "primary human hepatocytes",
            "culture_format": "sandwich culture",
            "tissue_health_state": "healthy adult donor",
            "liver_zone": "midlobular",
            "biological_replicate_id": "replicate-1",
            "compartment": "cytosol",
            "subcompartment": "aqueous mobile phase",
            "molecular_form": "free ATP",
            "label_or_probe_identity": "software fixture probe",
            "probe_hydrodynamic_radius_value": str(probe_radius),
            "probe_hydrodynamic_radius_unit": "nm",
            "measurement_method": "software fixture FCS",
            "independent_axis_name": "lag_time",
            "independent_value": str(independent_value),
            "independent_unit": "s",
            "observed_quantity": "autocorrelation",
            "observed_value": str(1.0 / (1.0 + independent_value)),
            "observed_unit": "dimensionless",
            "uncertainty_value": "0.01",
            "uncertainty_type": "software fixture SD",
            "assay_temperature_value": "37",
            "assay_temperature_unit": "degC",
            "assay_ph": "7.2",
            "raw_artifact_path": str(raw_path),
            "raw_artifact_sha256": raw_sha256,
            "manual_primary_source_review_status": "pass",
        }
    )
    return row


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=_header())
        writer.writeheader()
        writer.writerows(rows)


def test_empty_mobility_intake_keeps_all_authority_zero(tmp_path: Path) -> None:
    snapshot = intracellular_mobility_intake_snapshot(tmp_path / "missing.csv")
    summary = snapshot["summary"]
    assert summary["required_field_count"] == 36
    assert summary["conditional_field_count"] == 14
    assert summary["target_species_count"] == 43
    assert summary["required_stage_slot_count"] == 387
    assert summary["record_count"] == 0
    assert summary["apparent_diffusivity_authorized_species_count"] == 0
    assert summary["crowding_law_authorized_species_count"] == 0
    assert summary["reaction_coupled_species_count"] == 0
    assert summary["global_viscosity_multiplier_count"] == 0


def test_exact_mobility_header_is_required(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("record_id,target_species_id\n1,ATP\n", encoding="utf-8")
    with pytest.raises(IntracellularMobilityError, match="header changed"):
        load_intracellular_mobility_observations(path)


def test_donor_split_leakage_is_rejected(tmp_path: Path) -> None:
    raw_path, raw_sha = _raw_artifact(tmp_path)
    rows = [
        _base_row(
            raw_path=raw_path,
            raw_sha256=raw_sha,
            record_id="calibration",
            stage_id="molecular_identity_state",
            series_id="identity-calibration",
        ),
        _base_row(
            raw_path=raw_path,
            raw_sha256=raw_sha,
            record_id="heldout",
            stage_id="compartment_localization",
            series_id="localization-heldout",
            split_role="independent_heldout",
        ),
    ]
    path = tmp_path / "leak.csv"
    _write_rows(path, rows)
    with pytest.raises(IntracellularMobilityError, match="donor leaks"):
        load_intracellular_mobility_observations(path)


def test_dynamic_series_requires_three_strictly_ordered_points(tmp_path: Path) -> None:
    raw_path, raw_sha = _raw_artifact(tmp_path)
    rows = [
        _base_row(
            raw_path=raw_path,
            raw_sha256=raw_sha,
            record_id=f"raw-{index}",
            stage_id="raw_mobility_trajectory",
            series_id="raw-series",
            observation_index=index,
            independent_value=value,
        )
        for index, value in enumerate((0.0, 0.2))
    ]
    path = tmp_path / "short.csv"
    _write_rows(path, rows)
    with pytest.raises(IntracellularMobilityError, match="at least three"):
        load_intracellular_mobility_observations(path)


def test_complete_software_fixture_never_auto_activates_mobility(tmp_path: Path) -> None:
    raw_path, raw_sha = _raw_artifact(tmp_path)
    rows: list[dict[str, str]] = []
    scalar_stages = [
        "molecular_identity_state",
        "compartment_localization",
        "apparent_diffusivity_model",
        "local_crowding_abundance_field",
        "binding_free_fraction",
    ]
    for stage in scalar_stages:
        rows.append(
            _base_row(
                raw_path=raw_path,
                raw_sha256=raw_sha,
                record_id=stage,
                stage_id=stage,
                series_id=f"{stage}-series",
            )
        )
    for probe_index, radius in enumerate((1.0, 2.0, 3.0)):
        rows.append(
            _base_row(
                raw_path=raw_path,
                raw_sha256=raw_sha,
                record_id=f"probe-{probe_index}",
                stage_id="probe_scale_calibration",
                series_id=f"probe-series-{probe_index}",
                probe_radius=radius,
            )
        )
    for stage in ("raw_mobility_trajectory", "perturbation_transport_response"):
        for index, value in enumerate((0.0, 0.1, 0.2)):
            rows.append(
                _base_row(
                    raw_path=raw_path,
                    raw_sha256=raw_sha,
                    record_id=f"{stage}-{index}",
                    stage_id=stage,
                    series_id=f"{stage}-series",
                    observation_index=index,
                    independent_value=value,
                )
            )
    for index, value in enumerate((0.0, 0.1, 0.2)):
        rows.append(
            _base_row(
                raw_path=raw_path,
                raw_sha256=raw_sha,
                record_id=f"heldout-{index}",
                stage_id="independent_heldout_validation",
                series_id="heldout-series",
                observation_index=index,
                independent_value=value,
                split_role="independent_heldout",
                donor_id="donor-heldout",
                source_study_id="study-heldout",
            )
        )
    path = tmp_path / "complete.csv"
    _write_rows(path, rows)

    snapshot = intracellular_mobility_intake_snapshot(path)
    assessment = next(
        item for item in snapshot["assessments"] if item["target_species_id"] == "ATP"
    )
    assert assessment["structurally_complete"] is True
    assert assessment["size_resolved_crowding_chain"] is True
    assert assessment["apparent_diffusivity_activation_allowed"] is False
    assert assessment["crowding_law_activation_allowed"] is False
    assert assessment["reaction_coupling_allowed"] is False
    assert snapshot["summary"]["structurally_complete_species_count"] == 1
    assert snapshot["summary"]["apparent_diffusivity_authorized_species_count"] == 0
    assert snapshot["summary"]["global_viscosity_multiplier_count"] == 0
