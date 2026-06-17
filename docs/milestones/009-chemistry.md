# Milestone 009: Chemistry (reaction–diffusion)

## Objective

Bring real chemistry into the project: molecules that react. Two reactant
species diffuse and combine into a product — **A + B → C** — the simplest unit of
the chemistry that, grounded the same way, later drives metabolism and signaling.

## Model (`src/physics/reactions.ts`)

Particles of species A and B undergo Brownian motion in a periodic box and react
on contact (within a reaction radius) to form C. This is the **Smoluchowski**
picture of a diffusion-limited reaction, whose rate constant is, from first
principles,

```text
k = 4π (D_A + D_B) R          (Smoluchowski, 1917)
```

The rate is not invented: it emerges from sourced diffusion coefficients and a
contact radius. The engine reports `k` and the live A/B/C counts.

## Validation (covered by tests)

- **Atom conservation**: every C is produced from exactly one A and one B
  (A + C = A₀, B + C = B₀, reactions = C).
- **It proceeds**: reactants fall, product rises over time.
- **Rate ∝ R**: a larger reaction radius yields more product (Smoluchowski k ∝ R).
- **Rate ∝ diffusion**: faster D yields more product in the same time
  (k ∝ D_A + D_B).
- The engine exposes a positive Smoluchowski rate constant and a scene.

## In the viewer

A **Chemistry** building-block scene, drawn as a point cloud: blue A and gold B
react into green C. The readout shows live counts of A, B, C and the number of
reactions. Watch A and B fall as C climbs.

## Honest boundaries

- One irreversible bimolecular reaction (A + B → C), diffusion-limited, in
  implicit solvent — no reverse reaction, catalysis, or energy budget yet.
- These are generic species, not parameterized real metabolites; the point is the
  correct, grounded *mechanism*, ready to be specialized with measured rate
  constants when specific chemistry is modeled.

## Next

Coupling chemistry to the cell (reactions inside the vesicle, a pump with an ATP
cost), then the continuum/fluid handoff and growth — the documented frontier in
`docs/05-roadmap.md`.
