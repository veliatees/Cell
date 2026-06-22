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
- [ ] **2. Amino-acid catabolism.** Glutamine/glutamate + alanine transamination
  feeding the urea cycle (aspartate/fumarate node) and gluconeogenesis. (HEPATOKIN1)
- [ ] **3. Glycerol → gluconeogenesis.** Glycerol kinase + G3P dehydrogenase entry;
  link lipolysis to glucose output.
- [ ] **4. Validation panel expansion.** Add HMDB physiological concentration
  ranges (β-OHB, acetoacetate, glucose, lactate, alanine, …) as validation targets;
  grow the scorecard from a handful to dozens. (HMDB 5.0)
- [ ] **5. Ground illustrative magnitudes.** Replace flagged `placeholder` rate
  magnitudes module-by-module with BRENDA/SABIO-RK human/liver kinetics; drive the
  placeholder count toward zero. (BRENDA, SABIO-RK)
- [ ] **6. Signaling depth.** Gene-level hormonal control: glucagon→cAMP/PKA→PEPCK/
  G6Pase induction; insulin→SREBP-1c→lipogenic genes. (König 2012; AMPK/CRTC2)
- [ ] **7. Transport kinetics.** Ground NTCP, OATP1B1/3, GLUT2, BSEP, MRP2,
  Na⁺/K⁺-ATPase with literature Km/Vmax; couple to membrane potential.
- [ ] **8. Calcium / electrophysiology depth.** Stochastic IP₃R Markov clusters;
  membrane potential from Na/K-ATPase + K⁺ channel. (IP3R stochastic models)
- [ ] **9. Lipid depth.** DNL (ACC/FASN), VLDL biogenesis (ApoB100/MTP), steatosis
  threshold; link to ketogenesis acetyl-CoA. (iHepatocytes2322)
- [ ] **10. DNA-repair depth.** Quantitative NHEJ/HR + p53/p21 fate network feeding
  apoptosis. (PLoS Comput Biol stochastic NHEJ+p53)
- [ ] **11. Spatial fusion → RDME.** Fuse 1-D spatial with the real reaction network
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
