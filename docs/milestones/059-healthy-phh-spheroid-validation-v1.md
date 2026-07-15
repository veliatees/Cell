# Milestone 059: Healthy PHH Spheroid Validation v1

Date verified: 2026-07-14

## Goal

Turn the delivered glucose, endocrine, oxygen and validation bundle into a
primary-source-audited healthy-PHH validation layer without allowing a supplied
table, model trajectory or organ-scale conversion to silently become a live
single-cell parameter.

## Evidence Review

The delivery contract named nine required files. Seven were available across
the current and immediately preceding deliveries; `human_phh_scale_bridge.csv`
and `koenig_model_provenance_audit.md` were absent. Every reviewed artifact is
recorded by filename, byte size, SHA-256 digest, delivery wave, review status
and reason in:

`data/evidence_intake/reviews/2026-07-14_phh_signal_flux_review.v1.json`

Raw supplied artifacts are not redistributed. The article text was used only
for primary-source review and restoration of table semantics.

The review corrected the following scientifically material issues:

- Kemas high glucose is 11 mM, not 25 mM.
- Low insulin is 0.1 nM (100 pM), not approximately 1 nM.
- Low-insulin media also contain 100 nM supplemented glucagon. The high- versus
  low-insulin rows therefore do not isolate a pure insulin intervention.
- The four highlighted glucose-consumption values are 0-6 h means with SD, not
  context-free point estimates.
- The delivered held-out trajectory table contains model predictions and a
  null human comparator. It contributes zero held-out human validation results.
- Controlled 3-13% oxygen in a human liver microphysiology system is an
  experimental device setting, not an in-situ human sinusoidal pO2 measurement.

The supplied integration contract also conflicted with the repository's
reproduced Koenig model-lineage audit. The current vendored executable remains
2/5 on its tracked benchmark, while a non-vendored legacy lineage reaches 5/5
under separately recovered conditions. The contract was therefore quarantined
instead of overriding the local audit.

## Curated PHH Targets

The machine-readable record is:

`data/phh_baseline/curated/healthy_phh_glucose_validation.v1.json`

It contains all 16 Table 1 glucose-consumption records for insulin-sensitive,
non-steatotic 3D primary human hepatocyte spheroids:

- four exposure bundles;
- 0-6, 6-24, 24-72 and overlapping 0-72 h windows;
- reported means, SD, n=6 and seeded-cell denominator;
- 12 non-overlapping windows suitable for a predeclared same-format comparison;
- two source donors overall, with table n explicitly not interpreted as six
  independent donors.

The four 0-6 h values are 10.0 +/- 2.4, 9.9 +/- 2.5, 6.1 +/- 1.7 and
3.0 +/- 0.8 fmol/cell/h for the exact exposure bundles recorded in the curated
file. These are net medium-glucose disappearance measurements. They are not a
direct GLUT2 transport assay, a fresh-PHH production rate or an in-vivo
single-cell flux.

## Measured Insulin Responses

The Kemas study also supplies three matched downstream responses to a 1.7 uM
insulin challenge in the insulin-sensitive PHH spheroid system:

- pAKT Ser473 increased 3.5-fold at 7 min;
- PCK1 expression decreased 4.1-fold after 6 h;
- G6PC expression decreased 3.9-fold after 6 h.

The pAKT replicate count is preserved as a source discrepancy: the Results
text reports n=4 and the figure caption reports n=3. The expression results
report an n range of 3-6. No uncertainty value, receptor abundance, receptor
occupancy, dose-response curve or complete time series is available. These
observations support the pathway and expose validation targets, but they do not
identify a quantitative INSR/AKT kinetic law.

## Human Scale Context

Wilson et al. provide a human hepatocellularity geometric mean of
107 million cells/g liver, with an observed range of 65-185 million cells/g
(n=7), and a microsomal-protein geometric mean of 33 mg/g liver with an
observed range of 26-54 mg/g (n=20).

Honka et al. report liver glucose uptake of 22.4 +/- 9.2
umol/kg liver/min in 326 participants without diabetes during a
hyperinsulinemic-euglycemic clamp with FDG-PET. Combining the reported mean with
the Wilson geometric-mean denominator gives 12.5607 fmol/cell/h. Crossing
mean +/- one reported SD with the observed hepatocellularity extremes gives
4.2811-29.1692 fmol/cell/h.

That range is a sensitivity analysis, not a confidence interval or a direct
single-cell measurement. It is retained as contextual scale evidence and has
`may_drive_cell_state=false`.

## Engine Integration

- `phh_glucose_validation.py` loads and strictly validates the curated record.
- The scientific model audit exposes a source-backed validation surface.
- Research-preview release checks require the curated record to remain
  internally consistent and fail closed.
- Predictive release remains blocked because no exact spheroid model protocol
  and no independent held-out human result exist.
- The communication system records one measured insulin exposure and three
  matched responses, while predicted receptor activation and downstream
  response remain null.
- The zonation state records the human MPS 3-13% oxygen experiment as
  directional functional evidence and explicitly forbids pO2 initialization.
- The browser shows measurements, derived context and blocked predictions in
  separate fields. No visual animation is used to imply molecular activation.

## Current Gates

- curated glucose windows: 16
- non-overlapping glucose windows: 12
- measured insulin responses: 3
- exact-protocol model predictions: 0
- independent held-out human results: 0
- automatic cell-state coupling: disabled
- fresh-PHH parameterization: blocked
- endocrine kinetic fitting: blocked
- predictive release: blocked

## Primary Sources

- Kemas et al., 3D primary human hepatocyte spheroid glucose and insulin
  responses: https://faseb.onlinelibrary.wiley.com/doi/10.1096/fj.202001989RR
- Wilson et al., human hepatocellularity and microsomal protein scaling:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC1884378/
- Honka et al., human liver glucose uptake by FDG-PET during clamp:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC5920018/
- Allen et al., human liver acinus microphysiology under controlled oxygen:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC5661766/
- Koenig et al., published hepatic glucose model:
  https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1002577

## Next Validation Work

1. Implement a 3D PHH spheroid protocol that reproduces the exact glucose,
   insulin, glucagon, cell denominator and four time-window definitions.
2. Freeze the 16 observations before model fitting and predeclare the error
   metric, treatment of overlapping windows and held-out split.
3. Obtain donor-resolved surface INSR abundance plus dose-time pAKT data to fit
   and validate receptor-to-AKT kinetics.
4. Acquire a genuinely independent PHH donor or study as a held-out test.
5. Keep human in-situ zonal oxygen and redox variables unavailable until direct,
   scale-matched evidence is found.
