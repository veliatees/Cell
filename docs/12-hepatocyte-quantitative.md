# Human hepatocyte — quantitative reference (organelle counts/sizes, protein copy numbers)

This is the sourced numerical foundation that lets the model render organelles
at their true counts/sizes and seed proteins at their true per-cell copy
numbers. It is consumed by the engine (`cell_engine/quantitative/hepatocyte_counts.py`,
the canonical source of truth) and mirrored for the renderer in
`public/cell_quantitative.json` (a test asserts the two agree).

**Honesty rule.** Every value is one of: measured (with citation), an explicitly
flagged *order-of-magnitude* estimate, or absent (`null`/`None`). Nothing is
fabricated. The flags are not decoration — they mark how much weight a number
can bear. Read the caveats below before using any figure.

## Cell-level

| Quantity | Value | Range | Organism | Quality | Source |
|---|---|---|---|---|---|
| Diameter | 25 µm | 20–30 | human | measured | consensus |
| Volume | 3 400 µm³ | 3 000–11 000 | human | order-of-magnitude | BioNumbers |
| Volume (rat) | 5 000 µm³ | 4 900–5 100 | rat | measured | Weibel 1969 |
| Total protein | 464 pg | 150–700 | human | measured | Wiśniewski 2014 / Niu 2022 |
| Protein molecules | 5×10⁹ | 2–8×10⁹ | human | measured | Niu 2022 |
| Binucleate fraction | 0.20 | 0.15–0.25 | human | order-of-magnitude | consensus |
| PM domain split (sinusoidal : lateral : canalicular) | 37 : 50 : 13 % | — | rat | order-of-magnitude | Weibel 1969 / Blouin 1977 |

## Organelles

Volume fractions are rat stereology (best available proxy for human). The
**characteristic diameter** is *derived* (equivalent-sphere from volume fraction
÷ count), not measured — see `characteristic_diameter_um()`.

| Organelle | Count/cell | Vol. fraction | Derived ⌀ | Location | Quality | Source |
|---|---|---|---|---|---|---|
| Nucleus | 1 (1–4; 20% binucleate) | 6.2 % | ~7–8 µm | central | measured (vol) | Weibel 1969 |
| Mitochondria | ~1 000 (500–2 500) | 20 % | ~1 µm | dispersed | order-of-mag (count) | Weibel 1969 / Loud 1968 |
| Rough ER | network | 15 % | — | perinuclear | measured | Weibel 1969 |
| Smooth ER | network | 6 % | — | cytoplasm | measured | Weibel 1969 |
| Golgi | ~40–50 dictyosomes (one apparatus) | 2.6 % | — | canalicular pole | order-of-mag | Blouin 1977 |
| Lysosomes | ~400 (200–600) | 1.0 % | ~0.5 µm | canalicular pole | order-of-mag | Weibel 1969 |
| Peroxisomes | ~500 (350–620) | 1.5 % | ~0.5–0.6 µm | dispersed | order-of-mag | Weibel 1969 |
| Ribosomes | ~10⁷ | — | — | cytosol + RER | order-of-mag | consensus |
| Glycogen | rosettes | 6 % (3–12, fed) | — | cytosol | order-of-mag | Loud 1968 |
| Lipid droplets | ~100 (10–600) | ~1 % (≫ in steatosis) | ~0.4–1 µm | cytosol (ER-derived) | order-of-mag | Fujimoto 2011 |

> **Mitochondria are one heterogeneous population, not several "types."** Hepatocyte
> mitochondria are discrete **spherical/oblong** units (~0.7 × 1.5 µm) — not the
> filamentous reticulum seen in many cell lines — kept heterogeneous in size/shape
> by ongoing fission↔fusion. The model's `mitochondria` and `mitochondrialFragments`
> fields track that single population's fission state, not two distinct organelles.
>
> **Lipid droplets** are ER-derived neutral-lipid stores bounded by a phospholipid
> *monolayer* (not a bilayer organelle). Their count and volume are strongly
> nutritional-state-dependent — few in a lean fed cell, dominating the cytoplasm in
> steatosis — so the ~100 / ~1 % figures are a normal-cell order-of-magnitude anchor.

## Protein copy numbers (per cell)

All seven are **order-of-magnitude** (see caveat 2). Trust the ranking, not the
digits: **CPS1 ≫ NTCP > Na/K-ATPase > GLUT2 > GCK ≈ MRP2 > BSEP**.

