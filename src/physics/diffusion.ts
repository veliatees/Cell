import {
  BOLTZMANN_CONSTANT_J_K,
  ION_DIFFUSION_M2_S,
  M2_S_TO_NM2_FS,
  WATER_SELF_DIFFUSION_M2_S,
  WATER_VISCOSITY_PA_S
} from "./constants";
import { CHLORIDE_ION, SODIUM_ION } from "./ions";

// ---------------------------------------------------------------------------
// Brownian (overdamped Langevin) dynamics.
//
// At the cell scale, motion is diffusion-dominated and inertia is irrelevant.
// A particle with diffusion coefficient D takes a random step each timestep:
//
//     Δx = (D / kT)·F·Δt  +  √(2 D Δt)·ξ        (ξ ~ N(0,1) per axis)
//
// The drift term carries the mobility μ = D/kT (Einstein relation). With no
// force it is pure diffusion, whose mean-squared displacement grows as
// ⟨r²⟩ = 6 D t in three dimensions.
//
// Units: length nm, time fs, energy eV·… handled in SI for kT. D is stored in
// nm²/fs (converted from the sourced m²/s values).
// ---------------------------------------------------------------------------

export type Vec3 = { x: number; y: number; z: number };

export type DiffParticle = {
  label: string;
  color: string;
  diffusionNm2PerFs: number;
  posNm: Vec3;
};

export type DiffusionSnapshot = {
  particles: { label: string; color: string; posNm: Vec3 }[];
  /** Mean-squared displacement from start (nm²), averaged over particles. */
  msdNm2: number;
  /** Root-mean-square displacement (nm). */
  rmsNm: number;
  elapsedFs: number;
};

/** Stokes–Einstein diffusion coefficient (m²/s) for a sphere of radius r (m). */
export function stokesEinsteinM2PerS(
  radiusM: number,
  temperatureK = 298,
  viscosityPaS = WATER_VISCOSITY_PA_S
): number {
  return (BOLTZMANN_CONSTANT_J_K * temperatureK) / (6 * Math.PI * viscosityPaS * radiusM);
}

export function diffusionNm2PerFs(dM2PerS: number): number {
  return dM2PerS * M2_S_TO_NM2_FS;
}

export type DiffusionConfig = {
  label: string;
  color: string;
  diffusionM2PerS: number;
  posNm: Vec3;
};

export class DiffusionSystem {
  private particles: DiffParticle[];
  private startPositions: Vec3[];
  private elapsedFs = 0;
  private seed: number;

  timeStepFs: number;

  constructor(configs: DiffusionConfig[], timeStepFs = 50, seed = 2_246_311) {
    this.particles = configs.map((c) => ({
      label: c.label,
      color: c.color,
      diffusionNm2PerFs: diffusionNm2PerFs(c.diffusionM2PerS),
      posNm: { ...c.posNm }
    }));
    this.startPositions = configs.map((c) => ({ ...c.posNm }));
    this.timeStepFs = timeStepFs;
    this.seed = seed >>> 0;
  }

  step(iterations = 1) {
    for (let i = 0; i < iterations; i += 1) {
      this.integrateOnce();
    }
  }

  snapshot(): DiffusionSnapshot {
    let msd = 0;
    this.particles.forEach((p, i) => {
      const s = this.startPositions[i];
      msd += (p.posNm.x - s.x) ** 2 + (p.posNm.y - s.y) ** 2 + (p.posNm.z - s.z) ** 2;
    });
    msd /= Math.max(this.particles.length, 1);
    return {
      particles: this.particles.map((p) => ({ label: p.label, color: p.color, posNm: { ...p.posNm } })),
      msdNm2: msd,
      rmsNm: Math.sqrt(msd),
      elapsedFs: this.elapsedFs
    };
  }

  private integrateOnce() {
    const dt = this.timeStepFs;
    for (const p of this.particles) {
      const amplitude = Math.sqrt(2 * p.diffusionNm2PerFs * dt);
      p.posNm = {
        x: p.posNm.x + amplitude * this.gaussian(),
        y: p.posNm.y + amplitude * this.gaussian(),
        z: p.posNm.z + amplitude * this.gaussian()
      };
    }
    this.elapsedFs += dt;
  }

  private nextRandom(): number {
    this.seed = (1_664_525 * this.seed + 1_013_904_223) >>> 0;
    return this.seed / 4_294_967_296;
  }

  private gaussian(): number {
    const u = Math.max(this.nextRandom(), Number.EPSILON);
    const v = Math.max(this.nextRandom(), Number.EPSILON);
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  }
}

// --- scene presets ---

export type DiffusionScenePreset = {
  id: string;
  label: string;
  description: string;
  timeStepFs: number;
  configs: DiffusionConfig[];
};

/** A puff of particles started at the origin, to watch them spread (an ink drop). */
function puff(count: number, color: string, label: string, dM2PerS: number): DiffusionConfig[] {
  return Array.from({ length: count }, () => ({
    label,
    color,
    diffusionM2PerS: dM2PerS,
    posNm: { x: 0, y: 0, z: 0 }
  }));
}

export const DIFFUSION_SCENES: DiffusionScenePreset[] = [
  {
    id: "ink-drop",
    label: "Diffusion (ink drop)",
    description:
      "200 tracer particles released at a point spread by Brownian motion; ⟨r²⟩ grows as 6·D·t.",
    timeStepFs: 100,
    configs: puff(200, "#6db5ff", "tracer", WATER_SELF_DIFFUSION_M2_S)
  },
  {
    id: "na-vs-cl",
    label: "Na+ vs Cl- diffusion",
    description:
      "Chloride diffuses faster than sodium (D 2.03 vs 1.33 ×10⁻⁹ m²/s); the Cl- cloud spreads wider.",
    timeStepFs: 100,
    configs: [
      ...puff(120, SODIUM_ION.color, "Na+", ION_DIFFUSION_M2_S["sodium-ion"]),
      ...puff(120, CHLORIDE_ION.color, "Cl-", ION_DIFFUSION_M2_S["chloride-ion"])
    ]
  }
];

export function diffusionSystemFromPreset(preset: DiffusionScenePreset): DiffusionSystem {
  return new DiffusionSystem(preset.configs, preset.timeStepFs);
}
