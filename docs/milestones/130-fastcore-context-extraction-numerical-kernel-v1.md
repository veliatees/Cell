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
  <https://github.com/opencobra/cobratoolbox/tree/master/src/dataIntegration/transcriptomics/FASTCORE>.

FASTCORE receives a flux-consistent network and a set of reactions supported by
strong context evidence. It builds a compact, flux-consistent subnetwork that
retains the core and adds only the reactions needed to support it.

## Implemented

- LP-7 approximate flux-cardinality maximization.
- LP-10 L1 penalty minimization outside the core.
- Forward and reverse handling without splitting reversible reactions.
- Reverse-only reaction normalization.
- Global input and extracted-output flux-consistency audits.
- Mandatory, explicit epsilon and LP10 scaling inputs with no runtime defaults.
- Fail-closed rejection of blocked input reactions, missing core IDs and invalid
  numerical controls.
- Explicit reporting that the greedy extraction need not be unique.

## Synthetic Verification

With `A_to_B` as the only core reaction, the analytic fixture retains
`A_in`, `A_to_B` and `B_out`, while omitting an independent `X` pathway. A
blocked-reaction fixture is rejected and a reversible core remains intact.

## Scientific Boundary

Human-GEM has not been context-extracted. No healthy-PHH core reaction set,
donor omics bundle or biological flux authority is present. Future FASTCORE
output will be a computational model hypothesis and will still require measured
exchange bounds, an explicit objective, uncertainty analysis and independent
validation.
