# Milestone 173 - Durable experiment run archive v1

## Problem

The engine already had a complete `CellState + EngineRng` checkpoint. That made
one paused state resumable, but it did not provide the longitudinal substrate
needed by the project's central experiment:

- keep a cell alive across process or machine restarts;
- preserve the states that preceded a later phenotype;
- record exactly which external exposure was declared and in which unit;
- distinguish observations from interventions;
- fork one pre-event state into controlled counterfactual continuations; and
- detect silent alteration of an old record.

A directory of unrelated checkpoint JSON files cannot establish run order,
branch ancestry, transactional writes, or tamper evidence.

## Delivered

`ExperimentArchive` stores many runs in one standard-library SQLite database.
Each run begins with a complete `CellCheckpoint`, and every later record carries:

- the run identity and contiguous sequence index;
- engine elapsed time;
- a canonical payload checksum;
- the previous record checksum; and
- a checksum over the complete record envelope.

This produces one append-only SHA-256 chain per run. SQLite `BEGIN IMMEDIATE`
transactions and `synchronous=FULL` keep run creation and record append atomic.
An additional immutable run-manifest checksum covers definition, purpose,
creation time and the complete parent-fork anchor rather than protecting only
the record payloads.
The archive can be closed, reopened, verified, and resumed without re-seeding:
the complete RNG state is restored alongside the immutable cell state.

## Counterfactual lineage

A child run can fork only from a verified checkpoint. Its run metadata stores
the parent run, parent sequence index and exact parent-record hash. The child's
first checkpoint must have the same payload checksum as that anchor. Integrity
verification rejects a missing, altered or non-checkpoint parent.

Branches therefore reproduce identically until their declared inputs or future
state operators differ. This is software support for committor-style questions;
it does not make the current exploratory dynamics biologically predictive.

## External inputs and observations

Two non-causal record types accompany checkpoints:

- `external_input` preserves an input identity, type, target, scalar parameters,
  explicit units, duration, sources and notes;
- `observation` preserves unit-explicit scalar readouts without mutating state.

Every numeric scalar requires a unit. Non-finite values, backwards elapsed time,
unknown unit keys and writes to sealed runs fail closed. In v1, external-input
records deliberately declare `applied_to_cell_state = false`: a future APAP,
smoke or drug exposure may become causal only through a separately sourced,
validated intervention operator.

## Authority boundary

Run creation calls the existing whole-cell runtime authority gate. Only
`schematic_visualization` and `exploratory_execution` are accepted.
Quantitative validation, predictive execution and authoritative PHH state
coupling remain blocked. Archive integrity proves software history and
provenance, not biological validity.

## Command-line operation

`scripts/run_cell_experiment.py` starts or resumes a run and writes a complete
checkpoint at a requested cadence. For example:

```bash
PYTHONPATH=engine python3 scripts/run_cell_experiment.py \
  output/experiments/cell.sqlite3 \
  --run-id baseline-001 --steps 1000 --checkpoint-every 100

PYTHONPATH=engine python3 scripts/run_cell_experiment.py \
  output/experiments/cell.sqlite3 \
  --run-id baseline-001 --steps 1000 --checkpoint-every 100 --resume
```

The output reports integrity status and keeps predictive authority false.

## Verification

- Exact resumed state equals an uninterrupted run.
- Reopened on-disk archives preserve the complete RNG continuation.
- Fork parent identity and checkpoint hash are exact.
- Parent and child RNG instances are independent.
- Payload tampering prevents verification and resume.
- Unitless numeric inputs, backwards time and sealed-run writes fail closed.
- Unsupported scientific-authority purposes create no run.
- Focused archive, checkpoint, authority, completion and overlay suite:
  `60 passed`.
- Full Python suite: `941 passed, 2 skipped`.
- Full Vitest suite: `27` files and `196` tests passed.
- Production TypeScript/Vite build and exact browser-bundle budget gate passed:
  `919,022` initial raw JS bytes and `250,376` gzip bytes.

## Boundaries

- v1 stores full JSON checkpoint payloads without compression or delta encoding.
- It is a single-node transactional file, not yet remote object-store replication.
- It does not schedule an always-on cloud worker.
- It does not infer an intervention from an annotation.
- It does not replace donor-resolved PHH calibration or independent validation.

## Main surfaces

- `engine/cell_engine/core/experiment_archive.py`
- `scripts/run_cell_experiment.py`
- `engine/tests/test_experiment_archive.py`
- `engine/cell_engine/validation/completion_matrix.py`
