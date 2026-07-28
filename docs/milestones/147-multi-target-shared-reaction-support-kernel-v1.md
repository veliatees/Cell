# Milestone 147: Multi-target shared reaction-support kernel v1

## Scope

Find the smallest caller-supplied candidate-reaction identity set that can
support several steady-state target reactions. Every target receives an
independent flux vector. Candidate identities are shared across those
scenarios, so one reaction used by several targets is counted once.

This is a structural numerical kernel. It does not select a hepatocyte
objective, infer an enzyme concentration, attach an exchange measurement or
authorize a runtime rate.

## Formulation

For target scenario `t`, reaction `j` has flux `v[t,j]`. Candidate reaction
`c` has forward and reverse scenario binaries `f[t,c]` and `r[t,c]`, plus one
shared identity binary `y[c]`.

- `S v[t] = 0` independently for every target;
- `f[t,c] + r[t,c] <= y[c]`;
- `y[c] <= sum_t(f[t,c] + r[t,c])`;
- an active forward or reverse candidate must carry at least the declared
  algorithmic epsilon while preserving its native finite Human-GEM bound;
- an inactive candidate has exactly zero flux in that scenario;
- each target has an explicit forward/reverse choice, with previously proven
  infeasible directions optionally fixed;
- the objective is `min sum_c y[c]`;
- optional cardinality and no-good constraints support exact optimum
  enumeration.

The shared identity is therefore the logical OR of threshold-crossing
scenario directions. Subthreshold candidate activation is not accepted.

## Certification

- SciPy `milp`/HiGHS with zero relative MIP gap;
- integrality residual checked against the documented HiGHS tolerance;
- raw MILP witnesses checked for mass balance, bounds, target direction and
  every candidate-direction threshold;
- rounded identity sets re-solved independently by LP for every target;
- three fail-closed LP attempts are available: HiGHS with presolve, dual
  simplex without presolve and IPM without presolve;
- no failed LP certificate is promoted.

Fourteen synthetic tests cover shared and disjoint supports, reverse targets,
positive candidate lower bounds, cardinality/no-good cuts, target-direction
restrictions and a stoichiometric amplification case that rejects
subthreshold candidate flux.

## Scientific Boundary

Epsilon is a numerical consistency threshold, not a measured biological rate.
Independent target scenarios establish that functions are individually
possible in one selected reaction set; they do not claim simultaneous
coactivity. Structural selection does not establish PHH activity.

## Sources

- Reed et al., optimization-based gap filling:
  <https://doi.org/10.1186/1471-2105-8-212>
- Latendresse, fast gap filling:
  <https://doi.org/10.1186/1471-2105-15-225>
- HiGHS option definitions:
  <https://ergo-code.github.io/HiGHS/stable/options/definitions/>
