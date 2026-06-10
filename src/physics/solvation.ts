import {
  FORCE_EV_NM_TO_ACC,
  JOUNG_CHEATHAM_SPCE,
  KE2_EV_NM,
  KJ_PER_MOL_TO_EV,
  SPCE_WATER
} from "./constants";
import { CHLORIDE_ION, SODIUM_ION, type IonSpecies } from "./ions";
import {
  SPCE_INERTIA,
  SPCE_SITE_MASSES,
  SPCE_SITES,
  SPCE_TOTAL_MASS,
  type Quat,
  type Vec3
} from "./water";

// ---------------------------------------------------------------------------
// Unified solvation engine: single-site ions + rigid SPC/E water in one box.
// Non-bonded interactions are Coulomb + Lennard-Jones with Lorentz–Berthelot
// mixing. Ion LJ parameters are Joung–Cheatham (2008), SPC/E set; water O–O LJ
// is SPC/E. Units: nm, fs, eV, u, e (same as water.ts).
// ---------------------------------------------------------------------------

type LJ = { sigmaNm: number; epsilonEv: number } | null;

type BodySite = {
  offset: Vec3; // body-frame offset from COM (nm)
  chargeE: number;
  lj: LJ;
};

type Body = {
  isWater: boolean;
  label: string;
  color: string;
  /** Display radius (nm) for ions; ignored for water. */
  renderRadiusNm: number;
  massAmu: number;
  inertia: Vec3;
  comNm: Vec3;
  velNmPerFs: Vec3;
  orientation: Quat;
  angVelBodyRadPerFs: Vec3;
  sites: BodySite[];
};

export type SolvationSnapshot = {
  ions: { label: string; color: string; renderRadiusNm: number; positionNm: Vec3 }[];
  waters: { sitePositionsNm: [Vec3, Vec3, Vec3] }[];
  potentialEnergyEv: number;
  kineticEnergyEv: number;
  totalEnergyEv: number;
  /** Closest ion→water-oxygen distance (nm), or null if no ion/water pair. */
  minIonOxygenNm: number | null;
  elapsedFs: number;
};

const SPCE_O_LJ: LJ = {
  sigmaNm: SPCE_WATER.sigmaOxygenNm,
  epsilonEv: SPCE_WATER.epsilonOxygenKjMol * KJ_PER_MOL_TO_EV
};

function ionLj(species: IonSpecies): LJ {
  const p = JOUNG_CHEATHAM_SPCE[species.id as keyof typeof JOUNG_CHEATHAM_SPCE];
  return p ? { sigmaNm: p.sigmaNm, epsilonEv: p.epsilonKjMol * KJ_PER_MOL_TO_EV } : null;
}

function makeIonBody(species: IonSpecies, comNm: Vec3): Body {
  return {
    isWater: false,
    label: species.label,
    color: species.color,
    renderRadiusNm: species.renderRadiusNm,
    massAmu: species.massAmu,
    inertia: { x: 1, y: 1, z: 1 }, // unused (no torque on a point body)
    comNm: { ...comNm },
    velNmPerFs: zero(),
    orientation: { w: 1, x: 0, y: 0, z: 0 },
    angVelBodyRadPerFs: zero(),
    sites: [{ offset: zero(), chargeE: species.chargeE, lj: ionLj(species) }]
  };
}

function makeWaterBody(comNm: Vec3, orientation: Quat): Body {
  return {
    isWater: true,
    label: "H₂O",
    color: "#ff5d5d",
    renderRadiusNm: 0,
    massAmu: SPCE_TOTAL_MASS,
    inertia: { ...SPCE_INERTIA },
    comNm: { ...comNm },
    velNmPerFs: zero(),
    orientation: normalizeQuat(orientation),
    angVelBodyRadPerFs: zero(),
    sites: SPCE_SITES.map((s) => ({
      offset: { ...s.offset },
      chargeE: s.chargeE,
      lj: s.isOxygen ? SPCE_O_LJ : null
    }))
  };
}

export type SolvationConfig =
  | { kind: "ion"; species: IonSpecies; comNm: Vec3 }
  | { kind: "water"; comNm: Vec3; orientation?: Quat };

export class SolvationSystem {
  private bodies: Body[];
  private elapsedFs = 0;

