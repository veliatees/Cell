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
    build_hepatocyte_contact_diagnostic_world,
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
        "cdh1_adherens_contact",
        "gjb1_connexin32_gap_junction",
    }
    assert pathway_by_id["hgf_met_regeneration"].steps[0].upstream == "HGF"
    assert pathway_by_id["cdh1_adherens_contact"].contact_required
    assert pathway_by_id["gjb1_connexin32_gap_junction"].mode == "gap_junction"
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
    assert not system.reference_geometry_is_biological_observation


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
