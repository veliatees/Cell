"""Integrated hepatocyte network (v1.0 M5) — the fasting fuel program as one cell.

This fuses the migrated, molar-scale fuel pathways into a single reaction network on
one shared cytosolic volume, so they couple through shared cofactor and metabolite
pools (ATP/ADP, NAD+/NADH, acetyl-CoA, pyruvate, glucose...) and run as one system.

It is built additively — a NEW builder alongside the existing
``build_whole_cell_network`` — so the established whole-cell tests and snapshot are
untouched until this integrated network is proven and HMDB-validated.

Pathways fused (each already validated standalone):
- glycogen control (signaling)        - amino-acid catabolism (N -> ammonia/aspartate)
- gluconeogenesis (lactate/alanine)   - glycerol gluconeogenesis
- ketogenesis + beta-oxidation        - the malonyl-CoA node (DNL / CPT1 switch)

Reaction-id dedupe (composition keeps the FIRST/authoritative definition):
- ``alanine_transaminase`` — amino-acid catabolism owns it (richer N handling).
- the shared lower-gluconeogenic bypass enzymes (FBPase1, G6Pase, PGI,
  hepatic_glucose_output) — gluconeogenesis owns them; glycerol reuses them.
So the priority order is: glycogen, amino-acids, gluconeogenesis, glycerol,
ketogenesis, malonyl.

This is the catabolic/fasting fuel program; the glycolytic core, urea cycle and
gene-expression layers are folded in next (and lipid.py's lumped reactions are
superseded by the malonyl/ketogenesis detail, so lipid is left out here).
"""

from __future__ import annotations

from cell_engine.core.random import EngineRng
from cell_engine.processes.hepatocyte import build_hepatocyte_definition
from cell_engine.quantitative.geometry import (
    AVOGADRO,
    build_hepatocyte_geometry,
    molecules_from_concentration_mM,
)
from cell_engine.stochastic.amino_acid_catabolism import build_amino_acid_catabolism_network
from cell_engine.stochastic.cell_model import CYTOSOL, CellReactionModel
from cell_engine.stochastic.glycerol_gluconeogenesis import build_glycerol_gluconeogenesis_network
from cell_engine.stochastic.gluconeogenesis import build_gluconeogenesis_network
from cell_engine.stochastic.ketogenesis import build_hepatic_ketogenic_response
from cell_engine.stochastic.malonyl_coa_node import build_malonyl_node_network
from cell_engine.stochastic.reactions import ReactionNetwork, compose_networks
from cell_engine.stochastic.signaling import HormoneState, build_glycogen_control_network

INTEGRATED_VOLUME_L = build_hepatocyte_geometry(build_hepatocyte_definition()).volume_of(CYTOSOL)

# Physiological starting concentrations (mM) for the fuel substrates and cofactors.
DEFAULT_SEEDS_mM: dict[str, float] = {
    "glycogen": 75.0, "glucose_cyto": 5.0,          # glycogen store
    "lactate": 1.5, "alanine": 0.4, "glutamine": 0.6,  # gluconeogenic / amino substrates
    "alpha_ketoglutarate": 0.2, "oxaloacetate": 0.2,
    "glycerol": 0.2, "fatty_acids": 0.5,             # lipolysis products
    "acetyl_CoA": 0.1,
    "ATP": 30.0, "NAD_plus": 2.0, "NADH": 0.5,       # ATP a supplied budget; matrix oxidised
}


def build_integrated_hepatocyte_network(
    hormones: HormoneState,
    volume_l: float = INTEGRATED_VOLUME_L,
) -> ReactionNetwork:
    """Fuse the migrated fuel pathways into one network (deduped, one shared volume)."""
    return compose_networks(
        build_glycogen_control_network(hormones, volume_l),
        build_amino_acid_catabolism_network(volume_l=volume_l),
        build_gluconeogenesis_network(hormones, volume_l=volume_l),
        build_glycerol_gluconeogenesis_network(hormones, volume_l=volume_l),
        build_hepatic_ketogenic_response(hormones, volume_l=volume_l),
        build_malonyl_node_network(hormones, volume_l=volume_l),
        volume_l=volume_l,
        dedupe_reactions=True,
    )


def run_integrated_hepatocyte(
    hormones: HormoneState,
    t_end_s: float,
    rng: EngineRng,
    *,
    seeds_mM: dict[str, float] | None = None,
    dt_s: float = 0.05,
) -> dict[str, float]:
    """Run the fused network from physiological mM seeds; returns molecule counts."""
    network = build_integrated_hepatocyte_network(hormones)
    v = network.volume_l
    seeds = dict(DEFAULT_SEEDS_mM)
    if seeds_mM:
        seeds.update(seeds_mM)
    counts = {s: 0.0 for s in network.species}
    for species, mM in seeds.items():
        if species in counts:
            counts[species] = molecules_from_concentration_mM(mM, v)
    return CellReactionModel(network=network, counts=counts).advance(
        t_end_s, rng, mode="cle", dt_s=dt_s
    ).counts


def concentrations_mM(counts: dict[str, float], volume_l: float = INTEGRATED_VOLUME_L) -> dict[str, float]:
    """Convert molecule counts to mM concentrations (for HMDB scoring)."""
    scale = AVOGADRO * volume_l
    return {s: n / scale * 1000.0 for s, n in counts.items()}
