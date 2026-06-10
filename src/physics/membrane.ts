// ---------------------------------------------------------------------------
// Cooke–Deserno solvent-free lipid membrane (the first mesoscale structure).
//
// Source: Cooke, Kremer & Deserno, "Efficient tunable generic model for fluid
// bilayer membranes", Phys. Rev. E 72, 011506 (2005). Each lipid = 1 head + 2
// tail beads. Pair potentials alone make lipids self-assemble into a fluid
// bilayer with NO explicit solvent.
//
// This is a GENERIC coarse-grained model in reduced units: length σ, energy ε,
// mass m (all = 1), time τ = σ√(m/ε). It is not in SI: by the paper's own
// calibration a bilayer is ~5σ thick ≈ 5 nm, so σ ≈ 1 nm. Forcing SI numbers
// here would be dishonest; we keep the model's native units and state the map.
//
// Potentials (paper Eqs. 1–4):
//   WCA repulsion  V_rep(r;b) = 4ε[(b/r)¹² − (b/r)⁶ + 1/4], r ≤ 2^{1/6} b
//     b_head,head = b_head,tail = 0.95 σ ; b_tail,tail = σ
//   FENE bond      V = −½ k r∞² ln[1 − (r/r∞)²], k = 30 ε/σ², r∞ = 1.5 σ
//   bending spring V = ½ k_bend (r − 4σ)², k_bend = 10 ε/σ² (head ↔ 2nd tail)
//   tail attraction V_attr = −ε                      r < r_c
//                            −ε cos²[π(r−r_c)/(2 w_c)] r_c ≤ r ≤ r_c+w_c
//     with r_c = 2^{1/6} σ and tunable range w_c (1.6 σ → fluid bilayer)
//   thermostat: Langevin at k_BT = 1.1 ε.
// ---------------------------------------------------------------------------

export type Vec3 = { x: number; y: number; z: number };
export type BeadKind = "head" | "tail";

export type Bead = { kind: BeadKind; lipid: number; pos: Vec3; vel: Vec3 };

export type MembraneSnapshot = {
  beads: { kind: BeadKind; lipid: number; pos: Vec3 }[];
  /** [head, tail1, tail2] bead indices per lipid, for drawing bonds. */
  lipids: [number, number, number][];
  potentialEnergy: number;
  /** Nematic order S = ½⟨3cos²θ − 1⟩ of lipid axes vs the bilayer normal (z). */
  orderS: number;
  /** Bilayer thickness estimate (σ): head–head peak separation across leaflets. */
  thicknessSigma: number;
  elapsedTau: number;
};

const TWO_POW_1_6 = 2 ** (1 / 6);

// --- sourced model parameters (reduced units) ---
const EPS = 1;
const SIGMA = 1;
const B_HEAD = 0.95 * SIGMA; // head-head and head-tail WCA diameter
const B_TAIL = 1.0 * SIGMA; // tail-tail WCA diameter
const K_BOND = 30 * EPS; // FENE stiffness (ε/σ²)
const R_INF = 1.5 * SIGMA; // FENE divergence length
const K_BEND = 10 * EPS; // bending spring stiffness (ε/σ²)
const REST_BEND = 4 * SIGMA; // head ↔ tail2 rest length
const RC_ATTR = TWO_POW_1_6 * SIGMA; // tail attraction onset (tail WCA cutoff)

export type MembraneConfig = {
  /** Lipids per side of the square patch (per leaflet). */
  perSide?: number;
  /** Lattice spacing of the patch (σ). */
  spacingSigma?: number;
  wc?: number; // attraction range (σ)
  kT?: number; // temperature (ε)
  dt?: number; // timestep (τ)
  gamma?: number; // Langevin friction (1/τ)
  /** Start as a pre-assembled bilayer (default) or a random gas to self-assemble. */
  mode?: "bilayer" | "gas";
  boxSigma?: number; // box size for the gas mode
  seed?: number;
};

export class MembraneSystem {
  private beads: Bead[];
  private lipids: [number, number, number][];
  private elapsedTau = 0;
  private seed: number;

  wc: number;
  kT: number;
  dt: number;
  gamma: number;
  /** Lateral periodic box (σ) in x and y; z (the membrane normal) is free. */
  private lx: number;
  private ly: number;

