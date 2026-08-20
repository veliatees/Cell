from __future__ import annotations

from cell_engine.quantitative.metabolic_constraint_shell import (
    metabolic_constraint_shell_snapshot,
    validate_metabolic_constraint_shell,
)


def test_constraint_shell_pins_artifact_but_stays_non_executable_without_phh_context() -> None:
    snapshot = metabolic_constraint_shell_snapshot()
    validate_metabolic_constraint_shell(snapshot)
    assert snapshot["version"] == "metabolic_constraint_shell_v15"
    reconstruction = snapshot["candidate_reconstruction"]
    assert reconstruction["model_version"] == "2.0.0"
    assert reconstruction["release_tag"] == "v2.0.0"
    assert reconstruction["release_commit"] == "635f533152dc5f7290ce04d12700eaa882273c3e"
    assert reconstruction["artifact_sha256"] == "cc5a4383c6116b0c91f4db089cc640f29aec7e840249b573b74d3792c9ca4a7a"
    assert reconstruction["artifact_size_bytes"] == 43115559
    assert reconstruction["structural_counts_verified_from_sbml"] == {
        "compartments": 9,
        "metabolites": 8461,
        "reactions": 12931,
        "genes": 2848,
    }
    assert reconstruction["sbml_path"] is None
    assert reconstruction["model_loaded_by_runtime"] is False
    assert reconstruction["model_loader_verified_against_pinned_artifact"] is True
    assert reconstruction["mass_charge_balance_audited_in_project"] is True
    audit = reconstruction["structural_audit"]
    assert audit["one_sided_reaction_count"] == 1660
    assert audit["two_sided_reaction_count"] == 11271
    assert audit["elementally_assessable_reaction_count"] == 9849
    assert audit["elementally_balanced_reaction_count"] == 9832
    assert audit["elementally_imbalanced_reaction_count"] == 17
    assert audit["jointly_unassessable_reaction_count"] == 1422
    assert audit["active_objective_id"] == "obj"
    loader = reconstruction["sparse_fbc_loader_audit"]
    assert loader["stoichiometric_shape"] == [8461, 12931]
    assert loader["stoichiometric_nonzero_count"] == 55198
    assert loader["gene_associated_reaction_count"] == 7782
    assert loader["gene_product_label_count"] == 2848
    assert loader["active_objective_id"] == "obj"
    assert loader["healthy_phh_context_extracted"] is False
    assert loader["fba_execution_allowed"] is False
    fastcc = reconstruction["generic_flux_consistency_audit"]
    assert fastcc["epsilon"] == 1e-4
    assert fastcc["consistent_reaction_count"] == 11641
    assert fastcc["blocked_reaction_count"] == 1290
    assert fastcc["lp7_solve_count"] == 6
    assert fastcc["lp3_solve_count"] == 247
    assert fastcc["maximum_mass_balance_residual"] < 1e-8
    assert fastcc["healthy_phh_context_extracted"] is False
    assert fastcc["biological_flux_authority"] is False
    generic_fba = reconstruction["generic_native_objective_audit"]
    assert generic_fba["objective_id"] == "obj"
    assert generic_fba["objective_reaction_id"] == "MAR13082"
    assert generic_fba["objective_is_healthy_phh_measurement"] is False
    assert generic_fba["status"] == "optimal"
    assert generic_fba["objective_value"] == 124.86814837744569
    assert generic_fba["active_reaction_count_at_1e_minus_9"] == 2566
    assert generic_fba["maximum_mass_balance_residual"] < 1e-8
    assert generic_fba["biological_flux_authority"] is False
    proteome_gpr = reconstruction["seven_donor_proteome_gpr_audit"]
    assert proteome_gpr["donor_count"] == 7
    assert proteome_gpr["not_healthy_volunteers"] is True
    assert proteome_gpr["flux_consistent_core_candidate_count"] == 4555
    fastcore_trial = reconstruction["seven_donor_fastcore_trial"]
    assert fastcore_trial["source_fastcore_selected_reaction_count"] == 7320
    assert fastcore_trial["source_fastcore_output_blocked_reaction_count"] == 408
    assert fastcore_trial["closure_selected_reaction_count"] == 11639
    assert fastcore_trial["context_model_accepted"] is False
    donor_stability = reconstruction["seven_donor_gpr_stability_audit"]
    assert donor_stability["zero_donor_support_reaction_count"] == 1801
    assert donor_stability["six_donor_support_reaction_count"] == 150
    assert donor_stability["largest_leave_one_out_core_expansion_count"] == 62
    scaling = reconstruction["fastcore_scaling_comparison"]
    assert scaling["fixed_output_blocked_reaction_count"] == 408
    assert scaling["adaptive_selected_reaction_count"] == 7415
    assert scaling["adaptive_output_blocked_reaction_count"] == 17
    assert scaling["adaptive_fixed_fallback_count"] == 1
    assert scaling["context_model_accepted"] is False
    diagnostics = reconstruction["fastcore_blocker_diagnostics"]
    assert diagnostics["diagnosed_blocker_count"] == 17
    assert diagnostics["full_network_active_blocker_count"] == 17
    assert diagnostics["candidate_blocked_reaction_count"] == 17
    assert diagnostics["minimum_reaction_support_proven"] is False
    repair = reconstruction["fastcore_support_repair"]
    assert repair["direction_milp_solve_count"] == 34
    assert repair["added_reaction_union_count"] == 65
    assert repair["repaired_candidate_reaction_count"] == 7480
    assert repair["strict_fastcc_blocked_reaction_count"] == 0
    assert repair["added_reaction_without_gpr_count"] == 8
    assert repair["added_reaction_zero_donor_gpr_count"] == 57
    assert repair["union_strictly_flux_consistent"] is True
    assert repair["reaction_activity_in_phh_established"] is False
    assert repair["context_model_accepted"] is False
    assert repair["fba_execution_allowed"] is False
    shared = reconstruction["fastcore_shared_support"]
    assert shared["input_candidate_union_count"] == 65
    assert shared["minimum_shared_added_reaction_count"] == 59
    assert shared["removed_from_per_target_union_count"] == 6
    assert shared["repaired_candidate_reaction_count"] == 7474
    assert shared["strict_fastcc_blocked_reaction_count"] == 0
    assert shared["selected_reaction_without_gpr_count"] == 4
    assert shared["selected_reaction_zero_donor_gpr_count"] == 55
    assert (
        shared["minimum_cardinality_within_65_reaction_union_proven"]
        is True
    )
    assert shared["reaction_activity_in_phh_established"] is False
    optimality = reconstruction["fastcore_support_optimality"]
    assert optimality["minimum_support_set_count"] == 2
    assert optimality["minimum_support_identity_enumeration_complete"] is True
    assert optimality[
        "reactions_present_in_every_minimum_support_count"
    ] == 58
    assert optimality["optional_reaction_count"] == 2
    assert optimality["optional_reaction_ids_in_input_order"] == [
        "MAR02308",
        "MAR10035",
    ]
    assert optimality["terminal_infeasibility_proven"] is True
    assert optimality["reaction_activity_in_phh_established"] is False
    global_optimality = reconstruction[
        "fastcore_global_support_optimality"
    ]
    assert global_optimality["global_candidate_reaction_count"] == 4226
    assert global_optimality["full_target_count"] == 17
    assert global_optimality["lower_bound_target_count"] == 2
    assert global_optimality[
        "lower_bound_target_ids_in_input_order"
    ] == ["MAR00468", "MAR00612"]
    assert global_optimality[
        "lower_bound_exact_minimum_added_reaction_count"
    ] == 59
    assert global_optimality[
        "upper_bound_feasible_added_reaction_count"
    ] == 59
    assert global_optimality["bounds_match"] is True
    assert global_optimality["global_minimum_cardinality_proven"] is True
    assert (
        global_optimality["global_minimum_identity_sets_enumerated"]
        is False
    )
    assert global_optimality["global_minimum_support_set_unique"] is None
    assert (
        global_optimality[
            "global_minimum_over_all_omitted_reactions_guaranteed"
        ]
        is True
    )
    assert global_optimality["reaction_activity_in_phh_established"] is False
    assert global_optimality["context_model_accepted"] is False
    assert global_optimality["fba_execution_allowed"] is False
    global_counterexample = reconstruction[
        "fastcore_global_support_counterexample"
    ]
    assert global_counterexample["global_candidate_reaction_count"] == 4226
    assert global_counterexample["global_minimum_cardinality"] == 59
    assert (
        global_counterexample[
            "known_distinct_global_minimum_support_set_count_lower_bound"
        ]
        == 3
    )
    assert global_counterexample["presolve_infeasibility_disagreed"] is True
    assert global_counterexample["solver_attempt_count"] == 2
    assert global_counterexample["accepted_solve_used_presolve"] is False
    assert global_counterexample[
        "counterexample_only_reaction_ids_in_input_order"
    ] == ["MAR00494"]
    assert global_counterexample[
        "outside_scoped_pool_reaction_ids_in_input_order"
    ] == ["MAR00494"]
    assert global_counterexample["all_target_lp_certificate_count"] == 17
    assert global_counterexample[
        "strict_fastcc_blocked_reaction_count"
    ] == 0
    assert (
        global_counterexample[
            "global_minimum_identity_enumeration_complete"
        ]
        is False
    )
    assert global_counterexample["global_minimum_support_set_unique"] is False
    assert global_counterexample[
        "additional_global_minimum_search_required"
    ] is True
    assert global_counterexample["reaction_activity_in_phh_established"] is False
    fixed_core_completion = reconstruction[
        "fastcore_fixed_core_completion_enumeration"
    ]
    assert fixed_core_completion["fixed_common_reaction_count"] == 58
    assert fixed_core_completion["conditioned_retained_reaction_count"] == 7473
    assert fixed_core_completion["remaining_candidate_reaction_count"] == 4168
    assert fixed_core_completion["known_singleton_completion_count"] == 3
    assert fixed_core_completion[
        "known_singleton_completion_ids_in_model_order"
    ] == ["MAR00494", "MAR02308", "MAR10035"]
    assert fixed_core_completion["terminal_infeasibility_proven"] is True
    assert fixed_core_completion["terminal_solver_attempt_count"] == 2
    assert fixed_core_completion[
        "terminal_infeasibility_confirmed_without_presolve"
    ] is True
    assert fixed_core_completion[
        "exact_singleton_completion_count_given_fixed_core"
    ] == 3
    assert fixed_core_completion[
        "fixed_core_singleton_completion_enumeration_complete"
    ] is True
    assert fixed_core_completion[
        "fourth_singleton_completion_with_same_fixed_core_exists"
    ] is False
    assert fixed_core_completion[
        "global_minimum_identity_enumeration_complete"
    ] is False
    assert fixed_core_completion[
        "multi_replacement_global_optima_excluded"
    ] is False
    assert fixed_core_completion[
        "reaction_activity_in_phh_established"
    ] is False
    global_identity = reconstruction[
        "fastcore_global_support_identity_completeness"
    ]
    assert global_identity["global_candidate_reaction_count"] == 4226
    assert global_identity["global_minimum_added_reaction_count"] == 59
    assert global_identity["global_minimum_support_set_count"] == 3
    assert global_identity[
        "global_minimum_support_identity_enumeration_complete"
    ] is True
    assert global_identity["global_minimum_support_set_unique"] is False
    assert global_identity[
        "global_universal_minimum_support_reaction_count"
    ] == 58
    assert global_identity[
        "global_optional_minimum_support_reaction_ids_in_model_order"
    ] == ["MAR00494", "MAR02308", "MAR10035"]
    assert global_identity[
        "every_global_minimum_contains_exactly_one_optional_identity"
    ] is True
    assert global_identity["core_breaking_global_minimum_exists"] is False
    assert global_identity["multi_replacement_global_optima_excluded"] is True
    assert global_identity[
        "additional_global_minimum_identity_search_required"
    ] is False
    assert global_identity[
        "terminal_infeasibility_confirmed_without_presolve"
    ] is True
    assert global_identity[
        "structural_essentiality_at_larger_support_sizes_established"
    ] is False
    assert global_identity["reaction_activity_in_phh_established"] is False
    evidence = reconstruction["reaction_evidence_manifest"]
    assert evidence["manifest_reaction_count"] == 4895
    assert evidence["adaptive_fastcore_noncore_reaction_count"] == 2860
    assert evidence["adaptive_noncore_without_gpr_count"] == 2177
    assert evidence["automatic_bound_change_allowed"] is False
    assert snapshot["optimization_problem"]["objective"] is None
    assert snapshot["optimization_problem"]["boundary_fluxes"] is None
    numerics = snapshot["generic_constraint_numerics"]
    assert numerics["backend"] == "scipy.optimize.linprog"
    assert numerics["backend_version"] == "1.17.1"
    assert numerics["analytic_fixture_pass_count"] == 5
    assert numerics["human_gem_loaded"] is False
    assert numerics["biological_flux_authority"] is False
    dynamic_numerics = snapshot["generic_dynamic_fba_numerics"]
    assert dynamic_numerics["summary"][
        "registered_dynamic_fba_update_law_count"
    ] == 1
    assert dynamic_numerics["summary"]["analytic_fixture_pass_count"] == 6
    assert dynamic_numerics["generic_dynamic_update_kernel_ready"] is True
    assert dynamic_numerics["automatic_unit_conversion"] is False
    assert dynamic_numerics["biological_flux_authority"] is False
    assert dynamic_numerics["runtime_state_coupling_allowed"] is False
    context_kernel = snapshot["context_extraction_kernel"]
    assert context_kernel["algorithm"] == "FASTCORE"
    assert context_kernel["synthetic_fixture_pass_count"] == 1
    assert context_kernel["epsilon_has_runtime_default"] is False
    assert context_kernel["human_gem_context_extraction_executed"] is False
    assert context_kernel["biological_flux_authority"] is False
    bundle = snapshot["phh_execution_bundle_intake"]
    assert bundle["required_artifact_count"] == 10
    assert bundle["delivered_bundle_count"] == 0
    assert bundle["structurally_complete_bundle_count"] == 0
    assert bundle["runtime_flux_coupling_allowed"] is False
    assert not any(snapshot["gates"].values())


def test_exact_release_pin_removed_only_the_artifact_identity_blocker() -> None:
    snapshot = metabolic_constraint_shell_snapshot()
    blockers = snapshot["blockers"]
    assert not any("release and checksum are not pinned" in item for item in blockers)
    assert any("context specificity was not established" in item for item in blockers)
    assert any("raw output left 17 reactions blocked" in item for item in blockers)
    assert any(
        "global minimum support identity space is complete" in item
        and "sufficient PHH activity evidence is absent" in item
        for item in blockers
    )
    assert any("independent flux validation" in item for item in blockers)
    assert not any("have not been audited" in item for item in blockers)
    assert any("structural audit exceptions" in item for item in blockers)


def test_default_constraint_shell_cache_returns_an_isolated_copy() -> None:
    first = metabolic_constraint_shell_snapshot()
    first["candidate_reconstruction"]["model_version"] = "mutated"
    first["gates"]["fba_execution_allowed"] = True

    second = metabolic_constraint_shell_snapshot()

    assert first is not second
    assert second["candidate_reconstruction"]["model_version"] == "2.0.0"
    assert second["gates"]["fba_execution_allowed"] is False
