# Source-by-Source Audit

**Task:** Substrate transport/flux in healthy adult human liver across fed, postabsorptive, and prolonged-fasted states.

**How to read this audit:** Each entry states what was *retrieved and read this session*, which *verbatim values* were extractable, and what remains *inaccessible*. The dominant limitation is that the primary human-catheterization literature (Felig/Wahren, Ahlborg, Garber/Boden, Hagenfeldt, Eriksson, Wahren/Sato, Nurjhan) is deposited in PubMed Central only as **scanned page-images**: abstract text is machine-readable but the quantitative data **tables are image-only and could not be parsed this session**. Paywalled journals (AJP, Diabetes, Metabolism) returned rich quantitative abstracts but no table access. Consequently most records carry `source_locator='abstract'` and their SD/SEM, n, and per-subject demographic fields are null by **access limitation**, distinct from biological unidentifiability (documented separately in unidentifiable_parameters.md).

---

## PMID 5097575 — Influence of endogenous insulin secretion on splanchnic glucose and amino acid metabolism in man.
- **Ref:** J Clin Invest (1971); DOI: 10.1172/JCI106659
- **Access tier:** abstract_only (PMC scanned page-images; data tables image-only, INACCESSIBLE this session)
- **Cohort/health:** normal subjects, basal postabsorptive — health_status=`healthy`
- **Records extracted (1):**
    - glucose | postabsorptive | splanchnic_balance/production: **3.4 mg/kg/min** (dispersion=null, n=null, whole_splanchnic_bed)
  - *Fields null by access limit:* SD/SEM (unless in abstract), subject-level age/sex/BMI, exact table/figure numbers, arterial vs portal vs hepatic-vein split (unless stated).

## PMID 4430728 — Hepatic ketogenesis and gluconeogenesis in humans.
- **Ref:** J Clin Invest (1974); DOI: 10.1172/JCI107839
- **Access tier:** abstract_only (PMC scanned page-images; data tables image-only, INACCESSIBLE this session)
- **Cohort/health:** 5 subjects after 3 days starvation — health_status=`fasting_study_subjects_health_unspecified`
- **Records extracted (2):**
    - glucose | prolonged_fast(3 days) | splanchnic_balance/net_output_cumulative: **123 g/24h** (dispersion=null, n=5, whole_splanchnic_bed)
    - betahydroxybutyrate+acetoacetate | prolonged_fast(3 days) | splanchnic_balance/production_cumulative: **115 g/24h** (dispersion=null, n=5, whole_splanchnic_bed)
  - *Fields null by access limit:* SD/SEM (unless in abstract), subject-level age/sex/BMI, exact table/figure numbers, arterial vs portal vs hepatic-vein split (unless stated).

## PMID 1126590 — Influence of oral glucose ingestion on splanchnic glucose and gluconeogenic substrate metabolism in man.
- **Ref:** Diabetes (1975); DOI: 10.2337/diab.24.5.468
- **Access tier:** abstract_only (paywalled; quantitative abstract retrieved, tables inaccessible)
- **Cohort/health:** 10 healthy subjects, 3 h after 100 g oral glucose — health_status=`healthy`
- **Records extracted (2):**
    - glucose | fed(oral 100g glucose) | splanchnic_balance/net_output_cumulative: **40 g/3h** (dispersion=±3 (SEM), n=10, whole_splanchnic_bed)
    - pyruvate | fed(100g oral glucose) | splanchnic_balance/direction_change_qualitative: **null** (dispersion=null, n=10, whole_splanchnic_bed)
  - *Fields null by access limit:* SD/SEM (unless in abstract), subject-level age/sex/BMI, exact table/figure numbers, arterial vs portal vs hepatic-vein split (unless stated).