  constructor(config: MembraneConfig = {}) {
    this.wc = config.wc ?? 1.6;
    this.kT = config.kT ?? 1.1;
    this.dt = config.dt ?? 0.01;
    this.gamma = config.gamma ?? 1.0;
    this.seed = (config.seed ?? 99_173) >>> 0;

    this.beads = [];
    this.lipids = [];
    if (config.mode === "gas") {
      const box = config.boxSigma ?? 14;
      this.lx = box;
      this.ly = box;
      this.buildGas(config.perSide ?? 8, box);
    } else {
      const perSide = config.perSide ?? 8;
      const spacing = config.spacingSigma ?? 1.25;
      this.lx = perSide * spacing;
      this.ly = perSide * spacing;
      this.buildBilayer(perSide, spacing);
    }
    this.thermalizeVelocities();
  }

  /** Minimum-image displacement in the periodic x,y plane (z untouched). */
  private minImage(d: Vec3): Vec3 {
    return {
      x: d.x - this.lx * Math.round(d.x / this.lx),
      y: d.y - this.ly * Math.round(d.y / this.ly),
      z: d.z
    };
  }

  step(iterations = 1) {
    for (let i = 0; i < iterations; i += 1) {
      this.integrateOnce();
    }
  }

  snapshot(): MembraneSnapshot {
    return {
      beads: this.beads.map((b) => ({ kind: b.kind, lipid: b.lipid, pos: { ...b.pos } })),
      lipids: this.lipids.map((l) => [...l] as [number, number, number]),
      potentialEnergy: this.potentialEnergy(),
      orderS: this.orderParameter(),
      thicknessSigma: this.thickness(),
      elapsedTau: this.elapsedTau
    };
  }

  // --- construction ---

  private addLipid(headPos: Vec3, axis: Vec3) {
    // axis points from head toward the tails (unit); beads spaced ~1σ.
    const head: Bead = { kind: "head", lipid: this.lipids.length, pos: { ...headPos }, vel: zero() };
    const t1: Bead = { kind: "tail", lipid: this.lipids.length, pos: vadd(headPos, vscale(axis, 1.0)), vel: zero() };
    const t2: Bead = { kind: "tail", lipid: this.lipids.length, pos: vadd(headPos, vscale(axis, 2.0)), vel: zero() };
    const base = this.beads.length;
    this.beads.push(head, t1, t2);
    this.lipids.push([base, base + 1, base + 2]);
  }

  private buildBilayer(perSide: number, spacing: number) {
    const offset = ((perSide - 1) * spacing) / 2;
    const headZ = 2.6; // outer head height; tails reach toward the midplane (z≈0)
    for (let i = 0; i < perSide; i += 1) {
      for (let j = 0; j < perSide; j += 1) {
        const x = i * spacing - offset;
        const y = j * spacing - offset;
        // upper leaflet: head up (+z), tails pointing down toward midplane
        this.addLipid({ x, y, z: headZ }, { x: 0, y: 0, z: -1 });
        // lower leaflet: head down (−z), tails pointing up toward midplane
        this.addLipid({ x, y, z: -headZ }, { x: 0, y: 0, z: 1 });
      }
    }
  }

  private buildGas(perSide: number, box: number) {
    const count = perSide * perSide * 2;
    for (let n = 0; n < count; n += 1) {
      const head = { x: (this.nextRandom() - 0.5) * box, y: (this.nextRandom() - 0.5) * box, z: (this.nextRandom() - 0.5) * box };
      const axis = randomUnit(() => this.nextRandom());
      this.addLipid(head, axis);
    }
  }

  private thermalizeVelocities() {
    const sigmaV = Math.sqrt(this.kT); // m = 1
    for (const b of this.beads) {
      b.vel = {
        x: this.gaussian() * sigmaV,
        y: this.gaussian() * sigmaV,
        z: this.gaussian() * sigmaV
      };
    }
  }

  // --- dynamics (BAOAB-style Langevin) ---

  private integrateOnce() {
    const dt = this.dt;
    const forces = this.computeForces();
    // B (half kick) + A (drift)
    this.beads.forEach((b, i) => {
      b.vel = vadd(b.vel, vscale(forces[i], 0.5 * dt));
      b.pos = vadd(b.pos, vscale(b.vel, dt));
    });
    const forces2 = this.computeForces();
    // B (half kick)
    this.beads.forEach((b, i) => {
      b.vel = vadd(b.vel, vscale(forces2[i], 0.5 * dt));
    });
    // O (Ornstein–Uhlenbeck thermostat)
    const c = Math.exp(-this.gamma * dt);
    const noiseScale = Math.sqrt((1 - c * c) * this.kT);
    for (const b of this.beads) {
      b.vel = {
        x: c * b.vel.x + noiseScale * this.gaussian(),
        y: c * b.vel.y + noiseScale * this.gaussian(),
        z: c * b.vel.z + noiseScale * this.gaussian()
      };
    }
    this.elapsedTau += dt;
  }

