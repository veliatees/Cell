# Milestone 174 — Hash-bound independent evidence review gate v1

## Outcome

Machine-readable evidence is no longer equivalent to reviewed evidence. A CSV
may satisfy every column, type, unit-label, donor-split and held-out identity
check while still containing numbers that do not occur in the cited paper. The
new gate therefore requires two separate keys:

1. the scope-specific structural intake validator accepts the delivery; and
2. an independent review decision is bound to the exact delivery, contract and
   review-artifact SHA-256 values.

The second key requires curator/reviewer separation, row-level primary-source
review, raw-artifact hash verification, context/unit review and held-out
independence review. Approval grants structural evidence credit only. It never
authorizes a parameter, fit, prediction, flux, reaction or cell-state coupling.

## Quarantined curation attempt

An unreviewed four-file curation attempt was found in the local incoming
directory. All files were removed from the active intake path without deletion
and retained under the git-ignored local forensic quarantine. No numeric row
was promoted.

| Delivery | Rows including header | SHA-256 | Decision |
|---|---:|---|---|
| PHH energy/redox trajectories | 21 | `41fca5a249de21269696be54ae8ffc416556d6a83c2ca5cafb01048639a9d92d` | rejected from active intake |
| PHH injury trajectories | 26 | `b27149ac630f66aa37b0a00e2c2908b493465ebabae49449eb7dfb2b755ffcf8` | independent source review required |
| PHH reaction evidence | 433 | `f42a4ecc3d51b644e3a56b47ef520a6bc55d8170335741bfff015447c15e536d` | rejected from active intake |
| PHH receptor/signaling trajectories | 185 | `20847cb165107ffd4c264f08be24d3aca4f160f2b68df12d0df491fec7c037de` | rejected from active intake |

The audit found decisive source-identity failures:

- `10.1007/s00204-022-03299-x`, cited as a compartment-resolved PHH ATP
  trajectory experiment, is an Archives of Toxicology review about integrated
  alternatives to animal testing, not an ATeam PHH time-series study.
- `10.1016/j.molcel.2014.05.008` reports isotope tracing in engineered H1299,
  A549 and other cell lines. It is not a donor-resolved healthy-PHH
  Grx1-roGFP2 trajectory source.
- `10.1093/toxsci/kfs214`, cited for APAP PHH injury trajectories, is a study of
  maternal immunotoxic exposure and newborn immune function, not an APAP
  hepatotoxicity experiment.
- `10.1038/s41467-021-25916-w` is a real PHH spheroid culture-condition study,
  but it cannot serve as held-out dynamic validation for all eight receptor,
  junction and viral-entry pathways, and it does not report the uniformly
  templated receptor densities and kinetic trajectories in the delivery.
- The energy delivery used the SHA-256 of an empty file as its raw-artifact
  identity. Reaction and signaling held-out rows used the same empty digest as
  a purported frozen model artifact.

Primary records used for this audit:

- <https://doi.org/10.1007/s00204-022-03299-x>
- <https://pmc.ncbi.nlm.nih.gov/articles/PMC4106038/>
- <https://pubmed.ncbi.nlm.nih.gov/22738990/>
- <https://pmc.ncbi.nlm.nih.gov/articles/PMC8551077/>
- <https://pmc.ncbi.nlm.nih.gov/articles/PMC4855186/>
- <https://pmc.ncbi.nlm.nih.gov/articles/PMC4171351/>

## Implemented surfaces

- `phh_delivery_review_registry.v1.json` is the canonical fail-closed review
  registry. It begins with zero approvals.
- `evidence_review.py` computes stable file/directory hashes, validates exact
  review records and quarantines changed or rejected deliveries.
- The unified 16-contract preflight reports independent-review status and gives
  zero structural credit to unreviewed deliveries.
- Reaction-evidence and receptor-signaling rows can no longer self-authorize by
  writing `verified` inside their own CSV.
- Empty-file digests are prohibited for raw evidence, frozen model artifacts
  and split manifests.
- Incoming evidence, forensic quarantine and local output are excluded from
  source control by policy.
- Reaction-evidence slot definitions now live in one dependency-free schema
  module instead of being copied between intake and atlas modules.

## Remaining boundary

The review registry is a repository-governance control, not a cryptographic
proof of a reviewer's real-world identity. A future external collaboration may
add signed review receipts. Until then, approval still requires explicit human
review of the tracked diff and review artifact. All four biological execution
loops remain quantitatively closed until source-correct evidence is curated.
