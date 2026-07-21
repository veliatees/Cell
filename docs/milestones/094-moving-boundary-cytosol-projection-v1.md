# Milestone 094: Moving-Boundary Cytosol Projection v1

## Goal

Replace independent decorative cytosol motion with one numerical field that
shares the rendered membrane coordinate system and recognizes moving organelle
volumes, without assigning unmeasured healthy-PHH fluid units.

## Implemented

- A coarse, cell-centered three-dimensional Eulerian velocity grid.
- A Jacobi pressure-projection step that reduces numerical divergence.
- The same volume-preserving affine membrane map used by the renderer, including
  an exact inverse map for tracer integration.
- Analytic moving sphere, ellipsoid and capsule obstacles with a spatial hash.
- Renderer-matched capsule boundaries for instanced mitochondria and sphere
  boundaries for peroxisomes, lysosomes and lipid droplets.
- Motion-derived obstacle boundary velocity and dimensionless pressure/reaction
  diagnostics.
- Explicitly disabled pressure feedback to membrane mechanics.

## Verification

Tests cover deterministic seeded fields, divergence reduction, moving-obstacle
domain rebuilding, sphere/ellipsoid/capsule collision geometry and exact
forward/inverse membrane mapping.

## Scientific Boundary

Grid velocity is measured in renderer world units per renderer second. Pressure
is a dimensionless projection variable. Neither is a healthy-hepatocyte
measurement, and neither may initialize reactions, membrane forces or a
poroelastic constitutive model. Large static anatomy still uses conservative
sphere proxies; this is not a mesh-resolved CFD boundary.

## Files

- `src/physics/cytosolNumerics.ts`
- `src/physics/cytosolNumerics.test.ts`
- `src/physics/intracellularFluid.ts`
- `src/main.ts`
