# Milestone 115: PHH reaction-evidence intake v1

Date: 2026-07-26

## Scope

This milestone creates the data plane needed to fill the active network's 36
reactions by 12 typed evidence slots. It does not activate a reaction.

## Implemented

- A versioned 45-column CSV contract.
- Exact active reaction-ID and evidence-slot validation.
- Slot-specific value-kind and canonical-unit-target checks.
- Preservation of source-reported values, units, statistics, uncertainty,
  enzyme identity, isoform, compartment, membrane side, direction, cofactors,
  active state, assay temperature, and pH.
- Strict human/PHH, human-liver bridge, and purified-human-enzyme context roles.
- Donor-disjoint splits and study-disjoint independent held-out data.
- Frozen-model digest and prediction/observation IDs for held-out validation.
- Structural coverage reporting for all 432 slots.

## Boundary

No automatic unit conversion, parameter fit, atlas mutation, reaction
activation, or cell-state coupling is permitted. Even a structurally complete
delivery still requires manual primary-source and cross-record biochemical
adjudication.
