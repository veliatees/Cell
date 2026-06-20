from __future__ import annotations

from cell_engine.core.provenance import SourceReference
from cell_engine.core.random import EngineRng
from cell_engine.quantitative.geometry import AVOGADRO
from cell_engine.stochastic.cell_model import CellReactionModel
from cell_engine.stochastic.reactions import ReactionNetwork, mass_action

DATE_VERIFIED = "2026-06-21"

PPP_SOURCES: dict[str, SourceReference] = {
    "oxidative_ppp": SourceReference(
        id="oxidative_ppp",
        title="Oxidative pentose phosphate pathway: G6PD rate-limiting, NADP+/NADPH regulation, 2 NADPH/G6P",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC11251397/",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes="Oxidative branch yields 2 NADPH + 1 CO2 per glucose-6-phosphate: G6PD (rate-limiting) makes the first NADPH, 6-phosphogluconate dehydrogenase the second + CO2. G6PD is activated by NADP+ and inhibited by NADPH; it runs far below Vmax and flux tracks the NADP+/NADPH ratio.",
    ),
}

PPP_VOLUME_L = 1.0 / AVOGADRO


def build_ppp_network(volume_l: float = PPP_VOLUME_L, *, g6pd_rate: float = 2.0e-4,
                      pgd_rate: float = 5.0e-4) -> ReactionNetwork:
    """Oxidative pentose phosphate pathway (the cell's main cytosolic NADPH source).

    Stoichiometry is grounded (2 NADPH + CO2 per G6P). The NADP+/NADPH sensitivity
    is built in: both dehydrogenases consume NADP+ and produce NADPH, so as the
    NADP+/NADPH ratio falls the bimolecular flux falls — exactly the measured
    regulation, without an invented control function. The rate constants set speed
    only (G6PD runs far below Vmax in vivo); they are not flux-identifying and are
    flagged as representative, not measured.
    """
    species = ("glucose_6_phosphate", "phosphogluconate_6", "ribulose_5_phosphate",
               "NADP_plus", "NADPH", "CO2")
    reactions = (
        mass_action("g6pd", {"glucose_6_phosphate": 1, "NADP_plus": 1},
                    {"phosphogluconate_6": 1, "NADPH": 1}, g6pd_rate, source_id="oxidative_ppp",
                    notes="G6PD (rate-limiting); rate rises with NADP+, the first NADPH. Rate magnitude representative, not measured."),
        mass_action("pgd_6", {"phosphogluconate_6": 1, "NADP_plus": 1},
                    {"ribulose_5_phosphate": 1, "NADPH": 1, "CO2": 1}, pgd_rate, source_id="oxidative_ppp",
                    notes="6-phosphogluconate dehydrogenase; second NADPH + CO2. Rate magnitude representative, not measured."),
    )
    return ReactionNetwork(species=species, reactions=reactions, volume_l=volume_l)


def total_nadp(counts: dict[str, float]) -> float:
    """Conserved cofactor pool: NADP+ + NADPH."""
    return counts.get("NADP_plus", 0.0) + counts.get("NADPH", 0.0)


def run_ppp(t_end_s: float, rng: EngineRng, *, g6p: float = 5000.0, nadp_plus: float = 4000.0,
            dt_s: float = 0.02) -> dict[str, float]:
    network = build_ppp_network()
    counts = {s: 0.0 for s in network.species}
    counts["glucose_6_phosphate"] = g6p
    counts["NADP_plus"] = nadp_plus
    return CellReactionModel(network=network, counts=counts).advance(t_end_s, rng, mode="cle", dt_s=dt_s).counts
