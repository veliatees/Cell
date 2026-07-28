"""Fail-closed contract for a genome-scale hepatocyte constraint shell."""

from __future__ import annotations

import json
from pathlib import Path

from cell_engine.core.provenance import SourceReference
from cell_engine.quantitative.fastcore_context import (
    fastcore_context_snapshot,
    validate_fastcore_context_snapshot,
)
from cell_engine.quantitative.constraint_numerics import (
    constraint_numerics_snapshot,
    validate_constraint_numerics_snapshot,
)
from cell_engine.quantitative.human_gem_structural_audit import (
    load_committed_human_gem_audit,
)
from cell_engine.quantitative.human_gem_fbc_loader import (
    load_committed_fbc_loader_audit,
)
from cell_engine.quantitative.human_gem_flux_consistency import (
    load_committed_human_gem_fastcc_audit,
)
from cell_engine.quantitative.human_gem_generic_fba import (
    load_committed_human_gem_generic_fba_audit,
)
from cell_engine.quantitative.human_gem_phh_fastcore_context import (
    load_committed_human_gem_phh_fastcore_context_audit,
)
from cell_engine.quantitative.human_gem_phh_fastcore_scaling import (
    load_committed_human_gem_phh_fastcore_scaling_comparison,
)
from cell_engine.quantitative.human_gem_phh_fastcore_blocker_diagnostics import (
    load_committed_human_gem_phh_fastcore_blocker_diagnostics,
)
from cell_engine.quantitative.human_gem_phh_fastcore_support_repair import (
    load_committed_human_gem_phh_fastcore_support_repair,
)
from cell_engine.quantitative.human_gem_phh_fastcore_shared_support import (
    load_committed_human_gem_phh_fastcore_shared_support,
)
from cell_engine.quantitative.human_gem_phh_fastcore_global_support_optimality import (
    load_committed_human_gem_phh_fastcore_global_support_optimality,
)
from cell_engine.quantitative.human_gem_phh_fastcore_support_optimality import (
    load_committed_human_gem_phh_fastcore_support_optimality,
)
from cell_engine.quantitative.human_gem_phh_donor_stability import (
    load_committed_human_gem_phh_donor_stability_audit,
)
from cell_engine.quantitative.human_gem_phh_proteome_context import (
    load_committed_human_gem_phh_proteome_gpr_audit,
)
from cell_engine.quantitative.human_gem_phh_reaction_evidence_manifest import (
    load_committed_human_gem_phh_reaction_evidence_manifest,
)
from cell_engine.quantitative.phh_metabolic_execution_bundle import (
    phh_metabolic_execution_bundle_intake_snapshot,
    validate_phh_metabolic_execution_bundle_intake_snapshot,
)


DATE_VERIFIED = "2026-07-26"
VERSION = "metabolic_constraint_shell_v11"
ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = ROOT / "data/published_models/human_gem_v2.0.0.manifest.json"

METABOLIC_CONSTRAINT_SOURCES: dict[str, SourceReference] = {
    "human1_metabolic_atlas": SourceReference(
        id="human1_metabolic_atlas",
        title="An atlas of human metabolism",
        url="https://doi.org/10.1126/scisignal.aaz1482",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Genome-scale stoichiometric scaffold. FBA/FVA outcomes depend on model version, "
            "context extraction, boundary constraints and objective; they are not measured fluxes."
        ),
    ),
    "human_gem_repository": SourceReference(
        id="human_gem_repository",
        title="Human-GEM version-controlled model repository",
        url="https://github.com/SysBioChalmers/Human-GEM",
        source_type="database",
        date_verified=DATE_VERIFIED,
        notes=(
            "Official release repository for the pinned Human-GEM v2.0.0 candidate artifact. "
            "A generic human reconstruction is not a healthy-PHH context model."
        ),
    ),
    "fastcore": SourceReference(
        id="fastcore",
        title="Fast Reconstruction of Compact Context-Specific Metabolic Network Models",
        url="https://doi.org/10.1371/journal.pcbi.1003424",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Defines FASTCC flux-consistency classification and the FASTCORE "
            "LP-3/LP-7/LP-10 extraction method. FASTCC has been applied to the "
            "pinned generic reconstruction. A conservative seven-donor total-"
            "proteome core was trialed with both official fixed and adaptive "
            "LP-10 scaling. Adaptive scaling reduced, but did not eliminate, "
            "strict output inconsistency."
        ),
    ),
    "gapfill": SourceReference(
        id="gapfill",
        title="Optimization based automated curation of metabolic reconstructions",
        url="https://doi.org/10.1186/1471-2105-8-212",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Primary source for a mixed-integer minimum-reaction gap-filling "
            "formulation. The project restricts candidates to the pinned "
            "generic Human-GEM network and treats output as structural only."
        ),
    ),
    "fast_gap_filling": SourceReference(
        id="fast_gap_filling",
        title="Efficiently gap-filling reaction networks",
        url="https://doi.org/10.1186/1471-2105-15-225",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Supports minimum-reaction structural repair and explicitly does "
            "not turn an added reaction into evidence of biological activity."
        ),
    ),
}


def _load_manifest() -> dict[str, object]:
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "cell.published-model-manifest.v1":
        raise ValueError("unsupported Human-GEM artifact manifest")
    return payload


