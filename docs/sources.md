# Source Ledger

The source ledger tracks references used by the project. Model decisions should
link back here or to a more specific research file.

## Physics And Chemistry

- NIST physical constants: https://pml.nist.gov/cuu/Constants/
  - Use for CODATA fundamental constants.
- NIST Chemistry WebBook: https://webbook.nist.gov/
  - Use for ionization energy, electron affinity, spectra, and thermochemical
    data where available.
  - Glucose record (CAS 50-99-7):
    https://webbook.nist.gov/cgi/cbook.cgi?ID=C50997
    gives formula C6H12O6 and molecular weight 180.1559 g/mol. This grounds the
    explicit mg-glucose to umol-glucose conversion in the external hepatic-output
    comparison; it is not a fitted model factor.
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

## Malonyl-CoA node (lipogenesis / fatty-acid-oxidation switch)

- Malonyl-CoA inhibition of CPT1 (fat synthesis vs oxidation switch):
  McGarry, Mannaerts & Foster, "A possible role for malonyl-CoA in the regulation
  of hepatic fatty acid oxidation and ketogenesis," J Clin Invest 1977;60:265.
  https://ncbi.nlm.nih.gov/pmc/articles/PMC372365
  - Malonyl-CoA inhibits long-chain fatty-acid oxidation/ketogenesis at CPT1; high
    fatty-acid synthesis -> low oxidation, and vice versa. Grounds the CPT1
    inhibition in malonyl_coa_node.py.
- Malonyl-CoA as the regulator (ACC/MCD/AMPK control):
  Foster DW, "Malonyl-CoA: the regulator of fatty acid synthesis and oxidation,"
  J Clin Invest 2012;122:1958.
  https://www.jci.org/articles/view/63967
  - ACC (insulin/fed) makes malonyl-CoA; AMPK switches ACC off and MCD on in fasting.

## Real protein structures

- Human glucokinase (GCK / hexokinase IV), glucose-bound — PDB 1V4S:
  https://www.rcsb.org/structure/1V4S
  - Organism: Homo sapiens. Method: X-ray diffraction, 2.30 Å. Single chain (A),
    glucokinase is the monomeric glucose sensor of the hepatocyte.
  - Bound ligands: GLC (alpha-D-glucopyranose, the physiological substrate),
    MRK (a synthetic small-molecule allosteric activator), NA (sodium), HOH (waters).
  - UniProt: P35557 (human GCK). EC 2.7.1.1.
  - Citation: Kamata, Mitsuya, Nishimura, Eiki & Nagata, "Structural Basis for
    Allosteric Regulation of the Monomeric Allosteric Enzyme Human Glucokinase,"
    Structure 2004;12:429-438. DOI 10.1016/j.str.2004.02.005, PMID 15016359.
  - This is the experimentally-determined structure rendered in 3D for glucokinase
    (downloaded to public/glucokinase.pdb via https://files.rcsb.org/download/1V4S.pdb).
    Chosen because the engine already models GCK's function (glucose S0.5 ~8 mM,
    Hill ~1.7; see kinetics_data.py / glucokinase_mol_physiol) — so the rendered
    atoms and the computed kinetics describe the same real protein.
  - Caveats: this is the closed/active conformation captured WITH a synthetic
    activator (MRK) bound at the allosteric site; the activator is not physiological.
    Modelled residues span 14-461 — the N-terminal ~13 residues and 14 disordered
    residues (REMARK 465) are absent from the coordinates, as is normal for X-ray
    structures.

### Membrane and intracellular protein structures

