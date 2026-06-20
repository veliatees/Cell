from __future__ import annotations

from cell_engine.core.cell_definition import CellDefinition
from cell_engine.core.provenance import SourceReference
from cell_engine.quantitative.geometry import (
    build_hepatocyte_geometry,
    molecules_from_concentration_mM,
)
from cell_engine.quantitative.species import HEPATOCYTE_SPECIES, species_copy_numbers
from cell_engine.stochastic.cell_model import CYTOSOL, CellReactionModel
from cell_engine.stochastic.kinetics_data import glucokinase_reaction
from cell_engine.stochastic.reactions import Reaction, ReactionNetwork, mass_action, michaelis_menten

DATE_VERIFIED = "2026-06-20"

GLYCOLYSIS_SOURCES: dict[str, SourceReference] = {
    "pfk1_cancer_kinetics": SourceReference(
        id="pfk1_cancer_kinetics",
        title="Phosphofructokinase type 1 kinetics, isoform expression and polymorphisms",
        url="https://pubmed.ncbi.nlm.nih.gov/22213537/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="PFK1 is cooperative in F6P and inhibited by high ATP; liver isoform allosterically regulated.",
    ),
    "pyruvate_kinase_review": SourceReference(
        id="pyruvate_kinase_review",
        title="Pyruvate kinase: function, regulation and role in cancer (PMC4662905)",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC4662905/",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes="PKL sigmoidal in PEP with positive cooperativity; K0.5(PEP) ~2.37 mM, nH ~1.41; ADP bound non-cooperatively.",
    ),
    "lehninger_glycolysis": SourceReference(
        id="lehninger_glycolysis",
        title="Lehninger Principles of Biochemistry — glycolysis",
        url="https://www.macmillanlearning.com/college/us/product/Lehninger-Principles-of-Biochemistry/p/131957066X",
        source_type="textbook",
        date_verified=DATE_VERIFIED,
        notes="Pathway topology, cofactor stoichiometry, and near-equilibrium vs committed steps.",
    ),
}

# Enzyme concentration assumption shared by the committed-step Vmax terms.
# Placeholder until hepatocyte copy numbers are curated; flagged low-confidence.
_ENZYME_M = 1.0e-6


def _phosphofructokinase() -> Reaction:
    # F6P + ATP -> fructose-1,6-bisphosphate + ADP. Cooperative in F6P.
    return michaelis_menten(
        "phosphofructokinase_1",
        reactants={"fructose_6_phosphate": 1, "ATP": 1},
        products={"fructose_1_6_bisphosphate": 1, "ADP": 1},
        vmax_M_per_s=100.0 * _ENZYME_M,   # kcat placeholder
        km_M=0.3e-3,                       # S0.5(F6P) ~0.3 mM (cooperative)
        substrate="fructose_6_phosphate",
        hill=2.0,
        cosubstrate="ATP",
        cosubstrate_km_M=0.1e-3,           # ATP co-substrate availability (placeholder Km)
        source_id="pfk1_cancer_kinetics",
        notes="Committed regulatory step; kcat and exact S0.5 are placeholders, cooperativity is grounded.",
    )


def _pyruvate_kinase() -> Reaction:
    # PEP + ADP -> pyruvate + ATP. Sigmoidal in PEP (liver L-type).
    return michaelis_menten(
        "pyruvate_kinase_L",
        reactants={"phosphoenolpyruvate": 1, "ADP": 1},
        products={"pyruvate": 1, "ATP": 1},
        vmax_M_per_s=300.0 * _ENZYME_M,   # kcat placeholder
        km_M=2.37e-3,                      # measured K0.5(PEP) ~2.37 mM
        substrate="phosphoenolpyruvate",
        hill=1.41,                         # measured Hill coefficient
        cosubstrate="ADP",
        cosubstrate_km_M=0.3e-3,           # ADP bound with high affinity (non-cooperative)
        source_id="pyruvate_kinase_review",
        notes="K0.5(PEP) and Hill are literature-measured; kcat is a placeholder.",
    )


# Near-equilibrium steps: modelled as fast forward mass-action. The rate
# constants are LUMPED placeholders (confidence ~0.2) chosen so the pathway
# carries flux; correctness is enforced by the stoichiometric conservation laws,
# not by these values. Full reversible thermodynamics is a later refinement.
_FAST = "lehninger_glycolysis"


