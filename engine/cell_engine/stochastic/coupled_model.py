from __future__ import annotations

from cell_engine.core.cell_definition import CellDefinition
from cell_engine.quantitative.geometry import build_hepatocyte_geometry
from cell_engine.quantitative.species import HEPATOCYTE_SPECIES, species_copy_numbers
from cell_engine.stochastic.cell_model import CYTOSOL, CellReactionModel
from cell_engine.stochastic.central_dogma import (
    HEPATOCYTE_ENZYME_GENE,
    GeneExpressionKinetics,
    build_central_dogma_network,
)
from cell_engine.stochastic.kinetics_data import GLUCOKINASE
from cell_engine.stochastic.reactions import (
    Reaction,
    ReactionNetwork,
    compose_networks,
    mass_action,
    michaelis_menten,
)

GLUCOKINASE_ENZYME = "glucokinase_enzyme"


def expressed_glucokinase_reaction() -> Reaction:
    """Glucokinase whose Vmax is set live by the expressed enzyme count.

    Identical grounded kinetics to the standalone glucokinase (S0.5, Hill, ATP
    Km), but Vmax = kcat * [enzyme] is read from the ``glucokinase_enzyme`` pool
    that gene expression produces — so metabolic flux follows the cell's own
    protein level instead of a hard-coded constant.
    """
    return michaelis_menten(
        "glucokinase_expressed",
        reactants={"glucose": 1, "ATP": 1},
        products={"glucose_6_phosphate": 1, "ADP": 1},
        km_M=GLUCOKINASE.km_or_s05_M,
        substrate="glucose",
        hill=GLUCOKINASE.hill,
        cosubstrate="ATP",
        cosubstrate_km_M=GLUCOKINASE.atp_km_M,
        enzyme=GLUCOKINASE_ENZYME,
        kcat_per_s=GLUCOKINASE.kcat_per_s,
        source_id=GLUCOKINASE.source_id,
        notes="Expressed-enzyme glucokinase: Vmax driven by gene expression.",
    )


def build_expression_coupled_network(volume_l: float) -> ReactionNetwork:
    """Central dogma producing the glucokinase enzyme, composed with the reaction
    it catalyses + adenylate recycling, into one coupled system."""
    # Gene expression whose protein *is* the glucokinase enzyme.
    expression = build_central_dogma_network(HEPATOCYTE_ENZYME_GENE, volume_l=volume_l)
    expression = _rename_protein(expression, GLUCOKINASE_ENZYME)

    metabolism = ReactionNetwork(
        species=("glucose", "ATP", "ADP", "glucose_6_phosphate", GLUCOKINASE_ENZYME),
        reactions=(
            expressed_glucokinase_reaction(),
            mass_action("g6p_drain", {"glucose_6_phosphate": 1}, {}, 0.5,
                        notes="LUMPED downstream glycolysis flux."),
            mass_action("atp_regeneration", {"ADP": 1}, {"ATP": 1}, 0.3,
                        notes="LUMPED OXPHOS regenerating ATP."),
            mass_action("atp_maintenance", {"ATP": 1}, {"ADP": 1}, 0.1,
                        notes="LUMPED baseline ATP consumption."),
        ),
        volume_l=volume_l,
    )
    return compose_networks(expression, metabolism, volume_l=volume_l)


def _rename_protein(network: ReactionNetwork, new_name: str) -> ReactionNetwork:
    def rename(d: dict[str, int]) -> dict[str, int]:
        return {(new_name if k == "protein" else k): v for k, v in d.items()}

    reactions = tuple(
        Reaction(r.id, rename(r.reactants), rename(r.products), r.propensity, r.source_id, r.notes)
        for r in network.reactions
    )
    species = tuple(new_name if s == "protein" else s for s in network.species)
    return ReactionNetwork(species=species, reactions=reactions, volume_l=network.volume_l)


def seed_expression_coupled_model(
    definition: CellDefinition,
    *,
    kinetics: GeneExpressionKinetics = HEPATOCYTE_ENZYME_GENE,
) -> CellReactionModel:
    """Coupled gene-expression + metabolism model seeded from the M030 foundation."""
    geometry = build_hepatocyte_geometry(definition)
    volume = geometry.volume_of(CYTOSOL)
    network = build_expression_coupled_network(volume)

    seeded = species_copy_numbers(geometry, HEPATOCYTE_SPECIES)
    counts = {s: 0.0 for s in network.species}
    counts["glucose"] = seeded.get("glucose", 0.0)
    counts["ATP"] = seeded.get("ATP", 0.0)
    counts["ADP"] = seeded.get("ADP", 0.0)
    counts["gene"] = float(kinetics.gene_copies)
    return CellReactionModel(network=network, counts=counts, t_s=0.0)
