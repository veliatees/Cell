from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

from cell_engine import EngineRng, build_hepatocyte_definition, initial_hepatocyte_state, run_cell
from cell_engine.core.genome import GENOME_SOURCES
from cell_engine.core.expression import EXPRESSION_SOURCES
from cell_engine.core.genomic_architecture import GENOMIC_ARCHITECTURE_SOURCES
from cell_engine.core.serialization import to_plain
from cell_engine.io.snapshots import snapshot_to_json
from cell_engine.io.brian2 import BRIAN2_SOURCES, brian2_communication_snapshot
from cell_engine.ml.generative import GENERATIVE_SOURCES, generative_modeling_snapshot
from cell_engine.multicell.communication import (
    COMMUNICATION_SOURCES,
    hepatocyte_communication_snapshot,
)
from cell_engine.multicell.spatial_world import (
    SPATIAL_WORLD_SOURCES,
    apply_spatial_world_to_cell,
    build_single_hepatocyte_world,
    spatial_world_snapshot,
)
from cell_engine.stochastic.cell_cycle import CELL_CYCLE_TIMING_PROFILES, apply_timing_profile
from cell_engine.stochastic.whole_cell import (
    WHOLE_CELL_CYCLE,
    run_whole_cell_population,
    seed_whole_cell_population,
    whole_cell_population_snapshot,
)
from cell_engine.stochastic.hepatocyte_regeneration import (
    HepatocyteRegenerationInput,
    apply_regeneration_decision,
    evaluate_hepatocyte_regeneration,
    regeneration_timing_profile,
)
from cell_engine.stochastic.integrated_cell import (
    SCOREABLE_SPECIES,
    build_integrated_hepatocyte_network,
)
from cell_engine.stochastic.signaling import HormoneState
from cell_engine.validation.hmdb_ranges import score_compartment_concentrations
from cell_engine.validation.experiments import CURATED_EXPERIMENTS, apply_scenario
from cell_engine.validation.phh_baseline import load_phh_baseline, phh_baseline_snapshot
from cell_engine.validation.scientific_release import assert_scientific_release, scientific_release_snapshot
from cell_engine.quantitative.phh_profiles import PhhNutritionalState, phh_profiles_snapshot
from cell_engine.quantitative.phh_profiles import phh_profile
from cell_engine.quantitative.phh_state import quantitative_phh_state_snapshot, schematic_visual_state_snapshot
from cell_engine.quantitative.zonation import ZONATION_SOURCES, human_hepatocyte_zonation_snapshot
from cell_engine.quantitative.human_liver_open_atlas import (
    HUMAN_LIVER_OPEN_ATLAS_SOURCES,
    human_liver_open_atlas_snapshot,
)
from cell_engine.quantitative.human_hepatocyte_3d_morphometry import (
    HUMAN_HEPATOCYTE_3D_MORPHOMETRY_SOURCES,
    human_hepatocyte_3d_morphometry_snapshot,
)
from cell_engine.quantitative.homeostasis_v3 import HOMEOSTASIS_V3_SOURCES, human_nutritional_homeostasis_v3_snapshot
from cell_engine.quantitative.endocrine import ENDOCRINE_SOURCES, human_endocrine_context_snapshot
from cell_engine.quantitative.published_glucose_model import (
    PUBLISHED_GLUCOSE_MODEL_SOURCES,
    published_hepatic_glucose_snapshot,
)
from cell_engine.quantitative.published_glucose_lineage import (
    PUBLISHED_GLUCOSE_LINEAGE_SOURCES,
    published_glucose_lineage_snapshot,
)
from cell_engine.quantitative.published_glucose_external_validation import (
    PUBLISHED_GLUCOSE_EXTERNAL_VALIDATION_SOURCES,
    published_glucose_external_validation_snapshot,
)
from cell_engine.quantitative.human_validation_protocol import human_mixed_meal_validation_protocol_snapshot
from cell_engine.quantitative.phh_glucose_validation import (
    PHH_GLUCOSE_VALIDATION_SOURCES,
    healthy_phh_glucose_validation_snapshot,
)
from cell_engine.quantitative.phh_spheroid_protocol import phh_spheroid_validation_protocol_snapshot
from cell_engine.quantitative.phh_glucose_observability import (
    PHH_GLUCOSE_OBSERVABILITY_SOURCES,
    phh_glucose_observability_snapshot,
)
from cell_engine.quantitative.glucose_homeostasis_contract import (
    exact_glucose_homeostasis_snapshot,
)
from cell_engine.quantitative.glucose_open_system import glucose_open_system_snapshot
from cell_engine.quantitative.phh_albumin_secretion import (
    PHH_ALBUMIN_SECRETION_SOURCES,
    phh_albumin_secretion_snapshot,
)
from cell_engine.quantitative.phh_cyp_function import (
    PHH_CYP_FUNCTION_SOURCES,
    phh_cyp_function_snapshot,
)
from cell_engine.quantitative.phh_biliary_excretion import (
    PHH_BILIARY_EXCRETION_SOURCES,
    phh_biliary_excretion_snapshot,
)
from cell_engine.quantitative.phh_identity_heterogeneity import (
    PHH_IDENTITY_HETEROGENEITY_SOURCES,
    phh_identity_heterogeneity_snapshot,
)
from cell_engine.quantitative.phh_proteome_budget import (
    PHH_PROTEOME_BUDGET_SOURCES,
    phh_proteome_budget_snapshot,
)
from cell_engine.quantitative.phh_proteome_atlas import (
    PHH_PROTEOME_ATLAS_SOURCES,
    phh_proteome_atlas_snapshot,
)
from cell_engine.quantitative.phh_transporter_inventory import (
    PHH_TRANSPORTER_INVENTORY_SOURCES,
    phh_transporter_inventory_snapshot,
)
from cell_engine.quantitative.phh_protein_functional_evidence import (
    PHH_PROTEIN_FUNCTIONAL_EVIDENCE_SOURCES,
    phh_protein_functional_evidence_snapshot,
)
from cell_engine.quantitative.human_sch_bile_acids import (
    HUMAN_SCH_BILE_ACID_SOURCES,
    human_sch_bile_acids_snapshot,
)
from cell_engine.stochastic.secretion import SECRETION_SOURCES
from cell_engine.stochastic.sinusoid import sinusoid_boundary_snapshot, sinusoid_coupled_homeostasis_snapshot
from cell_engine.validation.model_audit import scientific_model_audit_snapshot
from cell_engine.validation.hepatic_flux import hepatic_flux_evidence_snapshot, unified_nutritional_context_snapshot
from cell_engine.validation.evidence_intake import evidence_intake_snapshot
from cell_engine.validation.physical_validation import (
    PHYSICAL_VALIDATION_SOURCES,
    physical_validation_snapshot,
)
from cell_engine.validation.reaction_authority import audit_reaction_network
from cell_engine.validation.kinetic_transfer import (
    KINETIC_TRANSFER_SOURCES,
    kinetic_transfer_snapshot,
)
from cell_engine.validation.glucose_calibration import glucose_calibration_validation_snapshot
from cell_engine.validation.reports import build_assumption_report
from cell_engine.processes.cellular_memory import CELLULAR_MEMORY_SOURCES
from cell_engine.processes.cellular_response import CELLULAR_RESPONSE_SOURCES


