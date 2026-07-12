from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from cell_engine.core.genome import HepatocyteGenomeState
from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain


ObservationStatus = Literal["measured", "reference_only", "not_measured"]
MilestoneScientificStatus = Literal["validated", "implemented_data_required", "reference_only"]

DATE_VERIFIED = "2026-07-10"

GENOMIC_ARCHITECTURE_SOURCES: dict[str, SourceReference] = {
    "human_liver_cell_atlas": SourceReference(
        id="human_liver_cell_atlas",
        title="A human liver cell atlas reveals heterogeneity and epithelial progenitors",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC6687507/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Single-cell RNA-seq of about 10,000 cells from nine human donors supports donor-aware hepatocyte heterogeneity and zonation.",
    ),
    "gtex_v8": SourceReference(
        id="gtex_v8",
        title="NIH Genotype-Tissue Expression project, data release V8",
        url="https://commonfund.nih.gov/GTEx",
        source_type="database",
        date_verified=DATE_VERIFIED,
        notes="Bulk tissue reference; liver values are not single-hepatocyte molecule counts and require cell-composition-aware interpretation.",
    ),
    "human_liver_multiome": SourceReference(
        id="human_liver_multiome",
        title="Liver single-nucleus multiome profiling reveals cell-type mechanisms for cardiometabolic traits",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC12805840/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Human liver single-nucleus RNA plus ATAC data support joint expression/chromatin state while preserving donor and cell-type context.",
    ),
}


@dataclass(frozen=True)
class GeneModuleState:
    id: str
    label: str
    member_genes: tuple[str, ...]
    explicit_expression_genes: tuple[str, ...]
    representation_mode: str
    dynamic_status: str
    source_ids: tuple[str, ...]
    notes: str = ""


@dataclass(frozen=True)
class EpigeneticLocusState:
    gene_symbol: str
    chromatin_accessibility: Literal["open", "closed", "poised", "unknown"]
    dna_methylation_fraction: float | None
    histone_marks: dict[str, float]
    observation_status: ObservationStatus
    biological_system: str
    assay: str
    source_ids: tuple[str, ...]
    notes: str = ""


@dataclass(frozen=True)
class OmicsDatasetRecord:
    id: str
    assay_type: str
    biological_system: str
    donor_or_cohort: str
    genome_assembly: str
    normalization: str
    observed_genes: tuple[str, ...]
    source_ids: tuple[str, ...]
    evidence: str
    use: Literal["calibration", "validation", "reference_only"]
    notes: str = ""


@dataclass(frozen=True)
class VariantFunctionalLink:
    id: str
    variant_id: str
    target_gene_or_module: str
    effect_layer: str
    observed_effect: str
    evidence_status: str
    experimental_system: str
    source_ids: tuple[str, ...]
    notes: str = ""


@dataclass(frozen=True)
class CellIdentityContext:
    species: str
    cell_type: str
    zonation: str
    donor_id: str
    donor_age: str
    donor_sex: str
    tissue_health: str
    genotype_status: str
    clone_id: str
    identity_status: str
    source_ids: tuple[str, ...]
    notes: str = ""


@dataclass(frozen=True)
class GenomicMilestoneStatus:
    milestone: int
    title: str
    software_complete: bool
    scientific_status: MilestoneScientificStatus
    implemented_capabilities: tuple[str, ...]
    data_requirements: tuple[str, ...]


@dataclass(frozen=True)
class GenomicArchitectureState:
    architecture_id: str
    gene_modules: tuple[GeneModuleState, ...]
    epigenetic_loci: dict[str, EpigeneticLocusState]
    omics_datasets: tuple[OmicsDatasetRecord, ...]
    variant_functional_links: tuple[VariantFunctionalLink, ...]
    identity: CellIdentityContext
    milestones: tuple[GenomicMilestoneStatus, ...]
    source_ids: tuple[str, ...]
    notes: str = ""

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def build_genomic_architecture(
    genome: HepatocyteGenomeState,
    *,
    zonation: str,
) -> GenomicArchitectureState:
    locus_symbols = tuple(locus.symbol for locus in genome.functional_loci)
    expression_symbols = frozenset({"HNF4A", "NR1H4", "NR0B2", "CYP7A1", "SLC10A1", "ABCB11", "ABCC2"})
    modules = (
        _module("bile_acid_homeostasis", "Bile-acid synthesis, sensing and transport", ("HNF4A", "NR1H4", "NR0B2", "CYP7A1", "SLC10A1", "ABCB11", "ABCC2"), expression_symbols),
        _module("hepatic_identity_and_secretion", "Hepatocyte identity and secretion", ("HNF4A", "ALB"), expression_symbols),
        _module("glucose_homeostasis", "Bidirectional glucose handling", ("SLC2A2",), expression_symbols),
        _module("nitrogen_disposal", "Urea-cycle entry", ("CPS1",), expression_symbols),
        _module("damage_checkpoint", "DNA-damage checkpoint and arrest", ("TP53", "CDKN1A"), expression_symbols),
        _module("epigenetic_maintenance", "DNA methylation maintenance and removal", ("DNMT1", "UHRF1", "TET2"), expression_symbols),
    )
    epigenetic = {
        symbol: EpigeneticLocusState(
            gene_symbol=symbol,
            chromatin_accessibility="unknown",
            dna_methylation_fraction=None,
            histone_marks={},
            observation_status="not_measured",
            biological_system="not_provided",
            assay="not_provided",
            source_ids=("human_liver_multiome",),
            notes="No donor-matched locus measurement is loaded; reference atlases do not define this cell's epigenetic state.",
        )
        for symbol in locus_symbols
    }
    identity = CellIdentityContext(
        species="Homo sapiens",
        cell_type="hepatocyte",
        zonation=zonation,
        donor_id="not_provided",
        donor_age="not_provided",
        donor_sex="not_provided",
        tissue_health="reference_healthy_context_not_donor_observation",
        genotype_status=genome.individual_genotype_status,
        clone_id="founder-cell-no-clonal-inference",
        identity_status="reference_cell_context_with_unknown_donor",
        source_ids=("human_liver_cell_atlas",),
        notes="Zonation labels describe the simulation context; they are not inferred from a donor expression profile.",
    )
    return GenomicArchitectureState(
        architecture_id="hepatocyte_genome_program_v1",
        gene_modules=modules,
        epigenetic_loci=epigenetic,
        omics_datasets=(),
        variant_functional_links=(),
        identity=identity,
        milestones=_milestone_report(),
        source_ids=("ncbi_grch38_p14", "ncbi_gene_records", "human_liver_cell_atlas", "gtex_v8", "human_liver_multiome"),
        notes="All six software milestones are represented. Scientific validation remains per-dataset and per-parameter; missing donor data is never generated.",
    )


