from __future__ import annotations

from cell_engine.quantitative.compartmental_energy_redox import (
    build_compartmental_energy_redox_contract,
    compartmental_energy_redox_snapshot,
    validate_compartmental_energy_redox_contract,
)


def test_contract_separates_all_required_energy_redox_compartments() -> None:
    contract = build_compartmental_energy_redox_contract()
    validate_compartmental_energy_redox_contract(contract)

    assert len(contract.compartments) == 6
    assert len(contract.pools) == 38
    assert len(contract.processes) == 14
    assert not any(item.volume_initialization_allowed for item in contract.compartments)
    assert not any(item.initialization_allowed for item in contract.pools)
    assert not any(item.numerical_execution_allowed for item in contract.processes)

    pools = {item.id: item for item in contract.pools}
    assert {
        pools["atp_cytosol"].compartment_id,
        pools["atp_mitochondrial_intermembrane_space"].compartment_id,
        pools["atp_mitochondrial_matrix"].compartment_id,
        pools["atp_er_lumen"].compartment_id,
    } == {
        "cytosol",
        "mitochondrial_intermembrane_space",
        "mitochondrial_matrix",
        "er_lumen",
    }
    assert pools["nadph_cytosol"].id != pools["nadph_mitochondrial_matrix"].id
    assert pools["gsh_cytosol"].id != pools["gsh_mitochondrial_matrix"].id
    assert pools["gsh_er_lumen"].initial_value is None


def test_mitochondrial_double_membrane_transport_is_not_collapsed() -> None:
    processes = {
        item.id: item
        for item in build_compartmental_energy_redox_contract().processes
    }
    vdac = processes["outer_mitochondrial_membrane_metabolite_permeation"]
    ant = processes["mitochondrial_adp_atp_exchange"]
    phosphate = processes["mitochondrial_phosphate_import"]

    assert vdac.mediator_gene_symbols == ("VDAC1", "VDAC2", "VDAC3")
    assert "atp_cytosol" in vdac.reactant_pool_ids
    assert "atp_mitochondrial_intermembrane_space" in vdac.product_pool_ids
    assert ant.reactant_pool_ids == (
        "atp_mitochondrial_matrix",
        "adp_mitochondrial_intermembrane_space",
    )
    assert ant.product_pool_ids == (
        "atp_mitochondrial_intermembrane_space",
        "adp_mitochondrial_matrix",
    )
    assert phosphate.mediator_gene_symbols == ("SLC25A3",)
    assert phosphate.product_pool_ids == ("phosphate_mitochondrial_matrix",)


def test_phh_proteome_bridge_preserves_donors_and_distinct_protein_groups() -> None:
    contract = build_compartmental_energy_redox_contract()
    evidence = {
        item.gene_symbol: item
        for item in contract.human_phh_proteome_evidence
    }

    assert len(evidence) == 31
    assert sum(bool(item.protein_groups) for item in evidence.values()) == 27
    for gene in ("SLC25A4", "SLC25A5", "SLC25A6", "SLC25A3"):
        assert evidence[gene].protein_groups
    for gene in ("SLC25A39", "SLC35B1", "ERO1A", "ERO1B"):
        assert not evidence[gene].protein_groups
        assert evidence[gene].source_status == (
            "not_quantified_in_this_source_not_evidence_of_absence"
        )

    assert len(evidence["IDH2"].protein_groups) == 2
    assert len(evidence["NNT"].protein_groups) == 3
    assert len(evidence["VDAC1"].protein_groups) == 2
    assert all(
        tuple(donor_id for donor_id, _ in group.donor_copies_per_nucleus)
        == ("A", "B", "C", "D", "E", "F", "G")
        for item in evidence.values()
        for group in item.protein_groups
    )


def test_aggregate_observations_retain_units_and_cannot_seed_compartments() -> None:
    observations = {
        item.id: item
        for item in build_compartmental_energy_redox_contract().aggregate_observations
    }

    assert len(observations) == 7
    assert observations["human_liver_atp_control"].value == 2.08
    assert observations["human_liver_atp_control"].unit == "umol_per_g_wet_liver"
    exchange = observations["human_liver_apparent_atp_synthesis"]
    assert exchange.value == 29.5
    assert exchange.unit == "mM_per_min"
    assert "exchange" in exchange.permitted_use
    assert not any(item.compartment_allocation_allowed for item in observations.values())
    assert not any(item.kinetic_parameter_fit_allowed for item in observations.values())


def test_contract_detects_legacy_runtime_conflicts_and_activates_nothing() -> None:
    contract = build_compartmental_energy_redox_contract()
    assert len(contract.runtime_conflicts) == 6
    assert all(item.detected for item in contract.runtime_conflicts)
    assert not contract.compartment_initialization_ready
    assert not contract.numerical_execution_enabled
    assert not contract.parameter_activation_allowed
    assert not contract.automatic_state_coupling
    assert not contract.predictive_ready

    summary = compartmental_energy_redox_snapshot()["summary"]
    assert summary["detected_runtime_conflict_count"] == 6
    assert summary["initialized_compartment_pool_count"] == 0
    assert summary["executable_process_count"] == 0
    assert summary["activated_parameter_count"] == 0