Real, named hepatocyte proteins placed at their correct subcellular location and
membrane orientation for the 3D scene, replacing the abstract family "footprints".
Files live in `public/proteins/` with the machine-readable index in
`public/proteins/manifest.json`. Membrane proteins prefer the OPM
(Orientations of Proteins in Membranes, https://opm.phar.umich.edu) membrane-aligned
coordinates, which bake in the correct tilt (membrane normal = z, dummy DUM atoms
at the two bilayer boundaries; hydrophobic thickness ~31 Å for all three). For these
OPM files the extracellular side was determined here to be +z because the large
cytosolic domain sits at -z (BSEP/MRP2 NBDs, Na/K-ATPase catalytic head, NTCP's
nanobody on the cytosolic face). Selection prioritises proteins whose FUNCTION the
engine already models, so rendered atoms and simulated flux describe the same protein.

- GLUT2 / glucose transporter 2 (SLC2A2, UniProt P11168) — `proteins/glut2_slc2a2.pdb`.
  Location: basolateral/sinusoidal plasma membrane. PREDICTED structure: AlphaFold
  AF-P11168-F1 (model_v6, global pLDDT 86.62), https://alphafold.ebi.ac.uk/entry/P11168.
  Organism: Homo sapiens. 12-TM major-facilitator carrier, both termini cytosolic.
  No experimental human GLUT2 structure exists in the PDB (relatives GLUT1 4PYP/6THA,
  GLUT4 7WSN are experimental). Citation: Jumper et al., Nature 2021;596:583
  (DOI 10.1038/s41586-021-03819-2); Varadi et al., Nucleic Acids Res 2024;52:D368
  (DOI 10.1093/nar/gkad1011). Caveat: PREDICTED model, orientation not membrane-
  calibrated — renderer must embed in the bilayer (may borrow tilt from an OPM GLUT
  homolog).
- Na+/K+-ATPase α1/β1 (ATP1A1, UniProt P05023) — `proteins/naka_atp1a1.pdb`.
  Location: basolateral plasma membrane. PDB 7E1Z, cryo-EM 3.2 Å, Homo sapiens
  (recombinant), E1·3Na state. RCSB https://www.rcsb.org/structure/7E1Z;
  OPM-oriented https://opm.phar.umich.edu/proteins?search=7E1Z (extracellular = +z).
  Ligands: 3 Na+ (transported), Mg, N-glycan, cholesterol-hemisuccinate, phospholipid.
  Citation: Guo et al., "Cryo-EM structures of recombinant human sodium-potassium pump
  determined in three different states," Nat Commun 2022;13:3957
  (DOI 10.1038/s41467-022-31602-y, PMID 35803952). Caveat: single E1 catalytic state;
  sets the Na+ gradient/membrane potential that powers NTCP cotransport.
- NTCP / Na+-taurocholate cotransporting polypeptide (SLC10A1, UniProt Q14973) —
  `proteins/ntcp_slc10a1.pdb`. Location: basolateral/sinusoidal plasma membrane
  (bile-salt UPTAKE). PDB 7PQG, cryo-EM 3.7 Å, Homo sapiens. RCSB
  https://www.rcsb.org/structure/7PQG; OPM-oriented
  https://opm.phar.umich.edu/proteins?search=7PQG (extracellular = +z). Citation:
  Goutam, Ielasi, Pardon, Steyaert, Reyes, "Structural basis of sodium-dependent bile
  salt uptake into the liver," Nature 2022;606:1015 (DOI 10.1038/s41586-022-04723-z,
  PMID 35545671). Caveat: THERMOSTABILISED construct with a conformation-locking
  nanobody (Nb87, chain B) bound on the cytosolic face and no bile salt (apo) — the
  nanobody chain should be hidden by the renderer.
- BSEP / bile salt export pump (ABCB11, UniProt O95342) — `proteins/bsep_abcb11.pdb`.
  Location: canalicular/apical plasma membrane (ATP-driven bile-salt EXPORT; the
  cholestasis-demo transporter). PDB 6LR0, cryo-EM 3.5 Å, Homo sapiens, apo inward-open.
  RCSB https://www.rcsb.org/structure/6LR0; OPM-oriented
  https://opm.phar.umich.edu/proteins?search=6LR0 (canalicular lumen = +z; cytosolic
  NBDs at -z). Citation: Wang et al., "Cryo-EM structure of human bile salts exporter
  ABCB11," Cell Res 2020;30:623 (DOI 10.1038/s41422-020-0302-0, PMID 32203132). Caveat:
  apo state, no bile salt or nucleotide bound.
