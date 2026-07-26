# Milestone 142: Source-limited minimum-reaction support kernel v1

## Purpose

Find the smallest set of explicitly allowed candidate reactions that can
support a target reaction at steady state, while preventing numerical
gap-filling from silently becoming biological evidence.

## Formulation

For every candidate reaction, separate forward and reverse binary variables
control its native bounded flux. The objective minimizes the number of active
candidate directions. Constraints enforce:

- steady-state mass balance, `S v = 0`;
- target flux of at least `epsilon` in the requested direction;
- at least `epsilon` absolute flux for every selected candidate;
- zero flux for every unselected or unavailable reaction;
- at most one selected direction per candidate.

Only native finite reaction bounds provide linking constants. There is no
invented universal bound, biological weight or reaction-priority score.

## Numerical Certification

- backend: `scipy.optimize.milp` / HiGHS;
- pinned SciPy version: `1.17.1`;
- relative MIP gap: `0`;
- explicit HiGHS MIP feasibility tolerance: `1e-9`;
- every rounded support is independently re-solved as a continuous LP with
  all unselected candidates fixed exactly to zero;
- mass balance, native bounds, target flux and every selected candidate flux
  are checked again;
- solver limits and ambiguous failures are rejected rather than interpreted as
  infeasibility.

The HiGHS numerical option definition is:
<https://ergo-code.github.io/HiGHS/stable/options/definitions/>.

## Method Sources

- Kumar et al., optimization-based GapFind/GapFill:
  <https://doi.org/10.1186/1471-2105-8-212>;
- Latendresse, minimum-reaction gap-filling context and limitations:
  <https://doi.org/10.1186/1471-2105-15-225>.

The project does not use either paper as evidence that a suggested reaction is
biologically active. It uses the minimum-reaction principle only as a
structural diagnostic.

## Verification

Synthetic networks cover:

- exact one-reaction repair;
- exact two-reaction repair;
- an unavailable-reaction failure;
- full-versus-disconnected flux ranges;
- invalid reaction partitions.

Minimum-support uniqueness is never claimed.
