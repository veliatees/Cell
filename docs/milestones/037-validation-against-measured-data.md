# Milestone 037 — Validation against measured hepatocyte data

> **Superseded authority note (2026-07-20):** The ATP, ATP:ADP, energy-charge
> and later GSH:GSSG range matches used calibrated shared-pool software fixtures
> and unmatched aggregate reference ranges. They are not independent biological
> validation and the former `100%` accuracy claim is retired. The current harness
> retains only the glucokinase S0.5 same-equation implementation check and labels
> it explicitly as non-independent. See Milestones 087-088.

## Why this is the keystone gap

Every other gap (coverage, grounding, integration, spatial) is about *building
more*. This one is about *knowing whether what we built is real*. Until the model
is checked against measured numbers, "how realistic is it?" has no answer — not a
low one, simply an unmeasured one. M037 gives the project its first quantitative
"how real" number.

## What was added (`stochastic/validation.py`)

A harness that checks **emergent** outputs of the real-units stochastic models
against literature-measured hepatocyte values:

| Target | Measured range | Source | Emergent? |
|---|---|---|---|
| Adenylate energy charge | 0.80–0.95 | Atkinson energy charge | yes |
| Steady-state cytosolic ATP | 2.5–4.5 mM | BioNumbers/textbook | yes |
| Total ATP:ADP ratio | 2–10 | BioNumbers/textbook | yes |
| Glucokinase glucose S0.5 | 6–10 mM | Glucokinase mol. physiology | dose-response |

The first three are read from the glucose/ATP model after it runs to an energetic
steady state — they are **not seeded**; they emerge from the balance of
glucokinase consumption, ATP maintenance, and regeneration. The fourth sweeps
glucose through the glucokinase propensity and locates the half-maximal point.

Each target carries a measured range and a source; `evaluate_target` reports the
model value, whether it falls in range, and the relative error to the nearest
edge. `validation_accuracy` returns the fraction passing; `format_report` prints
a readable scorecard.

## Result — the first "how real" number

```
[PASS] Adenylate energy charge:        model=0.872   (measured 0.80–0.95)
[PASS] Steady-state cytosolic ATP:     model=3.5 mM  (measured 2.5–4.5)
[PASS] Total ATP:ADP ratio:            model=2.91    (measured 2–10)
[PASS] Glucokinase glucose S0.5:       model=8 mM    (measured 6–10)
Accuracy: 100% of targets within measured range
```

## What this does and does NOT mean

**Does:** the model's energy homeostasis and hepatic glucose-sensing are now
*measured* to be physiologically consistent, not assumed. There is finally a
number, and it is regression-guarded by tests.

**Does not:** this is 4 checkpoints on energy/glucose handling — not a validated
cell. Coverage is still <1% of a hepatocyte, most rate constants are still
placeholders, and whole categories (lipid, nitrogen/urea, redox dynamics, ion
homeostasis, signaling) have no measured checks yet. 100% here means "passes the
checkpoints we have," not "100% realistic." The honest headline: the first
validated behaviors are in place; the harness is the instrument that will keep
the rest honest as scope grows.

## Verification (`tests/test_stochastic_validation.py`, 5 tests)

Every target is sourced; energy charge, steady ATP, and the glucokinase
half-response are asserted in range; overall accuracy is reported.

Full engine suite: **101/101 passing** (96 prior + 5 new), no regressions.

## Next (the remaining gaps, now measurable)

- **Coverage** — add grounded pathways (urea cycle, lipid, PPP) and expand
  validation targets to each (urea output, NADPH/GSH redox, lactate).
- **Integration** — run glycolysis + expression + cycle as one coupled cell and
  validate whole-cell observables.
- **Spatial** — reaction–diffusion so the kinetic state has real geometry.
- **Grounding** — replace lumped placeholders with literature kinetics, each
  newly added constant earning a validation target.
