# Milestone 176 — Event-driven dynamic-FBA boundary numerics v1

## Outcome

The project now has a generic numerical operator for advancing extracellular
amounts between future FBA solves. For external pool `i`, it applies

`n_i(t + dt) = n_i(t) + dt * (b_i + N * sum_r(nu_ir * v_r))`

with canonical units of fmol, fmol/cell/h, fmol/h and hours. Cellular exchange
and non-cellular boundary flow remain separate ledger terms.

This closes a numerical software gap only. The operator supplies no
healthy-PHH context, Human-GEM exchange bounds, biological objective,
organ-to-cell conversion or measured flux.

## Numerical invariants

- External amounts may never become negative.
- A fixed-flux interval ends at the earliest pool-depletion event.
- Simultaneous depletion events are retained together.
- Continuation after depletion requires a new FBA solve.
- Exchange fluxes are never silently rescaled.
- No unit conversion is inferred or applied.
- Every external exchange delta has an equal and opposite cell-exchange ledger
  delta.
- Input order cannot change aggregated rates or outputs.

## Analytic verification

Six synthetic fixtures cover:

1. finite uptake with exact external/cell ledgers;
2. earliest-depletion event detection;
3. simultaneous depletion;
4. open-boundary feed cancelling cellular uptake;
5. secretion increasing an external pool; and
6. permutation-invariant aggregation.

Malformed states, negative amounts, invalid time steps, unknown pools,
duplicate reaction/pool identities and non-finite fluxes fail closed.

## Integration boundary

The kernel is included in the metabolic constraint shell and the four-cycle
metabolic authority graph. It closes the generic dynamic-update-law gate, so
the graph now reports eight of 38 gates satisfied. Quantitative execution
remains zero because the PHH context, measured bounds, objective, scale bridge,
independent evidence review and held-out validation gates remain closed.

## Code surfaces

- `engine/cell_engine/quantitative/dynamic_fba_numerics.py`
- `engine/tests/test_dynamic_fba_numerics.py`
- `engine/cell_engine/quantitative/metabolic_constraint_shell.py`
- `engine/cell_engine/validation/metabolic_cycle_program.py`
