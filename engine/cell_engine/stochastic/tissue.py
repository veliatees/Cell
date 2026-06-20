from __future__ import annotations

from dataclasses import dataclass

from cell_engine.core.provenance import SourceReference
from cell_engine.core.random import EngineRng
from cell_engine.quantitative.geometry import AVOGADRO
from cell_engine.stochastic.cell_model import CellReactionModel
from cell_engine.stochastic.reactions import ReactionNetwork, mass_action

DATE_VERIFIED = "2026-06-20"

TISSUE_SOURCES: dict[str, SourceReference] = {
    "liver_ammonia_clearance": SourceReference(
        id="liver_ammonia_clearance",
        title="Hepatic ammonia detoxification and lobular function (textbook physiology)",
        url="https://www.ncbi.nlm.nih.gov/books/NBK22600/",
        source_type="textbook",
        date_verified=DATE_VERIFIED,
        notes="Hepatocytes lining a sinusoid collectively clear blood ammonia to urea; clearance scales with the number of functioning cells.",
    ),
}

# N_A * V = 1: rate constants act directly in molecule-count space.
TISSUE_VOLUME_L = 1.0 / AVOGADRO


@dataclass(frozen=True)
class TissueParams:
    clearance_per_cell_per_s: float = 0.05  # ammonia -> urea, per cell
    glucose_uptake_per_cell_per_s: float = 0.02


def build_tissue_network(
    n_cells: int, params: TissueParams = TissueParams(), *, volume_l: float = TISSUE_VOLUME_L
) -> ReactionNetwork:
    """A sheet of ``n_cells`` hepatocytes sharing one sinusoidal microenvironment.

    The cells share extracellular ammonia and glucose pools. Each cell clears
    ammonia to urea and takes up glucose; with more cells the *same* shared pool
    is cleared faster — a tissue-level behaviour that a single cell cannot show.
    """
    if n_cells < 1:
        raise ValueError("n_cells must be >= 1")
    species = ("env_ammonia", "env_urea", "env_glucose", "cell_glucose")
    reactions = []
    for i in range(n_cells):
        reactions.append(
            mass_action(f"clearance_cell_{i}", {"env_ammonia": 1}, {"env_urea": 1},
                        params.clearance_per_cell_per_s, source_id="liver_ammonia_clearance",
                        notes="One hepatocyte clearing shared ammonia to urea.")
        )
        reactions.append(
            mass_action(f"glucose_uptake_cell_{i}", {"env_glucose": 1}, {"cell_glucose": 1},
                        params.glucose_uptake_per_cell_per_s, source_id="liver_ammonia_clearance",
                        notes="One hepatocyte taking up shared glucose.")
        )
    return ReactionNetwork(species=species, reactions=tuple(reactions), volume_l=volume_l)


def seed_tissue(ammonia: float = 10000.0, glucose: float = 50000.0) -> dict[str, float]:
    return {"env_ammonia": ammonia, "env_urea": 0.0, "env_glucose": glucose, "cell_glucose": 0.0}


def run_tissue(
    n_cells: int,
    t_end_s: float,
    rng: EngineRng,
    *,
    dt_s: float = 0.01,
    ammonia: float = 10000.0,
    glucose: float = 50000.0,
    params: TissueParams = TissueParams(),
) -> dict[str, float]:
    """Run a tissue of ``n_cells`` and return the final shared-environment state."""
    network = build_tissue_network(n_cells, params)
    model = CellReactionModel(network=network, counts=seed_tissue(ammonia, glucose))
    advanced = model.advance(t_end_s, rng, mode="cle", dt_s=dt_s)
    return advanced.counts


def total_nitrogen(counts: dict[str, float]) -> float:
    """Conserved nitrogen pool: ammonia + urea (clearance moves one to the other)."""
    return counts.get("env_ammonia", 0.0) + counts.get("env_urea", 0.0)
