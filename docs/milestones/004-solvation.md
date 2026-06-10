# Milestone 004: Solvation (ions in water)

## Objective

Put ions and water in the same box and let them interact, so we can see the
single most important event in cell chemistry: an ion gathering a **hydration
shell**, and a salt beginning to **dissolve**.

## Unified engine (`src/physics/solvation.ts`)

The ion engine (point charges) and the water engine (rigid SPC/E molecules) were
unified into one site-based molecular-dynamics system. Every body — whether a
single-site ion or a three-site rigid water — contributes charged sites, and all
non-bonded interactions between sites on different bodies are:

- **Coulomb**: `F = k·e²·q_i q_j / r²`
- **Lennard-Jones**: `U = 4ε[(σ/r)¹² − (σ/r)⁶]`, with **Lorentz–Berthelot**
  mixing (`σ_ij = (σ_i+σ_j)/2`, `ε_ij = √(ε_i ε_j)`).

Translation uses symplectic Euler for all bodies; rotation (Euler's equations +
quaternion update) is applied to water only. Units stay nm / fs / eV / u / e.

## Sourced parameters (nothing invented)

- Ion Lennard-Jones: **Joung & Cheatham 2008** (J. Phys. Chem. B 112, 9020),
  the SPC/E-specific set, converted from their Rmin/2 (Å), ε (kcal/mol) to
  σ (nm), ε (eV): Na+ σ = 0.2160 nm, ε = 1.475 kJ/mol; Cl- σ = 0.4830 nm,
  ε = 0.0535 kJ/mol.
- Water: SPC/E (as in Milestone 003).
- Ion charges ±1 e, masses from IUPAC.

## Validation (covered by tests)

- A Na+ ion surrounded by water pulls the water **oxygens inward** (the negative
  end of the dipole turns toward the cation) and settles them at
  **Na–O ≈ 0.235 nm** — the experimental first-shell distance. Measured across
  six waters: 0.235–0.254 nm.
- Lennard-Jones repulsion prevents the water from collapsing onto the ion
  (Na–O stays > 0.18 nm).
- Water stays perfectly rigid (O–H = 0.1 nm) throughout; total energy finite.
- "NaCl in water" is represented as Na+ + Cl- + a water bath.

## In the viewer

A new **Solvation** scene group:

- **Na+ hydration shell** — watch six waters rotate so their O atoms face Na+ and
  lock into the first shell; the readout shows the live Na–O distance.
- **NaCl in water** — Na+ and Cl- each collect their own water molecules.

## Honest boundaries

- Few water molecules (6–8), no periodic boundaries / Ewald summation, so this is
  a small cluster, not bulk solution. Coordination numbers and full dissolution
  need many more waters and long-range electrostatics — a later milestone.
- Damped (settling) dynamics for a clear picture, not a constant-temperature
  ensemble.

## Next

1. scale up the number of water molecules and add periodic boundaries + a proper
   long-range electrostatics treatment
2. continuum / fields for bulk solvent (the particle→field handoff)
3. begin a lipid membrane patch (Milestone 005)
