# Milestone 108: donor-resolved cellular-memory intake v1

Date: 2026-07-26

## Scope

This milestone adds the data plane required before a past exposure can become an
executable hepatocyte memory law. It does not create a memory half-life, stress
score, epigenetic transition, or future-response multiplier.

## Implemented

- A versioned 34-column long-form CSV contract at
  `data/evidence_intake/phh_cellular_memory_trajectory_contract.v1.json`.
- Exact primary-human-hepatocyte, substrate-id, phase, unit, and denominator
  validation.
- Explicit separation of physical-substrate, future-response, inheritance, and
  erasure measurements.
- A complete candidate requires, in the same donor and trajectory:
  - physical-carrier baseline;
  - write-phase carrier measurement;
  - persistence measurement after verified trigger removal;
  - matched first-challenge response;
  - matched rechallenge response.
- Donor split-leakage and independent-heldout-study leakage rejection.
- Direct-trace storage now also requires a named physical-substrate assay and
  persistence evidence record ids.

## Fail-closed boundary

Even a structurally complete delivery cannot activate a model automatically.
Manual primary-source review, a checksum-frozen write/read/decay operator, and a
donor- and study-disjoint held-out result remain required. Current delivered
record count and authorized law count are both zero.

## Verification

Software fixtures test absent delivery, structural completeness, verified
washout timing, split leakage, non-PHH rejection, and unknown-substrate
rejection. Fixtures are never exported as biological observations.
