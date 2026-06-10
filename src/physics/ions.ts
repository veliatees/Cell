import {
  ATOMIC_MASS_AMU,
  ATOMIC_MASS_UNIT_KG,
  BOLTZMANN_CONSTANT_J_K,
  COULOMB_CONSTANT_N_M2_C2,
  ELECTRON_VOLT_J,
  ELEMENTARY_CHARGE_C,
  FS_TO_S,
  KE2_EV_NM,
  NACL_BOND_LENGTH_NM,
  NACL_PAULI_ENERGY_AT_R0_EV,
  NM_TO_M,
  SHANNON_RADIUS_NM
} from "./constants";

export type Vec3 = {
  x: number;
  y: number;
  z: number;
};

export type IonSpecies = {
  id: string;
  label: string;
  atomicNumber: number;
  electronCount: number;
  chargeE: number;
  massAmu: number;
  renderRadiusNm: number;
  cloudRadiusNm: number;
  color: string;
};

export type IonState = {
  species: IonSpecies;
  positionNm: Vec3;
  velocityNmPerFs: Vec3;
  accelerationNmPerFs2: Vec3;
};

export type EnvironmentMode = "vacuum" | "implicit-water";

export type SimulationSettings = {
  environment: EnvironmentMode;
  timeStepFs: number;
  softeningNm: number;
  dampingPerFs: number;
  temperatureK: number;
  thermalNoise: boolean;
  forceCapN: number;
  /**
   * Pauli (core-electron) repulsion. Modeled as Born–Mayer U_ex = B·exp(-r/ρ),
   * where B and ρ are *derived* (not invented) from the measured NaCl bond
   * length and the measured 0.32 eV Pauli energy at that separation, plus the
   * equilibrium force-balance condition. Toggling it off isolates the Coulomb
   * term so collapse can be observed.
   */
  pauliRepulsion: boolean;
};

export type SimulationSnapshot = {
  ions: IonState[];
  /** Net force vectors (N) acting on each ion, index-aligned with `ions`. */
  forcesN: Vec3[];
  /** Distance between the first two ions, or 0 when fewer than two ions exist. */
  distanceNm: number;
  /** Magnitude of the net force on the first ion. */
  forceN: number;
  /** Total electrostatic potential energy of the system, summed over unique pairs. */
  potentialEnergyEv: number;
  kineticEnergyEv: number;
  totalEnergyEv: number;
  dielectric: number;
  elapsedFs: number;
};

/**
 * An initial configuration of ions. Presets let the same engine demonstrate
 * attraction (opposite charges), repulsion (like charges), and small clusters.
 */
export type ScenePreset = {
  id: string;
  label: string;
  description: string;
  ions: Array<{
    species: IonSpecies;
    positionNm: Vec3;
    velocityNmPerFs?: Vec3;
  }>;
};

export const SODIUM_ION: IonSpecies = {
  id: "sodium-ion",
  label: "Na+",
  atomicNumber: 11,
  electronCount: 10,
  chargeE: 1,
  massAmu: ATOMIC_MASS_AMU.sodium,
  renderRadiusNm: SHANNON_RADIUS_NM["sodium-ion"],
  cloudRadiusNm: SHANNON_RADIUS_NM["sodium-ion"],
  color: "#4aa3ff"
};

export const CHLORIDE_ION: IonSpecies = {
  id: "chloride-ion",
  label: "Cl-",
  atomicNumber: 17,
  electronCount: 18,
  chargeE: -1,
  massAmu: ATOMIC_MASS_AMU.chlorine,
  renderRadiusNm: SHANNON_RADIUS_NM["chloride-ion"],
  cloudRadiusNm: SHANNON_RADIUS_NM["chloride-ion"],
  color: "#f2c45b"
};

export const POTASSIUM_ION: IonSpecies = {
  id: "potassium-ion",
  label: "K+",
  atomicNumber: 19,
  electronCount: 18,
  chargeE: 1,
  massAmu: ATOMIC_MASS_AMU.potassium,
  renderRadiusNm: SHANNON_RADIUS_NM["potassium-ion"],
  cloudRadiusNm: SHANNON_RADIUS_NM["potassium-ion"],
  color: "#7ee0a8"
};

const zero = (): Vec3 => ({ x: 0, y: 0, z: 0 });

