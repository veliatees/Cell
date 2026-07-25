# Milestone 104: Frozen PHH injury assay evaluation v1

Date: 2026-07-25

## Objective

Permit a future injury model to be compared with independent donor-heldout PHH
measurements while preventing context drift, post-outcome refitting, and
unsupported predictive claims.

## Implemented

- Defined an exact identity measurement operator:
  `projected_assay_value = model_predicted_assay_value`.
- Requires exact equality across 20 record, donor, protocol, assay, unit, time,
  replicate, normalization, intervention, washout, and recovery dimensions.
- Requires lowercase SHA-256 identities for the model, parameter manifest,
  dataset, data contract, source review, and acceptance-criteria artifacts.
- Requires the model to be frozen before heldout outcome access and permits zero
  post-freeze parameter refits.
- Requires manual source review, donor-identity review, heldout-study review,
  and independent reviewer attestation.
- Produces only per-record residuals in unchanged source units.
- Rejects censored scalar residuals until a separate censored-data likelihood is
  validated.

## Deliberately not implemented

- No unit conversion or dose/time interpolation.
- No aggregate score or inferred acceptance threshold.
- No pass/fail or predictive claim.
- No parameter fitting, generalized death/recovery equation, or runtime
  cell-state coupling.

The operator is engineering-ready, but numerical projection remains at zero
until real donor-resolved trajectories and a frozen model submission arrive.
