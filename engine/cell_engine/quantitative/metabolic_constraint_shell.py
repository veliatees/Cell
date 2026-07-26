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
from cell_engine.quantitative.human_gem_phh_proteome_context import (
    load_committed_human_gem_phh_proteome_gpr_audit,
)
from cell_engine.quantitative.phh_metabolic_execution_bundle import (
    phh_metabolic_execution_bundle_intake_snapshot,
    validate_phh_metabolic_execution_bundle_intake_snapshot,
)


DATE_VERIFIED = "2026-07-26"
VERSION = "metabolic_constraint_shell_v7"
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
            "proteome core was trialed with FASTCORE, but the output failed "
            "strict consistency and the closure retained nearly the full network."
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
            "seven_donor_proteome_FASTCORE_trial_rejected_PHH_execution_blocked"
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
            "source-defined FASTCORE selected 7,320 reactions but left 408 output reactions blocked at the declared epsilon",
            "strict connected-component closure retained 11,639 of 11,641 consistent reactions, so context specificity was not established",
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
