# Milestone 117 - Local membrane geometric conservation v1

## Scope

This milestone improves the dimensionless cytosol numerical test bed. It does
not assign primary-human-hepatocyte pressure, viscosity, permeability, tension,
velocity, or time-scale parameters.

## Implemented

- The smooth star-shaped outer membrane is rasterized with eight subcell volume
  samples instead of a binary cell-center mask.
- Internal grid faces use four tangential area samples for an outer-membrane
  aperture. This aperture is combined with the existing analytic organelle
  aperture.
- Local outer-membrane volume change contributes a discrete geometric
  conservation source to the pressure projection.
- Passive scalar mass uses the moving partial volumes and is conservatively
  remapped when membrane motion exposes or removes fluid volume.
- The numerical-grid time step now receives the full elapsed interval between
  moving-boundary refreshes.
- Tests cover fractional membrane cells/faces, local non-affine motion,
  projection-residual reduction, non-negativity, and moving-domain mass
  conservation.

## What This Closes

The repository now contains locally conservative smooth star-shaped
membrane-to-fluid coupling at the cut-cell scale. The completion ledger no
longer lists local conservative moving-boundary coupling as absent.

## Still Blocked

- folds with multiple radial intersections;
- remeshing, neck closure, budding, endocytosis, and exocytosis topology;
- measured event-specific membrane reservoirs and neck mechanics;
- cytosol pressure feedback into membrane mechanics;
- healthy-PHH constitutive coefficients and biological validation.

The pressure and velocity remain dimensionless renderer quantities. The new
algorithm must not be described as validated PHH CFD or fluid-structure
interaction.
