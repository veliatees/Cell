# Milestone 083 - Published reaction kinetic-transfer audit v1

## Goal

Determine exactly which parameters from a published human hepatic-glucose model
can be transferred into the active integrated hepatocyte network without
conflating a shared enzyme name with an equivalent kinetic equation.

## Evidence

The audit uses the Koenig et al. human hepatic-glucose model, its official
[primary paper](https://doi.org/10.1371/journal.pcbi.1002577), official
[Text S2 kinetic supplement](https://doi.org/10.1371/journal.pcbi.1002577.s013),
and the pinned author-maintained executable SBML already vendored by the
project.

The publication describes a 49-metabolite, 36-reaction model. Its kinetic
constants are assembled from literature, while reaction capacities are fitted
within the complete model. Reported flux outputs use a per-kilogram body-mass
scale. These are valid properties of that model; they are not direct
single-hepatocyte measurements.

## Equation fingerprints

The generic SBML inspection layer now extracts, for every reaction:

- reactants, products, coefficients, direction, and compartment;
- boundary-condition status for each participant;
- modifier species;
- all species and parameter symbols referenced by the kinetic law;
- a SHA-256 digest of canonicalized MathML.

The digest is an exact artifact-integrity check. It does not claim that two
algebraically equivalent expressions must have the same string-level hash.

## Exhaustive mapping

`data/published_models/koenig2012_reaction_transfer_manifest.json` covers every
active reaction exactly once. Runtime validation rejects missing, duplicated,
unexpected, or unknown reaction IDs and rejects a stale source-model checksum.

Current result:

- active integrated reactions: `36`;
- reactions with one or more related published candidates: `12`;
- outside the glucose model's scope: `24`;
- exact stoichiometry after explicit species aliases: `3`;
- exact symbolic-rate-law matches: `0`;
- validated per-cell unit bridges: `0`;
- matched healthy-PHH experimental contexts: `0`;
- activated published parameter transfers: `0`.

The three topology matches are:

- `glucose_export` against reverse `GLUT2`;
- `phosphoglucose_isomerase_reverse` against reverse `GPI`;
- `hepatic_glucose_output` against reverse `GLUT2`.

These are not kinetic matches. The active channels do not reproduce the full
published reversible laws, membrane/compartment semantics, per-cell scale, and
validation context.

## Why no Vmax was copied

Several active reactions are simplified or lumped. Examples include free
glucose-to-glycogen instead of UDP-glucose chemistry, one event replacing six
lower-glycolysis reactions, ATP/ADP standing in for PEPCK's GTP/GDP chemistry,
and mitochondrial pyruvate carboxylase without its complete substrates,
products, compartment, and activation terms.

Assigning one published `Vmax` to those channels would create a numerically
precise but chemically different model. The transfer guard therefore requires
all of the following before activation:

1. exact stoichiometry and direction;
2. exact compartment semantics;
3. an equivalent symbolic kinetic law;
4. a validated conversion to molecules per second per hepatocyte;
5. matched healthy-PHH biological and experimental context;
6. independent held-out validation for predictive use.

`assert_kinetic_transfer_allowed()` raises `KineticTransferError` while any gate
is open.

## Browser and snapshots

All 41 committed snapshots expose the same audit. The scientific evidence panel
shows candidate coverage, topology matches, equation matches, unit/context
readiness, and activated transfers as separate quantities. The compact engine
diagnostic reports `12/36 candidates`, `3 topology matches`, and `0 activated`.

## Scientific effect

This milestone adds no biological rate and therefore does not increase the
whole-hepatocyte completeness estimate. It converts the next calibration task
from an informal search into an exact reaction-by-reaction acquisition plan and
prevents a published whole-model fit from being mislabeled as direct PHH
kinetics.

## Verification

- exact executable-model checksum and 36/36 kinetic-law coverage;
- regression hashes for selected published MathML equations;
- exact 36-reaction manifest coverage;
- exact candidate, scope, and topology-match counts;
- explicit lumped-versus-out-of-scope classifications;
- fail-closed activation error for a topology-only match;
- scientific-release integration;
- Python and TypeScript suites, production build, snapshot matrix, and browser
  inspection.
