# Milestone 003: Real Water (SPC/E)

## Objective

Add water — the medium in which all of cell biology happens — as a *real*,
source-backed molecule, not a decorative blob. This is the first molecule in the
project with internal structure and orientation, so it is also where the project
gains a proper rigid-body molecular-dynamics engine.

## Why This Step (and not a crystal)

The project is heading toward a cell, and a cell is ~70% water. Every later
process — ion solvation, membranes, transport, protein behavior — happens in
water. A salt crystal would be a detour downward into the solid state; water is
the road upward toward biology.

## Model: SPC/E (sourced, not tuned)

Source: Berendsen, Grigera & Straatsma (1987), "The Missing Term in Effective
Pair Potentials", J. Phys. Chem. 91, 6269. Every number is from the paper:

- O–H bond length 0.1 nm, H–O–H angle 109.47°
- partial charges q(O) = −0.8476 e, q(H) = +0.4238 e
- Lennard-Jones on oxygen only: σ = 0.3166 nm, ε = 0.6502 kJ/mol
- masses from IUPAC standard atomic weights

Interactions: Coulomb between all site pairs on different molecules, plus an
O–O Lennard-Jones term. Water is treated as a **rigid body** (its geometry can
never deform), which is exactly what "rigid SPC/E" means.

## New Engine: rigid-body dynamics (`src/physics/water.ts`)

Built from scratch because a point-particle engine cannot represent an oriented
molecule. Each molecule carries a centre of mass, velocity, an orientation
quaternion, and a body-frame angular velocity. Per step the engine:

1. places the three sites in world space from the orientation quaternion,
2. sums Coulomb + LJ forces over all inter-molecular site pairs,
3. reduces them to a net force and a torque about each centre of mass,
4. integrates translation (symplectic Euler) and rotation (Euler's equations in
   the body frame + quaternion update).

Units are consistent throughout: nm, fs, eV, u, e.

## Validation (all covered by tests)

- **Dipole moment = 2.35 D** — reproduces the known SPC/E value exactly, which
  confirms the geometry and charges are right.
- Molecule is electrically neutral; O–H length and H–O–H angle match the inputs.
- **Rigidity**: after thousands of steps of translation + spin, every internal
  distance is unchanged to 1e-6 nm.
- **Energy conservation (NVE)**: a free spinning molecule conserves energy
  exactly; an interacting pair conserves total energy to <5% over thousands of
  steps — the integrator is sound.
- **Water dimer**: two molecules released apart bind into a hydrogen-bonded
  dimer at **O–O ≈ 0.273 nm** with a binding energy of **≈ −30 kJ/mol**, both in
  the published SPC/E range (~0.276 nm, ~−30 kJ/mol). Not tuned — it emerges.

## Honest Boundaries

- Rigid (non-polarizable) water, as SPC/E is defined. No bond flexibility.
- No long-range electrostatics treatment (Ewald/PME) yet; fine for a few
  molecules, needed later for bulk water.
- Not yet coupled to the ion engine — that is the next step.

## Next Milestone

Toward Milestone 004 (solvation):

1. unify ions and water into one site-based system
2. add sourced ion–water Lennard-Jones parameters (e.g. Joung–Cheatham 2008,
   parameterized specifically for SPC/E) — no invented mixing
3. show Na+ and Cl- gaining hydration shells; show NaCl dissociating in water
4. then scale up particle counts and introduce the field/continuum handoff
