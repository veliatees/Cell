# Milestone 065 - PHH identity, purity, and heterogeneity observability v1

## Question

How can commercial PHH identity and composition data inform a one-hepatocyte
simulation without confusing product contaminants, marker positivity, and
within-hepatocyte state?

## Two separate identity assays

Peng et al. 2025 measured intracellular ALB and HNF4A positivity by FACS in six
PHH batches. The same batches were profiled by 10x Genomics Chromium Single
Cell 3' v2 RNA-seq, aligned to GRCh38 and processed with Seurat 4.2.0. The
published QC gates were more than 500 genes, more than 600 UMIs, and less than
20% mitochondrial transcripts per cell.

These outputs remain separate:

- FACS asks what fraction is positive under a marker/antibody/gating assay.
- scRNA classification asks what fraction of filtered transcriptomes matches a
  cell-type marker signature.

They are not interchangeable purity estimates. For example, PHH789 is 98.9%
ALB-positive by FACS but 69.22% hepatocytes by the published scRNA classifier.

## Loaded batch composition

Figure S2B provides exact counts and rounded percentages for five cell types in
54,134 filtered cells. Hepatocyte fractions range from 69.22% to 98.91%.
PHH211, PHH025, and PHH789 each contain more than 10% non-hepatocytes; PHH789
contains 23.17% lymphocytes and 6.22% LSECs.

The FACS ranges are:

```text
ALB-positive:   49.4-98.9%
HNF4A-positive: 37.7-91.4%
```

Only PHH409 and PHH416 meet both source product-marker criteria of >=90%. The
criterion is not converted into a single-cell state threshold.

## Heterogeneity and correlation boundary

The study reports five hepatocyte subsets with distinct enrichment patterns.
The subset count and qualitative enrichments are retained, but no donor-by-
subset numeric matrix is curated. The study reports weak, non-significant
relationships between scRNA hepatocyte fraction and FACS ALB (`r=0.16`) or
HNF4A (`r=0.20`) across six batches. Marker fractions therefore cannot stand in
for cell-type composition or metabolic function.

Non-hepatocyte cells describe the contents of a commercial PHH product. They
are not organelles, molecular fractions, or hidden states inside one simulated
hepatocyte. Consequently, product composition cannot initialize this cell.

## Generative-model boundary

GEO accession GSE289636 is registered as the raw-data provenance. Six batches
can support inspection and future feature-schema work, but they cannot support
a donor-disjoint train/validation/test split, broad donor distribution, or a
validated VAE. Generative training and synthetic-cell coupling remain blocked.

## Files

- `data/phh_baseline/curated/peng2025_phh_identity_heterogeneity.v1.json`
- `engine/cell_engine/quantitative/phh_identity_heterogeneity.py`
- `engine/tests/test_phh_identity_heterogeneity.py`
- `scripts/export_engine_snapshot.py`
- `src/engineSnapshot.ts`
- `src/main.ts`

## Release status

- Six-batch FACS table: loaded.
- Six-batch scRNA composition table: loaded.
- GEO accession: registered.
- Five-subset count: loaded; numeric batch matrix not loaded.
- One-cell initialization from product composition: blocked.
- Generative training: blocked.
- Automatic cell-state coupling: blocked.
- Predictive release: blocked.