export const SCENE_PRESETS: ScenePreset[] = [
  {
    id: "na-cl",
    label: "Na+ / Cl- (gas-phase bond)",
    description:
      "Real NaCl: Coulomb attraction + measured Pauli repulsion settle the pair at the experimental 0.236 nm bond length (vacuum / gas phase).",
    ions: [
      { species: SODIUM_ION, positionNm: { x: -0.2, y: 0, z: 0 } },
      { species: CHLORIDE_ION, positionNm: { x: 0.2, y: 0, z: 0 } }
    ]
  },
  {
    id: "na-k",
    label: "Na+ / K+ (repulsion)",
    description: "Two like-charged cations: pure Coulomb repulsion pushes them apart.",
    ions: [
      { species: SODIUM_ION, positionNm: { x: -0.2, y: 0, z: 0 } },
      { species: POTASSIUM_ION, positionNm: { x: 0.2, y: 0, z: 0 } }
    ]
  },
  {
    id: "nacl-cluster",
    label: "NaCl cluster (6 ions, illustrative)",
    description:
      "Alternating Na+/Cl- ring. Na–Cl pairs use the sourced potential; like-pair repulsion is Coulomb-only, so treat the relaxed shape as illustrative.",
    ions: ringCluster()
  }
];

export const DEFAULT_PRESET = SCENE_PRESETS[0];

export const DEFAULT_SETTINGS: SimulationSettings = {
  environment: "vacuum",
  timeStepFs: 0.3,
  softeningNm: 0,
  dampingPerFs: 0.02,
  temperatureK: 310,
  thermalNoise: false,
  forceCapN: 2e-7,
  pauliRepulsion: true
};

export class IonSimulation {
  private ions: IonState[];
  private elapsedFs = 0;
  private randomSeed = 12_345;
  private preset: ScenePreset;

  settings: SimulationSettings;

  constructor(
    settings: SimulationSettings = DEFAULT_SETTINGS,
    preset: ScenePreset = DEFAULT_PRESET
  ) {
    this.settings = { ...settings };
    this.preset = preset;
    this.ions = ionsFromPreset(preset);
    this.recalculateAccelerations();
  }

  /** Replace the active scene and restart from its initial configuration. */
  setPreset(preset: ScenePreset) {
    this.preset = preset;
    this.reset();
  }

  reset() {
    this.ions = ionsFromPreset(this.preset);
    this.elapsedFs = 0;
    this.randomSeed = 12_345;
    this.recalculateAccelerations();
  }

  step(iterations = 1) {
    for (let i = 0; i < iterations; i += 1) {
      this.integrateOnce();
    }
  }

  snapshot(): SimulationSnapshot {
    const forcesN = this.computeForces();
    const distanceNm =
      this.ions.length >= 2
        ? distance(this.ions[0].positionNm, this.ions[1].positionNm)
        : 0;
    const potentialEnergyEv = this.computePotentialEnergyEv();
    const kineticEnergyEv = this.computeKineticEnergyEv();

    return {
      ions: cloneIons(this.ions),
      forcesN,
      distanceNm,
      forceN: length(forcesN[0] ?? zero()),
      potentialEnergyEv,
      kineticEnergyEv,
      totalEnergyEv: kineticEnergyEv + potentialEnergyEv,
      dielectric: dielectricFor(this.settings.environment),
      elapsedFs: this.elapsedFs
    };
  }

  private integrateOnce() {
    const dtFs = this.settings.timeStepFs;

    // Velocity Verlet: half-kick + drift using current accelerations.
    for (const ion of this.ions) {
      ion.velocityNmPerFs = add(ion.velocityNmPerFs, scale(ion.accelerationNmPerFs2, 0.5 * dtFs));
      ion.positionNm = add(ion.positionNm, scale(ion.velocityNmPerFs, dtFs));
    }

    this.recalculateAccelerations();

    // Second half-kick with the updated accelerations, then dissipative damping.
    const dampingFactor = Math.max(0, 1 - this.settings.dampingPerFs * dtFs);
    for (const ion of this.ions) {
      ion.velocityNmPerFs = add(ion.velocityNmPerFs, scale(ion.accelerationNmPerFs2, 0.5 * dtFs));
      ion.velocityNmPerFs = scale(ion.velocityNmPerFs, dampingFactor);
    }

    if (this.settings.thermalNoise) {
      this.applyThermalKick();
    }

    this.elapsedFs += dtFs;
  }

  private recalculateAccelerations() {
    const forces = this.computeForces();
    this.ions.forEach((ion, index) => {
      const massKg = ion.species.massAmu * ATOMIC_MASS_UNIT_KG;
      ion.accelerationNmPerFs2 = accelerationNToNmPerFs2(forces[index], massKg);
    });
  }

