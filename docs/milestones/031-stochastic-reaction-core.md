# Milestone 031 — Stochastic reaction core (SSA + CLE)

## Why this is the keystone

The whole roadmap — real rate constants, central dogma, scope, division, cancer
— is the same object underneath: **reactions firing on molecule counts**. A gene
expressing is a low-copy reaction; a metabolic flux is a high-copy reaction; cell
division is counts being partitioned. So before any of that, the engine needs a
correct stochastic reaction core that operates on the real counts from the M030
quantitative foundation. This milestone builds and validates it.

It is additive: the legacy deterministic `step_cell` loop is untouched. Wiring
this core into the live loop is M032.

## What was added (`cell_engine.stochastic`)

- `reactions.py`
  - `Reaction` (reactant/product stoichiometry + a propensity in molecules/s)
    and `ReactionNetwork` (species, reactions, compartment volume).
  - `mass_action(...)` — takes a **real macroscopic rate constant** `k` and
    converts to the stochastic constant `c = k * (N_A V)^(1-order)`. The
    propensity uses the falling-factorial combinatorial count, so it is exact at
    low copy numbers (`2A→` uses `X(X-1)/2`, not `X²`) and reduces to mass action
    at high counts.
  - `michaelis_menten(...)` — Michaelis-Menten / Hill propensity from molar
    `Vmax` and `Km` (or `S0.5`), reading concentration from counts and volume.
- `integrators.py`
  - `gillespie_step` / `simulate_ssa` — **exact** stochastic simulation
    (Gillespie Direct Method). The right tool for low-copy species.
  - `cle_step` / `simulate_cle` — **chemical Langevin** (Euler-Maruyama): drift
    `+ √propensity` diffusion per reaction. The right tool for high-copy species;
    fixed cost per step instead of per event.
  - `partition_species_by_copy` — splits species into low-copy (→SSA) and
    high-copy (→CLE) sets. This is the seam for the hybrid regime real cells
    require; full hybrid coupling is a later milestone.
- `kinetics_data.py`
  - `GLUCOKINASE` + `glucokinase_reaction(...)` — the hepatic glucose-sensing
    step encoded with **literature constants**: glucose S0.5 ≈ 8 mM, Hill ≈ 1.7,
    kcat ≈ 48 /s, Mg-ATP Km ≈ 0.4 mM. The sigmoidal high-S0.5 behavior is the
    reason the liver only traps glucose when blood glucose is high — and it falls
    straight out of the propensity.

`EngineRng` gained `expovariate` (SSA waiting times) and `gauss` (CLE noise).

## How it is validated (method correctness, not yet biology)

Biological-data validation is deliberately later. First the *integrators* must be
provably correct, so they are tested against systems with closed-form answers
(`tests/test_stochastic_core.py`, 8 tests):

- **Birth-death → Poisson:** SSA stationary mean = a₀/k_deg and variance = mean.
- **Reversible A⇌B → Binomial:** stationary mean = Np and variance = Np(1−p).
- **CLE consistency:** the Langevin integrator reproduces the same stationary
  mean (~50) and noise scale (std ≈ √50) as the SSA/Poisson result.
- **Hill law:** glucokinase velocity is exactly Vmax/2 at glucose = S0.5 and
  saturates toward Vmax far above it.
- **Low-copy combinatorics**, **first-order propensity**, **seed determinism**,
  and the **copy-number partition** are all checked directly.

Full engine suite: **67/67 passing** (59 prior + 8 new), no regressions.

> Sandbox note: project targets Python 3.11+ (`datetime.UTC`); the CI sandbox
> had only 3.10, so verification used an in-memory `datetime.UTC` shim. Local
> 3.14 runs `python -m unittest discover -s engine/tests -t engine` directly.

## Next

- **M032** — bind this core into `step_cell`: evolve a real reaction network on
  real counts instead of the normalized hand-picked coefficients.
- **M033** — encode one full pathway (glycolysis or urea cycle) with per-enzyme
  literature kinetics.
- **M034** — central dogma as low-copy SSA reactions driving enzyme levels.