- MRP2 / multidrug resistance-associated protein 2 (ABCC2, UniProt Q92887) —
  `proteins/mrp2_abcc2.pdb`. Location: canalicular/apical plasma membrane (conjugated
  bilirubin / organic-anion EXPORT; loss = Dubin-Johnson syndrome). PDB 8JXQ, cryo-EM
  3.32 Å, Homo sapiens, with a CONJUGATED-BILIRUBIN substrate (bilirubin ditaurate, FEI)
  plus cholesterol bound. RCSB https://www.rcsb.org/structure/8JXQ. Citation: Mao et al.,
  "Transport mechanism of human bilirubin transporter ABCC2 tuned by the inter-module
  regulatory domain," Nat Commun 2024;15:1061 (DOI 10.1038/s41467-024-45337-5,
  PMID 38316776). Caveat: NOT in OPM — orientation is the raw deposited cryo-EM frame and
  is NOT membrane-calibrated; renderer must orient it (TMDs in membrane, NBDs + regulatory
  R-domain cytosolic), approximating tilt from OPM-oriented BSEP (6LR0, same ABC-exporter
  fold). Flagged as approximate.
- CPS1 / carbamoyl-phosphate synthetase 1 (CPS1, UniProt P31327, EC 6.3.4.16) —
  `proteins/cps1.pdb`. Location: mitochondrial matrix (committed first step of the urea
  cycle; engine models urea-cycle entry). PDB 5DOU, X-ray 2.6 Å, Homo sapiens,
  ligand-bound active form. RCSB https://www.rcsb.org/structure/5DOU. Ligands:
  N-acetyl-L-glutamate (NLG, essential activator), ADP, phosphate, Mg, K. Citation:
  de Cima et al., "Structure of human carbamoyl phosphate synthetase: deciphering the
  on/off switch of human ureagenesis," Sci Rep 2015;5:16950 (DOI 10.1038/srep16950,
  PMID 26592762). Caveat: large soluble ~1500-residue matrix enzyme — place inside the
  mitochondrion, not in a membrane.

### Cholestasis, proteostasis and cell-fate response

- BSEP loss and intracellular bile-acid disposition — Y. Imai et al.,
  "Disruption of BSEP Function in HepaRG Cells Alters Bile Acid Disposition and
  Is a Susceptive Factor to Drug-Induced Cholestatic Injury," *Molecular
  Pharmaceutics* 2015. DOI 10.1021/acs.molpharmaceut.5b00659. Used for the
  causal BSEP-loss → bile-acid-retention experiment; it does not supply an
  absolute whole-cell export rate.
- Transporter dysregulation, cholestasis and ER stress — I. M. Bochkis et al.,
  "Hepatocyte-specific ablation of Foxa2 alters bile acid homeostasis and
  results in endoplasmic reticulum stress," *Nature Medicine* 2008;14:828-836.
  https://www.nature.com/articles/nm.1853. Used for the cholestasis → ER-stress
  causal edge.
- Bile-acid ROS, mitochondrial permeability transition and apoptosis — B.
  Yerushalmi et al., "Bile acid-induced rat hepatocyte apoptosis is inhibited
  by antioxidants and blockers of the mitochondrial permeability transition,"
  *Journal of Hepatology* 2001. PMID 11230742,
  https://pubmed.ncbi.nlm.nih.gov/11230742/. Freshly isolated rat hepatocytes;
  used as a mechanistic, not human-quantitative, link.
- UPR and bile-acid hepatotoxicity — H. H. Li et al., "The involvement of
  endoplasmic reticulum stress in bile acid-induced hepatocellular injury,"
  *Cell Death & Disease* 2013. PMCID PMC3947968,
  https://pmc.ncbi.nlm.nih.gov/articles/PMC3947968/. Used for the unresolved
  UPR → pro-apoptotic-response edge.
- ATP-dependent apoptosis/necrosis selection — M. Leist et al., "Intracellular
  adenosine triphosphate (ATP) concentration: a switch in the decision between
  apoptosis and necrosis," *Journal of Experimental Medicine* 1997;185:1481.
  https://rupress.org/jem/article/185/8/1481/7145/Intracellular-Adenosine-Triphosphate-ATP.
  Used by the separately calibrated death-commitment module.

## Intercellular Communication And Generative Modeling

- Reactome, "Signaling by Insulin receptor":
  https://reactome.org/content/detail/R-HSA-74752. Curated human mechanism for
  INSR autophosphorylation, IRS/SHC recruitment, PI3K/AKT, and RAS signaling.
