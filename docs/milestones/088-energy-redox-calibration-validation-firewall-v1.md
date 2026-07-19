# Milestone 088 - Energy/redox calibration and validation firewall v1

## Goal

Make it impossible for legacy ATP, glutathione or OXPHOS software-fixture values
to appear as measured healthy-PHH kinetics, fitted parameters or predictive
validation.

## Corrected Authority

Nine executable legacy reactions are audited:

- 2 matched ATP-turnover fixture reactions;
- 4 glutathione/ROS fixture reactions;
- 3 TCA/OXPHOS fixture reactions.

All nine have complete parameter metadata, and all nine are classified
`placeholder`. Zero are fit-eligible, quantitatively valid, predictively
executable or automatically coupled to the authoritative cell state.

The integrated 36-reaction fuel network therefore reports:

- `0` source-backed numerical parameterizations;
- `2` placeholder parameterizations;
- `34` unparameterized reactions;
- `36` reactions blocked from quantitative validation.

The earlier `2 / 36` claim was caused by using a real 31P-MRS apparent-exchange
observation as provenance for two unmeasured first-order constants.

## Observation-use Audit

All seven energy/redox aggregate observations may remain denominator-preserved
references. Only apparent Pi-to-ATP exchange has a future same-assay comparison
role. None may:

- seed cytosolic or organelle concentrations;
- fit a reaction-specific parameter;
- count as a donor-held-out result;
- activate cell-state coupling.

## Activation Requirements

Numerical activation remains blocked until all nine requirements pass:

1. matched healthy-human PHH biological and experimental context;
2. measured or qualified compartment volumes;
3. compartment-resolved initial states with uncertainty;
4. denominator-matched OCR and ATP-linked-respiration trajectories;
5. compartment-targeted redox or isotope trajectories;
6. localized active protein abundance and complex assembly;
7. mechanism-identifying perturbations;
8. donor-disjoint calibration and held-out partition;
9. a frozen prediction artifact, measurement operator, uncertainty rule and
   independent held-out result.

Every requirement is currently false and visible in the snapshot.

## Retired Validation Claim

The former stochastic validation harness reported ATP, ATP:ADP, energy charge
and GSH:GSSG fixture outputs inside broad ranges as `100% accuracy`. Those checks
were not independent and mixed shared-pool model outputs with unmatched tissue
or generic ranges. They have been removed from the biological scorecard.

The remaining glucokinase S0.5 check verifies that the implemented equation
reproduces its own sourced parameter. The report labels it a software
consistency check and permits zero independent biological-validation claims.

## Snapshot and Browser

The exported snapshot includes the complete structural contract and gate. The
evidence panel reports compartment, pool, process and PHH-proteome coverage,
legacy conflicts, placeholder reactions, fit eligibility, held-out results and
activated parameter counts. This surface reports scientific authority; it does
not alter the rendered cell's organelle animation or claim visible molecular
resolution.

## Verification

- exact compartment/pool/process registry checks;
- double-membrane VDAC/ANT/phosphate topology checks;
- donor-column and distinct-protein-group preservation;
- original-unit aggregate observation checks;
- all nine placeholder reaction classifications;
- fail-closed fit and predictive-activation guards;
- research-preview and predictive-release regression tests;
- snapshot, TypeScript summary, production build and browser inspection.
