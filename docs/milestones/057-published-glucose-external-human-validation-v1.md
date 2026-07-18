# Milestone 057 - Published Glucose External Human Validation v1

This milestone asks a narrower and more useful question than publication
reproduction: how close is the currently vendored published-model prediction to
an external healthy-human hepatic glucose-output observation when both are
expressed on the same scale?

## Source-Backed Unit Conversion

Taylor et al. reported basal hepatic glucose output as
`1.90 +/- 0.04 mg glucose/kg body mass/min`. The Koenig shadow model reports HGP
in `umol glucose/kg body mass/min` and uses the opposite sign for production.

NIST Chemistry WebBook SRD 69 gives the molecular weight of glucose
(`C6H12O6`) as `180.1559 g/mol`. The conversion is therefore:

```text
umol glucose = mg glucose * 1000 / 180.1559
```

No fitted or project-selected conversion factor is used.

| Quantity | Original | Converted production magnitude |
|---|---:|---:|
| Healthy-human tracer estimate | 1.90 +/- 0.04 mg/kg/min | 10.5464 +/- 0.2220 umol/kg/min |
| Published-model shadow | -10.0231 umol/kg/min | 10.0231 umol/kg/min |

The model-minus-observation residual is `-0.5233 umol/kg/min`, or `-4.962%` of
the observed production magnitude. Dividing the residual by the reported cohort
SEM gives `-2.357`, but that number is descriptive only. SEM is not converted
into a validation tolerance or a pass/fail rule.

## Why This Is Not A Validation Pass

Only normalization basis and flux direction match after conversion. The full
protocol does not:

- the model output is the result of a 200-minute static-boundary simulation;
- the human value is a pre-meal tracer-derived baseline estimate;
- model glucose is 4.75 mM from a separate fasting reference, while Study B
  measured 5.0 +/- 0.1 mM peripheral glucose;
- model glycogen is 229 mM from another study; Study A reported
  207 +/- 22 mM and used different participants from Study B;
- model lactate is fixed at 1.2 mM, with no matched Study B lactate value;
- no donor matching exists;
- no audit establishes that the Taylor data were held out from development of
  the published model.

The comparison status is therefore
`contextual_external_comparison_no_validation_claim`. It has no acceptance
threshold, no pass flag and no authority over cell state or reaction rates.

## Blocked Validation Matrix

Four stronger targets are represented explicitly and remain null:

1. Mixed-meal hepatic-output time course at 60, 255 and recovery time.
2. Mixed-meal glycogen trajectory and synthesis rate.
3. Causal glucagon-clamp glycogen response.
4. Independently audited healthy-adult-PHH held-out trajectory.

The current model cannot run the causal clamp through its public interface
because glucagon is generated phenomenologically from glucose rather than
supplied as an independently manipulated input. Creating a synthetic glucagon
control would alter the model and is not done here.

## Evidence Correction

Hepatic glucose-output records are now labelled
`tracer_derived_cohort_mean_plus_minus_sem` and
`whole_liver_tracer_derived_estimate`. Plasma glucose, insulin and glucagon remain
measured plasma observations. Values are unchanged; only the evidence class is
made more precise.

## Browser And Release Gates

All 41 snapshots show:

- model production: 10.02 umol/kg/min;
- human tracer estimate: 10.55 +/- 0.22 umol/kg/min;
- residual: -0.52 umol/kg/min (-5.0%);
- exact protocol comparisons: 0;
- held-out results: 0;
- validation passes: 0;
- blocked targets: 4.

Research preview remains available. Predictive release now additionally requires
an exact-protocol external comparison and an independently audited held-out PHH
validation result.

## Scientific Boundary

This milestone improves quantitative validation depth but does not add a new
metabolic pathway or a validated single-cell rate. The approximately 5%
contextual residual is interesting, not proof of predictive validity.

## Sources

- NIST Chemistry WebBook SRD 69, Glucose:
  https://webbook.nist.gov/cgi/cbook.cgi?ID=C50997
- Taylor et al., J Clin Invest 1996, DOI 10.1172/JCI118379:
  https://www.jci.org/articles/view/118379
- Koenig et al., PLOS Computational Biology 2012, DOI
  10.1371/journal.pcbi.1002577:
  https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1002577
