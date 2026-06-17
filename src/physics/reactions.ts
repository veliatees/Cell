import { M2_S_TO_NM2_FS } from "./constants";

// ---------------------------------------------------------------------------
// Reaction–diffusion: the first chemistry in the project.
//
// Particles of species A and B diffuse by Brownian motion in a periodic box and
// react on contact: A + B → C. The contact (Smoluchowski) picture is the honest
// grounding — for a diffusion-limited reaction the rate constant is
//
//     k = 4π (D_A + D_B) R          (Smoluchowski, 1917)
//
// where D are diffusion coefficients and R the reaction radius. We don't invent
// a rate; we let real diffusion + a contact radius produce one, and report it.
//
// Units: length nm, time fs. D stored in nm²/fs (from the sourced m²/s values).
// ---------------------------------------------------------------------------

export type Vec3 = { x: number; y: number; z: number };
export type Species = "A" | "B" | "C";

export type RxParticle = { species: Species; pos: Vec3 };

export type ReactionSnapshot = {
  particles: { species: Species; pos: Vec3 }[];
  countA: number;
  countB: number;
  countC: number;
  reactions: number;
  elapsedFs: number;
};

export type ReactionConfig = {
  countA?: number;
  countB?: number;
  boxNm?: number;
  diffusionM2PerS?: number; // shared D for A and B (C inherits it)
  reactionRadiusNm?: number;
  timeStepFs?: number;
  seed?: number;
};

export class ReactionSystem {
  private particles: RxParticle[];
  private box: number;
  private dNm2PerFs: number;
  private reactionRadiusNm: number;
  private reactions = 0;
  private elapsedFs = 0;
  private seed: number;

  timeStepFs: number;

  constructor(config: ReactionConfig = {}) {
    this.box = config.boxNm ?? 8;
    this.dNm2PerFs = (config.diffusionM2PerS ?? 2e-9) * M2_S_TO_NM2_FS;
    this.reactionRadiusNm = config.reactionRadiusNm ?? 0.6;
    this.timeStepFs = config.timeStepFs ?? 400;
    this.seed = (config.seed ?? 8_675_309) >>> 0;

    this.particles = [];
    const a = config.countA ?? 70;
    const b = config.countB ?? 70;
    for (let i = 0; i < a; i += 1) {
      this.particles.push({ species: "A", pos: this.randomPos() });
    }
    for (let i = 0; i < b; i += 1) {
      this.particles.push({ species: "B", pos: this.randomPos() });
    }
  }

  /** Smoluchowski diffusion-limited rate constant k = 4π(D_A+D_B)R, in nm³/fs. */
  smoluchowskiRate(): number {
    return 4 * Math.PI * (2 * this.dNm2PerFs) * this.reactionRadiusNm;
  }

  step(iterations = 1) {
    for (let i = 0; i < iterations; i += 1) {
      this.integrateOnce();
    }
  }

  snapshot(): ReactionSnapshot {
    let a = 0;
    let b = 0;
    let c = 0;
    for (const p of this.particles) {
      if (p.species === "A") a += 1;
      else if (p.species === "B") b += 1;
      else c += 1;
    }
    return {
      particles: this.particles.map((p) => ({ species: p.species, pos: { ...p.pos } })),
      countA: a,
      countB: b,
      countC: c,
      reactions: this.reactions,
      elapsedFs: this.elapsedFs
    };
  }

  private integrateOnce() {
    const amp = Math.sqrt(2 * this.dNm2PerFs * this.timeStepFs);
    for (const p of this.particles) {
      p.pos = this.wrap({
        x: p.pos.x + amp * this.gaussian(),
        y: p.pos.y + amp * this.gaussian(),
        z: p.pos.z + amp * this.gaussian()
      });
    }
    this.react();
    this.elapsedFs += this.timeStepFs;
  }

  /** A + B → C when an A and a B are within the reaction radius. */
  private react() {
    const r2 = this.reactionRadiusNm * this.reactionRadiusNm;
    const reacted = new Array<boolean>(this.particles.length).fill(false);
    for (let i = 0; i < this.particles.length; i += 1) {
      if (reacted[i] || this.particles[i].species !== "A") {
        continue;
      }
      for (let j = 0; j < this.particles.length; j += 1) {
        if (reacted[j] || this.particles[j].species !== "B") {
          continue;
        }
        if (this.dist2(this.particles[i].pos, this.particles[j].pos) <= r2) {
          // A becomes C at its position; B is consumed.
          this.particles[i].species = "C";
          reacted[i] = true;
          reacted[j] = true;
          this.reactions += 1;
          break;
        }
      }
    }
    if (reacted.some(Boolean)) {
      this.particles = this.particles.filter((p, idx) => !(reacted[idx] && p.species === "B"));
    }
  }

  private dist2(a: Vec3, b: Vec3): number {
    let dx = a.x - b.x;
    let dy = a.y - b.y;
    let dz = a.z - b.z;
    dx -= this.box * Math.round(dx / this.box);
    dy -= this.box * Math.round(dy / this.box);
    dz -= this.box * Math.round(dz / this.box);
    return dx * dx + dy * dy + dz * dz;
  }

  private wrap(p: Vec3): Vec3 {
    return {
      x: p.x - this.box * Math.round(p.x / this.box),
      y: p.y - this.box * Math.round(p.y / this.box),
      z: p.z - this.box * Math.round(p.z / this.box)
    };
  }

  private randomPos(): Vec3 {
    return {
      x: (this.nextRandom() - 0.5) * this.box,
      y: (this.nextRandom() - 0.5) * this.box,
      z: (this.nextRandom() - 0.5) * this.box
    };
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

export type ReactionScenePreset = {
  id: string;
  label: string;
  description: string;
  config: ReactionConfig;
};

export const REACTION_SCENES: ReactionScenePreset[] = [
  {
    id: "reaction-abc",
    label: "Reaction A + B → C",
    description:
      "Two reactant species (A, B) diffuse and react on contact to form product C. The reaction is diffusion-limited — its rate follows Smoluchowski's k = 4π(D_A+D_B)R. Watch A and B fall as C rises.",
    config: { countA: 70, countB: 70, boxNm: 8, reactionRadiusNm: 0.6 }
  }
];

export function reactionSystemFromPreset(preset: ReactionScenePreset): ReactionSystem {
  return new ReactionSystem(preset.config);
}
