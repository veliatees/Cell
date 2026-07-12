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
from cell_engine.quantitative.phh_profiles import PhhNutritionalState, phh_profile
from cell_engine.stochastic.amino_acid_catabolism import build_amino_acid_catabolism_network
from cell_engine.stochastic.bioenergetics import build_phh_atp_turnover_network
from cell_engine.stochastic.cell_model import CYTOSOL, CellReactionModel
from cell_engine.stochastic.glycerol_gluconeogenesis import build_glycerol_gluconeogenesis_network
from cell_engine.stochastic.gluconeogenesis import build_gluconeogenesis_network
from cell_engine.stochastic.ketogenesis import build_hepatic_ketogenic_response
from cell_engine.stochastic.malonyl_coa_node import build_malonyl_node_network
from cell_engine.stochastic.reactions import ReactionNetwork, compose_networks, mass_action
from cell_engine.stochastic.signaling import HormoneState, build_glycogen_control_network
from cell_engine.stochastic.sinusoid import build_sinusoid_boundary_network
from cell_engine.stochastic.urea_cycle import build_urea_cycle_network

INTEGRATED_VOLUME_L = build_hepatocyte_geometry(build_hepatocyte_definition()).volume_of(CYTOSOL)

# Source-anchored pools are injected from ``phh_profile`` at run time. Remaining
# substrates are legacy pathway-context seeds and are not part of the authoritative
# Healthy PHH Baseline v1 release surface.
DEFAULT_SEEDS_mM: dict[str, float] = {
    "glucose_cyto": 5.0,
    "lactate": 1.5, "alanine": 0.4, "glutamine": 0.6,  # gluconeogenic / amino substrates
    "alpha_ketoglutarate": 0.2, "oxaloacetate": 0.2,
    "glycerol": 0.2, "fatty_acids": 0.5,             # lipolysis products
    "acetyl_CoA": 0.1,
    "ornithine": 0.3, "aspartate": 1.0,              # urea-cycle carrier + 2nd N donor
    "NADH": 0.5,
}

# Metabolites whose mM concentration is meaningful to score against HMDB. The blood
# "export" pools (glucose_blood, vldl_blood) are cumulative output flux, not regulated
# blood concentrations, so they are NOT scored here (they need a homeostatic reservoir
# + continuous-influx layer, tracked separately).
SCOREABLE_SPECIES = (
    "urea", "ammonia", "beta_hydroxybutyrate", "acetoacetate",
    "lactate", "pyruvate", "alanine", "glutamine", "glutamate", "glycerol",
)


def build_integrated_hepatocyte_network(
    hormones: HormoneState,
    volume_l: float = INTEGRATED_VOLUME_L,
    *,
    sinusoid_profile_id: PhhNutritionalState | None = None,
) -> ReactionNetwork:
    """Fuse the migrated fuel pathways into one network (deduped, one shared volume)."""
    networks = [
        build_glycogen_control_network(hormones, volume_l),
        build_amino_acid_catabolism_network(volume_l=volume_l),
        build_gluconeogenesis_network(hormones, volume_l=volume_l),
        build_glycerol_gluconeogenesis_network(hormones, volume_l=volume_l),
        build_hepatic_ketogenic_response(hormones, volume_l=volume_l),
        build_malonyl_node_network(hormones, volume_l=volume_l),
        build_urea_cycle_network(volume_l),       # consumes ammonia + aspartate -> urea
        build_phh_atp_turnover_network(volume_l),
    ]
    if sinusoid_profile_id is not None:
        networks.append(build_sinusoid_boundary_network(sinusoid_profile_id, volume_l))
    return compose_networks(*networks, volume_l=volume_l, dedupe_reactions=True)


def run_integrated_hepatocyte(
    hormones: HormoneState,
    t_end_s: float,
    rng: EngineRng,
    *,
    seeds_mM: dict[str, float] | None = None,
    profile_id: PhhNutritionalState | None = None,
    use_sinusoid_boundary: bool = False,
    dt_s: float = 0.05,
) -> dict[str, float]:
    """Run the fused network from physiological mM seeds; returns molecule counts."""
    if profile_id is None:
        profile_id = "prolonged_fasted" if hormones.glucagon > hormones.insulin else "fed_peak"
    network = build_integrated_hepatocyte_network(
        hormones,
        sinusoid_profile_id=profile_id if use_sinusoid_boundary else None,
    )
    v = network.volume_l
    seeds = dict(DEFAULT_SEEDS_mM)
    seeds.update(phh_profile(profile_id).concentrations_mM())
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