## PMID 1133176 — Splanchnic and leg exchange of glucose, amino acids, and free fatty acids during exercise in diabetes mellitus.
- **Ref:** J Clin Invest (1975); DOI: 10.1172/JCI108050
- **Access tier:** abstract_only (PMC scanned page-images; data tables image-only, INACCESSIBLE this session)
- **Cohort/health:** 8 healthy controls (exercise study) — health_status=`healthy_controls`
- **Records extracted (1):**
    - betahydroxybutyrate | postabsorptive | arterial/concentration: **null** (dispersion=null, n=8, whole_splanchnic_bed)
  - *Fields null by access limit:* SD/SEM (unless in abstract), subject-level age/sex/BMI, exact table/figure numbers, arterial vs portal vs hepatic-vein split (unless stated).

## PMID 7372062 — A tracer method for measuring rate of urea synthesis in normal and cirrhotic subjects.
- **Ref:** Gastroenterology (1980); DOI: nan
- **Access tier:** no_abstract_available (no DOI; not retrievable this session)
- **Cohort/health:** normal + cirrhotic subjects — health_status=`mixed_normal_and_cirrhotic`
- **Records extracted (1):**
    - urea | postabsorptive | systemic/synthesis_rate: **null** (dispersion=null, n=null, systemic_whole_body)
  - *Fields null by access limit:* SD/SEM (unless in abstract), subject-level age/sex/BMI, exact table/figure numbers, arterial vs portal vs hepatic-vein split (unless stated).

## PMID 6642279 — Splanchnic exchange of glucose, amino acids and free fatty acids in patients with chronic inflammatory bowel disease.
- **Ref:** Gut (1983); DOI: 10.1136/gut.24.12.1161
- **Access tier:** abstract_only (PMC scanned page-images; data tables image-only, INACCESSIBLE this session)
- **Cohort/health:** control subjects (IBD study control arm) — health_status=`healthy_controls`
- **Records extracted (1):**
    - NEFA | postabsorptive | splanchnic_balance/ketone_fraction_of_FFA_uptake: **20 % of splanchnic FFA uptake** (dispersion=±5 (SEM), n=null, whole_splanchnic_bed)
  - *Fields null by access limit:* SD/SEM (unless in abstract), subject-level age/sex/BMI, exact table/figure numbers, arterial vs portal vs hepatic-vein split (unless stated).

## PMID 6715541 — Turnover and splanchnic metabolism of free fatty acids and ketones in insulin-dependent diabetics at rest and in response to exercise.
- **Ref:** J Clin Invest (1984); DOI: 10.1172/JCI111340
- **Access tier:** abstract_only (PMC scanned page-images; data tables image-only, INACCESSIBLE this session)
- **Cohort/health:** control subjects (6 healthy) — value stated is DIABETIC group; see notes — health_status=`see_notes`
- **Records extracted (1):**
    - NEFA | postabsorptive | arterial/concentration: **967 µmol/l** (dispersion=±110 (SEM), n=6, systemic_whole_body)
  - *Fields null by access limit:* SD/SEM (unless in abstract), subject-level age/sex/BMI, exact table/figure numbers, arterial vs portal vs hepatic-vein split (unless stated).

## PMID 4042572 — Ammonia metabolism during exercise in man.
- **Ref:** Clin Physiol (1985); DOI: 10.1111/j.1475-097x.1985.tb00753.x
- **Access tier:** abstract_only (paywalled; quantitative abstract retrieved, tables inaccessible)
- **Cohort/health:** 11 healthy subjects at rest — health_status=`healthy`
- **Records extracted (2):**
    - ammonia | postabsorptive | arterial/concentration: **22 µmol/l** (dispersion=±2 (SEM), n=11, whole_splanchnic_bed)
    - ammonia | postabsorptive | splanchnic_balance/net_uptake: **12 µmol/min** (dispersion=±2 (SEM), n=11, whole_splanchnic_bed)
  - *Fields null by access limit:* SD/SEM (unless in abstract), subject-level age/sex/BMI, exact table/figure numbers, arterial vs portal vs hepatic-vein split (unless stated).

