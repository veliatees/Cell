from __future__ import annotations

from dataclasses import dataclass, replace
from math import isfinite
from typing import Literal

from cell_engine.core.genome import HepatocyteGenomeState
from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain
from cell_engine.quantitative.hepatocyte_counts import PROTEIN_BY_ID


PromoterState = Literal["active", "inactive", "poised", "unknown"]
ChromatinState = Literal["open", "closed", "poised", "unknown"]
ExpressionEvidenceStatus = Literal[
    "measured",
    "literature_derived",
    "normalized_reference",
    "experimental_control",
    "calibrated",
    "unknown",
]
KineticCalibrationStatus = Literal[
    "matched_human_hepatocyte",
    "external_system_reference",
    "synthetic_test_fixture",
]
RegulatoryEffect = Literal["activates", "represses"]
RegulatoryLayer = Literal["promoter", "functional_protein"]

DATE_VERIFIED = "2026-07-10"

EXPRESSION_SOURCES: dict[str, SourceReference] = {
    "genomic_burst_kinetics": SourceReference(
        id="genomic_burst_kinetics",
        title="Genomic encoding of transcriptional burst kinetics",
        url="https://www.nature.com/articles/s41586-018-0836-1",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Mammalian alleles transcribe in bursts; enhancer and core-promoter architecture affect burst frequency and size.",
    ),
    "primary_hepatocyte_protein_turnover": SourceReference(
        id="primary_hepatocyte_protein_turnover",
        title="Systematic analysis of protein turnover in primary cells",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC5814408/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Primary human hepatocyte proteins have widely different half-lives; no universal protein-decay constant is defensible.",
    ),
    "expression_unknown_policy": SourceReference(
        id="expression_unknown_policy",
        title="Genome-expression milestone missing-data policy",
        url="docs/16-genome-expression-milestone.md",
        source_type="project_assumption",
        date_verified=DATE_VERIFIED,
        notes="Gene-specific RNA and protein kinetics remain null until measured or calibrated; generic demo rates cannot silently become hepatocyte parameters.",
    ),
    "phh_bile_acid_gene_regulation": SourceReference(
        id="phh_bile_acid_gene_regulation",
        title="Potency of individual bile acids to regulate bile acid synthesis and transport genes in primary human hepatocyte cultures",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC4271050/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Primary human hepatocytes support FXR-SHP and FXR-FGF19 activation, CYP7A1 repression and BSEP induction; dose/time observations must not be converted into unsourced kinetic constants.",
    ),
    "human_fxr_shp_regulation": SourceReference(
        id="human_fxr_shp_regulation",
        title="Human FXR regulates SHP expression through direct binding to an LRH-1 binding site",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC3912179/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Supports human FXR-to-SHP regulation and the SHP/LRH-1 links to CYP7A1 and NTCP regulation.",
    ),
    "human_cyp7a1_feedback": SourceReference(
        id="human_cyp7a1_feedback",
        title="Bile acids and cytokines inhibit the human cholesterol 7-alpha-hydroxylase gene via the JNK/c-Jun pathway",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC1526464/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Primary human hepatocyte data support bile-acid-dependent CYP7A1 repression and show that human regulation is not reducible to a single FXR-SHP edge.",
    ),
    "human_hnf4a_cyp7a1": SourceReference(
        id="human_hnf4a_cyp7a1",
        title="Retinoic acid represses CYP7A1 expression in human hepatocytes and HepG2 cells",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC2903807/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Supports HNF4A as a major positive CYP7A1 transcriptional regulator and parallel FXR/SHP and FGF19 feedback mechanisms.",
    ),
}


@dataclass(frozen=True)
class GeneProgramDefinition:
    symbol: str
    product: str
    role: str
    protein_location: str
    coupling_target: str
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class GeneRegulatoryEdge:
    id: str
    regulator: str
    target_gene: str
    target_layer: RegulatoryLayer
    effect: RegulatoryEffect
    mechanism: str
    biological_context: str
    quantification_status: str
    source_ids: tuple[str, ...]
    notes: str = ""


@dataclass(frozen=True)
class GeneExpressionKineticProfile:
    gene_symbol: str
    promoter_on_rate_per_s: float
    promoter_off_rate_per_s: float
    transcription_rate_per_active_allele_per_s: float
    splicing_rate_per_s: float
    nuclear_export_rate_per_s: float
    cytoplasmic_mrna_decay_rate_per_s: float
    translation_rate_per_mrna_per_s: float
    protein_decay_rate_per_s: float
    calibration_status: KineticCalibrationStatus
    biological_system: str
    assay: str
    evidence: str
    source_ids: tuple[str, ...]
    notes: str = ""


