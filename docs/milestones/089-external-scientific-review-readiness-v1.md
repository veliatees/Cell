# Milestone 089: External Scientific Review Readiness v1

## Goal

Replace informal whole-cell realism percentages with an auditable external
review program that states what the model represents, what it may claim, who
must review each claim, and which independent evidence is still absent.

## Implemented

- Four explicit contexts of use:
  - healthy-PHH evidence reference and research preview;
  - exact-protocol 3D-PHH glucose comparison;
  - single-hepatocyte contact geometry;
  - blocked predictive healthy-PHH digital twin.
- Ten claim-level contracts covering identity/scale, membrane/contact geometry,
  nutrition/zonation, glucose, proteins/transport, energy/redox,
  communication, cell fate/disease, genome/generative modeling and the
  whole-cell predictive claim.
- Six reviewer roles with role-specific questions and independence rules:
  PHH biology, computational liver modeling, membrane biophysics,
  hepatology/pathology, validation/uncertainty and scientific-software
  reproducibility.
- Four ordered review rounds:
  source-and-claim red team, same-assay held-out validation, prospective PHH
  experiment and independent reproduction.
- Fail-closed claim-level validation guard. No claim can be promoted beyond
  `internal_contract_ready` without a registered result artifact.
- Machine-readable JSON and generated Markdown review dossier.
- Scoped outreach templates and current official expert/network routes.
- Snapshot and browser evidence card showing current review readiness without a
  biological-accuracy percentage.

## Current Result

- Contexts of use: `4`
- Scoped claims: `10`
- Reviewer roles: `6`
- Internal review contracts ready: `10`
- Independent external review results: `0`
- Same-assay validated claims: `0`
- Prospectively validated claims: `0`
- Independent reproductions: `0`
- Predictive claims: `0`
- Whole-cell biological accuracy: `null`

These are program-record counts, not biological parameters or evidence of model
accuracy.

## Files

- `engine/cell_engine/validation/external_review.py`
- `engine/tests/test_external_review.py`
- `scripts/export_external_review_dossier.py`
- `data/validation/external_validation_program.v1.json`
- `docs/validation/external-review-dossier.md`
- `docs/validation/expert-outreach.md`

## Scientific Boundary

The first review round is ready because sources, claims, contexts and blockers
can now be inspected. The three quantitative rounds remain blocked. A reviewer
network, repository or named expert is never represented as an endorsement.
Software verification remains distinct from same-assay biological validation,
and both remain distinct from a frozen prospective prediction tested by an
independent PHH laboratory.

## Standards and Guidance

- FDA computational model credibility guidance, November 2023.
- BioModels submission and curation guidance.
- Human Cell Atlas Liver Biological Network as a liver-atlas expert route.
- EASL Basic Science Task Force as a liver-domain reviewer route.
