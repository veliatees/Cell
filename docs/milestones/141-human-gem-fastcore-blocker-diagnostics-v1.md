# Milestone 141: Human-GEM FASTCORE blocker diagnostics v1

## Purpose

Determine whether the `17` reactions blocked in the adaptive FASTCORE output
are blocked in generic Human-GEM itself or were disconnected by context
extraction.

## Method

The audit uses the checksum-pinned Human-GEM v2.0.0 artifact and its complete
generic FASTCC-consistent subset:

- generic consistent network: `11,641` reactions;
- adaptive FASTCORE candidate: `7,415` reactions;
- numerical activity threshold: `1e-4`, retained from the pinned FASTCC
  experiment and explicitly not interpreted as a biological threshold;
- unchanged generic reaction bounds;
- exact minimum and maximum steady-state flux LPs for each blocker in both
  networks;
- full-network flux witnesses, incident metabolites and omitted one-hop
  reaction identities.

The primary extraction method remains Vlassis, Pacheco and Sauter:
<https://doi.org/10.1371/journal.pcbi.1003424>.

## Result

- blockers diagnosed: `17`;
- active in generic FASTCC-consistent Human-GEM: `17/17`;
- blocked in the adaptive candidate: `17/17`;
- omitted reactions appearing across the selected generic extrema witnesses:
  `1,169`;
- omitted reactions appearing across one-hop neighborhoods: `1,402`;
- maximum witness mass-balance residual: `6.366462912410498e-12`;
- maximum witness bound violation: `2.5011104298755527e-12`.

The large extremum witnesses are not minimum repair sets. They establish that
the reactions are structurally possible in generic Human-GEM and identify
where adaptive extraction removed support.

## Scientific Boundary

No reaction bound was changed. No active enzyme, PHH flux, exchange condition,
objective or kinetic rate was inferred. This milestone diagnoses the numerical
failure but does not repair it and does not accept a PHH context model.
