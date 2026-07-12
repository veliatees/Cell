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
)
from cell_engine.validation.hmdb_ranges import score_compartment_concentrations
from cell_engine.validation.experiments import CURATED_EXPERIMENTS, apply_scenario
from cell_engine.validation.phh_baseline import load_phh_baseline, phh_baseline_snapshot
from cell_engine.validation.scientific_release import assert_scientific_release, scientific_release_snapshot
from cell_engine.quantitative.phh_profiles import phh_profiles_snapshot
from cell_engine.quantitative.phh_profiles import phh_profile
from cell_engine.quantitative.phh_state import quantitative_phh_state_snapshot, schematic_visual_state_snapshot
from cell_engine.quantitative.zonation import ZONATION_SOURCES, human_hepatocyte_zonation_snapshot
from cell_engine.quantitative.homeostasis_v3 import HOMEOSTASIS_V3_SOURCES, human_nutritional_homeostasis_v3_snapshot
from cell_engine.stochastic.sinusoid import sinusoid_boundary_snapshot, sinusoid_coupled_homeostasis_snapshot
from cell_engine.validation.model_audit import scientific_model_audit_snapshot
from cell_engine.validation.hepatic_flux import hepatic_flux_evidence_snapshot
from cell_engine.validation.reports import build_assumption_report
from cell_engine.processes.cellular_memory import CELLULAR_MEMORY_SOURCES
from cell_engine.processes.cellular_response import CELLULAR_RESPONSE_SOURCES


def integrated_metabolism_snapshot() -> dict:
    """Compartment-correct boundary validation, isolated from placeholder pathways."""
    glucose_target = phh_profile("postabsorptive").pools["glucose_blood"].value_mM
    scored, unavailable = score_compartment_concentrations(
        {"blood": {"glucose": glucose_target}, "intracellular": {}},
        only=("glucose",) + SCOREABLE_SPECIES,
    )
    return {
        "state": "postabsorptive",
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
        "sinusoid_boundary": sinusoid_boundary_snapshot(),
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
    parser.add_argument("--require-predictive-release", action="store_true")
    args = parser.parse_args()

    definition = replace(build_hepatocyte_definition(), zone=args.zone)
    phh_baseline = load_phh_baseline()
    assert_scientific_release("predictive" if args.require_predictive_release else "research_preview")
    state = initial_hepatocyte_state(definition)
    experiment = CURATED_EXPERIMENTS[args.experiment]
    state = apply_scenario(state, experiment)
    state = run_cell(definition, state, dt_s=args.dt, steps=args.steps, rng=EngineRng(definition.stochastic_policy.seed))
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
        seed_whole_cell_population(definition, fed=True),
        args.division_t_end,
        args.division_dt,
        EngineRng(args.division_seed),
        params=division_params,
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
                    **HOMEOSTASIS_V3_SOURCES,
                    **phh_baseline.sources,
                }),
                "phh_baseline": {
                    **phh_baseline_snapshot(phh_baseline),
                    **phh_profiles_snapshot(),
                    "scientific_release": scientific_release_snapshot(),
                },
                "scientific_audit": scientific_model_audit_snapshot(),
                "assumption_report": build_assumption_report(definition, state),
                "model_authority": {
                    "status": "mixed_authority_research_preview",
                    "primary_state_path": "quantitative_state",
                    "schematic_state_path": "pools",
                    "authoritative_sections": ["quantitative_state", "zonation_state.reference_context", "sinusoid_homeostasis.perfusion_boundary", "nutritional_homeostasis_v3.organ_validation_trajectory", "phh_baseline", "integrated_metabolism", "genome.reference_assembly"],
                    "schematic_sections": ["pools", "organelles", "stress", "metabolic_fluxes", "pathway_results", "signaling_results", "membrane_state"],
                    "policy": "quantitative_state wins on overlapping species; relative 0-1 state may drive visualization but cannot support quantitative biological claims.",
                },
                "quantitative_state": quantitative_phh_state_snapshot("postabsorptive"),
                "zonation_state": human_hepatocyte_zonation_snapshot(args.zone),
                "sinusoid_homeostasis": sinusoid_coupled_homeostasis_snapshot(args.zone),
                "nutritional_homeostasis_v3": human_nutritional_homeostasis_v3_snapshot(args.zone),
                "hepatic_flux_evidence": hepatic_flux_evidence_snapshot(),
                "schematic_visual_state": schematic_visual_state_snapshot(tuple(sorted(definition.pool_ids))),
                "integrated_metabolism": integrated_metabolism_snapshot(),
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
