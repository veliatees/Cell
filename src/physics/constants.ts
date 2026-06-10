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

export const SOURCE_NOTES = {
  constants: "NIST CODATA 2018 fundamental constants",
  ke2: "k·e² = 1.440 eV·nm (OpenStax University Physics Vol. 3 §9.2)",
  naclBond:
    "NaCl r0 = 0.236 nm, Pauli energy 0.32 eV at r0, D = 4.26 eV (OpenStax Univ. Physics Vol. 3 §9.2, Table 9.2.1)",
  ionicRadii: "Shannon effective ionic radii, 6-coordinate (Shannon 1976, Acta Cryst. A32 751)",
  masses: "IUPAC 2021 standard atomic weights"
} as const;
