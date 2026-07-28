# Milestone 113: donor multimodal generative-data contract v1

Date: 2026-07-26

## Scope

This milestone upgrades the VAE/scVI boundary from a model-family declaration
to an auditable donor-linked data intake. It does not train a model.

## Implemented

- A strict JSON delivery contract for measured adult primary-human-hepatocyte
  samples and feature definitions.
- Donor-disjoint train, validation, and test splits before preprocessing.
- Study-disjoint test data.
- Required assay-batch and technical covariates.
- Explicit accounting for age, sex, genotype, zonation, nutrition state, and
  disease history as observed or missing. Unknown values cannot be silently
  imputed.
- Feature-level modality, assay, unit, value semantics, source, and missingness
  semantics.
- Generated records are prohibited from measured training data.
- Every feature is barred from directly initializing the mechanistic engine.
- The future evaluation contract requires donor-held-out posterior predictive,
  batch-effect, within-donor variance, provenance, and mechanistic-constraint
  reports.

## Current state

No qualifying donor manifest is loaded, no model is trained, and no synthetic
cell can modify the engine. A single aggregate accuracy score is explicitly
insufficient.
