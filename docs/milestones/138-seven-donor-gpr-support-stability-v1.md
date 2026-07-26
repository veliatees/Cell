# Milestone 138: Seven-donor GPR support stability v1

## Purpose

Replace a single all-donor intersection count with an exact donor-support
stability audit for every Human-GEM reaction carrying an FBC GPR.

## Method

The input remains the seven surgical-resection PHH donors in Wisniewski et
al. (<https://doi.org/10.1016/j.jprot.2016.01.016>). The audit uses the exact
donor reaction identities frozen by milestone 136.

- No abundance threshold is introduced.
- No missing value is imputed.
- No synonym mapping is added.
- Support frequencies are exact set counts from `0/7` through `7/7`.
- Every pair of donors is compared by an unweighted set Jaccard index.
- Each donor is held out once; the other six sets are intersected exactly.
- Generic FASTCC-consistent results remain separate from all GPR results.

## Pinned Result

Across `7,782` GPR-associated reactions:

| Supported donors | All GPR reactions | Generic FASTCC-consistent |
|---:|---:|---:|
| 0 | 1,801 | 1,654 |
| 1 | 48 | 42 |
| 2 | 115 | 99 |
| 3 | 98 | 72 |
| 4 | 363 | 357 |
| 5 | 125 | 102 |
| 6 | 150 | 132 |
| 7 | 5,082 | 4,555 |

Leave-one-donor-out expansion of the `4,555`-reaction seven-donor
flux-consistent core:

| Held-out donor | Added reactions |
|---|---:|
| A | 3 |
| B | 0 |
| C | 9 |
| D | 58 |
| E | 62 |
| F | 0 |
| G | 0 |

Pairwise donor-support Jaccard values span approximately `0.8878-0.9939`.

## Scientific Boundary

The finite cohort is not a healthy-volunteer population sample. A missing
protein-group observation can reflect assay coverage, sample context or donor
variation and is not interpreted as biological inactivity. The analysis
quantifies sensitivity; it does not infer prevalence, enzyme capacity or flux.
