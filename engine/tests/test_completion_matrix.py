from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from cell_engine.validation.completion_matrix import (
    build_hepatocyte_completion_matrix,
    validate_hepatocyte_completion_matrix,
)


ROOT = Path(__file__).resolve().parents[2]


def test_completion_matrix_reports_scoped_progress_without_a_realism_percentage() -> None:
    matrix = build_hepatocyte_completion_matrix()
    validate_hepatocyte_completion_matrix(matrix)
    summary = matrix["summary"]
    assert summary["entry_count"] == 49
    assert summary["closed_count"] == 27
    assert summary["partial_count"] == 8
    assert summary["blocked_missing_evidence_count"] == 12
    assert summary["external_action_required_count"] == 1
    assert summary["not_applicable_at_model_scale_count"] == 1
    assert summary["biological_accuracy_pct"] is None


def test_whole_cell_runtime_is_closed_only_as_an_authority_firewall() -> None:
    matrix = build_hepatocyte_completion_matrix()
    entries = {entry["id"]: entry for entry in matrix["entries"]}
    runtime = entries["whole_cell_runtime_authority_firewall"]
    metrics = runtime["observed_metrics"]
    assert runtime["status"] == "closed"
    assert metrics["explicit_purpose_guard_count"] == 1
    assert metrics["audited_legacy_surface_count"] == 4
    assert metrics["phh_context_matched_surface_count"] == 0
    assert metrics["quantitative_authority_surface_count"] == 0
    assert metrics["predictive_authority_surface_count"] == 0
    assert metrics["authoritative_state_coupling_surface_count"] == 0


def test_legacy_calibration_is_closed_only_as_a_fixture_score_firewall() -> None:
    matrix = build_hepatocyte_completion_matrix()
    entries = {entry["id"]: entry for entry in matrix["entries"]}
    calibration = entries["legacy_calibration_authority_firewall"]
    metrics = calibration["observed_metrics"]
    assert calibration["status"] == "closed"
    assert metrics["explicit_purpose_guard_count"] == 1
    assert metrics["audited_workflow_count"] == 3
    assert metrics["built_in_target_count"] == 3
    assert metrics["placeholder_target_count"] == 3
    assert metrics["source_backed_target_count"] == 0
    assert metrics["biologically_authorized_target_count"] == 0
    assert metrics["scientific_authority_purpose_count"] == 0


def test_render_integrity_is_closed_without_claiming_cross_gpu_pixel_identity() -> None:
    matrix = build_hepatocyte_completion_matrix()
    entries = {entry["id"]: entry for entry in matrix["entries"]}
    visual = entries["visual_regression_automation"]
    assert visual["status"] == "closed"
    assert visual["observed_metrics"]["automated_visual_regression_suites"] == 1
    assert visual["observed_metrics"]["automated_viewport_count"] == 2
    assert visual["observed_metrics"]["exact_cross_gpu_pixel_baseline_count"] == 0
    assert visual["observed_metrics"]["exact_cross_gpu_pixel_equivalence_claim"] is False


def test_context_snapshot_matrix_is_lossless_and_biologically_inert() -> None:
    matrix = build_hepatocyte_completion_matrix()
    entries = {entry["id"]: entry for entry in matrix["entries"]}
    context_matrix = entries["context_snapshot_matrix_integrity"]
    metrics = context_matrix["observed_metrics"]
    assert context_matrix["status"] == "closed"
    assert metrics["canonical_snapshot_count"] == 1
    assert metrics["context_overlay_count"] == 40
    assert metrics["zone_count"] == 3
    assert metrics["nutrition_profile_count"] == 3
    assert metrics["experiment_count"] == 4
    assert metrics["offline_exact_reconstruction_verifier_count"] == 1
    assert metrics["runtime_base_identity_guard_count"] == 1
    assert metrics["runtime_state_surface_guard_count"] == 1
    assert metrics["automatic_biological_parameter_activation_count"] == 0


