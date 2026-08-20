from __future__ import annotations

from copy import deepcopy

import pytest

from cell_engine.validation.metabolic_cycle_program import (
    CYCLE_IDS,
    EDGE_IDS,
    MetabolicCycleProgramError,
    assert_metabolic_cycle_execution_allowed,
    assert_metabolic_edge_coupling_allowed,
    hepatocyte_metabolic_cycle_program_snapshot,
    load_metabolic_cycle_manifest,
    validate_hepatocyte_metabolic_cycle_program,
    validate_metabolic_cycle_manifest,
)


@pytest.fixture(scope="module")
def program() -> dict[str, object]:
    return hepatocyte_metabolic_cycle_program_snapshot()


def _cycles(program: dict[str, object]) -> dict[str, dict[str, object]]:
    return {item["id"]: item for item in program["cycles"]}


def _gates(cycle: dict[str, object]) -> dict[str, dict[str, object]]:
    return {item["id"]: item for item in cycle["gates"]}


def test_manifest_declares_connected_four_cycle_program_without_authority() -> None:
    manifest = load_metabolic_cycle_manifest()

    assert tuple(manifest["cycle_order"]) == CYCLE_IDS
    assert tuple(item["id"] for item in manifest["shared_edges"]) == EDGE_IDS
    assert manifest["scientific_authority"] is False
    assert manifest["automatic_parameter_activation"] is False
    assert manifest["automatic_state_coupling"] is False
    validate_metabolic_cycle_manifest(manifest)


def test_current_program_reports_real_structural_progress_but_zero_execution(
    program: dict[str, object],
) -> None:
    summary = program["summary"]

    assert summary == {
        "cycle_count": 4,
        "cycle_with_structural_surface_count": 4,
        "gate_count": 38,
        "satisfied_gate_count": 8,
        "quantitative_execution_ready_cycle_count": 0,
        "predictive_ready_cycle_count": 0,
        "runtime_coupling_ready_cycle_count": 0,
        "cross_cycle_runtime_ready_cycle_count": 0,
        "shared_edge_count": 5,
        "edge_operator_count": 35,
        "satisfied_edge_operator_count": 5,
        "coupled_edge_count": 0,
        "automatic_parameter_activation_count": 0,
        "automatic_state_coupling_count": 0,
    }
    validate_hepatocyte_metabolic_cycle_program(program)


def test_glucose_gate_preserves_partial_koenig_transfer_truth(
    program: dict[str, object],
) -> None:
    gates = _gates(_cycles(program)["glucose_glycogen_control"])

    assert gates["glucose_topology_audited"]["satisfied"] is True
    equation_gate = gates["glucose_transfer_equations_exact"]
    assert equation_gate["satisfied"] is False
    assert equation_gate["observed"] == {
        "candidate_count": 12,
        "exact_stoichiometry_count": 3,
        "exact_symbolic_rate_law_count": 0,
    }
    scale_gate = gates["glucose_single_cell_scale_ready"]
    assert scale_gate["observed"]["ready_bridge_count"] == 0
    assert gates["glucose_fit_identifiability_ready"]["observed"][
        "fit_eligible_reaction_count"
    ] == 0
    assert gates["glucose_independent_evidence_review_ready"]["satisfied"] is False


def test_apap_gate_separates_mechanism_shape_from_quantitative_cascade(
    program: dict[str, object],
) -> None:
    gates = _gates(_cycles(program)["cyp_apap_redox_injury"])

    assert gates["apap_competing_pathway_topology_ready"]["satisfied"] is True
    assert gates["cyp_function_observation_surface_ready"]["satisfied"] is True
    assert gates["apap_compartmental_redox_topology_ready"]["satisfied"] is True
    assert gates["apap_donor_trajectory_ready"]["satisfied"] is False
    assert gates["apap_donor_trajectory_ready"]["observed"][
        "complete_donor_trajectory_record_count"
    ] == 0
    assert gates["apap_kinetics_calibrated"]["satisfied"] is False
    assert gates["apap_mpt_injury_law_ready"]["satisfied"] is False
    assert gates["apap_independent_evidence_review_ready"]["satisfied"] is False


def test_transport_gate_does_not_turn_total_copies_into_surface_flux(
    program: dict[str, object],
) -> None:
    cycle = _cycles(program)["polarized_transport_bile_flux"]
    gates = _gates(cycle)

    assert tuple(cycle["target_components"]) == (
        "BSEP",
        "MRP2",
        "NTCP",
        "GLUT2",
        "OATP1B1",
        "OATP1B3",
    )
    assert gates["transporter_total_abundance_observed"]["satisfied"] is True
    assert gates["polarized_target_inventory_ready"]["observed"] == {
        "target_transporter_count": 6,
        "quantitative_inventory_count": 2,
        "quantitative_inventory_ids": ("ABCB11_BSEP", "ABCC2_MRP2"),
    }
    assert gates["transporter_surface_density_ready"]["observed"][
        "surface_density_record_count"
    ] == 0
    assert gates["transporter_active_copy_ready"]["observed"][
        "active_copy_count_record_count"
    ] == 0
    assert gates["transporter_flux_fit_ready"]["satisfied"] is False
    assert gates["transport_independent_evidence_review_ready"]["satisfied"] is False


