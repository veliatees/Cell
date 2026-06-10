# Milestone 006: Lipid Membrane (the first cell boundary)

## Objective

Build the structure that *makes* a cell a cell: a lipid bilayer. This is the
first mesoscale object and the first real inside/outside boundary — the moment
the project starts to look like biology.

## Model: Cooke–Deserno solvent-free lipids (`src/physics/membrane.ts`)

Source: Cooke, Kremer & Deserno, "Efficient tunable generic model for fluid
bilayer membranes", Phys. Rev. E 72, 011506 (2005). Each lipid is one head bead
plus two tail beads. Remarkably, simple pair potentials make lipids
self-assemble into a fluid bilayer with **no explicit solvent** — the solvent's
effect is folded into a tunable tail–tail attraction.

Potentials, exactly as published (Eqs. 1–4):

- **WCA repulsion** sets bead sizes: `b = 0.95σ` (head–head, head–tail), `σ` (tail–tail).
- **FENE bonds** link the three beads: `k = 30 ε/σ²`, `r∞ = 1.5σ`.
- **Bending spring** (head ↔ 2nd tail, rest length 4σ, `k = 10 ε/σ²`) keeps lipids straight.
- **Tail attraction** `−ε cos²[π(r−r_c)/(2w_c)]` with range `w_c = 1.6σ` → fluid bilayer.
- **Langevin thermostat** at `k_BT = 1.1 ε`, plus lateral **periodic boundaries**
  (x, y), exactly as the model is meant to be run.

## Units (honest)

This is a *generic* coarse-grained model in reduced units (σ, ε, τ), not SI.
By the paper's own calibration a bilayer is ~5σ thick ≈ 5 nm, so **σ ≈ 1 nm**.
Forcing fake SI numbers would misrepresent the model, so the engine keeps σ/ε/τ
and states the mapping.

## Validation (covered by tests)

- Lipids are built correctly (1 head + 2 tails) in two leaflets.
- The bilayer is real: heads point outward, tails sit toward the midplane,
  thickness in the bilayer range.
- Under thermal motion it **stays a cohesive, orientationally ordered bilayer**
  (order parameter S > 0.3) rather than melting into a gas or falling apart —
  this is the property naive Lennard-Jones models fail to reproduce, and the
  reason the Cooke–Deserno tail potential exists.
- Every bead stays finite over long runs.

Note: lateral periodic boundaries were essential — a free finite patch splays at
its edges and loses order; with PBC (as in the paper) the bilayer is stable.

## In the viewer

A new **Membrane** scene group:

- **Lipid bilayer patch** — a pre-assembled bilayer; heads (gold) form the two
  outer surfaces, tails (blue) fill the core. The readout shows the order
  parameter S and bilayer thickness (σ).
- **Membrane self-assembly** — lipids released as a random gas cluster
  tails-together into a bilayer, with no solvent.

## Honest boundaries

- Generic CG lipids: one species, no chemistry-specific head/tail identity yet.
- A flat periodic patch, not a closed vesicle (a vesicle is a natural next step).
- No explicit water here (the model is solvent-free by design); coupling a
  membrane to the explicit-water/ion engines is future work.

## Next

Milestone 007 — membrane transport: put a channel/pore in the bilayer and move
ions across it; the membrane's first biological *function*.
