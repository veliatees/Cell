from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Literal

from cell_engine.core.provenance import SourceReference

GenomeVariantType = Literal[
    "snv",
    "insertion",
    "deletion",
    "copy_number",
    "structural_variant",
    "mtDNA_variant",
]


GENOME_SOURCES: dict[str, SourceReference] = {
    "ncbi_grch38_p14": SourceReference(
        id="ncbi_grch38_p14",
        title="Human Genome Assembly GRCh38.p14",
        url="https://www.ncbi.nlm.nih.gov/grc/human/data",
        source_type="database",
        date_verified="2026-07-10",
        notes=(
            "GRC/NCBI chromosome lengths and RefSeq accessions. Chromosome lengths "
            "are placed-scaffold lengths including estimated gaps."
        ),
    ),
    "ncbi_mtdna_rcrs": SourceReference(
        id="ncbi_mtdna_rcrs",
        title="Homo sapiens mitochondrion, complete genome (NC_012920.1)",
        url="https://www.ncbi.nlm.nih.gov/nuccore/NC_012920.1",
        source_type="database",
        date_verified="2026-07-10",
        notes="Revised Cambridge Reference Sequence; 16,569 bp reference molecule.",
    ),
    "ncbi_gene_records": SourceReference(
        id="ncbi_gene_records",
        title="NCBI Gene, Homo sapiens GRCh38.p14 annotation",
        url="https://www.ncbi.nlm.nih.gov/gene/",
        source_type="database",
        date_verified="2026-07-10",
        notes="Coordinates use annotation release RS_2025_08 on GCF_000001405.40.",
    ),
}


@dataclass(frozen=True)
class ChromosomeReference:
    name: str
    refseq_accession: str
    length_bp: int
    chromosome_type: Literal["autosome", "sex_chromosome"]


# GRC placed-scaffold lengths for GRCh38.p14. The patch release does not imply
# that an individual cell carries the reference alleles.
GRCH38_P14_CHROMOSOMES: tuple[ChromosomeReference, ...] = (
    ChromosomeReference("1", "NC_000001.11", 248_956_422, "autosome"),
    ChromosomeReference("2", "NC_000002.12", 242_193_529, "autosome"),
    ChromosomeReference("3", "NC_000003.12", 198_295_559, "autosome"),
    ChromosomeReference("4", "NC_000004.12", 190_214_555, "autosome"),
    ChromosomeReference("5", "NC_000005.10", 181_538_259, "autosome"),
    ChromosomeReference("6", "NC_000006.12", 170_805_979, "autosome"),
    ChromosomeReference("7", "NC_000007.14", 159_345_973, "autosome"),
    ChromosomeReference("8", "NC_000008.11", 145_138_636, "autosome"),
    ChromosomeReference("9", "NC_000009.12", 138_394_717, "autosome"),
    ChromosomeReference("10", "NC_000010.11", 133_797_422, "autosome"),
    ChromosomeReference("11", "NC_000011.10", 135_086_622, "autosome"),
    ChromosomeReference("12", "NC_000012.12", 133_275_309, "autosome"),
    ChromosomeReference("13", "NC_000013.11", 114_364_328, "autosome"),
    ChromosomeReference("14", "NC_000014.9", 107_043_718, "autosome"),
    ChromosomeReference("15", "NC_000015.10", 101_991_189, "autosome"),
    ChromosomeReference("16", "NC_000016.10", 90_338_345, "autosome"),
    ChromosomeReference("17", "NC_000017.11", 83_257_441, "autosome"),
    ChromosomeReference("18", "NC_000018.10", 80_373_285, "autosome"),
    ChromosomeReference("19", "NC_000019.10", 58_617_616, "autosome"),
    ChromosomeReference("20", "NC_000020.11", 64_444_167, "autosome"),
    ChromosomeReference("21", "NC_000021.9", 46_709_983, "autosome"),
    ChromosomeReference("22", "NC_000022.11", 50_818_468, "autosome"),
    ChromosomeReference("X", "NC_000023.11", 156_040_895, "sex_chromosome"),
    ChromosomeReference("Y", "NC_000024.10", 57_227_415, "sex_chromosome"),
)


@dataclass(frozen=True)
class FunctionalGeneLocus:
    symbol: str
    ncbi_gene_id: str
    ensembl_gene_id: str
    chromosome: str
    start_bp: int
    end_bp: int
    strand: Literal["plus", "minus"]
    simulation_role: str
    source_url: str


