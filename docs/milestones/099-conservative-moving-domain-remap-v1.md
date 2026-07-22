# Milestone 099: Conservative Moving-Domain Remap v1

## Goal

Prevent membrane or organelle motion from numerically deleting a transported
scalar when a previously fluid voxel becomes solid.

## Implemented

- Each scalar tracks the fluid mask on which its current values are defined.
- Fluid-to-solid cells transfer their amount to fluid face neighbours.
- A deterministic multi-source nearest-fluid map handles covered cells without a
  fluid face neighbour.
- Newly exposed cells begin empty unless they receive displaced amount.
- Every remap reports displaced cells, exposed cells, transferred amount and
  absolute/relative conservation residuals.
- The transport step synchronizes the moving domain even when the requested time
  increment is zero.
- Float64 storage avoids avoidable remap accumulation loss.

## Verification

A moving spherical organelle crosses a uniformly filled domain in the TypeScript
test suite. The fluid mask changes on both sides, concentrations remain
non-negative and total discrete amount is conserved to numerical precision.

## Scientific Boundary

This is a dimensionless conservative remap, not a claim about cytosolic velocity,
pressure, viscosity, diffusivity or reaction rate. It is also not yet a
fractional cut-cell or arbitrary-Lagrangian-Eulerian solver. Biological coupling
remains disabled until PHH transport evidence and validation are available.

## Files

- `src/physics/cytosolNumerics.ts`
- `src/physics/cytosolNumerics.test.ts`
- `engine/cell_engine/quantitative/cytosol_transport.py`
