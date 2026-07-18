# Human hepatocyte — quantitative reference (organelle counts/sizes, protein copy numbers)

This is the sourced numerical foundation that lets the model render organelles
at their sourced counts/sizes and seed selected proteins at measured copies per
reference nucleus. It is consumed by the engine (`cell_engine/quantitative/hepatocyte_counts.py`,
the canonical source of truth) and mirrored for the renderer in
`public/cell_quantitative.json` (a test asserts the two agree).

**Honesty rule.** Every value is one of: measured (with citation), an explicitly
flagged *order-of-magnitude* estimate, or absent (`null`/`None`). Nothing is
fabricated. The flags are not decoration — they mark how much weight a number
can bear. Read the caveats below before using any figure.

## Cell-level

| Quantity | Value | Range | Organism | Quality | Source |
|---|---|---|---|---|---|
| Volume | 5 657.07116 µm³ median | MAD 744.875484 µm³ | normal-control human liver, 3D reconstruction | measured aggregate, 5 reconstructions, 0.3 µm isotropic voxels | Segovia-Miranda 2019, Supplementary Table 3 Fig. 3c |
| Volume-equivalent diameter | 22.1070608 µm | — | derived from active 3D NC median volume | exact geometry, not an independent observation | (6 × 5 657.07116 / π)^(1/3) |
| Historical in-situ volume cross-check | 2 850 ± 99.9 µm³ mean | uncertainty statistic not identified in accessible abstract | normal human, intermediate lobular zone | measured stereology, 5 selected cases; retained but not averaged | Duarte 1989 |
| Isolated-cell diameter cross-check | 18.4 µm median | 12–26 (88% of cells) | human isolated PHH | measured, 54 cryopreserved batches | Olander 2021 |
| Volume (rat) | 5 000 µm³ | 4 900–5 100 | rat | measured | Weibel 1969 |
| Total protein | 604.89 pg/nucleus donor mean (paper rounds to 600) | 481.96–818.10 donor means | human PHH, 7 donors | measured | Wiśniewski 2016 Supplementary Table 2 |
| Quantified protein-group copy sum | 8.759×10⁹/nucleus donor mean (paper rounds to 8.7×10⁹/reference cell) | 6.920–11.841×10⁹ | human PHH, 7 donors | measured + arithmetic sum | Wiśniewski 2016 Supplementary Table 2 |
| Binucleate fraction | 0.20 | 0.15–0.25 | human | order-of-magnitude | consensus |
| PM domain split (sinusoidal : lateral : canalicular) | 37 : 50 : 13 % | — | rat | order-of-magnitude | Weibel 1969 / Blouin 1977 |

## Organelles

Volume fractions are rat stereology (best available proxy for human). The
**characteristic diameter** is *derived* (equivalent-sphere from volume fraction
÷ count), not measured — see `characteristic_diameter_um()`.

The active volume anchor is the direct normal-control 3D median
`5 657.07116 µm³`. Its `22.1070608 µm` volume-equivalent diameter is a
conversion geometry, not a claim that an in-situ polarized hepatocyte is
spherical. Duarte's older `2 850 µm³` stereology mean and Olander's `18.4 µm`
isolated-cell median remain separate cross-checks; they are not averaged. All
absolute compartment volumes, the renderer, RDME lattice,
concentration-to-count conversion and contact world consume the same active
reference rather than carrying independent cell sizes.

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
| Lipid droplets | count unavailable | 0.507807 % median (MAD 0.403178 percentage points; n=5 reconstructions) | distribution unavailable | cytosol (ER-derived) | measured aggregate healthy-human 3D volume fraction | Segovia-Miranda 2019 Fig. 3i |

> **Mitochondria are one heterogeneous population, not several "types."** Hepatocyte
> mitochondria are discrete **spherical/oblong** units (~0.7 × 1.5 µm) — not the
> filamentous reticulum seen in many cell lines — kept heterogeneous in size/shape
> by ongoing fission↔fusion. The model's `mitochondria` and `mitochondrialFragments`
> fields track that single population's fission state, not two distinct organelles.
>
> **Lipid droplets** are ER-derived neutral-lipid stores bounded by a phospholipid
> *monolayer* (not a bilayer organelle). Their count and volume are strongly
> nutritional-state-dependent, but the project does not yet have a matched human
> PHH dose-time law. The browser therefore keeps the measured healthy aggregate
> `0.507807 %` display volume static. Display samples do not encode droplet count,
> individual size distribution, or an inferred fed/fasted response.

## Protein copy numbers (per reference nucleus)

These are seven-donor medians and observed donor ranges from the official
Supplementary Table 2. All seven selected canonical groups were quantified in
all seven donors. The measured ranking is **CPS1 ≫ GLUT2 > Na/K-ATPase > BSEP >
MRP2 ≈ GCK > NTCP**.