## PMID 2653926 — Predominant role of gluconeogenesis in increased hepatic glucose production in NIDDM.
- **Ref:** Diabetes (1989); DOI: 10.2337/diab.38.5.550
- **Access tier:** abstract_only (paywalled; quantitative abstract retrieved, tables inaccessible)
- **Cohort/health:** 9 nondiabetic volunteers (control arm of NIDDM study) — health_status=`healthy`
- **Records extracted (1):**
    - glucose | postabsorptive | systemic/hepatic_glucose_output: **12.0 µmol/kg/min** (dispersion=±0.6 (SEM), n=9, systemic_whole_body)
  - *Fields null by access limit:* SD/SEM (unless in abstract), subject-level age/sex/BMI, exact table/figure numbers, arterial vs portal vs hepatic-vein split (unless stated).

## PMID 2189767 — Gut exchange of glucose and lactate in basal state and after oral glucose ingestion in postoperative patients.
- **Ref:** Diabetes (1990); DOI: 10.2337/diab.39.6.747
- **Access tier:** abstract_only (paywalled; quantitative abstract retrieved, tables inaccessible)
- **Cohort/health:** 5 postoperative patients (gallbladder/colon/liver surgery) — health_status=`postoperative_patients_not_healthy`
- **Records extracted (2):**
    - lactate | fed(100g oral glucose) | portal_vein/net_balance_A-PV: **-0.16 mM** (dispersion=±0.06 (SEM), n=5, gut_portal_drained_viscera)
    - pyruvate | fed(100g oral glucose) | portal_vein/net_balance_A-PV: **null** (dispersion=null, n=5, gut_portal_drained_viscera)
  - *Fields null by access limit:* SD/SEM (unless in abstract), subject-level age/sex/BMI, exact table/figure numbers, arterial vs portal vs hepatic-vein split (unless stated).

## PMID 1729269 — Increased lipolysis and its consequences on gluconeogenesis in non-insulin-dependent diabetes mellitus.
- **Ref:** J Clin Invest (1992); DOI: 10.1172/JCI115558
- **Access tier:** abstract_only (PMC scanned page-images; data tables image-only, INACCESSIBLE this session)
- **Cohort/health:** 16 nondiabetic age/weight-matched volunteers (control arm) — health_status=`healthy`
- **Records extracted (1):**
    - glycerol | postabsorptive | systemic/rate_of_appearance: **1.62 µmol/kg/min** (dispersion=±0.08 (SEM), n=16, systemic_whole_body)
  - *Fields null by access limit:* SD/SEM (unless in abstract), subject-level age/sex/BMI, exact table/figure numbers, arterial vs portal vs hepatic-vein split (unless stated).

## PMID 8997232 — Glycerol production and utilization in humans: sites and quantitation.
- **Ref:** Am J Physiol (1996); DOI: 10.1152/ajpendo.1996.271.6.E1110
- **Access tier:** abstract_only (paywalled; quantitative abstract retrieved, tables inaccessible)
- **Cohort/health:** ten 60h-fasted healthy subjects — health_status=`healthy`
- **Records extracted (1):**
    - glycerol | prolonged_fast(60h) | systemic/rate_of_appearance: **5.11 µmol/kg/min** (dispersion=null, n=10, systemic_whole_body)
  - *Fields null by access limit:* SD/SEM (unless in abstract), subject-level age/sex/BMI, exact table/figure numbers, arterial vs portal vs hepatic-vein split (unless stated).