- Herzig et al., "CREB regulates hepatic gluconeogenesis through the coactivator
  PGC-1": https://www.nature.com/articles/35093131. Primary hepatic evidence
  for the glucagon/cAMP/PKA/CREB direction; no project kinetic constants are
  inferred from the pathway description.
- Reactome, "Signaling by MET":
  https://reactome.org/content/detail/R-HSA-6806834. Curated human HGF/MET and
  downstream PI3K/AKT, RAS, and STAT3 mechanism.
- Reactome, "Interleukin-6 signaling":
  https://reactome.org/content/detail/R-HSA-1059683. Curated human
  IL-6/IL6R/gp130/JAK/STAT mechanism.
- Tan et al., "Conditional deletion of beta-catenin reveals its role in liver
  growth and regeneration": https://pubmed.ncbi.nlm.nih.gov/17101329/. Mouse
  in-vivo mechanism evidence only; not a human PHH quantitative calibration.
- Reactome, "Adherens junctions interactions":
  https://reactome.org/content/detail/R-HSA-418990. Curated human
  calcium-dependent cadherin trans-contact and cytoskeletal linkage.
- Nelles et al., "Defective propagation of signals generated by sympathetic
  nerve stimulation in connexin32-deficient liver":
  https://pmc.ncbi.nlm.nih.gov/articles/PMC38468/. Mouse in-vivo evidence for
  Cx32-dependent hepatocyte signal propagation; human abundance and
  permeability are not inferred.
- Brian2 2.10.1: https://pypi.org/project/Brian2/2.10.1/ and custom-event
  documentation:
  https://brian2.readthedocs.io/en/2.10.1/examples/advanced.custom_events.html.
  Brian2 is an optional equation/event executor and does not supply biological
  equations or parameter values.
- Kingma and Welling, "Auto-Encoding Variational Bayes":
  https://arxiv.org/abs/1312.6114. Original VAE framework.
- Lopez et al., "Deep generative modeling for single-cell transcriptomics":
  https://www.nature.com/articles/s41592-018-0229-2. Source for a count-aware,
  batch-aware scVI-family design target.
- Lotfollahi et al., "scGen predicts single-cell perturbation responses":
  https://www.nature.com/articles/s41592-019-0494-8. Source for a possible
  perturbation model with out-of-sample evaluation.
- scvi-tools documentation: https://docs.scvi-tools.org/en/stable/. Optional
  software target; not a core dependency and not currently coupled to cell
  state.

## Healthy PHH Spheroid Validation And Human Scale Context

- Kemas et al., "Insulin-dependent glucose consumption dynamics in 3D primary
  human liver cultures measured by a sensitive and specific glucose sensor with
  nanoliter input volume":
  https://faseb.onlinelibrary.wiley.com/doi/10.1096/fj.202001989RR. Primary
  source for all 16 healthy insulin-sensitive 3D PHH glucose-consumption
  windows and the acute pAKT, PCK1 and G6PC responses. The curated record
  preserves 11/5.5 mM glucose, 1.7 uM/0.1 nM insulin, the 100 nM glucagon
  supplement in low-insulin media, seeded-cell denominator, window semantics,
  SD and replicate caveats. These data are validation-only and do not define a
  fresh-PHH or in-vivo single-cell flux. Methods 2.4 and 2.7 additionally anchor
  1500 seeded viable cells/well, a 100 uL culture-seeding volume, one spheroid per
  well after aggregation, 10 uL assay samples in duplicate, and the reported
  `(C0*V0-Ct*Vt)/(VF*n)` calculation. The post-medium-change initial volume,
  remaining-volume schedule, numeric `VF`, window-specific viable-cell counts,
  and covariance are not identified and remain null. Supplementary Figure 2
  reports that Donor 1 showed net glucose production at 6 h in three of four
  conditions while Donor 2 showed no net production at studied times; the
  caption does not expose a numeric donor trajectory, so only the sign constraint
  is curated. Supplementary Figure 1 reports no significant ATP-assay viability
  difference from challenge start to 72 h (`n=8`), which cannot substitute for
  window-specific viable-cell counts.
