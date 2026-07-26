from __future__ import annotations

import csv
from pathlib import Path

import pytest

from cell_engine.quantitative.receptor_signaling_trajectory import (
    ReceptorSignalingTrajectoryError,
    assess_receptor_signaling_pathway,
    load_receptor_signaling_contract,
    load_receptor_signaling_dataset,
    receptor_signaling_trajectory_snapshot,
)


def _fields() -> list[str]:
    contract = load_receptor_signaling_contract()
    return [
        item["id"]
        for group in ("required_columns", "conditional_columns")
        for item in contract[group]
    ]


def _row(record_id: str, stage: str, time: float, **updates: str) -> dict[str, str]:
    row = {field: "null" for field in _fields()}
    row.update(
        {
            "record_id": record_id,
            "pathway_id": "insulin_insr_pi3k_akt",
            "stage_slot_id": stage,
            "series_id": f"{stage}-series",
            "observable_id": stage,
            "observable_kind": "abundance",
            "split_role": "calibration",
            "donor_id": "donor-cal",
            "source_study_id": "study-cal",
            "source_locator": "doi:test#fixture",
            "source_type": "primary_experiment",
            "species": "Homo sapiens",
            "cell_type": "primary human hepatocyte",
            "biological_system": "3D PHH spheroid",
            "culture_format": "spheroid",
            "health_state": "healthy",
            "medium_context": "defined fixture medium",
            "ligand_or_partner": "insulin",
            "receptor_or_channel": "INSR",
            "membrane_domain": "sinusoidal_basolateral",
            "measurement_geometry": "cell_internal",
            "assay": "fixture assay",
            "biological_replicate_id": "replicate-cal",
            "time_value": str(time),
            "time_unit": "min",
            "reported_value": "0.5",
            "reported_unit": "dimensionless",
            "reported_statistic": "raw",
            "sample_size": "1",
            "manual_primary_source_review_status": "verified",
            "context_role": "direct_healthy_phh",
            "notes": "software fixture only",
        }
    )
    row.update(updates)
    return row


def _complete_rows() -> list[dict[str, str]]:
    rows = [
        _row(
            "exposure",
            "ligand_or_partner_exposure",
            0,
            observable_kind="concentration",
            measurement_geometry="soluble_3d",
            reported_unit="nM",
            ligand_exposure_value="10",
            ligand_exposure_unit="nM",
        ),
        _row(
            "density",
            "receptor_or_channel_surface_density",
            0,
            observable_kind="surface_density",
            measurement_geometry="membrane_2d",
            reported_unit="copies_per_um2",
            surface_area_value="250",
            surface_area_unit="um2",
        ),
    ]
    for index, time in enumerate((0, 5, 15)):
        rows.append(
            _row(
                f"occupancy-{index}",
                "active_fraction_or_occupancy",
                time,
                observable_kind="occupancy_fraction",
            )
        )
    rows.extend(
        (
            _row(
                "kon",
                "association_dissociation",
                0,
                observable_kind="kon_3d",
                measurement_geometry="soluble_3d",
                reported_unit="per_nM_per_s",
                binding_dimension="3d",
            ),
            _row(
                "koff",
                "association_dissociation",
                1,
                observable_kind="koff",
                measurement_geometry="soluble_3d",
                reported_unit="per_s",
            ),
        )
    )
    dynamic = (
        ("internal", "internalization_recycling_or_gate_turnover", "internalized_fraction"),
        ("proximal", "proximal_signal", "phosphorylation_fraction"),
        ("downstream", "downstream_functional_response", "functional_response"),
    )
    for prefix, stage, kind in dynamic:
        for index, time in enumerate((0, 10, 30)):
            rows.append(
                _row(
                    f"{prefix}-{index}",
                    stage,
                    time,
                    observable_kind=kind,
                )
            )
    digest = "a" * 64
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


def test_empty_receptor_signal_intake_is_explicitly_non_authoritative() -> None:
    snapshot = receptor_signaling_trajectory_snapshot()
    assert snapshot["expected_header_count"] == 48
    assert snapshot["target_pathway_count"] == 8
    assert snapshot["required_stage_slot_count"] == 64
    assert snapshot["record_count"] == 0
    assert snapshot["receptor_activation_allowed_count"] == 0
    assert snapshot["signal_execution_allowed_count"] == 0
    assert snapshot["cell_state_coupling_allowed_count"] == 0


def test_receptor_signal_header_is_exact(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("pathway_id,value\nx,1\n", encoding="utf-8")
    with pytest.raises(ReceptorSignalingTrajectoryError):
        load_receptor_signaling_dataset(path)


def test_receptor_signal_donor_cannot_cross_split_roles(tmp_path: Path) -> None:
    rows = _complete_rows()
    for row in rows:
        if row["split_role"] == "independent_heldout":
            row["donor_id"] = "donor-cal"
            row["source_study_id"] = "study-cal"
    path = tmp_path / "leak.csv"
    _write(path, rows)
    with pytest.raises(ReceptorSignalingTrajectoryError):
        load_receptor_signaling_dataset(path)


def test_structurally_complete_signal_chain_still_has_zero_runtime_authority(
    tmp_path: Path,
) -> None:
    path = tmp_path / "complete.csv"
    _write(path, _complete_rows())
    dataset = load_receptor_signaling_dataset(path)
    assessment = assess_receptor_signaling_pathway(
        "insulin_insr_pi3k_akt", dataset.records
    )
    assert assessment.complete_calibration_donor_count == 1
    assert assessment.structurally_complete is True
    assert assessment.receptor_activation_allowed is False
    assert assessment.signal_execution_allowed is False
    assert assessment.cell_state_coupling_allowed is False
