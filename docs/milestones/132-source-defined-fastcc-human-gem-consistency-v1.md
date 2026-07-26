# Milestone 132: Source-defined FASTCC Human-GEM consistency v2

## Purpose

Determine which reactions in the exact pinned generic Human-GEM v2.0.0
reconstruction can carry nonzero steady-state flux in at least one feasible
mode, without confusing generic feasibility with healthy-hepatocyte activity.

## Method

The implementation follows the FASTCC procedure defined by Vlassis, Pacheco
and Sauter:

- primary paper:
  <https://doi.org/10.1371/journal.pcbi.1003424>;
- official COBRA Toolbox reference implementation:
  <https://github.com/opencobra/cobratoolbox/blob/67c790dbac809d9d891fdbafc33e18c21fc9bddc/src/dataIntegration/transcriptomics/FASTCORE/fastcc.m>.

An iterative sign-definite dead-end prepass removes only reactions that are
provably blocked because a metabolite lacks a distinct producer or consumer.
The remaining network is classified with the official LP-7 group and LP-3
singleton orientation loop. Support uses the reference implementation's
`0.99 * epsilon` criterion. Every witness is restored to original reaction
orientation and checked against mass balance and original bounds.

## Pinned Result

For the checksum-pinned Human-GEM v2.0.0 artifact and explicit
`epsilon = 1e-4`:

- input reactions: `12,931`;
- sign-definite blocked reactions: `1,133`;
- reduced-network FASTCC blocked reactions: `157`;
- total blocked reactions: `1,290`;
- flux-consistent reactions: `11,641`;
- LP-7 group solves: `6`;
- LP-3 singleton solves: `247`;
- maximum mass-balance residual: `3.3518572306275897e-10`;
- maximum bound violation: `5.4152662179700575e-11`.

Reaction identities and the complete blocked-reaction list are committed with
SHA-256 digests in
`data/published_models/human_gem_v2.0.0.fastcc_audit.json`.

## Scientific Boundary

`epsilon` is a numerical flux threshold, not a biological parameter. A
flux-consistent reaction is merely capable of carrying flux somewhere in the
generic reconstruction. It is not necessarily active in a hepatocyte, and this
audit supplies no donor context, exchange state, objective, flux magnitude,
kinetic rate, time course or runtime authority.
