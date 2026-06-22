# Source Ledger

The source ledger tracks references used by the project. Model decisions should
link back here or to a more specific research file.

## Physics And Chemistry

- NIST physical constants: https://pml.nist.gov/cuu/Constants/
  - Use for CODATA fundamental constants.
- NIST Chemistry WebBook: https://webbook.nist.gov/
  - Use for ionization energy, electron affinity, spectra, and thermochemical
    data where available.
- OpenStax University Physics, hydrogen atom:
  https://openstax.org/books/university-physics-volume-3/pages/8-1-the-hydrogen-atom
  - Use for wave function, probability density, quantum numbers, and hydrogen
    atom fundamentals.
- OpenStax Chemistry, quantum theory:
  https://openstax.org/books/chemistry-2e/pages/6-3-development-of-quantum-theory
  - Use for the quantum model, orbitals, and probability-density framing.
- OpenStax University Physics Vol. 3, §9.2 "Types of Molecular Bonds"
  (LibreTexts mirror):
  https://phys.libretexts.org/Bookshelves/University_Physics/University_Physics_(OpenStax)/University_Physics_III_-_Optics_and_Modern_Physics_(OpenStax)/09:_Condensed_Matter_Physics/9.02:_Types_of_Molecular_Bonds
  - PRIMARY SOURCE for the ion model. Provides: k·e² = 1.440 eV·nm;
    NaCl equilibrium bond length r0 = 0.236 nm; Pauli (exclusion) repulsion
    energy 0.32 eV at r0; homolytic dissociation energy 4.26 eV; and Table 9.2.1
    of bond lengths/energies for other salts. The simulation's Born–Mayer
    repulsion (B, ρ) is DERIVED from these measured values plus the equilibrium
    force-balance condition — no fitted/invented parameters.
- Shannon, R. D. (1976). "Revised effective ionic radii", Acta Cryst. A32, 751.
  - Source for the 6-coordinate effective ionic radii used as the ion render
    radii: Na+ 0.102 nm, Cl- 0.181 nm, K+ 0.138 nm.
- IUPAC 2021 standard atomic weights.
  - Source for ion masses (Na 22.9898 u, Cl 35.45 u, K 39.0983 u).
- Eukaryotic cell organelles — sizes, functions, organization:
  - NIGMS, "Take a Tour of Your Cells' Organelles": https://nigms.nih.gov/biobeat/2021/03/take-a-tour-of-your-cells-organelles
  - Biology LibreTexts, "Cell Organelles": https://bio.libretexts.org/Courses/Cosumnes_River_College/Introductory_Anatomy_and_Physiology_(Aptekar)/02:_Cells_and_Tissues/2.06:_Cell_Organelles
  - Alberts et al., Molecular Biology of the Cell (NCBI Bookshelf, already listed).
  - Key figures used: typical animal cell ~10–30 µm; nucleus ~6 µm (largest
    organelle); mitochondria ~0.5–1 µm × 1–5 µm (hundreds–thousands per cell);
    Golgi 4–10 cisternae; lysosomes ~0.1–0.5 µm; ribosomes ~25 nm; ER forms a
    network contiguous with the nuclear envelope and contacts mitochondria/Golgi.
