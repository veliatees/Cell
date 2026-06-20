from __future__ import annotations

from cell_engine.core.provenance import SourceReference
from cell_engine.core.random import EngineRng
from cell_engine.quantitative.geometry import AVOGADRO
from cell_engine.stochastic.cell_model import CellReactionModel
from cell_engine.stochastic.reactions import ReactionNetwork, mass_action

DATE_VERIFIED = "2026-06-21"

TRANSPORT_SOURCES: dict[str, SourceReference] = {
    "bile_formation": SourceReference(
        id="bile_formation",
        title="Molecular Mechanisms in Bile Formation (Physiology 2000) + hepatocyte transporter reviews",
        url="https://journals.physiology.org/doi/full/10.1152/physiologyonline.2000.15.2.89",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes="Sinusoidal uptake: Na/K-ATPase, NTCP (Na-dependent bile salt), OATP1B1/1B3 (organic anions), GLUT2 (glucose). Canalicular export: BSEP (bile salts, ATP-dependent), MRP2 (bilirubin glucuronides/GSH, ATP-dependent), MDR3 (phospholipid). Vectorial sinusoid->cell->canaliculus flux.",
    ),
}

# N_A * V = 1: rate constants act directly in molecule-count space.
TRANSPORT_VOLUME_L = 1.0 / AVOGADRO


def build_transport_network(volume_l: float, *, bsep_active: bool = True) -> ReactionNetwork:
    """Polarized hepatocyte membrane transport (vectorial blood -> cell -> bile).

    Sinusoidal (basolateral) uptake feeds the cytosol; canalicular (apical)
    ATP-dependent pumps export to bile. Setting ``bsep_active=False`` models a
    BSEP defect -> bile salts accumulate in the cell (cholestasis).
    """
    species = (
        "glucose_blood", "glucose_cyto",
        "bile_blood", "bile_cyto", "bile_canaliculus",
        "bilirubin_blood", "bilirubin_cyto", "bilirubin_canaliculus",
        "ATP", "ADP",
    )
    reactions = [
        # Sinusoidal uptake.
        mass_action("glut2_uptake", {"glucose_blood": 1}, {"glucose_cyto": 1}, 0.4,
                    source_id="bile_formation", notes="GLUT2 facilitated glucose uptake."),
        mass_action("glut2_efflux", {"glucose_cyto": 1}, {"glucose_blood": 1}, 0.1,
                    source_id="bile_formation", notes="GLUT2 is bidirectional (smaller efflux)."),
        mass_action("ntcp_uptake", {"bile_blood": 1}, {"bile_cyto": 1}, 0.5,
                    source_id="bile_formation", notes="NTCP Na-dependent bile salt uptake (Na gradient from Na/K-ATPase)."),
        mass_action("oatp_uptake", {"bilirubin_blood": 1}, {"bilirubin_cyto": 1}, 0.4,
                    source_id="bile_formation", notes="OATP1B1/1B3 organic-anion (bilirubin) uptake."),
        # Na/K-ATPase maintains the Na gradient at an ATP cost.
        mass_action("na_k_atpase", {"ATP": 1}, {"ADP": 1}, 0.05,
                    source_id="bile_formation", notes="Na/K-ATPase sets the Na gradient (ATP cost)."),
        # Canalicular ATP-dependent export.
        mass_action("mrp2_export", {"bilirubin_cyto": 1, "ATP": 1}, {"bilirubin_canaliculus": 1, "ADP": 1}, 0.3,
                    source_id="bile_formation", notes="MRP2 ATP-dependent bilirubin-conjugate export to bile."),
    ]
    if bsep_active:
        reactions.append(
            mass_action("bsep_export", {"bile_cyto": 1, "ATP": 1}, {"bile_canaliculus": 1, "ADP": 1}, 0.3,
                        source_id="bile_formation", notes="BSEP ATP-dependent bile-salt export to canaliculus.")
        )
    return ReactionNetwork(species=species, reactions=tuple(reactions), volume_l=volume_l)


def seed_transport(bile: float = 5000.0, glucose: float = 5000.0, bilirubin: float = 3000.0) -> dict[str, float]:
    counts = {s: 0.0 for s in (
        "glucose_blood", "glucose_cyto", "bile_blood", "bile_cyto", "bile_canaliculus",
        "bilirubin_blood", "bilirubin_cyto", "bilirubin_canaliculus", "ATP", "ADP")}
    counts.update(bile_blood=bile, glucose_blood=glucose, bilirubin_blood=bilirubin, ATP=50000.0, ADP=5000.0)
    return counts


def run_transport(t_end_s: float, rng: EngineRng, *, bsep_active: bool = True, dt_s: float = 0.02,
                  bile: float = 5000.0) -> dict[str, float]:
    network = build_transport_network(TRANSPORT_VOLUME_L, bsep_active=bsep_active)
    model = CellReactionModel(network=network, counts=seed_transport(bile=bile))
    return model.advance(t_end_s, rng, mode="cle", dt_s=dt_s).counts
