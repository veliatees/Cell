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

The definition once used a 12 um radius while quantitative conversion used a
separate 3400 um3 volume. Later renderer and collision paths also carried a
25 um diameter. These independent anchors could not all describe one cell.

Correction:

- the active scale anchor is the direct normal-control human 3D median volume
  `5657.07116 um3` (MAD `744.875484 um3`, `n=5` reconstructions) from
  Segovia-Miranda et al. 2019 Supplementary Table 3;
- imaging used approximately `100 um` sections and `0.3 x 0.3 x 0.3 um`
  voxels;
- equivalent-sphere diameter (`22.107060841416555 um`), radius
  (`11.053530420708277 um`) and area (`1535.3658816738957 um2`) are exact
  derivations, not additional observations;
- Duarte et al. 1989's `2850 +/- 99.9 um3` five-case stereology result is
  preserved as a conflicting historical cross-check. It is not averaged with
  the 3D median, and the unidentified `+/-` statistic is not relabelled;
- Olander et al. 2021's `18.4 um` isolated-PHH median across 54 batches remains
  an independent isolated-cell cross-check rather than an in-situ shape claim;
- the engine definition, quantitative conversion, RDME lattice, renderer and
  generated browser artifacts consume this shared scale;
- the model states that this is a conversion geometry, not actual polarized
  hepatocyte morphology or a donor-specific mesh;
- the measured normal-control lipid-droplet volume fraction (`0.507807%`
  median, MAD `0.403178` percentage points) calibrates only aggregate display
  volume. Count, size distribution and nutritional dynamics remain blocked.

### 7. Transporter abundance was being overinterpreted

Total protein, total membrane fraction, plasma-membrane abundance, correctly
polarized surface abundance, and transport-active copies are distinct
denominators. Culture state can also change membrane abundance.

Correction:

- BSEP, MRP2, NTCP, GLUT2, ATP1A1, GCK and CPS1 estimates were replaced by
  official seven-donor Supplementary Table 2 medians and ranges;
- all 8,689 quantified target groups are queryable without imputation;
- copy-number denominator is `per_nucleus`, never silently `per_cell`;
- BSEP and MRP2 total copies per nucleus are available, while canalicular
  surface and transport-active copies remain absent;
- absolute transport flux stays blocked;
- legacy first-order transport rates are explicitly placeholder and excluded
  from predictive release.

Additional correction in Milestone 078:

- total-copy ratios are descriptive and can no longer drive transporter rates;
- an explicit activity multiplier must declare either a scenario-intervention
  or measured-surface-activity basis;
- measured-surface activity requires source-tagged, correctly localized copies;
- MRP2 rates `183` and `104 pmol/min/mg assay protein` are retained as
  observations at `0.5 uM` substrate, not mislabeled as Vmax;
- the two BSEP Km/Vmax datasets remain independent assay contexts;
- receptor response timepoints cannot substitute for binding kinetics.

### 8. In-vivo liver and isolated PHH were treated too closely

Isolation and culture substantially alter ATP, ADP, AMP, NADP(H), GSH, GSSG and
TCA metabolites. Tissue-derived PHH baseline values are therefore not silently
claimed as culture-PHH measurements.

Correction:

- profiles say `whole_tissue_equivalent`;
- isolated/cultured PHH prediction remains blocked;
- redox conversion and kinetics remain data-gated.

### 9. Contact markers were being overinterpreted as contact surfaces

A fixed glowing point or a radius guessed by the renderer can look like a
measured receptor-active interface even when the engine does not know the
external object's size or a finite contact area.

Correction:

- stochastic approach direction is sampled only by an explicit seeded
  scenario, never by per-frame visual flicker;
- the supplied sphere, capsule, or convex-polyhedron support geometry sets the
  placement, so object size and orientation change the first-contact location;
- missing or invalid object dimensions fail closed;
- contact patch position and area are geometry outputs, not random UI values;
- the renderer draws a patch only for an active engine-supplied finite polygon
  with positive area;
- mixed-shape point contacts with unresolved area no longer receive a fallback
  ring or glow;
- the normal one-hepatocyte runtime contains no external body and therefore no
  contact marker.

### 10. Pathway citations were being overinterpreted as numerical rate authority

The integrated fuel network has source-linked reaction topology, but a source
ID on a reaction does not show that the numerical constant used by the runtime
was reported by that source. Direct inspection found 36 active reactions, only
two with source-backed numerical parameter provenance, and 34 with no numerical
parameter provenance record.

Correction:

- every reaction is independently classified as source-backed, fitted,
  placeholder, unparameterized, or invalid;
- source-backed topology and source-backed numerical parameterization are
  separate fields;
- quantitative validation requires complete source-backed parameterization and
  a confirmed biological/experimental context match;
- predictive execution additionally requires independent held-out validation;
- unsupported reactions may execute only under the explicit exploratory role;
- all browser context snapshots expose the machine-generated `2 / 36` authority
  result instead of implying that the full network is quantitative.

### 11. Related published reactions were being mistaken for transferable kinetics

The Koenig human hepatic-glucose model contains literature kinetic constants
and fitted `Vmax` values, but those values belong to its own equations, fixed
cofactor assumptions, compartments, mean-liver context, and per-kilogram output
scale. A shared enzyme name is not sufficient evidence for copying a number into
the active single-cell network.

Correction:

- all 36 active reactions are mapped in one checksum-locked manifest;
- the executable SBML is inspected reaction by reaction for exact
  stoichiometry, direction, compartment, modifiers, kinetic symbols, boundary
  species, and canonicalized MathML hash;
- 12 active reactions have related published candidates;
- only `glucose_export`, `phosphoglucose_isomerase_reverse`, and
  `hepatic_glucose_output` share exact stoichiometry after explicit aliases;
- none shares the complete symbolic law, validated per-cell scale, matched
  healthy-PHH context, and held-out validation;
- the transfer guard therefore activates `0 / 36` published parameter sets and
  raises an error if code requests one prematurely.

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
- quantitative or predictive use of the 36-reaction integrated fuel network.

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
