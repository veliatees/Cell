# Milestone 135: Human-GEM FBC gene labels and strict GPR evaluation v1

## Purpose

Create a deterministic bridge from measured protein gene symbols to the exact
gene-product-reaction rules in the checksum-pinned Human-GEM v2.0.0 artifact.

## Implementation

The sparse SBML/FBC loader now preserves every `fbc:geneProduct` identifier and
label pair rather than retaining only Ensembl identifiers. The loader audit
binds the ordered identifier-label pairs to a SHA-256 digest.

GPR expressions are parsed through a strict Boolean grammar:

- identifiers are the only leaves;
- `and` and `or` are the only operators;
- calls, comparisons, constants, arithmetic, negation and arbitrary Python
  syntax are rejected;
- every parsed identifier must agree with the reaction's FBC association and
  resolve to a model gene product.

## Pinned Result

- Human-GEM gene products: `2,848`;
- unique preserved FBC labels: `2,848`;
- GPR-associated reactions: `7,782`;
- ordered gene references across those rules: `23,929`.

## Scientific Boundary

An FBC label establishes model identity only. It does not show that a protein
is expressed, localized, active, correctly assembled or carrying flux in a
human hepatocyte.
