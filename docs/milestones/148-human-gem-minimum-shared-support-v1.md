# Milestone 148: Human-GEM minimum shared support v1

## Scope

Apply Milestone 147 to the `65` Human-GEM reactions in the committed
Milestone 143 per-target repair union. The retained network is the `7,415`
reaction adaptive FASTCORE candidate and the targets are its `17` strict
output blockers.

The candidate pool is deliberately source-limited:

- every candidate already belongs to checksum-pinned Human-GEM v2.0.0;
- no external universal reaction database is used;
- generic model bounds are preserved;
- thirteen target directions previously proven infeasible are fixed;
- four targets retain both possible directions.

## Result

- input candidate union: `65`;
- exact minimum shared additions inside that pool: `59`;
- redundant union members removed: `6`;
- selected candidate network: `7,474` reactions;
- strict FASTCC consistency: `7,474/7,474`;
- post-MILP target LP certificates: `17/17`;
- MIP node count: `1`;
- maximum integrality residual: `0`;
- maximum target-certificate mass-balance residual:
  `1.1544765143867153e-11`;
- maximum target-certificate bound violation:
  `2.3874235921539366e-12`.

The selected additions contain:

- `4` reactions without a GPR annotation;
- `55` reactions with zero-of-seven donor GPR support;
- `0` reactions with partial or seven-of-seven donor GPR support.

All `59` therefore remain in the reaction-level biological evidence queue.

## Reproducibility

The committed audit stores the pinned model identity, prerequisite audit
versions, selected reaction order and digest, target certificate digests,
evidence-record digest, solver settings, residuals and strict FASTCC result.

Regenerate with:

```bash
PYTHONPATH=engine python3 scripts/minimize_human_gem_phh_fastcore_shared_support.py
```

## Scientific Boundary

The `59` count is globally minimum only inside the committed `65`-reaction
pool. The wider `4,226` reactions omitted by adaptive FASTCORE were not solved
as one multi-target candidate universe. The result supplies no active-enzyme
abundance, measured exchange state, healthy-PHH objective, FBA permission or
runtime coupling.
