from dataclasses import replace

import pytest

from cell_engine.quantitative.phh_proteome_budget import (
    build_phh_proteome_budget,
    derive_compartment_protein_mass_budget,
    phh_proteome_budget_snapshot,
    validate_phh_proteome_budget,
)


def test_phh_proteome_budget_preserves_source_anchors_and_mass_semantics() -> None:
    state = build_phh_proteome_budget()

    assert state.cohort.donor_count == 7
    assert state.whole_cell_anchors.total_protein_pg_per_cell.value == 600.0
    assert state.whole_cell_anchors.total_protein_molecules_per_cell.value == 8_700_000_000.0
    assert "assumed_200_g_per_L" in state.whole_cell_anchors.estimated_cell_volume_um3.evidence_role
    fractions = {
        item.id: item.fraction_of_total_cellular_protein
        for item in state.compartment_protein_mass_fractions
    }
    assert fractions == {
        "mitochondria": 0.25,
        "endoplasmic_reticulum_and_golgi": 0.12,
        "nucleus": 0.10,
        "integral_plasma_membrane_proteins": 0.012,
    }


def test_phh_proteome_budget_derives_only_arithmetic_protein_masses() -> None:
    state = build_phh_proteome_budget()
    masses = {
        item.id: item.derived_protein_mass_pg_per_cell
        for item in state.derived_compartment_mass_budget
    }

    assert masses == {
        "mitochondria": 150.0,
        "endoplasmic_reticulum_and_golgi": 72.0,
        "nucleus": 60.0,
        "integral_plasma_membrane_proteins": 7.2,
    }
    assert not state.geometry_coupling_ready
    assert not state.dynamic_proteostasis_ready
    assert not state.automatic_state_coupling


def test_phh_proteome_budget_fails_closed_for_invalid_mass_or_promoted_gate() -> None:
    state = build_phh_proteome_budget()

    with pytest.raises(ValueError, match="finite and positive"):
        derive_compartment_protein_mass_budget(0.0, state.compartment_protein_mass_fractions)
    with pytest.raises(ValueError, match="readiness gates"):
        validate_phh_proteome_budget(replace(state, geometry_coupling_ready=True))


def test_phh_proteome_budget_snapshot_reports_static_not_dynamic_coverage() -> None:
    snapshot = phh_proteome_budget_snapshot()

    assert snapshot["summary"]["mitochondrial_protein_mass_pg_per_cell"] == 150.0
    assert snapshot["summary"]["integral_plasma_membrane_protein_mass_pg_per_cell"] == 7.2
    assert snapshot["summary"]["dynamic_parameter_count"] == 0
    assert snapshot["summary"]["geometry_parameter_count"] == 0
