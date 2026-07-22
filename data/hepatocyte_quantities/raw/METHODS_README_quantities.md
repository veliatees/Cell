# Hepatocyte Quantitative-Parameter Harvest (7 categories) — Methods & README

**Purpose.** Second provenance-strict primary-literature harvest of ABSOLUTE QUANTITIES ("nicelikler") to
parameterize a human-hepatocyte whole-cell computational model. Complements the earlier cholestasis
experimental panel. Every value is traceable to a primary source; every absent value is explicitly
`NOT_REPORTED`, never inferred.

## 1. Categories harvested (as requested)

| Track | Requested category (TR → EN) |
|-------|------------------------------|
| Organelle cycles | Normalize organel fonksiyon döngüleri → organelle function-cycle turnover rates |
| Redox/ROS | Redoks/ROS kinetikleri → redox / ROS kinetics |
| GNG/Ketogenesis | Glukoneogenez ve ketogenez mutlak hızları → absolute gluconeogenesis & ketogenesis rates |
| Transporter flux | Absolute BSEP/MRP2/GLUT2 transport flux |
| Fate thresholds | Hasar, ölüm ve senesens zaman eşikleri → damage/death/senescence time thresholds |
| Donor variability | Donor-specific gen ekspresyonu → inter-donor gene/protein expression variability |
| Division probability | İnsan hepatosit bölünme olasılıkları → human hepatocyte division probabilities |

## 2. Deliverables

| File | Contents |
|------|----------|
| `hepatocyte_quantities_master.csv` / `.json` | All 168 rows, unified schema, tagged by track/category/organism_bucket |
| `organism_split_q/hepatocyte_quantities_human.csv` | 74 rows |
| `organism_split_q/hepatocyte_quantities_rat.csv` | 49 rows |
| `organism_split_q/hepatocyte_quantities_mouse.csv` | 8 rows |
| `organism_split_q/hepatocyte_quantities_HepaRG.csv` | 1 row |
| `organism_split_q/hepatocyte_quantities_other.csv` | 36 rows (heterologous/other-species: Xenopus oocyte, insect-cell vesicles, bovine, avian, primate, rabbit) |
| Per-track source tables | organelle_cycles, redox_ros_kinetics, gng_ketogenesis_rates, transporter_flux, fate_thresholds, donor_expression_variability, division_probability (each CSV+JSON) |

## 3. Master schema

`track, category, condition, time_h, endpoint, value, unit, mean_or_median, error, n,
organism_bucket, organism, model, assay, substrate_condition, temperature, pmid, doi, url,
figure_table, usable_for_human_wholecell, notes`

- **organism_bucket** ∈ {human, rat, mouse, HepaRG, other}. Heterologous expression systems (Xenopus oocyte,
  Sf9/HEK293 vesicles) and non-rodent species (bovine, avian, rabbit, macaque) are filed under **other** and
  never blended into a mammalian-species bucket. Primary hepatocytes of a species keep that species label.
- **usable_for_human_wholecell** is the sub-agent's per-row flag on whether the datum is directly usable for a
  human model or an indirect/non-human proxy.

## 4. Search & extraction strategy

Identical protocol to the cholestasis panel, run as 7 independent parallel harvests:
1. Primary literature + authoritative curated DBs only (PubMed/PMC, OpenAlex citation graph, bioRxiv,
   Human Protein Atlas, PRIDE). Reviews used only to locate primaries, which were opened and cited directly.
2. No inference/interpolation/figure-digitization. Missing = `NOT_REPORTED`.
3. Full provenance per row (value·unit·organism·model·assay·condition·temperature·uncertainty[SD/SEM/CI+n]·
   PMID·DOI·URL·figure/table).
4. Organisms kept strictly separate; human primary hepatocyte / human liver prioritized.

## 5. Coverage summary

| Track | Rows | Unique PMIDs | value=NOT_REPORTED |
|-------|------|--------------|--------------------|
| Organelle cycles | 22 | 9 | 0% |
| Redox/ROS | 25 | 20 | 24% |
| GNG/Ketogenesis | 30 | 25 | 43% |
| Transporter flux | 29 | 14 | 7% |
| Fate thresholds | 19 | 9 | 5% |
| Donor variability | 19 | 6 | 0% |
| Division probability | 24 | 8 | 8% |
| **Total** | **168** | **91** | — |

144/168 rows carry a reported value; 65 carry an explicit error term (SD/SEM/CI); 59 carry n.
Organism distribution: human 74, rat 49, other 36, mouse 8, HepaRG 1.
A high value-fill (low NOT_REPORTED %) here reflects that many values are qualitative/fractional or from
classic isotope studies whose point estimates ARE in the abstract; the *uncertainty* fields (error, n) are
much sparser — see per-track gaps.

## 6. Directly-usable human anchors (highlights)

