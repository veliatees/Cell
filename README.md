# Cell

A research-first, source-grounded simulation of a **hepatocyte (liver cell)**,
built the way the whole-cell modelling field builds them: a stochastic, real-units
biochemical engine, validated against measured data, with an interactive 3-D scene
on top.

The project began as a bottom-up "atom → molecule → membrane → cell" experiment.
That proved computationally unrealistic on consumer hardware (as it is for every
serious effort), so the work pivoted to the **cell scale** — exactly where E-Cell,
Virtual Cell, the Karr/JCVI whole-cell models, and HEPATOKIN1 operate. The old
molecular-scale pieces remain as background/zoom-in scenes, not the focus.

## What It Is Now

A running, hepatocyte-scale **stochastic kinetic cell**, in real units, with a
first layer of validation against measured biology.

The Python engine (`engine/cell_engine`) now contains:

- **Real units** — concentrations and molecule counts tied to a grounded
  hepatocyte volume (M030).
- **A stochastic reaction core** — exact Gillespie SSA for low-copy species and
  the chemical Langevin equation (SDE) for high-copy species, verified against
  analytic results (M031).
- **Real pathways** — full glycolysis with literature enzyme kinetics, the urea
  cycle, and the glutathione/NADPH redox couple, each with exact conservation
  laws (M033, M038).
- **Central dogma** — stochastic gene → mRNA → protein expression that reproduces
  translational bursting (M034).
- **A unified whole cell** — all of the above composed into one network that grows,
  expresses genes, runs its urea cycle, divides (partitioning real molecule
  counts), and can be pushed into uncontrolled (cancer-like) proliferation
  (M036, M039).
- **Validation** — emergent outputs checked against measured hepatocyte values
  (energy charge, ATP, ATP:ADP, glucokinase glucose sensing, GSH:GSSG); currently
  **5/5 targets within the measured physiological range** (M037, M038).
- **Spatial reaction–diffusion** — a first non-well-mixed layer reproducing the
  analytic morphogen gradient `λ = √(D/k)` (M040).

The browser scene (TypeScript + Three.js) renders a polarized hepatocyte with a
**fenestrated sinusoidal endothelium** (sieve-plate pores, LSEC nuclei), a
canalicular bile groove, true-size membrane protein footprints, and blood-side
cargo crossing the endothelium through many fenestrae.

This is **not** a predictive digital twin. It is an early-stage, source-grounded
model: the architecture is now field-aligned and a few behaviours are validated,
but coverage is still a small fraction of a real hepatocyte and most rate
constants are still provisional. See the honest accounting under "Status" below.

## Run The Prototype

```bash
npm install
npm run dev
```

Then open the local URL printed by Vite. The app starts on the **hepatocyte
organelle scene**: a whole cell with nucleus, mitochondria, ER, Golgi,
lysosome/endosome, peroxisome, ribosomes, glycogen granules, plasma-membrane
transport proteins, a sinusoidal blood-facing vessel, and a canalicular bile
groove.

Below it, **legacy zoom-in scenes** from the original molecular-scale phase are
kept as background: the lipid vesicle, ion, water (SPC/E), solvation, diffusion,
membrane, and chemistry building blocks. These are no longer the project's focus —
the science now lives in the cell-scale stochastic engine — but they remain
source-grounded and are useful for intuition. See
[docs/06-one-reality.md](docs/06-one-reality.md) and
[docs/sources.md](docs/sources.md).

## Verify

```bash
npm test
npm run build
python -m unittest discover -s engine/tests -t engine
```

To print the validation scorecard (model vs measured hepatocyte data):

```bash
PYTHONPATH=engine python -c "from cell_engine.stochastic.validation import run_validation, format_report; print(format_report(run_validation()))"
```

> The engine targets Python 3.11+ (it uses `datetime.UTC`).

## Current Target Cell Type

The current target is **hepatocyte-first**, not a generic animal cell. The engine
roadmap is now organized around hepatocyte metabolism, detox, secretion,
sinusoidal/canalicular polarity, bile handling, urea-cycle coupling, and
state-conditioned organelle failure. See
[docs/07-integrated-cell-engine-roadmap.md](docs/07-integrated-cell-engine-roadmap.md).

Current browser features include:

- sinusoidal/basolateral import and canalicular/apical export context;
- true-size embedded plasma-membrane protein footprints with a 1:1 zoom-density
  patch and whole-surface LOD;
- stochastic cargo packets instead of fixed intracellular tracks;
- live hepatocyte activity, organelle health, fault risk, cargo fidelity and
  event log panels;
- explicit visual time-scale disclosure so the accelerated scene is not confused
  with real-time microscopy.

## Status — honest accounting

What is real now: the engine does the *right kind* of thing the field does
(hybrid stochastic kinetics in real units), and a handful of behaviours are
**validated** against measured hepatocyte data (5/5 targets in range). The full
test suite covers the stochastic core, every pathway's conservation laws, gene
expression statistics, the whole-cell run, and the spatial solver.

What is still missing (the road ahead is depth, not a new approach):

- most rate constants are still provisional placeholders, not curated per-enzyme
  literature kinetics (HEPATOKIN1-level coverage is hundreds of grounded reactions);
- coverage is a small fraction of a hepatocyte — lipid metabolism, the pentose
  phosphate pathway, signalling, and ion/calcium electrophysiology are not yet in;
- the spatial layer is 1-D and deterministic (not 3-D stochastic RDME), and is not
  yet wired into the whole-cell network;
- volume dynamics at division, real cell-cycle checkpoint circuitry (CDK/cyclin/p53),
  and organelle-resolved geometry are not modelled;
