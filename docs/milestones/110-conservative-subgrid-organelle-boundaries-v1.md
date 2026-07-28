# Milestone 110: conservative subgrid organelle boundaries v1

Date: 2026-07-26

## Scope

This milestone prevents thin renderer-linked ER, canalicular, and Golgi
boundaries from disappearing when their thickness is below one Eulerian grid
cell. It is a dimensionless numerical treatment, not a microscopy-derived
organelle reconstruction.

## Implemented

- Optional `conservative_subgrid` boundary sampling on analytic obstacles.
- Deterministic 2 x 2 x 2 subcell occupancy quadrature.
- A conservative half-cell-diagonal intersection fallback when an even thinner
  surface falls between all eight samples.
- Fractional occupancy diagnostics and a dimensionless obstacle-volume
  estimate.
- Thin rough-ER cisternae, ER/canalicular capsule chains, and Golgi envelopes
  use the new path.
- A refinement test verifies that thin-box volume error decreases over three
  grid resolutions.

## Numerical meaning

Any intercepted cell is currently excluded from the binary no-flux projection
mask. Fractional occupancy is measured, but face-aperture-weighted cut-cell
fluxes are not yet solved. This is conservative and stable, though locally
over-blocking at coarse resolution.

## Remaining boundary gap

- Watertight donor- or microscopy-derived organelle meshes.
- Fractional face-aperture finite-volume flux weighting.
- Registered-mesh grid convergence and independent microscopy validation.
