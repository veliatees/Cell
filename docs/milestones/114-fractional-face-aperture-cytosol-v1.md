# Milestone 114: fractional face-aperture cytosol v1

Date: 2026-07-26

## Scope

This milestone improves the dimensionless renderer-linked cytosol solver. It
does not assign healthy-PHH viscosity, pressure, velocity, diffusivity, or
membrane force.

## Implemented

- Analytic line-segment intersection for sphere, ellipsoid, capsule, and
  oriented-box obstacles.
- Four deterministic midpoint channels per positive grid face.
- A conservative centerline fallback for features narrower than the four face
  channels.
- Fractional open-face weights in divergence, pressure projection, passive
  advection, and passive diffusion.
- Partial-cell fluid-volume fractions from the existing 2x2x2 occupancy
  quadrature.
- Conservative passive-scalar remapping when moving obstacles change either a
  binary domain mask or a partial-cell volume.
- Tests showing reduced transport through a thin barrier, conservation of
  partial-cell scalar mass, and deterministic apertures.

## Boundary

This is an embedded-boundary numerical approximation, not a watertight
microscopy mesh or a biological CFD calibration. Smooth analytic obstacles may
still differ from donor organelle geometry, membrane topology change is absent,
and dimensionless pressure cannot push the membrane.
