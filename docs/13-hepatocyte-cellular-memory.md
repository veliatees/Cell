# Hepatocyte cellular memory: evidence and simulation contract

Date reviewed: 2026-07-10

## Scope and operational definition

In this project, **cellular memory** means that a past event changes a later
hepatocyte response after the original trigger has disappeared. A state is not
called memory merely because it changes slowly. At least one of the following
must be supported:

1. persistence after washout, recovery, cure, or diet reversal;
2. a changed response to a second exposure;
3. mitotic transmission to daughter hepatocytes;
4. a stable physical record such as a mutation or clonally inherited mtDNA
   variant.

Memory is therefore distinct from current signaling, current stress, and simple
elapsed time. The simulation must retain both the **event history** and the
**physical substrate that stores the trace**.

## Where information is physically stored

| Layer | Physical substrate | How an event writes information | How it is read later | Persistence and inheritance | Hepatocyte evidence |
|---|---|---|---|---|---|
| Nuclear genome | DNA sequence, structural variants, chromosome copy number | Replication errors, ROS/adduct damage that escapes repair, viral integration, chromosome mis-segregation | Altered gene dosage or sequence/function | Potentially lifelong; passed clonally at division | Strong human and mouse evidence |
| Nuclear DNA methylation | 5-methylcytosine at CpG sites | DNMT/TET activity changes after injury, diet, infection, differentiation, or regeneration | Methyl-CpG readers and altered TF access influence transcription | Can persist through quiescence; DNMT1/UHRF1 can copy patterns during replication, but fidelity is locus- and context-dependent | Strong liver evidence; hepatocyte specificity varies by study |
| Histones and chromatin | Nucleosomes, histone variants, H3K27ac, H3K27me3, H3K4me3, H3K14ac, accessibility and 3-D contacts | TF recruitment, acetyltransferases/methyltransferases, remodelers, DNA damage and inflammatory/metabolic signaling | Alters promoter/enhancer accessibility and response gain | Highly mark-, locus- and context-dependent; persistent marks are measured in selected liver contexts, while parental histone recycling can support mitotic inheritance in mammalian cells | Strong injury/regeneration evidence; no generic hepatocyte persistence time |
| Transcriptional network | TF abundance/localization, poised polymerase, mRNA and feedback loops | Receptor and stress pathways activate or repress transcription and feedback | Faster or stronger reactivation while the network or chromatin remains primed | Usually minutes to days; not long-term memory unless maintained by feedback or a stable chromatin state | Strong for liver response programs; persistence must be measured per program |
| Proteome and proteostasis | Long-lived proteins, PTMs, chaperones, aggregates, ubiquitinated cargo | Translation, oxidation, misfolding, aggregation, phosphorylation/acetylation and failed clearance | Changes enzyme capacity, signaling thresholds, ERAD/proteasome/autophagy load | Hours to days for many liver proteins; aggregates may persist longer; diluted or partitioned during division | Strong turnover evidence; hepatocyte aggregate inheritance is poorly quantified |
| Mitochondrial state | mtDNA sequence/heteroplasmy, copy number, respiratory complexes, membrane state, morphology and damage | Replication errors, ROS, selective mtDNA expansion, fission/fusion and incomplete mitophagy | Alters ATP, ROS, redox and death susceptibility | mtDNA variants can be long-lived; mitochondrial proteins and organelles turn over; mitochondria are partitioned at division | Strong liver-aging and turnover evidence; daughter-level partition distributions need calibration |
| Other organelles | ER folding capacity, lysosome/autophagy capacity, lipid droplets, peroxisomal damage | Repeated load changes organelle composition, cargo backlog and quality-control capacity | Alters the response to later protein, lipid, xenobiotic or oxidative load | Generally hours to days and reversible through turnover; division partitions the remaining state | Mechanistically strong, but quantitative long-term hepatocyte memory data are sparse |
| Metabolic state | Glycogen, lipids, NAD(H), NADP(H), glutathione, acetyl-CoA, SAM and other metabolites | Feeding, fasting, hypoxia, toxins and disease change pool sizes and fluxes | Immediate enzyme/allosteric effects; some metabolites influence chromatin-modifying enzymes | Seconds to hours for many pools; storage lipids/glycogen can persist longer. A metabolite is not long-term memory by itself | Strong state evidence; persistent memory requires downstream chromatin/proteome evidence |
| Senescent/damage state | Persistent DNA-damage response, p53/p21 or p16 programs, chromatin remodeling, lysosomal expansion and SASP-like output | Unrepaired damage, telomere dysfunction, oncogenic or chronic stress | Stable cell-cycle arrest and altered signaling/secretory behavior | Often long-lived; reversibility is context-dependent and cannot be represented by a universal switch | Strong general mechanism; hepatocyte timing and reversibility require context-specific data |
| Spatial/niche state | Canalicular polarity, ECM, sinusoidal position, oxygen/Wnt gradients and neighbor signals | Injury, matrix remodeling and cell displacement alter the local environment | External signals maintain zonation, identity and response thresholds | May persist without being intracellular or heritable | Strong liver evidence; must be modeled as environment history, not internal epigenetic memory |

