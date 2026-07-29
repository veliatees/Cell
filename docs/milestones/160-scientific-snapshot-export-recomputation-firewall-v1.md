# Milestone 160 - Scientific snapshot export recomputation firewall v1

## Problem

The engine snapshot was scientifically deterministic but computationally
wasteful. One export repeatedly rebuilt the same default evidence surfaces,
rescanned the 8,689-record PHH proteome, reparsed identical SBML files and
revalidated the same 4,895-reaction Human-GEM manifest.

This did not change biology, but it increased startup, export and context-matrix
work enough to obscure real regressions.

## Implementation

`data/validation/scientific_snapshot_export_policy.v1.json` records seven
process-local reuse surfaces and their isolation rules:

- SBML document and reaction-fingerprint parsing use resolved path, nanosecond
  modification time and file size as invalidation keys.
- PHH proteome lookup builds one gene index and one accession index for the
  pinned default artifact. Explicit payloads bypass the index.
- The frozen compartmental energy/redox contract is reused directly.
- Default kinetic-transfer, reaction-evidence and metabolic-shell builds are
  cached. Mutable results are returned as defensive deep copies.
- Custom reaction networks and transfer audits bypass default caches.
- Human-GEM gap-membership sets are constructed once per manifest validation,
  not once per reaction record.

No cache crosses a Python process boundary, writes a derived biological value or
turns a missing evidence field into a parameter.

## Equivalence

The pre-change and post-change engine snapshots were compared field by field.
The only difference was the declared volatile path
`metadata.created_at_utc`. After removing that timestamp, the JSON documents
were exactly equal. Both files were 1,826,395 bytes.

## Local profile

The same M1 workspace and Python 3.13 runtime produced:

| Profile | Function calls | Profiler time |
| --- | ---: | ---: |
| Before | 31,271,983 | 32.038 s |
| After | 8,183,484 | 4.925 s |

A non-profiled post-change export completed in 2.29 s. These are local
diagnostics, not portable performance guarantees or biological timescales.

## Scientific boundary

This milestone has zero scientific authority. It changes no reaction equation,
rate, concentration, abundance, geometry, trajectory, donor interpretation or
validation gate. Cache reuse is permitted only where the default input identity
is explicit; mutable public outputs are isolated from the cached source.

## Verification

- defensive-copy mutation tests for SBML, kinetic transfer, reaction evidence
  and the metabolic shell;
- immutable frozen-contract reuse test;
- default PHH gene/accession index identity test;
- custom-network cache-bypass coverage;
- exact scientific-payload comparison excluding only the creation timestamp;
- focused and full Python suites;
- TypeScript snapshot contract and production build.
