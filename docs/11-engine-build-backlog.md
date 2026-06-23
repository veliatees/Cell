# Engine Build Backlog (living queue)

The ordered, trackable queue the build queue tracks. Derived from
[docs/08-depth-roadmap-and-literature.md](08-depth-roadmap-and-literature.md)
§"Uygulama sırası". Each item is one gated cycle: **source → implement →
conservation/behavior test → validation → commit → push**. Accuracy > coverage;
magnitudes flagged honestly; the visual never bends the science.

Definition of done for an item: a source-backed module + tests, full engine suite
green via `scripts/gate.sh`, sources recorded in `docs/sources.md`, committed and
pushed.

## Done (this programme)
- [x] Metabolic core: glycolysis, PPP, TCA/OXPHOS, urea cycle, redox
- [x] Central dogma + two-state promoter bursting
- [x] Hormonal glycogen control (insulin/glucagon/AMPK)
- [x] Membrane transport, calcium oscillations, lipid handling, secretion
- [x] DNA repair + apoptosis, cell cycle / division / regeneration
- [x] 1-D spatial reaction–diffusion
- [x] **Ketogenesis** (HMGCS2-limited; BDH1 redox readout) + fasting coupling
- [x] **Gluconeogenesis** (PYC/PEPCK/FBPase/G6Pase; reciprocal control; 6 ATP/glucose)

## Queue (in order)
- [x] **1a. Integrated fasting response.** `fasting_response.py` composes
  glycogenolysis + gluconeogenesis + ketogenesis under one `HormoneState`
  (shared `glucose_blood` + redox pools). FASTED raises both blood glucose and
  ketones; FED stores glucose as glycogen and makes neither. (compose_networks)
- [ ] **1b. Fuse into whole_cell.py core + snapshot.** Carry the fasting fuel
  program into the tracked whole-cell state and `engine-snapshot.json` so the
  browser shows it. Larger surgical cycle (309-line whole-cell test + snapshot).
- [x] **2. Amino-acid catabolism.** `amino_acid_catabolism.py`: transdeamination
  (glutaminase + ALT + AST + GDH) produces the urea cycle's two N donors (ammonia,
  aspartate) and gluconeogenic pyruvate; glutamate is the N hub; N + NAD conserved
  exactly. GDH modelled on NAD+ (NADP(H) gated). (Brosnan 2000; Karaca 2018)

> Note: `1b` (whole_cell.py + snapshot fusion) is deferred to an **attended** cycle —
> too much regression risk (snapshot drives the browser) for autonomous execution.
> Tech debt: `_pseudo_first_order` is now duplicated in ketogenesis/gluconeogenesis/
> amino_acid_catabolism — lift into `reactions.py` during an attended refactor.
- [x] **3. Glycerol → gluconeogenesis.** `glycerol_gluconeogenesis.py`: glycerol
  kinase + GPD1 entry at DHAP (below PEP), so glucose costs ~2 ATP vs pyruvate's 6;
  2:1 carbon; fasted/fed reciprocal control; adenine+NAD conserved. Completes the
  fate of lipolysis (fat→ketones, glycerol→glucose). (Lal 2018; glycerol/G3P review)
- [x] **4. Validation panel expansion.** `validation/hmdb_ranges.py`: 11 curated
  HMDB physiological concentration ranges (glucose, lactate, pyruvate, alanine,
  glutamine, glutamate, β-OHB, acetoacetate, ammonia, urea, glycerol) as
  `ReferenceRange`s + a `classify_concentration` checker. Gated classes excluded.
  Ready to score once pathways are wired into the validated whole-cell run (1b).
  (HMDB 5.0)
- [ ] **5. Ground illustrative magnitudes.** _(ATTENDED)_ Needs the molar-volume +
  Michaelis-Menten re-architecture so BRENDA/SABIO-RK Km/kcat are meaningful; the
  normalized-scale modules can't carry real Vmax. A foundational decision, not an
  unattended cycle. (BRENDA, SABIO-RK)
