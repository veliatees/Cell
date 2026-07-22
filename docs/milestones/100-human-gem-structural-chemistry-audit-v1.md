# Milestone 100: Human-GEM Structural Chemistry Audit v1

## Goal

Move the genome-scale candidate from checksum-only identity to a reproducible
reaction-level structural audit without activating FBA or claiming a healthy-PHH
flux model.

## Implemented

- Streaming parse of the pinned 43,115,559-byte SBML artifact.
- Verification against the immutable release SHA-256 before audit.
- Deterministic digests for compartment, species, reaction and gene identifiers.
- Separation of one-sided exchange/demand/sink reactions from two-sided internal
  candidates.
- Chemical formula parsing using actual element symbols only.
- Elemental, charge and joint balance residuals for assessable reactions.
- Explicit unassessable class for missing formulas and generic R/X groups.
- Committed report validation against the pinned manifest.

## Audited Result

- Compartments: `9`
- Species: `8,461`
- Reactions: `12,931`
- Gene products: `2,848`
- One-sided reactions: `1,660`
- Two-sided reactions: `11,271`
- Elementally assessable: `9,849`
- Elementally balanced / imbalanced: `9,832 / 17`
- Charge balanced / imbalanced among all two-sided reactions: `11,051 / 220`
- Jointly assessable: `9,849`
- Jointly balanced / imbalanced: `9,652 / 197`
- Jointly unassessable: `1,422`

## Scientific Boundary

An audit records what the artifact contains; it does not prove that every
imbalance is a model defect or that every balanced reaction is biologically
correct. Proton conventions, generic groups and pseudo-reactions require
reaction-level interpretation. No healthy-hepatocyte context, measured exchange
bounds, objective, solver result or flux validation is created here. All FBA
gates remain false.

## Files

- `engine/cell_engine/quantitative/human_gem_structural_audit.py`
- `scripts/audit_human_gem.py`
- `data/published_models/human_gem_v2.0.0.structural_audit.json`
- `engine/tests/test_human_gem_structural_audit.py`