def integrated_metabolism_snapshot(profile_id: PhhNutritionalState) -> dict:
    """Compartment-correct boundary validation, isolated from placeholder pathways."""
    profile = phh_profile(profile_id)
    glucose_pool = profile.pools.get("glucose_blood")
    if glucose_pool is None:
        return {
            "state": profile_id,
            "validation_scope": "unavailable_no_profile_specific_blood_boundary",
            "model_role": "missingness_visible_not_zero",
            "n_in_range": 0,
            "n_scored": 0,
            "metabolites": [],
            "unavailable": [{
                "species": "glucose",
                "required_compartment": "blood",
                "hmdb_id": "HMDB0000122",
                "reason": f"no source-backed blood glucose target registered for {profile_id}",
            }],
            "sinusoid_boundary": sinusoid_coupled_homeostasis_snapshot("midlobular", profile_id),
        }
    glucose_target = glucose_pool.value_mM
    scored, unavailable = score_compartment_concentrations(
        {"blood": {"glucose": glucose_target}, "intracellular": {}},
        only=("glucose",) + SCOREABLE_SPECIES,
    )
    return {
        "state": profile_id,
        "validation_scope": "explicit_blood_boundary_only",
        "model_role": "source_boundary_validation_not_integrated_pathway_output",
        "n_in_range": sum(1 for s in scored if s.classification == "in_range"),
        "n_scored": len(scored),
        "metabolites": [
            {
                "species": s.species,
                "value_mM": round(s.value_mM, 4),
                "low_mM": s.low_mM,
                "high_mM": s.high_mM,
                "classification": s.classification,
                "hmdb_id": s.hmdb_id,
                "compartment": s.compartment,
            }
            for s in scored
        ],
        "unavailable": unavailable,
        "sinusoid_boundary": sinusoid_boundary_snapshot(profile_id),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a Python engine snapshot for the TypeScript visualizer.")
    parser.add_argument("--out", default="public/engine-snapshot.json")
    parser.add_argument("--steps", type=int, default=8)
    parser.add_argument("--dt", type=float, default=120.0)
    parser.add_argument("--include-division-demo", action="store_true")
    parser.add_argument("--division-t-end", type=float, default=80.0)
    parser.add_argument("--division-dt", type=float, default=0.05)
    parser.add_argument("--division-seed", type=int, default=20260621)
    parser.add_argument("--division-timing-profile", choices=tuple(CELL_CYCLE_TIMING_PROFILES), default=None)
    parser.add_argument("--regeneration-species", choices=("rat", "mouse", "human", "unknown"), default="mouse")
    parser.add_argument("--experiment", choices=tuple(CURATED_EXPERIMENTS), default="baseline")
    parser.add_argument("--zone", choices=("periportal", "midlobular", "pericentral"), default="midlobular")
    parser.add_argument("--nutrition-profile", choices=("fed_peak", "postabsorptive", "prolonged_fasted"), default="postabsorptive")
    parser.add_argument("--require-predictive-release", action="store_true")
    args = parser.parse_args()

    definition = replace(build_hepatocyte_definition(), zone=args.zone)
    phh_baseline = load_phh_baseline()
    assert_scientific_release("predictive" if args.require_predictive_release else "research_preview")
    state = initial_hepatocyte_state(definition)
    experiment = CURATED_EXPERIMENTS[args.experiment]
    state = apply_scenario(state, experiment)
    state = replace(state, model_controls={**state.model_controls, "nutrition_profile": args.nutrition_profile})
    state = run_cell(definition, state, dt_s=args.dt, steps=args.steps, rng=EngineRng(definition.stochastic_policy.seed))
    spatial_world = build_single_hepatocyte_world(time_s=state.elapsed_s)
    state = apply_spatial_world_to_cell(state, spatial_world, "hepatocyte_primary")
    if args.include_division_demo:
        regeneration_input = HepatocyteRegenerationInput(
            trigger="major_partial_hepatectomy",
            liver_mass_restored=False,
            hgf_ligand="elevated",
            met_receptor="baseline",
            egfr_ligand="elevated",
            egfr_receptor="baseline",
            il6_ligand="elevated",
            stat3_activation="elevated",
            tnf_alpha="elevated",
            nfkb_activation="elevated",
            wnt_ligand="elevated",
            beta_catenin_nuclear="elevated",
        )
        regeneration_decision = evaluate_hepatocyte_regeneration(
            regeneration_input
        )
        division_params = apply_regeneration_decision(WHOLE_CELL_CYCLE, regeneration_decision)
    else:
        regeneration_input = HepatocyteRegenerationInput()
        regeneration_decision = evaluate_hepatocyte_regeneration(regeneration_input)
        division_params = WHOLE_CELL_CYCLE
    division_timing_profile = (
        args.division_timing_profile
        or ("compressed_demo" if args.include_division_demo else "rat_hepatocyte_phx_reference")
    )
    division_params = apply_timing_profile(division_params, division_timing_profile)
    timing = regeneration_timing_profile(species=args.regeneration_species, trigger=regeneration_input.trigger)
    population = run_whole_cell_population(
        seed_whole_cell_population(definition, fed=args.nutrition_profile != "prolonged_fasted"),
        args.division_t_end,
        args.division_dt,
        EngineRng(args.division_seed),
        params=division_params,
    )
    integrated_reaction_authority = audit_reaction_network(
        build_integrated_hepatocyte_network(HormoneState()),
        network_id="integrated_hepatocyte_fuel_network_v1",
        context_match_confirmed=False,
        context_description=(
            "Composed exploratory fuel network without a matched healthy-human PHH "
            "multi-pathway flux protocol."
        ),
    )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        snapshot_to_json(
            definition,
            state,
            state_extras={
                "evidence_sources": to_plain({
                    **GENOME_SOURCES,
                    **EXPRESSION_SOURCES,
                    **GENOMIC_ARCHITECTURE_SOURCES,
                    **CELLULAR_MEMORY_SOURCES,
                    **CELLULAR_RESPONSE_SOURCES,
                    **ZONATION_SOURCES,
                    **HUMAN_HEPATOCYTE_3D_MORPHOMETRY_SOURCES,
                    **HUMAN_LIVER_OPEN_ATLAS_SOURCES,
                    **HOMEOSTASIS_V3_SOURCES,
                    **ENDOCRINE_SOURCES,
                    **PUBLISHED_GLUCOSE_MODEL_SOURCES,
                    **PUBLISHED_GLUCOSE_LINEAGE_SOURCES,
                    **PUBLISHED_GLUCOSE_EXTERNAL_VALIDATION_SOURCES,
                    **PHH_GLUCOSE_VALIDATION_SOURCES,
                    **PHH_GLUCOSE_OBSERVABILITY_SOURCES,
                    **PHH_ALBUMIN_SECRETION_SOURCES,
                    **PHH_CYP_FUNCTION_SOURCES,
                    **PHH_BILIARY_EXCRETION_SOURCES,
                    **PHH_IDENTITY_HETEROGENEITY_SOURCES,
                    **PHH_PROTEOME_BUDGET_SOURCES,
                    **PHH_PROTEOME_ATLAS_SOURCES,
                    **PHH_TRANSPORTER_INVENTORY_SOURCES,
                    **PHH_PROTEIN_FUNCTIONAL_EVIDENCE_SOURCES,
                    **HUMAN_SCH_BILE_ACID_SOURCES,
                    **SECRETION_SOURCES,
                    **COMMUNICATION_SOURCES,
                    **SPATIAL_WORLD_SOURCES,
                    **BRIAN2_SOURCES,
                    **GENERATIVE_SOURCES,
                    **PHYSICAL_VALIDATION_SOURCES,
                    **KINETIC_TRANSFER_SOURCES,
                    **phh_baseline.sources,
                }),
                "phh_baseline": {
                    **phh_baseline_snapshot(phh_baseline),
                    **phh_profiles_snapshot(args.nutrition_profile),
                    "scientific_release": scientific_release_snapshot(),
                },
                "scientific_audit": scientific_model_audit_snapshot(),
                "assumption_report": build_assumption_report(definition, state),
                "model_authority": {
                    "status": "mixed_authority_research_preview",
                    "primary_state_path": "quantitative_state",
                    "schematic_state_path": "pools",
                    "authoritative_sections": ["quantitative_state", "quantitative_state.geometry_reference", "human_hepatocyte_3d_morphometry.normal_control_cell_volume_um3", "human_hepatocyte_3d_morphometry.normal_control_lipid_droplet_volume_percent", "nutritional_context", "endocrine_context.measured_observations", "endocrine_context.causal_glycogen_benchmark", "human_validation_protocol.observations", "healthy_phh_glucose_validation.glucose_consumption_observations", "healthy_phh_glucose_validation.insulin_response_observations", "healthy_phh_glucose_validation.human_scale_bridge", "phh_spheroid_validation_protocol.method_contract", "phh_spheroid_validation_protocol.window_targets", "phh_spheroid_validation_protocol.cumulative_target_trajectories", "phh_spheroid_validation_protocol.overlap_consistency_audits", "phh_glucose_observability.measurement_contract", "phh_glucose_observability.supplemental_constraints", "phh_glucose_observability.quantity_audit", "exact_glucose_homeostasis.source_species", "exact_glucose_homeostasis.source_reactions", "exact_glucose_homeostasis.canonical_pools", "glucose_open_system.physiological_sinusoid", "glucose_open_system.phh_batch_assay", "glucose_calibration_validation.reaction_fit_eligibility", "glucose_calibration_validation.observation_use_audit", "glucose_calibration_validation.validation_requirements", "phh_albumin_secretion.assay_contract", "phh_albumin_secretion.observed_batch_span", "phh_albumin_secretion.measurement_contract", "phh_albumin_secretion.quantity_audit", "phh_cyp_function.assay_contract", "phh_cyp_function.enzymes", "phh_biliary_excretion.assay_contract", "phh_biliary_excretion.batch_records", "phh_biliary_excretion.measurement_contract", "phh_identity_heterogeneity.facs_records", "phh_identity_heterogeneity.scrna_records", "phh_proteome_budget.whole_cell_anchors", "phh_proteome_budget.compartment_protein_mass_fractions", "phh_proteome_budget.derived_compartment_mass_budget", "phh_absolute_proteome_atlas.selected_canonical_gene_panel", "phh_absolute_proteome_atlas.cohort", "phh_transporter_inventory.transporters", "phh_protein_functional_evidence.proteins", "phh_protein_functional_evidence.kinetic_observations", "phh_protein_functional_evidence.whole_cell_transport_validations", "phh_protein_functional_evidence.functional_responses", "human_sch_bile_acids.assay_contract", "human_sch_bile_acids.measurement_contract", "human_sch_bile_acids.conditions", "human_liver_open_atlas.morphometry_2d", "human_liver_open_atlas.surfaceome", "human_liver_open_atlas.spatial_proteome", "human_liver_open_atlas.interaction_hypotheses", "zonation_state.reference_context", "zonation_state.experimental_oxygen_context", "sinusoid_homeostasis.perfusion_boundary", "nutritional_homeostasis_v3.organ_validation_trajectory", "phh_baseline", "integrated_metabolism", "reaction_authority", "kinetic_transfer", "genome.reference_assembly", "spatial_state", "spatial_world", "physical_validation"],
                    "runtime_authoritative_sections": ["spatial_state", "spatial_world"],
                    "shadow_sections": ["healthy_phh_glucose_validation.contextual_organ_to_cell_conversion", "published_glucose_model.profile_projection", "published_glucose_model.shadow_flux_prediction", "published_glucose_lineage", "published_glucose_external_validation", "intercellular_communication", "brian2_communication", "generative_modeling"],
                    "schematic_sections": ["pools", "organelles", "stress", "metabolic_fluxes", "pathway_results", "signaling_results", "membrane_state", "intercellular_communication.reference_cells"],
                    "policy": "quantitative_state wins on overlapping species; spatial_world wins on runtime geometry; reaction_authority prevents topology citations or unsupported rates from entering quantitative validation; kinetic_transfer additionally requires exact stoichiometry, compartment, symbolic equation, per-cell units, context and validation before a published parameter can enter the active network; exact_glucose_homeostasis owns canonical glucose-pool identity while glucose_open_system keeps sinusoid and PHH assay contexts non-interchangeable; glucose_calibration_validation permits descriptive residuals but blocks fitting and prediction until observability and held-out gates pass; geometry may change spatial_state but cannot alter biochemistry until a source-backed interaction law passes validation.",
                },
                "quantitative_state": quantitative_phh_state_snapshot(args.nutrition_profile),
                "human_hepatocyte_3d_morphometry": human_hepatocyte_3d_morphometry_snapshot(),
                "zonation_state": human_hepatocyte_zonation_snapshot(args.zone),
                "human_liver_open_atlas": human_liver_open_atlas_snapshot(args.zone),
                "sinusoid_homeostasis": sinusoid_coupled_homeostasis_snapshot(args.zone, args.nutrition_profile),
                "nutritional_homeostasis_v3": human_nutritional_homeostasis_v3_snapshot(args.zone),
                "hepatic_flux_evidence": hepatic_flux_evidence_snapshot(),
                "nutritional_context": unified_nutritional_context_snapshot(args.nutrition_profile),
                "endocrine_context": human_endocrine_context_snapshot(args.nutrition_profile),
                "human_validation_protocol": human_mixed_meal_validation_protocol_snapshot(),
                "healthy_phh_glucose_validation": healthy_phh_glucose_validation_snapshot(),
                "phh_spheroid_validation_protocol": phh_spheroid_validation_protocol_snapshot(),
                "phh_glucose_observability": phh_glucose_observability_snapshot(),
                "exact_glucose_homeostasis": exact_glucose_homeostasis_snapshot(),
                "glucose_open_system": glucose_open_system_snapshot(),
                "glucose_calibration_validation": glucose_calibration_validation_snapshot(),
                "phh_albumin_secretion": phh_albumin_secretion_snapshot(),
                "phh_cyp_function": phh_cyp_function_snapshot(),
                "phh_biliary_excretion": phh_biliary_excretion_snapshot(),
                "phh_identity_heterogeneity": phh_identity_heterogeneity_snapshot(),
                "phh_proteome_budget": phh_proteome_budget_snapshot(),
                "phh_absolute_proteome_atlas": phh_proteome_atlas_snapshot(),
                "phh_transporter_inventory": phh_transporter_inventory_snapshot(),
                "phh_protein_functional_evidence": phh_protein_functional_evidence_snapshot(),
                "human_sch_bile_acids": human_sch_bile_acids_snapshot(),
                "evidence_intake": evidence_intake_snapshot(),
                "published_glucose_model": published_hepatic_glucose_snapshot(args.nutrition_profile),
                "published_glucose_lineage": published_glucose_lineage_snapshot(),
                "published_glucose_external_validation": published_glucose_external_validation_snapshot(),
                "spatial_world": spatial_world_snapshot(spatial_world),
                "physical_validation": physical_validation_snapshot(),
                "intercellular_communication": hepatocyte_communication_snapshot(spatial_world),
                "brian2_communication": brian2_communication_snapshot(),
                "generative_modeling": generative_modeling_snapshot(),
                "schematic_visual_state": schematic_visual_state_snapshot(tuple(sorted(definition.pool_ids))),
                "integrated_metabolism": integrated_metabolism_snapshot(args.nutrition_profile),
                "reaction_authority": integrated_reaction_authority,
                "kinetic_transfer": kinetic_transfer_snapshot(),
                "experiment": {
                    "id": experiment.id,
                    "description": experiment.description,
                    "controls": experiment.controls,
                    "source_ids": ["bsep_cholestasis", "cholestasis_er_stress", "bile_acid_mitochondrial_apoptosis", "upr_proteostasis", "atp_death_switch", "human_tki_bile_acid_trajectory", "human_bile_acid_death_mode"],
                    "notes": "Intervention type is explicit. Control values are exact loss-of-function (0) or reference (1). Intermediate surface activity requires matched measurement or calibration.",
                },
                "division": whole_cell_population_snapshot(population, params=division_params),
                "regeneration_context": {
                    "input": regeneration_input,
                    "decision": regeneration_decision,
                    "timing_profile": timing,
                    "timing_is_real_world_reference": True,
                    "division_demo_is_time_compressed": bool(args.include_division_demo and division_params.timing_profile.time_compressed),
                },
            },
        ),
        encoding="utf-8",
    )
    print(out)


if __name__ == "__main__":
    main()