  timeStepFs: number;
  dampingPerFs: number;

  constructor(configs: SolvationConfig[], timeStepFs = 0.2, dampingPerFs = 0.01) {
    this.bodies = configs.map((c) =>
      c.kind === "ion"
        ? makeIonBody(c.species, c.comNm)
        : makeWaterBody(c.comNm, c.orientation ?? { w: 1, x: 0, y: 0, z: 0 })
    );
    this.timeStepFs = timeStepFs;
    this.dampingPerFs = dampingPerFs;
  }

  step(iterations = 1) {
    for (let i = 0; i < iterations; i += 1) {
      this.integrateOnce();
    }
  }

  snapshot(): SolvationSnapshot {
    const worldSites = this.bodies.map((b) => this.worldSites(b));
    const ions: SolvationSnapshot["ions"] = [];
    const waters: SolvationSnapshot["waters"] = [];
    this.bodies.forEach((b, i) => {
      if (b.isWater) {
        waters.push({ sitePositionsNm: worldSites[i] as [Vec3, Vec3, Vec3] });
      } else {
        ions.push({
          label: b.label,
          color: b.color,
          renderRadiusNm: b.renderRadiusNm,
          positionNm: { ...worldSites[i][0] }
        });
      }
    });

    const potentialEnergyEv = this.potentialEnergy(worldSites);
    const kineticEnergyEv = this.kineticEnergy();
    return {
      ions,
      waters,
      potentialEnergyEv,
      kineticEnergyEv,
      totalEnergyEv: potentialEnergyEv + kineticEnergyEv,
      minIonOxygenNm: this.minIonOxygen(worldSites),
      elapsedFs: this.elapsedFs
    };
  }

  private worldSites(body: Body): Vec3[] {
    return body.sites.map((s) => vadd(body.comNm, qRotate(body.orientation, s.offset)));
  }

  private mixedLj(a: LJ, b: LJ): { sigma: number; epsilon: number } | null {
    if (!a || !b) {
      return null;
    }
    return { sigma: 0.5 * (a.sigmaNm + b.sigmaNm), epsilon: Math.sqrt(a.epsilonEv * b.epsilonEv) };
  }

  private computeSiteForces(worldSites: Vec3[][]): Vec3[][] {
    const forces = worldSites.map((sites) => sites.map(() => zero()));
    for (let i = 0; i < this.bodies.length; i += 1) {
      for (let j = i + 1; j < this.bodies.length; j += 1) {
        for (let a = 0; a < this.bodies[i].sites.length; a += 1) {
          for (let b = 0; b < this.bodies[j].sites.length; b += 1) {
            const pa = worldSites[i][a];
            const pb = worldSites[j][b];
            const d = vsub(pa, pb);
            const r = Math.max(vlen(d), 1e-6);
            const dir = vscale(d, 1 / r);

            let fMag =
              (KE2_EV_NM * this.bodies[i].sites[a].chargeE * this.bodies[j].sites[b].chargeE) /
              (r * r);

            const lj = this.mixedLj(this.bodies[i].sites[a].lj, this.bodies[j].sites[b].lj);
            if (lj) {
              const sr = lj.sigma / r;
              const sr6 = sr ** 6;
              const sr12 = sr6 * sr6;
              fMag += (24 * lj.epsilon * (2 * sr12 - sr6)) / r;
            }

            const f = vscale(dir, fMag);
            forces[i][a] = vadd(forces[i][a], f);
            forces[j][b] = vsub(forces[j][b], f);
          }
        }
      }
    }
    return forces;
  }