## PMID 9843908 — Effects of physiological hyperinsulinemia on systemic, renal, and hepatic substrate metabolism.
- **Ref:** Am J Physiol (1998); DOI: 10.1152/ajprenal.1998.275.6.F915
- **Access tier:** abstract_only (paywalled; quantitative abstract retrieved, tables inaccessible)
- **Cohort/health:** 9 normal volunteers, basal postabsorptive — health_status=`healthy`
- **Records extracted (2):**
    - glucose | postabsorptive | splanchnic_balance/hepatic_glucose_release: **8.7 µmol/kg/min** (dispersion=±0.4 (SEM), n=9, whole_splanchnic_bed)
    - glutamine | postabsorptive | splanchnic_balance/gluconeogenesis_rate: **0.35 µmol/kg/min** (dispersion=±0.02 (SEM), n=9, liver_specific)
  - *Fields null by access limit:* SD/SEM (unless in abstract), subject-level age/sex/BMI, exact table/figure numbers, arterial vs portal vs hepatic-vein split (unless stated).

## PMID 9612239 — Human kidney and liver gluconeogenesis: evidence for organ substrate selectivity.
- **Ref:** Am J Physiol (1998); DOI: 10.1152/ajpendo.1998.274.5.E817
- **Access tier:** abstract_only (paywalled; quantitative abstract retrieved, tables inaccessible)
- **Cohort/health:** 9 normal postabsorptive volunteers — health_status=`healthy`
- **Records extracted (2):**
    - alanine | postabsorptive | systemic/gluconeogenesis_incorporation: **51 µmol/min** (dispersion=±6 (SEM), n=9, systemic_whole_body)
    - glutamine | postabsorptive | systemic/gluconeogenesis_incorporation: **37 µmol/min** (dispersion=±2 (SEM), n=9, systemic_whole_body)
  - *Fields null by access limit:* SD/SEM (unless in abstract), subject-level age/sex/BMI, exact table/figure numbers, arterial vs portal vs hepatic-vein split (unless stated).

## PMID 9781626 — Effects of glucagon on renal and hepatic glutamine gluconeogenesis in normal postabsorptive humans.
- **Ref:** Metabolism (1998); DOI: 10.1016/s0026-0495(98)90328-6
- **Access tier:** abstract_only (Elsevier XML stub, no body)
- **Cohort/health:** 6 normal postabsorptive subjects (pre-glucagon control) — health_status=`healthy`
- **Records extracted (1):**
    - glutamine | postabsorptive | hepatic_vein/gluconeogenesis_rate: **0.11 µmol/kg/min** (dispersion=±0.02 (SEM), n=6, liver_specific)
  - *Fields null by access limit:* SD/SEM (unless in abstract), subject-level age/sex/BMI, exact table/figure numbers, arterial vs portal vs hepatic-vein split (unless stated).

## PMID 10334304 — Contributions by kidney and liver to glucose production in the postabsorptive state and after 60 h of fasting.
- **Ref:** Diabetes (1999); DOI: 10.2337/diabetes.48.2.292
- **Access tier:** abstract_only (paywalled; quantitative abstract retrieved, tables inaccessible)
- **Cohort/health:** healthy individuals, postabsorptive — health_status=`healthy`
- **Records extracted (2):**
    - glucose | postabsorptive | splanchnic_balance/net_output: **9.8 µmol/kg/min** (dispersion=±0.8 (SEM), n=null, whole_splanchnic_bed)
    - glucose | prolonged_fast(60 h) | splanchnic_balance/net_output: **5.8 µmol/kg/min** (dispersion=±0.7 (SEM), n=null, whole_splanchnic_bed)
  - *Fields null by access limit:* SD/SEM (unless in abstract), subject-level age/sex/BMI, exact table/figure numbers, arterial vs portal vs hepatic-vein split (unless stated).

## PMID 10331398 — Splanchnic and leg substrate exchange after ingestion of a natural mixed meal in humans.
- **Ref:** Diabetes (1999); DOI: 10.2337/diabetes.48.5.958
- **Access tier:** abstract_only (paywalled; quantitative abstract retrieved, tables inaccessible)
- **Cohort/health:** 11 male subjects, basal before mixed meal — health_status=`healthy`
- **Records extracted (2):**
    - glucose | postabsorptive(basal, pre-meal) | splanchnic_balance/net_balance: **-6.7 µmol/kg/min** (dispersion=±0.5 (SEM), n=11, whole_splanchnic_bed)
    - lactate | postabsorptive(basal) | splanchnic_balance/net_uptake: **3.2 µmol/kg/min** (dispersion=±0.6 (SEM), n=11, whole_splanchnic_bed)
  - *Fields null by access limit:* SD/SEM (unless in abstract), subject-level age/sex/BMI, exact table/figure numbers, arterial vs portal vs hepatic-vein split (unless stated).

