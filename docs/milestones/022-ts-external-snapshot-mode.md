# Milestone 022 - TS external snapshot mode

Status: implemented

M022 starts connecting the TypeScript visualizer to the Python scientific engine.
The 3D scene still renders locally, but the UI can now load a Python engine
snapshot over HTTP/local replay and show a diagnostic when no snapshot is
available.

## What Was Added

- `src/engineSnapshot.ts`
  - snapshot type definitions;
  - HTTP/local snapshot loader;
  - summary builder for UI readouts;
  - WebSocket stream boundary;
  - diagnostic result for missing/invalid snapshots.
- `src/engineSnapshot.test.ts`
  - loader, summary, diagnostics, endpoint and WebSocket-unavailable tests.
- `scripts/export_engine_snapshot.py`
  - exports Python engine snapshots for Vite/local replay.
- `src/main.ts`
  - report panel now shows Python engine status when a snapshot is available;
  - report panel shows a clear diagnostic when it is not.

## Usage

Generate a local replay snapshot:

```bash
PYTHONPATH=engine python scripts/export_engine_snapshot.py --out public/engine-snapshot.json
```

Then run:

```bash
npm run dev
```

The app loads `/engine-snapshot.json` by default. A custom endpoint can be
selected with:

```text
http://127.0.0.1:5173/?engineSnapshot=/some-snapshot.json
```

## Contract

- The visualizer does not invent Python engine state.
- Missing snapshots produce diagnostics, not a blank render.
- HTTP/local replay is supported now.
- WebSocket streaming has a typed boundary for live mode.

## Boundaries

- The 3D organelle scene still uses the existing TypeScript visual model.
- Python state is currently shown as readout/diagnostic data, not yet used as
  the sole visual driver.
- A live Python HTTP/WebSocket server is not implemented yet.

## Verification

```bash
python -m unittest discover -s engine/tests -t engine
npm test -- --maxWorkers=1
npm run build
```

