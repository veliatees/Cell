# Milestone 124 - Non-star-shaped closed-mesh cytosol domain v1

## Scope

This milestone removes the star-shaped radius function as a hard numerical
requirement for the cytosol grid. It does not switch the current renderer to a
microscopy-derived membrane.

## Implemented

- A projection grid accepts exactly one outer-domain representation: a radial
  boundary or a provider returning an audited closed triangle mesh.
- Mesh containment drives the existing eight-sample cell volume fractions and
  four-sample face-area fractions.
- The same moving-domain geometric-conservation and passive-scalar remap paths
  remain active.
- A concave L-prism test proves that a non-star-shaped domain retains its notch
  and converges to the expected enclosed volume.
- Biological units, pressure, velocity, mechanics, and species coupling remain
  absent.

## Boundary

The live hepatocyte renderer still uses its smooth star-shaped membrane
residual. The closed-mesh path is a verified numerical option awaiting a
registered donor mesh. Remeshing, neck closure, budding, endocytosis,
exocytosis, and changes in mesh connectivity are not implemented.