def test_browser_bundle_budget_is_closed_without_biological_authority() -> None:
    matrix = build_hepatocyte_completion_matrix()
    entries = {entry["id"]: entry for entry in matrix["entries"]}
    browser_bundle = entries["browser_startup_bundle_budget"]
    metrics = browser_bundle["observed_metrics"]
    assert browser_bundle["status"] == "closed"
    assert metrics["production_manifest_gate_count"] == 1
    assert metrics["initial_js_chunk_count"] == 2
    assert metrics["initial_js_raw_bytes"] <= metrics[
        "maximum_initial_js_raw_bytes"
    ]
    assert metrics["initial_js_gzip_bytes"] <= metrics[
        "maximum_initial_js_gzip_bytes"
    ]
    assert metrics["required_deferred_entry_count"] == 6
    assert metrics["automatic_biological_parameter_activation_count"] == 0


def test_organelle_boundaries_report_geometry_adapter_without_mesh_overclaim() -> None:
    matrix = build_hepatocyte_completion_matrix()
    entries = {entry["id"]: entry for entry in matrix["entries"]}
    boundaries = entries["organelle_fluid_boundaries"]
    assert boundaries["status"] == "partial"
    assert boundaries["observed_metrics"]["analytic_obstacle_shape_count"] == 4
    assert boundaries["observed_metrics"]["renderer_geometry_boundary_class_count"] == 10
    assert boundaries["observed_metrics"]["rigid_body_boundary_kinematics_count"] == 1
    assert boundaries["observed_metrics"]["conservative_subgrid_boundary_treatment_count"] == 1
    assert boundaries["observed_metrics"]["subgrid_boundary_grid_convergence_test_count"] == 1
    assert boundaries["observed_metrics"]["fractional_face_aperture_solver_count"] == 1
    assert boundaries["observed_metrics"]["generic_watertight_mesh_boundary_kernel_count"] == 1
    assert boundaries["observed_metrics"]["repository_self_intersection_audit_kernel_count"] == 1
    assert boundaries["observed_metrics"]["repository_self_intersection_audited_mesh_count"] == 0
    assert boundaries["observed_metrics"]["mesh_intake_contract_count"] == 1
    assert boundaries["observed_metrics"]["mesh_target_structure_count"] == 11
    assert boundaries["observed_metrics"]["delivered_mesh_artifact_count"] == 0
    assert boundaries["observed_metrics"]["full_watertight_mesh_boundary_count"] == 0


def test_memory_and_active_cargo_engineering_remain_biologically_fail_closed() -> None:
    matrix = build_hepatocyte_completion_matrix()
    entries = {entry["id"]: entry for entry in matrix["entries"]}
    memory = entries["cellular_memory_laws"]["observed_metrics"]
    assert memory["trajectory_contract_column_count"] == 34
    assert memory["write_persist_rechallenge_gate_count"] == 1
    assert memory["complete_donor_trajectory_record_count"] == 0
    assert memory["quantitatively_authorized_memory_law_count"] == 0
    cargo = entries["active_intracellular_transport_model"]["observed_metrics"]
    assert cargo["dimensionless_renderer_route_kernels"] == 1
    assert cargo["healthy_phh_active_transport_kernels"] == 0
    assert cargo["trajectory_intake_contract_count"] == 1
    assert cargo["delivered_phh_route_count"] == 0
    assert cargo["quantitatively_authorized_phh_route_count"] == 0


