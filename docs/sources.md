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
