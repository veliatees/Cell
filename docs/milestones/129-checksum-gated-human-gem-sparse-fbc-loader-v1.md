# Milestone 129: Checksum-gated Human-GEM sparse FBC loader v1

## Purpose

Load the exact pinned Human-GEM reconstruction into executable data structures
without vendoring a 43 MB artifact or claiming that a generic human model is a
healthy hepatocyte.

## Implemented

- TLS certificate verification using a pinned `certifi` dependency; certificate
  validation is never disabled.
- Byte-size and SHA-256 verification before XML parsing.
- Streaming SBML Level 3 Version 1 and FBC Version 2 parsing.
- Ordered compartment and species records.
- A sparse stoichiometric matrix with deterministic coordinate ordering.
- Reaction bounds resolved through FBC parameter references.
- Reversibility, active objective, flux-objective and nested Boolean
  gene-product association preservation.
- Rejection of DTD/entity declarations, duplicate IDs, unresolved references,
  non-finite coefficients and invalid bounds.
- A compact committed audit regenerated from the real pinned artifact.

## Verified Artifact Result

- compartments: `9`;
- species: `8,461`;
- reactions: `12,931`;
- sparse stoichiometric terms: `55,198`;
- reversible reactions: `5,725`;
- gene-associated reactions: `7,782`;
- gene products: `2,848`;
- active objective: `obj`, targeting the generic human-cell biomass reaction.

## Scientific Boundary

The loader proves artifact identity and software fidelity only. The generic
biomass objective is not a healthy-PHH measurement. No donor context, exchange
boundary, PHH objective, flux, time course or runtime coupling is authorized.

## Reproduction

Run:

```bash
PYTHONPATH=engine python3 scripts/fetch_human_gem.py
PYTHONPATH=engine python3 scripts/audit_human_gem_fbc_loader.py
```

The 43 MB cache artifact remains gitignored; the compact audit is committed.
