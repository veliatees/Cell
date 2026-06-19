# Milestone 017 - Cargo packet and routing engine

Status: implemented

M017 adds packet-level intracellular cargo routing. This is the first engine
piece that makes "produced material reaches its destination" non-guaranteed.
Cargo can move, wait, be delivered, retained, degraded, misrouted, or lost.

## What Was Added

- `CargoPacket` in `engine/cell_engine/core/state.py`
  - species, origin, target, current location, route plan, quality, age,
    ATP cost, motor dependency, target membrane side, state, and fate reason.
- `engine/cell_engine/cargo/routing.py`
  - hepatocyte route graph,
  - route edges,
  - packet routing,
  - success probability,
  - state-conditioned failure selection.
- Initial hepatocyte cargo packets:
  - albumin to sinusoidal face,
  - canalicular bile transporter/cargo to canalicular face,
  - lysosomal hydrolase to lysosome/endosome system,
  - misfolded secretory cargo to proteasome.
- `step_cell(...)` now routes cargo after organelle-local state updates.
- Snapshot JSON now exposes `state.cargo_packets`.

## Biological Contract

Routing success is not fixed and not guaranteed. It depends on:

- ATP pool;
- edge-specific stress axes;
- cargo quality;
- cargo age;
- energy cost;
- cytoskeleton health when motor transport is required.

Failure fate is also state-biased:

- low quality and proteotoxic stress bias degradation;
- trafficking/cholestatic stress bias misrouting;
- energy stress biases loss;
- overloaded edges bias retention.

## Boundaries

- Cargo packets are seeded at initial state; production of new cargo packets is
  not implemented yet.
- Route probabilities are structural placeholders. They are state-conditioned,
  but quantitative rates still need literature curation.
- Cargo packets do not yet consume pools or produce downstream fluxes.

## Verification

```bash
python -m unittest discover -s engine/tests -t engine
npm test -- --maxWorkers=1
npm run build
```