## PMID 10831183 — Regulation of splanchnic and renal substrate supply by insulin in humans.
- **Ref:** Metabolism (2000); DOI: 10.1016/s0026-0495(00)80048-7
- **Access tier:** abstract_only (Elsevier XML stub, no body)
- **Cohort/health:** 10 healthy subjects, overnight fast — health_status=`healthy`
- **Records extracted (2):**
    - glucose | postabsorptive | splanchnic_balance/hepatic_glucose_production: **10.4 µmol/kg/min** (dispersion=±1.1 (SEM), n=10, whole_splanchnic_bed)
    - alanine | postabsorptive | splanchnic_balance/net_uptake: **1.8 µmol/kg/min** (dispersion=±0.1 (SEM), n=10, whole_splanchnic_bed)
  - *Fields null by access limit:* SD/SEM (unless in abstract), subject-level age/sex/BMI, exact table/figure numbers, arterial vs portal vs hepatic-vein split (unless stated).

## PMID 11788375 — Role of human liver, kidney, and skeletal muscle in postprandial glucose homeostasis.
- **Ref:** Am J Physiol Endocrinol Metab (2002); DOI: 10.1152/ajpendo.00032.2001
- **Access tier:** abstract_only (paywalled; quantitative abstract retrieved, tables inaccessible)
- **Cohort/health:** 10 normal volunteers, 75 g oral glucose — health_status=`healthy`
- **Records extracted (1):**
    - glucose | fed(75g oral glucose) | splanchnic_balance/uptake_cumulative: **22 g/4.5h** (dispersion=±2 (SEM); 30±3% of load, n=10, whole_splanchnic_bed)
  - *Fields null by access limit:* SD/SEM (unless in abstract), subject-level age/sex/BMI, exact table/figure numbers, arterial vs portal vs hepatic-vein split (unless stated).

## PMID 11788376 — Renal substrate exchange and gluconeogenesis in normal postabsorptive humans.
- **Ref:** Am J Physiol Endocrinol Metab (2002); DOI: 10.1152/ajpendo.00116.2001
- **Access tier:** abstract_only (paywalled; quantitative abstract retrieved, tables inaccessible)
- **Cohort/health:** 24 postabsorptive humans — health_status=`healthy`
- **Records extracted (2):**
    - lactate | postabsorptive | systemic/gluconeogenesis_rate: **1.97 µmol/kg/min** (dispersion=±0.12 (SEM), n=24, systemic_whole_body)
    - glycerol | postabsorptive | systemic/gluconeogenesis_rate: **null** (dispersion=null, n=24, systemic_whole_body)
  - *Fields null by access limit:* SD/SEM (unless in abstract), subject-level age/sex/BMI, exact table/figure numbers, arterial vs portal vs hepatic-vein split (unless stated).

## PMID 18703642 — The gut does not contribute to systemic ammonia release in humans without portosystemic shunting.
- **Ref:** Am J Physiol Gastrointest Liver Physiol (2008); DOI: 10.1152/ajpgi.00333.2007
- **Access tier:** abstract_only (paywalled; quantitative abstract retrieved, tables inaccessible)
- **Cohort/health:** 21 surgical patients with normal liver function — health_status=`surgical_patients_normal_liver`
- **Records extracted (1):**
    - ammonia | postabsorptive(intraoperative) | portal_vein/interorgan_trafficking_qualitative: **null** (dispersion=null, n=21, gut_portal_and_hepatic)
  - *Fields null by access limit:* SD/SEM (unless in abstract), subject-level age/sex/BMI, exact table/figure numbers, arterial vs portal vs hepatic-vein split (unless stated).
