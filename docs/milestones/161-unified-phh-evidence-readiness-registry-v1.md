# Milestone 161 - Unified PHH evidence readiness registry v1

## Problem

The repository had 15 versioned PHH evidence contracts, but no single surface
could answer which contracts were intact, which validators existed, where a
delivery belonged, which completion gaps it addressed, or whether a malformed
delivery had attempted to cross a scientific-authority boundary.

The older nine-file evidence-bundle audit covered only the original
glucose/signal package. Later reaction, protein, signaling, mobility, mechanics,
mesh, injury, memory, donor and metabolic contracts remained separate.

## Implementation

`data/evidence_intake/phh_evidence_readiness_registry.v1.json` now pins, for all
15 contracts:

- repository path, SHA-256, schema version and contract id;
- expected versioned delivery path and artifact kind;
- one statically registered validator surface;
- the exact completion-matrix scopes that the evidence could address.

`cell_engine.validation.evidence_readiness` verifies the registry and canonical
contracts before dispatch. It then audits each delivery independently and emits
one normalized readiness report. Mobility and 3D geometry record identities are
passed explicitly to the reaction-transport audit. Arbitrary callables are never
loaded from registry data.

One malformed delivery is reported as rejected and contributes no artifact,
record, structural-completeness or authority count. The remaining contracts are
still inspected. The read-only command is:

```bash
PYTHONPATH=engine python scripts/audit_phh_evidence_readiness.py
```

An alternate incoming root can be supplied with `--incoming-root`; `--out`
writes the normalized report only when explicitly requested.

## Scientific boundary

This is evidence logistics and validation infrastructure, not a biological
model. Contract identity, schema completeness and checksum validity do not make
a measurement applicable to a healthy human hepatocyte. Manual primary-source
review remains mandatory. Automatic parameter activation, state coupling,
training and predictive authority remain disabled.

The default repository state has:

- 15 registered contracts;
- 15 verified canonical identities;
- 15 registered validators;
- 19 mapped completion scopes;
- zero delivered artifacts;
- zero quantitatively authorized outputs;
- zero automatic parameter or state-coupling activations.

## Verification

- exact contract identity and checksum audit;
- registry-order and static-validator checks;
- completion-matrix target-id coverage;
- malformed single-delivery quarantine;
- external topology-delivery path audit;
- scientific-release fail-closed checks;
- Python, TypeScript, snapshot and browser integration tests.