- Wilson et al., "Human hepatocyte determination and the scaling of metabolic
  clearance in vitro": https://pmc.ncbi.nlm.nih.gov/articles/PMC1884378/.
  Primary source for 107 million hepatocytes/g liver geometric mean, observed
  65-185 million range (n=7), and 33 mg microsomal protein/g liver geometric
  mean with 26-54 mg/g range (n=20). Supports an organ-to-cell denominator, not
  single-cell geometry.
- Honka et al., "Liver blood dynamics and glucose uptake before and after
  bariatric surgery": https://pmc.ncbi.nlm.nih.gov/articles/PMC5920018/.
  Primary source for liver glucose uptake of 22.4 +/- 9.2 umol/kg liver/min in
  326 participants without diabetes during hyperinsulinemic-euglycemic clamp
  FDG-PET. The per-cell conversion is contextual and cannot initialize the
  simulated cell.
- Allen et al., "An in vitro model of zonation in the human liver":
  https://pmc.ncbi.nlm.nih.gov/articles/PMC5661766/. Human liver acinus
  microphysiology evidence for directional Zone 1/Zone 3 functional responses
  under controlled 3-13% oxygen. The oxygen settings are not direct human
  in-situ sinusoidal pO2 measurements.
- Koenig et al., "Quantifying the contribution of the liver to glucose
  homeostasis":
  https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1002577.
  Published liver-scale model source retained as a non-authoritative shadow
  model. Delivered model trajectories without numeric human comparators are
  not classified as held-out validation.
- Grankvist et al., "Global 13C tracing and metabolic flux analysis of intact
  human liver tissue ex vivo":
  https://www.nature.com/articles/s42255-024-01119-3. Primary intact-human-liver
  study combining global 13C tracing, extracellular uptake/release,
  non-targeted mass spectrometry and model-based metabolic flux analysis. It
  supports the measurement design needed to separate pathway fluxes; no numeric
  result is transferred into the PHH spheroid model.

## PHH Albumin Secretion Observability

- Peng et al., "The validation of quality attributes in Primary Human
  Hepatocytes Standard":
  https://pmc.ncbi.nlm.nih.gov/articles/PMC12532551/. Primary study of
  commercial PHH batches. Secreted albumin was measured in six batches by
  Bethyl E88-129 ELISA after 24 h of regular 2D culture and normalized by the
  reported PHH cell number. MD5-verified supplementary Table S3 provides all
  six batch means plus SD values for `n=3`; the table does not identify the
  replicate class: 762.7 +/- 174.1,
  6957.7 +/- 2440.5, 4076.1 +/- 422.5, 2358.7 +/- 742.6,
  4122.0 +/- 955.2, and 2792.5 +/- 774.9 ng/24 h/10^6 cells. The CSCB
  >=800 ng/24 h/10^6 cells criterion remains a PHH product-quality criterion,
  not a physiological interval or simulation pass threshold.
- Wisniewski et al., "In-depth quantitative analysis and comparison of the
  human hepatocyte and hepatoma cell line HepG2 proteomes":
  https://pubmed.ncbi.nlm.nih.gov/26825538/. Quantitative proteomics of purified
  hepatocytes from seven human donors supports the approximate 20,000,000 ALB
  copies/cell context. This is a protein-pool abundance from an unmatched
  cohort, not a synthesis or secretion rate.
- UniProtKB P02768, human albumin:
  https://www.uniprot.org/uniprotkb/P02768/entry. Reviewed sequence record for
  the 609-residue canonical precursor and its processed mature form. The mature
  chain contains 585 residues.
- USP rAlbumin Human reference standard:
  https://doi.usp.org/USPNF/USPNF_M2992_03_01.html. Compendial molecular entity
  reference for the 585-residue, 66,438-Da mature albumin used by the unit
  conversion operator.
- Lodish et al., "Hepatoma secretory proteins migrate from rough endoplasmic
  reticulum to Golgi at characteristic rates":
  https://www.nature.com/articles/304080a0. Primary pulse-chase study in human
  HepG2 hepatoma cells. It supports the selective ER-to-Golgi pathway topology,
  but its transit behavior is not used as a primary-human-hepatocyte numeric
  default.

## PHH CYP, Biliary Excretion, And Identity Quality Panel

