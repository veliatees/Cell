# Milestone 116: PHH energy/redox trajectory intake v1

Date: 2026-07-26

## Scope

This milestone creates a donor-resolved time-series intake for the 38 explicit
energy/redox pools. It does not initialize a pool or fit a process rate.

## Implemented

- A versioned 47-column CSV contract.
- Exact pool, molecule, and compartment matching.
- Raw time, value, unit, uncertainty, oxygen, nutrient, viability, spatial, and
  perturbation context.
- Direct compartment-targeting validation and same-assay sensor calibration.
- At least three strictly increasing points per trajectory.
- One predeclared split-manifest digest across the delivery.
- Donor-disjoint development and validation records.
- Sealed, study-disjoint independent held-out trajectories.
- Pool-level reporting of calibration plus held-out structural coverage.

## Boundary

Whole-liver measurements cannot be allocated to organelles. Uncalibrated
signals cannot become concentrations. Structurally complete trajectories still
cannot initialize compartments, fit rates, couple cell state, or establish
predictive validity without manual review and approved measurement operators.
