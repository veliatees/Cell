from __future__ import annotations

from math import log

from cell_engine.core.provenance import SourceReference
from cell_engine.core.random import EngineRng
from cell_engine.quantitative.geometry import AVOGADRO
from cell_engine.stochastic.cell_model import CellReactionModel
from cell_engine.stochastic.reactions import ReactionNetwork, mass_action

DATE_VERIFIED = "2026-06-21"

SECRETION_SOURCES: dict[str, SourceReference] = {
    "albumin_secretion": SourceReference(
        id="albumin_secretion",
        title="Hepatocyte secretory protein transport rates (pulse-chase) + constitutive albumin secretion",
        url="https://pubmed.ncbi.nlm.nih.gov/6538481/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Secretory proteins move ER->Golgi at t1/2 = 14-137 min (selective); Golgi->medium t1/2 ~15 min; mean transit ~30 min. Albumin is secreted constitutively (proalbumin -> ER -> Golgi pro-peptide cleavage -> blood), not stored.",
    ),
}

SECRETION_VOLUME_L = 1.0 / AVOGADRO

# Grounded transit half-times (seconds).
T_HALF_ER_GOLGI_S = 30.0 * 60.0   # ~30 min (within the measured 14-137 min range)
T_HALF_GOLGI_BLOOD_S = 15.0 * 60.0  # ~15 min


def _rate_from_half_time(t_half_s: float) -> float:
    return log(2.0) / t_half_s


def build_albumin_secretion_network(volume_l: float = SECRETION_VOLUME_L) -> ReactionNetwork:
    """The constitutive albumin secretory pathway with literature transit rates.

    amino acids -> proalbumin (ER) -> albumin (Golgi, pro-peptide cleaved) -> blood.
    Rates come from measured ER->Golgi and Golgi->medium half-times, so the
    secretion timescale (~30 min transit) is grounded, not invented.
    """
    species = ("amino_acids", "proalbumin_ER", "albumin_golgi", "albumin_blood")
    reactions = (
        mass_action("albumin_translation", {"amino_acids": 1}, {"proalbumin_ER": 1}, 0.01,
                    source_id="albumin_secretion", notes="ER-targeted translation of proalbumin."),
        mass_action("er_to_golgi", {"proalbumin_ER": 1}, {"albumin_golgi": 1},
                    _rate_from_half_time(T_HALF_ER_GOLGI_S), source_id="albumin_secretion",
                    notes="ER->Golgi export (t1/2 ~30 min); pro-peptide cleaved in Golgi."),
        mass_action("golgi_to_blood", {"albumin_golgi": 1}, {"albumin_blood": 1},
                    _rate_from_half_time(T_HALF_GOLGI_BLOOD_S), source_id="albumin_secretion",
                    notes="Golgi->blood constitutive secretion (t1/2 ~15 min)."),
    )
    return ReactionNetwork(species=species, reactions=reactions, volume_l=volume_l)


def run_secretion(t_end_s: float, rng: EngineRng, *, amino_acids: float = 10000.0,
                  dt_s: float = 1.0) -> dict[str, float]:
    network = build_albumin_secretion_network()
    counts = {s: 0.0 for s in network.species}
    counts["amino_acids"] = amino_acids
    return CellReactionModel(network=network, counts=counts).advance(t_end_s, rng, mode="cle", dt_s=dt_s).counts