| Protein (gene) | Location | Median copies/nucleus | Seven-donor range | Source |
|---|---|---|---|---|
| GLUT2 (SLC2A2; canonical group P11168) | basolateral | 2.292×10⁶ | 1.994–2.979×10⁶ | Wiśniewski 2016 Table 2 |
| Na⁺/K⁺-ATPase (ATP1A1; P05023 group) | basolateral | 1.886×10⁶ | 1.352–2.610×10⁶ | Wiśniewski 2016 Table 2 |
| NTCP (SLC10A1; Q14973) | basolateral | 5.831×10⁴ | 7.554×10³–1.267×10⁵ | Wiśniewski 2016 Table 2 |
| BSEP (ABCB11; O95342 group) | canalicular | 4.194×10⁵ | 3.545–7.510×10⁵ | Wiśniewski 2016 Table 2 |
| MRP2 (ABCC2; Q92887 group) | canalicular | 1.299×10⁵ | 8.239×10⁴–1.934×10⁵ | Wiśniewski 2016 Table 2 |
| Glucokinase (GCK; P35557 group) | cytosol | 1.247×10⁵ | 3.422×10⁴–2.421×10⁵ | Wiśniewski 2016 Table 2 |
| CPS1 (P31327 group) | mitochondrial matrix | 1.131×10⁸ | 9.238–12.228×10⁷ | Wiśniewski 2016 Table 2 |

The full atlas retains 8,689 quantified target protein groups from 9,565 source
rows: 179 contaminant-only rows are excluded and 697 target rows with no
positive PHH donor value remain visible in the source audit rather than becoming
zeros. Of the retained groups, 5,110 were quantified in all seven donors. No
value is imputed. MaxQuant protein groups may contain multiple accessions or
genes, so the engine never silently collapses groups by gene.

## Functional use in the simulation

The engine does **not** draw one object for every protein molecule. Instead, the
selected gene-keyed reference inventory (for example `protein:ABCB11`) is
converted into a dimensionless model multiplier relative to its cohort-median
abundance:
`activity = copies / reference copies`. This multiplier scales the corresponding
transporter pathway: GLUT2 for whole-cell glucose exchange; BSEP for canalicular
bile-salt export; MRP2 for bilirubin-conjugate export; NTCP and Na+/K+-ATPase for
their represented transport functions. A zero count is an explicit functional
depletion; a missing entry means the reference healthy abundance.

This is a **relative-effect model**, not an absolute flux prediction. The current
base transport rates are explicitly recorded in reaction provenance as
`placeholder`: total copies per nucleus alone cannot establish transporter turnover,
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

### Coupled whole-cell transport validation

Bi et al. 2006 measured taurocholate handling in sandwich-cultured
cryopreserved human hepatocytes across five lots. The retained ranges are
apparent uptake `11-17 pmol/min/mg cell protein`, apparent intrinsic biliary
clearance `5.8-10 µL/min/mg cell protein`, and biliary excretion index `41-63%`.
These observations jointly reflect sinusoidal uptake, intracellular handling,
BSEP-mediated export, and an intact canalicular compartment. They are therefore
stored as a coupled whole-cell validation panel, not divided into invented NTCP,
OATP, or BSEP rate constants. Exact trajectory comparison remains disabled
until the simulation reproduces the source protocol and units.

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

Canalicular export is now explicitly mass-conserving. The legacy `bile_acids`
and `bilirubin_conjugates` ids denote intracellular retained cargo, while
`canalicular_bile_acids` and `canalicular_bilirubin_conjugates` receive the
exact BSEP/MRP2 export transfer. Canalicular cargo is outside the hepatocyte and
does not contribute to intracellular cholestatic stress. This is a structural
upgrade, not a kinetic calibration: CYP7A1 synthesis feedback and basolateral
escape remain absent until assay-matched rates can be identified.

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
2. **Protein groups are measured, but not molecule identities.** Supplementary
   Table 2 is now checksum-locked and transcribed donor by donor. A MaxQuant
   group can contain several accessions or genes; the group-level value cannot
   be split among isoforms without additional peptide evidence.
3. **Per nucleus is not per hepatocyte.** The workbook explicitly says copies
   per nucleus. Adult hepatocytes may be polyploid or binucleate, but the current
   evidence does not identify a donor-matched conversion from one reference
   nucleus to one simulated cell. The engine therefore does not apply an
   automatic ×2 or ploidy multiplier.
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
- **Wiśniewski JR, et al.** In-depth quantitative analysis and comparison of the
  human hepatocyte and hepatoma cell line HepG2 proteomes. *J Proteomics.* 2016.
  DOI `10.1016/j.jprot.2016.01.016`; PMID `26825538`. Official Supplementary
  Tables 1–2 are checksum locked; raw proteomics are MassIVE `MSV000079562` /
  ProteomeXchange `PXD001874` (CC0).
- **Human Protein Atlas**, proteinatlas.org (liver nTPM + localization);
  **UniProt** (canonical localization); **BioNumbers**.

The proteome values above are generated reproducibly by
`scripts/curate_wisniewski2016_phh_proteome.py`; source byte sizes and SHA-256
digests are validated before parsing.
