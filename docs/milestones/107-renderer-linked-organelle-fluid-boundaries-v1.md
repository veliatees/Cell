# Milestone 107 - Renderer-linked organelle fluid boundaries v1

## Scope

The numerical cytosol no longer derives all static anatomy from the placement
system's broad exclusion spheres. It now receives analytic assemblies generated
from the renderer geometry that the user sees.

## Boundary mapping

- Nuclear envelope: moving sphere tied to the rendered envelope transform.
- Bile canaliculus: capsule chain sampled from the rendered canalicular curve.
- Rough ER cisternae: oriented boxes matching rendered lamellar dimensions.
- Rough and smooth ER branches: capsule chains sampled from their rendered
  centerline curves and tube radii.
- Golgi stacks: moving oriented boxes tied to stack transforms.
- Lipid droplets: source-normalized rendered spheres.
- Mitochondria, peroxisomes and lysosomes: per-instance moving analytic
  boundaries already used by the display populations.

The moving-boundary scalar remap is tested with a translating and rotating
compound ER/Golgi-style boundary and conserves dimensionless mass.

## Claim boundary

This is a geometry-linked analytic decomposition, not a watertight
microscopy-derived mesh. Thin ER membranes remain below the coarse Eulerian grid
spacing, and no cut-cell or immersed-boundary convergence claim is made. The
geometry carries no donor morphometry, PHH pressure, viscosity or mechanical
calibration.