  private integrateOnce() {
    const dt = this.timeStepFs;
    const worldSites = this.bodies.map((b) => this.worldSites(b));
    const siteForces = this.computeSiteForces(worldSites);
    const damp = Math.max(0, 1 - this.dampingPerFs * dt);

    this.bodies.forEach((body, index) => {
      const sites = worldSites[index];
      const forces = siteForces[index];

      let netForce = zero();
      let torque = zero();
      for (let a = 0; a < body.sites.length; a += 1) {
        netForce = vadd(netForce, forces[a]);
        torque = vadd(torque, vcross(vsub(sites[a], body.comNm), forces[a]));
      }

      // Translation (symplectic Euler).
      const acc = vscale(netForce, FORCE_EV_NM_TO_ACC / body.massAmu);
      body.velNmPerFs = vscale(vadd(body.velNmPerFs, vscale(acc, dt)), damp);
      body.comNm = vadd(body.comNm, vscale(body.velNmPerFs, dt));

      // Rotation (water only).
      if (body.isWater) {
        const torqueBody = qRotateInverse(body.orientation, torque);
        const w = body.angVelBodyRadPerFs;
        const Iw = { x: body.inertia.x * w.x, y: body.inertia.y * w.y, z: body.inertia.z * w.z };
        const gyro = vcross(w, Iw);
        const angAcc = {
          x: (torqueBody.x * FORCE_EV_NM_TO_ACC - gyro.x) / body.inertia.x,
          y: (torqueBody.y * FORCE_EV_NM_TO_ACC - gyro.y) / body.inertia.y,
          z: (torqueBody.z * FORCE_EV_NM_TO_ACC - gyro.z) / body.inertia.z
        };
        body.angVelBodyRadPerFs = vscale(vadd(w, vscale(angAcc, dt)), damp);
        const wWorld = qRotate(body.orientation, body.angVelBodyRadPerFs);
        const spin: Quat = { w: 0, x: wWorld.x, y: wWorld.y, z: wWorld.z };
        const dq = quatScale(quatMul(spin, body.orientation), 0.5 * dt);
        body.orientation = normalizeQuat(quatAdd(body.orientation, dq));
      }
    });

    this.elapsedFs += dt;
  }

  private potentialEnergy(worldSites: Vec3[][]): number {
    let energy = 0;
    for (let i = 0; i < this.bodies.length; i += 1) {
      for (let j = i + 1; j < this.bodies.length; j += 1) {
        for (let a = 0; a < this.bodies[i].sites.length; a += 1) {
          for (let b = 0; b < this.bodies[j].sites.length; b += 1) {
            const r = Math.max(vlen(vsub(worldSites[i][a], worldSites[j][b])), 1e-6);
            energy +=
              (KE2_EV_NM * this.bodies[i].sites[a].chargeE * this.bodies[j].sites[b].chargeE) / r;
            const lj = this.mixedLj(this.bodies[i].sites[a].lj, this.bodies[j].sites[b].lj);
            if (lj) {
              const sr6 = (lj.sigma / r) ** 6;
              energy += 4 * lj.epsilon * (sr6 * sr6 - sr6);
            }
          }
        }
      }
    }
    return energy;
  }

  private kineticEnergy(): number {
    return this.bodies.reduce((sum, b) => {
      const transl = 0.5 * b.massAmu * vdot(b.velNmPerFs, b.velNmPerFs);
      let rot = 0;
      if (b.isWater) {
        const w = b.angVelBodyRadPerFs;
        rot = 0.5 * (b.inertia.x * w.x * w.x + b.inertia.y * w.y * w.y + b.inertia.z * w.z * w.z);
      }
      return sum + (transl + rot) / FORCE_EV_NM_TO_ACC;
    }, 0);
  }

  private minIonOxygen(worldSites: Vec3[][]): number | null {
    let min = Infinity;
    for (let i = 0; i < this.bodies.length; i += 1) {
      if (this.bodies[i].isWater) {
        continue;
      }
      const ionPos = worldSites[i][0];
      for (let j = 0; j < this.bodies.length; j += 1) {
        if (!this.bodies[j].isWater) {
          continue;
        }
        const o = worldSites[j][0];
        min = Math.min(min, vlen(vsub(ionPos, o)));
      }
    }
    return Number.isFinite(min) ? min : null;
  }
}

// --- scene presets ---

export type SolvationScenePreset = {
  id: string;
  label: string;
  description: string;
  timeStepFs: number;
  dampingPerFs: number;
  configs: SolvationConfig[];
};

/** Place `count` water molecules on a shell of radius r, each oriented so the
 *  oxygen (negative end) points toward a cation at the origin. */