- Hepatocyte / animal-cell division and organelle inheritance:
  - Cytokinesis, Molecular Biology of the Cell / NCBI Bookshelf:
    https://www.ncbi.nlm.nih.gov/books/NBK26831/
    - Use for spindle-defined division plane, contractile ring, cleavage furrow,
      membrane insertion, midbody and the rule that membrane-bound organelles
      must be inherited.
  - Mechanics and regulation of cytokinetic abscission:
    https://www.frontiersin.org/journals/cell-and-developmental-biology/articles/10.3389/fcell.2022.1046617/full
    - Use for intercellular bridge/midbody maturation, ESCRT-III abscission and
      bridge-tension effects.
  - Organelle inheritance control of mitotic entry and progression:
    https://www.frontiersin.org/journals/cell-and-developmental-biology/articles/10.3389/fcell.2019.00133/full
    - Use for mitotic Golgi disassembly, mitochondrial/peroxisome positioning,
      endosome/lysosome inheritance and organelle-spindle coupling.
  - Mitochondrial dynamics during mitosis:
    https://www.frontiersin.org/journals/cell-and-developmental-biology/articles/10.3389/fcell.2021.767221/full
    - Use for CDK1/Aurora-A/DRP1-driven mitotic mitochondrial fragmentation.
  - Centrosome duplication/segregation:
    https://www.mdpi.com/2073-4409/11/15/2445
    - Use for one centrosome in G1, duplication before mitosis and one
      centrosome inherited by each normal daughter.
  - Hepatocyte binucleation / polyploidy:
    https://pubmed.ncbi.nlm.nih.gov/38727809/ and
    https://pubmed.ncbi.nlm.nih.gov/23150829/
    - Use for hepatocyte-specific endomitosis/cytokinesis failure and late
      cytokinetic regression.
  - Mammalian cell-cycle timing:
    https://book.bionumbers.org/how-long-do-the-different-stages-of-the-cell-cycle-take/
    - Use for real-time anchors: S phase ~6-8 h, G2 ~2-3 h, M ~1 h; browser
      visualization remains time-compressed and discloses this.
  - HeLa phase-duration benchmark, BioNumbers BNID 106404:
    https://bionumbers.hms.harvard.edu/bionumber.aspx?id=106404&s=n&v=2
    - Use only as a mammalian cell-cycle timing benchmark: G1 8.40 h, S 6.04 h,
      G2 4.56 h, M 1.10 h. Not hepatocyte-specific.
  - Rat hepatocyte post-partial-hepatectomy cell-cycle regulator timing:
    https://www.nature.com/articles/emm199629
    - Use for the hepatocyte regeneration timing profile: S phase begins around
      18 h after PHx and DNA synthesis peaks around 21-24 h. S/M durations still
      use mammalian anchors until hepatocyte-specific durations are added.
  - The Restriction Point of the Cell Cycle:
    https://www.ncbi.nlm.nih.gov/books/NBK6318/
    - Use for the qualitative G1/S network: mitogen-driven Cyclin D/CDK4/6,
      RB phosphorylation, E2F release and Cyclin E/CDK2 commitment.
  - Intracellular Control of Cell-Cycle Events:
    https://www.ncbi.nlm.nih.gov/books/NBK26856/
    - Use for ordered cyclin-CDK switches, APC/C-Cdc20, securin destruction,
      separase activation and spindle-attachment checkpoint logic.
  - Regulators of Cell Cycle Progression:
    https://www.ncbi.nlm.nih.gov/books/NBK9962/
    - Use for p21 CDK inhibition and Chk1/Cdc25/CDK1 G2/M checkpoint logic.
  - Cell cycle regulation: p53-p21-RB signaling:
    https://pubmed.ncbi.nlm.nih.gov/35361964/
    - Use for p53 -> p21 -> cyclin-CDK inhibition -> RB/E2F repression after
      DNA damage or equivalent checkpoint stress.
