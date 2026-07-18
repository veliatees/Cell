# Milestone 063 - PHH CYP450 batch-resolved function observability v1

## Question

How can direct PHH drug-metabolism measurements test the simulation without
turning assay endpoints into invented CYP kinetics or treating undetectable
signals as true zero activity?

## Primary evidence and artifact audit

Peng et al. 2025 measured six CYP substrate/metabolite pairs in six commercial
cryopreserved PHH batches. Tables S4-S6 were extracted from the Europe PMC
supplementary DOCX after checksum verification:

```text
MD5     cf6103b084c236f3fedf2f30e548559e
SHA-256 deeb835fe82d7e0e883447268354b9abb8f3ca4950639be3b68b802d3c6183bf
```

The source assay used 1,000,000 cells/well in collagen-I-coated 12-well 2D
culture, 1.0 uM substrate, and Shimadzu LCMS-8030 detection. Tables S4-S5
report `n=3` for each batch but do not identify the replicate class. SCR is
reported in `uL_per_h_per_1e6_cells`; MFR is reported in
`pmol_per_h_per_1e6_cells`.

## Loaded observation matrix

The engine contains 6 enzymes x 6 batches x 2 outputs = 72 reported means:

| Enzyme | Substrate -> metabolite | Quantified SCR span | Quantified MFR span |
|---|---|---:|---:|
| CYP1A2 | phenacetin -> 4-acetamidophenol | 72.4-208.8 | 33.9-353.0 |
| CYP2B6 | bupropion -> 4-hydroxybupropion | 146.8-476.8 | 26.7-769.5 |
| CYP2C9 | diclofenac -> 4'-hydroxydiclofenac | 78.6-246.7 | 102.7-744.7 |
| CYP2C19 | mephenytoin -> 4-hydroxymephenytoin | 34.8-255.1 | 15.2-211.7 |
| CYP2D6 | dextromethorphan -> dextrorphan | 72.1-902.9 | 67.7-849.9 |
| CYP3A4 | testosterone -> 6beta-hydroxytestosterone | 802.7-1981.0 | 234.8-2008.6 |

The spans exclude source-reported undetectable entries. Of 72 means, 62 are
quantified and 10 were printed as 0.0 without an SD. Those ten records carry a
`source_reported_undetectable` status and receive no numeric residual against
zero.

## Same-format comparator

A candidate model must provide the exact six-enzyme by six-batch matrix with
matching species, culture format, 1.0 uM substrates, units, cell denominator,
model identity, and artifact SHA-256. The comparator reports residuals only for
quantified observations. It fits zero parameters, assigns no pass threshold,
and cannot alter cell state.

The printed SCR/MFR formulas are preserved as source semantics. Raw substrate
and product time courses, sampling times, LLOQs, covariance, viable-cell
trajectories, genotype, and absolute CYP/POR abundance are unavailable; the
endpoint table is not reverse-engineered into hidden rate constants.

## Biological boundary

The observations can validate assay-level drug-metabolism output. They do not
separately identify transport, nonspecific binding, CYP catalytic turnover,
POR coupling, competing pathways, or metabolite loss. The `n=3` observations
are within-batch replicates of unspecified class, not independent estimates of
donor population variance.

The CSCB standard states a `>=100 uL/h/10^6-cell` criterion for representative
drug-metabolism ability and explicitly gives CYP3A4 with testosterone as the
example. That commercial PHH product criterion is not generalized to every CYP
assay, and it is not a healthy physiological interval or simulation pass
threshold.

## Files

- `data/phh_baseline/curated/peng2025_phh_cyp_function.v1.json`
- `engine/cell_engine/quantitative/phh_cyp_function.py`
- `engine/tests/test_phh_cyp_function.py`
- `scripts/export_engine_snapshot.py`
- `src/engineSnapshot.ts`
- `src/main.ts`

## Release status

- Batch-resolved observation matrix: loaded.
- Same-format diagnostic comparator: ready.
- Raw time-course reconstruction: blocked.
- Kinetic parameter fitting: blocked.
- Donor-causal model: blocked.
- Automatic cell-state coupling: blocked.
- Predictive release: blocked.
