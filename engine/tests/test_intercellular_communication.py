from dataclasses import replace

import pytest

from cell_engine.multicell.communication import (
    COMMUNICATION_SOURCES,
    SignalExposure,
    build_hepatocyte_communication_system,
    build_reference_contact_geometry,
    evaluate_signal_chain,
    validate_hepatocyte_communication_system,
)
from cell_engine.multicell.spatial_world import (
    HBV_CRYO_EM_OUTER_DIAMETER_UM,
    SphereShape,
    build_hbv_contact_diagnostic_world,
    build_hepatocyte_contact_diagnostic_world,
    initialize_spatial_world,
    move_body,
    step_spatial_world,
)


def test_atlas_has_source_backed_soluble_and_contact_mechanisms() -> None:
    system = build_hepatocyte_communication_system()
    pathway_by_id = {pathway.id: pathway for pathway in system.pathways}

    assert set(pathway_by_id) == {
        "insulin_insr_pi3k_akt",
        "glucagon_gcgr_camp_pka_creb",
        "hgf_met_regeneration",
        "il6_il6r_gp130_jak_stat3",
        "wnt_fzd_lrp_beta_catenin",
        "hbv_pres1_ntcp_egfr_entry",
        "cdh1_adherens_contact",
        "gjb1_connexin32_gap_junction",
    }
    assert pathway_by_id["hgf_met_regeneration"].steps[0].upstream == "HGF"
    assert pathway_by_id["cdh1_adherens_contact"].contact_required
    assert pathway_by_id["gjb1_connexin32_gap_junction"].mode == "gap_junction"
    assert pathway_by_id["hbv_pres1_ntcp_egfr_entry"].mode == "host_entry"
    assert any(step.downstream == "GCGR_early_endosome" for step in pathway_by_id["glucagon_gcgr_camp_pka_creb"].steps)
    assert all(set(pathway.source_ids) <= set(COMMUNICATION_SOURCES) for pathway in system.pathways)
    assert system.measured_exposure_count == 1
    assert system.matched_response_evidence_count == 3


def test_reference_geometry_separates_contact_from_noncontact() -> None:
    cells, contacts = build_reference_contact_geometry()
    contact_by_cells = {
        frozenset((contact.cell_a, contact.cell_b)): contact
        for contact in contacts
    }
    tangent = contact_by_cells[frozenset(("reference_hepatocyte_A", "reference_hepatocyte_B"))]
    separated = contact_by_cells[frozenset(("reference_hepatocyte_A", "reference_hepatocyte_C"))]

    assert tangent.geometric_contact
    assert tangent.surface_gap_um == pytest.approx(0.0)
    assert tangent.contact_patch_area_um2 is None
    assert not separated.geometric_contact
    assert separated.surface_gap_um > 0.0
    assert len(cells) == 3


def test_default_communication_world_does_not_invent_a_neighbor() -> None:
    system = build_hepatocyte_communication_system()

    assert [cell.id for cell in system.reference_cells] == ["hepatocyte_primary"]
    assert system.reference_contacts == ()
    assert [profile.body_id for profile in system.body_surface_profiles] == ["hepatocyte_primary"]
    assert system.contact_event_chains == ()
    assert system.recognition_candidate_count == 0
    assert system.active_transport_count == 0
    assert not system.reference_geometry_is_biological_observation


def test_phh_surface_capture_expands_identity_without_binding_parameters() -> None:
    system = build_hepatocyte_communication_system()
    profile = system.body_surface_profiles[0]
    molecules = {item.id: item for item in profile.molecules}

    observed_ids = {
        "SLC10A1_NTCP",
        "EGFR",
        "INSR",
        "MET",
        "IL6ST_gp130",
        "ABCB11_BSEP",
        "ABCC2_MRP2",
        "ABCB1_MDR1",
    }
    assert observed_ids <= set(molecules)
    assert all(
        "mallanna2016_phh_surfaceome" in molecules[item].source_ids
        for item in observed_ids
    )
    assert "mallanna2016_phh_surfaceome" not in molecules["CDH1"].source_ids
    assert "not detected" in molecules["CDH1"].evidence_scope
    assert all(
        molecule.surface_abundance_per_um2 is None
        and molecule.kon_2d_um2_per_molecule_s is None
        and molecule.koff_s is None
        and not molecule.patch_distribution_available
        and not molecule.orientation_model_available
        for molecule in molecules.values()
    )