- **GNG/ketogenesis:** postabsorptive human EGP ~85.6 mg·m⁻²·min⁻¹ (PMID 8904352) and 2.34 mg·min⁻¹·kg⁻¹
  (PMID 3891471); gluconeogenic fraction 54% at 16-h fast → 78% in cirrhosis (PMID 12633904); total ketone
  turnover ~294 µmol·min⁻¹·1.73m⁻² overnight-fasted (PMID 2336923).
- **Transporter flux:** human BSEP Km(taurocholate) 7.9±2.1 µM (PMID 12404240); human MRP2 E17βG S50 170±17 µM,
  Vmax 1447±137 pmol·mg⁻¹·min⁻¹ (PMID 28325716); human GLUT2 Km(2-DG) 11.2±1.1 mM (PMID 8987985).
- **Fate thresholds:** human PHH APAP 10 mM → NAC-rescue point-of-no-return between 15 h and 24 h (PMID
  24905542); GCDC necrosis at biliary ~1 mM, not serum ~20 µM (PMID 25636263).
- **Redox/ROS:** human peroxiredoxin-2 + H₂O₂ k = 1.3×10⁷ M⁻¹s⁻¹ (PMID 17329258); human Cu,Zn-SOD kcat
  1.30×10⁹ M⁻¹s⁻¹ at physiological ionic strength (PMID 16934676).
- **Donor variability:** human liver OATP1B1 15.0±6.0 fmol/µg (n=141, PMID ethnic-panel 2015); CYP3A 29-fold
  inter-donor range (n=31, Achour 2014).
- **Division probability:** quiescent adult human liver Ki-67 LI 2.5 (SD 3.2, PMID 9062874) / PCNA 0.4% (PMID
  1372584); regenerating human liver 3.8% phospho-H3⁺ mitotic (PMID 15633121).

## 7. Largest evidence gaps (verbatim from track harvests)

**Organelle cycles** — NO human primary data at all: every organelle turnover value is rat/mouse or
rat-hepatoma proxy. Mitochondrial half-life varies >5-fold by method (label re-utilization); most defensible
in-vivo figure is mouse-liver 1.83 d (PMID 18691181). No direct hepatocyte mitophagy/ER-phagy flux rate; no
biogenesis rate (organelles/cell/time).

**Redox/ROS** — Absolute human primary-hepatocyte GSH/GSSG pools and mitochondrial/peroxisomal H₂O₂
production/consumption fluxes not located with full-text numeric access (most are rat, in paywalled figures).
NADPH regeneration rate NOT_REPORTED. Catalase kcat / GPx Km,Vmax for human liver enzyme not captured as
absolute constants. Systematic full-text pull with journal access would recover many NOT_REPORTED numbers.

**GNG/ketogenesis** — No absolute per-cell/per-g GNG rate in human isolated hepatocytes or HepaRG; human data
are whole-body tracer EGP or *fractional* GNG only. Absolute per-min GNG/ketogenesis rates in perfused-liver
studies sit in paywalled figures/tables. AcAc vs BHB split production rates sparse.

**Transporter flux** — Turnover number (kcat, s⁻¹) NOT_REPORTED for BSEP, MRP2, GLUT2 in ANY primary source —
vesicle Vmax is per-mg protein, not per-transporter. Per-cell/per-hepatocyte absolute flux NOT_REPORTED. No
human GLUT2 Vmax (only Km from Xenopus oocyte).

**Fate thresholds** — SENESCENCE: no primary study reports a quantitative time-to-commitment/irreversibility
threshold for hepatocyte senescence (highest-priority gap). No single-cell MOMP-timing point-of-no-return in
human cells. Bile-acid apoptosis-vs-necrosis is a strong species divergence, so rodent apoptosis thresholds
are NOT usable human proxies.

**Donor variability** — No accessible primary donor-panel CV/fold-range for BSEP/ABCB11, MRP2/ABCC2 or NTCP;
none for GCK/PCK1/G6PC/GLUT2. Per-isoform CYP SD/CV often behind Elsevier paywall (captured as fold-range from
abstracts). No GTEx-liver eQTL expression-range dataset harvested within scope.

**Division probability** — No absolute division PROBABILITY per unit time for human hepatocytes (only
labeling-index snapshots; a rate needs labeling duration, rarely reported). No human post-hepatectomy
Ki-67/BrdU time-course (best is macaque proxy). % cells undergoing 0/1/2+ divisions not reported for human.

## 8. NOT_REPORTED policy

`NOT_REPORTED` = the primary source did not state the value in text accessible to this harvest (frequently
because it lives in a paywalled figure/table). It does NOT mean zero or not-applicable. These cells are left
for the modeler to fill by obtaining full-text access + digitizing the specific figure, or by supplying an
explicit modeling assumption recorded separately from this evidence layer. Nothing was estimated to avoid a
NOT_REPORTED.

## 9. Cross-cutting caveat for the modeler

The two categories most central to a *human* whole-cell model are the sparsest in human primary data:
**organelle turnover** (entirely non-human proxy) and **per-transporter turnover numbers** (absent for all
three transporters). Recommend treating these as calibration free-parameters constrained by the proxy ranges
here, rather than fixed inputs.
