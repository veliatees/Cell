# Milestone 139: Human-GEM FASTCORE scaling sensitivity v1

## Purpose

Test whether the rejected fixed-scaling FASTCORE result is sensitive to the
adaptive LP-10 branch present in the same pinned official implementation.

## Pinned Method

- FASTCORE primary paper:
  <https://doi.org/10.1371/journal.pcbi.1003424>
- COBRA Toolbox commit:
  `67c790dbac809d9d891fdbafc33e18c21fc9bddc`
- official implementation directory:
  <https://github.com/opencobra/cobratoolbox/tree/67c790dbac809d9d891fdbafc33e18c21fc9bddc/src/dataIntegration/transcriptomics/FASTCORE>
- identical input: `11,641` generic flux-consistent reactions;
- identical core: `4,555` seven-donor Boolean reactions;
- identical numerical epsilon: `1e-4`;
- fixed branch: LP-10 scale `1e4`;
- adaptive branch: preserve active core at ten times the minimum preceding
  LP-7 core flux, then fall back to fixed scaling if that LP is infeasible;
- strict output FASTCC is required for both branches.

The multiplier and fixed scale are source-defined numerical choices, not
hepatocyte parameters.

## Pinned Comparison

| Result | Fixed LP-10 | Adaptive LP-10 |
|---|---:|---:|
| Selected reactions | 7,320 | 7,415 |
| Strict-output blocked reactions | 408 | 17 |
| LP-7 solves | 18 | 15 |
| LP-10 solver calls | 13 | 12 |
| Adaptive LP-10 calls | 0 | 11 |
| Fixed fallbacks | 0 | 1 |

The selected-set intersection is `7,143`; the union is `7,592`, for a
Jaccard index of approximately `0.9409`. Ten blocked reactions are shared
between branches; the blocked-set union contains `415`.

## Decision

Adaptive scaling is numerically much better for this input, reducing the
strict blocked set from `408` to `17`, but it does not produce a fully
flux-consistent extracted network. No context model is accepted.

Even a consistent structural candidate would still lack healthy-PHH active
enzyme capacities, measured exchange bounds, a matched objective and
independent validation. FBA, FVA and runtime coupling remain disabled.
