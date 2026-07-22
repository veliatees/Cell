# Hepatocyte quantitative literature harvest

This directory preserves the external 168-record literature harvest received on
2026-07-22. The raw CSV, JSON, organism partitions and methods file are stored
byte-for-byte under `raw/`; `raw/manifest.v1.json` pins their SHA-256 values.

The harvest is evidence intake, not a parameter table. In particular:

- whole-body glucose or ketone turnover is not a per-hepatocyte flux;
- recombinant Sf9, HEK or Xenopus measurements are same-assay protein evidence;
- liver membrane abundance is not an active surface copy count;
- injury observations apply only to their exact dose, culture and time protocol;
- rat, mouse, HepaRG and other-system records cannot calibrate healthy PHH.

`curated/source_review.v1.json` records the source families manually checked in
Cell and the exact raw rows used downstream. All automatic parameter and runtime
coupling gates remain false.

## Audit result

- 168 rows across seven tracks and 91 unique PMIDs;
- 144 rows with a reported value and 115 with a standalone numeric scalar/range;
- 65 rows with an error field and 59 with a sample-size field;
- 73 distinct free-text values in `usable_for_human_wholecell`, so that column is
  never interpreted as an executable enum;
- one known bucket inconsistency: CSV row 167 is a macaque record placed in the
  `human` partition. It remains unchanged in raw data and is excluded by audit.

The executable audit is implemented in
`engine/cell_engine/validation/hepatocyte_quantities.py`.
