# Milestone 151: Human-GEM global support counterexample v1

## Question

Milestone 149 found exactly two `59`-reaction support identities inside a
scoped `65`-reaction repair pool. Milestone 150 proved that `59` is also the
global minimum cardinality over all `4,226` reactions omitted by adaptive
FASTCORE. This milestone asks whether the scoped pair exhausts the wider
global identity space.

## Numerical Firewall

The first no-good solve excluded the committed primary support and initially
returned infeasible with HiGHS presolve enabled. A second solve of the same
MILP with presolve disabled found a feasible optimum. The shared-support
kernel now treats every presolve infeasibility as provisional and requires a
no-presolve confirmation before accepting it as a proof.

A synthetic regression test forces this failure mode and verifies the retry
path. The scoped Milestone 149 terminal result is also regenerated with
presolve disabled and remains infeasible, preserving its two-set conclusion
inside the `65`-reaction pool.

## Result

The wider candidate search found a third distinct global minimum support:

- added reaction count: `59`;
- overlap with the committed primary set: `58`;
- primary-only identity: `MAR10035`;
- counterexample-only identity: `MAR00494`;
- `MAR00494` is outside the scoped `65`-reaction pool;
- all-target post-MILP LP certificates: `17/17`;
- repaired strict FASTCC result: `7,474/7,474` consistent;
- known distinct global minimum-set count: at least `3`.

The source-preserving reaction-evidence manifest reports zero-of-seven donor
total-proteome support for `MAR00494`. Structural feasibility therefore does
not establish that this reaction is active in healthy primary human
hepatocytes.

## Reproducibility

```bash
PYTHONPATH=engine python3 scripts/audit_human_gem_phh_fastcore_global_support_counterexample.py
```

The committed artifact is:

`data/phh_baseline/derived/human_gem_v2.0.0.seven_donor_fastcore_global_support_counterexample.json`

It pins the model identity, global candidate universe, ordered reaction-set
checksums, presolve cross-check, all-target LP certificates, strict FASTCC
result and scientific boundary.

## Scientific Boundary

This is a counterexample to global identity uniqueness, not a complete global
enumeration. It proves neither universal reaction membership nor the total
number of global minimum sets. No active enzyme abundance, measured exchange
bound, biological objective, healthy-PHH context, FBA execution or runtime
flux coupling is authorized.