CHOLESTASIS_GENE_PROGRAM: tuple[GeneProgramDefinition, ...] = (
    GeneProgramDefinition("HNF4A", "hepatocyte nuclear factor 4 alpha", "hepatocyte identity control", "nucleus", "hepatocyte_identity", ("ncbi_gene_records",)),
    GeneProgramDefinition("NR1H4", "farnesoid X receptor (FXR)", "bile-acid sensing and transcriptional regulation", "nucleus", "bile_acid_feedback", ("ncbi_gene_records",)),
    GeneProgramDefinition("NR0B2", "small heterodimer partner (SHP)", "nuclear-receptor coregulation", "nucleus", "cyp7a1_feedback", ("ncbi_gene_records",)),
    GeneProgramDefinition("CYP7A1", "cholesterol 7 alpha-hydroxylase", "rate-limiting classical bile-acid synthesis step", "smooth_er", "bile_acid_synthesis", ("ncbi_gene_records",)),
    GeneProgramDefinition("SLC10A1", "NTCP", "sinusoidal bile-acid uptake", "sinusoidal_face", "ntcp_surface_activity", ("ncbi_gene_records", "transporter_copy_numbers")),
    GeneProgramDefinition("ABCB11", "BSEP", "canalicular bile-acid export", "canalicular_face", "bsep_surface_activity", ("ncbi_gene_records", "transporter_copy_numbers")),
    GeneProgramDefinition("ABCC2", "MRP2", "canalicular conjugate export", "canalicular_face", "mrp2_surface_activity", ("ncbi_gene_records", "transporter_copy_numbers")),
)


GENE_REGULATORY_EDGES: tuple[GeneRegulatoryEdge, ...] = (
    GeneRegulatoryEdge(
        "bile-acid-fxr-activation", "bile_acids", "NR1H4", "functional_protein", "activates",
        "Bile acids act as FXR ligands.", "primary human hepatocyte culture", "qualitative_direction_only",
        ("phh_bile_acid_gene_regulation",),
    ),
    GeneRegulatoryEdge(
        "fxr-shp-induction", "activated_NR1H4", "NR0B2", "promoter", "activates",
        "Ligand-activated human FXR induces SHP expression.", "human liver-derived and primary hepatocyte evidence", "qualitative_direction_only",
        ("human_fxr_shp_regulation", "phh_bile_acid_gene_regulation"),
    ),
    GeneRegulatoryEdge(
        "fxr-bsep-induction", "activated_NR1H4", "ABCB11", "promoter", "activates",
        "FXR activation induces BSEP expression.", "primary human hepatocyte culture", "qualitative_direction_only",
        ("phh_bile_acid_gene_regulation", "human_fxr_shp_regulation"),
    ),
    GeneRegulatoryEdge(
        "shp-cyp7a1-repression", "NR0B2", "CYP7A1", "promoter", "represses",
        "SHP interferes with positive nuclear-receptor control of CYP7A1.", "human hepatocyte regulatory evidence", "qualitative_direction_only",
        ("human_fxr_shp_regulation", "human_hnf4a_cyp7a1"),
        "FGF19/FGFR4/JNK is a parallel and potentially dominant human pathway; this edge cannot stand in for the complete feedback system.",
    ),
    GeneRegulatoryEdge(
        "hnf4a-cyp7a1-activation", "HNF4A", "CYP7A1", "promoter", "activates",
        "HNF4A is a major positive transcriptional regulator of CYP7A1.", "primary human hepatocyte and human liver-derived evidence", "qualitative_direction_only",
        ("human_hnf4a_cyp7a1",),
    ),
    GeneRegulatoryEdge(
        "fgf19-jun-cyp7a1-repression", "FGF19_FGFR4_JNK", "CYP7A1", "promoter", "represses",
        "FGF19/FGFR4 signalling and JNK/c-Jun repress human CYP7A1 transcription.", "primary human hepatocyte evidence", "qualitative_direction_only",
        ("human_cyp7a1_feedback", "phh_bile_acid_gene_regulation"),
        "FGF19, FGFR4 and JNK are boundary nodes in milestone 2, not yet dynamic gene products in the seven-gene slice.",
    ),
)


@dataclass(frozen=True)
class GeneExpressionState:
    gene_symbol: str
    product: str
    role: str
    coupling_target: str
    allele_copies: float
    functional_dosage_scale: float
    active_allele_count: float | None
    promoter_state: PromoterState
    chromatin_state: ChromatinState
    nuclear_pre_mrna_count: float | None
    nuclear_mature_mrna_count: float | None
    cytoplasmic_mrna_count: float | None
    total_protein_count: float | None
    functional_protein_scale: float | None
    protein_location: str
    evidence_status: ExpressionEvidenceStatus
    source_ids: tuple[str, ...]
    notes: str = ""


