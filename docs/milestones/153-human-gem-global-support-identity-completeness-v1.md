# Milestone 153: Human-GEM global support identity completeness v1

## Question

Milestone 150 proved that the global minimum support cardinality is `59`.
Milestone 152 proved that exactly three one-reaction completions exist when
the known common `58` identities are fixed. The remaining question is whether
another minimum set can replace two or more of those common identities.

## Core-Breaking Search

The exact shared-support MILP exposes all `4,226` reactions omitted by
adaptive FASTCORE and caps additions at the proven global minimum `59`. One
no-good constraint forbids selecting all `58` common identities:

```text
sum(selected common-core identities) <= 57
```

Any feasible result would therefore be a core-breaking global minimum. The
search uses the exact lower-bound target pair `MAR00468` and `MAR00612`.
HiGHS reports infeasible with presolve enabled, and a second solve with
presolve disabled independently confirms infeasibility.

## Composed Proof

The three exact results now compose:

```text
global minimum cardinality = 59
common identities per known set = 58
exact singleton completions given that core = 3
core-breaking support with cardinality <= 59 = infeasible
```

Therefore:

- global minimum support-set count: exactly `3`;
- global universal identities within minimum sets: `58`;
- global optional identities: `MAR00494`, `MAR02308`, `MAR10035`;
- every global minimum contains exactly one optional identity;
- multi-replacement global minima: excluded;
- additional global minimum identity search: not required.

All three sets have `17/17` post-MILP target LP certificates and produce
`7,474/7,474` strict-FASTCC-consistent reactions.

## Reproducibility

```bash
PYTHONPATH=engine python3 scripts/audit_human_gem_phh_fastcore_global_support_identity_completeness.py
```

The committed artifact is:

`data/phh_baseline/derived/human_gem_v2.0.0.seven_donor_fastcore_global_support_identity_completeness.json`

It pins the candidate universe, all three ordered support sets, universal and
optional identity checksums, the common-core no-good constraint and the
terminal no-presolve solver proof.

## Scientific Boundary

Universal membership here means membership in every minimum structural
support set inside the pinned Human-GEM candidate universe. It is not
biological essentiality, gene-knockout essentiality or evidence that a
reaction is active in healthy PHH. Larger nonminimum support sets are not
enumerated. No active enzyme capacity, exchange bound, biological objective,
healthy-PHH context, FBA result or runtime rate is authorized.
