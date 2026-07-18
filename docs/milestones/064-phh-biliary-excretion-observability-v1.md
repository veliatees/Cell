# Milestone 064 - PHH d8-TCA biliary-excretion observability v1

## Question

What does the published PHH bile-excretion index actually measure, and how can
it be used without pretending that one ratio is a direct BSEP kinetic constant?

## Source-locked assay contract

Peng et al. 2025 seeded 250,000 PHHs/well on collagen-I-coated 24-well plates,
added 2% Matrigel after overnight attachment, maintained sandwich cultures for
five days, and then used paired calcium-containing and calcium-free HBSS
conditions. After 15 min preincubation, cells received 5 uM d8-taurocholate for
15 min at 37 C. LC-MS supplied the paired assay values.

The published operator is retained exactly:

```text
BEI_percent = (A_Ca - A_CaFree) / A_Ca * 100
```

`A_Ca` must be positive; both inputs must be finite, non-negative, and use the
same concentration unit. A model input must also match species, commercial PHH
system, sandwich format, five-day culture, probe exposure, model identity, and
artifact SHA-256.

## Loaded observations

Table S7 provides five batch values:

```text
PHH393 27.2%
PHH396 27.5%
PHH416 25.7%
PHH005 62.0%
PHH910 59.0%
```

The CSCB >=30% value is retained only as a commercial PHH product criterion.
Two of five batches are at or above it. This count is descriptive and does not
become a model pass/fail result.

## Identifiability boundary

The paired assay identifies BEI as one aggregate output. It identifies zero of
four registered mechanism-specific quantities:

- basolateral d8-TCA uptake rate;
- BSEP canalicular export rate;
- intracellular d8-TCA binding or loss;
- canalicular network volume and sealing.

The source does not publish the paired `A_Ca`/`A_CaFree` values, replicate
uncertainty, extraction volume, live-cell recovery, or transporter surface
abundance. BEI therefore combines uptake, retention, export, geometry, and the
effect of calcium-free buffer on canalicular junctions.

## Files

- `data/phh_baseline/curated/peng2025_phh_biliary_excretion.v1.json`
- `engine/cell_engine/quantitative/phh_biliary_excretion.py`
- `engine/tests/test_phh_biliary_excretion.py`
- `scripts/export_engine_snapshot.py`
- `src/engineSnapshot.ts`
- `src/main.ts`

## Release status

- Five-batch BEI table: loaded.
- Paired-condition measurement operator: ready.
- Raw paired assay values: not loaded because they were not published.
- Transporter-specific fitting: blocked.
- Canalicular-geometry coupling: blocked.
- Automatic cell-state coupling: blocked.
- Predictive release: blocked.