@dataclass(frozen=True)
class ExpressionEventRecord:
    id: str
    t_s: float
    gene_symbol: str
    event_type: str
    changed_fields: tuple[str, ...]
    source_id: str
    evidence: str
    notes: str = ""


@dataclass(frozen=True)
class GeneExpressionProgramState:
    program_id: str
    genes: dict[str, GeneExpressionState]
    events: tuple[ExpressionEventRecord, ...]
    kinetics_status: str
    engine_mode: str
    kinetic_profiles: dict[str, GeneExpressionKineticProfile]
    regulatory_edges: tuple[GeneRegulatoryEdge, ...]
    regulatory_status: str
    source_ids: tuple[str, ...]
    notes: str = ""

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


@dataclass(frozen=True)
class ObservedExpressionUpdate:
    id: str
    t_s: float
    gene_symbol: str
    event_type: str
    source_id: str
    evidence: str
    promoter_state: PromoterState | None = None
    chromatin_state: ChromatinState | None = None
    functional_dosage_scale: float | None = None
    active_allele_count: float | None = None
    nuclear_pre_mrna_count: float | None = None
    nuclear_mature_mrna_count: float | None = None
    cytoplasmic_mrna_count: float | None = None
    total_protein_count: float | None = None
    functional_protein_scale: float | None = None
    evidence_status: ExpressionEvidenceStatus | None = None
    notes: str = ""


def build_initial_hepatocyte_expression(
    genome: HepatocyteGenomeState,
) -> GeneExpressionProgramState:
    loci = {locus.symbol: locus for locus in genome.functional_loci}
    missing = {definition.symbol for definition in CHOLESTASIS_GENE_PROGRAM} - set(loci)
    if missing:
        raise ValueError(f"expression program is missing genome loci: {sorted(missing)}")

    allele_copies = genome.total_chromosome_sets
    protein_anchors = {
        "SLC10A1": PROTEIN_BY_ID["ntcp"].copies_typical,
        "ABCB11": PROTEIN_BY_ID["bsep"].copies_typical,
        "ABCC2": PROTEIN_BY_ID["mrp2"].copies_typical,
    }
    genes: dict[str, GeneExpressionState] = {}
    for definition in CHOLESTASIS_GENE_PROGRAM:
        protein_count = protein_anchors.get(definition.symbol)
        genes[definition.symbol] = GeneExpressionState(
            gene_symbol=definition.symbol,
            product=definition.product,
            role=definition.role,
            coupling_target=definition.coupling_target,
            allele_copies=allele_copies,
            functional_dosage_scale=1.0,
            active_allele_count=None,
            promoter_state="unknown",
            chromatin_state="unknown",
            nuclear_pre_mrna_count=None,
            nuclear_mature_mrna_count=None,
            cytoplasmic_mrna_count=None,
            total_protein_count=protein_count,
            functional_protein_scale=(1.0 if protein_count is not None else None),
            protein_location=definition.protein_location,
            evidence_status=("literature_derived" if protein_count is not None else "unknown"),
            source_ids=definition.source_ids + ("expression_unknown_policy",),
            notes=(
                "Protein count is an order-of-magnitude total-abundance anchor; functional scale 1 is the normalized healthy reference, not a measured surface fraction."
                if protein_count is not None
                else "Gene-specific RNA counts, promoter kinetics and protein abundance are not calibrated."
            ),
        )
    return GeneExpressionProgramState(
        program_id="hepatocyte_cholestasis_expression_v1",
        genes=genes,
        events=(),
        kinetics_status="gene_specific_kinetics_not_calibrated",
        engine_mode="calibration_gated_exact_ssa",
        kinetic_profiles={},
        regulatory_edges=GENE_REGULATORY_EDGES,
        regulatory_status="source_backed_qualitative_graph_no_autonomous_regulatory_inference",
        source_ids=("ncbi_gene_records", "genomic_burst_kinetics", "primary_hepatocyte_protein_turnover", "expression_unknown_policy", "phh_bile_acid_gene_regulation", "human_fxr_shp_regulation", "human_cyp7a1_feedback", "human_hnf4a_cyp7a1"),
        notes="Seven-gene vertical slice. Missing values remain null and generate no stochastic event.",
    )


