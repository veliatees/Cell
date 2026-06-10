# Project Charter

## Goal

Create an interactive 3D research environment for exploring human biology from
physical foundations. The long-term target is not only visual beauty, but a
source-backed model where atoms, molecules, membranes, organelles, cells,
tissues, and organs exchange matter, energy, force, and information.

## Core Principle

No object is just decoration. If something appears in the world, the project
should know what it is, what it can interact with, what it consumes, what it
produces, and which model layer owns its behavior.

## Reality Boundary

The project should be honest about scale:

- Quantum behavior is required for atomic correctness, but full live quantum
  many-body simulation is not practical for an interactive cell or organ.
- Molecular dynamics is useful for small regions, but not for every molecule in
  a cell at all times.
- Cell and organ behavior requires coarse-grained, statistical, agent-based,
  ODE/PDE, or rule-based models.

The correct approach is multiscale coupling: detailed models are used where
they matter, and compressed models preserve the important inputs and outputs at
larger scales.

## Initial Scope

1. Atomic and ionic foundations.
2. Real-time interaction of two oppositely charged ions.
3. Molecule formation and bond representation.
4. Lipid membrane patch.
5. Epithelial cell surface with apical/basolateral polarity.
6. Transport, energy, signaling, and waste exchange.

## Research Method

Each research file should separate:

- known facts
- equations
- model decisions
- approximations
- unknowns
- source links
- implementation notes

## Hardware Constraint

Initial development targets an Apple Silicon M1 Mac. That strongly favors a
lightweight, incremental simulation architecture with GPU acceleration where
available and aggressive level-of-detail controls.
