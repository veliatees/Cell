# Milestone 066 - Absolute PHH proteome budget v1

> Denominator clarification (Milestone 077): the article uses rounded
> reference-cell headlines, while Supplementary Table 2 explicitly labels
> proteomic-ruler abundance per nucleus. Current runtime protein populations use
> the supplement denominator and do not equate one nucleus with one hepatocyte.

## Question

How much protein does a human hepatocyte contain, and which parts of that
measurement can safely constrain the simulation?

## Source-backed whole-cell reference

Wisniewski et al. quantified purified primary hepatocytes from seven human
donors by LC-MS/MS with the Total Protein Approach and Proteomic Ruler. The
source reports these cohort-average values:

```text
Total protein:                         600 pg/cell
Estimated protein molecules:          8.7 x 10^9 molecules/cell
Mitochondrial protein:                 25% of total protein
ER + Golgi protein:                    12% of total protein
Nuclear protein:                       10% of total protein
Integral plasma-membrane protein:      1.2% of total protein
```

The paper does not publish uncertainty for these headline averages. The
reported `3000 um3` cell volume is not direct morphometry: it is derived using
an assumed average cellular protein concentration of `200 g/L`.

## Arithmetic mass budget

Only unit-preserving arithmetic is applied to the 600 pg average:

```text
Mitochondria:                         150 pg/cell
ER + Golgi:                            72 pg/cell
Nucleus:                               60 pg/cell
Integral plasma-membrane proteins:    7.2 pg/cell
```

These are protein-mass allocations. They are not organelle volumes, membrane
areas, geometric scale factors, molecule-rendering counts, or dynamic state
variables.

## Interpretation boundary

The combined study dataset contains 9400 quantified proteins across the study;
that number is not interpreted as exactly 9400 proteins in every hepatocyte.
The aggregate molecule count also does not specify every molecular species.
Static abundance cannot identify synthesis, degradation, trafficking,
macromolecular crowding, or donor-specific proteostasis.

## Files

- `data/phh_baseline/curated/wisniewski2016_hepatocyte_proteome_budget.v1.json`
- `engine/cell_engine/quantitative/phh_proteome_budget.py`
- `engine/tests/test_phh_proteome_budget.py`
- `scripts/export_engine_snapshot.py`
- `src/engineSnapshot.ts`
- `src/main.ts`

## Release status

- Absolute cohort-average protein budget: loaded.
- Arithmetic compartment protein masses: loaded.
- Donor-specific initialization: blocked.
- Dynamic proteostasis and crowding: blocked.
- Geometry coupling: blocked.
- Automatic cell-state coupling: blocked.
- Predictive release: blocked.
