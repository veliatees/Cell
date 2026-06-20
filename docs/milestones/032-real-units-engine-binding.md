# Milestone 032 — Binding real units into a running cell model

## Why

M030 gave real units; M031 gave the stochastic reaction core. M032 connects
them into one runnable object so the cell is actually driven by counts and real
kinetics instead of normalized hand-picked coefficients. The legacy
`step_cell` deterministic loop (which feeds the visual snapshot bridge) is left
untouched; this is a parallel, real-units path that the quantitative simulation
grows on.

## What was added

- `stochastic/cell_model.py`
  - `CellReactionModel` — wraps a `ReactionNetwork`, molecule `counts`, and a
    real compartment volume. Reports `concentration_mM(...)` / `concentrations_mM()`
    and steps via `advance(t_end, rng, mode=...)` with `mode in {ssa, cle, hybrid}`.
  - `build_hepatic_glucose_atp_network(volume)` — a small but **running and
    conservative** cytosolic subset: real glucokinase (Hill kinetics) plus three
    clearly-labelled lumped placeholders that keep the system bounded and the
    adenylate pool (ATP+ADP) conserved.
  - `seed_glucose_atp_model(definition)` — seeds the counts directly from the
    M030 grounded concentrations and hepatocyte geometry.
- `stochastic/integrators.py`
  - `simulate_hybrid` — operator-split SSA+CLE: any reaction touching a low-copy
    reactant is integrated exactly, the rest take the continuous update,
    re-partitioned every step. Reduces to pure SSA (all low-copy) or pure CLE
    (all high-copy) in the limits.

## What it demonstrates

Seeded from real units, ATP starts at ~3.5 mM (~3.7e9 molecules in the cytosol)
and glucose at ~7 mM. Run forward, the adenylate regeneration/maintenance loop
holds ATP in a physiological 2-5 mM band, glucokinase converts glucose to
glucose-6-phosphate, and glucose depletes only modestly over 60 s. The model is
bounded, non-negative, and seed-deterministic.

## Honest limits (v1)

The only real rate law here is glucokinase. Glucose has no buffered portal
supply yet, so it slowly depletes; the ATP regeneration/drain reactions are
lumped placeholders chosen for conservation and boundedness, not measured
fluxes. They are labelled `LUMPED placeholder` in code. Replacing them with full
per-enzyme glycolysis (or urea-cycle) kinetics is M033.

## Verification (`tests/test_cell_model.py`, 4 tests)

- Counts seed to physiological concentrations (ATP ~3.5 mM, glucose ~7 mM).
- A 60 s run stays bounded, non-negative, ATP in 2-5 mM, glucose only modestly
  consumed, and glucose-6-phosphate produced.
- The adenylate pool ATP+ADP is conserved to <0.1% (stoichiometric invariant).
- All three integration modes run.

Exact SSA on a ~1e9-molecule system is deliberately costly — the concrete reason
the CLE/hybrid path exists — so the SSA smoke test uses a sub-millisecond
horizon.

Full engine suite: **71/71 passing** (67 prior + 4 new), no regressions.

## Next

- **M033** — replace the lumped reactions with a full pathway (glycolysis or the
  urea cycle), each enzyme carrying literature Km/Vmax/kcat with provenance.