# This is a simulation-facing index, not a claim that only these genes matter.
# Coordinates were read from NCBI Gene's current GRCh38.p14 annotation.
HEPATOCYTE_FUNCTIONAL_LOCI: tuple[FunctionalGeneLocus, ...] = (
    FunctionalGeneLocus("ABCB11", "8647", "ENSG00000073734", "2", 168_915_391, 169_031_325, "minus", "BSEP canalicular bile-acid export", "https://www.ncbi.nlm.nih.gov/gene/8647"),
    FunctionalGeneLocus("ABCC2", "1244", "ENSG00000023839", "10", 99_782_641, 99_852_595, "plus", "MRP2 canalicular conjugate export", "https://www.ncbi.nlm.nih.gov/gene/1244"),
    FunctionalGeneLocus("SLC10A1", "6554", "ENSG00000100652", "14", 69_775_417, 69_797_242, "minus", "NTCP sinusoidal bile-acid uptake", "https://www.ncbi.nlm.nih.gov/gene/6554"),
    FunctionalGeneLocus("SLC2A2", "6514", "ENSG00000163581", "3", 170_996_348, 171_026_721, "minus", "GLUT2 bidirectional glucose transport", "https://www.ncbi.nlm.nih.gov/gene/6514"),
    FunctionalGeneLocus("ALB", "213", "ENSG00000163631", "4", 73_404_288, 73_421_483, "plus", "albumin synthesis and secretion", "https://www.ncbi.nlm.nih.gov/gene/213"),
    FunctionalGeneLocus("CPS1", "1373", "ENSG00000021826", "2", 210_477_686, 210_679_108, "plus", "mitochondrial urea-cycle entry", "https://www.ncbi.nlm.nih.gov/gene/1373"),
    FunctionalGeneLocus("CYP7A1", "1581", "ENSG00000167910", "8", 58_490_179, 58_500_164, "minus", "classic bile-acid synthesis", "https://www.ncbi.nlm.nih.gov/gene/1581"),
    FunctionalGeneLocus("NR1H4", "9971", "ENSG00000012504", "12", 100_473_866, 100_564_414, "plus", "FXR bile-acid sensing and transcriptional regulation", "https://www.ncbi.nlm.nih.gov/gene/9971"),
    FunctionalGeneLocus("NR0B2", "8431", "ENSG00000131910", "1", 26_911_489, 26_913_975, "minus", "SHP nuclear-receptor coregulator in bile-acid feedback", "https://www.ncbi.nlm.nih.gov/gene/8431"),
    FunctionalGeneLocus("HNF4A", "3172", "ENSG00000101076", "20", 44_355_700, 44_434_597, "plus", "hepatocyte identity transcriptional control", "https://www.ncbi.nlm.nih.gov/gene/3172"),
    FunctionalGeneLocus("TP53", "7157", "ENSG00000141510", "17", 7_668_422, 7_687_491, "minus", "DNA-damage and fate control", "https://www.ncbi.nlm.nih.gov/gene/7157"),
    FunctionalGeneLocus("CDKN1A", "1026", "ENSG00000124762", "6", 36_676_464, 36_687_333, "plus", "p21 cell-cycle arrest", "https://www.ncbi.nlm.nih.gov/gene/1026"),
    FunctionalGeneLocus("DNMT1", "1786", "ENSG00000130816", "19", 10_133_347, 10_194_954, "minus", "maintenance DNA methylation", "https://www.ncbi.nlm.nih.gov/gene/1786"),
    FunctionalGeneLocus("UHRF1", "29128", "ENSG00000276043", "19", 4_903_081, 4_962_155, "plus", "replication-coupled epigenetic maintenance", "https://www.ncbi.nlm.nih.gov/gene/29128"),
    FunctionalGeneLocus("TET2", "54790", "ENSG00000168769", "4", 105_145_876, 105_279_804, "plus", "DNA demethylation pathway", "https://www.ncbi.nlm.nih.gov/gene/54790"),
)


@dataclass(frozen=True)
class SomaticVariantRecord:
    id: str
    chromosome: str
    position_bp: int
    variant_type: GenomeVariantType
    reference: str | None
    alternate: str | None
    observed_time_s: float
    source_id: str
    evidence: str
    allele_fraction: float | None = None
    affected_gene: str | None = None
    notes: str = ""


