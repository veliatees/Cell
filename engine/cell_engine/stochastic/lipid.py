from __future__ import annotations

from dataclasses import dataclass

from cell_engine.core.provenance import SourceReference
from cell_engine.core.random import EngineRng
from cell_engine.processes.hepatocyte import build_hepatocyte_definition
from cell_engine.quantitative.geometry import (
    build_hepatocyte_geometry,
    molecules_from_concentration_mM,
)
from cell_engine.stochastic.cell_model import CYTOSOL, CellReactionModel
from cell_engine.stochastic.reactions import ReactionNetwork, mass_action

DATE_VERIFIED = "2026-06-21"

LIPID_SOURCES: dict[str, SourceReference] = {
    "hepatic_lipid": SourceReference(
        id="hepatic_lipid",
        title="Hepatic lipid metabolism and NAFLD (lipid uptake, DNL, beta-oxidation, VLDL secretion)",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC6105174/",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes="Liver lipid balance = supply (uptake + de novo lipogenesis) vs disposal (beta-oxidation + VLDL secretion). Steatosis (NAFLD) develops when triglyceride synthesis exceeds VLDL secretion.",
    ),
}

# Real cytosolic volume of the canonical hepatocyte (same approach as
# glycolysis.seed_glycolysis_model): build the geometry from the hepatocyte
# definition and take the cytosol compartment volume (~1.77e-12 L). This puts
# seeded counts and concentrations on the real molar / hepatocyte-volume scale.
# NOTE: every reaction in this module is FIRST-ORDER mass_action, whose rate
# constant is volume-independent ((N_A*V)^(order-1) = 1), so the per-second
# constants in LipidParams are unchanged by this rescaling.
LIPID_VOLUME_L = build_hepatocyte_geometry(build_hepatocyte_definition()).volume_of(CYTOSOL)


@dataclass(frozen=True)
class LipidParams:
    fa_uptake_per_s: float = 0.3
    dnl_per_s: float = 0.05         # de novo lipogenesis (acetyl-CoA -> FA)
    beta_ox_per_s: float = 0.15     # fatty-acid oxidation
    tg_synthesis_per_s: float = 0.3
    vldl_secretion_per_s: float = 0.3  # disposal capacity (impaired -> steatosis)
    ketogenesis_per_s: float = 0.05


def build_lipid_network(params: LipidParams = LipidParams(), volume_l: float = LIPID_VOLUME_L) -> ReactionNetwork:
    """Hepatic lipid handling: uptake + DNL vs beta-oxidation + VLDL secretion.

    The cellular triglyceride pool is the fat droplet: it grows (steatosis) when
    triglyceride synthesis outpaces VLDL secretion.
    """
    species = ("fatty_acids_blood", "fatty_acids", "acetyl_CoA", "triglyceride",
               "vldl_blood", "ketone_bodies")
    reactions = (
        mass_action("fa_uptake", {"fatty_acids_blood": 1}, {"fatty_acids": 1},
                    params.fa_uptake_per_s, source_id="hepatic_lipid", notes="Circulating FFA uptake."),
        mass_action("de_novo_lipogenesis", {"acetyl_CoA": 1}, {"fatty_acids": 1},
                    params.dnl_per_s, source_id="hepatic_lipid", notes="ACC/FASN de novo lipogenesis."),
        mass_action("beta_oxidation", {"fatty_acids": 1}, {"acetyl_CoA": 1},
                    params.beta_ox_per_s, source_id="hepatic_lipid", notes="Mitochondrial/peroxisomal beta-oxidation."),
        mass_action("tg_synthesis", {"fatty_acids": 1}, {"triglyceride": 1},
                    params.tg_synthesis_per_s, source_id="hepatic_lipid", notes="Triglyceride synthesis (fat droplet)."),
        mass_action("vldl_secretion", {"triglyceride": 1}, {"vldl_blood": 1},
                    params.vldl_secretion_per_s, source_id="hepatic_lipid", notes="VLDL secretion (TG disposal)."),
        mass_action("ketogenesis", {"acetyl_CoA": 1}, {"ketone_bodies": 1},
                    params.ketogenesis_per_s, source_id="hepatic_lipid", notes="Ketone body production from excess acetyl-CoA."),
    )
    return ReactionNetwork(species=species, reactions=reactions, volume_l=volume_l)


def run_lipid(t_end_s: float, rng: EngineRng, *, fa_load_mM: float = 0.3,
              acetyl_coa_mM: float = 0.1,
              params: LipidParams = LipidParams(), dt_s: float = 0.05) -> dict[str, float]:
    """Run the hepatic lipid network seeded on the real molar scale.

    ``fa_load_mM`` is the circulating free-fatty-acid pool (plasma FFA is
    physiologically ~0.3-0.6 mM; default 0.3 mM) and ``acetyl_coa_mM`` is the
    hepatic acetyl-CoA pool feeding DNL/ketogenesis (~0.05-0.1 mM; default
    0.1 mM). Both are converted to molecule counts in the real cytosolic
    volume via ``molecules_from_concentration_mM``.
    """
    network = build_lipid_network(params)
    volume_l = network.volume_l
    counts = {s: 0.0 for s in network.species}
    counts["fatty_acids_blood"] = molecules_from_concentration_mM(fa_load_mM, volume_l)
    counts["acetyl_CoA"] = molecules_from_concentration_mM(acetyl_coa_mM, volume_l)
    return CellReactionModel(network=network, counts=counts).advance(t_end_s, rng, mode="cle", dt_s=dt_s).counts
