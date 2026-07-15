# Milestone 060 - PHH spheroid exact-protocol validation v1

## Purpose

Milestone 059 curated the measured healthy, insulin-sensitive primary-human-
hepatocyte (PHH) spheroid observations. Milestone 060 turns those observations
into an executable validation contract. A model output is now comparable only
when its biological format, seeded-cell denominator, glucose/insulin/glucagon
bundle, sign convention, unit and all 16 time windows match exactly.

This milestone does not claim that the current cell model passes the experiment.
No matching model prediction has been submitted, so the comparison count and
pass/fail count both remain zero.

## Primary-source method lock

The protocol is locked to Kemas et al. 2021:

- two-donor BioIVT PHH culture;
- ultra-low-attachment 96-well plate;
- 1500 viable cells seeded per well;
- one spheroid observed per well after spontaneous aggregation;
- 100 uL reported culture-seeding volume;
- 10 uL supernatant sampled for the glucose assay, assayed in duplicate;
- four exact glucose/insulin/glucagon exposure bundles; and
- net medium-glucose disappearance calculated using the paper's expression
  `(C0 * V0 - Ct * Vt) / (VF * n)`.

The 100 uL value is not silently reused as the glucose-challenge initial volume.
Methods 2.7 says that the medium was changed, but does not restate that volume.
The challenge initial volume, remaining-volume schedule, `VF`, and viable-cell
count at every observation window therefore remain `null`. A medium glucose-
concentration trajectory cannot be reconstructed from this record.

Primary paper: [Kemas et al., FASEB Journal 2021](https://faseb.onlinelibrary.wiley.com/doi/10.1096/fj.202001989RR).

## Cumulative mean targets

The 0-6, 6-24 and 24-72 h records do not overlap. For each window, the cumulative
mean increment is an exact linear transformation:

`window mean rate * window duration`.

Summing those increments gives the following cumulative mean net disappearance
per seeded cell. The zero at time zero is the mathematical definition of a
cumulative trajectory, not a measured concentration.

| Exposure | 0 h | 6 h | 24 h | 72 h | Unit |
|---|---:|---:|---:|---:|---|
| 11 mM glucose + 1.7 uM insulin | 0.0 | 60.0 | 123.0 | 190.2 | fmol/seeded cell |
| 11 mM glucose + 0.1 nM insulin + 100 nM glucagon | 0.0 | 59.4 | 122.4 | 184.8 | fmol/seeded cell |
| 5.5 mM glucose + 1.7 uM insulin | 0.0 | 36.6 | 79.8 | 123.0 | fmol/seeded cell |
| 5.5 mM glucose + 0.1 nM insulin + 100 nM glucagon | 0.0 | 18.0 | 39.6 | 58.8 | fmol/seeded cell |

Each window SD is multiplied by that window's duration and retained. The SDs are
not combined across windows: the primary paper does not report the covariance or
repeated-measures structure needed to do that correctly.

## Overlap audits

The separately reported 0-72 h means overlap all three shorter windows. They are
not counted as four additional independent trajectory observations. Instead,
they provide descriptive internal checks:

| Exposure | Weighted subwindow mean | Reported 0-72 h mean | Reported - derived | Cumulative difference |
|---|---:|---:|---:|---:|
| 11 mM + high insulin | 2.6417 | 2.6000 | -0.0417 | -3.0 fmol/cell |
| 11 mM + low insulin + glucagon | 2.5667 | 2.6000 | +0.0333 | +2.4 fmol/cell |
| 5.5 mM + high insulin | 1.7083 | 1.7000 | -0.0083 | -0.6 fmol/cell |
| 5.5 mM + low insulin + glucagon | 0.8167 | 0.8000 | -0.0167 | -1.2 fmol/cell |

No tolerance is inferred from these differences, so no pass/fail label is
assigned.

## Fail-closed comparator

`phh_spheroid_protocol.py` rejects a prediction when any of these differ:

- protocol version, species, PHH 3D-spheroid format or health context;
- 1500-seeded-cell denominator;
- net-disappearance quantity, positive sign convention or
  `fmol_per_cell_per_h` unit;
- any 5.5/11 mM glucose, 0.1 nM/1.7 uM insulin or glucagon field;
- any one of the 16 exact condition-window combinations; or
- model and prediction identifiers plus a SHA-256 artifact checksum.

An exact match produces 16 descriptive residuals. Twelve are marked independent
trajectory targets and four are marked overlapping. A residual divided by the
reported SD may be shown descriptively, but there is no aggregate score,
acceptance threshold, state coupling or predictive claim.

## Files

- `data/phh_baseline/curated/kemas2021_phh_spheroid_protocol.v1.json`
- `engine/cell_engine/quantitative/phh_spheroid_protocol.py`
- `engine/tests/test_phh_spheroid_protocol.py`
- `scripts/export_engine_snapshot.py`
- `src/engineSnapshot.ts`
- `src/main.ts`

## Scientific effect

The project now knows exactly what a future PHH spheroid simulation must emit to
be compared with this experiment. It still does not know the challenge-medium
volume trajectory, vectorial glucose flux decomposition, donor-specific kinetics
or a preregistered biological acceptance threshold. This is validation rigor and
reproducibility infrastructure, not evidence that the current hepatocyte is
predictive.
