# Milestone 155 - Legacy calibration authority firewall v1

## Problem

The early ML scaffold compared the schematic whole-cell runtime against three
project-defined relative targets for ATP, ROS and energy stress. It returned a
generic `fit_score`, even though the targets explicitly described themselves as
placeholders and the runtime is not calibrated to matched primary human
hepatocyte measurements.

That behavior was useful for deterministic software tests and exploratory
candidate ordering, but the API did not make the scientific boundary hard
enough. A fixture score could be mistaken for biological parameter fitting,
quantitative validation or predictive model selection.

## Implemented boundary

- `evaluate_calibration` now requires an explicit execution purpose.
- `rank_calibration_candidates` accepts only
  `exploratory_candidate_ranking`.
- Software-fixture evaluation and exploratory ranking remain available.
- Biological parameter calibration, quantitative validation and predictive
  model selection raise `LegacyCalibrationAuthorityError`.
- The former generic `fit_score` is now `fixture_fit_score`.
- Every calibration result reports its execution purpose, fixture-only score
  authority and three false scientific-use permissions.
- Each built-in target declares
  `evidence_authority = schematic_project_fixture`.
- The authority contract lives in an import-independent module, so release and
  completion gates cannot create a circular dependency through the validation
  package.
- Scenario and ML-policy wrappers propagate an explicit exploratory runtime
  purpose instead of hiding the whole-cell execution context.
- The engine snapshot, completion matrix, release gate, model audit and browser
  evidence panel expose the firewall and its zero-authority counts.

## Current audited inventory

| Item | Count |
| --- | ---: |
| Audited workflows | 3 |
| Built-in fixture targets | 3 |
| Placeholder targets | 3 |
| Source-backed targets | 0 |
| Biologically authorized targets | 0 |
| Scientific-authority purposes allowed | 0 |

## Scientific interpretation

The three relative targets remain available only to exercise deterministic
software behavior. Their residuals and fixture-fit scores:

- are not estimates of healthy-PHH concentrations or stress states;
- do not calibrate any biological parameter;
- do not validate the hepatocyte model;
- do not select a predictive model;
- do not mutate authoritative cell rules.

No biological value, kinetic law, threshold or uncertainty was added in this
milestone.

## Requirements for future quantitative calibration

A separate quantitative workflow must use source-reviewed measurements with
matched donor, cell system, compartment, assay, unit, denominator, exposure and
time context. Model and measurement operators must be frozen before
donor-disjoint and study-disjoint held-out evaluation. The legacy relative-pool
runner cannot gain that authority merely by replacing its fixture targets.
