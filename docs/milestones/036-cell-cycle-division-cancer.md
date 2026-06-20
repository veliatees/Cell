# Milestone 036 — Cell states, growth, division, and cancer

## Why

The final item on the roadmap list: emergent cell-level behavior on top of the
kinetic + expression core. A real cell is not a fixed bag of reactions — it
grows, passes through cell-cycle states with checkpoints, divides (partitioning
its molecules between two daughters), and can lose that control (cancer). M036
adds all four.

## What was added (`stochastic/cell_cycle.py`)

- **State machine (G1 → S → G2 → M):** `step(state, dt, params)` grows the cell
  and evaluates the current phase's transition. G1/S and G2/M are **size
  checkpoints** (require a biomass threshold); S replicates the genome; M ends in
  division.
- **Growth:** a biomass proxy that accumulates only while a nutrient
  (ATP by default) is present — so a starved cell arrests in G1 and never
  divides (a real checkpoint behavior).
- **Genome replication:** entering G2, the genome species double (2 → 4 copies).
- **Division with the right noise structure:** `divide(...)` splits a mitotic
  cell into two daughters. The genome **segregates exactly** (sister chromatids,
  2 + 2 — chromosomes are not partitioned randomly), while every other species
  partitions **binomially** (Binomial(n, ½)) — the real stochastic partitioning
  noise, exact at low copy via Bernoulli sampling and a normal approximation at
  high copy. Total counts are conserved exactly; biomass halves.
- **Cancer (oncogene):** `oncogene_active=True` bypasses the size checkpoints, so
  the cell cycles on phase durations alone regardless of size — uncontrolled
  proliferation. `simulate_lineage(...)` follows one daughter to compare rates.

## What emerges (and is validated) — `tests/test_cell_cycle.py`, 9 tests

- Phases advance strictly in order G1 → S → G2 → M.
- Genome is replicated (2 → 4) during S, before division.
- A **starved cell arrests** in G1 (checkpoint works).
- Division **conserves every species' count** exactly.
- Genome **segregates exactly** 2 + 2; small molecules partition **binomially**
  with the correct statistics (mean n/2, variance n/4).
- Daughters reset to G1, halve biomass, increment generation.
- **Cancer:** an oncogene-active lineage completes **more divisions** in the same
  time, and divides **even while undersized/starved** — exactly the loss of
  checkpoint control that defines uncontrolled proliferation.

Full engine suite: **96/96 passing** (87 prior + 9 new), no regressions.

## Honest limits (v1)

Growth is a biomass *proxy* that ticks up with time-while-fed, not biomass
synthesised stoichiometrically from the metabolic network; coupling biomass to
actual flux (and the oncogene to a real expressed gene from M034/M035) is the
natural next step. Checkpoints are size/time thresholds, not the real
CDK/cyclin/p53 control circuitry. The model captures the *structure and noise* of
the cell cycle and division, not yet its molecular regulation.

## Where this leaves the roadmap

The original list — real units, stochastic core, real kinetics, central dogma,
scope/integration, and states/growth/division/cancer — is now all in place as a
tested, source-grounded foundation (M030–M036). What remains is depth: more
grounded kinetics, real checkpoint circuitry, and the step the project has
deliberately deferred — **validation against real data** — plus the longer-horizon
goals (host–pathogen, multicellular tissue).
