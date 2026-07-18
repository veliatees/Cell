# Milestone 081 - Stochastic contact placement and scientific overlays v1

## Goal

Remove the last fixed-anchor contact cue and establish one fail-closed contract
for future cell, bacterium, and virus encounters in the single-hepatocyte scene.

The random variable is the external body's approach trajectory when a scenario
explicitly requests a stochastic prior. The contact surface is not random
screen decoration: at each instant it is the geometric consequence of the two
declared shapes and poses.

## Stochastic placement contract

`place_external_body_at_isotropic_approach` samples a direction uniformly over
solid angle using the engine RNG and an explicit seed. The same seed reproduces
the same placement; different seeds do not share a fixed membrane anchor.

This isotropic sampler is a neutral diagnostic prior, not a measured liver
distribution. A sinusoid-flow, tissue-neighbour, bacterial, or viral scenario
must provide its own evidence-backed trajectory model when one is available.

`place_external_body_at_surface_gap` then aligns actual support points from the
supplied sphere, capsule, or convex polyhedron. Consequently:

- a larger body is placed farther from the hepatocyte centre at the same
  requested surface gap;
- orientation and asymmetric shape affect the first-contact point;
- a missing or non-positive size fails closed;
- no generic virus, bacterium, or cell radius is invented;
- a later trajectory can move the contact continuously over the membrane.

The normal runtime still contains exactly one hepatocyte and no external body.

## Contact-surface rendering contract

The browser may draw a filled contact surface only when the engine supplies all
of the following for the current `enter` or `stay` event:

- geometric contact is true;
- contact input is active;
- a finite positive patch area exists;
- at least three finite polygon vertices exist.

There is no fallback ring, guessed radius, fixed glowing point, or renderer-only
contact patch. Mixed round/polyhedral contacts currently expose closest points
and contact state but not a resolved finite area, so no area marker is drawn.
The external object itself remains visible when it exists in the engine world.

## Scientific-view overlays

The organelle-network scene now exposes four independent layers:

- a projected `10 um` physical scale bar derived from the active
  micrometre-to-world conversion;
- basolateral, lateral, and apical membrane-domain colours;
- three central slices of the exported RDME lattice, loaded from
  `cell_voxel_field.json` and labelled with its actual `dxUm`;
- contact geometry, enabled only when the engine snapshot contains an external
  body and subject to the polygon gate above.

The voxel layer is a computational partition, not intracellular
ultrastructure. Domain colours show topology on the canonical proxy surface;
they do not claim donor-specific domain areas. The regular hepatocyte boundary
is still not a measured individual human-cell mesh.

## Evidence boundary

The active cell scale remains the normal-control human 3D median volume from
Segovia-Miranda et al. 2019. Fluid-mosaic and curvature literature support the
membrane architecture, but no cross-system diffusion coefficient, bending
modulus, adhesion strength, receptor density, or rupture threshold is promoted
to a healthy-human-hepatocyte parameter here.

This milestone does not enable:

- receptor occupancy or binding kinetics at a contact;
- adhesion force, contact pressure, or junction permeability;
- a protein-activity heat map;
- donor-specific contact-area statistics;
- stochastic liver encounter frequencies;
- viral entry, bacterial invasion, or downstream biochemical effects.

Those outputs require object-specific size/shape/trajectory evidence and
membrane-domain-resolved molecular measurements. Until then they remain null.

## Verification

Tests cover seeded reproducibility, direction diversity, support-point
placement for different declared sizes, invalid-input rejection, and the
renderer rule that unknown area never becomes a visual patch.

## Sources

- Singer and Nicolson 1972: https://doi.org/10.1126/science.175.4023.720
- Helfrich 1973: https://doi.org/10.1515/znc-1973-11-1209
- Segovia-Miranda et al. 2019: https://doi.org/10.1038/s41591-019-0660-7
- Evans et al. 1976: https://doi.org/10.1016/S0006-3495(76)85713-X
- Rawicz et al. 2000: https://doi.org/10.1016/S0006-3495(00)76295-3
