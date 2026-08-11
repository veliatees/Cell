# Milestone 172 - Complete evidence handoff and software boundary v1

## Problem

The completion matrix named 23 biological scopes as `partial` or
`blocked_missing_evidence`, but the unified evidence-readiness registry covered
only 19 of them. The missing handoff paths were:

- healthy-PHH p53/MDM2 damage-response dynamics;
- healthy-PHH clonal population dynamics;
- quantitative evidence for the 44 capability-atlas parameter slots; and
- healthy-PHH cytoplasm/organelle motion, which was not linked to the existing
  intracellular-mobility contract.

That mismatch meant the repository could not distinguish an external evidence
blocker from an unclassified engineering omission.

## Delivered

### Exact remaining-evidence bundle

`phh_completion_evidence_bundle_contract.v1.json` defines three independent
raw-data tables:

1. donor-resolved p53, phospho-p53, MDM2, fate and recovery trajectories;
2. donor-, clone-, genotype-, ploidy-, niche- and space-resolved population
   trajectories; and
3. source-located observations keyed to every exact capability and parameter
   slot, with the atlas quantity and unit preserved.

The intake rejects header drift, duplicate record identities, non-human or
non-PHH contexts, donor split leakage, non-finite values, mismatched uncertainty
fields, unsupported p53 or clone endpoints, unknown capability slots, and unit
or quantity drift from the capability atlas. A valid structural delivery still
authorizes zero parameters and zero state coupling.

### Full registry coverage

The unified readiness registry now has 16 checksum-verified contracts and 16
registered validators. Their target mapping is exactly equal to the 23
completion entries whose status is `partial` or `blocked_missing_evidence`.
The existing intracellular-mobility intake now also covers the explicit
healthy-PHH cytoplasm/organelle-motion gap.

### Machine-checked software boundary

`software_completion.py` classifies every declared non-closed scope as one of:

- external evidence followed by reviewed implementation;
- independent external action; or
- a representation explicitly inapplicable at whole-cell scale.

The boundary fails if an evidence-gated scope has no intake contract, if a
registry target does not correspond to an evidence-gated scope, or if any
surface attempts automatic parameter or state activation.

The current result is:

- 56 scopes audited before adding the boundary entry;
- 23 evidence-gated scopes;
- 23 registered evidence-gated scopes;
- 0 unregistered scopes;
- 0 orphan registry targets;
- 0 responsible code-only scopes;
- 1 independent external-action scope; and
- 1 scale-inapplicable scope.

The final completion matrix has 57 entries: 32 narrowly closed, 8 partial, 15
blocked on evidence, 1 external action, and 1 scale-inapplicable entry.

## Interpretation

`current_repository_implementation_complete_for_available_evidence = true`
means only that no declared scope can be responsibly promoted with code alone
before new evidence arrives. It does not mean that a future evidence-specific
implementation has already been guessed.

The same boundary keeps all of these values explicit:

- `scientific_model_complete = false`;
- `biological_validation_complete = false`;
- `digital_twin_predictive_authority = false`; and
- `biological_accuracy_pct = null`.

## Browser and export integration

The canonical Python snapshot now exports both the new intake and software
boundary. The scientific panel reports 23/23 mapped evidence-gated scopes and
zero unclassified code-only scopes while displaying predictive authority as
absent. The model-authority policy also reflects Milestone 171: the normalized
browser biochemical fixture is test-only and cannot execute in production under
any snapshot state.

## Verification

- Full Python suite: `931 passed, 2 skipped`.
- Full Vitest suite: `27` files and `196` tests passed with one worker.
- Production TypeScript/Vite build: passed with `2` initial JS chunks,
  `919,022` raw bytes, `250,376` gzip bytes, and all `6` required dynamic
  entries still deferred.
- Context export: `1` canonical snapshot plus `40` exact overlays; artifact
  bytes reduced by `90.0%` relative to the full snapshot matrix.
- Playwright render integrity: `6/6` desktop, mobile, engine-only authority,
  missing-snapshot, offscreen cadence, and deferred-module checks passed.
- In-app browser: live canvas present and moving, no horizontal overflow, no
  warning/error log, engine-only authority attributes loaded, and the new panel
  displayed `23/23`, zero code-only gaps, and no predictive authority.
- Research-preview release gate: `55` checks, `0` blockers. Predictive release
  remains blocked with `100` explicit scientific/evidence blockers.

## Main surfaces

- `data/evidence_intake/phh_completion_evidence_bundle_contract.v1.json`
- `data/evidence_intake/phh_evidence_readiness_registry.v1.json`
- `engine/cell_engine/quantitative/completion_evidence.py`
- `engine/cell_engine/validation/evidence_readiness.py`
- `engine/cell_engine/validation/software_completion.py`
- `engine/cell_engine/validation/completion_matrix.py`
- `scripts/export_engine_snapshot.py`
- `src/engineSnapshot.ts`
- `src/main.ts`
- `engine/tests/test_completion_evidence.py`
- `engine/tests/test_software_completion.py`
