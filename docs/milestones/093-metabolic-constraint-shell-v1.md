# Milestone 093: Metabolic Constraint Shell v2

## Goal

Prepare a genome-scale stoichiometric boundary around validated dynamic cores
without pretending that flux-balance analysis supplies measured single-cell
rates or time trajectories.

## Implemented

- Fail-closed Human-GEM/Human1 artifact contract.
- Official Human-GEM `v2.0.0` release pinned to commit `635f533`.
- Official 43,115,559-byte SBML artifact pinned to SHA-256
  `cc5a4383c6116b0c91f4db089cc640f29aec7e840249b573b74d3792c9ca4a7a`.
- Namespace-aware inspection of the pinned SBML verified 9 compartments,
  8,461 metabolites, 12,931 reactions and 2,848 genes.
- Manifest and checksum-verifying fetch tool; the 43 MB model is not vendored.
- Required SBML loading, license, mass/charge and artifact checks remain explicit.
- Required hepatocyte extraction algorithm, donor/cohort, nutrition, zonation,
  transcriptome and proteome context.
- Required objective, measured exchange bounds, thermodynamic constraints,
  enzyme capacities and pinned solver.
- Required alternate-optimum audit, flux-variability intervals, residuals,
  blocked-reaction diagnostics and independent flux validation.

## Current Result

The generic reconstruction's identity is reproducibly pinned, but it is not
loaded by runtime. FBA, FVA, thermodynamic FBA, enzyme-constrained FBA,
dynamic-rate initialization and scientific-validation coupling are all
disabled. Healthy-PHH context extraction, measured exchange bounds, a measured
objective, mass/charge audit and independent flux validation remain absent.

## Scientific Boundary

A genome-scale reconstruction defines a feasible stoichiometric space. Its
solution depends on context extraction, exchange bounds and objective, and does
not become a healthy single-hepatocyte flux measurement. Dynamic pathways remain
separate and can only be constrained after compatible boundaries and validation
are frozen.

## Primary Reference

- Robinson et al. (2020), Human1 metabolism atlas:
  https://doi.org/10.1126/scisignal.aaz1482
- Human-GEM versioned repository:
  https://github.com/SysBioChalmers/Human-GEM

## Files

- `engine/cell_engine/quantitative/metabolic_constraint_shell.py`
- `engine/tests/test_metabolic_constraint_shell.py`
- `data/published_models/human_gem_v2.0.0.manifest.json`
- `scripts/fetch_human_gem.py`
