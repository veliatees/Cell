"""Generalised genotype -> phenotype: every metabolic enzyme is produced by its
own gene and its reaction's Vmax follows the expressed enzyme level.

The single-enzyme prototype (``coupled_model`` — glucokinase only) proved the
seam: ``michaelis_menten(enzyme=..., kcat_per_s=...)`` reads Vmax = kcat*[E] live
from an enzyme pool that gene expression fills. This module turns that one-off
into a framework: declare a set of :class:`ExpressionCoupledEnzyme` (each = a
gene's expression kinetics + the Michaelis/Hill reaction it catalyses) and
compose one network where every enzyme is transcribed, translated, and drives
its flux from its own protein count. Change a gene's transcription and the
downstream metabolic flux changes — real genotype -> phenotype at network scale.

Each enzyme gets its own prefixed expression species (``<id>_gene``,
``<id>_mRNA``, ``<id>``) and reaction ids, built directly (not by renaming a
generic network) so the propensities reference the correct pools.

HONESTY: only enzymes with grounded kinetic constants (currently glucokinase)
carry measured kcat/Km. A second enzyme is included to exercise the multi-enzyme
machinery with kcat/Km explicitly flagged as PLACEHOLDER (source_id starts with
"PLACEHOLDER") pending a BRENDA/SABIO-RK kinetic-constant pass. Adding a real
enzyme later is one ``ExpressionCoupledEnzyme`` entry.
"""

from __future__ import annotations

from dataclasses import dataclass

from cell_engine.stochastic.central_dogma import (
    HEPATOCYTE_ENZYME_GENE,
    GeneExpressionKinetics,
)
from cell_engine.stochastic.kinetics_data import GLUCOKINASE
from cell_engine.stochastic.reactions import (
    Reaction,
    ReactionNetwork,
    compose_networks,
    mass_action,
    michaelis_menten,
)


@dataclass(frozen=True)
class ExpressionCoupledEnzyme:
    """An enzyme whose amount is set by its own gene expression.

    ``enzyme_id`` is the protein-pool species name; the enzyme's reaction must be
    built with ``enzyme=enzyme_id`` so its Vmax reads that pool.
    """

    enzyme_id: str
    gene: GeneExpressionKinetics
    reaction: Reaction


def expression_species(enzyme_id: str) -> tuple[str, str, str]:
    """(gene, mRNA, protein) species names for an enzyme."""
    return (f"{enzyme_id}_gene", f"{enzyme_id}_mRNA", enzyme_id)


def _expression_network(enzyme: ExpressionCoupledEnzyme, volume_l: float) -> ReactionNetwork:
    gene, mrna, protein = expression_species(enzyme.enzyme_id)
    k = enzyme.gene
    eid = enzyme.enzyme_id
    reactions = (
        mass_action(f"{eid}_transcription", {gene: 1}, {gene: 1, mrna: 1},
                    k.k_transcription_per_s, source_id=k.source_id,
                    notes="Gene-catalysed mRNA synthesis."),
        mass_action(f"{eid}_mrna_decay", {mrna: 1}, {}, k.k_mrna_decay_per_s,
                    source_id=k.source_id, notes="First-order mRNA turnover."),
        mass_action(f"{eid}_translation", {mrna: 1}, {mrna: 1, protein: 1},
                    k.k_translation_per_s, source_id=k.source_id,
                    notes="mRNA-catalysed protein synthesis (bursts)."),
        mass_action(f"{eid}_protein_decay", {protein: 1}, {}, k.k_protein_decay_per_s,
                    source_id=k.source_id, notes="First-order protein turnover/dilution."),
    )
    return ReactionNetwork(species=(gene, mrna, protein), reactions=reactions, volume_l=volume_l)


def build_expression_coupled_metabolism(
    enzymes: tuple[ExpressionCoupledEnzyme, ...],
    volume_l: float,
    *,
    extra_reactions: tuple[Reaction, ...] = (),
) -> ReactionNetwork:
    """Compose {gene -> mRNA -> enzyme} + {enzyme-driven reaction} for every
    enzyme, plus any extra (e.g. lumped downstream / cofactor recycling)
    reactions, into one coupled network. Duplicate reaction ids raise (the
    per-enzyme prefixing keeps them unique)."""
    nets = [_expression_network(ez, volume_l) for ez in enzymes]

    metab_species: set[str] = set()
    for ez in enzymes:
        metab_species.update(ez.reaction.reactants)
        metab_species.update(ez.reaction.products)
    for r in extra_reactions:
        metab_species.update(r.reactants)
        metab_species.update(r.products)
    metabolism = ReactionNetwork(
        species=tuple(sorted(metab_species)),
        reactions=tuple(ez.reaction for ez in enzymes) + tuple(extra_reactions),
        volume_l=volume_l,
    )
    nets.append(metabolism)
    return compose_networks(*nets, volume_l=volume_l)


def initial_expression_coupled_counts(
    enzymes: tuple[ExpressionCoupledEnzyme, ...],
    seeds: dict[str, float],
) -> dict[str, float]:
    """Start each gene at its copy number with no mRNA/enzyme (expression builds
    up), and seed the metabolite pools from ``seeds``."""
    counts: dict[str, float] = {}
    for ez in enzymes:
        gene, mrna, protein = expression_species(ez.enzyme_id)
        counts[gene] = float(ez.gene.gene_copies)
        counts[mrna] = 0.0
        counts[protein] = 0.0
    counts.update(seeds)
    return counts


# --- Ready-made enzymes ---

# Grounded: human liver glucokinase (S0.5, Hill, kcat, ATP Km all cited).
GLUCOKINASE_COUPLED = ExpressionCoupledEnzyme(
    enzyme_id="glucokinase",
    gene=HEPATOCYTE_ENZYME_GENE,
    reaction=michaelis_menten(
        "glucokinase_expressed",
        {"glucose": 1, "ATP": 1},
        {"glucose_6_phosphate": 1, "ADP": 1},
        km_M=GLUCOKINASE.km_or_s05_M,
        substrate="glucose",
        hill=GLUCOKINASE.hill,
        cosubstrate="ATP",
        cosubstrate_km_M=GLUCOKINASE.atp_km_M,
        enzyme="glucokinase",
        kcat_per_s=GLUCOKINASE.kcat_per_s,
        source_id=GLUCOKINASE.source_id,
        notes="Vmax = kcat * [expressed glucokinase]; genotype -> phenotype.",
    ),
)

# PLACEHOLDER kinetics (flagged): glucose-6-phosphatase hydrolyses G6P -> glucose
# (the gluconeogenic counter-reaction). Included to exercise the multi-enzyme
# machinery; kcat/Km must be replaced with measured values (BRENDA/SABIO-RK).
GLUCOSE_6_PHOSPHATASE_COUPLED = ExpressionCoupledEnzyme(
    enzyme_id="glucose_6_phosphatase",
    gene=HEPATOCYTE_ENZYME_GENE,
    reaction=michaelis_menten(
        "g6pase_expressed",
        {"glucose_6_phosphate": 1},
        {"glucose": 1},
        km_M=2.0e-3,
        substrate="glucose_6_phosphate",
        enzyme="glucose_6_phosphatase",
        kcat_per_s=20.0,
        source_id="PLACEHOLDER_g6pase",
        notes="PLACEHOLDER kcat (20/s) and Km (2 mM), flagged, pending BRENDA/SABIO-RK.",
    ),
)
