# Milestone 030 — Real-units / copy-number foundation

## Why

Every prior pool lived on a normalized `[0, 1]` scale. That is adequate for
coarse visualization but mathematically incompatible with the stochastic core
the project is heading toward: reaction propensities in the Gillespie SSA and
the chemical Langevin equation are defined on **molecule counts**, not on
dimensionless fractions. So before any stochastic biochemistry, the model needs
an absolute-scale layer: real volumes, real concentrations, and a clean
concentration ↔ count conversion.

This milestone adds that layer **additively**. It does not touch the existing
`step_cell` deterministic loop; the normalized pools keep working. The new
`cell_engine.quantitative` package sits alongside as the foundation the
stochastic engine will seed from.

## What was added

- `quantitative/geometry.py`
  - `HEPATOCYTE_CELL_VOLUME_L = 3.4 pL` — source-anchored hepatocyte volume.
  - `build_hepatocyte_geometry(definition)` — turns each compartment's
    `volume_fraction` into an absolute volume (L), so the model definition stays
    the single source of truth for cell layout.
  - `molecules_from_concentration_mM` / `concentration_mM_from_molecules` —
    Avogadro-based, exactly invertible conversions.
- `quantitative/species.py`
  - `HEPATOCYTE_SPECIES` — a curated registry of physiological concentrations
    for species that have a *real, measurable* single-molecule concentration
    (ATP, ADP, AMP, NAD(H), NADPH, GSH/GSSG, glucose, glycogen, lactate,
    pyruvate, free cytosolic Ca²⁺). Each entry carries a representative value, a
    physiological range, a source, an assumption level, and an explicit honest
    confidence (0–1).
  - `species_copy_numbers(geometry)` — representative molecule counts per
    species, the integer-scale seeds for the stochastic core.

## Deliberate omissions (no fake precision)

Abstract model pools — cargo packets, `damaged_organelle_mass`, bulk `lipids`,
`glycogen` is flagged as glucosyl-unit-equivalent not free molecules — are **not**
assigned molar concentrations. Giving them a concentration would manufacture
precision the biology does not support. They remain on the normalized layer
until they are decomposed into real species.

## Honesty about the numbers

Confidence is rated per species. Free cytosolic Ca²⁺ (~100 nM) is well measured
(0.7). Total adenine-nucleotide and redox pools are textbook ranges where
*free* vs *total* and compartment partitioning blur the value (0.3–0.55). The
ranges are wide on purpose; this is a grounded starting point to be tightened
against hepatocyte-specific datasets, not a claim of measured truth.

## Verification

`tests/test_quantitative.py` (9 tests):
- concentration→count→concentration round-trips to 9 places;
- a known-magnitude check (1 mM in 1 L ≈ 6.022e20 molecules);
- compartment volumes positive and bounded by the cell volume;
- every curated species maps to a real pool in the definition, has a real
  source, a confidence in (0, 1], and a value inside its range;
- ATP copy number lands at ~10⁹ in the cytosol; Ca²⁺ far lower but still many
  copies.

Full engine suite: 59/59 passing, no regressions.

> Sandbox note: the project targets Python 3.11+ (`datetime.UTC`). The CI
> sandbox only had 3.10, so verification used an in-memory `datetime.UTC` shim;
> the user's local 3.14 runs the suite directly with `python -m unittest`.

## Next

This unblocks the stochastic core. The planned path:
1. A general stochastic integrator skeleton (propensity → step) supporting both
   exact SSA (low-copy species) and chemical Langevin (high-copy species).
2. Convert one real pathway (candidate: glycolysis or the urea cycle) end-to-end
   onto real units + the stochastic integrator + literature validation.
3. Partition species by copy number to run the hybrid SSA+CLE regime that
   reflects real cellular noise structure.
