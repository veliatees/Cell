# Milestone 013: The Imperfect, Spatial Cell (own loops, transport, faults, live report)

## The critique that drove this

Three demands, all sharper than "make it alive":

1. **Every** organelle — not just the mitochondria — must run its **own
   independent internal cycle / lifestyle**. They must not flow in lockstep.
2. The cell must be **imperfect**, because its environment is imperfect. Most of
   the time it works; sometimes it fails. And the failures are **not magic
   randomness** — what people call "random" is the uncomputable deterministic
   detail of the conditions. We model that as **probability driven by stress**.
3. ATP is **not used the instant it is made**. It has to travel a distance `x`
   from where it is produced to where it is consumed, and that takes time.
4. A **live report screen**: what each organelle is doing right now, what is
   moving where — plus an event log written **after** events happen (because the
   system is probabilistic, we don't know them in advance), updating continuously.

## 1. Each organelle has its own cycle (`CYCLE` in `cell.ts`)

Every organelle module advances its **own phase at its own period**, and its
activity is modulated by a rhythm whose time-average is exactly 1 (so steady-state
throughput is preserved). Two lifestyles:

- **Continuous** (powerhouses): mitochondria (~11 s swell), glycolysis (~5 s),
  membrane transporters (~7 s) — always on, gently oscillating.
- **Bursty** (batch workers): nucleus (~18 s), ribosomes (~4 s), Golgi (~9 s),
  lysosome (~13 s) — quiet between bursts, then a sharp pulse (~3–4×).

These bursty patterns are real: **transcriptional and translational bursting**,
**quantal (vesicle-by-vesicle) Golgi trafficking**, and **pulsatile lysosomal
degradation**. The periods are illustrative assumptions; the point is that **no
two organelles run on the same clock**.

## 2. ATP transport takes time (`setGeometry`, diffusion delay)

Each organelle has a **local ATP availability** that lags the global pool with a
diffusion time **τ = x² / (6·D)**, where `x` is its distance from the
mitochondrial source and `D` is the measured cytoplasmic ATP diffusion
coefficient (~150 µm²/s; Hubley et al. 1996). The viewer measures the real
distance from each organelle to the mitochondria in the scene and feeds it in, so
**organelles far from the mitochondria feel ATP changes later** and can be starved
of delivery even when the whole cell has ATP. Each organelle's ATP-dependent flux
is gated by *its* local availability, not the global average.

## 3. It is imperfect — stress-driven probabilistic faults

Each organelle carries an **efficiency** (0–1) that scales its work. A **fault
hazard** rises with stress (low local ATP, accumulated waste); each step there is
a probability `hazard·dt` of a fault that drops the efficiency. Organelles
**repair** over time (faster when ATP is available). So the cell mostly works, but
errors happen — and every error has a **cause** in the conditions, logged with
that cause. (Hazard rates are explicit assumptions; conservation and the
stress→failure structure are the real part.)

## 4. The live report panel (viewer)

Top-right of the organelle scene, updating every frame:

- a **status line** (health, energy charge, ATP, glucose, protein, waste, time);
- a **per-organelle row** for each compartment: what it is doing (e.g.
  `pyruvate → ATP`), an activity bar, a `burst / active / idle / FAULT` tag,
  its efficiency, the ATP it can actually reach, and its **ATP delivery time**;
- an **event log** written as things actually happen ("Mitochondria faulted —
  waste/oxidative stress", "Ribosomes repaired", "Cell under energy stress"),
  newest first, continuously.

In the 3D view each organelle now **glows with its own internal activity** (so you
see the bursts), and a **faulted organelle dims** — you can spot where the cell is
failing.

## Validated by tests (`cell.test.ts`, 12 tests)

Homeostasis, exact ATP+ADP conservation, starvation→death, recovery, dose
response — plus: every organelle's loop active at once; **distant organelles have
longer ATP transport times**; under stress organelles **fault and the cell logs
warn/crit events**; a well-fed cell is **mostly** (not perfectly) functional;
deterministic mode never faults; and **each organelle has a distinct phase and
period** (not in lockstep).

## Why this matters for the road ahead

This is the substrate for many interacting cells, each seeded with a different
character (organelle layout, periods, fault-proneness). Because faults are
probabilistic and cause-driven, we will be able to ask *which kinds of cells break
and why* — exactly the project's real goal.
