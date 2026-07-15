# Milestone 054 - Published Hepatic Glucose Shadow Model v1

This milestone adds an executable published glucose-metabolism model without
mistaking model output for measurement or silently allowing it to drive the
hepatocyte state.

## Biological Meaning

The Koenig, Bulik and Holzhutter model represents the liver's switch between
three broad behaviors as blood glucose changes:

- releasing versus taking up glucose;
- making glucose versus breaking glucose down;
- breaking glycogen down versus building glycogen.

It contains glycolysis, gluconeogenesis and glycogen metabolism across blood,
cytosolic and mitochondrial compartments. Insulin, glucagon and epinephrine are
represented by phenomenological glucose-response equations. A shared
phosphorylation fraction regulates GS, GP, PFK2, FBP2, PK and PDH.

These hormone values are model outputs, not measured portal concentrations.
The phosphorylation fraction is not receptor occupancy, AKT activity or
cAMP/PKA activity.

## Artifact Audit

The official PLOS Dataset S2 and the executable artifact are deliberately kept
separate.

| Property | Official PLOS Dataset S2 | Author executable re-encoding |
|---|---:|---:|
| SBML | Level 2 Version 4 | Level 3 Version 1 |
| Compartments | 5 | 5 |
| Species | 52 | 49 |
| Parameters | 0 | 258 |
| Reactions | 36 | 36 |
| Reactions with kinetic laws | 0 | 36 |
| Executed | No | Yes, as a shadow model |

The official supplement's SHA-256 is
`9dc142160a8c4c0179523c438baa6b8f6ba2edc27824a87910fa712ac16c4e6f`.
It contains reaction structure and extensive model notes but no SBML kinetic
laws. Treating it as an executable kinetic model would be incorrect.

The author-maintained re-encoding's SHA-256 is
`5091963c02f39cf00ae02b4fca9362af5f43544851f75b7e17768c7fc56835a3`.
It is pinned to `sbmlutils` commit
`ad15fdd0eb30e96cba1cdfef9286627eb6d4709c`; the model file itself was last
modified in commit `3cf02e91fc6355bdb9971b137454250751e6f808`.

## Reproduction Protocol

The executable model is run with libRoadRunner 2.9.2 and CVODE using:

- duration: `12,000 s` (`200 min`);
- relative tolerance: `1e-9`;
- absolute tolerance: `1e-9`;
- external lactate fixed explicitly at the current executable default of `1.2 mM`;
- glycogen fixed at `250 mM` for switch scans;
- 32 bisection iterations for each zero crossing.

This initial protocol combines the current executable's explicit lactate
default and 200-minute duration with the paper legend's literal `250 mM`
glycogen label. It must not be described as exact equivalence to the
publication-generation MATLAB protocol. Milestone 055 audits the model lineage
and the different conditions recovered from the later author repository. No
project-chosen biological fitting factor is introduced.

## Publication Benchmarks

Acceptance intervals come only from displayed reporting precision. For example,
`6.6 mM` maps to `[6.55, 6.65] mM`, and `94%` maps to `[93.5, 94.5]%`.

| Benchmark | Paper | Executable result | Pass |
|---|---:|---:|---:|
| Phosphorylation at 2 mM glucose | 94% | 94.0878% | Yes |
| Phosphorylation at 14 mM glucose | 5% | 5.0997% | Yes |
| Glucose production/utilization switch | 6.6 mM | 7.1437 mM | No |
| Gluconeogenesis/glycolysis switch | 8.5 mM | 8.3042 mM | No |
| Glycogenolysis/glycogenesis switch | 5.1 mM | 5.4340 mM | No |

The current reproduction result is therefore `2/5`, not validated equivalence.
The direct Python hormone equations and the executable SBML assignment rules
have numerical parity at the tested postabsorptive input, but this is only a
software implementation check.

Milestone 055 subsequently shows that a non-vendored legacy 2014 author model
reaches `5/5` under recovered repository conditions (`0.8 mM` lactate and the
actual `276.6667 mM` grid row selected by a trace labelled 250 mM). That result
does not change this vendored executable's `2/5` score and does not establish
exact official-publication equivalence.

## Profile Shadow Prediction

Only `postabsorptive` has a source-backed blood-glucose boundary in the current
PHH profiles. The model therefore runs only that profile:

- blood glucose input: `4.75 mM`;
- liver glycogen input: `229 mM`;
- simulation time: `200 min`;
- HGP output: `-10.0231 umol/kg body mass/min`;
- GNG output: `-6.8196 umol/kg body mass/min`;
- GLY output: `-3.2035 umol/kg body mass/min`.

In this executable model's sign convention, negative HGP denotes net glucose
production/export and positive HGP denotes uptake/utilization. These are
published-model predictions at organ/body-mass scale. They are not measured
single-cell fluxes and are not copied into the cell's quantitative state.

`fed_peak` and `prolonged_fasted` remain unavailable because the project does
not have a compatible source-backed static blood-glucose boundary for those
profiles. Missing inputs remain null rather than being guessed.

## Fail-Closed Gate

Authoritative coupling remains disabled because:

- all five publication benchmarks are not reproduced;
- the model represents mean liver/hepatocyte behavior, not a donor or zone;
- glucose-to-hormone behavior is phenomenological and instantaneous;
- energy and redox cofactors are fixed;
- oxygen limitation and hypoxia coupling are absent;
- outputs are per kilogram body mass, not per cell;
- the independent human glucagon-clamp glycogen response is not calibrated.

The browser exposes the official-versus-executable artifact audit, technical
parity, benchmark score, profile prediction and blocked cell-state coupling.

## Sources

- Koenig M, Bulik S, Holzhutter HG. PLoS Computational Biology 2012.
  https://doi.org/10.1371/journal.pcbi.1002577
- Official PLOS Dataset S2.
  https://journals.plos.org/ploscompbiol/article/file?type=supplementary&id=info:doi/10.1371/journal.pcbi.1002577.s002
- Author-maintained executable source.
  https://github.com/matthiaskoenig/sbmlutils
- libRoadRunner 2.9.2.
  https://github.com/sys-bio/roadrunner/releases/tag/2.9.2
