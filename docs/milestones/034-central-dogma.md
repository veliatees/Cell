# Milestone 034 — Central dogma (gene → mRNA → protein)

## Why

A real cell is *driven by gene expression*: enzyme levels (the Vmax terms in the
M033 kinetics) are themselves stochastic products of transcription and
translation. This is also the canonical low-copy system — a gene is 1–2 copies,
mRNA a handful — which is exactly where the exact SSA, not the CLE, is the
correct tool. M034 adds that layer and shows the real hallmark of stochastic
gene expression emerge: **translational bursting**.

## What was added (`stochastic/central_dogma.py`)

The standard two-stage model, on molecule counts:

- transcription: gene → gene + mRNA (gene catalytic)
- mRNA decay: mRNA → ∅
- translation: mRNA → mRNA + protein
- protein decay: protein → ∅

`GeneExpressionKinetics` carries the four rates plus derived analytic quantities
(`burst_size = k_tl/k_mRNA_decay`, `mean_mrna`, `mean_protein`).
The legacy constant named `HEPATOCYTE_ENZYME_GENE` is now explicitly classified
as a synthetic software benchmark. Its rates make the stochastic statistics
converge quickly; they are not a measured hepatocyte parameter set. The
mechanism and analytic noise structure are the tested part.

## What emerges (and is validated)

`tests/test_central_dogma.py` (4 tests) checks the model against the analytic
two-stage results (Thattai & van Oudenaarden, 2001):

- **mRNA is low-copy and Poisson**: mean ≈ k_tx·gene/k_decay (~17 copies) with
  Fano factor ≈ 1 — the regime that *requires* exact SSA.
- **Protein bursts (super-Poissonian)**: protein mean matches
  k_tl·⟨mRNA⟩/k_decay, but its Fano factor is far above 1 (> 3). Each mRNA
  produces a burst of proteins before decaying, so protein noise is much larger
  than a naive Poisson assumption — the real signature of gene expression, which
  a deterministic ODE model cannot reproduce.
- **Gene copy number conserved** (catalytic), counts non-negative.
- **Analytic relations** match the closed-form formulas.

Full engine suite: **82/82 passing** (78 prior + 4 new), no regressions.

## Honest limits (v1)

The bundled rates are synthetic and cannot run in the authoritative hepatocyte
expression program. The current production path is the calibration-gated,
compartmental exact-SSA process documented in
`17-genomic-system-six-milestones.md`.

## Next

- **M035** — grow the reaction network toward real hepatocyte coverage.
- **M036** — cell states, growth, division (count partitioning), and cancer,
  built on the kinetic + expression core.
