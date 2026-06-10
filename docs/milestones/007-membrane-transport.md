# Milestone 007: Membrane Transport (barrier + pore)

## Objective

Give the membrane its first biological *function*. A bilayer is not just a
structure — it is a selective barrier. This milestone shows the two faces of
that: an intact bilayer **blocks** solutes, while a **pore** lets them cross.

## Approach (honest scoping)

This is built inside the membrane's own Cooke–Deserno reduced-unit world
(`src/physics/membrane.ts`), not by bolting the SI ion/water engines onto it.
Merging two different unit systems would be error-prone and misleading; keeping
one consistent model is the honest choice. So "transport" here is demonstrated
with generic **solute particles**, not a specific parameterized ion channel.

- Solute beads interact with lipids and each other by **WCA repulsion only**
  (steric exclusion) — no charge, no tail attraction. They feel the same
  Langevin thermostat and lateral periodic boundaries as the lipids.
- They start above the membrane and diffuse under thermal motion.
- A **pore** is made by removing a disk of lipids from the bilayer centre.

This is a *qualitative* transport demonstration (barrier vs. permeation), not a
quantitative permeability or channel-conductance model.

## Validation (covered by tests)

- **Barrier:** with an intact bilayer, zero solutes cross to the far side over
  the test run — the membrane keeps them out.
- **Transport:** with a central pore, solutes reach the other side
  (soluteBelow ≥ 1) — they permeate through the channel.

Both runs are deterministic (seeded), so the contrast is reproducible.

## In the viewer

Two new **Membrane** scenes:

- **Barrier (intact bilayer)** — green solutes sit above the bilayer and bounce
  off; the readout shows the above/below counts holding steady.
- **Transport through a pore** — the same setup with a hole in the bilayer;
  solutes cross to the other side. The readout's above/below counts shift.

## Honest boundaries

- Generic solutes (no charge, no selectivity); a real channel is selective by
  charge/size and is gated — future work.
- A static hole, not a protein channel; fluid lipids can slowly reshape it.
- No electrochemical gradient or membrane potential yet.

## Next

Milestone 008 — the continuum handoff: where bulk solvent becomes a field
(reaction–diffusion) and, where flow matters, low-Reynolds-number (Stokes)
fluid mechanics enters. Then a membrane-bounded compartment → minimal cell.
