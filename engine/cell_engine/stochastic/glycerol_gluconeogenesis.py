"""Glycerol gluconeogenesis — the cheap glucose route from fat's backbone.

When adipose triglyceride is lipolysed in fasting, it releases fatty acids (-> the
liver oxidises them to ketone bodies) and a glycerol backbone (-> the liver turns it
into glucose). This module is the glycerol arm, completing the fate of lipolysis:

    glycerol + ATP            --(glycerol kinase, liver-only)--> glycerol-3-phosphate
    glycerol-3-phosphate + NAD+ --(GPD1)-->                      DHAP + NADH
    2 DHAP                    --(TPI + aldolase)-->              fructose-1,6-P2
    fructose-1,6-P2           --(FBPase1)-->                     fructose-6-P   [induced]
    fructose-6-P             --(PGI)-->                          glucose-6-P
    glucose-6-P              --(G6Pase)-->                       glucose        [induced]
    glucose                 --(GLUT2)-->                         blood glucose  [induced]

Glycerol enters **below** PEP, at the triose-phosphate level, so it bypasses the
expensive pyruvate->PEP steps: making glucose from glycerol costs only **~2 ATP**
(glycerol kinase) per glucose, versus 6 from pyruvate/lactate. Glycerol is
accordingly the *preferred*, lowest-energy gluconeogenic substrate
(Lal et al. 2018; glycerol/G3P review 2026).

Shares the lower gluconeogenic enzymes (FBPase1/PGI/G6Pase/GLUT2) with
``gluconeogenesis.py`` under the same reciprocal hormonal control — in a composed
whole-cell those lower steps are one shared pathway (dedupe is a 1b concern).
Magnitudes flagged ``placeholder``; topology, the below-PEP entry, the ~2-ATP cost
and 2:1 carbon are the grounded claims.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from cell_engine.core.provenance import SourceReference
from cell_engine.core.random import EngineRng
from cell_engine.processes.hepatocyte import build_hepatocyte_definition
from cell_engine.quantitative.geometry import (
    build_hepatocyte_geometry,
    molecules_from_concentration_mM,
)
from cell_engine.stochastic.cell_model import CYTOSOL, CellReactionModel
from cell_engine.stochastic.gluconeogenesis import gluconeogenic_drive
from cell_engine.stochastic.reactions import Reaction, ReactionNetwork
from cell_engine.stochastic.signaling import HormoneState

DATE_VERIFIED = "2026-06-22"

GLYCEROL_SOURCES: dict[str, SourceReference] = {
    "glycerol_preferred_substrate": SourceReference(
        id="glycerol_preferred_substrate",
        title="Glycerol induces G6pc in primary mouse hepatocytes and is the preferred substrate for gluconeogenesis both in vitro and in vivo",
        url="https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6885632/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Glycerol is a preferred, direct gluconeogenic substrate; synthesis of "
            "glucose from glycerol takes fewer steps and less energy than from "
            "pyruvate/lactate, and glycerol induces G6Pase (G6pc)."
        ),
    ),
    "glycerol_g3p_review": SourceReference(
        id="glycerol_g3p_review",
        title="Glycerol and Glycerol-3-Phosphate: Multifaceted Metabolites in Metabolism, Cancer, and Other Diseases",
        url="https://academic.oup.com/edrv/advance-article/doi/10.1210/endrev/bnaf033/8250484",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes=(
            "Endocrine Reviews. Hepatic glycerol kinase (liver-only, ATP) -> G3P; "
            "cytosolic GPD1 (NAD+/NADH) interconverts G3P and DHAP; DHAP feeds "
            "gluconeogenesis below PEP."
        ),
    ),
}

# Real hepatocyte cytosolic volume (pseudo-first-order reactions are volume-
# independent; seeds/outputs become real mM concentrations).
GLYCEROL_VOLUME_L = build_hepatocyte_geometry(build_hepatocyte_definition()).volume_of(CYTOSOL)


def _pseudo_first_order(
    reaction_id: str, reactants: dict[str, int], products: dict[str, int],
    k_per_s: float, driver: str, *, source_id: str, notes: str,
) -> Reaction:
    """Rate first-order in ``driver`` with exact stoichiometry (conservation-safe,
    no second-order blow-up). Pseudo-first-order approximation, flagged."""
    need = dict(reactants)

    def propensity(counts: Mapping[str, float], volume_l: float) -> float:
        for species, stoich in need.items():
            if counts.get(species, 0.0) < stoich:
                return 0.0
        return k_per_s * max(counts.get(driver, 0.0), 0.0)

    return Reaction(id=reaction_id, reactants=dict(reactants), products=dict(products),
                    propensity=propensity, source_id=source_id, notes=notes)


@dataclass(frozen=True)
class GlycerolGluconeogenesisParams:
    glycerol_kinase_per_s: float = 0.40    # glycerol + ATP -> G3P  (committed entry)
    gpd1_per_s: float = 0.50               # G3P + NAD+ -> DHAP + NADH
    triose_condensation_per_s: float = 0.60  # 2 DHAP -> F1,6P2
    fbpase_per_s: float = 0.50             # F1,6P2 -> F6P   [induced]
    pgi_per_s: float = 0.80                # F6P -> G6P
    g6pase_per_s: float = 0.50             # G6P -> glucose  [induced]
    glucose_export_per_s: float = 0.40     # glucose -> blood [induced]


def build_glycerol_gluconeogenesis_network(
    hormones: HormoneState,
    params: GlycerolGluconeogenesisParams = GlycerolGluconeogenesisParams(),
    volume_l: float = GLYCEROL_VOLUME_L,
) -> ReactionNetwork:
    """Glycerol -> glucose, with the lower bypass enzymes under reciprocal hormonal control.

    Conserved (tested): ``ATP + ADP`` and ``NADH + NAD_plus`` invariant.
    """
    drive = gluconeogenic_drive(hormones)
    species = (
        "glycerol", "glycerol_3_phosphate", "dihydroxyacetone_phosphate",
        "fructose_1_6_bisphosphate", "fructose_6_phosphate", "glucose_6_phosphate",
        "glucose", "glucose_blood", "ATP", "ADP", "NAD_plus", "NADH",
    )
    reactions = (
        _pseudo_first_order(
            "glycerol_kinase", {"glycerol": 1, "ATP": 1}, {"glycerol_3_phosphate": 1, "ADP": 1},
            params.glycerol_kinase_per_s * drive, driver="glycerol", source_id="glycerol_g3p_review",
            notes="Glycerol kinase (liver-only): glycerol -> G3P, 1 ATP. Gated by drive as the committed entry (constitutively liver-expressed; flux rises in fasting).",
        ),
        _pseudo_first_order(
            "glycerol_3_phosphate_dehydrogenase", {"glycerol_3_phosphate": 1, "NAD_plus": 1},
            {"dihydroxyacetone_phosphate": 1, "NADH": 1},
            params.gpd1_per_s, driver="glycerol_3_phosphate", source_id="glycerol_g3p_review",
            notes="GPD1 (cytosolic, NAD+): G3P -> DHAP + NADH; DHAP enters gluconeogenesis below PEP.",
        ),
        _pseudo_first_order(
            "triose_phosphate_condensation", {"dihydroxyacetone_phosphate": 2},
            {"fructose_1_6_bisphosphate": 1},
            params.triose_condensation_per_s, driver="dihydroxyacetone_phosphate",
            source_id="glycerol_preferred_substrate",
            notes="TPI + aldolase (lumped): 2 triose phosphates -> fructose-1,6-P2.",
        ),
        _pseudo_first_order(
            "fructose_1_6_bisphosphatase", {"fructose_1_6_bisphosphate": 1}, {"fructose_6_phosphate": 1},
            params.fbpase_per_s * drive, driver="fructose_1_6_bisphosphate", source_id="glycerol_preferred_substrate",
            notes="FBPase1 (shared lower gluconeogenic bypass, hormonally induced).",
        ),
        _pseudo_first_order(
            "phosphoglucose_isomerase_reverse", {"fructose_6_phosphate": 1}, {"glucose_6_phosphate": 1},
            params.pgi_per_s, driver="fructose_6_phosphate", source_id="glycerol_preferred_substrate",
            notes="PGI (reversible): F6P -> G6P.",
        ),
        _pseudo_first_order(
            "glucose_6_phosphatase", {"glucose_6_phosphate": 1}, {"glucose": 1},
            params.g6pase_per_s * drive, driver="glucose_6_phosphate", source_id="glycerol_preferred_substrate",
            notes="G6Pase: glucose release; glycerol induces G6pc (Lal et al. 2018).",
        ),
        _pseudo_first_order(
            "hepatic_glucose_output", {"glucose": 1}, {"glucose_blood": 1},
            params.glucose_export_per_s * drive, driver="glucose", source_id="glycerol_preferred_substrate",
            notes="GLUT2 hepatic glucose output.",
        ),
    )
    return ReactionNetwork(species=species, reactions=reactions, volume_l=volume_l)


def run_glycerol_gluconeogenesis(
    hormones: HormoneState,
    t_end_s: float,
    rng: EngineRng,
    *,
    glycerol_mM: float = 6.0,
    atp_mM: float = 20.0,
    nad_pool_mM: float = 8.0,
    params: GlycerolGluconeogenesisParams = GlycerolGluconeogenesisParams(),
    dt_s: float = 0.05,
) -> dict[str, float]:
    """Run glycerol -> glucose from a glycerol load (mM) at a given hormone state.

    ATP is seeded as a supplied budget (regeneration not modelled here)."""
    network = build_glycerol_gluconeogenesis_network(hormones, params)
    v = network.volume_l
    counts = {s: 0.0 for s in network.species}
    counts["glycerol"] = molecules_from_concentration_mM(glycerol_mM, v)
    counts["ATP"] = molecules_from_concentration_mM(atp_mM, v)
    counts["NAD_plus"] = molecules_from_concentration_mM(nad_pool_mM, v)
    counts["NADH"] = molecules_from_concentration_mM(nad_pool_mM * 0.25, v)
    return CellReactionModel(network=network, counts=counts).advance(
        t_end_s, rng, mode="cle", dt_s=dt_s
    ).counts


def glucose_output(counts: dict[str, float]) -> float:
    return counts["glucose_blood"] + counts["glucose"]
