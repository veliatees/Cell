# Genomic System: Six-Milestone Architecture

## Scope

The genomic system is organized into six milestones. All six now have executable
software contracts, serialization, validation rules and browser reporting. This
does not mean every biological parameter is known or validated. The engine
reports software readiness and scientific readiness separately.

## Milestone 1: Reference Genome to Functional Expression Slice

Implemented:

- GRCh38.p14 reference chromosomes and 15 simulation-facing loci;
- explicit separation of reference coordinates from an individual genotype;
- ploidy-derived allele copies;
- seven-gene bile-acid/hepatocyte-identity expression slice;
- compartmental RNA and protein state with `unknown` distinct from zero.

Data still required:

- donor-matched nuclear and mitochondrial genotype;
- allele-specific expression where relevant.

## Milestone 2: Regulation and Central Dogma

Implemented:

- source-backed qualitative FXR-SHP-CYP7A1, HNF4A-CYP7A1, FXR-BSEP and
  FGF19/FGFR4/JNK regulatory edges;
- promoter-active allele count;
- nuclear pre-mRNA, nuclear mature mRNA, cytoplasmic mRNA and protein stages;
- exact Gillespie SSA for promoter switching, transcription, splicing, export,
  RNA decay, translation and protein decay;
- mandatory biological system, assay, evidence and source metadata for every
  kinetic profile;
- runtime rejection of external-system and synthetic profiles in the
  authoritative hepatocyte engine.

The older generic central-dogma and telegraph rates are now labelled synthetic
software benchmarks. They are opt-in and excluded from exported authoritative
hepatocyte snapshots.

Data still required:

- matched primary-human-hepatocyte kinetic profiles for each modeled gene;
- measured initial RNA/protein counts for the same biological system;
- uncertainty distributions and replicate structure.

## Milestone 3: Reduced Transcriptome and Proteome

The project does not simulate approximately 20,000 protein-coding genes as
individual molecular agents. Instead it uses explicit genes where the mechanism
is required and functional modules elsewhere.

Implemented modules:

- bile-acid homeostasis;
- hepatocyte identity and secretion;
- glucose homeostasis;
- nitrogen disposal;
- DNA-damage checkpoint and arrest;
- epigenetic maintenance.

Each module declares which genes have explicit expression states and which are
registry-only. Omics datasets must declare assay, donor/cohort, assembly,
normalization and whether they are used for calibration or held-out validation.

## Milestone 4: Genome and Epigenome Change

Implemented:

- observed SNV, insertion, deletion, copy-number, structural and mtDNA records;
- coordinate and allele-fraction validation;
- per-locus chromatin accessibility, DNA methylation and histone-mark state;
- observed variant-to-function links with experimental-system provenance;
- no mutation, methylation or chromatin-scar generator enabled by default.

A variant can exist without a known functional consequence. A functional effect
cannot be created merely because a variant is present.

## Milestone 5: Cell Identity, Heterogeneity and Lineage

Implemented:

- species, cell type, zonation, donor, age, sex, tissue health and clone context;
- explicit unknown donor fields;
- compatibility with lineage, lifecycle, memory, ploidy and division state;
- source boundary based on human liver single-cell atlases.

The baseline cell is a reference-context hepatocyte, not an average donor and not
a generated individual. Future generative models may sample only from a fitted,
validated population distribution and must preserve donor-level grouping.

## Milestone 6: Validation and Inference Boundary

Implemented:

- ordered milestone readiness report in every engine snapshot;
- separate `software_complete` and `scientific_status` fields;
- explicit calibration-versus-validation dataset roles;
- required-data lists for every milestone;
- invariants preventing missing provenance, invalid fractions, unknown loci and
  unobserved variant-function links.

Still required before predictive claims:

- held-out primary-human-hepatocyte datasets;
- donor-aware cross-validation;
- uncertainty propagation and parameter-identifiability analysis;
- sensitivity analysis for every claimed phenotype;
- external replication of selected trajectories.

## Scientific Sources

- Human liver single-cell atlas and zonation:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC6687507/
- NIH GTEx V8 reference resource:
  https://commonfund.nih.gov/GTEx
- Human liver single-nucleus RNA/ATAC multiome:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC12805840/
- Primary-human-hepatocyte bile-acid regulation:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC4271050/
- Human FXR-SHP regulation:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC3912179/
- Human CYP7A1 feedback through JNK/c-Jun:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC1526464/
- HNF4A and human CYP7A1 regulation:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC2903807/

## Completion Meaning

All six software milestones are complete when their state contracts, update
functions, validation rules, snapshots, tests and UI are operational. A
scientific milestone becomes `validated` only after the named matched and
held-out datasets are loaded and pass predefined validation criteria. The engine
must continue to display `implemented_data_required` until then.