  private computeForces(): Vec3[] {
    const forces: Vec3[] = this.beads.map(() => zero());

    // Non-bonded: all pairs in DIFFERENT lipids (the 3 intramolecular pairs are
    // handled by FENE/bend springs and excluded here).
    for (let i = 0; i < this.beads.length; i += 1) {
      for (let j = i + 1; j < this.beads.length; j += 1) {
        if (this.beads[i].lipid === this.beads[j].lipid) {
          continue;
        }
        const d = this.minImage(vsub(this.beads[i].pos, this.beads[j].pos));
        const r = Math.max(vlen(d), 1e-6);
        const bothTail = this.beads[i].kind === "tail" && this.beads[j].kind === "tail";
        const b = bothTail ? B_TAIL : B_HEAD;

        let fOverR = wcaForceOverR(r, b);
        if (bothTail) {
          fOverR += this.attractionForceOverR(r);
        }
        if (fOverR !== 0) {
          const f = vscale(d, fOverR);
          forces[i] = vadd(forces[i], f);
          forces[j] = vsub(forces[j], f);
        }
      }
    }

    // Bonded springs per lipid.
    for (const [h, t1, t2] of this.lipids) {
      this.applyPairForce(forces, h, t1, feneForceOverR);
      this.applyPairForce(forces, t1, t2, feneForceOverR);
      this.applyPairForce(forces, h, t2, bendForceOverR);
    }
    return forces;
  }

  private applyPairForce(forces: Vec3[], i: number, j: number, forceOverR: (r: number) => number) {
    const d = vsub(this.beads[i].pos, this.beads[j].pos);
    const r = Math.max(vlen(d), 1e-6);
    const f = vscale(d, forceOverR(r));
    forces[i] = vadd(forces[i], f);
    forces[j] = vsub(forces[j], f);
  }

  /** d/dr of the tail attraction, returned as (−dV/dr)/r (attractive ⇒ negative). */
  private attractionForceOverR(r: number): number {
    if (r < RC_ATTR) {
      return 0; // flat well bottom: no attractive gradient (WCA dominates)
    }
    if (r > RC_ATTR + this.wc) {
      return 0;
    }
    // V = −ε cos²(x), x = π(r−rc)/(2wc); dV/dr = ε (π/wc) cos x sin x
    const x = (Math.PI * (r - RC_ATTR)) / (2 * this.wc);
    const dVdr = EPS * (Math.PI / this.wc) * Math.cos(x) * Math.sin(x);
    return -dVdr / r;
  }

  // --- measurements ---

  private potentialEnergy(): number {
    let e = 0;
    for (let i = 0; i < this.beads.length; i += 1) {
      for (let j = i + 1; j < this.beads.length; j += 1) {
        if (this.beads[i].lipid === this.beads[j].lipid) {
          continue;
        }
        const r = Math.max(vlen(this.minImage(vsub(this.beads[i].pos, this.beads[j].pos))), 1e-6);
        const bothTail = this.beads[i].kind === "tail" && this.beads[j].kind === "tail";
        e += wcaEnergy(r, bothTail ? B_TAIL : B_HEAD);
        if (bothTail) {
          e += this.attractionEnergy(r);
        }
      }
    }
    for (const [h, t1, t2] of this.lipids) {
      e += feneEnergy(beadDist(this.beads, h, t1));
      e += feneEnergy(beadDist(this.beads, t1, t2));
      const rb = beadDist(this.beads, h, t2);
      e += 0.5 * K_BEND * (rb - REST_BEND) ** 2;
    }
    return e;
  }

  private attractionEnergy(r: number): number {
    if (r < RC_ATTR) {
      return -EPS;
    }
    if (r > RC_ATTR + this.wc) {
      return 0;
    }
    return -EPS * Math.cos((Math.PI * (r - RC_ATTR)) / (2 * this.wc)) ** 2;
  }

