# Milestone 093: Metabolic Constraint Shell v1

## Goal

Prepare a genome-scale stoichiometric boundary around validated dynamic cores
without pretending that flux-balance analysis supplies measured single-cell
rates or time trajectories.

## Implemented

- Fail-closed Human-GEM/Human1 artifact contract.
- Required model release, checksum, SBML path, license and mass/charge audit.
- Required hepatocyte extraction algorithm, donor/cohort, nutrition, zonation,
  transcriptome and proteome context.
- Required objective, measured exchange bounds, thermodynamic constraints,
  enzyme capacities and pinned solver.
- Required alternate-optimum audit, flux-variability intervals, residuals,
  blocked-reaction diagnostics and independent flux validation.

## Current Result

FBA, FVA, thermodynamic FBA, enzyme-constrained FBA, dynamic-rate
initialization and scientific-validation coupling are all disabled. No model
artifact has been downloaded or silently pinned by this milestone.

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
