"""Hepatic amino-acid catabolism — the nitrogen funnel that feeds urea + glucose.

The liver disposes of amino-acid nitrogen through the **transdeamination** system
(Brosnan 2000): transaminases collect the alpha-amino group of most amino acids
onto a single carrier, glutamate, and glutamate dehydrogenase (GDH) then releases
it as free ammonia. The carbon skeletons left behind (pyruvate, oxaloacetate,
alpha-ketoglutarate) flow into gluconeogenesis, while the nitrogen (ammonia +
aspartate) flows into the urea cycle:

    glutamine             --(glutaminase)-->  glutamate + ammonia
    alanine + alpha-KG    --(ALT)-->          pyruvate + glutamate      [-> gluconeogenesis]
    glutamate + OAA       --(AST)-->          alpha-KG + aspartate      [-> urea cycle N2]
    glutamate + NAD+      --(GDH)-->          alpha-KG + ammonia + NADH [-> urea cycle N1]

So this module produces exactly the two nitrogen donors the urea cycle consumes
(``ammonia`` for CPS1, ``aspartate`` for ASS1) and the gluconeogenic carbon
(``pyruvate``) — the shared species names let it couple to those pathways.

Note on the evidence gate: GDH uses both NAD+ and NADP+ in vivo; NADP(H) is a
**gated** evidence class here, so GDH is modelled on NAD+ only (the hepatic
oxidative-deamination direction), flagged, until NADP(H) handling is curated.

Magnitudes are normalized/illustrative (flagged ``placeholder``), the same altitude
as the other pathway modules; the transdeamination topology, the glutamate-hub
funnel, the nitrogen stoichiometry and the urea/gluconeogenesis coupling are the
grounded claims.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from cell_engine.core.provenance import SourceReference
from cell_engine.core.random import EngineRng
from cell_engine.quantitative.geometry import AVOGADRO
from cell_engine.stochastic.cell_model import CellReactionModel
from cell_engine.stochastic.reactions import Reaction, ReactionNetwork

DATE_VERIFIED = "2026-06-22"

AMINO_ACID_SOURCES: dict[str, SourceReference] = {
    "glutamate_nitrogen_hub": SourceReference(
        id="glutamate_nitrogen_hub",
        title="Glutamate, at the Interface between Amino Acid and Carbohydrate Metabolism",
        url="https://jn.nutrition.org/article/S0022-3166(22)14024-1/fulltext",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes=(
            "Brosnan JT, J Nutr 2000;130:988S-990S. Transdeamination: aminotransferases "
            "funnel amino-N onto glutamate; GDH (oxidative deamination) releases ammonia; "
            "carbon skeletons -> glucose, nitrogen -> urea."
        ),
    ),
    "liver_gdh_gluconeogenesis": SourceReference(
        id="liver_gdh_gluconeogenesis",
        title="Liver Glutamate Dehydrogenase Controls Whole-Body Energy Partitioning Through Amino Acid-Derived Gluconeogenesis and Ammonia Homeostasis",
        url="https://diabetesjournals.org/diabetes/article/67/10/1949/35297",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Karaca et al., Diabetes 2018. Hepatic GDH bridges amino-acid-derived "
            "gluconeogenesis and ammonia/urea homeostasis."
        ),
    ),
}

AMINO_ACID_VOLUME_L = 1.0 / AVOGADRO


def _pseudo_first_order(
    reaction_id: str,
    reactants: dict[str, int],
    products: dict[str, int],
    k_per_s: float,
    driver: str,
    *,
    source_id: str,
    notes: str,
) -> Reaction:
    """Rate first-order in ``driver`` with exact (multi-reactant) stoichiometry, so
    conserved moieties stay invariant and second-order terms can't explode on the
    normalized scale. Gated to 0 if any reactant is below stoichiometric need.
    (Pseudo-first-order approximation, flagged; shared shape with the other pathway
    modules — a candidate to lift into reactions.py in an attended refactor.)"""
    need = dict(reactants)

    def propensity(counts: Mapping[str, float], volume_l: float) -> float:
        for species, stoich in need.items():
            if counts.get(species, 0.0) < stoich:
                return 0.0
        return k_per_s * max(counts.get(driver, 0.0), 0.0)

    return Reaction(
        id=reaction_id, reactants=dict(reactants), products=dict(products),
        propensity=propensity, source_id=source_id, notes=notes,
    )


@dataclass(frozen=True)
class AminoAcidCatabolismParams:
    glutaminase_per_s: float = 0.30     # glutamine -> glutamate + ammonia
    alt_per_s: float = 0.40             # alanine + alpha-KG -> pyruvate + glutamate
    ast_per_s: float = 0.40             # glutamate + OAA -> alpha-KG + aspartate
    gdh_per_s: float = 0.25             # glutamate + NAD+ -> alpha-KG + ammonia + NADH


def build_amino_acid_catabolism_network(
    params: AminoAcidCatabolismParams = AminoAcidCatabolismParams(),
    volume_l: float = AMINO_ACID_VOLUME_L,
) -> ReactionNetwork:
    """Transdeamination network producing urea substrates (ammonia, aspartate) and
    gluconeogenic carbon (pyruvate).

    Conserved (checked in tests):
    - nitrogen: ``alanine + 2*glutamine + glutamate + aspartate + ammonia`` invariant.
    - NAD: ``NADH + NAD_plus`` invariant.
    """
    species = (
        "alanine", "glutamine", "glutamate", "alpha_ketoglutarate", "aspartate",
        "oxaloacetate", "pyruvate", "ammonia", "NAD_plus", "NADH",
    )
    reactions = (
        _pseudo_first_order(
            "glutaminase", {"glutamine": 1}, {"glutamate": 1, "ammonia": 1},
            params.glutaminase_per_s, driver="glutamine", source_id="glutamate_nitrogen_hub",
            notes="Glutaminase: glutamine -> glutamate + ammonia (periportal; first N release).",
        ),
        _pseudo_first_order(
            "alanine_transaminase", {"alanine": 1, "alpha_ketoglutarate": 1}, {"pyruvate": 1, "glutamate": 1},
            params.alt_per_s, driver="alanine", source_id="glutamate_nitrogen_hub",
            notes="ALT: alanine amino group -> glutamate; pyruvate skeleton -> gluconeogenesis.",
        ),
        _pseudo_first_order(
            "aspartate_transaminase", {"glutamate": 1, "oxaloacetate": 1}, {"alpha_ketoglutarate": 1, "aspartate": 1},
            params.ast_per_s, driver="glutamate", source_id="glutamate_nitrogen_hub",
            notes="AST: makes aspartate, the urea cycle's second nitrogen donor (ASS1).",
        ),
        _pseudo_first_order(
            "glutamate_dehydrogenase", {"glutamate": 1, "NAD_plus": 1},
            {"alpha_ketoglutarate": 1, "ammonia": 1, "NADH": 1},
            params.gdh_per_s, driver="glutamate", source_id="liver_gdh_gluconeogenesis",
            notes="GDH oxidative deamination: glutamate -> alpha-KG + ammonia (urea cycle N1). NAD+ used (NADP+ gated).",
        ),
    )
    return ReactionNetwork(species=species, reactions=reactions, volume_l=volume_l)


def total_nitrogen(counts: dict[str, float]) -> float:
    """Total bound+free amino nitrogen across the tracked pools (glutamine carries 2)."""
    return (
        counts["alanine"] + 2.0 * counts["glutamine"] + counts["glutamate"]
        + counts["aspartate"] + counts["ammonia"]
    )


def run_amino_acid_catabolism(
    t_end_s: float,
    rng: EngineRng,
    *,
    alanine: float = 3000.0,
    glutamine: float = 3000.0,
    alpha_ketoglutarate: float = 2000.0,
    oxaloacetate: float = 2000.0,
    nad_pool: float = 4000.0,
    params: AminoAcidCatabolismParams = AminoAcidCatabolismParams(),
    dt_s: float = 0.05,
) -> dict[str, float]:
    """Run amino-acid catabolism from an amino-acid load with alpha-KG/OAA acceptors."""
    network = build_amino_acid_catabolism_network(params)
    counts = {s: 0.0 for s in network.species}
    counts["alanine"] = alanine
    counts["glutamine"] = glutamine
    counts["alpha_ketoglutarate"] = alpha_ketoglutarate
    counts["oxaloacetate"] = oxaloacetate
    counts["NAD_plus"] = nad_pool
    counts["NADH"] = nad_pool * 0.25
    return CellReactionModel(network=network, counts=counts).advance(
        t_end_s, rng, mode="cle", dt_s=dt_s
    ).counts
