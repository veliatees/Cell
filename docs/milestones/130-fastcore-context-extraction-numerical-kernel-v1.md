# Milestone 130: FASTCORE context-extraction numerical kernel v1

## Purpose

Prepare a source-defined route from a generic flux-consistent reconstruction to
a compact context-specific network without inventing transcript thresholds or
pretending that omics abundance is flux.

## Method

The kernel follows the LP-7, LP-10 and greedy extraction loop published by
Vlassis, Pacheco and Sauter:

- primary paper:
  <https://doi.org/10.1371/journal.pcbi.1003424>;
- official COBRA Toolbox implementation:
  <https://github.com/opencobra/cobratoolbox/tree/67c790dbac809d9d891fdbafc33e18c21fc9bddc/src/dataIntegration/transcriptomics/FASTCORE>.

FASTCORE receives a flux-consistent network and a set of reactions supported by
strong context evidence. It builds a compact, flux-consistent subnetwork that
retains the core and adds only the reactions needed to support it.

## Implemented

- LP-7 approximate flux-cardinality maximization.
- LP-10 L1 penalty minimization outside the core.
- Forward and reverse handling without splitting reversible reactions.
- Reverse-only reaction normalization.
- Restoration of original stoichiometry and bounds in extracted output.
- Global input and extracted-output flux-consistency audits.
- Identity- and epsilon-bound input consistency certificates.
- Mandatory, explicit epsilon and fixed LP-10 scale with no biological default.
- Pinned official fixed LP-10 scaling factor `1e4`.
- Pinned official adaptive LP-10 branch using ten times the minimum preceding
  LP-7 core flux, with counted fallback to the fixed branch.
- A diagnostic extraction API that returns blocked output identities without
  promoting the candidate; the accepting API still raises on inconsistency.
- Fail-closed rejection of blocked input reactions, missing core IDs and invalid
  numerical controls.
- Explicit reporting that the greedy extraction need not be unique.

## Synthetic Verification

With `A_to_B` as the only core reaction, the analytic fixture retains
`A_in`, `A_to_B` and `B_out`, while omitting an independent `X` pathway. A
blocked-reaction fixture is rejected and a reversible core remains intact.

## Scientific Boundary

A real fixed-scaling Human-GEM trial is reported in Milestone 137 and the
fixed/adaptive comparison in Milestone 139. Adaptive scaling reduced the
strict blocked set from `408` to `17` but did not eliminate it; the earlier
conservative closure retained nearly the entire generic network, so no PHH
context model was accepted. Any future
accepted output will remain a computational model hypothesis requiring measured
exchange bounds, an explicit objective, uncertainty analysis and independent
validation.
