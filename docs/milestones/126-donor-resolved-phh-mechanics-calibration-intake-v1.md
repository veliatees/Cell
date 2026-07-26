# Milestone 126: Donor-resolved PHH mechanics calibration intake v1

## Purpose

Make the pressure-to-membrane candidate data-ready without assigning a healthy
primary-human-hepatocyte tension, bending modulus, cortex modulus, viscosity,
hydraulic permeability, poroelastic diffusivity, pressure, or relaxation time.

## Implemented

- A versioned 48-column contract for healthy-PHH mechanics evidence.
- Fifteen explicit geometry, loading and constitutive quantity identities with
  exact canonical units and no automatic conversion.
- Separate `raw_observation` and `reported_parameter` records.
- Raw-artifact, fitting-report and protocol-report SHA-256 verification.
- Same donor, cell, assay, quantity, coordinate frame and acquisition-context
  checks within each trajectory.
- A minimum three-point baseline/loading/relaxation structural gate.
- Same-cell mesh and spatial boundary-condition requirements for an FSI-ready
  trajectory.
- Donor split-leakage and independent-heldout study guards.
- A snapshot and completion-ledger surface that remain biologically fail closed.

## Current Result

The contract targets fifteen quantities and contains zero delivered records.
Consequently:

- spatial-FSI-ready PHH trajectories: `0`;
- quantitatively authorized mechanics parameters: `0`;
- runtime membrane feedback: disabled.

## Scientific Boundary

A complete CSV is only structurally reviewable. It does not authorize fitting,
parameter transfer, membrane feedback or a biological mechanics claim. A
renderer deformation, cell-line experiment, non-human assay, aggregate liver
measurement or mesh alone cannot initialize healthy-PHH mechanics.

## Verification

Tests cover valid raw trajectories, unit and context mismatch, artifact checksum
failure, incomplete parameter provenance, donor leakage and heldout-study
leakage.