- Hepatocyte regeneration and proliferation gating:
  - Liver Regeneration after Hepatectomy and Partial Liver Transplantation:
    https://www.mdpi.com/1422-0067/21/21/8414
    - Use for PHx/PLTx regeneration context, rodent/human timing anchors,
      hemodynamic triggers, partial hepatectomy size effects and termination
      biology.
  - Signals and Cells Involved in Regulating Liver Regeneration:
    https://www.mdpi.com/2073-4409/1/4/1261
    - Use for HGF/MET, EGF/EGFR and cytokine orchestration in hepatocyte
      cell-cycle entry.
  - Combined systemic elimination of MET and epidermal growth factor receptor
    signaling completely abolishes liver regeneration:
    https://pubmed.ncbi.nlm.nih.gov/27397846/
    - Use for the direct-mitogen redundancy rule: MET or EGFR alone can support
      regeneration, while combined MET+EGFR loss abolishes regeneration and
      prevents liver-mass restoration.
  - EGFR: A Master Piece in G1/S Phase Transition of Liver Regeneration:
    https://pmc.ncbi.nlm.nih.gov/articles/PMC3461622/
    - Use for EGFR as a dedicated hepatocyte G1/S-transition axis rather than a
      generic growth knob.
  - Initiation of liver growth by tumor necrosis factor:
    https://pmc.ncbi.nlm.nih.gov/articles/PMC19810/
    - Use for TNF/TNFR1 as an initiation/priming pathway that acts through an
      IL-6-dependent regeneration route, not as a standalone direct mitogen.
  - Liver failure and defective hepatocyte regeneration in interleukin-6-deficient
    mice:
    https://pubmed.ncbi.nlm.nih.gov/8910279/
    - Use for IL-6/STAT3 as a hepatocyte priming/survival and DNA-synthesis
      support pathway after liver-mass loss.
  - Conditional deletion of beta-catenin reveals its role in liver growth and
    regeneration:
    https://pubmed.ncbi.nlm.nih.gov/17101329/
    - Use for Wnt/beta-catenin support: loss delays/suboptimizes regeneration
      rather than behaving as a universal absolute gate.
  - Inactivation of TGF-beta signaling in hepatocytes results in an increased
    proliferative response after partial hepatectomy:
    https://pubmed.ncbi.nlm.nih.gov/15735717/
    - Use for TGF-beta/SMAD as a proliferation brake/termination pressure in
      hepatocyte regeneration.
  - Knockdown and knockout of beta1-integrin in hepatocytes impairs liver
    regeneration through inhibition of growth factor signalling:
    https://pubmed.ncbi.nlm.nih.gov/24844558/
    - Use for ECM/integrin attachment as a permissive requirement for HGF/EGF
      signalling.
  - Hippo signaling in the liver: role in development, regeneration and disease:
    https://pmc.ncbi.nlm.nih.gov/articles/PMC9199961/
    - Use for contact/organ-size control and YAP/TAZ/Hippo context.
- Michaelis, L. & Menten, M. L. (1913) — Michaelis–Menten enzyme kinetics, the
  standard rate law used for the living cell's metabolic fluxes (uptake,
  respiration, synthesis) across all organelle modules.
- Allosteric feedback inhibition of glycolysis: phosphofructokinase (PFK) is
  inhibited by high ATP / activated by ADP-AMP — the standard textbook control
  point of glycolysis (Alberts et al., Molecular Biology of the Cell, already
  listed; Berg, Tymoczko & Stryer, Biochemistry, glycolysis regulation). Basis
  for the organelle-network model's ATP-demand down-regulation of glucose uptake
  and glycolysis, which gives the network a self-regulating steady state.
- Chemical Langevin equation (Gillespie, D. T., J. Chem. Phys. 113, 297, 2000) —
  basis for the cell's molecular noise term √(flux·dt/Ω)·ξ.
- Hubley, M. J., Locke, B. R., & Moerland, T. S. (1996). "The effects of
  temperature, pH, and magnesium on the diffusion coefficient of ATP in
  solutions of physiological ionic strength", Biochim. Biophys. Acta 1291, 115.
  - Source for the cytoplasmic ATP diffusion coefficient (~150 µm²/s) used to
    compute the per-organelle ATP transport delay τ = x²/(6·D): ATP is not used
    the instant it is made; distant organelles receive it later.
