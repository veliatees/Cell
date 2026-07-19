# Milestone 082 - Quantitative reaction authority firewall v1

## Goal

Prevent a source-backed pathway name or stoichiometric topology from being
mistaken for a source-backed numerical simulation. Every active reaction rate
must now pass its own parameter-provenance gate before it can contribute to a
quantitative validation or predictive claim.

## Finding

The current composed hepatocyte fuel network contains:

- `43` declared species;
- `36` active reaction channels;
- `2` reactions with source-backed numerical parameter provenance;
- `34` reactions with no registered numerical parameter provenance;
- `0` fitted, placeholder, or invalid parameter records in this specific audit.

The two source-backed channels are `atp_regeneration` and `atp_maintenance`.
Their apparent hepatic ATP exchange parameter is literature-derived. The other
34 reactions retain useful pathway topology and stoichiometry, but their
runtime magnitudes are not authorized as quantitative healthy-human-PHH rates.

This is a parameter-authority result, not a percentage estimate of whole-cell
biological realism.

## Separate gates

The firewall keeps three questions independent:

1. Does every numerical parameter carry valid measured or literature-derived
   provenance?
2. Does the source biological system, assay, unit, state, compartment, and time
   context match the runtime claim?
3. Has the complete network passed an independent held-out validation?

A topology citation cannot answer question 1. Complete provenance cannot answer
question 2. A context-matched calibration dataset cannot also be treated as the
independent answer to question 3.

## Runtime policy

Reactions are classified as `source_backed`, `fitted`, `placeholder`,
`unparameterized`, or `invalid`.

- Exploratory execution remains allowed and visibly labelled.
- Quantitative validation requires all reactions to be source-backed and the
  network context to be confirmed.
- Predictive execution additionally requires independent held-out validation.
- Unsupported channels raise `ReactionAuthorityError` when a caller requests a
  forbidden quantitative or predictive purpose.
- The normal research-preview snapshot stays available because the integrated
  network is quarantined as exploratory rather than silently promoted.

## Snapshot and browser

All `41` committed zone, nutritional-state, and experiment snapshots export the
same reaction-authority contract. The browser displays the current
`source-backed / total` count and runtime role. The evidence panel exposes the
full authority counts and the context and held-out gates.

No browser code infers authority from reaction names, pathway labels, or source
URLs; it renders the Python audit result.

## Scientific effect

This milestone does not add a new biological rate and therefore does not claim
that the hepatocyte became more complete. It makes the present limit exact and
machine-enforced. The next metabolic milestone can now replace the 34
unparameterized channels one by one without allowing partial progress to be
misreported as a validated whole network.

## Verification

- reaction classification and metadata validation;
- quantitative and predictive fail-closed behavior;
- separate network-context and held-out gates;
- an exact regression test for the current `2 / 36` integrated-network result;
- structured verification across all 41 exported snapshots;
- full Python and TypeScript test suites plus production build;
- browser text and console inspection.

## Evidence boundary

No new biological source or numerical parameter is activated here. The audit
operates on the provenance records already attached to reaction parameters. Its
central rule follows the project's existing scientific policy: a citation for a
mechanism is not evidence for an unreported numerical rate.