## How a trace can cross cell division

Nuclear DNA sequence and chromosome dosage cross division through chromosome
replication and segregation. For DNA methylation, a daughter duplex initially
contains a methylated parental strand and a newly synthesized strand; maintenance
methylation machinery including DNMT1 acts after replication to restore methylation
on the new strand. The process is coupled to replication, but it is neither
instantaneous nor perfectly faithful at every CpG. Source:
[Dynamics of Dnmt1 interaction with the replication machinery](https://pmc.ncbi.nlm.nih.gov/articles/PMC1934996/).

Modified parental H3-H4 histones can be recycled onto newly synthesized daughter
DNA and help reconstruct chromatin state. Perturbing their balanced segregation
alters mitotic inheritance of histone modifications in mammalian embryonic stem
cells. This establishes a plausible physical inheritance mechanism, but it is not
a hepatocyte-specific inheritance probability and cannot calibrate every liver
locus. Source:
[Symmetric inheritance of parental histones governs epigenome maintenance](https://www.nature.com/articles/s41588-023-01476-x).

Soluble proteins, RNAs, metabolites and organelles instead cross division by
partition and dilution. Their daughter-cell distributions depend on abundance,
localization, organelle dynamics and division geometry; no general hepatocyte
partition probability was identified that could replace entity-specific data.

## Direct hepatocyte and liver evidence

### 1. Genetic and clonal memory

Single-cell whole-genome sequencing of primary human hepatocytes from healthy
donors aged 5 months to 77 years found an age-related rise in somatic base
substitutions, with aged hepatocytes reaching about 3.3-fold the burden of young
hepatocytes. This is a physical, permanent record, not a modeled stress score.
Source: [Zhang et al., Science Advances 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC6994209/).

Whole-genome sequencing of 482 laser-capture microdissections from normal and
cirrhotic human livers showed that mutations record toxicity, regeneration and
clonal structure. Cirrhotic liver contained higher mutation burdens, structural
variants and a patchwork of hepatocyte clones. Source:
[Brunner et al., Nature 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC6837891/).

Mature hepatocytes also change chromosome content. Mouse polyploid hepatocytes
can undergo multipolar division and ploidy reversal, producing daughters with
different chromosome complements. Therefore ploidy and chromosome dosage belong
to lineage state, not a transient stress field. Source:
[Duncan et al., Nature 2010](https://pubmed.ncbi.nlm.nih.gov/20861837/).

### 2. Persistent epigenetic scars after infection

Chronic HCV infection is one of the strongest human-liver examples of an
experience leaving a persistent molecular trace. H3K27ac ChIP-seq and RNA-seq
from human liver, together with humanized-liver mice, found HCV-associated
epigenetic and transcriptional changes that persisted after sustained virologic
response. The study included noninfected, chronic-HCV and cured human cohorts;
the trace was associated with pathways linked to residual HCC risk. Source:
[Hamdane et al., Gastroenterology 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC8756817/).

A separate study reported an HCV-induced histone-acetylation/gene-expression
signature that remained after direct-acting antiviral cure in experimental
systems and human biopsies. Source:
[Perez et al., PLOS Genetics 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC6602261/).

This supports an `epigenetic_scar` state for a specifically evidenced exposure.
It does **not** justify a generic rule that every infection or stress creates the
same permanent mark.

### 3. Diet and metabolic-history traces

In mouse liver, a substantial subset of high-fat-diet-induced chromatin
accessibility changes remained after diet reversal, supporting a persistent
metabolic-history trace. Source:
[Persistent Chromatin Modifications Induced by High Fat Diet](https://pubmed.ncbi.nlm.nih.gov/27006400/).

Other mouse work found many HFD-induced transcriptional and enhancer changes
reversed with weight loss. Source:
[Siersbæk et al., Scientific Reports 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5223143/).

The correct conclusion is therefore locus-specific and probabilistic: some
diet-induced states persist and others reset. Whole-liver measurements also mix
hepatocytes with non-parenchymal cells, so they cannot automatically become a
single-hepatocyte transition rate.

### 4. Regeneration and injury-induced chromatin remodeling

During mouse liver repopulation after toxic injury, hepatocyte chromatin opens
at cell-cycle regulatory regions while many liver-function enhancers become less
accessible. CTCF occupancy rises at promoters and HNF4α occupancy falls at many
enhancers. Source:
[The Dynamic Chromatin Architecture of the Regenerating Liver](https://pmc.ncbi.nlm.nih.gov/articles/PMC6909351/).

Partial hepatectomy induces programmed DNA-methylation changes and a temporary
progenitor-like regenerative program, followed by substantial return toward the
adult pattern as regeneration matures. Source:
[Hepatocyte regeneration is driven by embryo-like DNA methylation reprogramming](https://pmc.ncbi.nlm.nih.gov/articles/PMC11032470/).

Hepatocyte-specific UHRF1 loss alters DNA methylation and redistributes
H3K27me3, causing earlier and more sustained activation of pro-regenerative
genes after partial hepatectomy. Source:
[Epigenetic compensation promotes liver regeneration](https://pmc.ncbi.nlm.nih.gov/articles/PMC6615735/).

These studies establish a writable chromatin program controlling future
response capacity. They do not yet provide a universal scalar called
`regeneration_memory` or a measured decay half-life.

### 5. Stable injury-responsive hepatocyte states

Single-cell ATAC-seq and genetic perturbation show that YAP/TEAD-driven
chromatin remodeling participates in hepatocyte-to-biliary reprogramming after
injury, while HBO1/H3K14ac/ZMYND8 acts as an epigenetic barrier. Source:
[Yuan et al., Cell Stem Cell 2025](https://pubmed.ncbi.nlm.nih.gov/40403721/).

SOX9-expressing hybrid hepatocytes show a permissive chromatin landscape at
injury-responsive loci and distinct H3K27ac/H3K27me3-supported state programs.
This is evidence for priming in a defined hepatocyte subpopulation, not proof
that every hepatocyte stores inflammatory memory identically. Source:
[Chromatin State Distinguishes Injury-Responsive Programs, 2026](https://pubmed.ncbi.nlm.nih.gov/42146427/).

### 6. Mitochondrial and proteome memory

Single-cell mtDNA sequencing in mouse and human hepatocytes shows that selection
can accelerate accumulation of mitochondrial mutations with age. Source:
[Selection promotes age-dependent degeneration of the mitochondrial genome](https://pmc.ncbi.nlm.nih.gov/articles/PMC11463671/).

In vivo metabolic labeling measured a median half-life of about 4.26 days for
458 proteins in mouse hepatic mitochondria, with individual half-lives ranging
from hours to roughly 60 days. Source:
[Kim et al., Molecular & Cellular Proteomics 2012](https://pmc.ncbi.nlm.nih.gov/articles/PMC3518123/).

A later mouse study measured median hepatic mitochondrial-protein half-lives of
approximately 3.8 days for annotated mitochondrial proteins. Source:
[Liu et al., Scientific Reports 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10349111/).

Dynamic SILAC has also measured protein turnover directly in non-dividing
primary human hepatocytes, demonstrating that proteins occupy widely different
timescales. Source:
[Systematic analysis of protein turnover in primary cells](https://pmc.ncbi.nlm.nih.gov/articles/PMC5814408/).

These data justify protein-specific or protein-family turnover. They do not
justify one universal `protein_memory_half_life`.

## Hepatocyte life history and life-cycle states

The life cycle must not be implemented as a fixed countdown from birth to death.
Retrospective carbon-14 birth dating found continuous, lifelong hepatocyte
renewal in adult humans and an average hepatocyte age below three years. Diploid
hepatocytes had more than sevenfold higher annual birth rates than polyploid
hepatocytes. These are population-level renewal distributions, not proof that an
individual hepatocyte dies at a fixed age. Source:
[Diploid hepatocytes drive physiological liver renewal in adult humans](https://www.sciencedirect.com/science/article/pii/S2405471222001715).

At homeostasis, a mature hepatocyte is normally quiescent in `G0`, while retaining
the capacity to re-enter the cell cycle. Injury or loss of liver mass can produce
a priming phase associated with TNF-alpha/IL-6 signaling, followed by growth-factor
signals including HGF/c-MET and EGFR ligands, cell-cycle entry, DNA synthesis and
mitosis. Once regeneration is complete, surviving cells can return to quiescence.
This sequence is well established, but the quantitative timing depends on species,
injury model and tissue context. Source:
[Cellular and Molecular Basis of Liver Regeneration](https://pmc.ncbi.nlm.nih.gov/articles/PMC7108750/).

A completed DNA-replication event does not guarantee two diploid daughters.
Rodent hepatocytes can fail cytokinesis and generate a binucleated tetraploid
cell; insulin/PI3K/AKT signaling participates in that developmental program.
Polyploid hepatocytes can also divide, reverse ploidy and generate daughters with
different chromosome complements. Sources:
[The insulin/Akt pathway controls a specific cell division program](https://pmc.ncbi.nlm.nih.gov/articles/PMC2701880/) and
[The ploidy conveyor of mature hepatocytes](https://pubmed.ncbi.nlm.nih.gov/20861837/).

The simulation therefore needs the following explicit states and outcomes:

1. `quiescent_G0`: metabolically active, non-cycling mature hepatocyte;
2. `primed`: competent to enter the cycle, but not yet committed to DNA synthesis;
3. `G1`, `S`, `G2`, `M`: explicit cycle phases only when experimentally supported
   timing is selected;
4. `cytokinesis`: an outcome event, with successful division, failed cytokinesis,
   endoreplication or abnormal segregation represented separately;
5. `post_mitotic_recovery`: polarity, organelle and metabolic re-establishment
   before return to `quiescent_G0`;
6. `senescent_or_stably_arrested`: persistent arrest supported by a multi-marker
   damage program, never inferred from cell age alone;
7. `dying` and `dead`: terminal outcomes driven by the existing mechanistic fate
   evidence, not a fixed lifespan timer.

Cell age, time in current state, number of completed DNA replications, number of
completed cytokineses, ploidy, nuclear count and lineage generation must be
different variables. They describe different physical facts and cannot safely be
collapsed into one `life_stage` or `biological_age` score.

## What writes memory

The event log must preserve the distinction between an exposure and a stored
trace. Candidate writers include:

- unrepaired nuclear or mitochondrial DNA damage;
- DNA replication and chromosome segregation;
- partial hepatectomy, toxic injury and compensatory proliferation;
- chronic or repeated viral infection;
- chronic diet/metabolic exposure followed by recovery;
- persistent bile-acid, oxidative, ER or inflammatory stress;
- altered cell position, polarity or niche;
- failed proteostasis or mitophagy that leaves long-lived cargo;
- cytokinesis failure, polyploidization and ploidy reversal.

An event should contain identity, onset, duration, dose or intensity in measured
units, compartment, evidence source and recovery/washout time. Without those
fields the engine can record exposure history but must not consolidate a
biological memory.

## How memory is read

Memory should modify a later **response function**, not merely add a decorative
score. Examples include:

- accessible inflammatory enhancers changing the gain or latency of a second
  inflammatory response;
- persistent H3K27ac states changing expression of a defined gene program;
- ploidy changing proliferative potential and chromosome dosage;
- mtDNA heteroplasmy and mitochondrial quality changing ATP/ROS response;
- long-lived proteostasis load changing ERAD, proteasome or autophagy reserve;
- persistent DNA-damage response changing repair, senescence and fate evidence;
- inherited transporter localization or organelle state changing the daughter's
  immediate phenotype.

Every readout link needs its own source. A global rule such as “past stress makes
future stress 20% stronger” is not scientifically defensible.

## How memory is erased or diluted

Erasure mechanisms are substrate-specific:

- DNA repair can remove lesions but not an established mutation;
- TET/DNMT and chromatin-remodeling systems can rewrite epigenetic states;
- protein degradation, ERAD, proteasome and autophagy remove protein traces;
- mitophagy and biogenesis reshape mitochondrial quality and heteroplasmy;
- metabolite exchange and biochemical turnover reset short-lived state;
- cell division dilutes soluble factors and partitions proteins and organelles;
- cell death removes the lineage, while clonal selection changes population
  composition.

No universal exponential memory decay is supported. Each substrate requires a
measured turnover, washout, persistence or inheritance dataset.

## Evidence tiers for implementation

### Tier A: implement as persistent physical state now

- nuclear somatic mutation records;
- ploidy, nuclei and chromosome-copy state;
- mtDNA variants/heteroplasmy as explicit records, without invented mutation
  rates;
- event history and lineage ancestry;
- measured experiment-specific epigenetic scars, such as HCV-associated marks,
  when the relevant dataset is supplied.

### Tier B: implement as reversible state with source-specific kinetics

- chromatin accessibility and selected histone/DNA-methylation programs;
- proteome and organelle composition;
- mitochondrial damage and quality-control state;
- persistent DNA-damage response and senescence programs;
- zonation/polarity and niche adaptation.

### Tier C: record only until calibration arrives

- generic “stress memory strength”;
- universal memory consolidation thresholds;
- generic transgenerational epigenetic inheritance;
- asymmetric aggregate or organelle inheritance probabilities in hepatocytes;
- exact conversion from normalized stress-time to chromatin, mutation or fate;
- a universal memory half-life.

## Proposed simulation data contract

```text
CellHistory
  lineage_id
  parent_cell_id
  birth_time
  lineage_generation
  completed_dna_replications
  completed_cytokineses
  event_log[]

CellLifecycle
  state
  entered_state_time
  ploidy
  nuclear_count
  cycle_phase
  division_competence
  terminal_status

MemoryTrace
  trace_id
  substrate_type
  compartment
  locus_or_entity
  written_by_event_id
  value
  unit
  established_time
  last_measured_time
  persistence_status
  inheritance_mode
  evidence_source_id
  experimental_system
  uncertainty

EventRecord
  event_type
  start_time
  end_time
  intensity
  unit
  compartment
  recovery_time
  evidence_source_id
```

`substrate_type` should be one of `genetic`, `dna_methylation`,
`histone_or_chromatin`, `transcriptional_network`, `protein_or_aggregate`,
`mitochondrial`, `organelle_composition`, `metabolic`, `damage_response`, or
`external_niche`.

The engine may always append an `EventRecord`. It may create or update a
`MemoryTrace` only when the event-to-trace rule and persistence behavior are
supported by the specified experimental system. Unknown inheritance or erasure
must remain `unknown`, not silently become 50%, zero, or exponential decay.

## Required calibration datasets

1. Repeated-exposure hepatocyte studies with baseline, first response, washout,
   second response and matched chromatin/transcript/protein measurements.
2. Primary human hepatocyte or human-liver time series after HCV cure, diet
   reversal, cholestatic injury recovery and toxic injury recovery.
3. Locus-resolved ATAC-seq, DNA methylation and histone-mark persistence data,
   including recovery duration.
4. Single-cell lineage data linking parent and daughter ploidy, mtDNA,
   organelles, damage and later response.
5. Human hepatocyte protein and organelle turnover distributions under healthy
   and stressed conditions.
6. Evidence distinguishing intracellular memory from persistent external ECM,
   inflammation or zonation signals.
7. Species- and context-specific distributions for hepatocyte quiescence exit,
   cell-cycle phase duration, successful cytokinesis, polyploidization, ploidy
   reversal, return to quiescence, senescence and death.

Until these arrive, the model can faithfully store experiences and physical
state but must not claim a calibrated adaptive-memory response.

## Implemented engine architecture

The first evidence-safe implementation is now present in the engine:

- `engine/cell_engine/core/genome.py` stores the GRCh38.p14 reference coordinate
  system, 24 nuclear reference chromosomes, the NC_012920.1 mitochondrial
  reference and a simulation-facing index of 13 hepatocyte-relevant loci.
- Reference coordinates are explicitly separate from an individual's genotype.
  Sex-chromosome complement, mtDNA copy number, heteroplasmy and inherited
  variants remain `not_provided` or `not_measured`.
- `record_somatic_variant` accepts only coordinate-valid, source-linked observed
  records. The engine does not generate mutations without a selected calibrated
  mutation model.
- `engine/cell_engine/core/history.py` separates lifecycle, experience events
  and persistent memory traces.
- `engine/cell_engine/processes/cellular_memory.py` records explicit experiments
  over time but does not convert stress-time into persistent memory.
- `MemoryTrace` requires a recorded writer event, a physical substrate, a
  persistence criterion, an experimental system and at least one source.
- The browser snapshot displays lifecycle, events, consolidated traces, genome
  reference, ploidy, functional loci and the current unknown-data boundary.

The next genetic extensions should be dataset-driven: import a donor VCF/BCF,
attach ClinVar or experimentally selected functional annotations, add copy-number
and structural-variant records, then connect measured variants to specific
transporter/enzyme parameters. Epigenetic marks remain separate from DNA sequence
and should be imported from locus-resolved methylation, ATAC-seq or ChIP-seq data.
