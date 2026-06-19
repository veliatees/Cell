# Milestone 024 - PhysiCell bridge

Status: implemented

M024 adds the first multicellular bridge. It does not vendor or run PhysiCell
C++ yet. Instead, it maps one Python engine cell state into a PhysiCell-like
agent phenotype and builds a microenvironment/population export that can support
100+ cells.

## What Was Added

- `engine/cell_engine/multicell/physicell_bridge.py`
  - `MicroenvironmentField`;
  - `CellAgent`;
  - `PhysiCellPopulation`;
  - single-cell state to agent phenotype mapping;
  - 100-cell population builder.

## Contract

- The bridge preserves an intracellular state reference.
- Agent phenotype includes viability, energy, stress and apoptosis pressure.
- Agent uptake/secretion maps intracellular state to microenvironment behavior.
- A 100-cell population export can be produced deterministically.

## Microenvironment Fields

- oxygen
- glucose
- amino acids
- xenobiotic
- waste
- bile signal

## Boundaries

- This is a Python-side bridge/export, not a compiled PhysiCell simulation.
- Cell mechanics, division and tissue physics remain outside this milestone.
- The interface is ready for a C++ PhysiCell project to consume.

## Verification

```bash
python -m unittest discover -s engine/tests -t engine
npm test -- --maxWorkers=1
npm run build
```

