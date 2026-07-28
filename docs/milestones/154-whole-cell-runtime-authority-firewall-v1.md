# Milestone 154: Whole-cell runtime authority firewall v1

## Problem

The legacy whole-cell loop contains relative `0-1` pools, normalized pathway
rates, heuristic stress weights, organelle cycles and event thresholds. These
surfaces are useful for renderer integration and software tests, but they are
not a calibrated primary-human-hepatocyte model.

Labels alone were insufficient: a caller could previously invoke `step_cell`
or `run_cell` without declaring why the schematic state was being advanced.

## Runtime Contract

Every public whole-cell step or run now requires one explicit purpose:

- `schematic_visualization`
- `exploratory_execution`
- `quantitative_validation`
- `predictive_execution`
- `authoritative_cell_state_coupling`

Only the first two purposes are permitted. The other three raise
`WholeCellRuntimeAuthorityError` before any state transition occurs.

The firewall audits four legacy surface groups:

1. normalized pool initialization;
2. heuristic metabolism and stress;
3. organelle, cargo, signaling, response and memory loops;
4. browser-local `LivingCell` animation.

All four have zero PHH context matches, quantitative authority, predictive
authority and authoritative state-coupling authority.

## Snapshot Boundary

The public snapshot now exposes:

- `whole_cell_runtime_authority`;
- the declared runtime purpose;
- whether schematic steps were executed;
- the executed step count and elapsed schematic time;
- explicit false flags for biological parameter authority, predictive use and
  authoritative state coupling.

The browser evidence panel renders these fields separately from the
source-backed `quantitative_state`.

## Energy And Redox Consequence

The six known legacy energy/redox conflicts remain visible. They have not been
relabeled as solved biology. The completion ledger now distinguishes:

- detected legacy conflicts: `6`;
- legacy quantitative-authority violations: `0`;
- legacy predictive-authority violations: `0`;
- legacy authoritative-coupling violations: `0`.

Replacing the quarantined aggregate pools still requires matched
compartment-resolved PHH states and validated trajectories.

## Verification

The milestone adds tests that prove:

- omission of `purpose` raises `TypeError`;
- schematic and exploratory execution remain available;
- quantitative, predictive and authoritative-coupling requests fail closed;
- the runtime authority snapshot reports zero scientific-authority surfaces;
- the research-preview release gate remains valid;
- the completion ledger and browser snapshot carry the new contract.

No biological value, rate, threshold or claimed accuracy was added.
