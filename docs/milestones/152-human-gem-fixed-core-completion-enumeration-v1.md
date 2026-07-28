# Milestone 152: Human-GEM fixed-core completion enumeration v1

## Question

The three certified globally minimum support sets each contain `59`
reactions and share `58` identities. This milestone asks a narrower,
fully decidable question: if those common `58` identities are fixed, are
`MAR00494`, `MAR02308` and `MAR10035` all possible one-reaction completions?

## Exact Conditioned Search

The conditioned retained network contains:

- adaptive FASTCORE reactions: `7,415`;
- fixed common support identities: `58`;
- conditioned retained total: `7,473`;
- remaining omitted candidates: `4,168`;
- required additional identities at the proven global cardinality: `1`.

The three known singleton completions are excluded with no-good cuts. The
terminal MILP uses the exact lower-bound targets `MAR00468` and `MAR00612`,
caps additional identities at one, and searches every remaining candidate.
HiGHS reports infeasible with presolve enabled and a second solve with
presolve disabled independently confirms infeasibility.

## Result

Exactly three singleton completions exist given the fixed common core:

1. `MAR00494`
2. `MAR02308`
3. `MAR10035`

No fourth one-reaction completion can satisfy the lower-bound target pair
with the same fixed `58` reactions. The first two completion reactions have
zero-of-seven total-proteome support in the current resection-PHH evidence
manifest. `MAR10035` has no GPR annotation and is not present in that
reaction-evidence manifest. These are evidence gaps, not inactivity proofs.

## Reproducibility

```bash
PYTHONPATH=engine python3 scripts/audit_human_gem_phh_fastcore_fixed_core_completion_enumeration.py
```

The committed artifact is:

`data/phh_baseline/derived/human_gem_v2.0.0.seven_donor_fastcore_fixed_core_completion_enumeration.json`

It pins the common-core, retained-universe, candidate-universe and completion
identity checksums, source evidence records, no-good constraints and terminal
no-presolve solver proof.

## Scientific Boundary

This milestone alone is exact only under the fixed-common-core condition.
Milestone 153 subsequently proves that the `58` identities are present in
every global minimum and excludes another `59`-reaction set that replaces two
or more of them together. Neither result establishes reaction activity in
healthy PHH, active enzyme capacity, exchange flux, objective, FBA result or
runtime rate.
