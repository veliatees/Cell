from __future__ import annotations

from cell_engine.io.sbml import inspect_sbml_species_fingerprints
from cell_engine.quantitative.glucose_homeostasis_contract import (
    build_exact_glucose_homeostasis_contract,
    exact_glucose_homeostasis_snapshot,
    validate_exact_glucose_homeostasis_contract,
)
from cell_engine.quantitative.published_glucose_model import OFFICIAL_MODEL_PATH


def test_species_fingerprints_preserve_compartment_and_initial_value_semantics() -> None:
    species = {item.species_id: item for item in inspect_sbml_species_fingerprints(OFFICIAL_MODEL_PATH)}

    assert len(species) == 52
    assert species["glc"].compartment_id == "cyto"
    assert species["glc_blood"].compartment_id == "blood"
    assert species["pyr_mito"].compartment_id == "mito"
    assert all(
        not (item.initial_concentration is not None and item.initial_amount is not None)
        for item in species.values()
    )


def test_exact_contract_keeps_topology_separate_from_numerical_execution() -> None:
    state = build_exact_glucose_homeostasis_contract()
    validate_exact_glucose_homeostasis_contract(state)

    assert state.exact_source_topology_ready
    assert state.canonical_pool_contract_ready
    assert state.source_species_count == 52
    assert state.source_reaction_count == 36
    assert state.source_kinetic_law_count == 0
    assert not state.active_runtime_replacement_ready
    assert not state.numerical_execution_enabled
    assert not state.parameter_activation_allowed
    assert not state.predictive_ready


def test_contract_exposes_split_pool_lumping_and_compartment_conflicts() -> None:
    state = build_exact_glucose_homeostasis_contract()
    conflicts = {item.id: item for item in state.runtime_conflicts}
    pools = {item.canonical_pool_id: item for item in state.canonical_pools}

    assert all(item.detected for item in conflicts.values())
    assert pools["glucose_cytosol"].source_species_ids == ("glc",)
    assert pools["glucose_cytosol"].exploratory_runtime_species_ids == ("glucose", "glucose_cyto")
    assert set(conflicts) == {
        "split_cytosolic_glucose_pool",
        "duplicate_glucose_export_channels",
        "lumped_lower_gluconeogenesis",
        "cytosol_mitochondrion_compartment_collapse",
    }


def test_exact_contract_snapshot_reports_zero_executable_reactions() -> None:
    summary = exact_glucose_homeostasis_snapshot()["summary"]

    assert summary["source_compartment_count"] == 5
    assert summary["source_species_count"] == 52
    assert summary["source_reaction_count"] == 36
    assert summary["source_kinetic_law_count"] == 0
    assert summary["detected_runtime_conflict_count"] == 4
    assert summary["activated_parameter_count"] == 0
    assert summary["executable_reaction_count"] == 0