- Organelle internal-cycle "lifestyles" (illustrative periods, real phenomena):
  - Transcriptional bursting: Raj & van Oudenaarden (2008), Cell 135, 216;
    Chubb et al. (2006), Curr. Biol. 16, 1018.
  - Translational bursting: Yu, Xiao, Ren, Lao & Xie (2006), Science 311, 1600.
  - Quantal / vesicular Golgi trafficking and pulsatile lysosomal degradation —
    Alberts et al., Molecular Biology of the Cell (already listed).
  - Basis for giving each organelle its own independent cycle (continuous
    powerhouses vs. bursty batch workers). Periods are assumptions; the
    independent-rhythm and bursting structure is real.
- Stress-driven organelle failure (illustrative hazard rates): the modelled
  fault probability rising with low ATP and accumulated waste/ROS reflects the
  real link between energy stress, oxidative damage and organelle dysfunction
  (Alberts et al., already listed). Hazard magnitudes are explicit assumptions.
- Smoluchowski, M. von (1917), Z. Phys. Chem. 92, 129 — diffusion-limited
  reaction rate.
  - Source for the reaction–diffusion rate constant k = 4π(D_A+D_B)R used to
    ground the A + B → C chemistry milestone.
- Berendsen, H. J. C., Grigera, J. R., & Straatsma, T. P. (1987). "The Missing
  Term in Effective Pair Potentials", J. Phys. Chem. 91, 6269.
  - Source for the SPC/E rigid water model: partial charges, O-H geometry,
    oxygen Lennard-Jones parameters, and model dipole.
- Joung, I. S., & Cheatham, T. E. (2008). "Determination of Alkali and Halide
  Monovalent Ion Parameters for Use in Explicitly Solvated Biomolecular
  Simulations", J. Phys. Chem. B 112, 9020.
  - Source for Na+ and Cl- Lennard-Jones parameters compatible with SPC/E water.
- CRC Handbook of Chemistry and Physics.
  - Source for water viscosity and limiting aqueous self-diffusion coefficients
    used in the Brownian diffusion scenes.
- Cooke, I. R., Kremer, K., & Deserno, M. (2005). "Efficient tunable generic
  model for fluid bilayer membranes", Phys. Rev. E 72, 011506.
  - Source for the 3-bead solvent-free lipid membrane model, including WCA,
    FENE, bending, tail-attraction, and Langevin reduced-unit parameters.

## Cell Biology

- NCBI Bookshelf, Molecular Biology of the Cell:
  https://www.ncbi.nlm.nih.gov/books/NBK21054/
  - Use as a broad conceptual cell biology reference.
- NCBI Bookshelf, cell junctions:
  https://www.ncbi.nlm.nih.gov/books/NBK26857/
  - Use for tight junctions, epithelial barriers, and junction behavior.
- NCBI Bookshelf, cell junction chapter index:
  https://www.ncbi.nlm.nih.gov/books/NBK20684/
  - Use for epithelial junction organization.
- NCBI Bookshelf, transport of small molecules:
  https://www.ncbi.nlm.nih.gov/books/NBK9847/
  - Use for membrane transport, ion gradients, and ATP-driven pumps.
- NCBI Bookshelf, active transport:
  https://www.ncbi.nlm.nih.gov/books/NBK547718/
  - Use for active transport concepts and pump/coupling definitions.
- NCBI Bookshelf, Molecular Biology of the Cell, "From DNA to RNA":
  https://www.ncbi.nlm.nih.gov/books/NBK26887/
  - Use for transcription and nuclear RNA production.
- NCBI Bookshelf, The Cell, "RNA Processing and Turnover":
  https://www.ncbi.nlm.nih.gov/books/NBK9864/
  - Use for eukaryotic mRNA processing, export and turnover.
- NCBI Bookshelf, Molecular Biology of the Cell, "The Endoplasmic Reticulum":
  https://www.ncbi.nlm.nih.gov/books/NBK26841/
  - Use for SRP-directed ER targeting, rough ER entry, folding and ER handling.