def record_epigenetic_observation(
    architecture: GenomicArchitectureState,
    observation: EpigeneticLocusState,
) -> GenomicArchitectureState:
    if observation.gene_symbol not in architecture.epigenetic_loci:
        raise ValueError(f"unknown epigenetic locus: {observation.gene_symbol}")
    if observation.observation_status != "measured":
        raise ValueError("recorded epigenetic observations must be measured")
    if not observation.biological_system or not observation.assay or not observation.source_ids:
        raise ValueError("epigenetic observations require biological system, assay and sources")
    if observation.dna_methylation_fraction is not None and not 0 <= observation.dna_methylation_fraction <= 1:
        raise ValueError("DNA methylation fraction must be in [0, 1]")
    if any(not 0 <= value <= 1 for value in observation.histone_marks.values()):
        raise ValueError("normalized histone-mark values must be in [0, 1]")
    loci = dict(architecture.epigenetic_loci)
    loci[observation.gene_symbol] = observation
    return replace(architecture, epigenetic_loci=loci)


def register_omics_dataset(
    architecture: GenomicArchitectureState,
    dataset: OmicsDatasetRecord,
) -> GenomicArchitectureState:
    if not dataset.id or not dataset.source_ids or not dataset.evidence:
        raise ValueError("omics datasets require identity, sources and evidence")
    if dataset.genome_assembly != "GRCh38.p14":
        raise ValueError("omics dataset must be explicitly lifted or aligned to GRCh38.p14")
    if any(item.id == dataset.id for item in architecture.omics_datasets):
        raise ValueError(f"duplicate omics dataset: {dataset.id}")
    return replace(architecture, omics_datasets=architecture.omics_datasets + (dataset,))


def link_variant_to_function(
    architecture: GenomicArchitectureState,
    genome: HepatocyteGenomeState,
    link: VariantFunctionalLink,
) -> GenomicArchitectureState:
    variant_ids = {item.id for item in genome.somatic_variants + genome.mitochondrial.variants}
    if link.variant_id not in variant_ids:
        raise ValueError("variant-functional link must reference an observed genome variant")
    if not link.source_ids or not link.experimental_system or not link.observed_effect:
        raise ValueError("variant-functional links require sources, system and observed effect")
    if any(item.id == link.id for item in architecture.variant_functional_links):
        raise ValueError(f"duplicate variant-functional link: {link.id}")
    return replace(architecture, variant_functional_links=architecture.variant_functional_links + (link,))


def _module(
    module_id: str,
    label: str,
    genes: tuple[str, ...],
    expression_symbols: frozenset[str],
) -> GeneModuleState:
    explicit = tuple(symbol for symbol in genes if symbol in expression_symbols)
    mode = "explicit_expression_states" if len(explicit) == len(genes) else "mixed_explicit_and_registry_only"
    return GeneModuleState(
        id=module_id,
        label=label,
        member_genes=genes,
        explicit_expression_genes=explicit,
        representation_mode=mode,
        dynamic_status="only calibrated explicit genes may evolve; registry-only members are structural",
        source_ids=("ncbi_gene_records",),
    )


def _milestone_report() -> tuple[GenomicMilestoneStatus, ...]:
    return (
        GenomicMilestoneStatus(1, "Reference genome to functional expression slice", True, "implemented_data_required", ("reference loci", "ploidy-aware alleles", "seven-gene expression state"), ("donor genotype",)),
        GenomicMilestoneStatus(2, "Calibration-gated central dogma and regulation", True, "implemented_data_required", ("compartmental RNA lifecycle", "exact SSA", "source-backed regulatory graph"), ("matched PHH gene-specific kinetics",)),
        GenomicMilestoneStatus(3, "Reduced transcriptome and proteome modules", True, "implemented_data_required", ("six functional gene modules", "omics dataset registry"), ("donor-aware scRNA/proteomics calibration",)),
        GenomicMilestoneStatus(4, "Genome and epigenome change", True, "implemented_data_required", ("observed variants", "locus epigenetic state", "variant-function links"), ("variant and epigenetic observations",)),
        GenomicMilestoneStatus(5, "Cell identity, heterogeneity and lineage", True, "implemented_data_required", ("donor/zone/clone context", "lineage-compatible state"), ("matched single-cell donor cohort",)),
        GenomicMilestoneStatus(6, "Validation and inference boundary", True, "implemented_data_required", ("calibration-versus-validation dataset roles", "per-milestone readiness report"), ("held-out PHH validation datasets", "uncertainty and identifiability analysis")),
    )

