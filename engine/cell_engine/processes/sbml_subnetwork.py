from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from cell_engine.core.state import CellState, PathwayResult
from cell_engine.io.sbml import SbmlSubsetModel, load_sbml_subset, simulate_sbml_subset

DEFAULT_SBML_MODEL = Path(__file__).resolve().parents[3] / "models" / "sbml" / "hepatocyte_redox.xml"


def apply_sbml_subnetwork(
    state: CellState,
    *,
    model: SbmlSubsetModel | None = None,
    model_path: str | Path | None = None,
    species_to_pool: dict[str, str] | None = None,
    dt_s: float,
    steps: int = 1,
) -> CellState:
    loaded_model = model or load_sbml_subset(model_path or DEFAULT_SBML_MODEL)
    mapping = species_to_pool or {species_id: species_id for species_id in loaded_model.species}
    initial_species = {
        species_id: state.pools[pool_id].value
        for species_id, pool_id in mapping.items()
        if pool_id in state.pools and species_id in loaded_model.species
    }
    result = simulate_sbml_subset(loaded_model, initial_species=initial_species, dt_s=dt_s, steps=steps)

    pools = dict(state.pools)
    for species_id, pool_id in mapping.items():
        if pool_id in pools and species_id in result.species:
            pools[pool_id] = replace(pools[pool_id], value=max(0.0, result.species[species_id]))

    pathway_result = PathwayResult(
        id=f"{loaded_model.id}_result_{int(state.elapsed_s + dt_s * steps)}",
        model_id=loaded_model.id,
        engine=result.engine,
        species=result.species,
        unit=result.unit,
        provenance=result.provenance,
        notes=f"reaction_extents={result.reaction_extents}",
    )
    return replace(state, pools=pools, pathway_results=state.pathway_results + (pathway_result,))

