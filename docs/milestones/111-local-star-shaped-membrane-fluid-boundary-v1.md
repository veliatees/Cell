# Milestone 111: local star-shaped membrane-fluid boundary v1

Date: 2026-07-26

## Scope

This milestone makes the dimensionless cytosol domain read the current plasma
membrane surface rather than only the canonical rest shape. It is a geometry
coupling improvement, not a healthy-PHH membrane constitutive model.

## Implemented

- `ReferenceMembraneRadialBoundary` samples the current membrane mesh into a
  32 x 16 reference-space angular field.
- The global volume-preserving contact map is inverted before sampling. The
  local field therefore contains only the residual and cannot apply the affine
  deformation twice.
- Both sparse aqueous tracers and the pressure-projection grid read the same
  dynamic radius function.
- Missing angular bins are filled deterministically from the nearest sampled
  neighborhood.
- Tests verify the rest shape, a local radial perturbation, and affine
  double-count prevention.

## Exact boundary

The representation supports smooth star-shaped surfaces with one radius per
direction. It does not support multiple ray intersections, overhangs, sealed
necks, detached vesicles, budding, fusion, fission, or topology changes.
Pressure feedback and locally conservative membrane-face fluxes remain off.