- NCBI Bookshelf, Molecular Biology of the Cell, "Transport from the ER through
  the Golgi Apparatus": https://www.ncbi.nlm.nih.gov/books/NBK26941/
  - Use for ER-to-Golgi traffic, Golgi organization, modification and sorting.
- NCBI Bookshelf, Molecular Biology of the Cell, "Transport from the Trans
  Golgi Network to the Cell Exterior": https://www.ncbi.nlm.nih.gov/books/NBK26892/
  - Use for secretory vesicles, exocytosis and polarized plasma-membrane
    delivery.
- NCBI Bookshelf, Molecular Biology of the Cell, "Transport from the Trans
  Golgi Network to Lysosomes": https://www.ncbi.nlm.nih.gov/books/NBK26844/
  - Use for lysosomal enzyme cargo and Golgi-to-endosome/lysosome routing.
- NCBI Bookshelf, Molecular Biology of the Cell, "The Mitochondrion":
  https://www.ncbi.nlm.nih.gov/books/NBK26894/
  - Use for mitochondrial sugar/fat oxidation and ATP production.
- NCBI Bookshelf, The Cell, "Lysosomes":
  https://www.ncbi.nlm.nih.gov/books/NBK9953/
  - Use for lysosomal degradation and autophagy turnover.
- NCBI Bookshelf, Molecular Biology of the Cell, "Peroxisomes":
  https://www.ncbi.nlm.nih.gov/books/NBK26858/
  - Use for peroxisomal oxidative reactions, catalase and lipid metabolism.
- NCBI Bookshelf, The Cell, "Protein Degradation":
  https://www.ncbi.nlm.nih.gov/books/NBK9957/
  - Use for ubiquitin-proteasome degradation and protein recycling.
- Hepatocyte polarity:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC3697931/
  - Use for hepatocyte polarity and canalicular/sinusoidal trafficking context.
- Dawson, Lan & Rao, "Bile acid transporters":
  https://pmc.ncbi.nlm.nih.gov/articles/PMC2781307/
  - Use for sinusoidal/canalicular bile acid transport and ATP-dependent export
    framing.
- Cell Biology by the Numbers:
  https://book.bionumbers.org/
  - Use for sizes, concentrations, rates, energies, and quantitative estimates.
- BioNumbers BNID 105911, internal membrane surface area of hepatocyte:
  https://bionumbers.hms.harvard.edu/bionumber.aspx?id=105911&s=n&v=1
  - Use for hepatocyte membrane-area scale; entry notes internal membrane area is
    50x plasma membrane area.
- Dupuy & Engelman, "Protein area occupancy at the center of the red blood cell
  membrane": https://pmc.ncbi.nlm.nih.gov/articles/PMC2268548/
  - Use as a conservative lower-bound membrane protein area occupancy estimate
    for density-scale visualization.
- NCBI Bookshelf, Molecular Biology of the Cell, "Principles of Membrane
  Transport": https://www.ncbi.nlm.nih.gov/books/NBK26815/
  - Use for channel vs carrier distinctions and the idea that transport proteins
    provide selective pathways across lipid bilayers.
- NCBI Bookshelf, Molecular Biology of the Cell, "Carrier Proteins and Active
  Membrane Transport": https://www.ncbi.nlm.nih.gov/books/NBK26896/
  - Use for alternating-access carriers and ATP/gradient-coupled active transport
    framing.
- Madeira et al., "Aquaporins: More Than Functional Monomers in a Tetrameric
  Arrangement": https://pmc.ncbi.nlm.nih.gov/articles/PMC6262540/
  - Use for aquaporin tetramer and monomer-pore visual framing.
- Mueckler & Thorens, "The SLC2 (GLUT) Family of Membrane Transporters":
  https://pmc.ncbi.nlm.nih.gov/articles/PMC4104978/
  - Use for GLUT-family 12-transmembrane-domain carrier visual framing.
- NCBI Bookshelf, The Cell, "Functions of Cell Surface Receptors":
  https://www.ncbi.nlm.nih.gov/books/NBK9866/
  - Use for receptor coupling from extracellular ligand recognition to
    intracellular signaling targets.