def test_local_membrane_and_generative_data_planes_are_partial_or_blocked() -> None:
    matrix = build_hepatocyte_completion_matrix()
    entries = {entry["id"]: entry for entry in matrix["entries"]}
    local = entries["local_non_affine_membrane_coupling"]
    assert local["status"] == "partial"
    assert local["observed_metrics"]["local_star_shaped_surface_modes_coupled"] == 1
    assert local["observed_metrics"]["local_topology_change_modes_coupled"] == 0
    assert local["observed_metrics"]["locally_conservative_membrane_face_flux_count"] == 1
    assert local["observed_metrics"]["non_star_shaped_closed_mesh_domain_kernel_count"] == 1
    assert local["observed_metrics"]["topology_preserving_adaptive_remeshing_kernel_count"] == 1
    assert local["observed_metrics"]["surface_state_transfer_kernel_count"] == 1
    assert local["observed_metrics"]["runtime_adaptive_remeshing_coupling_count"] == 1
    assert local["observed_metrics"]["automatic_runtime_remeshing_trigger_count"] == 0
    assert local["observed_metrics"]["topology_transition_representation_kernel_count"] == 1
    assert local["observed_metrics"]["conservative_topology_state_transfer_kernel_count"] == 1
    assert local["observed_metrics"]["topology_transition_candidate_transaction_count"] == 1
    assert local["observed_metrics"]["topology_event_intake_contract_count"] == 1
    assert local["observed_metrics"]["delivered_phh_topology_event_record_count"] == 0
    assert local["observed_metrics"]["authorized_phh_topology_event_record_count"] == 0
    assert local["observed_metrics"]["topology_change_remeshing_kernel_count"] == 0
    fsi = entries["fluid_structure_interaction"]
    assert fsi["status"] == "blocked_missing_evidence"
    assert fsi["observed_metrics"]["dimensionless_pressure_membrane_response_kernel_count"] == 1
    assert fsi["observed_metrics"]["force_energy_consistency_test_count"] == 1
    assert fsi["observed_metrics"]["volume_preserving_fsi_candidate_test_count"] == 1
    assert fsi["observed_metrics"]["membrane_pressure_feedback_count"] == 0
    assert fsi["observed_metrics"]["mechanics_calibration_intake_contract_count"] == 1
    assert fsi["observed_metrics"]["mechanics_target_quantity_count"] == 15
    assert fsi["observed_metrics"]["delivered_mechanics_trajectory_count"] == 0
    assert fsi["observed_metrics"]["spatial_fsi_ready_trajectory_count"] == 0
    donor = entries["donor_state_model"]
    assert donor["status"] == "blocked_missing_evidence"
    assert donor["observed_metrics"]["donor_manifest_intake_contract_count"] == 1
    assert donor["observed_metrics"]["delivered_donor_manifest_sample_count"] == 0
    assert donor["observed_metrics"]["validated_generative_donor_models"] == 0


