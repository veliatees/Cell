from __future__ import annotations

from dataclasses import dataclass

from cell_engine.core.provenance import SourceReference
from cell_engine.core.random import EngineRng
from cell_engine.quantitative.geometry import AVOGADRO
from cell_engine.stochastic.cell_model import CellReactionModel
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

LIPID_VOLUME_L = 1.0 / AVOGADRO


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


def run_lipid(t_end_s: float, rng: EngineRng, *, fa_load: float = 5000.0,
              params: LipidParams = LipidParams(), dt_s: float = 0.05) -> dict[str, float]:
    network = build_lipid_network(params)
    counts = {s: 0.0 for s in network.species}
    counts["fatty_acids_blood"] = fa_load
    counts["acetyl_CoA"] = 2000.0
    return CellReactionModel(network=network, counts=counts).advance(t_end_s, rng, mode="cle", dt_s=dt_s).counts
