from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import pytest

from cell_engine.quantitative.reaction_transport_coupling import (
    ReactionTransportCouplingError,
    load_reaction_transport_coupling_contract,
    load_reaction_transport_observations,
    reaction_transport_coupling_intake_snapshot,
    transport_scale_ratio,
)


REACTION_EQUATION = "glucose_cyto -> glycogen"
COUPLING_EQUATION = "dc/dt = -div(u*c) + div(D*grad(c)) - v(c)"


def _header() -> list[str]:
    contract = load_reaction_transport_coupling_contract()
    return [
        item["id"]
        for group in ("required_columns", "conditional_columns")
        for item in contract[group]
    ]


def _raw_artifact(tmp_path: Path) -> tuple[Path, str]:
    path = tmp_path / "raw-reaction-transport.txt"
    path.write_text("software fixture reaction transport observations", encoding="utf-8")
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
) -> dict[str, str]:
    row = {field: "null" for field in _header()}
    row.update(
        {
            "record_id": record_id,
            "target_reaction_id": "glycogen_synthesis",
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
            "reaction_equation": REACTION_EQUATION,
            "reaction_equation_sha256": hashlib.sha256(
                REACTION_EQUATION.encode("utf-8")
            ).hexdigest(),
            "participant_species_ids": "glucose_cyto;glycogen",
            "compartment": "cytosol",
            "localization_method": "software fixture localization",
            "mobility_evidence_record_ids": "mobility-001",
            "geometry_evidence_record_ids": "geometry-001",
            "independent_axis_name": "time",
            "independent_value": str(independent_value),
            "independent_unit": "s",
            "observed_quantity": "reaction output",
            "observed_value": str(1.0 + independent_value),
            "observed_unit": "fixture_unit",
            "uncertainty_value": "0.01",
            "uncertainty_type": "software fixture SD",
            "raw_artifact_path": str(raw_path),
            "raw_artifact_sha256": raw_sha256,
            "model_or_operator_version": "fixture-operator-v1",
            "frozen_before_heldout_access": (
                "true" if split_role == "independent_heldout" else "false"
            ),
            "manual_primary_source_review_status": "pass",
        }
    )
    return row


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=_header())
        writer.writeheader()
        writer.writerows(rows)


def test_empty_reaction_transport_intake_keeps_all_coupling_zero(tmp_path: Path) -> None:
    snapshot = reaction_transport_coupling_intake_snapshot(tmp_path / "missing.csv")
    summary = snapshot["summary"]
    assert summary["required_field_count"] == 35
    assert summary["conditional_field_count"] == 16
    assert summary["target_reaction_count"] == 36
    assert summary["required_stage_slot_count"] == 288
    assert summary["record_count"] == 0
    assert summary["local_concentration_coupled_reaction_count"] == 0
    assert summary["direct_rate_corrected_reaction_count"] == 0
    assert summary["runtime_activated_reaction_count"] == 0
    assert summary["global_fluid_multiplier_count"] == 0


def test_transport_scale_ratio_is_dimensionally_explicit() -> None:
    assert transport_scale_ratio(3.0, 2.0, 4.0) == pytest.approx(1.125)
    with pytest.raises(ReactionTransportCouplingError, match="finite and positive"):
        transport_scale_ratio(3.0, 0.0, 4.0)


def test_exact_reaction_transport_header_is_required(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("record_id,target_reaction_id\n1,glycogen_synthesis\n", encoding="utf-8")
    with pytest.raises(ReactionTransportCouplingError, match="header changed"):
        load_reaction_transport_observations(path)


def test_reaction_transport_donor_split_leakage_is_rejected(tmp_path: Path) -> None:
    raw_path, raw_sha = _raw_artifact(tmp_path)
    rows = [
        _base_row(
            raw_path=raw_path,
            raw_sha256=raw_sha,
            record_id="calibration",
            stage_id="exact_reaction_identity",
            series_id="identity-calibration",
        ),
        _base_row(
            raw_path=raw_path,
            raw_sha256=raw_sha,
            record_id="heldout",
            stage_id="participant_compartment_fields",
            series_id="compartment-heldout",
            split_role="independent_heldout",
        ),
    ]
    path = tmp_path / "leak.csv"
    _write_rows(path, rows)
    with pytest.raises(ReactionTransportCouplingError, match="donor leaks"):
        load_reaction_transport_observations(path)


def test_complete_software_fixture_never_auto_couples_reaction(tmp_path: Path) -> None:
    raw_path, raw_sha = _raw_artifact(tmp_path)
    rows: list[dict[str, str]] = []
    for stage in (
        "exact_reaction_identity",
        "participant_compartment_fields",
        "species_mobility_link",
        "characteristic_length_geometry",
    ):
        rows.append(
            _base_row(
                raw_path=raw_path,
                raw_sha256=raw_sha,
                record_id=stage,
                stage_id=stage,
                series_id=f"{stage}-series",
            )
        )
    for stage in (
        "reaction_timescale_trajectory",
        "transport_perturbation_demonstration",
    ):
        for index, value in enumerate((0.0, 1.0, 2.0)):
            row = _base_row(
                raw_path=raw_path,
                raw_sha256=raw_sha,
                record_id=f"{stage}-{index}",
                stage_id=stage,
                series_id=f"{stage}-series",
                observation_index=index,
                independent_value=value,
            )
            if stage == "transport_perturbation_demonstration":
                row.update(
                    {
                        "transport_limitation_criterion": "fixture pre-registered criterion",
                        "transport_limitation_result": "pass",
                        "perturbation_identity": "fixture transport perturbation",
                        "perturbation_value": "1.0",
                        "perturbation_unit": "fixture_unit",
                    }
                )
            rows.append(row)
    dimensional = _base_row(
        raw_path=raw_path,
        raw_sha256=raw_sha,
        record_id="dimensional-coupling",
        stage_id="dimensional_coupling_law",
        series_id="dimensional-coupling-series",
    )
    dimensional.update(
        {
            "apparent_diffusivity_value": "2.0",
            "apparent_diffusivity_unit": "um2/s",
            "characteristic_length_value": "3.0",
            "characteristic_length_unit": "um",
            "reaction_timescale_value": "4.0",
            "reaction_timescale_unit": "s",
            "transport_scale_ratio_value": "1.125",
            "transport_scale_ratio_definition": "L^2/(D*tau_reaction)",
            "coupling_equation": COUPLING_EQUATION,
            "coupling_equation_sha256": hashlib.sha256(
                COUPLING_EQUATION.encode("utf-8")
            ).hexdigest(),
        }
    )
    rows.append(dimensional)
    for index, value in enumerate((0.0, 1.0, 2.0)):
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

    snapshot = reaction_transport_coupling_intake_snapshot(
        path,
        available_mobility_record_ids={"mobility-001"},
        available_geometry_record_ids={"geometry-001"},
    )
    assessment = next(
        item
        for item in snapshot["assessments"]
        if item["target_reaction_id"] == "glycogen_synthesis"
    )
    assert assessment["structurally_complete"] is True
    assert assessment["dimensionally_consistent_scale_ratio"] is True
    assert assessment["transport_limitation_demonstrated"] is True
    assert assessment["local_concentration_coupling_allowed"] is False
    assert assessment["direct_rate_correction_allowed"] is False
    assert assessment["runtime_activation_allowed"] is False
    assert snapshot["summary"]["structurally_complete_reaction_count"] == 1
    assert snapshot["summary"]["local_concentration_coupled_reaction_count"] == 0
    assert snapshot["summary"]["global_fluid_multiplier_count"] == 0
