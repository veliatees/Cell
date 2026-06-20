# Milestone 035 — Scaling scope by integration (expression-coupled metabolism)

## Why this, not "more reactions"

"Scope" can mean two things: a longer list of reactions, or the pieces actually
wired into one system. The second is worth more and is the real systems-biology
step. M035 connects M034 (gene expression) to M033 (metabolic flux): the enzyme
that gene expression produces *is* the enzyme whose level sets metabolic Vmax. The
cell's metabolism is now driven by its own stochastic gene expression, and the
mechanism for composing further validated pathways is in place.

## What was added

- `reactions.michaelis_menten(..., enzyme=, kcat_per_s=)` — Vmax can now be
  computed live as `kcat * [enzyme]` from the current enzyme count, instead of a
  hard-coded constant. This is the seam between expression and metabolism.
- `reactions.compose_networks(*networks)` — merges sub-networks into one system:
  union of species, all reactions, shared volume. Coupling is by species *name*,
  so a gene-expression network whose product is named `glucokinase_enzyme`
  automatically feeds the metabolic reaction that reads it. Scope grows by
  composing validated pathways, not by hand-writing a monolith.
- `stochastic/coupled_model.py` — central dogma producing the glucokinase enzyme,
  composed with expressed-enzyme glucokinase + adenylate recycling into one
  runnable `CellReactionModel`.

## What it demonstrates

Starting from **zero** enzyme, the coupled system must first transcribe and
translate the gene before any glucose can be phosphorylated — then flux switches
on. Flux scales linearly with the expressed enzyme level (double the enzyme,
double the Vmax-limited rate), and with no enzyme there is exactly no flux. This
is the qualitative behavior of a real cell: metabolism gated by protein
expression.

## Verification (`tests/test_coupled_model.py`, 5 tests)

- Flux scales linearly with expressed-enzyme count; zero enzyme ⇒ zero flux.
- `compose_networks` unions species and concatenates reactions correctly.
- The coupled network exposes both expression (`transcription`) and metabolism
  (`glucokinase_expressed`) reactions over a shared enzyme pool.
- A full coupled run: enzyme is expressed from zero, glucose is then consumed,
  all counts stay non-negative.

Full engine suite: **87/87 passing** (82 prior + 5 new), no regressions.

## Honest limits (v1)

One gene drives one enzyme; the surrounding metabolism still uses the lumped
adenylate-recycling placeholders. True hepatocyte coverage (hundreds of enzymes,
allosteric and hormonal regulation — the scope of HEPATOKIN1) is a long road; the
contribution here is the *composition + expression-coupling machinery* that makes
adding pathways tractable and keeps them integrated rather than siloed.

## Next

- **M036** — cell states, growth, division (count partitioning between daughters),
  and oncogenic perturbations, built on the kinetic + expression core.
