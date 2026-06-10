# Atomic Foundations

## Purpose

The first physical objects in the simulation are atoms and ions. Even when the
electron cloud is hidden visually, electron probability must remain part of the
conceptual and mathematical model.

## Required Concepts

- nucleus: protons and neutrons
- electrons as quantum states, not classical planets
- charge
- mass
- ionization energy
- electron affinity
- Coulomb attraction/repulsion
- kinetic energy
- potential energy
- probability density

## Quantum Representation

The project should not start by solving the full many-electron Schrodinger
equation in real time. Instead:

- simple atoms may use analytic or precomputed orbital probability fields
- complex atoms may use data-backed approximations
- visible electron clouds can be toggled off
- hidden state should still track electron count, charge state, and orbital
  model metadata

Useful conceptual rule:

```text
probability density = |psi(position, time)|^2
```

This is the basis for representing electron probability clouds. The visual cloud
is a rendering of probability density, not the electron moving along a tiny
classical orbit.

## Classical Interaction Baseline

For two charged particles:

```text
F = k_e * q1 * q2 / r^2
U = k_e * q1 * q2 / r
KE = 0.5 * m * v^2
```

Where:

- F is electrostatic force magnitude
- U is electrostatic potential energy
- KE is kinetic energy
- k_e is Coulomb's constant
- q1 and q2 are charges
- r is distance
- m is mass
- v is velocity

## Gravity

Gravity should exist in the global physics vocabulary, but it is usually
negligible at atomic and cellular molecular scales compared with electrostatic,
thermal, and chemical interactions. It can be included as a global field and
disabled or visually de-emphasized depending on scale.

## First Simulation Decision

The two-ion milestone should start with:

- two point-like ion bodies
- charges +1e and -1e
- mass values selected from chosen ion species
- Coulomb attraction
- kinetic and potential energy readouts
- optional electron cloud overlay
- minimum radius or force softening for numerical stability

## Open Questions

- Which two ions should the first demo use: Na+ and Cl-, H+ and Cl-, or an
  abstract positive/negative ion pair?
- Should the first demo allow bond/compound formation, or only attraction and
  stabilized approach?
- How should solvent be represented in milestone 001: vacuum, implicit water,
  or hidden damping field?

## Sources

- NIST physical constants: https://pml.nist.gov/cuu/Constants/
- NIST Chemistry WebBook: https://webbook.nist.gov/
- OpenStax hydrogen atom: https://openstax.org/books/university-physics-volume-3/pages/8-1-the-hydrogen-atom
- OpenStax quantum theory: https://openstax.org/books/chemistry-2e/pages/6-3-development-of-quantum-theory
