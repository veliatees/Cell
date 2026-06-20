# Milestone 045 — Cell death: apoptosis vs necrosis (ATP switch)

## Why

A roadmap process ("apoptosis", "stress response") and the natural endpoint of the
stress the other modules generate. M045 adds the cell's **death decision**: it
integrates oxidative, energetic, damage, and infection stress and, past a
threshold, commits **irreversibly** to death — choosing between **apoptosis** and
**necrosis** by the cell's energy state — and it does so by *reading the outputs
of the detox (M044) and virus (M042) modules*, tying the engine together.

## The apoptosis/necrosis distinction (grounded)

Apoptosis is an active, **ATP-dependent** program; necrosis is passive lysis.
Leist et al. 1997 (J Exp Med) and Eguchi et al. 1997 (Cancer Res) showed
intracellular **ATP is the switch**: the same apoptotic stimulus produces necrosis
instead when ATP is depleted. So the model selects the mode by energy:

- **Necrosis** if ATP collapses (energy charge below the necrosis floor while the
  cell is injured), or if the caspase program reaches commitment but ATP is too
  low to execute apoptosis.
- **Apoptosis** if commitment is reached with ATP intact.

This is why **paracetamol overdose dies by necrosis** (NAPQI adducts collapse
mitochondrial ATP), not apoptosis — which matches the real clinical pathology.

## What was added (`stochastic/apoptosis.py`)

- `StressSignals` — ROS load, energy charge, surviving-GSH fraction, damage, viral load.
- `death_drive(signals)` — a state-conditioned pro-death drive (`P(event | state)`).
- `DeathState` with `mode ∈ {alive, apoptosis, necrosis}`; `step_death` / `run_death`
  accumulate caspase, apply the ATP switch, and latch the outcome irreversibly.
- `signals_from_detox` / `signals_from_infection` — translate M044/M042 outputs
  (including ATP collapse from adduct damage) into death signals.

## What it shows (and is validated) — `tests/test_apoptosis.py`, 6 tests

- **Healthy cell survives.**
- **Stress with ATP intact → apoptosis; the same insult with ATP collapsed → necrosis.**
- **Commitment is irreversible** and the mode is latched (healthy signals afterward
  do not revive or switch it).
- **Integrated — paracetamol overdose → necrosis**, therapeutic dose → survives.
- **Integrated — heavy viral infection → apoptosis**, uninfected cell survives.

Full engine suite: **138/138 passing**, no regressions.

## Honest limits

The caspase switch is a single accumulate-and-latch variable, not the real
Bcl-2/Bax/cytochrome-c/caspase-9 network; the apoptosis/necrosis *selection* is
modelled (by the ATP switch) but their distinct downstream execution
(membrane blebbing vs swelling/rupture, inflammatory signalling) is not; and the
thresholds/weights are reasoned, not yet fit to measured death-rate data (a future
calibration target via M041).
