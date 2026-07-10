from __future__ import annotations

import argparse
from pathlib import Path

from cell_engine import EngineRng, build_hepatocyte_definition, initial_hepatocyte_state, run_cell
from cell_engine.core.genome import GENOME_SOURCES
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
from cell_engine.stochastic.signaling import FASTED
from cell_engine.stochastic.integrated_cell import (
    SCOREABLE_SPECIES,
    concentrations_mM,
    run_integrated_hepatocyte,
)
from cell_engine.validation.hmdb_ranges import score_concentrations
from cell_engine.validation.experiments import CURATED_EXPERIMENTS, apply_scenario
from cell_engine.processes.cellular_memory import CELLULAR_MEMORY_SOURCES
from cell_engine.processes.cellular_response import CELLULAR_RESPONSE_SOURCES


def integrated_metabolism_snapshot() -> dict:
    """The fused integrated hepatocyte scored against HMDB (for the browser badges)."""
    conc = concentrations_mM(run_integrated_hepatocyte(FASTED, 120.0, EngineRng(7)))
    scored = score_concentrations(conc, only=SCOREABLE_SPECIES)
    return {
        "state": "fasted",
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
            }
            for s in scored
        ],
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
    args = parser.parse_args()

    definition = build_hepatocyte_definition()
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
                    **CELLULAR_MEMORY_SOURCES,
                    **CELLULAR_RESPONSE_SOURCES,
                }),
                "integrated_metabolism": integrated_metabolism_snapshot(),
                "experiment": {
                    "id": experiment.id,
                    "description": experiment.description,
                    "controls": experiment.controls,
                    "source_ids": ["bsep_cholestasis", "cholestasis_er_stress", "bile_acid_mitochondrial_apoptosis", "upr_proteostasis", "atp_death_switch"],
                    "notes": "Control values are exact loss-of-function (0) or reference (1). Intermediate surface activity requires matched measurement or calibration.",
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
