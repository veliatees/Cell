# Genome and Gene-Expression Milestone 1

## Objective

Milestone 1 establishes a source-traceable path from a human reference genome
locus to an observable RNA/protein state and, where justified, to an existing
hepatocyte process. It is deliberately a seven-gene vertical slice rather than a
claim to simulate the complete human genome or transcriptome.

The tracked program is:

| Gene | Product | Current model role |
| --- | --- | --- |
| `HNF4A` | HNF4-alpha | hepatocyte identity control |
| `NR1H4` | FXR | bile-acid sensing and transcriptional regulation |
| `NR0B2` | SHP | nuclear-receptor coregulation |
| `CYP7A1` | cholesterol 7-alpha-hydroxylase | classical bile-acid synthesis gate |
| `SLC10A1` | NTCP | sinusoidal bile-acid uptake |
| `ABCB11` | BSEP | canalicular bile-acid export |
| `ABCC2` | MRP2 | canalicular conjugate export |

## Implemented State Contract

Each gene has separate fields for:

- reference locus identity and coordinates;
- allele copies derived from the cell's nuclear ploidy;
- functional dosage;
- promoter and chromatin state;
- nuclear pre-mRNA, nuclear mature mRNA, and cytoplasmic mRNA;
- total protein abundance;
- normalized functional protein activity;
- protein location, evidence status, and source identifiers.

These fields must not be collapsed into one generic "gene activity" number.
DNA copy number, RNA abundance, total protein abundance, membrane-localized
protein, and functional activity are biologically different observables.

## Evidence and Missing-Data Policy

The initial coordinates use NCBI's GRCh38.p14 reference records. Mammalian
transcriptional bursting is represented as a supported mechanism, but no generic
burst rate is assigned to these seven genes. The primary-hepatocyte turnover
literature also shows that a universal protein-decay constant would be
indefensible.

Accordingly:

- unmeasured RNA, protein, promoter, and chromatin values remain `null` or
  `unknown`, never zero;
- every observed state update requires an event ID, source ID, and evidence
  description;
- negative or non-finite counts are rejected;
- BSEP/MRP2 loss experiments change functional activity without inventing a
  mutation coordinate or RNA measurement;
- transporter copy-number anchors are total-abundance order-of-magnitude values,
  not measured canalicular/sinusoidal surface counts;
- the browser creates no autonomous transcription events and only visualizes
  events supplied by the Python engine.

## Functional Coupling

`ABCB11` and `ABCC2` functional activity now drives the same BSEP and MRP2
transport controls used by the cholestasis engine. Conflicting expression and
legacy-control values fail explicitly instead of being silently reconciled.

`CYP7A1`-dependent bile-acid synthesis is gated twice: the expression program
must contain an explicit functional protein scale and the model controls must
contain an explicit calibrated synthesis rate. With either value missing, the
flux is exactly zero and the status reports that calibration is absent. No
default biological rate is invented.

## Visualization

The inspector reports all seven genes, ploidy-derived allele counts, compartmental
RNA, total protein, functional activity, and recent expression events. The seven
nuclear loci carry their real gene symbols. A locus flashes and an mRNA particle
is emitted only for a matching engine event. Particle travel is a schematic
rendering and is not interpreted as measured transport time.

The nucleolus label is also corrected: it describes rRNA transcription/processing
and ribosomal-subunit assembly; protein-coding mRNA transcription is assigned to
the nucleoplasm.

## Validation Boundary

Milestone 1 validates software contracts, provenance, conservation guards, and
experiment coupling. It does not yet validate gene-specific transcription,
splicing, export, translation, degradation, or protein-trafficking kinetics.
Those require matched hepatocyte measurements or an explicitly calibrated model.

## Primary Sources

- Karr et al. (2012), whole-cell model architecture:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC3413483/
- Larsson et al. (2019), mammalian transcriptional burst kinetics:
  https://www.nature.com/articles/s41586-018-0836-1
- Systematic protein-turnover analysis in primary human hepatocytes:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC5814408/
- NCBI human gene records and GRCh38 reference coordinates:
  https://www.ncbi.nlm.nih.gov/gene/

## Exit Criteria

Milestone 1 is complete when:

1. all seven genes exist in the reference genome and expression registries;
2. expression state and events serialize into baseline and experiment snapshots;
3. BSEP/MRP2 perturbations propagate through expression state into transport;
4. CYP7A1 synthesis remains disabled without explicit calibration;
5. the browser renders engine-authoritative expression state without fabricated
   transcription;
6. Python tests, frontend tests, production build, and browser checks pass.