## Platform

- Unity system requirements:
  https://docs.unity3d.com/Manual/system-requirements.html
- Unreal macOS development requirements:
  https://dev.epicgames.com/documentation/unreal-engine/macos-development-requirements-for-unreal-engine
- Godot Metal backend notes:
  https://godotengine.org/article/dev-snapshot-godot-4-4-dev-1/
- Apple WebGPU overview:
  https://developer.apple.com/videos/play/wwdc2025/236/

## Systems Biology Toolchain

- Brian simulator:
  https://briansimulator.org/
  - Use for equation-based ion/channel/Ca2+ dynamics and generated-code
    performance experiments. It is not the whole-cell core.
- libRoadRunner:
  https://github.com/sys-bio/roadrunner
  - Use for SBML biochemical network simulation through a C/C++ core with
    Python bindings.
- PySB:
  https://pysb.org/
  - Use for rule-based biochemical pathway models, especially receptor
    signaling, protein state changes, and pathway logic that would be too
    verbose as manually enumerated reactions.
- PhysiCell:
  https://physicell.org/
  - Use as the main candidate for future multicellular/tissue-scale simulation
    and microenvironment coupling.
- SBML:
  https://sbml.org/
  - Use as the standard model-exchange format for biochemical reaction networks.

## Ketogenesis (hepatic, mitochondrial)

- HMGCS2 as the rate-limiting control enzyme of ketogenesis:
  Hegardt FG, Biochem J 1999;338:569-582.
  https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1220089/
  - Mitochondrial HMG-CoA synthase (HMGCS2) is the liver-specific, committed,
    rate-limiting step (acetoacetyl-CoA + acetyl-CoA -> HMG-CoA). Grounds the
    `hmgcs2` reaction and the "rate-limiting" control test in
    `engine/cell_engine/stochastic/ketogenesis.py`.
- Ketone bodies as a mitochondrial redox readout:
  Williamson DH, Lund P, Krebs HA, Biochem J 1967;103:514-527.
  https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1270436/
  - The beta-hydroxybutyrate/acetoacetate ratio measures free mitochondrial
    NAD+/NADH via near-equilibrium BDH1. Grounds the BDH1 redox coupling and the
    `bhb_to_acetoacetate_ratio_tracks_mitochondrial_redox` test.
- Ketone body physiology and concentration ranges:
  Metabolic Messengers: ketone bodies, Nat Metab 2023.
  https://www.nature.com/articles/s42255-023-00935-3
  - Total blood ketones <~0.3 mM fed/rested, ~0.3-0.5 mM overnight-fasted, several
    mM in prolonged fasting; beta-hydroxybutyrate normally dominant. Cross-checked
    with HMDB (HMDB0000357 beta-hydroxybutyrate, HMDB0000060 acetoacetate).

## Gluconeogenesis (hepatic)

- Hepatic glucose homeostasis kinetic model (glycolysis + gluconeogenesis):
  König et al., PLoS Comput Biol 2012.
  https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1002577
  - Hormone-controlled kinetic model predicting net hepatic glucose output across
    fed/fasted. Grounds the gluconeogenic pathway and glucose-output behavior in
    `engine/cell_engine/stochastic/gluconeogenesis.py`.
- Reciprocal regulation of gluconeogenesis vs glycolysis:
  Pilkis SJ, Granner DK, Annu Rev Physiol 1992;54:885-909.
  https://pubmed.ncbi.nlm.nih.gov/1562196/
  - Insulin/glucagon reciprocally regulate the opposing enzyme pairs
    (PFK1/FBPase1, PK/PEPCK). Grounds the hormone-gated bypass enzymes and the
    `fasted_produces_glucose_fed_is_suppressed` test. Energetic cost (6 ATP per
    glucose from 2 pyruvate) is enforced by reaction stoichiometry.

