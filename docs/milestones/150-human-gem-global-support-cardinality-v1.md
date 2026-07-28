# Milestone 150: Human-GEM global support cardinality v1

## Question

Milestone 148 proved that `59` additions are minimum inside the committed
`65`-reaction union of per-target supports. This milestone asks the wider
question: can any of the other reactions omitted by adaptive FASTCORE reduce
that cardinality?

## Exact Proof

The candidate universe is the complete complement of the `7,415`-reaction
adaptive candidate inside the checksum-pinned, strict-FASTCC-consistent
Human-GEM v2.0.0 network:

- retained adaptive reactions: `7,415`;
- omitted candidate reactions: `4,226`;
- blocked targets: `17`.

An exact shared-identity MILP solves the explicit target subset `MAR00468` and
`MAR00612` against all `4,226` candidates. It proves that this subset alone
requires at least `59` added reaction identities. The previously committed
`59`-reaction support independently certifies all `17` targets and leaves
`7,474 / 7,474` reactions strict-FASTCC consistent.

Therefore:

```text
59 = subset lower bound
   <= all-target global optimum
   <= committed all-target feasible upper bound
   = 59
```

The global minimum cardinality is exactly `59` over the declared Human-GEM
candidate universe.

## Numerical Certificate

- zero MIP gap;
- one MIP node;
- two independent post-MILP LP certificates;
- maximum MILP/LP mass-balance residual below `1e-7`;
- maximum bound violation below `1e-7`;
- native finite Human-GEM reaction bounds preserved;
- numerical epsilon `1e-4`, explicitly not a biological parameter.

The committed artifact is:

`data/phh_baseline/derived/human_gem_v2.0.0.seven_donor_fastcore_global_support_optimality.json`

Regenerate it with:

```bash
PYTHONPATH=engine python3 scripts/audit_human_gem_phh_fastcore_global_support_optimality.py
```

## Scientific Boundary

Global cardinality does not imply global identity uniqueness. Milestone 149
enumerated exactly two minimum sets only inside the `65`-reaction pool.
Milestone 151 subsequently certified a third all-target minimum set using
`MAR00494` outside that pool, so global uniqueness is false while complete
global identity enumeration remains open. The result also establishes no
active PHH enzyme, measured exchange bound, biological objective,
donor-specific flux, healthy-PHH FBA or runtime rate.