- Peng et al., "Requirments for primary human hepatocyte":
  https://pmc.ncbi.nlm.nih.gov/articles/PMC9055892/. Primary publication of the
  CSCB product standard used only as criterion provenance. It specifies
  ALB/HNF4A-positive populations `>=90%`, albumin secretion
  `>=800 ng/(10^6 cells x 24 h)`, d8-TCA BEI `>=30%`, and a representative drug
  metabolism intrinsic-clearance criterion `>=100 uL/(h x 10^6 cells)` with
  CYP3A4/testosterone as the explicit example. These are commercial PHH product
  criteria, not healthy-human physiological intervals or simulation pass gates.
- Peng et al., "The validation of quality attributes in Primary Human
  Hepatocytes Standard":
  https://pmc.ncbi.nlm.nih.gov/articles/PMC12532551/. Primary source for all
  three quality-function surfaces. The supplementary DOCX was retrieved from
  the Europe PMC supplementary-file API and verified as
  `MD5 cf6103b084c236f3fedf2f30e548559e` and
  `SHA-256 deeb835fe82d7e0e883447268354b9abb8f3ca4950639be3b68b802d3c6183bf`.
  Tables S4 and S5 contain n=3 mean-plus-SD substrate-clearance and
  metabolite-formation outputs for CYP1A2, CYP2B6, CYP2C9, CYP2C19, CYP2D6,
  and CYP3A4 in six PHH batches; the tables do not label the replicate class.
  Ten table entries reported as 0.0 without an
  SD are retained as undetectable/censored rather than biological zero. Raw
  time points and LLOQs were not published, so kinetic fitting remains blocked.
- The same study's Table S7 reports d8-TCA BEI values of 27.2, 27.5, 25.7,
  62.0, and 59.0 percent after five days of sandwich culture. The implemented
  operator preserves `BEI=(A_Ca-A_CaFree)/A_Ca*100`; paired raw concentrations
  were not published. BEI therefore cannot identify BSEP turnover, uptake,
  intracellular retention, canalicular volume, or junction sealing separately.
- The same study's Table S2 reports ALB-positive and HNF4A-positive FACS
  fractions for six batches. Figure S2B reports exact counts and rounded
  percentages for hepatocytes, lymphocytes, LSECs, cholangiocytes, and stellate
  cells across 54,134 filtered cells. FACS marker positivity and transcriptomic
  cell-type fraction are retained as different assay constructs.
- NCBI GEO GSE289636:
  https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE289636. Primary raw-data
  accession for the six PHH scRNA-seq batches. The accession is registered for
  provenance; six batches are not enough for donor-disjoint generative-model
  training or a healthy in-vivo population distribution.

## Absolute PHH Proteome And Transporter Inventory

- Wisniewski et al., "In-depth quantitative analysis and comparison of the
  human hepatocyte and hepatoma cell line HepG2 proteomes":
  https://doi.org/10.1016/j.jprot.2016.01.016. Primary quantitative-proteomics
  study of purified hepatocytes from seven surgical-resection donors. The
  Max Planck repository PDF is registered with
  `MD5 5cd1a046891b8bc4b3819e443da006ec`. The source reports an average
  `600 pg` total protein and `8.7 x 10^9` protein molecules per hepatocyte,
  with 25% mitochondrial, 12% ER/Golgi, 10% nuclear, and 1.2% integral
  plasma-membrane protein mass. Its `3000 um3` cell volume is derived from an
  assumed `200 g/L` average cellular protein concentration, not direct
  morphometry. The same cohort reports BSEP at `1.4 pmol/mg total protein`,
  permitting an arithmetic total-copy estimate of `505,859.82384 copies/cell`.
  This is not canalicular surface or active BSEP.
- Deo et al., "Interindividual variability in hepatic expression of the
  multidrug resistance-associated protein 2 (MRP2/ABCC2)":
  https://pmc.ncbi.nlm.nih.gov/articles/PMC3336801/. Targeted LC-MS/MS of human
  liver membrane fractions from 51 donors reports
  `1.54 +/- 0.64 fmol/ug membrane protein`. The tissue membrane denominator is
  retained and is not converted to copies per hepatocyte.

## Human Sandwich-Culture Endogenous Bile Acids

