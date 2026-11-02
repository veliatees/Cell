# Milestone 177 - Legacy scene chunk deferral v1

## Problem

The scene selector was assembled synchronously during module evaluation from six
simulator registries, so every legacy "building blocks" simulator entered the
initial browser graph even though the application opens on the hepatocyte scene
and most visits never select one of them.

After milestone 157 the initial graph measured 919,022 raw / 251,532 gzip bytes
against ceilings of 980,000 / 275,000: 6.2% raw headroom and 8.5% gzip headroom.
That is thin enough that the next ordinary feature either fails the production
gate or tempts a maintainer to raise the ceilings instead of measuring. Raising
the ceilings would have been the wrong repair, because the gate exists precisely
to make that temptation visible.

## Implemented boundary

- `src/physics/sceneCatalog.ts` is a new synchronous, display-only index of
  scene ids and labels for the five deferred families. It contains no simulation
  code, no numeric parameter and no biological claim; it exists so the selector
  can render identical markup before any simulator chunk is fetched.
- The five simulator modules (`water`, `solvation`, `diffusion`, `membrane`,
  `reactions`) are now reached through cached dynamic imports inside `loadScene`.
  The browser module loader caches the promise, so a second visit to a scene does
  not refetch the chunk.
- The corresponding `main.ts` imports became `import type`, which the TypeScript
  compiler erases; they contribute no runtime bytes.
- `sceneLoadToken` invalidates an in-flight scene load when the visitor selects
  another scene before the chunk arrives, so a slow fetch cannot overwrite a
  newer choice.
- The ion fallback scene deliberately remains eager: `IonSimulation` is
  constructed at module scope (`main.ts:769`) and `mode` starts at `"ions"`.
  Deferring it requires making that instance nullable across the render loop and
  is tracked as separate work, not silently bundled here.
- `data/validation/browser_bundle_budget.v1.json` lists the five sources in
  `required_deferred_entries` (now 11). The gate therefore fails if any of them
  is pulled back into the initial graph by a future static import.
- `src/physics/sceneCatalog.test.ts` imports both the catalogue and the real
  registries and fails on any drift in id, label or order. Test code never enters
  the production bundle, so the parity check costs the browser nothing.

## Verified production graph

| Item | Before | After | Budget |
| --- | ---: | ---: | ---: |
| Initial JavaScript chunks | 2 | 2 | explicit graph |
| Initial JavaScript raw bytes | 919,022 | 894,578 | <= 980,000 |
| Initial JavaScript gzip bytes | 251,532 | 244,461 | <= 275,000 |
| Largest initial JavaScript chunk | 522,443 | 522,443 | <= 550,000 |
| Initial CSS raw bytes | 32,732 | 32,732 | <= 40,000 |
| Required deferred entries | 6 | 11 | exactly 11 |

The initial graph shrank by 24,444 raw bytes (-2.66%) and 7,071 gzip bytes
(-2.81%). The deferred chunks measure 26.90 kB raw (10.82 kB gzip) in total:
`water` 5.19 kB, `solvation` 5.97 kB, `diffusion` 1.91 kB, `reactions` 2.72 kB,
`membrane` 11.11 kB.

The byte ceilings were **not** raised. Headroom therefore grew from 60,978 to
85,422 raw bytes (8.7% of the ceiling) and from 23,468 to 30,539 gzip bytes
(11.1%). The largest-chunk ceiling remains the tightest constraint at 5.0%
headroom, because it is dominated by the Three.js core.

## Verification boundary

This is an artifact-graph measurement taken from the production manifest, not a
device-independent latency claim. Network protocol, browser cache, CPU, GPU,
thermal state and viewport still determine observed startup time, and the
deferred chunks are fetched the first time a visitor selects one of those scenes.

Manual verification in a development browser: selecting the water and vesicle
scenes fetched `water.ts` and `membrane.ts` on demand and rendered correctly, and
returning to the hepatocyte scene restored the default view.

Automated verification: 199 unit tests pass (196 existing plus 3 catalogue
tests); `npm run build` passes with the checked-in ledger matching the freshly
measured manifest graph.

## Scientific interpretation

No biological state, source record, protein count, kinetic parameter, reaction
law, membrane rule or validation result changed. This milestone changes when
legacy scene code is fetched and evaluated. The scientific snapshot, the
fail-closed authority gates and the engine's role as the sole biological state
source are untouched.
