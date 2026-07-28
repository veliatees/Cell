# Milestone 149: Human-GEM support optimum enumeration v1

## Scope

Resolve identity ambiguity at the Milestone 148 optimum. Each discovered
`59`-reaction set is excluded with a cumulative no-good cut while the total
candidate count remains capped at `59`. Enumeration stops only when HiGHS
proves the remaining problem infeasible with presolve disabled after an
initial presolve infeasibility result.

Every newly discovered set receives all `17` post-MILP LP certificates and an
independent strict FASTCC classification.

## Result

Exactly two minimum identity sets exist inside the scoped `65`-reaction pool:

- minimum support set count: `2`;
- reactions present in every minimum set: `58`;
- optional reaction identities: `MAR02308`, `MAR10035`;
- each optimum contains exactly one of those two identities;
- each optimum produces `7,474/7,474` strict-consistent reactions;
- cumulative no-good MILP solves: `2`;
- the terminal no-good problem is solved twice, and the no-presolve solve
  confirms that no third `59`-reaction set exists.

The no-presolve-confirmed terminal infeasibility certificate makes the
identity enumeration complete for this pool. The `58` common reactions are
proven members of every minimum-cardinality set in this scope.

## Reproducibility

```bash
PYTHONPATH=engine python3 scripts/audit_human_gem_phh_fastcore_support_optimality.py
```

The audit commits both ordered identity sets, their digests, universal and
optional memberships, target certificate counts, strict FASTCC results and
the terminal solver status.

## Scientific Boundary

Universal membership is not the same as biological essentiality. The result
does not test larger nonminimum repair sets, all `4,226` omitted reactions,
gene knockout viability, active PHH enzyme abundance or donor-specific
metabolism. No context model, objective, FBA result or runtime rate is
authorized.
