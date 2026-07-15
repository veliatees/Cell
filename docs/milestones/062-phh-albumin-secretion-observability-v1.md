# Milestone 062 - PHH albumin secretion observability + secretory-path gate v1

## Question

How much of a hepatocyte-defining albumin output can be represented from direct
primary-human-hepatocyte evidence without turning one 24-hour endpoint into
invented translation, trafficking or degradation kinetics?

## Primary evidence reviewed

- Peng et al. 2025 measured secreted albumin in six commercial PHH batches by
  ELISA after 24 h of regular 2D culture.
- Wisniewski et al. 2016 measured the PHH proteome in purified hepatocytes from
  seven human donors; its ALB copy-number anchor supplies pool context only.
- UniProtKB P02768 and the USP human-albumin reference define the precursor,
  mature chain and mature molecular mass needed for the observation operator.
- Lodish et al. 1983 established selective secretory-protein ER-to-Golgi transit
  in HepG2 cells. It is retained as pathway-topology evidence, not PHH kinetics.

## Source-locked assay contract

The curated Peng assay is kept in its published observation space:

- species: human;
- system: commercial primary human hepatocytes;
- format: regular 2D culture;
- window: 24 h;
- compartment: culture supernatant;
- assay: Bethyl E88-129 albumin ELISA;
- denominator: reported PHH cell number;
- unit: `ng_per_24h_per_1e6_cells`.

The main text reports the lowest and highest means, while the MD5-verified
supplementary Table S3 supplies all six batch records:

```text
762.7 +/- 174.1 to 6957.7 +/- 2440.5 ng/24 h/10^6 cells
```

```text
PHH330  762.7 +/- 174.1
PHH409  6957.7 +/- 2440.5
PHH416  4076.1 +/- 422.5
PHH211  2358.7 +/- 742.6
PHH025  4122.0 +/- 955.2
PHH789  2792.5 +/- 774.9 ng/24 h/10^6 cells
```

Table S3 labels each batch summary `n=3` but does not identify the replicate
class. The SD values are therefore retained as within-batch uncertainty with
unspecified replicate semantics, never as a population reference interval. No
value is digitized, interpolated or inferred.

## Measurement operator

A candidate model must provide cumulative secreted **mature** albumin molecules
per cell at exactly 0 and 24 h, with a zero origin, non-negative nondecreasing
output, matching PHH/2D context, matching denominator, model identity and
artifact SHA-256.

Using mature human albumin (`585 aa`, `66,438 g/mol` numerically), the operator is:

```text
ng/24 h/10^6 cells =
  delta molecules/cell / Avogadro
  * 66,438 g/mol
  * 10^9 ng/g
  * 10^6 cells
```

This maps the reported endpoint means to approximately 6.91-63.07 million
molecules/cell/24 h, or 80-730 molecules/cell/s. These values are mass-derived
representations of the measured 24-hour output, not separately measured
instantaneous secretion rates and not kinetic constants.

## Pool is not rate

The existing approximately 20,000,000 ALB copies/cell proteome anchor comes
from a different seven-donor cohort. It cannot be divided by an assumed transit
time to infer secretion. It does not distinguish precursor, ER/Golgi cargo,
intracellular mature albumin or newly secreted protein.

Peng et al. reported an ALB-secretion versus ALB-mRNA association of `r=0.78`,
`p=0.07`, `n=6`; it was not statistically significant as reported. The model
therefore does not infer a transcription-to-secretion rate law. Albumin
secretion also cannot stand in for CYP450 activity.

## Corrected legacy pathway

The previous stochastic module contained two unsupported biological claims:

- one pseudo amino-acid molecule produced one proalbumin molecule despite the
  609-residue precursor;
- a hard-coded `0.01/s` translation rate and selected hepatoma transit times
  were presented as grounded hepatocyte secretion behavior.

Those claims are removed. The module now contains only a labelled-albumin
`ER -> Golgi -> medium` pulse-chase transport network. It has no biological
default and can run only when both half-times, source, experimental system and
evidence role are supplied explicitly. Software tests use parameters labelled
`software_test_only`; they are never exported as biological values.

## Identifiability result

The current assay identifies one aggregate quantity: cumulative extracellular
albumin over 24 h. It identifies zero of five registered mechanistic rates:

- albumin translation;
- ER export;
- Golgi maturation;
- exocytosis;
- intracellular degradation.

The CSCB `>=800 ng/24 h/10^6 cells` value is a source-reported product-quality
criterion. It is not used as a simulation pass threshold.

## Measurements required to unlock mechanism

1. Donor-resolved secretion time courses with window-specific viable-cell
   counts and matched culture context.
2. PHH pulse-chase measurements resolving labelled albumin in ER, Golgi and
   medium fractions.
3. Matched ALB mRNA, ribosome/polysome occupancy and newly synthesized albumin.
4. Absolute intracellular precursor and mature-albumin pool time courses.
5. Matched ER-export, Golgi or exocytosis perturbations with intracellular,
   extracellular, viability and proteostasis readouts.

## Files

- `data/phh_baseline/curated/peng2025_phh_albumin_secretion.v1.json`
- `engine/cell_engine/quantitative/phh_albumin_secretion.py`
- `engine/cell_engine/stochastic/secretion.py`
- `engine/tests/test_phh_albumin_secretion.py`
- `engine/tests/test_secretion.py`
- `scripts/export_engine_snapshot.py`
- `src/engineSnapshot.ts`
- `src/main.ts`

## Release status

- PHH albumin observation operator: ready.
- Individual six-batch numeric table: loaded from Table S3.
- Exact cumulative model trajectory: not loaded.
- Secretory-path kinetic fitting: blocked.
- Model pass threshold: none.
- Automatic cell-state coupling: blocked.
- Predictive release: blocked.
