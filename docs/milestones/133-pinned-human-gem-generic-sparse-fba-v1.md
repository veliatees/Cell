# Milestone 133: Pinned Human-GEM generic sparse FBA v1

## Purpose

Verify that the checksum-pinned Human-GEM artifact can be solved end to end
without replacing its encoded SBML/FBC objective or bounds and without
presenting the result as healthy-PHH biology.

## Implemented

- Exact sparse stoichiometric matrix from the verified loader.
- Exact active FBC objective `obj`.
- Objective reaction `MAR13082`, named
  `Generic human cell biomass reaction`, with coefficient `1`.
- Pinned SciPy `1.17.1` and HiGHS linear programming.
- Original model bounds with no project-selected exchange context.
- Mass-balance, bound, solver-status and finite-result checks.
- Reaction-order flux-vector digest.
- Explicit statement that the selected optimum is not proven unique.

## Pinned Result

- solver status: `optimal`;
- generic objective value: `124.86814837744569`;
- reactions carrying at least `1e-9` absolute flux in the selected optimum:
  `2,566`;
- maximum mass-balance residual: `5.229594535194337e-12`;
- maximum bound violation: `1.9895196601282805e-13`.

The compact result is committed in
`data/published_models/human_gem_v2.0.0.generic_fba_audit.json`.

## Scientific Boundary

The native objective is a generic reconstruction objective, not a measured
healthy-hepatocyte objective. The generic exchange bounds are not a donor,
zonation or nutritional context. The selected flux vector is neither a
measurement nor a unique biological prediction and cannot initialize dynamic
reaction rates or couple to cell state.