  /** Net electrostatic force (N) on each ion from every other ion. */
  private computeForces(): Vec3[] {
    const dielectric = dielectricFor(this.settings.environment);
    const softeningNm = this.settings.softeningNm;
    const forces: Vec3[] = this.ions.map(() => zero());

    for (let i = 0; i < this.ions.length; i += 1) {
      for (let j = i + 1; j < this.ions.length; j += 1) {
        const deltaNm = subtract(this.ions[j].positionNm, this.ions[i].positionNm);
        const rNm = Math.max(length(deltaNm), 1e-6);
        const directionToJ = scale(deltaNm, 1 / rNm);
        const softenedMeters = Math.sqrt(rNm * rNm + softeningNm * softeningNm) * NM_TO_M;
        const q1 = this.ions[i].species.chargeE * ELEMENTARY_CHARGE_C;
        const q2 = this.ions[j].species.chargeE * ELEMENTARY_CHARGE_C;
        const coulombN =
          (COULOMB_CONSTANT_N_M2_C2 * q1 * q2) /
          (dielectric * softenedMeters * softenedMeters);
        // Pauli (Born–Mayer) repulsion is always outward (positive sign here).
        const repulsionN = this.settings.pauliRepulsion
          ? bornMayerForceN(rNm, this.ions[i].species, this.ions[j].species)
          : 0;
        const cappedN = clamp(
          coulombN + repulsionN,
          -this.settings.forceCapN,
          this.settings.forceCapN
        );

        // Positive magnitude => repulsive => i is pushed away from j.
        const forceOnI = scale(directionToJ, -cappedN);
        forces[i] = add(forces[i], forceOnI);
        forces[j] = subtract(forces[j], forceOnI);
      }
    }

    return forces;
  }

  private computePotentialEnergyEv() {
    const dielectric = dielectricFor(this.settings.environment);
    const softeningNm = this.settings.softeningNm;
    let energyJ = 0;

    for (let i = 0; i < this.ions.length; i += 1) {
      for (let j = i + 1; j < this.ions.length; j += 1) {
        const rNm = Math.max(distance(this.ions[i].positionNm, this.ions[j].positionNm), 1e-6);
        const softenedMeters = Math.sqrt(rNm * rNm + softeningNm * softeningNm) * NM_TO_M;
        const q1 = this.ions[i].species.chargeE * ELEMENTARY_CHARGE_C;
        const q2 = this.ions[j].species.chargeE * ELEMENTARY_CHARGE_C;
        energyJ += (COULOMB_CONSTANT_N_M2_C2 * q1 * q2) / (dielectric * softenedMeters);
        if (this.settings.pauliRepulsion) {
          energyJ += bornMayerEnergyJ(rNm, this.ions[i].species, this.ions[j].species);
        }
      }
    }

    return energyJ / ELECTRON_VOLT_J;
  }

  private computeKineticEnergyEv() {
    return this.ions.reduce((sum, ion) => {
      const massKg = ion.species.massAmu * ATOMIC_MASS_UNIT_KG;
      const speedMPerS = length(ion.velocityNmPerFs) * 1e6;
      const energyJ = 0.5 * massKg * speedMPerS * speedMPerS;
      return sum + energyJ / ELECTRON_VOLT_J;
    }, 0);
  }

  private applyThermalKick() {
    const dtS = this.settings.timeStepFs * FS_TO_S;
    const tempScale = Math.sqrt(BOLTZMANN_CONSTANT_J_K * this.settings.temperatureK);

    for (const ion of this.ions) {
      const massKg = ion.species.massAmu * ATOMIC_MASS_UNIT_KG;
      const sigmaMPerS = (tempScale / Math.sqrt(massKg)) * Math.sqrt(dtS / 1e-12);
      const kick = {
        x: gaussianRandom(() => this.nextRandom()) * sigmaMPerS * 1e-6,
        y: gaussianRandom(() => this.nextRandom()) * sigmaMPerS * 1e-6,
        z: gaussianRandom(() => this.nextRandom()) * sigmaMPerS * 1e-6
      };
      ion.velocityNmPerFs = add(ion.velocityNmPerFs, kick);
    }
  }

  private nextRandom() {
    this.randomSeed = (1_664_525 * this.randomSeed + 1_013_904_223) % 4_294_967_296;
    return this.randomSeed / 4_294_967_296;
  }
}

export function dielectricFor(environment: EnvironmentMode) {
  return environment === "implicit-water" ? 78.4 : 1;
}

