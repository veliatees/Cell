# Scientifically Unidentifiable & Session-Inaccessible Parameters

This document separates two fundamentally different reasons a requested field is empty in this dataset. Conflating them would misrepresent the state of the evidence.

- **Category A — Unidentifiable IN PRINCIPLE:** No existing in-vivo human method can produce the value; it is not a matter of finding the right paper.
- **Category B — Inaccessible THIS SESSION:** The value plausibly exists in the primary literature but could not be retrieved/read here (scanned image-only tables, paywalls, no machine-readable body). Recoverable with library access to the physical tables.

---

## Category A — Unidentifiable in principle (biological/methodological limits)

### A1. Single-hepatocyte substrate flux
Human in-vivo methods resolve flux at the **organ** (arteriovenous balance across the splanchnic bed × blood flow) or **whole-body** (isotopic rate of appearance) level. There is **no** in-vivo human method that measures uptake or release by an individual hepatocyte. Per-cell numbers can only be *estimated* by dividing an organ flux by an assumed hepatocyte count — which imports rodent/drug-metabolism-pooled constants (see conversion_scaffold.json) and manufactures false precision. **All `applicable_to_single_hepatocyte` fields are therefore `false`, and all per-hepatocyte values are `null`.**

### A2. True portal-vein substrate concentrations in healthy fasting humans
The portal vein is not cannulable in healthy volunteers for ethical reasons. Portal blood is obtainable only:
- intra-operatively in **surgical** patients (this session: PMID 18703642 ammonia/glutamine/glutamate; PMID 2189767 gut glucose/lactate — both explicitly **not** healthy fasting cohorts), or
- via trans-hepatic radiology in **disease** states.
Therefore portal-vein concentrations for the target healthy population are unidentifiable in principle. Where portal data exist they carry a surgical-cohort caveat and describe the **gut/portal-drained viscera**, not isolated hepatocytes.

### A3. Liver-specific (vs whole-splanchnic-bed) balances from peripheral catheterization
Hepatic-venous catheterization measures the **whole splanchnic bed** (gut + liver + spleen + pancreas). Isolating the liver's own contribution requires simultaneous portal sampling (see A2). So for the classic catheter studies, a strictly *liver-specific* net flux is not identifiable — the value is a splanchnic-bed balance. Records are tagged `bed_scope` accordingly (`whole_splanchnic_bed`, `systemic_whole_body`, `gut_portal_drained_viscera`, `liver_specific` only where the source itself isolated the liver isotopically, e.g. hepatic = systemic − renal in PMID 9781626 / 9843908).

### A4. GLUT2 transport kinetics (Km / Vmax) in human hepatocytes in vivo
The GLUT2 review (PMID 25421524) establishes GLUT2 as the hepatocyte glucose transporter and its role in sensing, but transport-kinetic constants for human hepatocytes in vivo are not measured by any organ-flux method. The coverage-matrix "GLUT2 flux" cell is legitimately empty.

### A5. Direct hepatocyte intracellular metabolite concentrations
In-vivo human data are extracellular (arterial/venous plasma or blood). Intracellular hepatocyte concentrations are not obtainable non-invasively; the requested "intracellular applicability" is therefore null.

---

## Category B — Inaccessible this session (recoverable with full-text/table access)

### B1. Dispersion (SD/SEM) and exact n for most records
Values not stated in the machine-readable abstract are null. The primary papers **do** report these in their tables — but those tables are scanned page-images (JCI 1971–1984) or behind paywalls (AJP/Diabetes/Metabolism). Recoverable from the physical/PDF tables.

### B2. Exact table/figure locators
Because tables were image-only, `source_locator` is `"abstract"` for nearly all records rather than a specific table number. The precise table/figure exists in each paper and can be cited with full-text access.

### B3. Per-subject demographics (age, sex, BMI, health screening)
Abstracts rarely state cohort age/sex/BMI numerically. Present in the papers' Methods sections; null here. (Sex was recoverable for two cohorts — PMID 10331398, 11788375: male.)

### B4. Arterial vs hepatic-vein split of a reported net balance
Several abstracts give only the net balance or only the arterial concentration. The paired A and HV values exist in the tables (image-only this session) → null.

### B5. Fed-state and prolonged-fasted coverage for ammonia and urea
- **Ammonia:** only postabsorptive resting data retrieved (PMID 4042572; 18703642 intra-operative). Fed and prolonged-fast ammonia balances not located in accessible text this session.
- **Urea:** PMID 7372062 (the tracer urea-synthesis-rate method paper) has **no DOI and no retrievable abstract** this session → fully null. Urea synthesis rates across nutritional states exist in the literature but were not machine-accessible here.

### B6. Glutamate
Requested with glutamine; appears only inside the compound descriptor of PMID 18703642 (portal/hepatic ammonia-glutamine-glutamate study) with no standalone numeric glutamate flux in the abstract → null.

### B7. Fed-state ketones
Ketone data retrieved are prolonged-fast (PMID 4430728) and exercise/diabetes (6715541, 1133176, 201421). Fed-state (ketone-suppressed) values not separately quantified in accessible text.

---

## Summary count

| Requested field class | Status | Reason category |
|---|---|---|
| Per-hepatocyte flux (all metabolites, all states) | null everywhere | A1 |
| Portal-vein conc, healthy fasting | null | A2 |
| Liver-specific balance from catheter studies | null (tagged splanchnic) | A3 |
| GLUT2 Km/Vmax human in vivo | null | A4 |
| Intracellular hepatocyte conc | null | A5 |
| SD/SEM, exact n (most records) | null | B1 |
| Exact table/figure locator | "abstract" | B2 |
| Per-subject age/sex/BMI | mostly null | B3 |
| A vs HV split | often null | B4 |
| Ammonia/urea in fed & prolonged states | null/sparse | B5 |
| Standalone glutamate flux | null | B6 |
| Fed-state ketones | null | B7 |

**Bottom line:** The healthy-human hepatocyte flux picture that IS identifiable is an **organ-level / whole-body** picture (splanchnic and systemic balances, isotopic turnover), not a per-cell or portal-resolved one. The per-cell and portal fields are empty by biological necessity (Category A), not merely by this session's retrieval limits. The dispersion/demographic/table-locator gaps (Category B) are the ones a repeat pass with institutional full-text access could fill.