## Amino-acid catabolism (hepatic nitrogen disposal)

- Transdeamination and the glutamate nitrogen hub:
  Brosnan JT, "Glutamate, at the Interface between Amino Acid and Carbohydrate
  Metabolism," J Nutr 2000;130:988S-990S.
  https://jn.nutrition.org/article/S0022-3166(22)14024-1/fulltext
  - Aminotransferases funnel amino-N onto glutamate; GDH releases it as ammonia;
    carbon skeletons -> glucose, nitrogen -> urea. Grounds
    engine/cell_engine/stochastic/amino_acid_catabolism.py.
- Hepatic GDH bridging gluconeogenesis and ammonia homeostasis:
  Karaca et al., "Liver Glutamate Dehydrogenase Controls Whole-Body Energy
  Partitioning...," Diabetes 2018;67:1949.
  https://diabetesjournals.org/diabetes/article/67/10/1949/35297
  - GDH oxidative deamination links amino-acid-derived gluconeogenesis to ammonia/
    urea. Note: GDH uses NAD+ or NADP+; modelled on NAD+ only (NADP(H) is a gated
    evidence class here).

## Glycerol gluconeogenesis

- Glycerol as the preferred, low-energy gluconeogenic substrate:
  Lal et al., "Glycerol induces G6pc in primary mouse hepatocytes and is the
  preferred substrate for gluconeogenesis both in vitro and in vivo," (PMC6885632).
  https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6885632/
  - Glucose from glycerol takes fewer steps / less energy (~2 ATP/glucose vs 6 from
    pyruvate); glycerol induces G6Pase. Grounds glycerol_gluconeogenesis.py.
- Glycerol kinase / GPD1 / G3P-DHAP entry:
  "Glycerol and Glycerol-3-Phosphate: Multifaceted Metabolites...," Endocrine Reviews.
  https://academic.oup.com/edrv/advance-article/doi/10.1210/endrev/bnaf033/8250484
  - Liver-only glycerol kinase (ATP) -> G3P; cytosolic GPD1 (NAD+/NADH) interconverts
    G3P and DHAP, which enters gluconeogenesis below PEP.

## HMDB physiological concentration ranges (validation targets)

- HMDB 5.0, the Human Metabolome Database:
  Wishart et al., Nucleic Acids Res 2022 (PMC8728138).
  https://pmc.ncbi.nlm.nih.gov/articles/PMC8728138/
  - Normal physiological concentrations (blood/plasma; tissue where noted) for the
    metabolites the engine tracks, curated in
    engine/cell_engine/validation/hmdb_ranges.py as validation targets (glucose,
    lactate, pyruvate, alanine, glutamine, glutamate, beta-hydroxybutyrate,
    acetoacetate, ammonia, urea, glycerol). Standard clinical/HMDB reference values;
    hmdb.ca blocks automated fetch so per-accession re-verification is manual.

## Gene-level hormonal control (reciprocal transcription)

- Glucagon/CREB induction of gluconeogenic genes:
  Herzig et al., "CREB regulates hepatic gluconeogenesis through the coactivator
  PGC-1," Nature 2001;413:179-183.
  https://www.nature.com/articles/35093131
  - Fasting/glucagon -> cAMP/PKA/CREB -> PGC-1alpha induces PEPCK/G6Pase. Grounds the
    gluconeogenic-gene induction in hormonal_gene_regulation.py.
- Insulin/SREBP-1c induction of lipogenic genes (and reciprocal gng suppression):
  Horton, Goldstein & Brown, "SREBPs: activators of the complete program of
  cholesterol and fatty acid synthesis in the liver," J Clin Invest 2002;109:1125.
  https://www.jci.org/articles/view/15593
  - Insulin -> SREBP-1c induces ACC/FASN; insulin/AKT/FOXO1 suppress gluconeogenic
    genes. Grounds the reciprocal transcriptional control.