def test_artifact_pin_is_closed_while_fba_and_reaction_activation_remain_blocked() -> None:
    matrix = build_hepatocyte_completion_matrix()
    entries = {entry["id"]: entry for entry in matrix["entries"]}
    assert entries["human_gem_artifact_identity"]["status"] == "closed"
    assert entries["human_gem_artifact_identity"]["observed_metrics"]["runtime_loaded"] is False
    loader = entries["human_gem_sparse_fbc_loader"]
    assert loader["status"] == "closed"
    assert loader["observed_metrics"]["stoichiometric_row_count"] == 8461
    assert loader["observed_metrics"]["stoichiometric_column_count"] == 12931
    assert loader["observed_metrics"]["stoichiometric_nonzero_count"] == 55198
    assert loader["observed_metrics"]["gene_product_label_count"] == 2848
    assert loader["observed_metrics"]["healthy_phh_context_extracted"] is False
    assert loader["observed_metrics"]["fba_execution_allowed"] is False
    fastcc_audit = entries["human_gem_generic_flux_consistency"]
    assert fastcc_audit["status"] == "closed"
    assert fastcc_audit["observed_metrics"]["epsilon"] == 1e-4
    assert fastcc_audit["observed_metrics"]["consistent_reaction_count"] == 11641
    assert fastcc_audit["observed_metrics"]["blocked_reaction_count"] == 1290
    assert fastcc_audit["observed_metrics"]["maximum_mass_balance_residual"] < 1e-8
    assert fastcc_audit["observed_metrics"]["biological_flux_authority"] is False
    native_fba = entries["human_gem_generic_native_fba"]
    assert native_fba["status"] == "closed"
    assert native_fba["observed_metrics"]["objective_reaction_id"] == "MAR13082"
    assert native_fba["observed_metrics"]["objective_is_healthy_phh_measurement"] is False
    assert native_fba["observed_metrics"]["objective_value"] == 124.86814837744569
    assert native_fba["observed_metrics"]["active_reaction_count_at_1e_minus_9"] == 2566
    assert native_fba["observed_metrics"]["biological_flux_authority"] is False
    proteome_gpr = entries["seven_donor_phh_proteome_gpr_core"]
    assert proteome_gpr["status"] == "closed"
    assert proteome_gpr["observed_metrics"][
        "flux_consistent_core_candidate_count"
    ] == 4555
    assert proteome_gpr["observed_metrics"][
        "active_enzyme_abundance_inferred"
    ] is False
    fastcore_trial = entries["human_gem_real_scale_fastcore_trial"]
    assert fastcore_trial["status"] == "closed"
    assert fastcore_trial["observed_metrics"][
        "source_fastcore_selected_reaction_count"
    ] == 7320
    assert fastcore_trial["observed_metrics"][
        "source_fastcore_output_blocked_reaction_count"
    ] == 408
    assert fastcore_trial["observed_metrics"][
        "closure_selected_reaction_count"
    ] == 11639
    assert fastcore_trial["observed_metrics"]["context_model_accepted"] is False
    stability = entries["seven_donor_gpr_support_stability"]
    assert stability["status"] == "closed"
    assert stability["observed_metrics"][
        "six_donor_support_reaction_count"
    ] == 150
    assert stability["observed_metrics"][
        "largest_leave_one_out_core_expansion_count"
    ] == 62
    scaling = entries["human_gem_fastcore_scaling_sensitivity"]
    assert scaling["status"] == "closed"
    assert scaling["observed_metrics"][
        "adaptive_selected_reaction_count"
    ] == 7415
    assert scaling["observed_metrics"][
        "adaptive_output_blocked_reaction_count"
    ] == 17
    assert scaling["observed_metrics"][
        "adaptive_output_flux_consistent"
    ] is False
    diagnostics = entries["human_gem_fastcore_blocker_diagnostics"]
    assert diagnostics["status"] == "closed"
    assert diagnostics["observed_metrics"][
        "diagnosed_blocker_count"
    ] == 17
    assert diagnostics["observed_metrics"][
        "full_network_active_blocker_count"
    ] == 17
    assert diagnostics["observed_metrics"][
        "minimum_reaction_support_proven"
    ] is False
    repair = entries[
        "human_gem_fastcore_source_limited_support_repair"
    ]
    assert repair["status"] == "closed"
    assert repair["observed_metrics"][
        "added_reaction_union_count"
    ] == 65
    assert repair["observed_metrics"][
        "repaired_candidate_reaction_count"
    ] == 7480
    assert repair["observed_metrics"][
        "strict_fastcc_blocked_reaction_count"
    ] == 0
    assert repair["observed_metrics"][
        "added_reaction_zero_donor_gpr_count"
    ] == 57
    assert repair["observed_metrics"][
        "reaction_activity_in_phh_established"
    ] is False
    assert repair["observed_metrics"]["context_model_accepted"] is False
    shared = entries["human_gem_fastcore_minimum_shared_support"]
    assert shared["status"] == "closed"
    assert shared["observed_metrics"][
        "minimum_shared_added_reaction_count"
    ] == 59
    assert shared["observed_metrics"][
        "removed_from_per_target_union_count"
    ] == 6
    assert shared["observed_metrics"][
        "repaired_candidate_reaction_count"
    ] == 7474
    assert shared["observed_metrics"][
        "strict_fastcc_blocked_reaction_count"
    ] == 0
    assert shared["observed_metrics"][
        "reaction_activity_in_phh_established"
    ] is False
    optimality = entries["human_gem_fastcore_support_optimality"]
    assert optimality["status"] == "closed"
    assert optimality["observed_metrics"][
        "minimum_support_set_count"
    ] == 2
    assert optimality["observed_metrics"][
        "reactions_present_in_every_minimum_support_count"
    ] == 58
    assert optimality["observed_metrics"][
        "optional_reaction_ids_in_input_order"
    ] == ["MAR02308", "MAR10035"]
    assert optimality["observed_metrics"][
        "terminal_infeasibility_proven"
    ] is True
    global_support = entries[
        "human_gem_fastcore_global_support_cardinality"
    ]
    assert global_support["status"] == "closed"
    assert global_support["observed_metrics"][
        "global_candidate_reaction_count"
    ] == 4226
    assert global_support["observed_metrics"][
        "lower_bound_target_ids_in_input_order"
    ] == ["MAR00468", "MAR00612"]
    assert global_support["observed_metrics"][
        "lower_bound_exact_minimum_added_reaction_count"
    ] == 59
    assert global_support["observed_metrics"][
        "upper_bound_feasible_added_reaction_count"
    ] == 59
    assert global_support["observed_metrics"]["bounds_match"] is True
    assert global_support["observed_metrics"][
        "global_minimum_cardinality_proven"
    ] is True
    assert global_support["observed_metrics"][
        "global_minimum_identity_sets_enumerated"
    ] is False
    assert global_support["observed_metrics"][
        "global_minimum_support_set_unique"
    ] is None
    assert global_support["observed_metrics"][
        "reaction_activity_in_phh_established"
    ] is False
    global_counterexample = entries[
        "human_gem_fastcore_global_support_counterexample"
    ]
    assert global_counterexample["status"] == "closed"
    assert global_counterexample["observed_metrics"][
        "global_minimum_cardinality"
    ] == 59
    assert global_counterexample["observed_metrics"][
        "known_distinct_global_minimum_support_set_count_lower_bound"
    ] == 3
    assert global_counterexample["observed_metrics"][
        "presolve_infeasibility_disagreed"
    ] is True
    assert global_counterexample["observed_metrics"][
        "counterexample_only_reaction_ids_in_input_order"
    ] == ["MAR00494"]
    assert global_counterexample["observed_metrics"][
        "outside_scoped_pool_reaction_ids_in_input_order"
    ] == ["MAR00494"]
    assert global_counterexample["observed_metrics"][
        "all_target_lp_certificate_count"
    ] == 17
    assert global_counterexample["observed_metrics"][
        "strict_fastcc_blocked_reaction_count"
    ] == 0
    assert global_counterexample["observed_metrics"][
        "global_minimum_identity_enumeration_complete"
    ] is False
    assert global_counterexample["observed_metrics"][
        "global_minimum_support_set_unique"
    ] is False
    assert global_counterexample["observed_metrics"][
        "reaction_activity_in_phh_established"
    ] is False
    fixed_core_completion = entries[
        "human_gem_fastcore_fixed_core_completion_enumeration"
    ]
    assert fixed_core_completion["status"] == "closed"
    assert fixed_core_completion["observed_metrics"][
        "fixed_common_reaction_count"
    ] == 58
    assert fixed_core_completion["observed_metrics"][
        "remaining_candidate_reaction_count"
    ] == 4168
    assert fixed_core_completion["observed_metrics"][
        "known_singleton_completion_ids_in_model_order"
    ] == ["MAR00494", "MAR02308", "MAR10035"]
    assert fixed_core_completion["observed_metrics"][
        "terminal_infeasibility_confirmed_without_presolve"
    ] is True
    assert fixed_core_completion["observed_metrics"][
        "exact_singleton_completion_count_given_fixed_core"
    ] == 3
    assert fixed_core_completion["observed_metrics"][
        "fixed_core_singleton_completion_enumeration_complete"
    ] is True
    assert fixed_core_completion["observed_metrics"][
        "global_minimum_identity_enumeration_complete"
    ] is False
    assert fixed_core_completion["observed_metrics"][
        "multi_replacement_global_optima_excluded"
    ] is False
    assert fixed_core_completion["observed_metrics"][
        "reaction_activity_in_phh_established"
    ] is False
    global_identity = entries[
        "human_gem_fastcore_global_support_identity_completeness"
    ]
    assert global_identity["status"] == "closed"
    assert global_identity["observed_metrics"][
        "global_minimum_added_reaction_count"
    ] == 59
    assert global_identity["observed_metrics"][
        "global_minimum_support_set_count"
    ] == 3
    assert global_identity["observed_metrics"][
        "global_minimum_support_identity_enumeration_complete"
    ] is True
    assert global_identity["observed_metrics"][
        "global_universal_minimum_support_reaction_count"
    ] == 58
    assert global_identity["observed_metrics"][
        "global_optional_minimum_support_reaction_ids_in_model_order"
    ] == ["MAR00494", "MAR02308", "MAR10035"]
    assert global_identity["observed_metrics"][
        "multi_replacement_global_optima_excluded"
    ] is True
    assert global_identity["observed_metrics"][
        "additional_global_minimum_identity_search_required"
    ] is False
    assert global_identity["observed_metrics"][
        "structural_essentiality_at_larger_support_sizes_established"
    ] is False
    assert global_identity["observed_metrics"][
        "reaction_activity_in_phh_established"
    ] is False
    evidence = entries["human_gem_reaction_evidence_manifest"]
    assert evidence["status"] == "closed"
    assert evidence["observed_metrics"]["manifest_reaction_count"] == 4895
    assert evidence["observed_metrics"][
        "adaptive_noncore_without_gpr_count"
    ] == 2177
    assert evidence["observed_metrics"][
        "automatic_bound_change_allowed"
    ] is False
    generic = entries["generic_fba_fva_numerics"]
    assert generic["status"] == "closed"
    assert generic["observed_metrics"]["analytic_fixture_pass_count"] == 5
    assert generic["observed_metrics"]["alternate_optimum_audit_count"] == 1
    assert generic["observed_metrics"]["biological_flux_authority"] is False
    fastcore = entries["fastcore_context_extraction_numerics"]
    assert fastcore["status"] == "closed"
    assert fastcore["observed_metrics"]["synthetic_fixture_pass_count"] == 1
    assert fastcore["observed_metrics"]["epsilon_has_runtime_default"] is False
    assert fastcore["observed_metrics"][
        "official_adaptive_lp10_supported"
    ] is True
    assert fastcore["observed_metrics"][
        "official_adaptive_lp10_core_multiplier"
    ] == 10.0
    assert fastcore["observed_metrics"]["human_gem_context_extraction_executed"] is False
    assert fastcore["observed_metrics"]["biological_flux_authority"] is False
    assert entries["hepatocyte_fba_execution"]["status"] == "blocked_missing_evidence"
    fba = entries["hepatocyte_fba_execution"]["observed_metrics"]
    assert fba["enabled_execution_gate_count"] == 0
    assert fba["context_extraction_fixture_pass_count"] == 1
    assert fba["human_gem_context_extraction_executed_count"] == 0
    assert fba["execution_bundle_intake_contract_count"] == 1
    assert fba["required_execution_bundle_artifact_count"] == 10
    assert fba["delivered_execution_bundle_count"] == 0
    assert fba["structurally_complete_execution_bundle_count"] == 0
    assert fba["runtime_flux_coupling_allowed_count"] == 0


