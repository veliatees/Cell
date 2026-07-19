# Milestone 086: Glucose Calibration and Held-Out Validation Gate v1

## Outcome

The glucose program now has an executable scientific firewall between
same-format comparison, parameter fitting, held-out validation and predictive
state activation.

All 36 active exploratory reactions receive an eligibility record. Twelve have
a related published-model candidate and three share source stoichiometry after
aliases, but zero reactions are eligible for fitting or parameter transfer.

## Why fitting remains blocked

The current PHH assay identifies one aggregate quantity: signed net medium
glucose disappearance. It does not separately identify transport influx,
transport efflux, glucokinase, G6PC, glycogen synthesis, glycogenolysis,
glycolysis, gluconeogenesis or pentose-phosphate flux.

Fitting many reaction constants to one aggregate endpoint would produce numbers
that look precise but are not biologically identifiable. The gate prevents that.

## Observation roles

- 12 non-overlapping windows are exact same-format comparison targets.
- Four 0-72 hour rows remain descriptive overlap audits.
- Zero rows may fit a reaction-specific kinetic parameter.
- Zero rows currently qualify as donor-held-out results.

An exact model submission can receive all 16 descriptive residuals. It receives
no aggregate score, acceptance threshold, pass/fail label or permission to drive
cell state.

## Requirements still open

Predictive activation requires all of the following:

1. a frozen exact-protocol model artifact;
2. donor-resolved numeric trajectories;
3. a donor-disjoint calibration/held-out split;
4. isotope and intracellular measurements that identify mechanisms;
5. window-specific volume and viable-cell normalization;
6. covariance plus a predeclared uncertainty model; and
7. an independent held-out human result evaluated without refitting.

The previously delivered `heldout_validation_trajectories.csv` does not satisfy
the final requirement because its numeric rows are model predictions and its
human comparator is null.

## Scientific boundary

This milestone activates zero biological parameters. Its contribution is a
testable guarantee that pooled validation data cannot silently become fitted
kinetics or a predictive claim.
