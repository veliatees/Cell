# Milestone 039 — Integration: the unified whole cell

## Why

Until now the subsystems were separate modules. M039 runs them as **one cell**:
glycolysis + urea cycle + glutathione redox + gene expression in a single reaction
network sharing pools by name, with the cell cycle coupled to the cell's *actual*
metabolic state. This closes the loop M036 left open (growth was a free-floating
proxy) and demonstrates the hybrid integrator on a real composed cell.

## What was added (`stochastic/whole_cell.py`)

- `build_whole_cell_network` — `compose_networks(glycolysis, urea_cycle, redox,
  central_dogma, homeostasis)`. ATP/ADP are shared across glycolysis and the urea
  cycle, so the urea cycle literally spends the ATP glycolysis makes. A lumped
  OXPHOS regeneration, maintenance, and portal glucose supply keep energy and
  glucose in homeostasis.
- `WholeCell` — the unified network + counts + a `CellCycleState`, with
  `energy_charge()` and concentration helpers.
- `step_whole_cell` / `run_whole_cell` — advance the unified reactions (hybrid),
  advance the cell cycle reading the network's **real glucose pool**, and on
  mitosis **partition the network's real molecule counts** between daughters.

### One network, both noise regimes

The unified network contains high-copy metabolites and low-copy genes/mRNA at
once. The hybrid integrator is pinned to a **subsystem partition**
(`discrete_species = {gene, mRNA}` → exact SSA; everything else → CLE). This is
the choice real whole-cell models make (stochastic gene expression, continuous
metabolism) and it avoids the trap where a fast-turnover but low-copy metabolic
intermediate would force SSA into astronomically many events.

## What it demonstrates (and is validated)

`tests/test_whole_cell.py` (4 tests):
- **All subsystems compose** into one network with a single shared ATP pool.
- **A fed cell lives, grows, and divides** (3 divisions in ~160 s), expresses its
  gene (protein > 0), runs its urea cycle (urea > 0), and **holds energy charge
  in the healthy range (≈0.80)** under the combined metabolic draw.
- **A starved cell arrests** — no glucose and no portal supply, so it never passes
  the G1 size checkpoint and never divides. Growth is now genuinely gated on the
  metabolic state, not a free timer.
- **Division partitions the unified counts** — total counts conserved, genome
  segregated exactly.

Full engine suite: **113/113 passing** (109 prior + 4 new), no regressions.

## Honest limits (v1)

- Cell volume is not halved at division, so daughter *concentrations* look diluted
  after several divisions even though the energy charge (a ratio) stays correct.
  Volume dynamics are a clear next refinement.
- Energy/glucose homeostasis leans on lumped OXPHOS/supply placeholders; the
  emergent ATP balance is only as real as those.
- Gene expression co-runs but is not yet wired to set a specific metabolic Vmax
  in the unified cell (that coupling was shown in isolation in M035).

## Next

- **M040** — spatial reaction–diffusion: give this unified kinetic state real
  geometry, replacing the well-mixed assumption.
