# Engine Build Backlog (living queue)

The ordered, trackable queue the agent loop works through. Derived from
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
- [ ] **7. Transport kinetics.** Ground NTCP, OATP1B1/3, GLUT2, BSEP, MRP2,
  Na⁺/K⁺-ATPase with literature Km/Vmax; couple to membrane potential.
- [ ] **8. Calcium / electrophysiology depth.** _(ATTENDED — large: IP3R Markov clusters + membrane potential)_ Stochastic IP₃R Markov clusters;
  membrane potential from Na/K-ATPase + K⁺ channel. (IP3R stochastic models)
- [ ] **9. Lipid depth.** DNL (ACC/FASN), VLDL biogenesis (ApoB100/MTP), steatosis
  threshold; link to ketogenesis acetyl-CoA. (iHepatocytes2322)
- [ ] **10. DNA-repair depth.** _(ATTENDED — large: quantitative p53/p21 fate network)_ Quantitative NHEJ/HR + p53/p21 fate network feeding
  apoptosis. (PLoS Comput Biol stochastic NHEJ+p53)
- [ ] **11. Spatial fusion → RDME.** _(ATTENDED — very large: 3-D voxel RDME)_ Fuse 1-D spatial with the real reaction network
  (per-species diffusion); then 3-D voxel RDME (low-copy SSA / high-copy CLE per
  voxel), sinusoidal↔canalicular gradients, mito ATP microdomains. (4D WCM, Lattice Microbes)

## Loop protocol
1. Pick the top unchecked item.
2. Curate sources first; never implement an unsourced value (respect the gated
   classes: NADP(H), G6PD/6PGD, GPx/glutathione reductase, direct PPP flux).
3. Implement at the established altitude; explore dynamics before fixing test
   thresholds; keep conservation exact under SSA.
4. Gate (`scripts/gate.sh`), commit, push, check the item off here.
5. If an item is too large for one cycle, split it and record the split here.
