from __future__ import annotations

from cell_engine.core.provenance import SourceReference
from cell_engine.core.random import EngineRng
from cell_engine.quantitative.geometry import AVOGADRO
from cell_engine.stochastic.cell_model import CellReactionModel
from cell_engine.stochastic.reactions import ReactionNetwork, michaelis_menten

DATE_VERIFIED = "2026-06-21"

OXPHOS_SOURCES: dict[str, SourceReference] = {
    "tca_cycle": SourceReference(
        id="tca_cycle",
        title="TCA cycle stoichiometry and regulation (rate-limiting isocitrate dehydrogenase)",
        url="https://www.ncbi.nlm.nih.gov/books/NBK556032/",
        source_type="textbook",
        date_verified=DATE_VERIFIED,
        notes="Per acetyl-CoA: 3 NADH + 1 FADH2 + 1 GTP + 2 CO2. Rate-limiting NAD+-dependent isocitrate dehydrogenase is activated by ADP/Ca2+ and inhibited by ATP/NADH; flux tracks NAD+/NADH and energy charge.",
    ),
    "oxphos_po_ratio": SourceReference(
        id="oxphos_po_ratio",
        title="Oxidative phosphorylation P/O ratios (NADH 2.5, FADH2 1.5; Hinkle/Yu)",
        url="https://www.ncbi.nlm.nih.gov/books/NBK9885/",
        source_type="textbook",
        date_verified=DATE_VERIFIED,
        notes="P/O ratio ~2.5 ATP per NADH and ~1.5 per FADH2 (10 vs 6 H+ translocated). ~30-32 ATP per glucose. OXPHOS rate is controlled by ADP availability (respiratory control).",
    ),
}

OXPHOS_VOLUME_L = 1.0 / AVOGADRO


def build_oxphos_network(volume_l: float = OXPHOS_VOLUME_L) -> ReactionNetwork:
    """TCA cycle + electron transport / ATP synthesis, with grounded stoichiometry.

    TCA (per acetyl-CoA): 3 NADH + FADH2 + GTP(~ATP) + 2 CO2 — grounded. Electron
    transport uses the measured P/O ratios (NADH -> 2.5 ATP, FADH2 -> 1.5 ATP),
    encoded as 2 NADH -> 5 ATP and 2 FADH2 -> 3 ATP to keep integer stoichiometry.
    Propensities are Michaelis-Menten in the carrier (so they don't explode at
    high order); the full cofactor stoichiometry lives in the net change. OXPHOS
    is gated on ADP (respiratory control) and TCA on NAD+ (IDH regulation) — both
    grounded, not invented control terms.
    """
    s = AVOGADRO * volume_l  # = 1 here; concentrations equal counts
    species = ("acetyl_CoA", "NAD_plus", "NADH", "FAD", "FADH2",
               "ADP", "ATP", "GDP", "GTP", "O2", "CO2")
    reactions = (
        michaelis_menten(
            "tca_cycle",
            # GTP (not ATP) is the TCA substrate-level product, from a separate
            # guanylate pool, so adenylate is touched only by OXPHOS below.
            reactants={"acetyl_CoA": 1, "NAD_plus": 3, "FAD": 1, "GDP": 1},
            products={"NADH": 3, "FADH2": 1, "GTP": 1, "CO2": 2},
            vmax_M_per_s=4.0e4 / s, km_M=2000.0 / s, substrate="NAD_plus",
            cosubstrate="acetyl_CoA", cosubstrate_km_M=1000.0 / s,
            source_id="tca_cycle",
            notes="3 NADH + FADH2 + GTP + 2 CO2 per acetyl-CoA; IDH gated on NAD+/acetyl-CoA.",
        ),
        michaelis_menten(
            "etc_nadh_oxidation",
            reactants={"NADH": 2, "O2": 1, "ADP": 5}, products={"NAD_plus": 2, "ATP": 5},
            vmax_M_per_s=5.0e4 / s, km_M=1000.0 / s, substrate="NADH",
            cosubstrate="ADP", cosubstrate_km_M=500.0 / s,  # respiratory control by ADP
            source_id="oxphos_po_ratio",
            notes="P/O 2.5: 2 NADH + O2 + 5 ADP -> 2 NAD+ + 5 ATP. Gated on ADP.",
        ),
        michaelis_menten(
            "etc_fadh2_oxidation",
            reactants={"FADH2": 2, "O2": 1, "ADP": 3}, products={"FAD": 2, "ATP": 3},
            vmax_M_per_s=5.0e4 / s, km_M=1000.0 / s, substrate="FADH2",
            cosubstrate="ADP", cosubstrate_km_M=500.0 / s,
            source_id="oxphos_po_ratio",
            notes="P/O 1.5: 2 FADH2 + O2 + 3 ADP -> 2 FAD + 3 ATP. Gated on ADP.",
        ),
    )
    return ReactionNetwork(species=species, reactions=reactions, volume_l=volume_l)


def total_nad(counts):
    return counts.get("NAD_plus", 0.0) + counts.get("NADH", 0.0)


def total_adenylate(counts):
    return counts.get("ADP", 0.0) + counts.get("ATP", 0.0)


def total_guanylate(counts):
    return counts.get("GDP", 0.0) + counts.get("GTP", 0.0)


def seed_oxphos(acetyl_CoA=2000.0, adp=20000.0):
    return {"acetyl_CoA": acetyl_CoA, "NAD_plus": 10000.0, "NADH": 1000.0,
            "FAD": 5000.0, "FADH2": 200.0, "ADP": adp, "ATP": 2000.0,
            "GDP": 5000.0, "GTP": 0.0, "O2": 50000.0, "CO2": 0.0}


def run_oxphos(t_end_s: float, rng: EngineRng, *, acetyl_CoA=2000.0, adp=20000.0,
               dt_s: float = 0.005) -> dict[str, float]:
    network = build_oxphos_network()
    return CellReactionModel(network=network, counts=seed_oxphos(acetyl_CoA, adp)).advance(
        t_end_s, rng, mode="cle", dt_s=dt_s).counts
