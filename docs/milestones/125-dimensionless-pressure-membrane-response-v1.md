# Milestone 125 - Dimensionless pressure-membrane response v1

## Scope

This milestone creates a numerical pressure-to-shape candidate and the tests
needed before any fluid-structure feedback can be considered. It does not apply
pressure to the runtime hepatocyte.

## Implemented

- Triangle pressure traction is distributed to mesh vertices with explicit
  action-reaction and torque diagnostics.
- Surface-mean pressure is removed from the shape mode so uniform pressure does
  not invent expansion in a model with no calibrated cortex compliance.
- Candidate displacement is bounded, enclosed volume is corrected around the
  mesh centroid, and a backtracking line search rejects topology failure or
  self intersection.
- Pressure work, maximum displacement, volume residual, and acceptance reason
  are returned with the candidate.
- Tests cover uniform-pressure force balance, non-uniform shape response,
  pressure work, volume preservation, invalid inputs, and zero runtime
  authority.

## Boundary

Compliance and displacement values used in tests are dimensionless software
fixtures. The kernel has no PHH pressure, membrane tension, bending modulus,
cortex adhesion, hydraulic permeability, or relaxation time. Its candidates
cannot alter the renderer or engine until those quantities and matched
deformation trajectories pass independent validation.
