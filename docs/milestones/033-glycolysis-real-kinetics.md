# Milestone 033 — Full glycolysis with real per-enzyme kinetics

## Why

M032 ran on one real enzyme (glucokinase) surrounded by lumped placeholders.
M033 replaces those placeholders with the **complete 10-step glycolytic
pathway**, glucose → 2 pyruvate, with the correct cofactor stoichiometry and
literature-grounded kinetics on the committed regulatory steps. This is the
first end-to-end *real* metabolic pathway on the stochastic core.

## The pathway (`stochastic/glycolysis.py`)

All ten enzymes, on molecule counts, with exact cofactor coupling:

| Step | Enzyme | Reaction | Kinetics |
|---|---|---|---|
| 1 | Glucokinase | glucose + ATP → G6P + ADP | **grounded** Hill (S0.5 8 mM, nH 1.7, ATP Km 0.4 mM) |
| 2 | Phosphoglucose isomerase | G6P → F6P | fast mass-action (lumped) |
| 3 | PFK-1 | F6P + ATP → F1,6BP + ADP | **grounded** cooperative (nH 2, ATP cofactor) |
| 4 | Aldolase B | F1,6BP → DHAP + GAP | mass-action (lumped) |
| 5 | Triosephosphate isomerase | DHAP → GAP | fast mass-action (lumped) |
| 6 | GAPDH | GAP + NAD⁺ → 1,3-BPG + NADH | mass-action (lumped) |
| 7 | Phosphoglycerate kinase | 1,3-BPG + ADP → 3-PG + ATP | mass-action (lumped) |
| 8 | Phosphoglycerate mutase | 3-PG → 2-PG | fast mass-action (lumped) |
| 9 | Enolase | 2-PG → PEP | fast mass-action (lumped) |
| 10 | Pyruvate kinase (L) | PEP + ADP → pyruvate + ATP | **grounded** sigmoidal (K0.5 2.37 mM, nH 1.41) |

Cofactor stoichiometry is exact: 2 ATP invested (steps 1, 3), 4 produced (steps
7, 10 — each runs twice per glucose), 2 NADH produced (step 6 twice). The two
trioses from aldolase both funnel to GAP via TPI, so lower glycolysis runs twice
per hexose automatically.

## A correctness fix that improved the biology

The committed steps are bi-substrate enzymes. The first SSA run drove ADP
negative because the Michaelis propensity only watched its varied substrate
(PEP/glucose/F6P), not the cofactor. The fix is also more realistic: a Michaelis
availability factor `[cofactor]/(Km+[cofactor])` was added to `michaelis_menten`.
It is ~1 when the cofactor is saturating — exactly the regime the literature
S0.5/Hill values were measured in — and falls to 0 as the cofactor is exhausted,
so no reaction can push a co-substrate below zero. Glucokinase uses its measured
ATP Km (~0.4 mM) here.

## Honest limits (v1)

Only the three committed/regulatory steps are grounded; the seven
near-equilibrium steps use fast forward mass-action placeholders (confidence
~0.2) and are labelled `LUMPED` in code. The model is forward-only (no reverse
fluxes / thermodynamics), inorganic phosphate is omitted from GAPDH, and the
committed-step kcat values are placeholders. Correctness here is carried by the
**conservation laws**, not by these provisional rate constants.

## Verification (`tests/test_glycolysis.py`, 7 tests)

Stoichiometric invariants, checked exactly under the exact SSA — the strongest
evidence the 10-step wiring is right:

- **Carbon conserved**: `2·hexoses + trioses` is invariant.
- **Adenylate conserved**: ATP + ADP invariant.
- **NAD conserved**: NAD⁺ + NADH invariant.
- **No negative counts** (the co-substrate fix).
- **Flux flows**: glucose consumed, pyruvate produced (SSA and physiological CLE).
- **Pyruvate kinase** is half-maximal exactly at K0.5(PEP).

Full engine suite: **78/78 passing** (71 prior + 7 new), no regressions.

## Next

- **M034** — central dogma: low-copy stochastic gene→mRNA→protein expression on
  the SSA core, eventually setting the enzyme levels (Vmax) used here.
