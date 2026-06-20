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
`HEPATOCYTE_ENZYME_GENE` uses representative mammalian order-of-magnitude rates
(2 gene copies, ~5 min mRNA half-life, burst size ~21), flagged low confidence —
the *mechanism and noise structure* are the grounded part, and they are universal.

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

Rates are order-of-magnitude, not gene-specific. Expression is constitutive — no
promoter states, transcription-factor regulation, or coupling yet to the
glycolytic enzyme Vmax values from M033. Wiring expression to enzyme levels (so
the cell's metabolism is set by its own gene expression) is the natural follow-up.

## Next

- **M035** — grow the reaction network toward real hepatocyte coverage.
- **M036** — cell states, growth, division (count partitioning), and cancer,
  built on the kinetic + expression core.