| Protein (gene) | Location | Copies/cell | Range | Source |
|---|---|---|---|---|
| GLUT2 (SLC2A2) | basolateral | 7.9×10⁴ | 2.5×10⁴–2.5×10⁵ | Ohtsuki 2012 / Wiśniewski 2016 |
| Na⁺/K⁺-ATPase (ATP1A1) | basolateral | 1.6×10⁵ | 5×10⁴–5×10⁵ | Ohtsuki 2012 |
| NTCP (SLC10A1) | basolateral | 3.2×10⁵ | 1×10⁵–1×10⁶ | Ohtsuki 2012 / Qiu 2013 |
| BSEP (ABCB11) | canalicular | 1.6×10⁴ | 5×10³–5×10⁴ | Ohtsuki 2012 / Wiśniewski 2016 |
| MRP2 (ABCC2) | canalicular | 3.2×10⁴ | 1×10⁴–1×10⁵ | Ohtsuki 2012 / Wiśniewski 2016 |
| Glucokinase (GCK) | cytosol | 6.1×10⁴ | 2.5×10⁴–1.5×10⁵ | HPA / UniProt |
| CPS1 | mito matrix | 5.4×10⁷ | 3.4–8.5×10⁷ | Niu 2022 / Wiśniewski 2016 |

**Derivation.** `copies = (fmol/µg membrane protein) × (µg membrane protein/cell)
× 10⁻¹⁵ × 6.022×10²³`. The conversion is exact; the only assumption is µg
membrane protein/cell ≈ 9–23 pg (464 pg total × 2–5% PM fraction). Drop measured
Ohtsuki 2012 / Wiśniewski 2016 fmol/µg values into this to upgrade the
transporters from order-of-magnitude to measured.

## Functional use in the simulation

The engine does **not** draw one object for every protein molecule. Instead, the
gene-keyed inventory (for example `protein:ABCB11`) is converted into a
dimensionless capacity multiplier relative to its healthy-reference abundance:
`activity = copies / reference copies`. This multiplier scales the corresponding
transporter pathway: GLUT2 for whole-cell glucose exchange; BSEP for canalicular
bile-salt export; MRP2 for bilirubin-conjugate export; NTCP and Na+/K+-ATPase for
their represented transport functions. A zero count is an explicit functional
depletion; a missing entry means the reference healthy abundance.

This is a **relative-effect model**, not an absolute flux prediction. The current
base transport rates are explicitly recorded in reaction provenance as
`placeholder`: copy number alone cannot establish transporter turnover,
membrane area, substrate gradients, or zonal polarization. Those base rates must
be replaced with transporter-specific primary kinetic measurements and calibrated
against measured uptake/export fluxes before the model is used quantitatively.

### Assay kinetics and trafficking guardrail

The engine now records published **assay-specific** kinetic anchors without
misusing them as whole-cell values. Human recombinant BSEP has reported
taurocholate `Km = 4.25 µM`, `Vmax = 200 pmol/mg protein/min`; human recombinant
MRP2 has reported bilirubin-glucuronide kinetics. These measurements retain their
membrane-vesicle units in `stochastic/transporter_kinetics.py`.

Correct membrane localization is a separate biological state: BSEP and MRP2 are
targeted to the canalicular surface and can be retrieved/reinserted. Therefore a
whole-cell capacity can use **measured surface copies** only when a matched healthy
surface-copy reference is supplied. The code refuses to infer surface abundance
from total protein abundance or from the schematic cargo-routing layer. This keeps
trafficking uncertainty visible instead of inventing a surface fraction.

The corresponding lifecycle state has explicit ER, Golgi, canalicular-surface,
basolateral-surface, subapical-endosome, unresolved-intracellular, and degraded
copy pools. It can apply **observed copy-number transfers** while conserving total
protein synthesis. It does not contain a default BSEP/MRP2 trafficking rate: the
literature establishes the topology and regulatory importance of canalicular
targeting, but the rate must be measured or calibrated in the chosen experimental
system before a dynamic run is defensible.

## Cholestasis, proteostasis, fate and experiments

The disease-response layer deliberately separates **causal biology** from
quantitative prediction. BSEP (`ABCB11`) loss removes the represented bile-acid
export term; MRP2 (`ABCC2`) loss removes the represented bilirubin-conjugate
export term. The browser's experiment menu currently exposes only exact control
(`1`) and loss-of-function (`0`) states. It does **not** present an invented
"50% inhibition" as a biological measurement. A non-binary activity may be
supplied only from a matched surface-abundance measurement or calibration.

Each engine step exports a `cellular_response` record with: retained bile-acid
and bilirubin pools; UPR marker and misfolded/ubiquitinated protein loads;
stress-time exposure (units: seconds) across cholestatic, proteotoxic,
oxidative, genotoxic, energetic, and senescence axes; and the dominant current
fate evidence. The exposure integral is explicitly **not** a lesion count and
contains no guessed repair half-life. Likewise, `fate_evidence` is not an
irreversible death decision. The existing ATP-dependent apoptosis/necrosis model
remains available for a separately calibrated temporal commitment experiment.

