# Milestone 103: Donor-disjoint PHH injury intake v1

Date: 2026-07-25

## Objective

Make future donor-resolved APAP and cholestasis trajectories machine-auditable
without treating a delivered spreadsheet as validated biology.

## Implemented

- Added a strict CSV loader for the existing 19 required and 10 conditional
  fields.
- Requires one versioned header with no duplicate, missing, or silently ignored
  columns.
- Rejects non-finite values, non-human/non-PHH records, incomplete
  intervention or uncertainty pairs, unqualified censored records, and invalid
  cell-normalized records.
- Rejects duplicate record identities and duplicate
  donor-replicate-condition-time-assay observations.
- Defines donor identity as `source_study_id + donor_id`.
- Rejects a donor appearing in more than one split role.
- Rejects an `independent_heldout` source study appearing in calibration or
  internal validation.
- Computes checksums and counts without promoting any parameter or cell state.

## Scientific boundary

A structurally valid CSV remains
`structurally_valid_manual_primary_source_review_required`. Anonymous donor
labels cannot prove cross-study identity, and the software cannot replace
primary-source review. The production snapshot currently finds no delivered
trajectory file, so all biological-data and validation-result counts are zero.

## Files

- `engine/cell_engine/quantitative/phh_injury_trajectory.py`
- `data/evidence_intake/phh_injury_trajectory_contract.v1.json`
- `engine/tests/test_phh_injury_trajectory.py`
