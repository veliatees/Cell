from __future__ import annotations

from dataclasses import dataclass

from cell_engine.core.provenance import SourceReference
from cell_engine.core.random import EngineRng
from cell_engine.quantitative.geometry import AVOGADRO
from cell_engine.stochastic.cell_model import CellReactionModel
from cell_engine.stochastic.reactions import ReactionNetwork, mass_action

DATE_VERIFIED = "2026-06-20"

DETOX_SOURCES: dict[str, SourceReference] = {
    "paracetamol_toxicity": SourceReference(
        id="paracetamol_toxicity",
        title="Paracetamol (acetaminophen) overdose and hepatotoxicity (Expert Opin. Drug Metab. Toxicol. 2023)",
        url="https://www.tandfonline.com/doi/full/10.1080/17425255.2023.2223959",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes="Most paracetamol is glucuronide/sulfate conjugated; a fraction is oxidized by CYP2E1/CYP3A4 to reactive NAPQI, detoxified by GSH conjugation. Overdose depletes GSH; free NAPQI binds proteins, raises ROS, lowers ATP, causes cell death.",
    ),
}

# N_A * V = 1: rate constants act directly in molecule-count space.
DETOX_VOLUME_L = 1.0 / AVOGADRO


@dataclass(frozen=True)
class DetoxParams:
    safe_conjugation_per_s: float = 0.30   # glucuronide/sulfate (dominant, safe)
    cyp_oxidation_per_s: float = 0.10      # CYP2E1 -> NAPQI (reactive fraction)
    gsh_conjugation_per_s: float = 2.0e-3  # NAPQI + GSH -> mercapturate (bimolecular)
    protein_binding_per_s: float = 0.5     # NAPQI -> adduct + ROS (when GSH is gone)


def build_detox_network(volume_l: float, params: DetoxParams = DetoxParams()) -> ReactionNetwork:
    """Hepatic xenobiotic detox, paracetamol as the worked example.

    Two routes compete for the reactive metabolite NAPQI: GSH conjugation (safe)
    and protein binding (toxic). While GSH lasts, NAPQI is cleared; once GSH is
    exhausted, NAPQI lingers and binds protein + generates ROS — the paracetamol
    overdose mechanism, emergent from the kinetics.
    """
    species = (
        "paracetamol", "safe_conjugate", "NAPQI", "mercapturate",
        "GSH", "protein_adduct", "ROS",
    )
    reactions = (
        mass_action("safe_conjugation", {"paracetamol": 1}, {"safe_conjugate": 1},
                    params.safe_conjugation_per_s, source_id="paracetamol_toxicity",
                    notes="Phase II glucuronide/sulfate route (dominant, non-toxic)."),
        mass_action("cyp_oxidation", {"paracetamol": 1}, {"NAPQI": 1},
                    params.cyp_oxidation_per_s, source_id="paracetamol_toxicity",
                    notes="CYP2E1/CYP3A4 Phase I -> reactive NAPQI."),
        mass_action("gsh_conjugation", {"NAPQI": 1, "GSH": 1}, {"mercapturate": 1},
                    params.gsh_conjugation_per_s, source_id="paracetamol_toxicity",
                    notes="Phase II GSH conjugation detoxifies NAPQI (consumes GSH)."),
        mass_action("protein_binding", {"NAPQI": 1}, {"protein_adduct": 1, "ROS": 1},
                    params.protein_binding_per_s, source_id="paracetamol_toxicity",
                    notes="Unconjugated NAPQI binds protein and raises ROS (toxic)."),
    )
    return ReactionNetwork(species=species, reactions=reactions, volume_l=volume_l)


def seed_detox(dose: float, gsh: float = 10000.0) -> dict[str, float]:
    return {
        "paracetamol": float(dose), "safe_conjugate": 0.0, "NAPQI": 0.0,
        "mercapturate": 0.0, "GSH": gsh, "protein_adduct": 0.0, "ROS": 0.0,
    }


def run_detox(
    dose: float,
    t_end_s: float,
    rng: EngineRng,
    *,
    gsh: float = 10000.0,
    dt_s: float = 0.01,
    params: DetoxParams = DetoxParams(),
) -> dict[str, float]:
    """Run a paracetamol dose through detox; return the final state."""
    network = build_detox_network(DETOX_VOLUME_L, params)
    model = CellReactionModel(network=network, counts=seed_detox(dose, gsh))
    advanced = model.advance(t_end_s, rng, mode="cle", dt_s=dt_s)
    return advanced.counts