- no host–pathogen (virus/bacteria) coupling or multicellular tissue yet;
- validation is 5 checkpoints, not a broad comparison against omics/perturbation data.

The earlier epithelial notes (inside vs outside; apical vs basolateral;
transcellular/paracellular transport; tight/adherens junctions, desmosomes, basal
lamina) remain useful background for polarity and barrier thinking.

## Documentation Map

- [Project charter](docs/00-project-charter.md)
- [Research index](docs/01-research-index.md)
- [Multiscale architecture](docs/02-multiscale-architecture.md)
- [Platform recommendation](docs/03-platform-recommendation.md)
- [Integrated cell engine roadmap](docs/07-integrated-cell-engine-roadmap.md)
- [Atomic foundations](docs/research/physics/atomic-foundations.md)
- [Epithelial cell starting scope](docs/research/biology/epithelial-cell.md)
- [Input/output registry](docs/research/biology/input-output-registry.md)
- [Milestone 001: two-ion formation](docs/milestones/001-two-ion-formation.md)
- [Milestone 002: many-ion system](docs/milestones/002-many-ion-system.md)
- [Milestone 003: real water (SPC/E)](docs/milestones/003-water-model.md)
- [Milestone 004: solvation (ions in water)](docs/milestones/004-solvation.md)
- [Milestone 005: diffusion & Brownian motion](docs/milestones/005-diffusion.md)
- [Milestone 006: lipid membrane](docs/milestones/006-lipid-membrane.md)
- [Milestone 007: membrane transport](docs/milestones/007-membrane-transport.md)
- [Milestone 008: the closed cell (vesicle)](docs/milestones/008-closed-cell.md)
- [Milestone 009: chemistry (reaction–diffusion)](docs/milestones/009-chemistry.md)
- [Milestone 010: the eukaryotic cell (organelles)](docs/milestones/010-eukaryotic-cell.md)
- [Milestone 011: the living cell (metabolism)](docs/milestones/011-living-cell.md)
- [Milestone 012: the organelle network (parallel loops)](docs/milestones/012-organelle-network.md)
- [Milestone 013: the imperfect, spatial cell (own loops, transport, faults, live report)](docs/milestones/013-imperfect-spatial-cell.md)
- [Milestone 015: Python engine skeleton](docs/milestones/015-python-engine-skeleton.md)
- [Milestone 016: Organelle module interface](docs/milestones/016-organelle-module-interface.md)
- [Milestone 017: Cargo routing engine](docs/milestones/017-cargo-routing-engine.md)
- [Milestone 018: Hepatocyte metabolism v1](docs/milestones/018-hepatocyte-metabolism-v1.md)
- [Milestone 019: SBML/libRoadRunner bridge](docs/milestones/019-sbml-roadrunner-bridge.md)
- [Milestone 020: Rule-based signaling](docs/milestones/020-rule-based-signaling.md)
- [Milestone 021: Brian2 membrane/Ca module](docs/milestones/021-brian2-membrane-calcium.md)
- [Milestone 022: TS external snapshot mode](docs/milestones/022-ts-external-snapshot-mode.md)
- [Milestone 023: Validation harness](docs/milestones/023-validation-harness.md)
- [Milestone 024: PhysiCell bridge](docs/milestones/024-physicell-bridge.md)
- [Milestone 025: ML calibration and policy environment](docs/milestones/025-ml-calibration-policy-env.md)
- [Milestone 026: Organelle functional cycles](docs/milestones/026-organelle-functional-cycles.md)
- [Milestone 027: Engine-driven visual bridge](docs/milestones/027-engine-driven-visual-bridge.md)
- [Milestone 028: Visual time-scale disclosure](docs/milestones/028-visual-time-scale.md)
- [Milestone 029: Membrane protein visual reality](docs/milestones/029-membrane-protein-visual-reality.md)
- [Milestone 030: Real-units / copy-number foundation](docs/milestones/030-real-units-foundation.md)
- [Milestone 031: Stochastic reaction core (SSA + CLE)](docs/milestones/031-stochastic-reaction-core.md)
- [Milestone 032: Binding real units into a running cell model](docs/milestones/032-real-units-engine-binding.md)
- [Milestone 033: Full glycolysis with real per-enzyme kinetics](docs/milestones/033-glycolysis-real-kinetics.md)
- [Milestone 034: Central dogma (gene → mRNA → protein)](docs/milestones/034-central-dogma.md)
- [Milestone 035: Scaling scope by integration (expression-coupled metabolism)](docs/milestones/035-expression-coupled-scope.md)
- [Milestone 036: Cell states, growth, division, and cancer](docs/milestones/036-cell-cycle-division-cancer.md)
- [Milestone 037: Validation against measured hepatocyte data](docs/milestones/037-validation-against-measured-data.md)
- [Milestone 038: Coverage — urea cycle + glutathione redox](docs/milestones/038-coverage-urea-redox.md)
- [Milestone 039: Integration — the unified whole cell](docs/milestones/039-whole-cell-integration.md)
- [Milestone 040: Spatial reaction–diffusion](docs/milestones/040-spatial-reaction-diffusion.md)
- [One reality — coarse but grounded](docs/06-one-reality.md)
- [Roadmap (what's next)](docs/05-roadmap.md)
- [Source ledger](docs/sources.md)

## Project Rule

Every simulated object should eventually have:

- a source-backed description
- a scale and unit system
- inputs and outputs
- relations to existing objects
- equations or rules of motion when known
- visual representation and hidden state representation
- confidence level and assumptions
