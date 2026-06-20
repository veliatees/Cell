from __future__ import annotations

from cell_engine.core.provenance import SourceReference
from cell_engine.quantitative.geometry import build_hepatocyte_geometry, molecules_from_concentration_mM
from cell_engine.stochastic.cell_model import CYTOSOL, CellReactionModel
from cell_engine.stochastic.reactions import Reaction, ReactionNetwork, mass_action

DATE_VERIFIED = "2026-06-20"

REDOX_SOURCES: dict[str, SourceReference] = {
    "glutathione_redox": SourceReference(
        id="glutathione_redox",
        title="Role of glutathione redox status in liver injury (Am. J. Physiol. 2006)",
        url="https://journals.physiology.org/doi/full/10.1152/ajpgi.00001.2006",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes="Cytosolic GSH/GSSG normally >100:1, maintained by GSSG reductase using NADPH; falls <4:1 under severe oxidative stress.",
    ),
}


def build_redox_network(volume_l: float, *, reductase_rate: float = 2.0e4) -> ReactionNetwork:
    """Glutathione antioxidant cycle coupled to NADPH.

    - Glutathione peroxidase: 2 GSH + ROS -> GSSG (detoxifies ROS)
    - Glutathione reductase:  GSSG + NADPH -> 2 GSH + NADP+ (NADPH-powered recharge)
    - NADPH regeneration (lumped PPP/G6PD): NADP+ -> NADPH
    - ROS influx (lumped oxidative load): -> ROS

    Conserved: total glutathione (GSH + 2*GSSG) and total NADP (NADPH + NADP+).
    The GSH:GSSG ratio that emerges is a measured redox readout (M037 harness).
    """
    species = ("GSH", "GSSG", "NADPH", "NADP_plus", "ROS")
    reactions: tuple[Reaction, ...] = (
        mass_action("glutathione_peroxidase", {"GSH": 2, "ROS": 1}, {"GSSG": 1}, 5.0e5,
                    source_id="glutathione_redox", notes="2 GSH neutralize ROS, forming GSSG."),
        mass_action("glutathione_reductase", {"GSSG": 1, "NADPH": 1}, {"GSH": 2, "NADP_plus": 1}, reductase_rate,
                    source_id="glutathione_redox", notes="LUMPED finite GR capacity: NADPH-powered GSSG -> 2 GSH recharge."),
        mass_action("nadph_regeneration", {"NADP_plus": 1}, {"NADPH": 1}, 5.0,
                    source_id="glutathione_redox", notes="LUMPED PPP/G6PD regenerating NADPH."),
        mass_action("ros_influx", {}, {"ROS": 1}, 2.8e-4,
                    source_id="glutathione_redox", notes="LUMPED baseline oxidative load; sets the steady GSSG."),
    )
    return ReactionNetwork(species=species, reactions=reactions, volume_l=volume_l)


def glutathione_total(counts: dict[str, float]) -> float:
    """Conserved glutathione: each GSSG holds two glutathione units."""
    return counts.get("GSH", 0.0) + 2.0 * counts.get("GSSG", 0.0)


def seed_redox_model(definition) -> CellReactionModel:
    """Seed the redox couple from the M030 glutathione/NADPH concentrations."""
    geometry = build_hepatocyte_geometry(definition)
    volume = geometry.volume_of(CYTOSOL)
    network = build_redox_network(volume)

    def n(mM: float) -> float:
        return molecules_from_concentration_mM(mM, volume)

    counts = {s: 0.0 for s in network.species}
    counts["GSH"] = n(7.0)        # M030 grounded
    counts["GSSG"] = n(0.07)      # M030 grounded (~100:1)
    counts["NADPH"] = n(0.2)      # M030 grounded
    counts["NADP_plus"] = n(0.02)
    counts["ROS"] = n(0.002)
    return CellReactionModel(network=network, counts=counts, t_s=0.0)
