# One Reality — coarse-grained, but grounded

## The decision

The project's main view is no longer a menu of isolated demos. It is **one
reality**: a single living slice of a cell — a lipid membrane separating an
inside from an outside, with particles populating both compartments, all in one
box, on one clock. (`Cell — one reality`, the default scene.)

The earlier per-phenomenon scenes (ions, the ionic bond, water, solvation,
diffusion, the bare membrane, transport) are kept, but demoted to **"building
blocks"** — they are the zoom-ins that show the rules underneath the one reality.

## The scale choice (and the honest limit)

You cannot render individual atoms *and* a whole cell in the same real-time
frame — a cell is ~10¹⁴ atoms. So "one reality" means choosing a scale, and we
chose the **cell scale**. At this scale the world is coarse-grained: lipids and
solutes are beads, not atoms.

## The principle that must never be broken

**Coarse-grained is not cartoon.** Not drawing the atoms does not mean deleting
the atomic/chemical rules. The cell-scale model must *carry* the lower-scale
physics in its parameters and behavior, so that when we later add chemistry
(signaling, reactions, and eventually disease processes like cancer), those
processes are genuinely *present and lived* in this reality — just not drawn.

This is why every parameter so far is sourced and traceable down a scale:

- the ionic-bond repulsion is derived from the quantum Pauli exclusion energy;
- SPC/E water charges come from quantum chemistry;
- Joung–Cheatham ion parameters come from measured hydration free energies;
- diffusion coefficients and viscosity are measured (CRC);
- the Cooke–Deserno membrane reproduces real bilayer elasticity and thickness.

Each cell-scale rule traces to a molecular/atomic justification. That chain of
provenance *is* how the atomic world stays alive at the cell scale.

## What "one reality" contains now

- a fluid lipid bilayer (Cooke–Deserno) as a real inside/outside boundary;
- solute particles in both compartments, moving by thermal (Langevin) motion;
- a periodic box so the membrane is effectively unbounded laterally.

## Where it goes next

- give solutes chemical identity (species, charge) so real chemistry can run in
  this reality;
- add transport proteins / pores and an electrochemical gradient;
- add reaction–diffusion fields for metabolites and signals;
- a continuum/fluid layer where bulk solvent flow matters (low-Reynolds Stokes);
- pathway machinery — the substrate on which disease processes (e.g. cancer
  signaling) could later be modeled, grounded the same way.

Guiding rule, unchanged: **nothing invented; everything traceable to a measured
or first-principles source.**