def build_glycolysis_network(volume_l: float) -> ReactionNetwork:
    """Full 10-step glycolysis on molecule counts (glucose -> 2 pyruvate).

    Cofactor stoichiometry is exact: 2 ATP invested (GK, PFK1), 4 ATP produced
    (2x PGK, 2x PK), 2 NADH produced (2x GAPDH). Inorganic phosphate is omitted
    in v1 (GAPDH written without Pi); committed steps GK/PFK1/PK use grounded
    cooperative kinetics, the seven near-equilibrium steps use fast forward
    mass-action placeholders.
    """
    species = (
        "glucose", "glucose_6_phosphate", "fructose_6_phosphate",
        "fructose_1_6_bisphosphate", "dihydroxyacetone_phosphate",
        "glyceraldehyde_3_phosphate", "bisphosphoglycerate_1_3",
        "phosphoglycerate_3", "phosphoglycerate_2", "phosphoenolpyruvate",
        "pyruvate", "ATP", "ADP", "NAD_plus", "NADH",
    )
    reactions: tuple[Reaction, ...] = (
        glucokinase_reaction(enzyme_concentration_M=_ENZYME_M),
        mass_action("phosphoglucose_isomerase", {"glucose_6_phosphate": 1},
                    {"fructose_6_phosphate": 1}, 20.0, source_id=_FAST, notes="LUMPED fast near-equilibrium."),
        _phosphofructokinase(),
        mass_action("aldolase_B", {"fructose_1_6_bisphosphate": 1},
                    {"dihydroxyacetone_phosphate": 1, "glyceraldehyde_3_phosphate": 1},
                    15.0, source_id=_FAST, notes="LUMPED: splits hexose into two trioses."),
        mass_action("triosephosphate_isomerase", {"dihydroxyacetone_phosphate": 1},
                    {"glyceraldehyde_3_phosphate": 1}, 50.0, source_id=_FAST, notes="LUMPED fast near-equilibrium."),
        mass_action("gapdh", {"glyceraldehyde_3_phosphate": 1, "NAD_plus": 1},
                    {"bisphosphoglycerate_1_3": 1, "NADH": 1}, 1.0e6, source_id=_FAST,
                    notes="LUMPED bimolecular; Pi omitted in v1. Couples NAD+->NADH."),
        mass_action("phosphoglycerate_kinase", {"bisphosphoglycerate_1_3": 1, "ADP": 1},
                    {"phosphoglycerate_3": 1, "ATP": 1}, 1.0e6, source_id=_FAST,
                    notes="LUMPED: first ATP-producing (substrate-level) step."),
        mass_action("phosphoglycerate_mutase", {"phosphoglycerate_3": 1},
                    {"phosphoglycerate_2": 1}, 30.0, source_id=_FAST, notes="LUMPED fast near-equilibrium."),
        mass_action("enolase", {"phosphoglycerate_2": 1},
                    {"phosphoenolpyruvate": 1}, 30.0, source_id=_FAST, notes="LUMPED; H2O omitted."),
        _pyruvate_kinase(),
    )
    return ReactionNetwork(species=species, reactions=reactions, volume_l=volume_l)


def carbon_triose_units(counts: dict[str, float]) -> float:
    """Conserved carbon bookkeeping: hexoses count as 2 triose-units, trioses as 1.

    Invariant under every glycolytic reaction, so it is the strongest single
    check that the 10-step stoichiometry is wired correctly.
    """
    hexoses = ("glucose", "glucose_6_phosphate", "fructose_6_phosphate", "fructose_1_6_bisphosphate")
    trioses = (
        "dihydroxyacetone_phosphate", "glyceraldehyde_3_phosphate", "bisphosphoglycerate_1_3",
        "phosphoglycerate_3", "phosphoglycerate_2", "phosphoenolpyruvate", "pyruvate",
    )
    return 2.0 * sum(counts.get(s, 0.0) for s in hexoses) + sum(counts.get(s, 0.0) for s in trioses)


def seed_glycolysis_model(definition: CellDefinition) -> CellReactionModel:
    """Glycolysis model seeded from the M030 foundation (intermediates start at 0)."""
    geometry = build_hepatocyte_geometry(definition)
    volume = geometry.volume_of(CYTOSOL)
    network = build_glycolysis_network(volume)

    seeded = species_copy_numbers(geometry, HEPATOCYTE_SPECIES)
    counts = {s: 0.0 for s in network.species}
    counts["glucose"] = seeded.get("glucose", 0.0)
    counts["ATP"] = seeded.get("ATP", 0.0)
    counts["ADP"] = seeded.get("ADP", 0.0)
    counts["NAD_plus"] = seeded.get("NAD+", 0.0)
    counts["NADH"] = seeded.get("NADH", 0.0)
    return CellReactionModel(network=network, counts=counts, t_s=0.0)