def metabolic_constraint_shell_snapshot() -> dict[str, object]:
    """Expose every input required before FBA/FVA can influence the cell state."""

    manifest = _load_manifest()
    audit = load_committed_human_gem_audit()
    loader_audit = load_committed_fbc_loader_audit()
    fastcc_audit = load_committed_human_gem_fastcc_audit()
    generic_fba_audit = load_committed_human_gem_generic_fba_audit()
    proteome_gpr_audit = (
        load_committed_human_gem_phh_proteome_gpr_audit()
    )
    fastcore_trial_audit = (
        load_committed_human_gem_phh_fastcore_context_audit()
    )
    donor_stability_audit = (
        load_committed_human_gem_phh_donor_stability_audit()
    )
    scaling_audit = (
        load_committed_human_gem_phh_fastcore_scaling_comparison()
    )
    evidence_manifest = (
        load_committed_human_gem_phh_reaction_evidence_manifest()
    )
    blocker_diagnostics = (
        load_committed_human_gem_phh_fastcore_blocker_diagnostics()
    )
    support_repair = (
        load_committed_human_gem_phh_fastcore_support_repair()
    )
    shared_support = (
        load_committed_human_gem_phh_fastcore_shared_support()
    )
    support_optimality = (
        load_committed_human_gem_phh_fastcore_support_optimality()
    )
    global_support_optimality = (
        load_committed_human_gem_phh_fastcore_global_support_optimality()
    )
    scope = manifest["scientific_scope"]
    verification = manifest["verification"]
    counts = manifest["structural_counts_verified_from_sbml"]
    numerics = constraint_numerics_snapshot()
    validate_constraint_numerics_snapshot(numerics)
    context_kernel = fastcore_context_snapshot()
    validate_fastcore_context_snapshot(context_kernel)
    execution_bundle = phh_metabolic_execution_bundle_intake_snapshot()
    validate_phh_metabolic_execution_bundle_intake_snapshot(execution_bundle)
    if not all(isinstance(item, dict) for item in (scope, verification, counts)):
        raise ValueError("Human-GEM manifest sections are malformed")

    return {
        "version": VERSION,
        "status": (
            "generic_human_gem_loaded_classified_native_objective_solved_"
            "seven_donor_stability_FASTCORE_scaling_and_source_limited_"
            "support_repair_minimized_optima_enumerated_"
            "reaction_evidence_pending_"
            "PHH_execution_blocked"
        ),
        "role": (
            "Genome-scale stoichiometric feasibility shell around validated dynamic cores. "
            "It may constrain boundary-consistent flux space but cannot supply a time trajectory."
        ),
        "candidate_reconstruction": {
            "model_family": "Human-GEM",
            "model_name": manifest["model_name"],
            "model_version": manifest["model_version"],
            "release_tag": manifest["release_tag"],
            "release_commit": manifest["release_commit"],
            "release_date": manifest["release_date"],
            "artifact_url": manifest["artifact_url"],
            "artifact_sha256": manifest["artifact_sha256"],
            "artifact_size_bytes": manifest["artifact_size_bytes"],
            "artifact_format": manifest["artifact_format"],
            "manifest_path": str(MANIFEST_PATH.relative_to(ROOT)),
            "expected_local_cache_path": manifest["expected_local_cache_path"],
            "sbml_path": None,
            "artifact_vendored_in_repository": verification["artifact_vendored_in_repository"],
            "model_loaded_by_runtime": verification["model_loaded_by_runtime"],
            "model_loader_verified_against_pinned_artifact": True,
            "fbc_loader_audit_report": (
                "data/published_models/human_gem_v2.0.0.fbc_loader_audit.json"
            ),
            "license": manifest["license"],
            "license_audited": True,
            "structural_counts_verified_from_sbml": counts,
            "structural_audit_report": verification["structural_audit_report"],
            "mass_charge_balance_audited_in_project": verification["mass_charge_audit_completed"],
            "structural_audit": {
                "active_objective_id": audit["sbml"]["active_objective_id"],
                "one_sided_reaction_count": audit["structure"]["one_sided_reaction_count"],
                "two_sided_reaction_count": audit["structure"]["two_sided_reaction_count"],
                "chemically_parseable_formula_count": audit["species_chemistry"]["chemically_parseable_formula_count"],
                "elementally_assessable_reaction_count": audit["elemental_balance"]["assessable_reaction_count"],
                "elementally_balanced_reaction_count": audit["elemental_balance"]["balanced_reaction_count"],
                "elementally_imbalanced_reaction_count": audit["elemental_balance"]["imbalanced_reaction_count"],
                "jointly_assessable_reaction_count": audit["joint_balance"]["assessable_reaction_count"],
                "jointly_balanced_reaction_count": audit["joint_balance"]["balanced_reaction_count"],
                "jointly_imbalanced_reaction_count": audit["joint_balance"]["imbalanced_reaction_count"],
                "jointly_unassessable_reaction_count": audit["joint_balance"]["unassessable_reaction_count"],
                "one_sided_reactions_excluded_from_internal_balance_claim": audit["scientific_boundary"]["one_sided_reactions_excluded_from_internal_balance_claim"],
            },
            "sparse_fbc_loader_audit": {
                "loader_version": loader_audit["loader_version"],
                "artifact_identity_verified_before_parse": loader_audit[
                    "integrity"
                ]["artifact_identity_verified_before_parse"],
                "stoichiometric_shape": loader_audit["loaded_structure"][
                    "stoichiometric_shape"
                ],
                "stoichiometric_nonzero_count": loader_audit[
                    "loaded_structure"
                ]["stoichiometric_nonzero_count"],
                "reversible_reaction_count": loader_audit["loaded_structure"][
                    "reversible_reaction_count"
                ],
                "gene_associated_reaction_count": loader_audit[
                    "loaded_structure"
                ]["gene_associated_reaction_count"],
                "gene_product_label_count": loader_audit[
                    "loaded_structure"
                ]["gene_product_label_count"],
                "unique_gene_product_label_count": loader_audit[
                    "loaded_structure"
                ]["unique_gene_product_label_count"],
                "parameter_count": loader_audit["loaded_structure"][
                    "parameter_count"
                ],
                "objective_count": loader_audit["loaded_structure"][
                    "objective_count"
                ],
                "active_objective_id": loader_audit["sbml_fbc"][
                    "active_objective_id"
                ],
                "generic_human_reconstruction_loaded": loader_audit[
                    "scientific_boundary"
                ]["generic_human_reconstruction_loaded"],
                "healthy_phh_context_extracted": loader_audit[
                    "scientific_boundary"
                ]["healthy_phh_context_extracted"],
                "fba_execution_allowed": loader_audit["scientific_boundary"][
                    "fba_execution_allowed"
                ],
            },
            "generic_flux_consistency_audit": {
                "audit_report": (
                    "data/published_models/"
                    "human_gem_v2.0.0.fastcc_audit.json"
                ),
                "algorithm": fastcc_audit["method"]["algorithm"],
                "epsilon": fastcc_audit["method"]["epsilon"],
                "epsilon_is_biological_parameter": fastcc_audit["method"][
                    "epsilon_is_biological_parameter"
                ],
                "solver_backend_version": fastcc_audit["method"][
                    "solver_backend_version"
                ],
                "solver_method": fastcc_audit["method"]["solver_method"],
                "consistent_reaction_count": fastcc_audit["classification"][
                    "consistent_reaction_count"
                ],
                "blocked_reaction_count": fastcc_audit["classification"][
                    "blocked_reaction_count"
                ],
                "lp7_solve_count": fastcc_audit["fastcc_reduced_network"][
                    "lp7_solve_count"
                ],
                "lp3_solve_count": fastcc_audit["fastcc_reduced_network"][
                    "lp3_solve_count"
                ],
                "maximum_mass_balance_residual": fastcc_audit[
                    "fastcc_reduced_network"
                ]["maximum_mass_balance_residual"],
                "complete_at_declared_epsilon": fastcc_audit[
                    "classification"
                ]["complete_at_declared_epsilon"],
                "healthy_phh_context_extracted": fastcc_audit[
                    "scientific_boundary"
                ]["healthy_phh_context_extracted"],
                "biological_flux_authority": fastcc_audit[
                    "scientific_boundary"
                ]["biological_flux_authority"],
            },
            "generic_native_objective_audit": {
                "audit_report": (
                    "data/published_models/"
                    "human_gem_v2.0.0.generic_fba_audit.json"
                ),
                "objective_id": generic_fba_audit["native_fbc_objective"][
                    "objective_id"
                ],
                "objective_type": generic_fba_audit[
                    "native_fbc_objective"
                ]["objective_type"],
                "objective_reaction_id": generic_fba_audit[
                    "native_fbc_objective"
                ]["terms"][0]["reaction_id"],
                "objective_reaction_name": generic_fba_audit[
                    "native_fbc_objective"
                ]["terms"][0]["reaction_name"],
                "objective_is_healthy_phh_measurement": generic_fba_audit[
                    "native_fbc_objective"
                ]["objective_is_healthy_phh_measurement"],
                "status": generic_fba_audit["generic_solve"]["status"],
                "objective_value": generic_fba_audit["generic_solve"][
                    "objective_value"
                ],
                "active_reaction_count_at_1e_minus_9": generic_fba_audit[
                    "generic_solve"
                ]["active_reaction_count_at_1e_minus_9"],
                "maximum_mass_balance_residual": generic_fba_audit[
                    "generic_solve"
                ]["maximum_mass_balance_residual"],
                "optimum_uniqueness_established": generic_fba_audit[
                    "generic_solve"
                ]["optimum_uniqueness_established"],
                "healthy_phh_context_extracted": generic_fba_audit[
                    "scientific_boundary"
                ]["healthy_phh_context_extracted"],
                "biological_flux_authority": generic_fba_audit[
                    "scientific_boundary"
                ]["biological_flux_authority"],
            },
            "seven_donor_proteome_gpr_audit": {
                "audit_report": (
                    "data/phh_baseline/derived/"
                    "human_gem_v2.0.0.seven_donor_proteome_gpr_audit.json"
                ),
                "donor_count": proteome_gpr_audit[
                    "phh_proteome_artifact"
                ]["donor_count"],
                "not_healthy_volunteers": proteome_gpr_audit[
                    "phh_proteome_artifact"
                ]["not_healthy_volunteers"],
                "single_gene_group_count": proteome_gpr_audit[
                    "protein_group_mapping"
                ]["single_gene_group_count"],
                "non_single_gene_excluded_group_count": proteome_gpr_audit[
                    "protein_group_mapping"
                ]["non_single_gene_excluded_group_count"],
                "reaction_support_intersection_count": proteome_gpr_audit[
                    "all_donor_support"
                ]["reaction_support_intersection_count"],
                "generic_fastcc_blocked_conflict_count": proteome_gpr_audit[
                    "all_donor_support"
                ]["generic_fastcc_blocked_conflict_count"],
                "flux_consistent_core_candidate_count": proteome_gpr_audit[
                    "all_donor_support"
                ]["flux_consistent_core_candidate_count"],
                "active_enzyme_abundance_inferred": proteome_gpr_audit[
                    "scientific_boundary"
                ]["protein_detection_interpreted_as_active_enzyme"],
                "flux_magnitude_inferred": proteome_gpr_audit[
                    "scientific_boundary"
                ]["flux_magnitude_inferred"],
            },
            "seven_donor_fastcore_trial": {
                "audit_report": (
                    "data/phh_baseline/derived/"
                    "human_gem_v2.0.0.seven_donor_proteome_"
                    "fastcore_context.json"
                ),
                "core_reaction_count": fastcore_trial_audit["extraction"][
                    "core_reaction_count"
                ],
                "source_fastcore_selected_reaction_count": (
                    fastcore_trial_audit["extraction"][
                        "source_fastcore_selected_reaction_count"
                    ]
                ),
                "source_fastcore_output_blocked_reaction_count": (
                    fastcore_trial_audit["extraction"][
                        "source_fastcore_output_blocked_reaction_count"
                    ]
                ),
                "closure_selected_reaction_count": fastcore_trial_audit[
                    "extraction"
                ]["selected_reaction_count"],
                "closure_omitted_reaction_count": fastcore_trial_audit[
                    "extraction"
                ]["omitted_reaction_count"],
                "source_FASTCORE_output_flux_consistent": (
                    fastcore_trial_audit["scientific_boundary"][
                        "source_FASTCORE_output_flux_consistent"
                    ]
                ),
                "context_specificity_established": fastcore_trial_audit[
                    "scientific_boundary"
                ]["context_specificity_established"],
                "context_model_accepted": fastcore_trial_audit[
                    "scientific_boundary"
                ]["context_model_accepted"],
            },
            "seven_donor_gpr_stability_audit": {
                "audit_report": (
                    "data/phh_baseline/derived/"
                    "human_gem_v2.0.0.seven_donor_gpr_stability_audit.json"
                ),
                "gpr_reaction_count": donor_stability_audit["summary"][
                    "gpr_reaction_count"
                ],
                "zero_donor_support_reaction_count": donor_stability_audit[
                    "support_frequency_by_donor_count"
                ]["0"]["gpr_reaction_count"],
                "six_donor_support_reaction_count": donor_stability_audit[
                    "support_frequency_by_donor_count"
                ]["6"]["gpr_reaction_count"],
                "seven_donor_support_reaction_count": donor_stability_audit[
                    "support_frequency_by_donor_count"
                ]["7"]["gpr_reaction_count"],
                "seven_donor_flux_consistent_core_count": (
                    donor_stability_audit["summary"][
                        "seven_donor_flux_consistent_core_count"
                    ]
                ),
                "largest_leave_one_out_core_expansion_count": max(
                    item["added_vs_seven_donor_core_count"]
                    for item in donor_stability_audit[
                        "leave_one_donor_out"
                    ]
                ),
                "missing_detection_interpreted_as_inactivity": (
                    donor_stability_audit["scientific_boundary"][
                        "missing_detection_interpreted_as_inactivity"
                    ]
                ),
            },
            "fastcore_scaling_comparison": {
                "audit_report": (
                    "data/phh_baseline/derived/"
                    "human_gem_v2.0.0.seven_donor_"
                    "fastcore_scaling_comparison.json"
                ),
                "fixed_selected_reaction_count": scaling_audit[
                    "fixed_scaling_trial"
                ]["selected_reaction_count"],
                "fixed_output_blocked_reaction_count": scaling_audit[
                    "fixed_scaling_trial"
                ]["output_blocked_reaction_count"],
                "adaptive_selected_reaction_count": scaling_audit[
                    "adaptive_scaling_trial"
                ]["selected_reaction_count"],
                "adaptive_output_blocked_reaction_count": scaling_audit[
                    "adaptive_scaling_trial"
                ]["output_blocked_reaction_count"],
                "adaptive_lp10_solve_count": scaling_audit[
                    "adaptive_scaling_trial"
                ]["lp10_adaptive_solve_count"],
                "adaptive_fixed_fallback_count": scaling_audit[
                    "adaptive_scaling_trial"
                ]["lp10_fixed_fallback_count"],
                "selected_jaccard": scaling_audit["comparison"][
                    "selected_jaccard"
                ],
                "adaptive_output_flux_consistent": scaling_audit[
                    "adaptive_scaling_trial"
                ]["output_flux_consistent"],
                "context_model_accepted": scaling_audit[
                    "scientific_boundary"
                ]["context_model_accepted"],
            },
            "fastcore_blocker_diagnostics": {
                "audit_report": (
                    "data/phh_baseline/derived/"
                    "human_gem_v2.0.0.seven_donor_"
                    "fastcore_blocker_diagnostics.json"
                ),
                "diagnosed_blocker_count": blocker_diagnostics[
                    "summary"
                ]["diagnosed_blocker_count"],
                "full_network_active_blocker_count": blocker_diagnostics[
                    "summary"
                ]["full_network_active_blocker_count"],
                "candidate_blocked_reaction_count": blocker_diagnostics[
                    "summary"
                ]["candidate_blocked_reaction_count"],
                "full_witness_omitted_reaction_union_count": (
                    blocker_diagnostics["summary"][
                        "full_witness_omitted_reaction_union_count"
                    ]
                ),
                "omitted_one_hop_reaction_union_count": (
                    blocker_diagnostics["summary"][
                        "omitted_one_hop_reaction_union_count"
                    ]
                ),
                "minimum_reaction_support_proven": (
                    blocker_diagnostics["scientific_boundary"][
                        "minimum_reaction_support_proven"
                    ]
                ),
                "context_model_accepted": blocker_diagnostics[
                    "scientific_boundary"
                ]["context_model_accepted"],
            },
            "fastcore_support_repair": {
                "audit_report": (
                    "data/phh_baseline/derived/"
                    "human_gem_v2.0.0.seven_donor_"
                    "fastcore_support_repair.json"
                ),
                "target_blocker_count": support_repair["summary"][
                    "target_blocker_count"
                ],
                "direction_milp_solve_count": support_repair["summary"][
                    "direction_milp_solve_count"
                ],
                "minimum_per_target_added_reaction_count": (
                    support_repair["summary"][
                        "minimum_per_target_added_reaction_count"
                    ]
                ),
                "maximum_per_target_added_reaction_count": (
                    support_repair["summary"][
                        "maximum_per_target_added_reaction_count"
                    ]
                ),
                "added_reaction_union_count": support_repair["summary"][
                    "added_reaction_union_count"
                ],
                "repaired_candidate_reaction_count": support_repair[
                    "summary"
                ]["repaired_candidate_reaction_count"],
                "strict_fastcc_blocked_reaction_count": support_repair[
                    "summary"
                ]["strict_fastcc_blocked_reaction_count"],
                "added_reaction_without_gpr_count": support_repair[
                    "summary"
                ]["added_reaction_without_gpr_count"],
                "added_reaction_zero_donor_gpr_count": support_repair[
                    "summary"
                ]["added_reaction_zero_donor_gpr_count"],
                "per_target_minimum_cardinality_proven": support_repair[
                    "scientific_boundary"
                ]["per_target_minimum_cardinality_proven"],
                "union_strictly_flux_consistent": support_repair[
                    "scientific_boundary"
                ]["union_strictly_flux_consistent"],
                "union_global_minimum_guaranteed": support_repair[
                    "scientific_boundary"
                ]["union_global_minimum_guaranteed"],
                "reaction_activity_in_phh_established": support_repair[
                    "scientific_boundary"
                ]["reaction_activity_in_phh_established"],
                "context_model_accepted": support_repair[
                    "scientific_boundary"
                ]["context_model_accepted"],
                "fba_execution_allowed": support_repair[
                    "scientific_boundary"
                ]["fba_execution_allowed"],
            },
            "fastcore_shared_support": {
                "audit_report": (
                    "data/phh_baseline/derived/"
                    "human_gem_v2.0.0.seven_donor_"
                    "fastcore_shared_support.json"
                ),
                "input_candidate_union_count": shared_support["summary"][
                    "input_candidate_union_count"
                ],
                "target_blocker_count": shared_support["summary"][
                    "target_blocker_count"
                ],
                "minimum_shared_added_reaction_count": shared_support[
                    "summary"
                ]["minimum_shared_added_reaction_count"],
                "removed_from_per_target_union_count": shared_support[
                    "summary"
                ]["removed_from_per_target_union_count"],
                "repaired_candidate_reaction_count": shared_support[
                    "summary"
                ]["repaired_candidate_reaction_count"],
                "strict_fastcc_blocked_reaction_count": shared_support[
                    "summary"
                ]["strict_fastcc_blocked_reaction_count"],
                "selected_reaction_without_gpr_count": shared_support[
                    "summary"
                ]["selected_reaction_without_gpr_count"],
                "selected_reaction_zero_donor_gpr_count": shared_support[
                    "summary"
                ]["selected_reaction_zero_donor_gpr_count"],
                "minimum_cardinality_within_65_reaction_union_proven": (
                    shared_support["scientific_boundary"][
                        "minimum_cardinality_within_65_reaction_union_proven"
                    ]
                ),
                "selected_subset_strictly_flux_consistent": (
                    shared_support["scientific_boundary"][
                        "selected_subset_strictly_flux_consistent"
                    ]
                ),
                "global_minimum_over_all_omitted_reactions_guaranteed": (
                    shared_support["scientific_boundary"][
                        "global_minimum_over_all_omitted_reactions_guaranteed"
                    ]
                ),
                "reaction_activity_in_phh_established": shared_support[
                    "scientific_boundary"
                ]["reaction_activity_in_phh_established"],
                "context_model_accepted": shared_support[
                    "scientific_boundary"
                ]["context_model_accepted"],
                "fba_execution_allowed": shared_support[
                    "scientific_boundary"
                ]["fba_execution_allowed"],
            },
            "fastcore_support_optimality": {
                "audit_report": (
                    "data/phh_baseline/derived/"
                    "human_gem_v2.0.0.seven_donor_"
                    "fastcore_support_optimality.json"
                ),
                "minimum_support_set_count": support_optimality["summary"][
                    "minimum_support_set_count"
                ],
                "minimum_support_identity_enumeration_complete": (
                    support_optimality["summary"][
                        "minimum_support_identity_enumeration_complete"
                    ]
                ),
                "reactions_present_in_every_minimum_support_count": (
                    support_optimality["summary"][
                        "reactions_proven_present_in_every_minimum_support_count"
                    ]
                ),
                "optional_reaction_count": support_optimality["summary"][
                    "minimum_support_optional_reaction_count"
                ],
                "optional_reaction_ids_in_input_order": support_optimality[
                    "summary"
                ]["minimum_support_optional_reaction_ids_in_input_order"],
                "terminal_infeasibility_proven": support_optimality[
                    "summary"
                ]["enumeration_terminal_infeasibility_proven"],
                "all_minimum_support_identities_enumerated": (
                    support_optimality["scientific_boundary"][
                        "all_minimum_support_identities_enumerated_within_65_pool"
                    ]
                ),
                "global_minimum_over_all_omitted_reactions_guaranteed": (
                    support_optimality["scientific_boundary"][
                        "global_minimum_over_all_omitted_reactions_guaranteed"
                    ]
                ),
                "reaction_activity_in_phh_established": support_optimality[
                    "scientific_boundary"
                ]["reaction_activity_in_phh_established"],
                "context_model_accepted": support_optimality[
                    "scientific_boundary"
                ]["context_model_accepted"],
                "fba_execution_allowed": support_optimality[
                    "scientific_boundary"
                ]["fba_execution_allowed"],
            },
            "fastcore_global_support_optimality": {
                "audit_report": (
                    "data/phh_baseline/derived/"
                    "human_gem_v2.0.0.seven_donor_"
                    "fastcore_global_support_optimality.json"
                ),
                "global_candidate_reaction_count": (
                    global_support_optimality["input"][
                        "global_candidate_reaction_count"
                    ]
                ),
                "full_target_count": global_support_optimality["input"][
                    "full_target_count"
                ],
                "lower_bound_target_count": global_support_optimality[
                    "input"
                ]["lower_bound_target_count"],
                "lower_bound_target_ids_in_input_order": (
                    global_support_optimality["input"][
                        "lower_bound_target_ids_in_input_order"
                    ]
                ),
                "lower_bound_exact_minimum_added_reaction_count": (
                    global_support_optimality["lower_bound_certificate"][
                        "exact_minimum_added_reaction_count"
                    ]
                ),
                "lower_bound_target_lp_certificate_count": (
                    global_support_optimality["lower_bound_certificate"][
                        "target_lp_certificate_count"
                    ]
                ),
                "upper_bound_feasible_added_reaction_count": (
                    global_support_optimality["upper_bound_certificate"][
                        "feasible_added_reaction_count"
                    ]
                ),
                "all_target_upper_bound_lp_certificate_count": (
                    global_support_optimality["upper_bound_certificate"][
                        "all_target_lp_certificate_count"
                    ]
                ),
                "strict_fastcc_blocked_reaction_count": (
                    global_support_optimality["upper_bound_certificate"][
                        "strict_fastcc_blocked_reaction_count"
                    ]
                ),
                "bounds_match": global_support_optimality["proof"][
                    "bounds_match"
                ],
                "global_minimum_added_reaction_count": (
                    global_support_optimality["proof"][
                        "global_minimum_added_reaction_count"
                    ]
                ),
                "global_minimum_cardinality_proven": (
                    global_support_optimality["proof"][
                        "global_minimum_cardinality_proven"
                    ]
                ),
                "lower_bound_support_matches_committed_upper_support": (
                    global_support_optimality["proof"][
                        "lower_bound_support_matches_committed_upper_support"
                    ]
                ),
                "global_minimum_identity_sets_enumerated": (
                    global_support_optimality["proof"][
                        "global_minimum_identity_sets_enumerated"
                    ]
                ),
                "global_minimum_support_set_unique": (
                    global_support_optimality["proof"][
                        "global_minimum_support_set_unique"
                    ]
                ),
                "global_universal_reaction_identities_established": (
                    global_support_optimality["proof"][
                        "global_universal_reaction_identities_established"
                    ]
                ),
                "global_minimum_over_all_omitted_reactions_guaranteed": (
                    global_support_optimality["scientific_boundary"][
                        "global_minimum_over_all_omitted_reactions_guaranteed"
                    ]
                ),
                "reaction_activity_in_phh_established": (
                    global_support_optimality["scientific_boundary"][
                        "reaction_activity_in_phh_established"
                    ]
                ),
                "context_model_accepted": global_support_optimality[
                    "scientific_boundary"
                ]["context_model_accepted"],
                "fba_execution_allowed": global_support_optimality[
                    "scientific_boundary"
                ]["fba_execution_allowed"],
            },
            "reaction_evidence_manifest": {
                "manifest_path": (
                    "data/evidence_intake/"
                    "human_gem_phh_reaction_evidence_manifest.v1.json"
                ),
                "manifest_reaction_count": evidence_manifest["summary"][
                    "manifest_reaction_count"
                ],
                "adaptive_fastcore_noncore_reaction_count": (
                    evidence_manifest["summary"][
                        "adaptive_fastcore_noncore_reaction_count"
                    ]
                ),
                "adaptive_noncore_without_gpr_count": evidence_manifest[
                    "evidence_gap_groups"
                ][
                    "adaptive_fastcore_noncore_without_gpr_annotation"
                ]["reaction_count"],
                "adaptive_noncore_zero_donor_gpr_count": evidence_manifest[
                    "evidence_gap_groups"
                ][
                    "adaptive_fastcore_noncore_zero_donor_gpr_support"
                ]["reaction_count"],
                "adaptive_noncore_partial_donor_gpr_count": evidence_manifest[
                    "evidence_gap_groups"
                ][
                    "adaptive_fastcore_noncore_partial_donor_gpr_support"
                ]["reaction_count"],
                "priority_score_used": evidence_manifest["method"][
                    "priority_score_used"
                ],
                "automatic_bound_change_allowed": evidence_manifest[
                    "execution_gates"
                ]["automatic_bound_change_allowed"],
            },
        },
        "hepatocyte_context": {
            "extraction_algorithm": None,
            "donor_or_cohort": None,
            "nutritional_state": None,
            "zonation_context": None,
            "transcriptome_input": None,
            "proteome_input": None,
        },
        "generic_constraint_numerics": numerics,
        "context_extraction_kernel": context_kernel,
        "phh_execution_bundle_intake": execution_bundle,
        "optimization_problem": {
            "objective": None,
            "objective_is_biological_measurement": False,
            "boundary_fluxes": None,
            "thermodynamic_constraints": None,
            "enzyme_capacity_constraints": None,
            "solver_and_version": None,
        },
        "required_outputs": (
            "FBA optimum plus alternate-optimum audit",
            "flux variability intervals",
            "mass-balance residuals",
            "blocked-reaction and infeasibility diagnostics",
            "comparison to independent measured exchange and isotope fluxes",
        ),
        "gates": {
            "fba_execution_allowed": False,
            "fva_execution_allowed": False,
            "thermodynamic_fba_allowed": False,
            "enzyme_constrained_fba_allowed": False,
            "may_initialize_dynamic_reaction_rates": False,
            "may_drive_scientific_validation": False,
        },
        "source_ids": tuple(METABOLIC_CONSTRAINT_SOURCES),
        "blockers": (
            "the 43 MB SBML remains cache-only and must be checksum-fetched in each execution environment",
            "the seven-donor resection-PHH total-proteome core is not a healthy-volunteer or active-enzyme core",
            "adaptive official LP-10 scaling selected 7,415 reactions but its raw output left 17 reactions blocked at the declared epsilon",
            "the exact two-target lower bound over all 4,226 omitted reactions matches the feasible 17-target upper bound at 59 additions, proving global cardinality; global minimum identity sets remain unenumerated and all additions still lack sufficient PHH activity evidence",
            "strict connected-component closure retained 11,639 of 11,641 consistent reactions, so context specificity was not established",
            "2,860 adaptive non-core support reactions require reaction-level PHH evidence; 2,177 lack a GPR annotation",
            "measured exchange bounds and explicit scale conversion are absent",
            "objective function is not linked to a matched healthy-PHH measurement",
            "structural audit exceptions require reaction-level resolution before scientific optimization",
            "independent flux validation is absent",
        ),
    }


