# Milestone 090: Hepatocyte Capability and Memory Atlas v1

## Goal

Declare the full engineering scope of the hepatocyte before deepening individual
features, and separate a chronological event log from persistent biological
memory.

## Implemented

- `38` concise capability templates across `12` domains.
- Explicit compartments, inputs, outputs, state variables, dependencies,
  validation observables, physical history substrates and visual roles.
- `44` quantitative parameter slots. Every value is `null` and every template
  is non-executable until context-matched evidence and validation exist.
- `12` physical memory-substrate contracts, including sequence, DNA damage,
  epigenetic state, RNA networks, receptor state, protein/aggregate state,
  organelle quality, metabolic stores, membrane/polarity state, damage response
  and the external niche.
- A strict write-persist-read rule: an experience becomes memory only when a
  directly assayed physical carrier persists after trigger removal and changes
  a later measured response.

## Current Result

- Filled capability parameter slots: `0 / 44`
- Quantitatively activated templates: `0 / 38`
- Required memory persistence tests: `34`
- Quantitatively coupled memory carriers: `0 / 12`
- Biological accuracy percentage: `null`

## Scientific Boundary

Feature coverage is not biological completeness. An implementation reference
does not promote an exploratory module, and a pathway citation cannot fill a
kinetic parameter. Event duration is provenance rather than memory; no trace is
consolidated, inherited or allowed to alter future responses without a measured
carrier, washout/persistence evidence and a readout law.

## Primary References

- Robinson et al. (2020), Human1 metabolism atlas:
  https://doi.org/10.1126/scisignal.aaz1482
- Thul et al. (2017), subcellular human proteome map:
  https://doi.org/10.1126/science.aal3321
- MacParland et al. (2018), normal human liver cell atlas:
  https://doi.org/10.1038/s41467-018-06318-7
- Alberts et al., *Molecular Biology of the Cell*:
  https://www.ncbi.nlm.nih.gov/books/NBK21054/

## Files

- `engine/cell_engine/validation/capability_atlas.py`
- `engine/cell_engine/processes/cellular_memory.py`
- `engine/cell_engine/core/history.py`
- `engine/tests/test_capability_atlas.py`
- `engine/tests/test_cellular_memory_contract.py`
