# Milestone 097: Pinned Human-GEM and Completion Ledger v1

## Goal

Replace ambiguous statements such as "CFD is done" or "the hepatocyte is 95%"
with exact, testable scopes while removing the model-artifact ambiguity that
blocked future genome-scale work.

## Implemented

- Pinned the official Human-GEM `v2.0.0` release by tag, commit, byte size and
  SHA-256 without adding a 43 MB binary to Git.
- Added an idempotent fetch tool that accepts an existing artifact only when its
  size and SHA-256 match the manifest.
- Upgraded the metabolic shell to v2 while leaving every FBA/FVA and scientific
  coupling gate disabled.
- Added a 26-entry completion matrix with five explicit statuses:
  `closed`, `partial`, `blocked_missing_evidence`,
  `external_action_required`, and `not_applicable_at_model_scale`.
- Derived matrix metrics from the live cytosol, reaction, energy/redox, protein,
  memory, capability, metabolic and external-validation contracts.
- Added fail-closed tests that reject unearned reaction, cytosol, FBA or external
  validation promotion.

## Current Result

- Scoped closed items: 4
- Partial items: 6
- Blocked for context-matched evidence: 14
- External-action requirements: 1
- Inapplicable whole-cell abstraction: 1
- Whole-cell biological accuracy percentage: `null`

The four closed scopes are the dimensionless cytosol numerics, quarantine of the
legacy 0.52 cytosol fraction, semantic separation of passive fluid from active
cargo, and exact Human-GEM artifact identity. None of these claims a calibrated
whole-cell hepatocyte.

## Scientific Boundary

Explicit water molecules are intentionally not a target for the whole-cell
renderer. Tracer points remain massless visualization samples. A quantitative
aqueous phase must instead use species concentration fields, diffusion and
advection at an appropriate coarse-grained scale.

Pinning a generic reconstruction does not identify a healthy PHH flux state.
FBA remains blocked until a PHH extraction context, measured boundaries,
objective, solver, audit and independent validation are frozen.

## Primary Sources

- Human-GEM official repository and release:
  https://github.com/SysBioChalmers/Human-GEM/releases/tag/v2.0.0
- Robinson et al. (2020), Human1 atlas:
  https://doi.org/10.1126/scisignal.aaz1482
- Grankvist et al. (2024), human liver tissue isotope tracing and MFA:
  https://doi.org/10.1038/s42255-024-01119-3

## Files

- `data/published_models/human_gem_v2.0.0.manifest.json`
- `scripts/fetch_human_gem.py`
- `engine/cell_engine/quantitative/metabolic_constraint_shell.py`
- `engine/cell_engine/validation/completion_matrix.py`
- `data/validation/hepatocyte_completion_matrix.v1.json`
- `engine/tests/test_completion_matrix.py`