def test_receptor_and_active_protein_intakes_are_present_but_fail_closed() -> None:
    matrix = build_hepatocyte_completion_matrix()
    entries = {entry["id"]: entry for entry in matrix["entries"]}
    receptor = entries["receptor_signaling_kinetics"]["observed_metrics"]
    assert receptor["trajectory_intake_contract_count"] == 1
    assert receptor["target_pathway_count"] == 8
    assert receptor["required_stage_slot_count"] == 64
    assert receptor["delivered_trajectory_record_count"] == 0
    assert receptor["receptor_activation_allowed_count"] == 0
    protein = entries["active_protein_copies"]["observed_metrics"]
    assert protein["localization_intake_contract_count"] == 1
    assert protein["required_protein_slot_count"] == 63
    assert protein["delivered_localization_record_count"] == 0
    assert protein["active_copy_or_concentration_authorized_count"] == 0
    assert entries["quantitative_reaction_core"]["observed_metrics"]["filled_evidence_slot_count"] == 0


def test_mobility_and_reaction_transport_intakes_are_present_but_fail_closed() -> None:
    matrix = build_hepatocyte_completion_matrix()
    entries = {entry["id"]: entry for entry in matrix["entries"]}
    mobility = entries["macromolecular_crowding_physics"]["observed_metrics"]
    assert mobility["mobility_intake_contract_count"] == 1
    assert mobility["target_species_count"] == 43
    assert mobility["required_mobility_stage_slot_count"] == 387
    assert mobility["delivered_mobility_record_count"] == 0
    assert mobility["apparent_diffusivity_authorized_species_count"] == 0
    assert mobility["quantitatively_bound_crowding_laws"] == 0
    assert mobility["global_viscosity_multiplier_count"] == 0
    transport = entries["reaction_fluid_coupling"]["observed_metrics"]
    assert transport["transport_coupling_intake_contract_count"] == 1
    assert transport["transport_coupling_target_reaction_count"] == 36
    assert transport["transport_coupling_required_stage_slot_count"] == 288
    assert transport["transport_coupling_record_count"] == 0
    assert transport["transport_limitation_demonstrated_reaction_count"] == 0
    assert transport["local_concentration_coupled_reaction_count"] == 0
    assert transport["direct_rate_corrected_reaction_count"] == 0


