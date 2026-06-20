# Milestone 044 — Xenobiotic detox (CYP450) and drug toxicity

## Why

Detoxification is a defining hepatocyte job and an explicit roadmap process
("CYP detox"). M044 models it with a real worked example — **paracetamol
(acetaminophen)** — whose overdose mechanism is one of the best-understood cases
of drug-induced liver injury, and which couples directly to the M038 glutathione
system.

## What was added (`stochastic/detox.py`)

Two routes compete for the drug, and two routes compete for its reactive
metabolite:

- **safe conjugation** — glucuronide/sulfate (the dominant, non-toxic route)
- **CYP oxidation** — CYP2E1/CYP3A4 turn a fraction into reactive **NAPQI**
- **GSH conjugation** — NAPQI + GSH → harmless mercapturate (detox), consuming GSH
- **protein binding** — unconjugated NAPQI binds protein and raises ROS (toxic)

While GSH lasts, NAPQI is cleared safely; once GSH is exhausted, NAPQI lingers and
turns toxic. The threshold is emergent from the kinetics, not coded in.

## What it reproduces (and is validated) — `tests/test_detox.py`, 4 tests

A dose-response straight out of the clinical mechanism:

| Dose | GSH left | Protein adducts | ROS | Outcome |
|---|---|---|---|---|
| 2,000  | ~9,500 | ~12   | ~12   | detoxified (safe) |
| 10,000 | ~7,500 | ~64   | ~64   | safe |
| 30,000 | ~2,800 | ~320  | ~320  | stressed |
| 60,000 | **0**  | ~5,100 | ~5,100 | **toxic** (GSH collapse) |

- A therapeutic dose keeps GSH intact and makes almost no adducts.
- An overdose **depletes GSH**, and NAPQI then binds protein and raises ROS — the
  paracetamol hepatotoxicity mechanism, emergent.
- Toxicity is monotonic in dose.

Full engine suite: **137/137 passing**, no regressions.

## Honest limits

Amounts are abstract counts (mechanism grounded, absolute doses not); the safe
glucuronide/sulfate capacity is not saturable yet (real conjugation saturates at
high dose, which is part of why overdose tips over); mitochondrial/ATP collapse
and the downstream cell-death decision live in M045, fed by this module's ROS and
GSH-depletion outputs.