  private orderParameter(): number {
    // S = ½⟨3 (a·n)² − 1⟩ with n = z axis; a = lipid head→tail2 axis.
    let sum = 0;
    for (const [h, , t2] of this.lipids) {
      const a = vsub(this.beads[t2].pos, this.beads[h].pos);
      const len = vlen(a) || 1;
      const cz = a.z / len;
      sum += 0.5 * (3 * cz * cz - 1);
    }
    return sum / Math.max(this.lipids.length, 1);
  }

  private thickness(): number {
    const headZ = this.beads.filter((b) => b.kind === "head").map((b) => b.pos.z);
    const upper = headZ.filter((z) => z > 0);
    const lower = headZ.filter((z) => z < 0);
    if (!upper.length || !lower.length) {
      return 0;
    }
    return mean(upper) - mean(lower);
  }

  // --- seeded RNG ---
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

// --- potential helpers (forces returned as (−dV/dr)/r) ---

function wcaForceOverR(r: number, b: number): number {
  const rc = TWO_POW_1_6 * b;
  if (r > rc) {
    return 0;
  }
  const br6 = (b / r) ** 6;
  const br12 = br6 * br6;
  // V = 4ε(br12 − br6 + 1/4); −dV/dr = 4ε(12 br12 − 6 br6)/r ; /r again ⇒ /r²
  return (4 * EPS * (12 * br12 - 6 * br6)) / (r * r);
}

function wcaEnergy(r: number, b: number): number {
  const rc = TWO_POW_1_6 * b;
  if (r > rc) {
    return 0;
  }
  const br6 = (b / r) ** 6;
  return 4 * EPS * (br6 * br6 - br6 + 0.25);
}

function feneForceOverR(r: number): number {
  const x = (r / R_INF) ** 2;
  // V = −½ k r∞² ln(1−x); −dV/dr = −k r /(1−x); /r ⇒ −k/(1−x)
  return -K_BOND / Math.max(1 - x, 1e-6);
}

function feneEnergy(r: number): number {
  const x = Math.min((r / R_INF) ** 2, 1 - 1e-9);
  return -0.5 * K_BOND * R_INF * R_INF * Math.log(1 - x);
}

function bendForceOverR(r: number): number {
  // V = ½ k_bend (r − rest)²; −dV/dr = −k_bend (r − rest); /r
  return (-K_BEND * (r - REST_BEND)) / r;
}

// --- scene presets ---

export type MembraneScenePreset = {
  id: string;
  label: string;
  description: string;
  config: MembraneConfig;
};

export const MEMBRANE_SCENES: MembraneScenePreset[] = [
  {
    id: "bilayer-patch",
    label: "Lipid bilayer patch",
    description:
      "A pre-assembled Cooke–Deserno bilayer (heads out, tails in) held together by tail attraction — the first inside/outside boundary. Thickness ~5σ ≈ 5 nm.",
    config: { perSide: 8, mode: "bilayer" }
  },
  {
    id: "self-assembly",
    label: "Membrane self-assembly",
    description:
      "Lipids released as a random gas spontaneously cluster, tails-together, into a bilayer — no solvent needed.",
    config: { perSide: 7, mode: "gas", boxSigma: 13 }
  }
];

export function membraneSystemFromPreset(preset: MembraneScenePreset): MembraneSystem {
  return new MembraneSystem(preset.config);
}

// --- vector helpers ---

function zero(): Vec3 {
  return { x: 0, y: 0, z: 0 };
}
function vadd(a: Vec3, b: Vec3): Vec3 {
  return { x: a.x + b.x, y: a.y + b.y, z: a.z + b.z };
}
function vsub(a: Vec3, b: Vec3): Vec3 {
  return { x: a.x - b.x, y: a.y - b.y, z: a.z - b.z };
}
function vscale(a: Vec3, s: number): Vec3 {
  return { x: a.x * s, y: a.y * s, z: a.z * s };
}
function vlen(a: Vec3): number {
  return Math.sqrt(a.x * a.x + a.y * a.y + a.z * a.z);
}
function beadDist(beads: Bead[], i: number, j: number): number {
  return Math.max(vlen(vsub(beads[i].pos, beads[j].pos)), 1e-6);
}
function mean(xs: number[]): number {
  return xs.reduce((s, x) => s + x, 0) / Math.max(xs.length, 1);
}
function randomUnit(next: () => number): Vec3 {
  const z = 2 * next() - 1;
  const t = 2 * Math.PI * next();
  const r = Math.sqrt(Math.max(0, 1 - z * z));
  return { x: r * Math.cos(t), y: r * Math.sin(t), z };
}
