# Milestone 005: Diffusion & Brownian Motion

## Objective

Add the motion that dominates the cell: diffusion. At cell scale, inertia is
negligible and everything moves by random thermal jostling, so this is the first
genuinely "cellular-scale" physics — and the conceptual gateway to the later
particle→field (continuum) handoff.

## Model (`src/physics/diffusion.ts`)

Overdamped Langevin (Brownian) dynamics. Each timestep a particle takes a random
step plus an optional drift:

```text
Δx = (D/kT)·F·Δt + √(2 D Δt)·ξ      ξ ~ N(0,1) per axis
```

With no force this is pure diffusion, whose mean-squared displacement grows as
⟨r²⟩ = 6·D·t in 3D. The drift term encodes the Einstein mobility μ = D/kT.

## Sourced parameters

Source: CRC Handbook (ion D° from limiting molar ionic conductivities via the
Nernst–Einstein relation), 25 °C.

- water dynamic viscosity η = 0.890 mPa·s
- aqueous ion self-diffusion: Na+ D° = 1.334×10⁻⁹ m²/s, Cl- D° = 2.032×10⁻⁹ m²/s
- water self-diffusion ≈ 2.30×10⁻⁹ m²/s
- Stokes–Einstein helper: D = kT / (6πηr)

## Validation (covered by tests)

- The simulation **recovers the input D** from the measured MSD (D = ⟨r²⟩/6t)
  to within 10% over 4000 tracers — proves the stochastic integrator is correct.
- MSD grows **linearly** in time (diffusive, not ballistic): doubling time
  doubles MSD.
- Faster D spreads wider in the same time.
- Stokes–Einstein gives a physically reasonable D (~10⁻⁹ m²/s for a nm sphere)
  and obeys D ∝ 1/r.

## In the viewer

A new **Diffusion** scene group, drawn as an efficient point cloud:

- **Diffusion (ink drop)** — 200 tracers released at a point spread outward; the
  readout shows live RMS displacement and ⟨r²⟩.
- **Na+ vs Cl- diffusion** — the chloride cloud visibly spreads wider than
  sodium, matching their measured diffusion coefficients.

## Honest boundaries

- Implicit solvent: water is represented only through D and viscosity, not
  explicit molecules (that is the point of Brownian dynamics).
- No inter-particle interactions in the diffusion scenes (independent tracers);
  crowding/interaction is a later concern.

## Next

Milestone 006 — the lipid membrane patch: the first mesoscale structure and the
project's first real inside/outside boundary.