- [x] **6. Signaling depth.** `hormonal_gene_regulation.py`: gene-level reciprocal
  control — glucagon→CREB/PGC-1 induces gluconeogenic enzyme (PEPCK/G6Pase),
  insulin→SREBP-1c induces lipogenic enzyme (ACC/FASN) and suppresses gluconeogenic
  (FOXO1). Smooth insulin dose-response; the mechanistic basis of the flux modules'
  drive multiplier. (Herzig 2001; Horton 2002)
- [ ] **7. Transport kinetics.** _(ATTENDED)_ The six transporters already exist in
  `transport.py` with vectorial flux + BSEP cholestasis; what remains is grounding
  Km/Vmax (needs the molar/MM re-architecture, item 5) and membrane-potential
  coupling (item 8) — both attended.
- [ ] **8. Calcium / electrophysiology depth.** _(ATTENDED — large: IP3R Markov clusters + membrane potential)_ Stochastic IP₃R Markov clusters;
  membrane potential from Na/K-ATPase + K⁺ channel. (IP3R stochastic models)
- [x] **9. Lipid depth (malonyl-CoA node).** `malonyl_coa_node.py`: ACC makes
  malonyl-CoA (fed, committed DNL), FASN→palmitate, MCD clears it (fasted/AMPK);
  malonyl-CoA inhibits CPT1, gating β-oxidation (McGarry & Foster). The
  metabolite-level reason fed is anti-ketogenic. Dose-dependent CPT1 inhibition;
  fed builds malonyl + does DNL, fasted clears it; adenine conserved.
  > Remaining lipid depth (VLDL ApoB/MTP biogenesis, quantitative steatosis
  > threshold) folds into the attended whole-cell integration.
- [ ] **10. DNA-repair depth.** _(ATTENDED — large: quantitative p53/p21 fate network)_ Quantitative NHEJ/HR + p53/p21 fate network feeding
  apoptosis. (PLoS Comput Biol stochastic NHEJ+p53)
- [ ] **11. Spatial fusion → RDME.** _(ATTENDED — very large: 3-D voxel RDME)_ Fuse 1-D spatial with the real reaction network
  (per-species diffusion); then 3-D voxel RDME (low-copy SSA / high-copy CLE per
  voxel), sinusoidal↔canalicular gradients, mito ATP microdomains. (4D WCM, Lattice Microbes)



## v1.0 migration (molar-grounded, integrated, validated, visualized)

Tracking the re-architecture from "normalized/qualitative" to a real-units model.

- [x] **M1** — composition safety guards (no double-counted flux; cofactor-pool audit).
- [x] **M2 (first-order modules)** — migrated to the real cytosolic volume + mM seeds:
  `lipid.py`, `signaling.py`, `hormonal_gene_regulation.py`. These were scale-only
  flips (first/zeroth-order rates are volume-independent or rescaled by N_A·V).
- [x] **M4 — scale migration of the bi-substrate modules (DONE).** All five migrated
  to the real cytosolic volume + mM seeds; `_pseudo_first_order` ignores volume so
  kinetics were unchanged. Every pathway now outputs real mM concentrations
  (HMDB-scoreable): `ketogenesis` (bHB ~2.1 mM), `gluconeogenesis` (glucose 3 mM),
  `glycerol_gluconeogenesis`, `amino_acid_catabolism`, `malonyl_coa_node` (CPT1 Ki
  expressed in mM). 263 tests green.
- [ ] **M3 — kinetics fidelity refinement (LATER, not a blocker).** Convert the
  pseudo-first-order form to true `michaelis_menten` with curated human/liver Km/kcat
  where it improves HMDB scores. Honest flagged placeholders on the real molar scale
  are acceptable until curated (the `glycolysis.py` pattern).
- [ ] **M5** — fuse all migrated pathways into `whole_cell.py`; rebalance shared
  ATP/CoA/NAD pools; remove lumped reactions superseded by detailed pathways.
- [ ] **M6** — turn on HMDB validation scoring against the integrated steady state.
- [ ] **M7** — browser shows live concentrations + in-range badges.

Design lens (per user): apply the **rise-peak-decline / Gaussian life-arc** to
time-varying inputs and capacities (e.g. nutrient score low→high→low) rather than
flat constants, once the agency/senescence layer is added post-v1.0.
