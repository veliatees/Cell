# Scientific Parameter Audit and Correction Pass

## Audit Rule

Every runtime surface is classified independently. A real pathway name or a
correct stoichiometric equation does not make its absolute rate quantitative.
Only `source_backed` or explicitly documented `derived` surfaces may drive a
scientific validation score.

## High-Impact Findings

### 1. Relative pools were presented too strongly

The main Python state contains 48 `relative_pool_0_1` placeholders. They are
useful for rendering and qualitative scenario direction, but values such as
`ATP 0.76`, `GSH 0.82`, or `ROS 0.02` are not concentrations.

Correction:

- snapshot authority is now `mixed_authority_research_preview`;
- browser labels these values as relative/schematic;
- they cannot drive quantitative validation;
- the PHH profile remains the real-unit ATP/ADP/AMP/glycogen/NAD+ surface.

### 2. HMDB validation was contaminated by placeholder pathway flux

The postabsorptive glucose boundary was previously advanced together with
placeholder gluconeogenesis and export rates. This produced 4.844 mM and made a
placeholder perturbation look validated.

Correction:

- blood-boundary validation is isolated from integrated pathway dynamics;
- it validates the source-derived 4.75 mM boundary midpoint directly;
- integrated fuel pathways remain exploratory and blocked from validation.

### 3. Organelle hazard rates were invented

The former engine assigned each organelle a base failure probability per hour
and multiplied it by uncalibrated stress weights. No matched PHH time-course
supported these absolute risks.

Correction:

- default hazard probability is zero;
- no passive damage or random failure event is generated from an uncalibrated
  hazard;
- a non-zero hazard requires a source-tagged `HazardCalibration` object.

### 4. Organelle ages were invented

Mitochondria started at 18 h, nuclei at 12 h, and other organelles at arbitrary
ages. These values affected the former hazard model.

Correction:

- all organelles start at simulation age zero;
- `age_h` now means tracked time since initialization, not inferred biological
  age of the organelle.

### 5. Cytokinesis failure probability was not identifiable

The default hepatocyte population used `0.20` as a per-division failure
probability. Adult human binucleated/polyploid prevalence is not the same
quantity. Healthy human hepatocyte organoids show late cytokinetic regression,
but available studies do not identify a transferable per-division probability
for this model context.

Correction:

- default probability is zero;
- context knobs cannot create a failure risk unless
  `cytokinesis_failure_calibrated=True`;
- explicit software tests may supply a calibrated flag, but exported healthy
  snapshots do not.

### 6. Hepatocyte radius and volume were inconsistent

The definition used a 12 um radius while quantitative conversion used a 3400
um3 volume. A 12 um sphere is approximately 7240 um3.

Correction:

- the reference volume remains 3400 um3;
- equivalent-sphere radius is derived as approximately 9.33 um;
- the model states that this is a conversion geometry, not actual polarized
  hepatocyte morphology.

### 7. Transporter abundance was being overinterpreted

Total protein, total membrane fraction, plasma-membrane abundance, correctly
polarized surface abundance, and transport-active copies are distinct
denominators. Culture state can also change membrane abundance.

Correction:

- BSEP/MRP2/NTCP abundance remains useful as an abundance anchor;
- absolute transport flux stays blocked;
- legacy first-order transport rates are explicitly placeholder and excluded
  from predictive release.

### 8. In-vivo liver and isolated PHH were treated too closely

Isolation and culture substantially alter ATP, ADP, AMP, NADP(H), GSH, GSSG and
TCA metabolites. Tissue-derived PHH baseline values are therefore not silently
claimed as culture-PHH measurements.

Correction:

- profiles say `whole_tissue_equivalent`;
- isolated/cultured PHH prediction remains blocked;
- redox conversion and kinetics remain data-gated.

## Current Authority Surface

May drive quantitative validation:

- source-traceable PHH energy and glycogen profiles;
- postabsorptive blood-glucose boundary.

May drive visualization or qualitative direction only:

- normalized pools and stress;
- organelle functional cycles;
- relative cholestasis response;
- integrated gluconeogenesis, ketogenesis, redox and urea networks;
- gene-expression structures without gene-specific calibration.

Disabled or blocked:

- organelle failure hazards;
- default cytokinesis failure;
- absolute transporter flux;
- quantitative redox kinetics;
- calibrated time-to-death.

## Evidence Reviewed

- Quantitative human cell volumes: PMCID `PMC10218018`.
- Human liver adenylates: PMCID `PMC2952479`.
- PHH isolation-induced metabolic changes: PMID `29284039`.
- Total versus plasma-membrane transporter abundance: DOI
  `10.1124/dmd.118.084988`.
- Human MRP2 membrane-fraction abundance: PMCID `PMC3336801`.
- Human hepatocyte late cytokinetic regression: PMCID `PMC11090133`.
- Adult human liver polyploid prevalence and mechanism boundary: PMCID
  `PMC3063936`.

## Remaining Work

The audit does not make blocked modules quantitative. It prevents them from
making unsupported claims. Each can be re-enabled only after a matched dataset,
unit-preserving parameter transform, uncertainty model and held-out validation
are added.
