# Milestone 175 — Four-cycle metabolic authority graph v1

## Outcome

The four proposed metabolic workstreams are now one machine-checked dependency
program rather than four disconnected implementation lists:

1. hepatic glucose, glycolysis/gluconeogenesis and glycogen control;
2. CYP450, glutathione/redox and APAP injury;
3. polarized membrane transport and bile flux; and
4. urea-cycle ammonia clearance with Human-GEM dynamic FBA.

Each cycle has cumulative gates for quantitative execution, prediction and
authoritative runtime coupling. Five cross-cycle edges additionally require an
explicit compartment map, unit/scale operator, time-alignment operator,
donor/context match, transfer or conservation law and uncertainty propagation.
A shared species name is recorded as an identity declaration only; it cannot
couple two numerical states.

The graph is an authority surface. It contains no kinetic parameter, performs
no fit and activates no biological runtime behavior.

## Current machine-derived state

| Program surface | Current result |
|---|---:|
| Declared cycles | 4 |
| Cycles with at least one real structural/observational surface | 4 |
| Cycle gates | 38 |
| Currently satisfied gates | 7 |
| Quantitatively executable cycles | 0 |
| Predictive cycles | 0 |
| Runtime-coupled cycles | 0 |
| Declared cross-cycle edges | 5 |
| Edge operators | 35 |
| Coupled edges | 0 |

This is not a statement that the biology has failed. It distinguishes useful
implemented structure from evidence sufficient to assign biological rates.

## Cycle audit

### 1. Glucose and glycogen

The source and active networks each expose 36 reactions and 12 candidate
relationships. Only three candidates currently have exact stoichiometry, none
has an exact symbolic kinetic-law match, none has an accepted single-cell unit
bridge and no reaction is fit-eligible. Existing PHH medium-glucose targets are
therefore descriptive validation surfaces, not reaction-specific calibration.

### 2. CYP/APAP/redox injury

The exploratory APAP fixture contains the competing safe-conjugation,
CYP-to-NAPQI, GSH-conjugation and protein-adduct/ROS branches. The PHH CYP assay
surface and 38-pool compartmental energy/redox topology are present. No complete
donor trajectory, calibrated CYP/redox kinetic chain, validated
mitochondrial-permeability-transition injury law or independent prediction is
available, so the fixture has no quantitative or cell-state authority.

### 3. Polarized transport and bile flux

BSEP and MRP2 have total-per-nucleus observations. The target program also
requires NTCP, GLUT2, OATP1B1 and OATP1B3. No target currently has an accepted
active local surface density. Aggregate biliary excretion and sandwich-culture
bile-acid endpoints do not identify transporter-specific rates, true
canalicular gradients or ATP work. Total copies therefore cannot become flux.

### 4. Urea cycle and Human-GEM

The five-enzyme urea-cycle topology is explicit, but its executable rates are
placeholder or lumped values. Human-GEM v2.0.0 identity, sparse loading and five
generic solver fixtures pass. A healthy-PHH context model, measured exchange
bounds, measured objective, single-cell scale operator, independent flux
validation and dynamic boundary-update law are absent. A successful generic
FBA solve therefore remains a software/structural result, not PHH dFBA.

## Cross-cycle interfaces

The program declares five intended causal interfaces:

- GLUT2-mediated sinusoid/cytosol glucose exchange;
- glucose/energy/redox coupling into APAP defence;
- APAP conjugate export through the polarized biliary surface;
- glucose/urea energy and carbon coupling; and
- ammonia/urea exchange at the sinusoidal system boundary.

All five currently preserve state identity only. None has the complete seven-
operator contract required for numerical coupling.

Each cycle also reads the hash-bound independent-review registry directly.
Structurally valid external tables or bundles therefore receive no cycle-level
scientific credit until an independent review is bound to their exact delivery,
contract and review-artifact hashes.

## Implemented surfaces

- `data/validation/hepatocyte_metabolic_cycle_program.v1.json` defines the
  versioned four-cycle graph and its cumulative gate identities.
- `engine/cell_engine/validation/metabolic_cycle_program.py` derives every gate
  from existing snapshots and reaction fixtures, validates graph invariants and
  exposes fail-closed execution assertions.
- Validation re-derives every gate and edge operator from the current evidence
  surfaces; an internally consistent but altered snapshot is rejected.
- `assert_metabolic_cycle_execution_allowed` rejects quantitative, predictive
  and runtime activation while any required gate is false.
- `assert_metabolic_edge_coupling_allowed` rejects name-only cross-cycle state
  sharing.
- The canonical engine snapshot, TypeScript snapshot summary and completion
  matrix expose the exact current graph without enabling it.

## Remaining boundary

The next quantitative progress must arrive through source-correct, independently
reviewed evidence: donor-resolved trajectories, exact equations, compartment
and unit mappings, single-cell scale operators, identifiable perturbations and
frozen held-out validation. New evidence can change individual gate inputs, but
the program version must be reviewed before any execution count can become
nonzero.