def test_tracers_are_not_misrepresented_as_water_molecules() -> None:
    matrix = build_hepatocyte_completion_matrix()
    entries = {entry["id"]: entry for entry in matrix["entries"]}
    water = entries["explicit_water_molecules"]
    assert water["status"] == "not_applicable_at_model_scale"
    assert water["observed_metrics"]["biological_species_bound_count"] == 0


def test_quantity_harvest_and_injury_evidence_remain_fail_closed() -> None:
    matrix = build_hepatocyte_completion_matrix()
    entries = {entry["id"]: entry for entry in matrix["entries"]}
    harvest = entries["hepatocyte_quantity_harvest"]
    assert harvest["status"] == "partial"
    assert harvest["observed_metrics"]["raw_record_count"] == 168
    assert harvest["observed_metrics"]["promoted_context_bound_claim_count"] == 16
    assert harvest["observed_metrics"]["healthy_phh_runtime_parameter_count"] == 0
    injury = entries["damage_fate_recovery_calibration"]
    assert injury["status"] == "partial"
    assert injury["observed_metrics"]["matching_protocol_observation_count"] == 9
    assert injury["observed_metrics"]["calibrated_fate_commitment_laws"] == 0
    assert injury["observed_metrics"]["runtime_coupled_observation_count"] == 0
    assert injury["observed_metrics"]["exact_protocol_replay_pass_count"] == 4
    assert injury["observed_metrics"]["near_miss_rejection_count"] == 7
    assert injury["observed_metrics"]["audited_legacy_injury_surface_count"] == 3
    assert injury["observed_metrics"]["legacy_quantitative_authority_surface_count"] == 0
    assert injury["observed_metrics"]["required_donor_trajectory_field_count"] == 19
    assert injury["observed_metrics"]["conditional_donor_trajectory_field_count"] == 10
    assert injury["observed_metrics"]["trajectory_intake_validator_count"] == 1
    assert injury["observed_metrics"]["donor_split_leakage_guard_count"] == 1
    assert injury["observed_metrics"]["independent_heldout_study_guard_count"] == 1
    assert injury["observed_metrics"]["exact_assay_projection_operator_count"] == 1
    assert injury["observed_metrics"]["frozen_evaluation_contract_count"] == 1
    assert injury["observed_metrics"]["complete_donor_trajectory_record_count"] == 0
    assert injury["observed_metrics"]["numeric_measurement_projection_count"] == 0
    assert injury["observed_metrics"]["independent_heldout_result_count"] == 0


def test_completion_matrix_rejects_an_unearned_reaction_promotion() -> None:
    matrix = deepcopy(build_hepatocyte_completion_matrix())
    reaction = next(entry for entry in matrix["entries"] if entry["id"] == "quantitative_reaction_core")
    reaction["observed_metrics"]["filled_evidence_slot_count"] = 1
    with pytest.raises(ValueError, match="reaction evidence"):
        validate_hepatocyte_completion_matrix(matrix)


def test_exported_completion_matrix_is_current() -> None:
    exported = json.loads(
        (ROOT / "data/validation/hepatocyte_completion_matrix.v1.json").read_text(
            encoding="utf-8"
        )
    )
    generated = json.loads(json.dumps(build_hepatocyte_completion_matrix()))
    assert exported == generated
