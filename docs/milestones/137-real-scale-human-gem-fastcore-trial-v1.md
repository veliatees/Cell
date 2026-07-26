# Milestone 137: Real-scale Human-GEM FASTCORE trial v1

## Purpose

Apply the seven-donor Boolean proteome core to the real pinned Human-GEM model
and accept a context only if the result is numerically consistent and
scientifically scoped.

## Source-Defined Numerical Method

FASTCORE follows Vlassis, Pacheco and Sauter:

- primary paper: <https://doi.org/10.1371/journal.pcbi.1003424>;
- pinned COBRA Toolbox implementation commit:
  `67c790dbac809d9d891fdbafc33e18c21fc9bddc`;
- `epsilon = 1e-4`, recorded as a numerical threshold;
- fixed LP-10 scale `1e4`, as defined by the pinned official implementation;
- input consistency supplied by an identity- and epsilon-bound FASTCC
  certificate;
- output reactions restored to original stoichiometry and bounds before
  validation.

## Pinned Trial Result

Input:

- globally flux-consistent reactions: `11,641`;
- evidence-backed initial core: `4,555`.

Source-defined FASTCORE:

- selected reactions: `7,320`;
- LP-7 solves: `18`;
- LP-10 solves: `13`;
- reactions blocked in the extracted output at the declared epsilon: `408`.

The source output therefore failed the strict acceptance gate.

This milestone records the official fixed-scaling branch. Milestone 139
separately compares it with the adaptive branch from the same pinned COBRA
Toolbox implementation; the fixed result remains frozen as a reproducible
baseline.

## Closure Diagnostic

To determine whether a parameter-free structural closure could rescue the
trial, every globally consistent reaction in the complete bipartite
reaction-metabolite connected components seeded by the blocked output was
added. This is a project diagnostic, not part of source FASTCORE.

- connected metabolites: `7,056`;
- closure reactions added: `4,319`;
- final reactions: `11,639 / 11,641`;
- omitted reactions: `2`;
- final blocked reactions: `0`;
- maximum mass-balance residual: `2.948032488427326e-10`;
- maximum bound violation: `3.524291969370097e-12`.

The two algorithmically omitted source reactions are `MAR06873` and
`MAR06884`. Because the closure retained `99.9828%` of the consistent generic
network, it did not establish useful context specificity.

## Decision

No Human-GEM PHH context model is accepted. No FBA, FVA, flux magnitude,
objective, exchange bound, kinetic rate or runtime coupling is authorized.

The negative result is informative: total-proteome Boolean detection alone is
insufficient for strict context extraction here. Future acceptance requires
more discriminating evidence such as reaction-specific active localization,
enzyme-capacity evidence, measured exchange constraints and independent
validation.