def validate_metabolic_constraint_shell(payload: dict[str, object]) -> None:
    if payload.get("version") != VERSION:
        raise ValueError("unexpected metabolic constraint shell version")
    reconstruction = payload.get("candidate_reconstruction")
    context = payload.get("hepatocyte_context")
    optimization = payload.get("optimization_problem")
    gates = payload.get("gates")
    numerics = payload.get("generic_constraint_numerics")
    context_kernel = payload.get("context_extraction_kernel")
    execution_bundle = payload.get("phh_execution_bundle_intake")
    if not all(
        isinstance(item, dict)
        for item in (
            reconstruction,
            context,
            optimization,
            gates,
            numerics,
            context_kernel,
            execution_bundle,
        )
    ):
        raise ValueError("metabolic constraint shell is malformed")
    validate_constraint_numerics_snapshot(numerics)
    validate_fastcore_context_snapshot(context_kernel)
    validate_phh_metabolic_execution_bundle_intake_snapshot(execution_bundle)
    if any(gates.values()):
        raise ValueError("metabolic constraint shell may not execute before evidence intake")
    if reconstruction.get("model_version") != "2.0.0":
        raise ValueError("unexpected Human-GEM version")
    if (
        reconstruction.get("release_tag") != "v2.0.0"
        or reconstruction.get("release_commit")
        != "635f533152dc5f7290ce04d12700eaa882273c3e"
    ):
        raise ValueError("unexpected Human-GEM release identity")
    if reconstruction.get("artifact_sha256") != "cc5a4383c6116b0c91f4db089cc640f29aec7e840249b573b74d3792c9ca4a7a":
        raise ValueError("unexpected Human-GEM artifact checksum")
    if reconstruction.get("artifact_size_bytes") != 43115559:
        raise ValueError("unexpected Human-GEM artifact size")
    if reconstruction.get("license") != "CC-BY-4.0" or reconstruction.get("license_audited") is not True:
        raise ValueError("Human-GEM license audit is incomplete")
    if reconstruction.get("model_loaded_by_runtime") is not False:
        raise ValueError("Human-GEM runtime loading changed without context review")
    if reconstruction.get("model_loader_verified_against_pinned_artifact") is not True:
        raise ValueError("Human-GEM sparse loader verification is missing")
    if reconstruction.get("mass_charge_balance_audited_in_project") is not True:
        raise ValueError("Human-GEM mass/charge audit is missing")
    audit = reconstruction.get("structural_audit")
    if not isinstance(audit, dict):
        raise ValueError("Human-GEM structural audit summary is missing")
    if audit.get("elementally_assessable_reaction_count") != 9849:
        raise ValueError("Human-GEM elemental audit count changed without review")
    if audit.get("elementally_imbalanced_reaction_count") != 17:
        raise ValueError("Human-GEM elemental imbalance count changed without review")
    if audit.get("jointly_unassessable_reaction_count") != 1422:
        raise ValueError("Human-GEM unassessable reaction count changed without review")
    if audit.get("active_objective_id") != "obj":
        raise ValueError("Human-GEM active objective identity changed")
    loader = reconstruction.get("sparse_fbc_loader_audit")
    if not isinstance(loader, dict):
        raise ValueError("Human-GEM sparse FBC loader audit is missing")
    if (
        loader.get("loader_version") != "human_gem_fbc_loader_v2"
        or loader.get("artifact_identity_verified_before_parse") is not True
        or loader.get("stoichiometric_shape") != [8461, 12931]
        or loader.get("stoichiometric_nonzero_count") != 55198
        or loader.get("reversible_reaction_count") != 5725
        or loader.get("gene_associated_reaction_count") != 7782
        or loader.get("gene_product_label_count") != 2848
        or loader.get("unique_gene_product_label_count") != 2848
        or loader.get("parameter_count") != 3
        or loader.get("objective_count") != 1
        or loader.get("active_objective_id") != "obj"
        or loader.get("generic_human_reconstruction_loaded") is not True
        or loader.get("healthy_phh_context_extracted") is not False
        or loader.get("fba_execution_allowed") is not False
    ):
        raise ValueError("Human-GEM sparse loader audit changed without review")
    fastcc = reconstruction.get("generic_flux_consistency_audit")
    if not isinstance(fastcc, dict):
        raise ValueError("Human-GEM generic FASTCC audit is missing")
    if (
        fastcc.get("algorithm")
        != "sign_definite_dead_end_prepass_plus_FASTCC"
        or fastcc.get("epsilon") != 1e-4
        or fastcc.get("epsilon_is_biological_parameter") is not False
        or fastcc.get("solver_backend_version") != "1.17.1"
        or fastcc.get("solver_method") != "highs-ipm"
        or fastcc.get("consistent_reaction_count") != 11641
        or fastcc.get("blocked_reaction_count") != 1290
        or fastcc.get("lp7_solve_count") != 6
        or fastcc.get("lp3_solve_count") != 247
        or not isinstance(
            fastcc.get("maximum_mass_balance_residual"),
            (int, float),
        )
        or fastcc["maximum_mass_balance_residual"] > 1e-8
        or fastcc.get("complete_at_declared_epsilon") is not True
        or fastcc.get("healthy_phh_context_extracted") is not False
        or fastcc.get("biological_flux_authority") is not False
    ):
        raise ValueError(
            "Human-GEM generic FASTCC audit changed without review"
        )
    proteome_gpr = reconstruction.get("seven_donor_proteome_gpr_audit")
    if not isinstance(proteome_gpr, dict):
        raise ValueError("Human-GEM PHH proteome GPR audit is missing")
    if (
        proteome_gpr.get("donor_count") != 7
        or proteome_gpr.get("not_healthy_volunteers") is not True
        or proteome_gpr.get("single_gene_group_count") != 8_110
        or proteome_gpr.get("non_single_gene_excluded_group_count") != 579
        or proteome_gpr.get("reaction_support_intersection_count") != 5_082
        or proteome_gpr.get("generic_fastcc_blocked_conflict_count") != 527
        or proteome_gpr.get("flux_consistent_core_candidate_count") != 4_555
        or proteome_gpr.get("active_enzyme_abundance_inferred") is not False
        or proteome_gpr.get("flux_magnitude_inferred") is not False
    ):
        raise ValueError(
            "Human-GEM PHH proteome GPR audit changed without review"
        )
    fastcore_trial = reconstruction.get("seven_donor_fastcore_trial")
    if not isinstance(fastcore_trial, dict):
        raise ValueError("Human-GEM PHH FASTCORE trial audit is missing")
    if (
        fastcore_trial.get("core_reaction_count") != 4_555
        or fastcore_trial.get("source_fastcore_selected_reaction_count")
        != 7_320
        or fastcore_trial.get(
            "source_fastcore_output_blocked_reaction_count"
        )
        != 408
        or fastcore_trial.get("closure_selected_reaction_count") != 11_639
        or fastcore_trial.get("closure_omitted_reaction_count") != 2
        or fastcore_trial.get("source_FASTCORE_output_flux_consistent")
        is not False
        or fastcore_trial.get("context_specificity_established") is not False
        or fastcore_trial.get("context_model_accepted") is not False
    ):
        raise ValueError(
            "Human-GEM PHH FASTCORE trial escaped its fail-closed boundary"
        )
    donor_stability = reconstruction.get(
        "seven_donor_gpr_stability_audit"
    )
    if not isinstance(donor_stability, dict) or (
        donor_stability.get("gpr_reaction_count") != 7_782
        or donor_stability.get("zero_donor_support_reaction_count")
        != 1_801
        or donor_stability.get("six_donor_support_reaction_count") != 150
        or donor_stability.get("seven_donor_support_reaction_count")
        != 5_082
        or donor_stability.get("seven_donor_flux_consistent_core_count")
        != 4_555
        or donor_stability.get(
            "largest_leave_one_out_core_expansion_count"
        )
        != 62
        or donor_stability.get(
            "missing_detection_interpreted_as_inactivity"
        )
        is not False
    ):
        raise ValueError("PHH donor GPR stability audit changed")
    scaling = reconstruction.get("fastcore_scaling_comparison")
    if not isinstance(scaling, dict) or (
        scaling.get("fixed_selected_reaction_count") != 7_320
        or scaling.get("fixed_output_blocked_reaction_count") != 408
        or scaling.get("adaptive_selected_reaction_count") != 7_415
        or scaling.get("adaptive_output_blocked_reaction_count") != 17
        or scaling.get("adaptive_lp10_solve_count") != 11
        or scaling.get("adaptive_fixed_fallback_count") != 1
        or scaling.get("adaptive_output_flux_consistent") is not False
        or scaling.get("context_model_accepted") is not False
    ):
        raise ValueError("PHH FASTCORE scaling comparison changed")
    blocker_diagnostics = reconstruction.get(
        "fastcore_blocker_diagnostics"
    )
    if not isinstance(blocker_diagnostics, dict) or (
        blocker_diagnostics.get("diagnosed_blocker_count") != 17
        or blocker_diagnostics.get("full_network_active_blocker_count")
        != 17
        or blocker_diagnostics.get("candidate_blocked_reaction_count")
        != 17
        or blocker_diagnostics.get(
            "full_witness_omitted_reaction_union_count"
        )
        != 1_169
        or blocker_diagnostics.get(
            "omitted_one_hop_reaction_union_count"
        )
        != 1_402
        or blocker_diagnostics.get("minimum_reaction_support_proven")
        is not False
        or blocker_diagnostics.get("context_model_accepted") is not False
    ):
        raise ValueError("PHH FASTCORE blocker diagnostics changed")
    support_repair = reconstruction.get("fastcore_support_repair")
    if not isinstance(support_repair, dict) or (
        support_repair.get("target_blocker_count") != 17
        or support_repair.get("direction_milp_solve_count") != 34
        or support_repair.get(
            "minimum_per_target_added_reaction_count"
        )
        != 1
        or support_repair.get(
            "maximum_per_target_added_reaction_count"
        )
        != 56
        or support_repair.get("added_reaction_union_count") != 65
        or support_repair.get("repaired_candidate_reaction_count")
        != 7_480
        or support_repair.get("strict_fastcc_blocked_reaction_count")
        != 0
        or support_repair.get("added_reaction_without_gpr_count") != 8
        or support_repair.get("added_reaction_zero_donor_gpr_count")
        != 57
        or support_repair.get("per_target_minimum_cardinality_proven")
        is not True
        or support_repair.get("union_strictly_flux_consistent")
        is not True
        or support_repair.get("union_global_minimum_guaranteed")
        is not False
        or support_repair.get("reaction_activity_in_phh_established")
        is not False
        or support_repair.get("context_model_accepted") is not False
        or support_repair.get("fba_execution_allowed") is not False
    ):
        raise ValueError("PHH FASTCORE support-repair audit changed")
    shared_support = reconstruction.get("fastcore_shared_support")
    if not isinstance(shared_support, dict) or (
        shared_support.get("input_candidate_union_count") != 65
        or shared_support.get("target_blocker_count") != 17
        or shared_support.get("minimum_shared_added_reaction_count")
        != 59
        or shared_support.get("removed_from_per_target_union_count")
        != 6
        or shared_support.get("repaired_candidate_reaction_count")
        != 7_474
        or shared_support.get("strict_fastcc_blocked_reaction_count")
        != 0
        or shared_support.get("selected_reaction_without_gpr_count")
        != 4
        or shared_support.get("selected_reaction_zero_donor_gpr_count")
        != 55
        or shared_support.get(
            "minimum_cardinality_within_65_reaction_union_proven"
        )
        is not True
        or shared_support.get(
            "selected_subset_strictly_flux_consistent"
        )
        is not True
        or shared_support.get(
            "global_minimum_over_all_omitted_reactions_guaranteed"
        )
        is not False
        or shared_support.get("reaction_activity_in_phh_established")
        is not False
        or shared_support.get("context_model_accepted") is not False
        or shared_support.get("fba_execution_allowed") is not False
    ):
        raise ValueError("PHH FASTCORE shared-support audit changed")
    support_optimality = reconstruction.get(
        "fastcore_support_optimality"
    )
    if not isinstance(support_optimality, dict) or (
        support_optimality.get("minimum_support_set_count") != 2
        or support_optimality.get(
            "minimum_support_identity_enumeration_complete"
        )
        is not True
        or support_optimality.get(
            "reactions_present_in_every_minimum_support_count"
        )
        != 58
        or support_optimality.get("optional_reaction_count") != 2
        or support_optimality.get(
            "optional_reaction_ids_in_input_order"
        )
        != ["MAR02308", "MAR10035"]
        or support_optimality.get("terminal_infeasibility_proven")
        is not True
        or support_optimality.get(
            "all_minimum_support_identities_enumerated"
        )
        is not True
        or support_optimality.get(
            "global_minimum_over_all_omitted_reactions_guaranteed"
        )
        is not False
        or support_optimality.get(
            "reaction_activity_in_phh_established"
        )
        is not False
        or support_optimality.get("context_model_accepted") is not False
        or support_optimality.get("fba_execution_allowed") is not False
    ):
        raise ValueError("PHH FASTCORE support-optimality audit changed")
    global_support_optimality = reconstruction.get(
        "fastcore_global_support_optimality"
    )
    if not isinstance(global_support_optimality, dict) or (
        global_support_optimality.get("global_candidate_reaction_count")
        != 4_226
        or global_support_optimality.get("full_target_count") != 17
        or global_support_optimality.get("lower_bound_target_count") != 2
        or global_support_optimality.get(
            "lower_bound_target_ids_in_input_order"
        )
        != ["MAR00468", "MAR00612"]
        or global_support_optimality.get(
            "lower_bound_exact_minimum_added_reaction_count"
        )
        != 59
        or global_support_optimality.get(
            "lower_bound_target_lp_certificate_count"
        )
        != 2
        or global_support_optimality.get(
            "upper_bound_feasible_added_reaction_count"
        )
        != 59
        or global_support_optimality.get(
            "all_target_upper_bound_lp_certificate_count"
        )
        != 17
        or global_support_optimality.get(
            "strict_fastcc_blocked_reaction_count"
        )
        != 0
        or global_support_optimality.get("bounds_match") is not True
        or global_support_optimality.get(
            "global_minimum_added_reaction_count"
        )
        != 59
        or global_support_optimality.get(
            "global_minimum_cardinality_proven"
        )
        is not True
        or global_support_optimality.get(
            "lower_bound_support_matches_committed_upper_support"
        )
        is not True
        or global_support_optimality.get(
            "global_minimum_identity_sets_enumerated"
        )
        is not False
        or global_support_optimality.get(
            "global_minimum_support_set_unique"
        )
        is not None
        or global_support_optimality.get(
            "global_universal_reaction_identities_established"
        )
        is not False
        or global_support_optimality.get(
            "global_minimum_over_all_omitted_reactions_guaranteed"
        )
        is not True
        or global_support_optimality.get(
            "reaction_activity_in_phh_established"
        )
        is not False
        or global_support_optimality.get("context_model_accepted")
        is not False
        or global_support_optimality.get("fba_execution_allowed")
        is not False
    ):
        raise ValueError(
            "PHH FASTCORE global-support optimality audit changed"
        )
    evidence_manifest = reconstruction.get("reaction_evidence_manifest")
    if not isinstance(evidence_manifest, dict) or (
        evidence_manifest.get("manifest_reaction_count") != 4_895
        or evidence_manifest.get(
            "adaptive_fastcore_noncore_reaction_count"
        )
        != 2_860
        or evidence_manifest.get("adaptive_noncore_without_gpr_count")
        != 2_177
        or evidence_manifest.get(
            "adaptive_noncore_zero_donor_gpr_count"
        )
        != 401
        or evidence_manifest.get(
            "adaptive_noncore_partial_donor_gpr_count"
        )
        != 282
        or evidence_manifest.get("priority_score_used") is not False
        or evidence_manifest.get("automatic_bound_change_allowed")
        is not False
    ):
        raise ValueError("PHH reaction-evidence manifest changed")
    generic_fba = reconstruction.get("generic_native_objective_audit")
    if not isinstance(generic_fba, dict):
        raise ValueError("Human-GEM generic FBA audit is missing")
    if (
        generic_fba.get("objective_id") != "obj"
        or generic_fba.get("objective_type") != "maximize"
        or generic_fba.get("objective_reaction_id") != "MAR13082"
        or generic_fba.get("objective_reaction_name")
        != "Generic human cell biomass reaction"
        or generic_fba.get("objective_is_healthy_phh_measurement") is not False
        or generic_fba.get("status") != "optimal"
        or not isinstance(generic_fba.get("objective_value"), (int, float))
        or abs(generic_fba["objective_value"] - 124.86814837744569) > 1e-9
        or generic_fba.get("active_reaction_count_at_1e_minus_9") != 2566
        or not isinstance(
            generic_fba.get("maximum_mass_balance_residual"),
            (int, float),
        )
        or generic_fba["maximum_mass_balance_residual"] > 1e-8
        or generic_fba.get("optimum_uniqueness_established") is not False
        or generic_fba.get("healthy_phh_context_extracted") is not False
        or generic_fba.get("biological_flux_authority") is not False
    ):
        raise ValueError(
            "Human-GEM generic native-objective audit changed without review"
        )
    required_nulls = (
        reconstruction.get("sbml_path"),
        context.get("extraction_algorithm"),
        optimization.get("objective"),
        optimization.get("boundary_fluxes"),
    )
    if any(value is not None for value in required_nulls):
        raise ValueError("constraint-shell inputs changed without a versioned evidence review")
    if (
        execution_bundle.get("delivered_bundle_count") != 0
        or execution_bundle.get("structurally_complete_bundle_count") != 0
        or execution_bundle.get("fba_execution_allowed") is not False
        or execution_bundle.get("runtime_flux_coupling_allowed") is not False
    ):
        raise ValueError("PHH metabolic execution escaped the empty intake gate")
