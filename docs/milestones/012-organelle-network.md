# Milestone 012: The Organelle Network (parallel loops, shared currencies)

## The critique that drove this

Milestone 011 made the cell *alive* but with a single lumped metabolism. The next
demand was sharper: **nothing should be serial**. Each organelle should run its
**own loop** — its own mechanism that produces some things and consumes others —
and the organelles should be coupled the way they really are: through **shared
pools** of metabolites. And the headline question: *where does the ATP go, and
how is it used?*

## The model (`src/physics/cell.ts`)

The cell is now a set of **shared cytoplasmic pools** —

> glucose · pyruvate · amino acids · ATP/ADP · mRNA · protein · waste · (secreted)

— plus a set of **independent organelle modules**, each with its own kinetic loop
that reads the pools, consumes some, and produces others. They are integrated
together every step, so they all act **at the same time** on the shared
currencies — exactly how real biochemistry works (many compartments in parallel,
not a pipeline).

| Organelle / module | Consumes | Produces |
| --- | --- | --- |
| Membrane transporters | external nutrient, ATP (pumps) | glucose, amino acids |
| Cytosol — glycolysis | glucose | pyruvate, a little ATP |
| **Mitochondria** | pyruvate, ADP | **lots of ATP**, waste |
| Nucleus — transcription | ATP | mRNA |
| Ribosome / ER — translation | mRNA, amino acids, ATP | protein |
| Golgi — packaging | protein, ATP | secreted protein |
| Lysosome | waste | recycled amino acids |
| Maintenance | ATP | (the cost of being alive) |

**ATP is the shared currency.** Mitochondria (and glycolysis) *make* it; the
membrane pumps, nucleus, ribosomes, Golgi and maintenance *spend* it. So "where
ATP goes" is now explicit and visible: it is the one pool every other module
draws on.

## Real feedback, not just plumbing

Glucose uptake and glycolysis are **down-regulated when the cell is already
energy-rich** (an ADP/energy-demand term — the phosphofructokinase allosteric
feedback). This is what keeps glucose and pyruvate from piling up and lets the
network settle into a self-regulating steady state instead of running away.

## Grounding

Michaelis–Menten kinetics (1913) for every flux; exact conservation of the
ATP+ADP pool; mass balance on every reaction; chemical-Langevin noise
(Gillespie 2000) so it is non-deterministic. Rate constants are
normalised/illustrative, but the **structure** — independent compartments,
shared pools, MM kinetics, allosteric feedback, conservation — is the real thing.

## Validated by tests (`cell.test.ts`)

- Fed, it reaches **energetic homeostasis** (energy charge ≈ 0.8) with bounded
  glucose and pyruvate pools.
- **Every organelle's loop is active at once** (all fluxes > 0).
- Pyruvate flows through to the mitochondria (no pile-up); the Golgi **secretes
  protein** over time.
- The ATP + ADP pool is conserved exactly.
- Cut the nutrient → ATP collapses and the cell **dies**; feed it again → it
  **recovers**.
- Higher nutrient sustains a higher energy charge.

## In the viewer

The eukaryotic-cell scene now shows the network running:

- **each organelle pulses with its own activity and its own rhythm** —
  mitochondria with respiration, the nucleolus with transcription, the ER and
  ribosomes with translation, the Golgi with secretion, lysosomes with
  degradation, membrane transporters with import;
- the readout shows **glucose, ATP, protein, energy charge, status, nutrient**;
- the **membrane is tinted by health**; the **Nutrient slider** feeds or starves
  the whole network.

## Why this matters for the road ahead

This is the substrate for the project's real goal: many interacting cells, each
seeded with a different "character" (organelle counts, rate constants, defects),
where you can watch **which kinds of cells break**, how protein load changes
behaviour, what a cell takes in and how that changes it, and how it repairs
itself. A cell whose organelles each run their own coupled loop had to exist first.
