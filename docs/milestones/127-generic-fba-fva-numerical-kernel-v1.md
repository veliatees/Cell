# Milestone 127: Generic FBA/FVA numerical kernel v1

## Purpose

Verify the linear-programming machinery required by a future hepatocyte
constraint model without confusing solver correctness with biological validity.

## Implemented

- A pinned `scipy.optimize.linprog` / HiGHS backend.
- Explicit stoichiometric matrices, reaction bounds, right-hand sides and
  objective coefficients.
- FBA maximization/minimization with mass-balance and bound-residual checks.
- Objective-constrained flux-variability analysis.
- Alternate-optimum detection.
- Elastic L1 infeasibility diagnosis that reports metabolite balance slack
  without silently deleting reactions or relaxing bounds.
- Validation of duplicate identifiers, dimensions, finite coefficients and
  invalid reaction bounds.

## Analytic Fixtures

Five software checks exercise:

- a mass-balanced linear chain with an analytic optimum;
- fixed optimum ranges;
- two interchangeable optimal routes;
- an infeasible steady-state system;
- localization of the minimum required mass-balance slack.

## Scientific Boundary

The fixtures are synthetic software tests. Human-GEM is not loaded, a
healthy-PHH context is not extracted, no objective or exchange bound is inferred
and no computed flux has biological authority.
