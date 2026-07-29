# Milestone 156 - Canonical context snapshot overlay matrix v1

## Problem

The browser exposes three zonation contexts, three nutrition profiles and four
experiment states. The repository previously stored each selectable context as
a complete engine snapshot. This caused two engineering failures:

- 40 context artifacts duplicated the same large evidence and validation
  surfaces;
- those artifacts had drifted behind the canonical snapshot and still exposed
  `metabolic_constraint_shell_v6` with 83 state keys, while the current engine
  exposed `metabolic_constraint_shell_v14` with 85 state keys and two additional
  authority-firewall surfaces.

The stale files could therefore render a scientifically obsolete state after a
context switch, and their repeated payload increased browser parsing and memory
pressure.

## Implemented contract

- One full midlobular, postabsorptive, baseline snapshot is the canonical base.
- All 40 existing context URLs now contain exact top-level state overlays.
- Each overlay declares its base schema, creation time, definition, state-key
  count, state-key digest and full canonical snapshot digest.
- The Python exporter first creates every target as a full engine snapshot in a
  temporary directory.
- It builds each overlay, reconstructs the target and requires exact structured
  equality plus the target canonical SHA-256 digest before publication.
- A generated manifest records the checksums, sizes, declared contexts and
  state-override counts for the complete artifact set.
- The browser rejects an overlay when the canonical base identity, state
  surface or declared zone, nutrition profile or experiment does not match.
- Existing full-snapshot URLs remain supported for external or custom snapshot
  use.
- Overlays and the manifest are replaced first and the canonical base last. A
  mixed generation therefore fails closed on base identity instead of silently
  combining incompatible state.

## Verified inventory

| Item | Value |
| --- | ---: |
| Canonical full snapshots | 1 |
| Exact context overlays | 40 |
| Zonation contexts | 3 |
| Nutrition profiles | 3 |
| Experiment states | 4 |
| Canonical state keys | 85 |
| Former full-matrix bytes | 77,097,820 |
| Canonical plus overlay bytes | 11,632,534 |
| Artifact-byte reduction | 84.9% |

The byte reduction is a repository measurement from
`public/context-snapshot-manifest.v1.json`; it is not a biological performance
or accuracy metric.

## Verification

- Python unit tests reject a stale base and tampered overlay.
- The integration test audits all 40 declared paths, file checksums, artifact
  counts and exact target reconstruction.
- TypeScript tests cover synthetic overlays, missing bases, stale bases and a
  checked-in BSEP-loss artifact.
- The browser runtime verifies the canonical identity and reconstructed state
  surface before accepting a context.

Offline generation verifies the full target snapshot digest. The browser avoids
rehashing the complete reconstructed multi-megabyte object on every context
switch; its runtime boundary verifies the checksummed base identity, state-key
digest and declared context instead.

## Scientific interpretation

This milestone changes transport and storage of already generated engine state.
It adds no protein count, kinetic constant, reaction rate, threshold,
interpolation, donor measurement or biological coupling. The 40 reconstructed
contexts remain exactly the contexts produced by the current engine.

Biological realism is therefore unchanged. What improves is reproducibility:
the browser can no longer switch from the current engine contract to an older
embedded scientific state without failing the snapshot gate.
