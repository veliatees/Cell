# Milestone 049 - Human PHH Zonation Context v1

This milestone replaces the single generic hepatocyte context with explicit
periportal, midlobular and pericentral human-hepatocyte reference contexts.

## Evidence Foundation

- The 2026 healthy-human spatial atlas combines Visium, MERFISH, Visium HD and
  protein validation. It reports widespread human zonation and important
  human-versus-mouse differences.
- The 2025 single-cell spatial proteomics cohort resolves continuous gradients
  across 20 portal-central bins in 413 healthy hepatocytes from 14 individuals.
- The 2019 human liver cell atlas independently supports canonical human
  hepatocyte zonation markers.

## Implemented

- Source-traceable marker registries for all three zones.
- Human-specific functional contexts and niche-signal direction.
- A categorical oxygen context: relatively higher, intermediate or relatively
  lower. No oxygen partial pressure is invented.
- Engine snapshots whose CellDefinition, genomic identity and zonation state
  agree on the selected zone.
- Twelve static contexts: three zones times four cholestasis experiments.
- A browser zone selector and evidence panel.
- Release-gate and audit checks that prohibit unmeasured zonal flux scaling.

## Marker Examples

- Periportal: PCK1, ALDOB, HAL, ASS1, ALB, GLS2, LDHB and SUCLG2.
- Midlobular: HSD17B13, C6, KLKB1, LIPC, HGD and SDC1.
- Pericentral: CYP2E1, CYP27A1, FASN, MLXIPL, PCK2, SLC2A2, GLUL,
  ADH4, HNF4A and ACSL5.

These are enrichment directions, not absolute expression levels for the
simulated cell.

## Scientific Boundary

Zone selection currently establishes anatomical and molecular identity only.
It does not alter enzyme abundance, oxygen concentration, reaction rates,
transport or disease severity. Those effects require matched human quantitative
measurements and held-out validation. Rodent oxygen or expression effect sizes
must not be silently substituted.

## Primary Sources

- https://www.nature.com/articles/s41586-026-10377-y
- https://pmc.ncbi.nlm.nih.gov/articles/PMC12027366/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC6687507/
