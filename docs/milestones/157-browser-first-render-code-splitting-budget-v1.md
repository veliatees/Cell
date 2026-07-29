# Milestone 157 - Browser first-render code splitting and budget v1

## Problem

The production build emitted one 1,042.19 kB JavaScript entry chunk
(283.44 kB in Vite's gzip report). It synchronously included code that is not
required to construct the first hepatocyte frame:

- the complete engine-snapshot validator and report summarizer;
- the PDB parser used for real protein structures;
- bloom-composer, render-pass and output-pass modules.

The context-overlay matrix removed repeated JSON parsing, but it did not prevent
these JavaScript modules from entering the initial parse and execution graph.

## Implemented boundary

- The snapshot endpoint resolver is a small standalone module.
- The full snapshot interpreter is loaded through one cached dynamic import.
- Concurrent context requests share both the dynamic module promise and the
  existing canonical-snapshot request cache.
- PDBLoader is requested only when the protein structure or embedded real
  protein layer needs it.
- Four bloom/post-processing entry modules are requested only after two render
  calls finish within the explicit engineering frame budget.
- Two consecutive render calls above 45 ms lower only visual cost: bloom is
  released, backing-pixel ratio is reduced and, if necessary, distant
  sub-pixel anatomy is capped at overview LOD. The biological engine, context
  state and membrane/contact rules continue to run unchanged.
- Degraded tiers insert a short scheduling gap between frames so controls and
  context events are not starved by a slow software or integrated GPU.
- The Three.js core is a separate cacheable production chunk.
- Vite emits a production manifest.
- `scripts/check_browser_bundle.mjs` recursively follows static manifest imports
  instead of assuming that the entry file alone is the initial payload.
- The production build fails if byte limits are exceeded or any required
  deferred source becomes an initial dependency.
- The build also fails when the checked-in `last_verified_build` ledger differs
  from the freshly measured manifest graph, preventing stale performance claims.

## Verified production graph

| Item | Measured value | Budget |
| --- | ---: | ---: |
| Initial JavaScript chunks | 2 | explicit graph |
| Initial JavaScript raw bytes | 942,685 | <= 980,000 |
| Initial JavaScript gzip bytes | 257,281 | <= 275,000 |
| Largest initial JavaScript chunk | 522,443 bytes | <= 550,000 |
| Initial CSS raw bytes | 32,732 | <= 40,000 |
| Required deferred entries | 6 | exactly 6 |

The gzip values in the gate use Node's deterministic level-9 zlib call. Vite's
displayed gzip sum for the same two initial chunks is 261.11 kB.

Relative to the previous Vite-reported monolithic entry, raw initial JavaScript
fell from approximately 1,042 kB to 943 kB, a 9.5% reduction. The
engine-snapshot interpreter is now an 86.21 kB deferred chunk; PDB and bloom
modules are also outside the initial graph.

## Verification boundary

This is an artifact-graph measurement, not a device-independent latency or
frame-rate claim. Network protocol, browser cache, CPU, GPU, thermal state and
viewport still affect observed startup time. Browser render-integrity tests and
context-switch checks remain separate. The visual suite also loads a BSEP
context and the real glucokinase PDB scene, then checks dynamic-module responses
and canvas-pixel diagnostics.

The byte ceilings are engineering regression budgets selected below the former
monolithic build with limited maintenance headroom. They are not biological
parameters, biological validation thresholds or estimates of hepatocyte
accuracy.

## Scientific interpretation

No biological state, source record, protein count, kinetic parameter, reaction
law, membrane rule or validation result changed. This milestone changes when
browser code is fetched and evaluated. The scientific snapshot remains
fail-closed and all 40 contexts reconstruct the same engine outputs as before.
