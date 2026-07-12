from __future__ import annotations

from dataclasses import dataclass

from cell_engine.core.provenance import SourceReference
from cell_engine.stochastic.reactions import ReactionNetwork, mass_action

DATE_VERIFIED = "2026-06-20"

CENTRAL_DOGMA_SOURCES: dict[str, SourceReference] = {
    "bionumbers_expression": SourceReference(
        id="bionumbers_expression",
        title="Cell Biology by the Numbers — mRNA/protein lifetimes and copy numbers",
        url="https://book.bionumbers.org/",
        source_type="database",
        date_verified=DATE_VERIFIED,
        notes="Order-of-magnitude mammalian transcription/translation rates, mRNA/protein half-lives.",
    ),
    "thattai_vanoudenaarden": SourceReference(
        id="thattai_vanoudenaarden",
        title="Thattai & van Oudenaarden, Intrinsic noise in gene regulatory networks (PNAS 2001)",
        url="https://www.pnas.org/doi/10.1073/pnas.151588598",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Two-stage model: mRNA is Poisson; protein noise is super-Poissonian with Fano = 1 + b (burst size b = k_tl/k_deg_mRNA).",
    ),
    "synthetic_expression_benchmark": SourceReference(
        id="synthetic_expression_benchmark",
        title="Synthetic central-dogma software benchmark",
        url="docs/milestones/034-central-dogma.md",
        source_type="project_assumption",
        date_verified=DATE_VERIFIED,
        notes="Non-biological rates retained only for analytic/SSA tests. This profile is opt-in and is excluded from authoritative hepatocyte snapshots.",
    ),
}


@dataclass(frozen=True)
class GeneExpressionKinetics:
    """Rates for a single gene's two-stage expression (per second).

    A profile must carry its own source and confidence. The bundled default is a
    synthetic software benchmark, not a human-hepatocyte calibration.
    """

    gene_id: str
    gene_copies: int
    k_transcription_per_s: float
    k_mrna_decay_per_s: float
    k_translation_per_s: float
    k_protein_decay_per_s: float
    source_id: str
    confidence: float
    notes: str = ""

    @property
    def burst_size(self) -> float:
        """Proteins made per mRNA before it decays: b = k_tl / k_mRNA_decay."""
        return self.k_translation_per_s / self.k_mrna_decay_per_s

    @property
    def mean_mrna(self) -> float:
        return self.k_transcription_per_s * self.gene_copies / self.k_mrna_decay_per_s

    @property
    def mean_protein(self) -> float:
        return self.k_translation_per_s * self.mean_mrna / self.k_protein_decay_per_s


# Synthetic rates chosen so stochastic statistics converge quickly in tests.
# This is not a hepatocyte parameter set and is excluded from default snapshots.
HEPATOCYTE_ENZYME_GENE = GeneExpressionKinetics(
    gene_id="enzyme_gene",
    gene_copies=2,
    k_transcription_per_s=0.02,    # ~0.04 mRNA/s from 2 copies
    k_mrna_decay_per_s=0.0023,     # mRNA half-life ~5 min
    k_translation_per_s=0.05,      # ~21 proteins per mRNA -> strong bursts
    k_protein_decay_per_s=0.002,   # protein half-life ~6 min (fast for testability)
    source_id="synthetic_expression_benchmark",
    confidence=0.0,
    notes="Synthetic software benchmark only; burst size ~21. Mechanism test, not biological calibration.",
)


def build_central_dogma_network(
    kinetics: GeneExpressionKinetics = HEPATOCYTE_ENZYME_GENE,
    *,
    volume_l: float = 1.0e-12,
) -> ReactionNetwork:
    """gene -> mRNA -> protein, with first-order decay of mRNA and protein.

    Every reaction is zeroth/first order in counts, so the dynamics are
    volume-independent; volume is carried only for API uniformity. This is the
    canonical low-copy system for which exact SSA (not CLE) is the correct tool.
    """
    gene, mrna, protein = "gene", "mRNA", "protein"
    reactions = (
        mass_action("transcription", {gene: 1}, {gene: 1, mrna: 1},
                    kinetics.k_transcription_per_s, source_id=kinetics.source_id,
                    notes="Gene-catalysed mRNA synthesis."),
        mass_action("mrna_decay", {mrna: 1}, {}, kinetics.k_mrna_decay_per_s,
                    source_id=kinetics.source_id, notes="First-order mRNA turnover."),
        mass_action("translation", {mrna: 1}, {mrna: 1, protein: 1},
                    kinetics.k_translation_per_s, source_id=kinetics.source_id,
                    notes="mRNA-catalysed protein synthesis (bursts)."),
        mass_action("protein_decay", {protein: 1}, {}, kinetics.k_protein_decay_per_s,
                    source_id=kinetics.source_id, notes="First-order protein turnover/dilution."),
    )
    return ReactionNetwork(species=(gene, mrna, protein), reactions=reactions, volume_l=volume_l)


def initial_expression_counts(
    kinetics: GeneExpressionKinetics = HEPATOCYTE_ENZYME_GENE,
) -> dict[str, float]:
    """Start at the gene copy number with no mRNA/protein (expression builds up)."""
    return {"gene": float(kinetics.gene_copies), "mRNA": 0.0, "protein": 0.0}