function shellWaters(count: number, radiusNm: number, towardOrigin: boolean): SolvationConfig[] {
  return Array.from({ length: count }, (_, i): SolvationConfig => {
    // Distribute roughly on a sphere (Fibonacci).
    const y = 1 - (2 * (i + 0.5)) / count;
    const radial = Math.sqrt(Math.max(0, 1 - y * y));
    const phi = Math.PI * (3 - Math.sqrt(5)) * i;
    const dir = { x: Math.cos(phi) * radial, y, z: Math.sin(phi) * radial };
    const com = vscale(dir, radiusNm);
    // Water body +z is the dipole (points toward the H side, i.e. positive end).
    // For a cation we want the H side pointing OUTWARD, so +z = +dir (outward).
    const target = towardOrigin ? dir : vscale(dir, -1);
    return { kind: "water", comNm: com, orientation: quatFromZ(target) };
  });
}

export const SOLVATION_SCENES: SolvationScenePreset[] = [
  {
    id: "na-hydration",
    label: "Na+ hydration shell",
    description:
      "Water oxygens (negative end) turn toward Na+ and pack into a first hydration shell near the measured ~0.24 nm Na–O distance.",
    timeStepFs: 0.2,
    dampingPerFs: 0.02,
    configs: [{ kind: "ion", species: SODIUM_ION, comNm: { x: 0, y: 0, z: 0 } }, ...shellWaters(6, 0.42, true)]
  },
  {
    id: "nacl-in-water",
    label: "NaCl in water",
    description:
      "Na+ and Cl- each gather their own water shells — the first step of a salt dissolving.",
    timeStepFs: 0.2,
    dampingPerFs: 0.02,
    configs: [
      { kind: "ion", species: SODIUM_ION, comNm: { x: -0.34, y: 0, z: 0 } },
      { kind: "ion", species: CHLORIDE_ION, comNm: { x: 0.34, y: 0, z: 0 } },
      ...shellWaters(8, 0.6, true)
    ]
  }
];

export function solvationSystemFromPreset(preset: SolvationScenePreset): SolvationSystem {
  return new SolvationSystem(preset.configs, preset.timeStepFs, preset.dampingPerFs);
}

// --- vector / quaternion helpers (same conventions as water.ts) ---

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
function vdot(a: Vec3, b: Vec3): number {
  return a.x * b.x + a.y * b.y + a.z * b.z;
}
function vcross(a: Vec3, b: Vec3): Vec3 {
  return { x: a.y * b.z - a.z * b.y, y: a.z * b.x - a.x * b.z, z: a.x * b.y - a.y * b.x };
}
function vlen(a: Vec3): number {
  return Math.sqrt(vdot(a, a));
}
function quatMul(a: Quat, b: Quat): Quat {
  return {
    w: a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z,
    x: a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y,
    y: a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x,
    z: a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w
  };
}
function quatAdd(a: Quat, b: Quat): Quat {
  return { w: a.w + b.w, x: a.x + b.x, y: a.y + b.y, z: a.z + b.z };
}
function quatScale(a: Quat, s: number): Quat {
  return { w: a.w * s, x: a.x * s, y: a.y * s, z: a.z * s };
}
function normalizeQuat(q: Quat): Quat {
  const n = Math.sqrt(q.w * q.w + q.x * q.x + q.y * q.y + q.z * q.z) || 1;
  return { w: q.w / n, x: q.x / n, y: q.y / n, z: q.z / n };
}
function qRotate(q: Quat, v: Vec3): Vec3 {
  const vq: Quat = { w: 0, x: v.x, y: v.y, z: v.z };
  const conj: Quat = { w: q.w, x: -q.x, y: -q.y, z: -q.z };
  const r = quatMul(quatMul(q, vq), conj);
  return { x: r.x, y: r.y, z: r.z };
}
function qRotateInverse(q: Quat, v: Vec3): Vec3 {
  return qRotate({ w: q.w, x: -q.x, y: -q.y, z: -q.z }, v);
}

/** Shortest-arc quaternion rotating the body +z axis onto unit vector `to`. */
function quatFromZ(to: Vec3): Quat {
  const len = vlen(to) || 1;
  const t = { x: to.x / len, y: to.y / len, z: to.z / len };
  const dot = t.z; // dot(+z, t)
  if (dot < -0.999999) {
    return { w: 0, x: 1, y: 0, z: 0 }; // 180° about x
  }
  // axis = cross(+z, t) = (-t.y, t.x, 0)
  const q: Quat = { w: 1 + dot, x: -t.y, y: t.x, z: 0 };
  return normalizeQuat(q);
}
