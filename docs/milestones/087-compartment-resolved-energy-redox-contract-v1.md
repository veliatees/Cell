# Milestone 087 - Compartment-resolved energy and redox contract v1

## Goal

Replace the scientifically invalid idea of one well-mixed ATP/redox pool with a
source-supported hepatocyte compartment graph, without inventing organelle
volumes, concentrations, rates, or active protein fractions.

## Structural Result

The contract defines six explicit physical compartments:

- sinusoidal extracellular space;
- cytosol;
- mitochondrial intermembrane space;
- mitochondrial matrix;
- ER lumen;
- peroxisomal matrix.

It registers 38 distinct pools for oxygen, ATP/ADP/AMP/Pi, NAD(H), NADP(H),
GSH/GSSG, peroxide, superoxide, water and the mitochondrial proton-motive state.
Every initial value and compartment volume is `null`. Whole-liver values are not
split across organelles.

## Process Topology

Fourteen non-executable process systems now distinguish:

- respiratory-chain proton pumping from ATP-synthase coupling;
- VDAC outer-mitochondrial-membrane metabolite permeation;
- ANT/SLC25A4-A6 inner-membrane ADP/ATP exchange;
- SLC25A3 mitochondrial phosphate import;
- SLC35B1/AXER ER nucleotide exchange;
- SLC25A39 mitochondrial glutathione import;
- reducing-equivalent shuttling rather than direct NADH transport;
- cytosolic and mitochondrial NADPH generation;
- cytosolic, mitochondrial, ER and peroxisomal antioxidant systems.

No exact process stoichiometry, P/O value, permeability, Vmax, Km, flux or
initial concentration is activated by this topology.

## Human PHH Protein Bridge

The seven-donor absolute PHH proteome is queried dynamically for every mediator
gene. The result covers 31 genes; 27 have one or more quantified protein groups.
Distinct groups and all donor A-G values are preserved rather than summed.

Non-quantification of SLC25A39, SLC35B1, ERO1A or ERO1B in this source is
represented as `not quantified`, never as biological absence. Total copies per
nucleus may support protein presence only; they cannot identify localization,
active fraction, complex assembly, concentration or flux.

## Aggregate Observation Boundary

Seven human-liver observations are retained with their original units and assay
semantics: ATP, ADP, AMP, energy charge, NAD+, total glutathione and apparent
Pi-to-ATP exchange. None may initialize a compartment or fit a kinetic
parameter. The apparent exchange observation is reserved for a future exact
same-assay comparison only.

## Detected Legacy Conflicts

The contract machine-detects six unresolved runtime conflicts:

1. adenylate compartment collapse;
2. NAD(H) compartment collapse;
3. apparent exchange miscast as first-order turnover;
4. placeholder glutathione/ROS kinetics;
5. placeholder TCA/OXPHOS kinetics;
6. omitted ER-lumen and peroxisomal redox state.

These detections are release invariants. A silent promotion or disappearance
causes validation to fail.

## Primary Evidence

- Human ANT exchange mechanism: DOI `10.15252/embr.202357127`.
- VDAC ATP/ADP pathway: DOI `10.1021/bi4011495`.
- Human SLC25A3 phosphate transport: DOI `10.1086/511788`.
- Mitochondrial GSH import through SLC25A39: DOI
  `10.1038/s41586-021-04025-w`.
- ER ATP import through SLC35B1/AXER: DOI `10.7554/eLife.49682`.
- Compartmental NADPH tracing: DOI `10.1016/j.molcel.2014.05.008`.
- Oxidized ER glutathione state: PMID `1523409`.
- PHH oxygen-consumption observability: PMCID `PMC8822303`.
- Seven-donor PHH absolute proteome: DOI `10.1016/j.jprot.2016.01.016`.

## Scientific Effect

This milestone increases mechanistic structure and prevents cross-compartment
category errors. It does not increase the number of calibrated kinetic
parameters and makes no predictive energy/redox claim.
