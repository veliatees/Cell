# Milestone 076: Human Liver Open-Data Atlas v1

## Goal

Use every presently compatible open human-liver measurement without turning
cross-assay evidence into a fictional donor or inventing missing geometry,
abundance, membrane localization, binding, or kinetic parameters.

## Reproducible Curation

`scripts/curate_human_liver_open_atlas.py` downloads five open supplementary
artifacts, verifies their byte counts and MD5 hashes, records SHA-256 hashes,
and writes the compact, reviewable bundle:

`data/phh_baseline/curated/human_liver_open_atlas.v1.json`

The source spreadsheets and the 61 MB tissue archive remain in an external
cache. The repository stores a 2 MB curated product rather than multi-gigabyte
raw spatial-omics matrices. The curation command is explicit and does not run
during normal simulation startup.

## Integrated Evidence Layers

### Human hepatocyte 2D morphometry

- Watson et al. source data contribute `56,055` healthy human hepatocytes.
- Segmented area has a `463.3 um2` median and `155.8-862.0 um2` P05-P95 range.
- Source-defined `Hep_1`, `Hep_2`, and `Hep_3` clusters retain the paper's
  mapping to zones 1, 2, and 3. This remains a cohort-specific mapping rather
  than a universal donor classifier.
- Detected-nucleus categories are retained. A source value of zero is treated
  as failed nucleus attribution, not proof of a biologically anucleate cell.
- These data can support a future 2D renderer distribution and a contextual
  range check. They cannot replace the current 3D equivalent-volume geometry.

### Primary-human-hepatocyte surface identities

- Mallanna et al. contribute `300` cell-surface-captured N-glycoproteins,
  including `66` CD annotations and `228` transmembrane annotations.
- The current surface capability profile gains assay-level identity evidence
  for `SLC10A1`, `EGFR`, `INSR`, `MET`, `IL6ST`, `ABCB11`, `ABCC2`, and `ABCB1`.
- Non-detection of `CDH1`, `GJB1`, `GCGR`, `IL6R`, `FZD6`, `LRP5`, or `LRP6`
  in this assay is not converted into biological absence.
- Surface density, sinusoidal/lateral/canalicular domain, molecular orientation,
  active fraction, and 2D binding kinetics remain unavailable.

### Human spatial protein zonation

- Weiss et al. Supplementary Table 3 contributes `1,736` machine-readable
  proteins across 20 central-to-portal bins in healthy human liver (`N=14`).
  The article text reports `1,741` proteins at the same completeness threshold;
  the unresolved five-record article/supplement difference is retained visibly.
- The published strong-zonation classification contains `171` proteins:
  `102` periportal and `69` pericentral.
- All 20-bin records remain in the curated bundle. The engine exposes all
  strong records through a query API and carries them in the zonation state.
- The browser snapshot exports the 12 strongest selected-zone records to keep
  transfer and rendering cost small.
- The source monotonic analysis does not define a separate midlobular maximum
  class. Its normalized coefficient is never used as a metabolic or transport
  rate multiplier.

### Hepatocyte communication hypotheses

- Watson et al. CellPhoneDB source data contain `1,679` interaction rows.
- The curated hepatocyte subset retains `209` interactions and `1,806` nonzero
  ordered edges involving `Hep_1`, `Hep_2`, or `Hep_3`.
- Source scores can rank hypotheses for later experiments. They are not binding
  probabilities, kinetic rates, local patch occupancy, or causal activators.
- Geometry, local molecule presence, orientation, density, 2D kinetics,
  downstream signaling, and membrane transport remain separate fail-closed
  gates.

### Tissue architecture

- Fabyan et al. contribute a `595 um` median healthy 3D lobule polygonal radius
  (`n=17`, range `428-717 um`) and an independent 2D histology mean of
  `592 +/- 87 um` (`52` measurements, `6` nonfibrotic samples).
- Healthy central-vein source rows are retained separately from cirrhotic rows.
- These values constrain future lobule and vascular scenes, not a single-cell
  boundary or contact-force law.

## Engine And Browser Binding

- `human_liver_open_atlas.py` validates counts, checksums, finite values, record
  uniqueness, and every fail-closed gate before exposing the atlas.
- The existing 18.4 um isolated-PHH diameter is compared only contextually with
  the in-situ 2D area distribution; the comparison cannot recalibrate 3D shape.
- The zonation engine now exposes measured strong protein gradients while
  keeping flux coupling false.
- The communication surface profile contains 11 relevant identities but every
  density, patch-distribution, orientation, and 2D kinetic field remains null.
- All zone, nutrition, and cholestasis snapshots include a compact atlas view.
- The evidence panel reports measured counts and states the missing gates rather
  than displaying an aggregate biological-realism percentage.

## Computational Budget

- Full open processed matrices measured in gigabytes are not vendored.
- The curated source-of-truth bundle is approximately 2 MB.
- The default engine snapshot remains approximately 0.6 MB.
- Atlas JSON is loaded once per Python process and query results are compact.
- No additional particles, literal proteins, cells, or continuous contact-time
  integration are added to the Three.js runtime.

## Validation

- Python tests verify source-artifact identity, morphometry, surface missingness,
  zonation counts, interaction counts, communication-profile expansion, and
  rejection of promoted score-driven signaling.
- TypeScript validates the compact atlas contract and rejects snapshots that
  promote unavailable density, geometry, flux, or binding fields.
- Browser evidence rendering consumes only validated engine snapshot state.

## Primary Sources

- Fabyan et al. 2026: https://doi.org/10.1126/sciadv.adz2299
- Watson et al. 2025: https://www.nature.com/articles/s41467-024-55325-4
- Mallanna et al. 2016: https://pmc.ncbi.nlm.nih.gov/articles/PMC5032032/
- Weiss et al. 2026: https://www.nature.com/articles/s42255-026-01459-2