def apply_observed_expression_update(
    program: GeneExpressionProgramState,
    update: ObservedExpressionUpdate,
) -> GeneExpressionProgramState:
    if update.gene_symbol not in program.genes:
        raise ValueError(f"unknown expression-program gene: {update.gene_symbol}")
    if not update.source_id or not update.evidence:
        raise ValueError("expression updates require source_id and evidence")
    if update.id in {event.id for event in program.events}:
        existing = next(event for event in program.events if event.id == update.id)
        if existing.gene_symbol == update.gene_symbol and existing.event_type == update.event_type:
            return program
        raise ValueError(f"duplicate expression event id: {update.id}")

    fields = (
        "functional_dosage_scale",
        "active_allele_count",
        "nuclear_pre_mrna_count",
        "nuclear_mature_mrna_count",
        "cytoplasmic_mrna_count",
        "total_protein_count",
        "functional_protein_scale",
    )
    for field_name in fields:
        value = getattr(update, field_name)
        if value is not None and (not isfinite(value) or value < 0):
            raise ValueError(f"{field_name} must be finite and non-negative")
    replacements = {
        field_name: getattr(update, field_name)
        for field_name in fields
        if getattr(update, field_name) is not None
    }
    if update.promoter_state is not None:
        replacements["promoter_state"] = update.promoter_state
    if update.chromatin_state is not None:
        replacements["chromatin_state"] = update.chromatin_state
    if update.evidence_status is not None:
        replacements["evidence_status"] = update.evidence_status
    if not replacements:
        raise ValueError("expression update must change at least one state field")

    genes = dict(program.genes)
    genes[update.gene_symbol] = replace(genes[update.gene_symbol], **replacements)
    event = ExpressionEventRecord(
        id=update.id,
        t_s=update.t_s,
        gene_symbol=update.gene_symbol,
        event_type=update.event_type,
        changed_fields=tuple(replacements),
        source_id=update.source_id,
        evidence=update.evidence,
        notes=update.notes,
    )
    return replace(program, genes=genes, events=program.events + (event,))


def register_kinetic_profile(
    program: GeneExpressionProgramState,
    profile: GeneExpressionKineticProfile,
) -> GeneExpressionProgramState:
    if profile.gene_symbol not in program.genes:
        raise ValueError(f"unknown expression-program gene: {profile.gene_symbol}")
    rates = (
        profile.promoter_on_rate_per_s,
        profile.promoter_off_rate_per_s,
        profile.transcription_rate_per_active_allele_per_s,
        profile.splicing_rate_per_s,
        profile.nuclear_export_rate_per_s,
        profile.cytoplasmic_mrna_decay_rate_per_s,
        profile.translation_rate_per_mrna_per_s,
        profile.protein_decay_rate_per_s,
    )
    if any(not isfinite(rate) or rate <= 0 for rate in rates):
        raise ValueError("gene-expression kinetic rates must be finite and positive")
    if not profile.biological_system or not profile.assay or not profile.evidence or not profile.source_ids:
        raise ValueError("kinetic profiles require biological system, assay, evidence and source IDs")
    profiles = dict(program.kinetic_profiles)
    profiles[profile.gene_symbol] = profile
    runnable = sum(item.calibration_status == "matched_human_hepatocyte" for item in profiles.values())
    return replace(
        program,
        kinetic_profiles=profiles,
        kinetics_status=f"{runnable}_matched_human_hepatocyte_profiles_runnable",
    )


def apply_regulatory_observation(
    program: GeneExpressionProgramState,
    *,
    edge_id: str,
    promoter_state: PromoterState,
    event_id: str,
    t_s: float,
    source_id: str,
    evidence: str,
) -> GeneExpressionProgramState:
    edge = next((item for item in program.regulatory_edges if item.id == edge_id), None)
    if edge is None:
        raise ValueError(f"unknown regulatory edge: {edge_id}")
    if edge.target_layer != "promoter":
        raise ValueError(f"regulatory edge {edge_id} does not target a promoter")
    if source_id not in edge.source_ids:
        raise ValueError(f"regulatory observation source is not registered for edge {edge_id}")
    return apply_observed_expression_update(
        program,
        ObservedExpressionUpdate(
            id=event_id,
            t_s=t_s,
            gene_symbol=edge.target_gene,
            event_type="regulatory_observation",
            source_id=source_id,
            evidence=evidence,
            promoter_state=promoter_state,
            evidence_status="measured",
            notes=f"Observed through regulatory edge {edge_id}; no downstream RNA count is inferred.",
        ),
    )


def apply_functional_perturbation(
    program: GeneExpressionProgramState,
    *,
    gene_symbol: str,
    activity_scale: float,
    event_id: str,
    t_s: float,
    source_id: str,
    evidence: str,
) -> GeneExpressionProgramState:
    return apply_observed_expression_update(
        program,
        ObservedExpressionUpdate(
            id=event_id,
            t_s=t_s,
            gene_symbol=gene_symbol,
            event_type="functional_perturbation",
            source_id=source_id,
            evidence=evidence,
            functional_protein_scale=activity_scale,
            evidence_status="experimental_control",
            notes="Functional experiment changes activity without inventing a variant coordinate, RNA count or total-protein change.",
        ),
    )
