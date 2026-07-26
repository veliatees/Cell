# Milestone 140: Reaction-level PHH evidence manifest v1

## Purpose

Convert broad statements such as "more active-enzyme data are needed" into a
machine-readable list of exact Human-GEM reactions, evidence-gap classes and
required research fields.

## Construction

The manifest is the union of:

- `17` adaptive FASTCORE output reactions that remain blocked;
- `527` all-donor GPR reactions blocked in generic Human-GEM;
- `150` reactions supported in exactly six of seven donors;
- adaptive FASTCORE non-core support reactions lacking all-donor evidence;
- all `1,801` GPR reactions with zero-of-seven total-proteome support.

Overlaps are retained as multiple gap codes on one reaction. No weighted score,
empirical cutoff or automatic priority value is assigned.

## Pinned Result

- unique manifest reactions: `4,895`;
- adaptive FASTCORE non-core support reactions: `2,860`;
- non-core support without a GPR annotation: `2,177`;
- non-core support with a GPR but zero-of-seven donor support: `401`;
- non-core support with partial donor support: `282`.

Each record preserves reaction identity, name, GPR, gene products, exact donor
support, generic consistency, adaptive selection/blocking and ordered gap
codes.

## Required Research Output

The intake requests reaction identity, species, cell type, health state,
donor/cohort metadata, age, sex, zonation or oxygen context, culture format,
assay type, active-versus-total entity, compartment/domain, value, unit,
uncertainty, sample size, timepoint, medium/exposure conditions, detection
limit, exact DOI/accession and exact table/figure/row location.

## Scientific Boundary

The manifest is a research queue, not a model-edit command. It cannot
automatically alter a bound, include or exclude a reaction, authorize FBA, or
drive a runtime rate. Missing proteomics remains missing evidence rather than
proof of inactivity.