@dataclass(frozen=True)
class MitochondrialGenomeState:
    reference_accession: str = "NC_012920.1"
    reference_length_bp: int = 16_569
    copy_number: int | None = None
    heteroplasmy_status: str = "not_measured"
    variants: tuple[SomaticVariantRecord, ...] = ()
    source_ids: tuple[str, ...] = ("ncbi_mtdna_rcrs",)


@dataclass(frozen=True)
class HepatocyteGenomeState:
    assembly_name: str
    assembly_accession: str
    annotation_release: str
    primary_assembly_length_bp: int
    all_scaffolds_length_bp: int
    chromosomes: tuple[ChromosomeReference, ...]
    functional_loci: tuple[FunctionalGeneLocus, ...]
    chromosome_sets_per_nucleus: tuple[float, ...]
    sex_chromosome_complement: str
    individual_genotype_status: str
    somatic_variants: tuple[SomaticVariantRecord, ...] = ()
    mitochondrial: MitochondrialGenomeState = field(default_factory=MitochondrialGenomeState)
    source_ids: tuple[str, ...] = ("ncbi_grch38_p14", "ncbi_gene_records", "ncbi_mtdna_rcrs")
    notes: str = ""

    @property
    def nuclei(self) -> int:
        return len(self.chromosome_sets_per_nucleus)

    @property
    def total_chromosome_sets(self) -> float:
        return sum(self.chromosome_sets_per_nucleus)


def build_reference_hepatocyte_genome(
    chromosome_sets_per_nucleus: tuple[float, ...] = (2.0,),
) -> HepatocyteGenomeState:
    if not chromosome_sets_per_nucleus or any(value <= 0 for value in chromosome_sets_per_nucleus):
        raise ValueError("chromosome sets per nucleus must be positive")
    return HepatocyteGenomeState(
        assembly_name="GRCh38.p14",
        assembly_accession="GCF_000001405.40",
        annotation_release="RS_2025_08",
        primary_assembly_length_bp=3_088_269_832,
        all_scaffolds_length_bp=3_099_734_149,
        chromosomes=GRCH38_P14_CHROMOSOMES,
        functional_loci=HEPATOCYTE_FUNCTIONAL_LOCI,
        chromosome_sets_per_nucleus=chromosome_sets_per_nucleus,
        sex_chromosome_complement="not_provided",
        individual_genotype_status="not_provided_reference_coordinates_only",
        notes=(
            "Reference coordinates are not an individual genotype. No inherited or somatic "
            "variant is assumed until a measured record is supplied."
        ),
    )


def record_somatic_variant(
    genome: HepatocyteGenomeState,
    variant: SomaticVariantRecord,
) -> HepatocyteGenomeState:
    """Add an observed variant without inventing a mutation process or rate."""
    if not variant.source_id or not variant.evidence:
        raise ValueError("a somatic variant requires a source_id and evidence description")
    if variant.allele_fraction is not None and not 0.0 <= variant.allele_fraction <= 1.0:
        raise ValueError("allele_fraction must be in [0, 1]")
    all_variant_ids = {
        existing.id
        for existing in genome.somatic_variants + genome.mitochondrial.variants
    }
    if variant.id in all_variant_ids:
        raise ValueError(f"duplicate somatic variant id: {variant.id}")
    chromosome = next((item for item in genome.chromosomes if item.name == variant.chromosome), None)
    if variant.chromosome == "MT":
        if not 1 <= variant.position_bp <= genome.mitochondrial.reference_length_bp:
            raise ValueError("mtDNA variant coordinate is outside NC_012920.1")
        mitochondrial = replace(
            genome.mitochondrial,
            variants=genome.mitochondrial.variants + (variant,),
            heteroplasmy_status=(
                "measured" if variant.allele_fraction is not None else "variant_observed_fraction_not_measured"
            ),
        )
        return replace(genome, mitochondrial=mitochondrial)
    if chromosome is None:
        raise ValueError(f"unknown chromosome: {variant.chromosome}")
    if not 1 <= variant.position_bp <= chromosome.length_bp:
        raise ValueError(f"variant coordinate is outside chromosome {variant.chromosome}")
    return replace(genome, somatic_variants=genome.somatic_variants + (variant,))
