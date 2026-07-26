# Milestone 128: Healthy-PHH metabolic execution bundle v1

## Purpose

Define the complete, reproducible package required before the pinned Human-GEM
reconstruction may be treated as a healthy-hepatocyte constraint model.

## Required Package

The checksum-frozen bundle contains ten artifacts:

1. context-extracted model;
2. deterministic context-extraction report;
3. measured exchange bounds;
4. explicit objective specification;
5. measurement-to-model scale operator;
6. pinned solver manifest;
7. FBA result;
8. FVA result;
9. infeasibility/relaxation report;
10. donor- and study-disjoint independent validation.

The gate verifies the exact Human-GEM v2.0.0 release identity, every artifact
checksum, healthy primary-human-hepatocyte context, development/heldout
separation, reaction-identity audit, structural-exception resolution, solver
tolerances, numerical residuals, explicit units and manual source review.

## Prohibited Shortcuts

- Generic Human-GEM is not relabelled as a healthy-PHH model.
- Transcript or protein abundance is not treated as flux.
- An optimizer objective is not treated as a measurement.
- Reported exchange means do not replace uncertainty bounds.
- No bound, objective or unit conversion is imputed automatically.
- A complete bundle does not automatically run FBA or modify dynamic rates.

## Current Result

The repository contains the gate and generic numerical self-tests, but zero PHH
execution bundles. FBA, FVA and runtime flux coupling therefore remain disabled.