def test_urea_human_gem_gate_separates_solver_from_phh_dfba(
    program: dict[str, object],
) -> None:
    gates = _gates(_cycles(program)["urea_ammonia_human_gem"])

    assert gates["urea_cycle_topology_ready"]["satisfied"] is True
    assert gates["urea_cycle_kinetics_ready"]["satisfied"] is False
    assert gates["human_gem_artifact_and_solver_ready"]["satisfied"] is True
    assert gates["healthy_phh_context_model_ready"]["satisfied"] is False
    assert gates["measured_exchange_bounds_ready"]["observed"][
        "measured_exchange_bound_count"
    ] == 0
    assert gates["dynamic_fba_update_law_ready"]["observed"][
        "registered_dynamic_fba_update_law_count"
    ] == 1
    assert gates["dynamic_fba_update_law_ready"]["satisfied"] is True
    assert gates["dynamic_fba_update_law_ready"]["observed"][
        "automatic_unit_conversion"
    ] is False
    assert gates["dynamic_fba_update_law_ready"]["observed"][
        "biological_flux_authority"
    ] is False
    assert gates["human_gem_independent_evidence_review_ready"][
        "satisfied"
    ] is False
    assert gates["urea_dfba_authoritative_state_coupling_ready"][
        "satisfied"
    ] is False


def test_shared_metabolite_names_never_self_authorize_coupling(
    program: dict[str, object],
) -> None:
    for edge in program["shared_edges"]:
        operators = {item["id"]: item for item in edge["operators"]}
        assert operators["shared_state_identity"]["satisfied"] is True
        assert operators["compartment_mapping"]["satisfied"] is False
        assert operators["unit_and_scale_operator"]["satisfied"] is False
        assert operators["time_alignment_operator"]["satisfied"] is False
        assert operators["donor_context_match"]["satisfied"] is False
        assert operators["transfer_or_conservation_law"]["satisfied"] is False
        assert operators["uncertainty_propagation"]["satisfied"] is False
        assert edge["coupling_ready"] is False
        assert edge["automatic_state_coupling"] is False


@pytest.mark.parametrize("cycle_id", CYCLE_IDS)
@pytest.mark.parametrize(
    "stage", ("quantitative_execution", "prediction", "runtime_coupling")
)
def test_every_current_cycle_activation_attempt_fails_closed(
    program: dict[str, object], cycle_id: str, stage: str
) -> None:
    with pytest.raises(MetabolicCycleProgramError, match="blocked"):
        assert_metabolic_cycle_execution_allowed(
            cycle_id,
            stage=stage,
            program=program,
        )


@pytest.mark.parametrize("edge_id", EDGE_IDS)
def test_every_current_cross_cycle_edge_fails_closed(
    program: dict[str, object], edge_id: str
) -> None:
    with pytest.raises(MetabolicCycleProgramError, match="coupling blocked"):
        assert_metabolic_edge_coupling_allowed(edge_id, program=program)


def test_validator_rejects_readiness_claim_not_supported_by_gates(
    program: dict[str, object],
) -> None:
    tampered = deepcopy(program)
    tampered["cycles"][0]["quantitative_execution_ready"] = True

    with pytest.raises(ValueError, match="readiness is inconsistent"):
        validate_hepatocyte_metabolic_cycle_program(tampered)


def test_validator_rejects_moving_a_blocked_gate_to_another_stage(
    program: dict[str, object],
) -> None:
    tampered = deepcopy(program)
    tampered["cycles"][0]["gates"][1]["stage"] = "runtime_coupling"

    with pytest.raises(ValueError, match="gate assessments changed"):
        validate_hepatocyte_metabolic_cycle_program(tampered)


def test_validator_rejects_gate_observation_not_derived_from_current_evidence(
    program: dict[str, object],
) -> None:
    tampered = deepcopy(program)
    tampered["cycles"][0]["gates"][0]["observed"]["source_reaction_count"] = 35

    with pytest.raises(ValueError, match="diverges from current evidence"):
        validate_hepatocyte_metabolic_cycle_program(tampered)


def test_validator_rejects_edge_operator_not_derived_from_current_evidence(
    program: dict[str, object],
) -> None:
    tampered = deepcopy(program)
    tampered["shared_edges"][0]["operators"][1]["evidence_surface"] = (
        "invented_compartment_map"
    )

    with pytest.raises(ValueError, match="diverge from current evidence"):
        validate_hepatocyte_metabolic_cycle_program(tampered)


def test_validator_rejects_undeclared_top_level_fields(
    program: dict[str, object],
) -> None:
    tampered = deepcopy(program)
    tampered["runtime_override"] = True

    with pytest.raises(ValueError, match="program fields changed"):
        validate_hepatocyte_metabolic_cycle_program(tampered)


def test_manifest_rejects_automatic_state_coupling() -> None:
    tampered = deepcopy(load_metabolic_cycle_manifest())
    tampered["automatic_state_coupling"] = True

    with pytest.raises(ValueError, match="fail-closed policy"):
        validate_metabolic_cycle_manifest(tampered)


def test_manifest_date_is_part_of_the_versioned_identity() -> None:
    tampered = deepcopy(load_metabolic_cycle_manifest())
    tampered["date_verified"] = "2026-08-18"

    with pytest.raises(ValueError, match="fail-closed policy"):
        validate_metabolic_cycle_manifest(tampered)


def test_unknown_cycle_edge_and_stage_are_rejected(
    program: dict[str, object],
) -> None:
    with pytest.raises(KeyError):
        assert_metabolic_cycle_execution_allowed("unknown_cycle", program=program)
    with pytest.raises(KeyError):
        assert_metabolic_edge_coupling_allowed("unknown_edge", program=program)
    with pytest.raises(ValueError, match="unsupported metabolic execution stage"):
        assert_metabolic_cycle_execution_allowed(
            CYCLE_IDS[0], stage="exploratory", program=program
        )
