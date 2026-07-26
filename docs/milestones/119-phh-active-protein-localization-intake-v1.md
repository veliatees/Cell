# Milestone 119 - PHH active protein localization intake v1

## Problem

The existing seven-donor proteome reports total protein groups per nucleus.
Those values do not identify how many molecules are in the correct compartment
or membrane domain, how many are active, or how fast they function.

## Implemented

`phh_active_protein_localization_contract.v1.json` defines a strict 52-column
delivery format for BSEP, MRP2, NTCP, INSR, MET, EGFR, GLUT2, and glucokinase.

For the seven membrane proteins, one donor/replicate must link:

- total abundance;
- plasma-membrane abundance;
- membrane-domain abundance;
- active fraction;
- measured domain surface area;
- directly measured active copies or density;
- a dynamic same-sample functional readout;
- frozen independent validation.

For cytosolic glucokinase, domain area is replaced by measured aqueous cytosol
volume and active compartment concentration.

The loader preserves original denominators and rejects donor/study split
leakage. It requires an operational definition of an active molecule, polarity
state for membrane proteins, three or more ordered functional/validation time
points, and frozen held-out prediction identities.

## Authority Boundary

Structural completeness does not authorize active copies, active
concentrations, transporter flux, receptor activity, reaction-rate scaling, or
cell-state coupling. The current delivery count and every authorization count
remain zero.