- Marion et al., "Endogenous Bile Acid Disposition in Rat and Human
  Sandwich-Cultured Hepatocytes":
  https://pmc.ncbi.nlm.nih.gov/articles/PMC3679176/ (DOI
  `10.1016/j.taap.2012.02.002`). Table 4 supplies vehicle and 10-uM
  troglitazone means plus SD for TCA, GCA, TCDCA, GCDCA, and Total from four
  human donor experiments on culture day 7. Vehicle totals are
  `281 +/- 85.7 uM` cells-plus-bile, `183 +/- 55.6 uM` cells, and
  `9.61 +/- 6.36 uM` medium. Published BEI is aggregated from experiment-level
  ratios and is not reconstructed from group means. Both paired-buffer
  concentrations use an estimated `6.79 uL/well` intracellular volume, so
  their difference is not a true canalicular concentration. Source proxy zeros
  below quantification remain censored because raw donor records and
  analyte-specific LLOQs are unavailable.

## Hepatocyte Visual Anatomy V2

- Wisse et al., "Fixation methods for electron microscopy of human and other
  liver": https://pmc.ncbi.nlm.nih.gov/articles/PMC2887580/. Human wedge-biopsy
  microscopy supports fenestrae grouped in sieve plates, the sinusoidal
  interface, and a `105 nm` human mean fenestra diameter. The source warns that
  dried SEM dimensions shrink, so no other SEM dimension is transferred.
- Ishii et al., "The intermediate filaments in human hepatocytes":
  https://pubmed.ncbi.nlm.nih.gov/3914103/. Human biopsy microscopy supports a
  cytoplasmic intermediate-filament mesh attached to junctional complexes,
  encircling the canalicular lumen, and directly attached to the nucleus.
- Bachour-El Azzi et al., "Comparative Localization and Functional Activity of
  the Main Hepatobiliary Transporters in HepaRG Cells and Primary Human
  Hepatocytes": https://pmc.ncbi.nlm.nih.gov/articles/PMC4833040/. Primary human
  hepatocyte cultures support pericanalicular F-actin and apical versus
  basolateral transporter localization. Culture geometry is not treated as
  in-vivo morphometry.
- Jiang et al., "Three-dimensional ATUM-SEM reconstruction and analysis of
  hepatic endoplasmic reticulum-organelle interactions":
  https://pubmed.ncbi.nlm.nih.gov/34048584/. Mouse liver 3D EM supports a
  contiguous, intracellularly distributed ER and ER-organelle contact topology;
  mouse dimensions and frequencies are not transferred to human rendering.
- Parlakgul et al., "Regulation of liver subcellular architecture controls
  metabolic homeostasis": https://pmc.ncbi.nlm.nih.gov/articles/PMC9014868/.
  Mouse liver FIB-SEM supports connected ER and spatially heterogeneous
  organelle architecture. Its quantitative morphometry is not a PHH default.
- Meyer et al., "A Predictive 3D Multi-Scale Model of Biliary Fluid Dynamics in
  the Liver Lobule": https://pmc.ncbi.nlm.nih.gov/articles/PMC8063490/. Mouse
  serial block-face EM supports a convoluted canalicular lumen densely packed
  with microvilli. Mouse hydraulic and apparent diameters are not transferred.
- Belicova et al., "Hepatocyte apical bulkheads provide a mechanical means to
  oppose bile pressure": https://pmc.ncbi.nlm.nih.gov/articles/PMC9930133/.
  Mouse liver and hepatoblast data support tight-junction loops, adherens
  junctions, and contractile actomyosin in apical bulkheads. Display frequency
  and thickness remain uncalibrated.
- "The ultrastructural characteristics of bile canaliculus in porcine liver
  donated after cardiac death and machine perfusion preservation":
  https://pmc.ncbi.nlm.nih.gov/articles/PMC7259665/. Control porcine liver
  supports microvilli between adjacent hepatocytes and small Golgi stacks near
  canaliculi. This is topology-only cross-species evidence.

## Geometry-Authoritative Spatial World

