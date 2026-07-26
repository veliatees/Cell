# Milestone 112: donor-resolved PHH active-cargo trajectory intake v1

Date: 2026-07-26

## Scope

This milestone creates the evidence plane needed to replace the renderer-only
active-cargo paths with measured primary-human-hepatocyte transport data.

## Implemented

- A versioned 39-column CSV contract for raw donor-resolved 3D cargo
  trajectories.
- Required time, xyz position, localization uncertainty, acquisition interval,
  cargo label, route compartments, track system, motor identity, ATP context,
  and observed event fields.
- Strict human PHH context checking.
- Donor-disjoint calibration/internal-validation/held-out splits.
- Independent-held-out study leakage rejection.
- Route consistency checks across cargo label, assay, reference frame, track,
  motor, origin, and destination.
- A structural gate requiring at least three positions, departure, in-transit,
  and an observed arrival/fusion/fission endpoint.

## Authority boundary

Structural completeness does not infer velocity, fit a motor law, activate a
route, or change cell state. The current delivery contains zero PHH routes.
Manual source review, a frozen route model, and donor- and study-disjoint
route-level evaluation are still required.