/**
 * Born–Mayer Pauli-repulsion parameters for the Na+/Cl- pair, U_ex = B·exp(-r/ρ).
 *
 * B and ρ are NOT free parameters. They are derived from two measured facts plus
 * the equilibrium condition, all sourced (OpenStax Univ. Physics Vol. 3 §9.2):
 *   (1) at r0 = 0.236 nm the net force is zero  ⇒  ke²/r0² = (B/ρ)·exp(-r0/ρ)
 *   (2) at r0 the Pauli energy is 0.32 eV       ⇒  B·exp(-r0/ρ) = U_ex(r0)
 * Dividing (1) by (2) gives ρ = U_ex(r0)·r0² / ke², then B follows from (2).
 */
const NACL_RHO_NM =
  (NACL_PAULI_ENERGY_AT_R0_EV * NACL_BOND_LENGTH_NM * NACL_BOND_LENGTH_NM) / KE2_EV_NM;
const NACL_B_EV =
  NACL_PAULI_ENERGY_AT_R0_EV * Math.exp(NACL_BOND_LENGTH_NM / NACL_RHO_NM);

/** True only for the {Na+, Cl-} pair, the one we have sourced repulsion data for. */
function isSodiumChloridePair(a: IonSpecies, b: IonSpecies): boolean {
  const ids = [a.id, b.id];
  return ids.includes("sodium-ion") && ids.includes("chloride-ion");
}

/** Born–Mayer repulsion force magnitude (N), outward: F = (B/ρ)·exp(-r/ρ). */
function bornMayerForceN(rNm: number, a: IonSpecies, b: IonSpecies): number {
  if (!isSodiumChloridePair(a, b)) {
    return 0;
  }
  const bJ = NACL_B_EV * ELECTRON_VOLT_J;
  const rhoM = NACL_RHO_NM * NM_TO_M;
  const rM = rNm * NM_TO_M;
  return (bJ / rhoM) * Math.exp(-rM / rhoM);
}

/** Born–Mayer repulsion potential energy (J): U = B·exp(-r/ρ). */
function bornMayerEnergyJ(rNm: number, a: IonSpecies, b: IonSpecies): number {
  if (!isSodiumChloridePair(a, b)) {
    return 0;
  }
  const bJ = NACL_B_EV * ELECTRON_VOLT_J;
  const rhoM = NACL_RHO_NM * NM_TO_M;
  const rM = rNm * NM_TO_M;
  return bJ * Math.exp(-rM / rhoM);
}

function ringCluster(): ScenePreset["ions"] {
  const species = [SODIUM_ION, CHLORIDE_ION];
  const count = 6;
  const radiusNm = 0.35;
  return Array.from({ length: count }, (_, index) => {
    const angle = (index / count) * Math.PI * 2;
    return {
      species: species[index % 2],
      positionNm: {
        x: Math.cos(angle) * radiusNm,
        y: Math.sin(angle) * radiusNm,
        z: 0
      }
    };
  });
}

function ionsFromPreset(preset: ScenePreset): IonState[] {
  return preset.ions.map((config) => ({
    species: config.species,
    positionNm: { ...config.positionNm },
    velocityNmPerFs: config.velocityNmPerFs ? { ...config.velocityNmPerFs } : zero(),
    accelerationNmPerFs2: zero()
  }));
}

function accelerationNToNmPerFs2(forceN: Vec3, massKg: number): Vec3 {
  // a[m/s^2] = F/m; convert m/s^2 -> nm/fs^2 by 1e9 nm/m / (1e15 fs/s)^2 = 1e-21.
  return scale(forceN, (1 / massKg) * 1e-21);
}

function cloneIons(ions: IonState[]): IonState[] {
  return ions.map((ion) => ({
    species: ion.species,
    positionNm: { ...ion.positionNm },
    velocityNmPerFs: { ...ion.velocityNmPerFs },
    accelerationNmPerFs2: { ...ion.accelerationNmPerFs2 }
  }));
}

function gaussianRandom(next: () => number) {
  const u = Math.max(next(), Number.EPSILON);
  const v = Math.max(next(), Number.EPSILON);
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function add(a: Vec3, b: Vec3): Vec3 {
  return { x: a.x + b.x, y: a.y + b.y, z: a.z + b.z };
}

function subtract(a: Vec3, b: Vec3): Vec3 {
  return { x: a.x - b.x, y: a.y - b.y, z: a.z - b.z };
}

function scale(vector: Vec3, scalar: number): Vec3 {
  return {
    x: vector.x * scalar,
    y: vector.y * scalar,
    z: vector.z * scalar
  };
}

function length(vector: Vec3) {
  return Math.sqrt(vector.x * vector.x + vector.y * vector.y + vector.z * vector.z);
}

function distance(a: Vec3, b: Vec3) {
  return length(subtract(a, b));
}
