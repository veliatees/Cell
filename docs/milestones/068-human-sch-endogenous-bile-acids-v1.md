# Milestone 068 - Human SCH endogenous bile-acid compartments v1

## Question

What measured human-hepatocyte bile-acid endpoint can constrain the model
without pretending that sandwich culture is an in-vivo healthy cell?

## Source and assay context

Marion et al. measured endogenous bile acids by LC-MS/MS in sandwich-cultured
primary human hepatocytes from four donors. Cells received a `0.25 mg/mL`
Matrigel overlay. Vehicle or `10 uM` troglitazone treatment began on day 6;
samples were collected after 24 hours on day 7.

The source reports mean plus SD across four donor experiments. Cell/bile values
were measured once or twice per experiment, while medium had two to six
measurements. The assay used a representative `0.9 mg protein/well` and an
estimated `6.79 uL intracellular volume/well`.

## Loaded vehicle-control totals

```text
Cells + bile:  281 +/- 85.7 uM
Cells:         183 +/- 55.6 uM
Medium:        9.61 +/- 6.36 uM
```

The complete Table 4 records for TCA, GCA, TCDCA, GCDCA, and Total are retained
for both vehicle and troglitazone. The discussion contains `183 +/- 111 uM`,
which conflicts with Table 4 and the abstract. The curated record preserves
Table 4 (`183 +/- 55.6 uM`) and flags the discrepancy instead of averaging it.

## BEI aggregation boundary

For one matched raw experiment, the source operator is:

```text
BEI = (standard-buffer accumulation - calcium-free accumulation)
      / standard-buffer accumulation x 100%
```

Published BEI is the mean of experiment-level ratios. It is not the ratio of
the published group means. For vehicle TCA, the ratio of group means is about
44.38%, while the published aggregate BEI is 41.7%. The engine preserves the
reported value and forbids reconstruction from aggregate concentrations.

Both cells-plus-bile and cells values use the same estimated intracellular
volume. Their difference is not a measured canalicular concentration or
canalicular volume.

## Censoring and biological scope

The source assigns proxy zero to values below quantification. Raw donor-level
censoring flags and analyte-specific LLOQs are unavailable, so source zeros
cannot become biological zeros. The day-7 culture was more than 99% glycine
conjugated, but the authors identify culture-related taurine depletion as a
possible cause. It is not used as an in-vivo human conjugation ratio.

## Files

- `data/phh_baseline/curated/marion2013_human_sch_bile_acids.v1.json`
- `engine/cell_engine/quantitative/human_sch_bile_acids.py`
- `engine/tests/test_human_sch_bile_acids.py`
- `scripts/export_engine_snapshot.py`
- `src/engineSnapshot.ts`
- `src/main.ts`

## Release status

- Table 4 vehicle and perturbation records: loaded.
- Aggregate measurement contract: ready.
- Raw donor records and LLOQs: blocked.
- True canalicular concentration: blocked.
- Kinetic fitting: blocked.
- Healthy in-vivo initialization: blocked.
- Automatic cell-state coupling: blocked.
- Predictive release: blocked.
