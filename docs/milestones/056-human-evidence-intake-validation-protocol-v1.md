# Milestone 056 - Human Evidence Intake + Validation Protocol v1

This milestone prepares the engine to receive the requested Claude Science
delivery without allowing an external research summary to become biology merely
because it contains plausible numbers. It also turns the existing healthy-human
mixed-meal observations into a scale-matched validation protocol.

## Nine-File Evidence Contract

The repository contract at
`data/evidence_intake/phh_evidence_bundle_contract.v1.json` requires:

1. `koenig_model_provenance_audit.md`
2. `human_phh_scale_bridge.csv`
3. `human_phh_glucose_fluxes.csv`
4. `human_endocrine_signal_chain.csv`
5. `human_oxygen_redox_zonation.csv`
6. `heldout_validation_trajectories.csv`
7. `integration_contract.json`
8. `source_audit.md`
9. `unidentifiable_parameters.md`

The intake rejects missing files, empty audits, malformed CSV records, duplicate
record identifiers, prose embedded in numeric fields, non-finite values,
descending bounds, negative uncertainty, numeric values without units, malformed
DOIs and ambiguous missing tokens such as `N/A`, `unknown` or `TBD`. Missing
values must remain empty or `null`.

Model output may be retained as model output, but a row that labels model output
as a measurement is rejected. Human, rodent, immortalized-cell and other systems
may coexist in a delivery only when they remain explicitly separated.

## No Automatic Promotion

A structurally valid delivery receives the status
`structurally_valid_manual_review_required`. It still cannot:

- activate a parameter;
- enable an organ-to-cell scale bridge;
- enable endocrine or redox coupling;
- initialize the authoritative cell state;
- satisfy predictive release.

Every candidate must first be checked against the cited primary source and moved
into a separately versioned curated registry. Positive activation flags in the
external `integration_contract.json` are rejected.

The audit command is:

```bash
PYTHONPATH=engine python scripts/audit_phh_evidence_bundle.py \
  /path/to/delivery --out /path/to/audit.json
```

The output stores SHA-256 hashes for all nine delivered files so a reviewed
bundle cannot change silently.

## Human Mixed-Meal Validation Protocol

The existing Taylor et al. measurements are now represented as:

- 14 observed time points;
- 2 measured time windows;
- 3 reported summary parameters;
- 1 categorical hepatic-output constraint;
- 0 interpolated values;
- 0 mechanistic single-cell inputs.

There are 19 numeric observations in total. Study A liver-glycogen/pathway data
and Study B endocrine/hepatic-output data remain separate because the
participants were different. The same meal protocol is not treated as donor
matching.

The reported `380 +/- 28 min` hepatic-output return is represented as a cohort
summary of individual return times, not as a sample collected at minute 380.
Likewise, the reported complete suppression within 30 minutes stays categorical;
the engine does not assign an invented zero cellular flux.

## Comparison Semantics

A model prediction can be compared with an observation only when all of these
match exactly:

- observation identifier and quantity;
- unit;
- biological specimen or scale;
- point time, or both boundaries of a reported window.

The comparison reports absolute, relative and, when available, SEM-standardized
residuals. It does not call the result a pass or failure because no acceptance
threshold is inferred from the reported SEM.

## Browser And Release Gates

All 41 browser snapshots expose the protocol and evidence-intake status. The
browser reports the observation structure, the absence of interpolation and the
nine-file delivery state. Research preview remains available because pending
external evidence does not alter existing validated surfaces. Predictive release
remains blocked until delivery, primary-source review, curated promotion and the
already registered biological scale/coupling requirements are complete.

## Scientific Boundary

This milestone improves reproducibility and validation readiness; it does not add
a new measured intracellular value or unlock a new reaction rate. Biological
coverage therefore does not increase. The value is that the next evidence
delivery can be integrated without silent unit conversion, cross-species pooling,
model-output laundering or automatic parameter activation.

## Existing Primary Source

- Taylor et al., J Clin Invest 1996, DOI 10.1172/JCI118379:
  https://www.jci.org/articles/view/118379