- Olander et al., "Hepatocyte size fractionation allows dissection of human
  liver zonation": https://doi.org/10.1002/jcp.30273. Direct measurements from
  54 cryopreserved isolated-human-hepatocyte batches report a median diameter
  of `18.4 um`, with 88% of cells between 12 and 26 um. The engine uses the
  median only as the equivalent-volume scale of its canonical hepatocyte
  surface. It does not infer an in-situ diameter distribution or mechanics.
- Fabyan et al., "3D reconstruction of human liver tissue at cellular
  resolution": https://doi.org/10.1126/sciadv.adz2299. Human cleared-tissue
  reconstruction supports explicit tissue-scale spatial architecture. It does
  not identify a donor-general hepatocyte surface mesh, contact-force law or
  the regular truncated-octahedron proxy used by the runtime.

The normal spatial snapshot contains one hepatocyte. A broad-face pair remains
only as an automated geometry fixture; it is not exported or shown as a browser
scene. Its shape, arrangement and computed patch area are mathematical runtime
state, not observed human contact morphometry.

## Intrinsic Fluid Membrane

- Singer and Nicolson, "The fluid mosaic model of the structure of cell
  membranes": https://doi.org/10.1126/science.175.4023.720. Primary architecture
  reference for a thermodynamically fluid lipid matrix containing amphipathic
  integral proteins. It supplies no hepatocyte diffusion coefficient.
- Helfrich, "Elastic properties of lipid bilayers: theory and possible
  experiments": https://doi.org/10.1515/znc-1973-11-1209. Primary curvature-
  elasticity framework separating stretching, tilt and bending. No PHH bending
  modulus is inferred from the theory.
- Fujiwara et al., "Phospholipids undergo hop diffusion in compartmentalized
  cell membrane": https://doi.org/10.1083/jcb.200202050. Single-molecule tracking
  in NRK cells reports `5.4 um2/s` DOPE diffusion inside approximately `230 nm`
  compartments and actin-dependent macroscopic hop diffusion. This demonstrates
  lateral mobility plus cortical compartmentalization; it is not transferred to
  human hepatocytes.
- "Insulin effect on translational diffusion of lipids and proteins in the
  plasma membrane of isolated rat hepatocytes":
  https://doi.org/10.1016/0167-4889(85)90209-5. FRAP at `21 C` reports NBD-PC
  `2.5e-9 cm2/s` (`0.25 um2/s`) and a mean for unselected labelled proteins of
  `6.4e-10 cm2/s` (`0.064 um2/s`). Probe choice, temperature and species are
  retained; neither value is a healthy-PHH default.

The current evidence bundle does not contain a direct healthy-adult-PHH plasma-
membrane thickness measurement. A generic `4-5 nm` statement is therefore not
stored as a PHH parameter. Thickness, tension, cortex adhesion, bending rigidity,
surface viscosity, lipid/protein diffusion and rupture strain remain `null` for
the simulated human hepatocyte.

## Contact-Deformation Safety Boundary

- Evans et al., "Elastic area compressibility modulus of red cell membrane":
  https://doi.org/10.1016/S0006-3495(76)85713-X. Human red-cell micropipette
  measurements report `2-4%` maximum fractional area expansion before lysis,
  with a `3%` mean. The engine uses `1%`, half the lower bound, as an explicit
  conservative engineering cap. This is not a hepatocyte rupture measurement.
- Rawicz et al., "Effect of chain length and unsaturation on elasticity of lipid
  bilayers": https://doi.org/10.1016/S0006-3495(00)76295-3. Micropipette
  measurements distinguish low-tension undulation smoothing from direct
  high-tension area stretch and report a mean direct area-stretch modulus of
  `243 mN/m` across the tested PC bilayers. That model-bilayer modulus is not
  transferred as hepatocyte cortex stiffness or a force law.
- Guillou et al., "T-lymphocyte passive deformation is controlled by unfolding
  of membrane surface reservoirs":
  https://doi.org/10.1091/mbc.E16-06-0414. Micropipette aspiration supports
  constant-volume cell deformation accompanied by an increase in apparent
  surface area through reservoir unfolding. This is cross-cell-type support for
  the kinematic principle only; no T-cell parameter is transferred to PHH.

The runtime's affine contact response is a volume-preserving kinematic geometry
model. It carries no inferred PHH force, stiffness, adhesion, viscoelasticity,
or biological relaxation-time parameter.
