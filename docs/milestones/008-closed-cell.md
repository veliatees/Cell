# Milestone 008: The Closed Cell (vesicle)

## Objective

Turn the membrane into an actual **cell**: a closed spherical bilayer (a vesicle)
that encloses an interior, holds its contents, and can exchange material with the
outside through a pore. This is the headline "one reality" the app opens with.

## What was built (`src/physics/membrane.ts`)

- **Vesicle mode**: lipids tiled on a sphere as two leaflets (heads out / heads
  in, tails meeting at the mid-radius) via an even Fibonacci distribution. No
  periodic boundaries — a vesicle is a free 3D object.
- **Warm-up force cap**: tiling rigid lipids on a sphere creates unavoidable
  initial overlaps; for the first steps the per-bead force is capped so they
  relax gently instead of exploding through the steep WCA wall. Standard MD
  warm-up; it does not change the equilibrium physics.
- **Neighbor (cell) list**: non-bonded forces use a spatial grid, making the cost
  O(N) instead of O(N²). This is what makes a ~700-bead vesicle run smoothly at
  one physics step per animation frame.
- **Pore + exchange**: a polar cap of lipids can be left open, and solutes can be
  placed inside and outside, so the cell takes up / releases material through the
  hole.

## Validation (covered by tests)

- The default `cell-reality` scene is a vesicle of a performant size (< 1000
  beads), builds finite, contains solutes.
- A closed vesicle **stays closed and traps its contents**: lipid beads stay in a
  spherical shell, none fly off, and most solutes remain enclosed over a long run.
- A **pore** lets the cell exchange contents: the enclosed-solute count changes
  as material moves through the hole.

## In the viewer

- **Cell — one reality (vesicle)** — the default: a round closed cell, gold head
  groups forming the surface, blue tails in the shell, green particles trapped
  inside. The readout shows enclosed / total solutes and the order parameter.
- **Cell with a pore (exchange)** — the same cell with an open pore and particles
  inside and outside; watch the enclosed count change as it exchanges.
- The flat-slice, bare-bilayer, barrier, pore, and self-assembly scenes remain as
  building-block "zoom-ins".

## Honest boundaries

- Generic coarse-grained lipids and solutes — no chemical species identity or
  reactions yet. Transport here is steric (a hole), not a selective protein
  channel or a pump.
- A single vesicle, not yet coupled to explicit water/ions (those live in the
  atomic-scale building-block scenes, a different unit system).
- This is a *minimal* cell: a boundary that encloses and exchanges. Metabolism,
  signaling, growth and division are the frontier below.

## Where "finished" honestly stands

The project now spans a coherent, source-grounded path from a single atom to a
closed, exchanging cell — every layer validated against measured or
first-principles data. A *complete* living human cell (let alone disease
processes like cancer) is not something any simulator finishes; it is open
research. What is finished here is a faithful **minimal-cell simulator** and a
documented, honest road for everything above it (see `docs/05-roadmap.md`).