The causal links are source-backed: transporter loss can produce intracellular
bile-acid retention; cholestasis is associated with ER stress; unresolved UPR
can become pro-apoptotic; and hydrophobic bile acids can drive ROS and
mitochondrial permeability transition in isolated hepatocytes. The internal
source registry is `processes/cellular_response.py`; browser snapshots expose
the source IDs alongside every experiment.

## Growth and membrane geometry contract

The cell-cycle biomass proxy is interpreted as relative cell volume. Therefore
the engine and visualizer share the same derived geometry: radius scales as
`biomass^(1/3)` and membrane area as `biomass^(2/3)`. During cytokinesis, two
equal-volume daughters require more total area than the mother; the exact
equivalent-sphere requirement is computed before partition. Existing
`membrane_supply` can limit that insertion, exposing a membrane deficit instead
of allowing unbounded elastic stretching. This is a shape-model approximation,
not a claim that a hepatocyte is a perfect sphere.

## CAVEATS (read before use)

1. **Rat vs human — the biggest caveat.** The gold-standard hepatocyte
   stereology (Weibel 1969; Blouin 1977; Loud 1968) is all **rat**. Human
   ultrastructural morphometry at that rigor largely does not exist openly. Rat
   organelle fractions are used as the best proxy; the cross-check holds —
   rat mitochondrial *volume* fraction ~20% (Weibel) agrees with human
   mitochondrial *protein-mass* fraction ~23% (Niu 2022), independent methods —
   so treat rat fractions as good to ~±30% for human. Where human data exist
   (protein mass/molecules, cell diameter, binucleate fraction) they are used and
   labelled human.
2. **Protein copy numbers are order-of-magnitude.** The absolute measurements
   exist (Ohtsuki 2012, fmol/µg in 17 human livers; Wiśniewski 2016, copies/cell
   for ~9 400 proteins) but their per-protein tables are paywalled and were not
   transcribed (transcribing from memory would violate the no-fabrication rule).
   Each copy number is instead derived from sourced anchors with the math shown.
   CPS1 is best-anchored (top-10 abundance ⇒ ~3–8×10⁷, reliable to ~½ an order of
   magnitude); GCK and the transporters are weaker — trust order of magnitude and
   ranking only.
3. **Polyploidy ⇒ underestimates.** The proteomic-ruler method assumes a diploid
   genome. Adult human hepatocytes are frequently 4n/8n and 15–25% binucleate, so
   per-cell copy numbers are *likely underestimated* (Niu 2022). Scale up ~×2 for
   a polyploid subpopulation.
4. **State dependence.** Smooth-ER volume fraction is induced by xenobiotics;
   glycogen swings from ~0 (fasted) to >10% (fed). Model these as variables.
5. **Cell volume is wide.** 3 000–11 000 µm³ across ploidy/zonation; 3 400 is a
   common citation, not a consensus. Rat (~5 000, Weibel) is tighter.
6. **Localization** is from UniProt (ECO-coded). HPA immunofluorescence
   (cell-line based) was a cross-check only and disagrees in a few cases
   (e.g. an HPA "uncertain"/nucleoplasm flag for BSEP is a known cell-line
   artefact; the canalicular/apical assignment is correct for hepatocytes).

## Sources

- **Weibel ER, Stäubli W, Gnägi HR, Hess FA.** Correlated morphometric and
  biochemical studies on the liver cell. I. … normal morphometric data for **rat**
  liver. *J Cell Biol.* 1969;42(1):68–91. PMID 4891915.
- **Blouin A, Bolender RP, Weibel ER.** Distribution of organelles and membranes
  between hepatocytes and nonhepatocytes in the rat liver parenchyma. *J Cell
  Biol.* 1977;72(2):441–455. PMID 833203.
- **Loud AV.** A quantitative stereological description of the ultrastructure of
  normal **rat** liver parenchymal cells. *J Cell Biol.* 1968;37(1):27–46. PMID 5645844.
- **Niu L, et al.** Dynamic human liver proteome atlas … *Mol Syst Biol.*
  2022;18(5):e10947. (human)
- **Ohtsuki S, et al.** Simultaneous absolute protein quantification of
  transporters … in human liver. *Drug Metab Dispos.* 2012;40(1):83–92. PMID 21994434.
- **Wiśniewski JR, et al.** Total-protein-approach / absolute hepatocyte proteome
  (2014, 2016). *Per-protein tables paywalled; not transcribed.*
- **Human Protein Atlas**, proteinatlas.org (liver nTPM + localization);
  **UniProt** (canonical localization); **BioNumbers**.

> These citations were assembled from a science-research pass. Landmark
> stereology refs and Ohtsuki 2012 are high-confidence; verify exact
> volume:page/DOI of the proteomics refs against the primary source before any
> publication use.
