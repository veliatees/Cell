# Milestone 067 - BSEP/MRP2 transporter inventory and denominator bridge v1

## Question

Can measured transporter abundance become a copy number, surface density, or
transport rate for one simulated hepatocyte?

## BSEP same-cohort bridge

Wisniewski et al. report both average total protein per hepatocyte and BSEP
abundance for the same seven-donor purified-PHH cohort:

```text
BSEP abundance = 1.4 pmol/mg total protein
Total protein  = 600 pg/cell = 6 x 10^-7 mg/cell
```

Using the exact Avogadro constant:

```text
copies/cell
= 1.4 pmol/mg x 6 x 10^-7 mg/cell x 10^-12 mol/pmol
  x 6.02214076 x 10^23 copies/mol
= 505,859.82384 total BSEP copies/cell
```

The UI displays approximately `5.1 x 10^5` because the source abundance has
limited precision. No uncertainty interval is invented because the source does
not publish uncertainty for either headline input.

## What that count does not mean

This is total cellular BSEP. It does not identify how many copies are on the
canalicular surface, correctly folded, ATP-coupled, substrate-accessible, or
transport-active. It therefore cannot define surface density or bile-salt flux.

## Why MRP2 remains unbridged

Deo et al. measured MRP2 as `1.54 +/- 0.64 fmol/ug liver membrane protein` in
membrane fractions from 51 human livers. This is exactly equivalent to
`1.54 +/- 0.64 pmol/mg liver membrane protein`, but its denominator is not
total protein in a purified hepatocyte. The fraction may contain multiple
membrane pools and cell types. Multiplying it by 600 pg PHH total protein would
mix incompatible denominators, so MRP2 copies per hepatocyte remain null.

## Visual boundary

Individual BSEP and MRP2 proteins are far below the whole-cell scene scale.
The renderer may use subpixel density/activity fields or explanatory reference
models, but not literal count-matched visible transporter objects.

## Files

- `data/phh_baseline/curated/human_hepatocyte_transporter_inventory.v1.json`
- `engine/cell_engine/quantitative/phh_transporter_inventory.py`
- `engine/tests/test_phh_transporter_inventory.py`
- `scripts/export_engine_snapshot.py`
- `src/engineSnapshot.ts`
- `src/main.ts`

## Release status

- BSEP total-copy denominator bridge: ready.
- BSEP surface and active copy counts: blocked.
- MRP2 per-hepatocyte denominator bridge: blocked.
- Surface density and flux coupling: blocked.
- Literal molecule rendering: prohibited.
- Automatic cell-state coupling: blocked.
- Predictive release: blocked.