def test_contact_is_necessary_but_does_not_activate_gap_junction() -> None:
    system = build_hepatocyte_communication_system(build_hepatocyte_contact_diagnostic_world())
    tangent = next(contact for contact in system.reference_contacts if contact.geometric_contact)
    evaluation = evaluate_signal_chain(
        SignalExposure(
            id="reference_gap_junction_candidate",
            pathway_id="gjb1_connexin32_gap_junction",
            sender_id=tangent.cell_a,
            receiver_id=tangent.cell_b,
            contact_id=tangent.id,
        ),
        pathways=system.pathways,
        contacts=system.reference_contacts,
    )

    assert evaluation.geometry_gate_passed
    assert evaluation.local_surface_gate_passed is None
    assert evaluation.local_surface_gate_status == "unknown_local_contact_requirements_not_measured"
    assert evaluation.predicted_receptor_activation is None
    assert evaluation.predicted_downstream_response is None
    assert not evaluation.may_drive_cell_state
    assert "receiver surface receptor/channel abundance is unavailable" in evaluation.blockers
    assert "quantitative receptor/junction kinetics are not curated" in evaluation.blockers


def test_local_contact_protein_gate_requires_patch_presence_partner_and_orientation() -> None:
    system = build_hepatocyte_communication_system(build_hepatocyte_contact_diagnostic_world())
    contact = next(item for item in system.reference_contacts if item.geometric_contact)
    base = SignalExposure(
        id="local_adherens_gate",
        pathway_id="cdh1_adherens_contact",
        sender_id=contact.cell_a,
        receiver_id=contact.cell_b,
        contact_id=contact.id,
        local_receptor_or_junction_present=True,
        ligand_or_partner_match_at_patch=True,
        orientation_compatible_at_patch=True,
    )

    open_gate = evaluate_signal_chain(base, pathways=system.pathways, contacts=system.reference_contacts)
    closed_gate = evaluate_signal_chain(
        replace(base, id="local_adherens_gate_mismatch", ligand_or_partner_match_at_patch=False),
        pathways=system.pathways,
        contacts=system.reference_contacts,
    )

    assert open_gate.geometry_gate_passed
    assert open_gate.local_surface_gate_passed
    assert open_gate.local_surface_gate_status == "open_local_contact_requirements_observed"
    assert open_gate.predicted_receptor_activation is None
    assert not open_gate.may_drive_cell_state
    assert closed_gate.local_surface_gate_passed is False
    assert closed_gate.local_surface_gate_status == "closed_explicit_local_mismatch"


def test_communication_uses_the_authoritative_spatial_world_when_supplied() -> None:
    world = build_hepatocyte_contact_diagnostic_world(time_s=12.0)
    system = build_hepatocyte_communication_system(world)

    assert {cell.id for cell in system.reference_cells} == {
        "hepatocyte_primary",
        "hepatocyte_neighbor",
    }
    assert len(system.reference_contacts) == 1
    contact = system.reference_contacts[0]
    relation = world.pair_relations[0]
    assert contact.surface_gap_um == pytest.approx(relation.surface_gap_um)
    assert contact.closest_point_a_um == pytest.approx(relation.closest_point_a_um)
    assert contact.closest_point_b_um == pytest.approx(relation.closest_point_b_um)
    assert contact.normal_a_to_b == pytest.approx(relation.normal_a_to_b)
    assert contact.contact_event == "enter"
    assert contact.contact_input_active
    assert contact.contact_patch_area_um2 == pytest.approx(relation.contact_patch_area_um2)
    assert len(contact.contact_patch_polygon_um) == 4
    assert contact.membrane_domain_a == "lateral"
    assert contact.membrane_domain_b == "lateral"
    assert set(contact.candidate_pathway_ids) == {
        "cdh1_adherens_contact",
        "gjb1_connexin32_gap_junction",
    }
    assert contact.normal_load_nN is None
    chain = system.contact_event_chains[0]
    assert chain.geometry_gate_status == "open_engine_contact_patch_input"
    assert {match.molecule_a_id for match in chain.molecular_matches} == {"CDH1", "GJB1_Cx32"}
    assert chain.molecular_recognition_status.startswith("candidate_")
    assert not chain.receptor_ligand_density_available
    assert not chain.two_dimensional_kinetics_available
    assert chain.signaling_status.startswith("blocked_")
    assert chain.transport_status.startswith("blocked_")
    assert not chain.may_drive_cell_state


def test_hbv_contact_uses_true_scale_and_separates_attachment_from_entry() -> None:
    world = build_hbv_contact_diagnostic_world(time_s=4.0)
    virion = next(body for body in world.bodies if body.biological_kind == "virus")
    assert isinstance(virion.shape, SphereShape)
    assert virion.shape.radius_um * 2 == pytest.approx(HBV_CRYO_EM_OUTER_DIAMETER_UM)

    system = build_hepatocyte_communication_system(world)
    contact = system.reference_contacts[0]
    chain = system.contact_event_chains[0]

    assert contact.geometric_contact
    assert contact.surface_gap_um == pytest.approx(0.0, abs=1e-8)
    assert contact.membrane_domain_a == "basolateral"
    assert contact.candidate_pathway_ids == ("hbv_pres1_ntcp_egfr_entry",)
    assert {(match.molecule_a_id, match.molecule_b_id) for match in chain.molecular_matches} == {
        ("SLC10A1_NTCP", "HBV_preS1")
    }
    assert chain.transport_programs == ("hbv_receptor_cofactor_endocytic_entry",)
    assert "molecular_match_candidate" in chain.emitted_events
    assert not chain.receptor_ligand_density_available
    assert not chain.two_dimensional_kinetics_available
    assert not chain.may_drive_cell_state
    assert system.active_transport_count == 0