---

## Sources retrieved but yielding NO verbatim numeric record (6)

These shortlisted sources were retrieved and read this session but produced no MEASURED record, for the stated reason. They remain part of the evidence base (method references / qualitative findings) and are listed here for completeness.

### PMID 5032528 — Splanchnic and peripheral glucose and amino acid metabolism in diabetes mellitus.
- J Clin Invest (1972); DOI 10.1172/JCI106989 | access: abstract_only (PMC scanned page-images; data tables image-only, INACCESSIBLE this session)
- **No-record reason:** Splanchnic glucose/AA in diabetes vs controls. Abstract gives only relative/percentage comparisons (precursor uptake could account for 32% of HGO in diabetics vs 20% controls; fractional-extraction fold-changes). No absolute healthy-control flux value with units stated in abstract → no verbatim numeric record.

### PMID 4815076 — Substrate turnover during prolonged exercise in man. Splanchnic and leg metabolism of glucose, free fatty acids, and amino acids.
- J Clin Invest (1974); DOI 10.1172/JCI107645 | access: abstract_only (PMC scanned page-images; data tables image-only, INACCESSIBLE this session)
- **No-record reason:** Ahlborg/Felig prolonged exercise. Rich abstract but values are exercise-dynamic percentages/fold-changes and one cumulative '75 g in 4 h' splanchnic output that is EXERCISE, not a resting nutritional-state balance. Exercise physiology falls outside the three resting nutritional states; retained as a source but no resting verbatim record extracted. (Table values are scanned/image-only.)

### PMID 4639017 — Uptake of individual free fatty acids by skeletal muscle and liver in man.
- J Clin Invest (1972); DOI 10.1172/JCI107043 | access: abstract_only (PMC scanned page-images; data tables image-only, INACCESSIBLE this session)
- **No-record reason:** Hagenfeldt individual-FFA uptake. Abstract is entirely qualitative (fractional-uptake patterns by chain length/unsaturation; small negative A-portal differences). No absolute concentration or flux number in abstract → no verbatim numeric record. Notably documents that arterial-hepatic-venous FFA differences mainly reflect hepatic uptake (small portal-vein contribution).

### PMID 201421 — Regulation of gluconeogenesis and ketogenesis during rest and exercise in diabetic subjects and normal men.
- Clin Sci Mol Med (1977); DOI 10.1042/cs0530411 | access: abstract_only (paywalled; quantitative abstract retrieved, tables inaccessible)
- **No-record reason:** Sestoft/Trap-Jensen GNG & ketogenesis rest+exercise. Abstract reports only relationships (linear load-vs-uptake regressions; ketogenesis 2-fold higher per NEFA load in diabetics). No absolute healthy flux number with units → no verbatim record.

### PMID 10817164 — Quantifying the contribution of gluconeogenesis to glucose production in fasted human subjects using stable isotopes.
- Proc Nutr Soc (1999); DOI 10.1017/s0029665199001275 | access: full_text_pdf (review, qualitative)
- **No-record reason:** Landau review — methods for quantifying GNG contribution using 2H2O. Full text retrieved (PDF) but purely methodological/qualitative; scanned for hepatic/splanchnic µmol|mmol values = zero. Cited as method reference only.

### PMID 25421524 — GLUT2, glucose sensing and glucose homeostasis.
- Diabetologia (2014); DOI 10.1007/s00125-014-3451-1 | access: full_text_pdf (review, qualitative)
- **No-record reason:** Thorens GLUT2 review — full text retrieved (PDF). Qualitative molecular physiology of GLUT2 expression/sensing; no transport-kinetic or flux numbers (no Km, no transport capacity). Cited for GLUT2 tissue expression/sensing role only; the coverage-matrix GLUT2 'flux' cell remains legitimately empty.
