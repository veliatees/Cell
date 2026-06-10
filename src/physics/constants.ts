// Fundamental constants — NIST CODATA 2018 values.
export const ELEMENTARY_CHARGE_C = 1.602_176_634e-19;
export const COULOMB_CONSTANT_N_M2_C2 = 8.987_551_792_3e9;
export const ATOMIC_MASS_UNIT_KG = 1.660_539_066_6e-27;
export const ELECTRON_VOLT_J = 1.602_176_634e-19;
export const BOLTZMANN_CONSTANT_J_K = 1.380_649e-23;

export const NM_TO_M = 1e-9;
export const FS_TO_S = 1e-15;

// k·e² expressed in eV·nm. Equals COULOMB_CONSTANT·e² / (eV per J) / (m per nm).
// OpenStax University Physics Vol. 3 §9.2 quotes this as 1.440 eV·nm.
export const KE2_EV_NM =
  (COULOMB_CONSTANT_N_M2_C2 * ELEMENTARY_CHARGE_C * ELEMENTARY_CHARGE_C) /
  ELECTRON_VOLT_J /
  NM_TO_M; // ≈ 1.43996 eV·nm

// --- Measured properties of the gas-phase diatomic NaCl molecule ---
// Source: OpenStax University Physics Vol. 3, §9.2 "Types of Molecular Bonds",
// Table 9.2.1 and the worked NaCl example.
export const NACL_BOND_LENGTH_NM = 0.236; // equilibrium separation r0
export const NACL_PAULI_ENERGY_AT_R0_EV = 0.32; // U_ex at r0 (Pauli repulsion)
export const NACL_DISSOCIATION_ENERGY_EV = 4.26; // homolytic, vs neutral atoms

// --- Shannon (1976) effective ionic radii, 6-coordinate, in nm ---
// Source: R. D. Shannon, Acta Cryst. A32 (1976) 751. Widely tabulated values.
export const SHANNON_RADIUS_NM = {
  "sodium-ion": 0.102, // Na+
  "chloride-ion": 0.181, // Cl-
  "potassium-ion": 0.138 // K+
} as const;

// --- Standard atomic weights (IUPAC 2021), in u ---
export const ATOMIC_MASS_AMU = {
  sodium: 22.989_769_28,
  chlorine: 35.45,
  potassium: 39.098_3
} as const;

export const KJ_PER_MOL_TO_EV = 1 / 96.485_332; // 1 eV = 96.485 kJ/mol
export const DEBYE_PER_E_NM = 48.032_1; // 1 e·nm = 48.032 D (1 e·Å = 4.803 D)

/**
 * Converts a force in eV/nm acting on a mass in u into an acceleration in nm/fs².
 * a[nm/fs²] = F[eV/nm] · FORCE_EV_NM_TO_ACC / mass[u].
 */
export const FORCE_EV_NM_TO_ACC =
  ((ELECTRON_VOLT_J / NM_TO_M) / ATOMIC_MASS_UNIT_KG) * 1e9 * (FS_TO_S * FS_TO_S);

// --- SPC/E rigid water model ---
// Source: Berendsen, Grigera & Straatsma (1987), "The Missing Term in Effective
// Pair Potentials", J. Phys. Chem. 91, 6269.
export const SPCE_WATER = {
  chargeOxygenE: -0.847_6,
  chargeHydrogenE: 0.423_8,
  bondLengthOhNm: 0.1, // O–H distance
  angleHohDeg: 109.47, // H–O–H angle
  sigmaOxygenNm: 0.316_6, // Lennard-Jones σ (O–O only)
  epsilonOxygenKjMol: 0.650_2, // Lennard-Jones ε (O–O only)
  massOxygenAmu: 15.999,
  massHydrogenAmu: 1.008,
  dipoleDebye: 2.35 // model dipole moment, for validation
} as const;

// --- Joung–Cheatham (2008) monovalent ion Lennard-Jones parameters, SPC/E set ---
// Source: Joung & Cheatham, J. Phys. Chem. B 112, 9020 (2008).
// Published as Rmin/2 (Å) and ε (kcal/mol); converted here to σ (nm) and ε (eV)
// via σ = (2·Rmin/2) / 2^(1/6) and 1 kcal/mol = 4.184 kJ/mol.
export const JOUNG_CHEATHAM_SPCE = {
  "sodium-ion": { sigmaNm: 0.215_955, epsilonKjMol: 1.475_45 }, // Rmin/2 1.212 Å, ε 0.352642 kcal/mol
  "chloride-ion": { sigmaNm: 0.483_046, epsilonKjMol: 0.053_492 } // Rmin/2 2.711 Å, ε 0.012785 kcal/mol
} as const;

export const SOURCE_NOTES = {
  constants: "NIST CODATA 2018 fundamental constants",
  ke2: "k·e² = 1.440 eV·nm (OpenStax University Physics Vol. 3 §9.2)",
  naclBond:
    "NaCl r0 = 0.236 nm, Pauli energy 0.32 eV at r0, D = 4.26 eV (OpenStax Univ. Physics Vol. 3 §9.2, Table 9.2.1)",
  ionicRadii: "Shannon effective ionic radii, 6-coordinate (Shannon 1976, Acta Cryst. A32 751)",
  masses: "IUPAC 2021 standard atomic weights",
  spceWater:
    "SPC/E rigid water model (Berendsen, Grigera & Straatsma 1987, J. Phys. Chem. 91, 6269)",
  ionWaterLj:
    "Joung & Cheatham 2008 (J. Phys. Chem. B 112, 9020) ion LJ parameters, SPC/E set; Lorentz–Berthelot mixing"
} as const;