def test_unknown_hepatocyte_contact_domain_blocks_molecular_candidate() -> None:
    world = build_hbv_contact_diagnostic_world()
    relation = replace(world.pair_relations[0], membrane_domain_a=None)
    unresolved_world = replace(world, pair_relations=(relation,))

    system = build_hepatocyte_communication_system(unresolved_world)
    chain = system.contact_event_chains[0]

    assert chain.geometric_contact
    assert chain.molecular_matches
    assert not chain.molecular_matches[0].domain_compatible
    assert chain.candidate_pathway_ids == ()
    assert chain.transport_programs == ()
    assert chain.molecular_recognition_status == "closed_molecules_outside_contacting_membrane_domains"
    assert not chain.may_drive_cell_state


def test_contact_exit_closes_molecular_signal_and_transport_candidates() -> None:
    world = build_hepatocyte_contact_diagnostic_world()
    primary, neighbor = world.bodies
    separated = step_spatial_world(
        world,
        1.0,
        bodies=(primary, move_body(neighbor, (0.0, 30.0, 0.0))),
    )

    system = build_hepatocyte_communication_system(separated)
    chain = system.contact_event_chains[0]

    assert chain.contact_event == "exit"
    assert not chain.geometric_contact
    assert chain.candidate_pathway_ids == ()
    assert chain.transport_programs == ()
    assert chain.emitted_events == ("geometry_contact_exit",)
    assert chain.molecular_recognition_status == "inactive_without_geometric_contact"
    assert not chain.may_drive_cell_state


def test_generic_bacterium_does_not_inherit_a_species_unspecified_uptake_rule() -> None:
    hbv_world = build_hbv_contact_diagnostic_world()
    primary, virion = hbv_world.bodies
    bacterium = replace(
        virion,
        id="generic_bacterium",
        biological_kind="bacterium",
        state_ref="species_unspecified_bacterium",
        geometry_evidence="unit_test_reuses_tangent_geometry_not_bacterium_morphometry",
        molecular_profile_id=None,
        source_ids=(),
    )
    world = initialize_spatial_world((primary, bacterium), scenario_kind="generic_bacterium_gate_test")

    system = build_hepatocyte_communication_system(world)
    chain = system.contact_event_chains[0]

    assert chain.geometric_contact
    assert chain.molecular_recognition_status == "blocked_surface_profile_missing"
    assert chain.candidate_pathway_ids == ()
    assert chain.transport_programs == ()
    assert not chain.may_drive_cell_state


def test_soluble_signal_requires_exposure_receptor_and_response() -> None:
    system = build_hepatocyte_communication_system()
    evaluation = evaluate_signal_chain(
        SignalExposure(
            id="unknown_hgf_exposure",
            pathway_id="hgf_met_regeneration",
            sender_id="stromal_context",
            receiver_id="reference_hepatocyte_A",
        ),
        pathways=system.pathways,
    )

    assert evaluation.geometry_gate_passed is None
    assert not evaluation.ligand_measurement_available
    assert not evaluation.receptor_measurement_available
    assert not evaluation.matched_response_available
    assert "matched extracellular ligand exposure is unavailable" in evaluation.blockers


def test_measured_phh_insulin_response_still_requires_receptor_abundance_and_kinetics() -> None:
    system = build_hepatocyte_communication_system()
    evaluation = system.evaluated_exposures[0]

    assert evaluation.pathway_id == "insulin_insr_pi3k_akt"
    assert evaluation.ligand_measurement_available
    assert evaluation.matched_response_available
    assert not evaluation.receptor_measurement_available
    assert set(evaluation.matched_response_ids) == {
        "kemas_insulin_pakt_ser473_7min",
        "kemas_insulin_pck1_6h",
        "kemas_insulin_g6pc_6h",
    }
    assert evaluation.predicted_receptor_activation is None
    assert evaluation.predicted_downstream_response is None
    assert not evaluation.may_drive_cell_state
    assert "receiver surface receptor/channel abundance is unavailable" in evaluation.blockers
    assert "quantitative receptor/junction kinetics are not curated" in evaluation.blockers


def test_communication_system_fails_if_uncalibrated_pathway_is_activated() -> None:
    system = build_hepatocyte_communication_system()
    with pytest.raises(ValueError, match="cannot activate cell state"):
        validate_hepatocyte_communication_system(
            replace(system, automatic_state_coupling=True, active_signal_count=1)
        )
