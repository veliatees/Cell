# Milestone 143: Human-GEM source-limited support repair v1

## Purpose

Apply the exact Milestone 142 kernel to all `17` adaptive FASTCORE blockers and
test whether their combined support restores strict flux consistency without
introducing reactions from outside pinned Human-GEM.

## Candidate Boundary

- retained adaptive candidate: `7,415` reactions;
- allowed candidates: the `4,226` reactions omitted by adaptive FASTCORE but
  already present in the checksum-pinned generic FASTCC-consistent Human-GEM
  network;
- external universal reaction database: not used;
- generic reaction bounds: unchanged;
- forward and reverse MILPs: `34`;
- post-MILP LP certificates: required for every feasible direction.

## Exact Result

- targets with proven minimum cardinality: `17/17`;
- per-target minimum additions: `1-56`;
- sum of per-target minimum counts before overlap removal: `519`;
- unique addition union: `65`;
- repaired candidate: `7,480` reactions;
- strict FASTCC consistency: `7,480/7,480`;
- strict FASTCC blocked reactions: `0`;
- maximum MILP witness mass-balance residual:
  `5.343281372915953e-12`;
- maximum strict FASTCC witness mass-balance residual:
  `7.529752393971821e-11`.

The union is not claimed to be a globally minimum multi-target repair. Each
target-specific cardinality is proven independently, and support-set
uniqueness is not established.

## Biological Evidence Audit

Every one of the `65` additions remains biologically unresolved:

- `57` have a GPR but zero-of-seven support in the available resection-PHH
  total-proteome cohort;
- `8` have no GPR annotation;
- `0` have partial donor support;
- `0` have seven-of-seven donor support.

This result is scientifically useful precisely because it separates two
questions:

1. Can a compact candidate be made mathematically flux consistent? Yes.
2. Are the added reactions active in a healthy human hepatocyte? Unknown.

## Execution Boundary

The repaired candidate is not accepted as a healthy-PHH model. Measured
exchange bounds, a matched biological objective, active-enzyme evidence,
donor-resolved validation and independent reproduction remain absent. PHH FBA,
runtime flux coupling and reaction-rate initialization remain blocked.
