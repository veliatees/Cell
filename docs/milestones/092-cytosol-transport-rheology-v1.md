# Milestone 092: Cytosol Transport and Rheology Contract v1

## Goal

Represent the cell interior as a moving aqueous phase embedded in a crowded,
poro-viscoelastic cytoplasm while refusing to invent healthy primary-human-
hepatocyte rheology or reaction-rate corrections.

## Implemented

- A two-phase material contract: aqueous cytosol plus cytoskeleton, organelles,
  membranes and macromolecular obstacles.
- Advection-diffusion-reaction balance:
  `partial_t(c_i) + div(u*c_i) = div(D_i*grad(c_i)) + R_i(c)`.
- Species-specific transport and reaction-level coupling gates.
- Explicit quarantine of the legacy `0.52` cytosol volume fraction: it may
  support the exploratory runtime but cannot initialize quantitative fluid or
  reaction models.
- `1,600` sparse renderer tracers and `220` short trails. These counts are
  renderer budgets, not molecular abundance or fluid-density measurements.
- Seeded, temporally correlated rotational modes; tracer motion avoids reserved
  organelle volumes.
- The exact membrane contact map is reused: axial scale `a`, tangential scales
  `1/sqrt(a)`, and determinant `a * (1/sqrt(a))^2 = 1`.
- Pause, domain-boundary, reproducibility, obstacle and volume-map tests.

## Current Result

- Cross-context rheology observations retained: `8`
- Healthy-PHH numerical rheology parameters: `0`
- Quantitative poroelastic solvers: `0`
- Reaction-fluid couplings: `0`
- Qualitative moving-domain tracer layers: `1`

## Scientific Boundary

The visual field is not water molecules, concentration, diffusion, pressure or
a measured PHH velocity. It gives the aqueous phase coherent movement and
membrane consistency only. Fluid can change chemistry through local
concentrations and boundary fluxes after species- and reaction-specific
validation; it cannot multiply every reaction by one viscosity factor.

No matched healthy primary-human-hepatocyte intracellular rheology dataset was
identified in this review. Values from cancer lines, immortalized lines, CHO or
MDCK cells remain cross-context observations and do not parameterize the PHH.

## Primary References

- Moeendarbary et al. (2013), poroelastic cytoplasm:
  https://doi.org/10.1038/nmat3517
- Kwapiszewska et al. (2020), scale-dependent cytoplasmic nanoviscosity:
  https://doi.org/10.1021/acs.jpclett.0c01748
- Swaminathan et al. (1997), intracellular GFP rotation and translation:
  https://doi.org/10.1016/S0006-3495(97)78835-0
- Guo et al. (2017), size- and speed-dependent cytoplasmic mechanics:
  https://doi.org/10.1073/pnas.1616310114

## Files

- `engine/cell_engine/quantitative/cytosol_transport.py`
- `engine/cell_engine/validation/reaction_evidence_atlas.py`
- `src/physics/intracellularFluid.ts`
- `src/physics/intracellularFluid.test.ts`
- `src/main.ts`
