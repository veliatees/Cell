import {
  DEBYE_PER_E_NM,
  FORCE_EV_NM_TO_ACC,
  KE2_EV_NM,
  KJ_PER_MOL_TO_EV,
  SPCE_WATER
} from "./constants";

// ---------------------------------------------------------------------------
// SPC/E rigid water — a small, self-contained molecular-dynamics module.
//
// Units throughout: length nm, time fs, energy eV, mass u (amu), charge e.
//   - Coulomb force  : F = KE2_EV_NM · q1 q2 / r²           [eV/nm]
//   - Lennard-Jones  : U = 4ε[(σ/r)¹² − (σ/r)⁶]             [eV], O–O only
//   - acceleration   : a = F · FORCE_EV_NM_TO_ACC / mass    [nm/fs²]
//   - kinetic energy : KE = ½ m v² / FORCE_EV_NM_TO_ACC     [eV]
//
// Each molecule is a rigid body: centre of mass, velocity, orientation
// (quaternion) and body-frame angular velocity. Geometry can never deform,
// which is exactly what "rigid SPC/E" means.
// ---------------------------------------------------------------------------

export type Vec3 = { x: number; y: number; z: number };
export type Quat = { w: number; x: number; y: number; z: number };

export type Site = {
  /** Body-frame offset from the centre of mass (nm). */
  offset: Vec3;
  chargeE: number;
  isOxygen: boolean;
};

export type WaterMolecule = {
  comNm: Vec3;
  velNmPerFs: Vec3;
  orientation: Quat;
  /** Angular velocity in the body frame (rad/fs). */
  angVelBodyRadPerFs: Vec3;
};

export type WaterSnapshot = {
  molecules: WaterMolecule[];
  /** World-space site positions per molecule: [O, H, H]. */
  sitePositionsNm: Vec3[][];
  potentialEnergyEv: number;
  kineticEnergyEv: number;
  totalEnergyEv: number;
  elapsedFs: number;
};

// --- SPC/E body-frame geometry, derived once from the sourced constants ---

const mO = SPCE_WATER.massOxygenAmu;
const mH = SPCE_WATER.massHydrogenAmu;
const TOTAL_MASS = mO + 2 * mH;

const half = (SPCE_WATER.angleHohDeg * Math.PI) / 180 / 2;
const rOH = SPCE_WATER.bondLengthOhNm;

// Place O at the origin, both H in the x–z plane, bisector along +z.
const hx = rOH * Math.sin(half);
const hz = rOH * Math.cos(half);
// Centre of mass lies on z by symmetry.
const comZ = (2 * mH * hz) / TOTAL_MASS;

export const SPCE_SITES: Site[] = [
  { offset: { x: 0, y: 0, z: -comZ }, chargeE: SPCE_WATER.chargeOxygenE, isOxygen: true },
  { offset: { x: hx, y: 0, z: hz - comZ }, chargeE: SPCE_WATER.chargeHydrogenE, isOxygen: false },
  { offset: { x: -hx, y: 0, z: hz - comZ }, chargeE: SPCE_WATER.chargeHydrogenE, isOxygen: false }
];

const SITE_MASSES = [mO, mH, mH];

// Principal moments of inertia about the COM (u·nm²); off-diagonals vanish by
// the molecule's symmetry, so the inertia tensor is diagonal in this frame.
const INERTIA: Vec3 = SPCE_SITES.reduce(
  (acc, site, index) => {
    const m = SITE_MASSES[index];
    const { x, y, z } = site.offset;
    return {
      x: acc.x + m * (y * y + z * z),
      y: acc.y + m * (x * x + z * z),
      z: acc.z + m * (x * x + y * y)
    };
  },
  { x: 0, y: 0, z: 0 }
);

const EPSILON_OO_EV = SPCE_WATER.epsilonOxygenKjMol * KJ_PER_MOL_TO_EV;
const SIGMA_OO_NM = SPCE_WATER.sigmaOxygenNm;

/** SPC/E dipole moment magnitude in Debye (origin-independent: molecule is neutral). */
export function spceDipoleDebye(): number {
  const mu = SPCE_SITES.reduce(
    (acc, site) => ({
      x: acc.x + site.chargeE * site.offset.x,
      y: acc.y + site.chargeE * site.offset.y,
      z: acc.z + site.chargeE * site.offset.z
    }),
    { x: 0, y: 0, z: 0 }
  );
  return vlen(mu) * DEBYE_PER_E_NM;
}

export type WaterConfig = {
  comNm: Vec3;
  /** Euler-free initial orientation; identity if omitted. */
  orientation?: Quat;
  velNmPerFs?: Vec3;
  angVelBodyRadPerFs?: Vec3;
};

export class WaterSystem {
  private molecules: WaterMolecule[];
  private elapsedFs = 0;

  timeStepFs: number;
  /** Optional velocity damping per fs (0 = energy-conserving NVE). */
  dampingPerFs: number;

  constructor(configs: WaterConfig[], timeStepFs = 0.25, dampingPerFs = 0) {
    this.molecules = configs.map((c) => ({
      comNm: { ...c.comNm },
      velNmPerFs: c.velNmPerFs ? { ...c.velNmPerFs } : zero(),
      orientation: normalizeQuat(c.orientation ?? { w: 1, x: 0, y: 0, z: 0 }),
      angVelBodyRadPerFs: c.angVelBodyRadPerFs ? { ...c.angVelBodyRadPerFs } : zero()
    }));
    this.timeStepFs = timeStepFs;
    this.dampingPerFs = dampingPerFs;
  }

  step(iterations = 1) {
    for (let i = 0; i < iterations; i += 1) {
      this.integrateOnce();
    }
  }

  snapshot(): WaterSnapshot {
    const sitePositionsNm = this.molecules.map((mol) => this.worldSites(mol));
    const potentialEnergyEv = this.potentialEnergy(sitePositionsNm);
    const kineticEnergyEv = this.kineticEnergy();
    return {
      molecules: this.molecules.map(cloneMolecule),
      sitePositionsNm,
      potentialEnergyEv,
      kineticEnergyEv,
      totalEnergyEv: potentialEnergyEv + kineticEnergyEv,
      elapsedFs: this.elapsedFs
    };
  }

  private worldSites(mol: WaterMolecule): Vec3[] {
    return SPCE_SITES.map((site) => vadd(mol.comNm, qRotate(mol.orientation, site.offset)));
  }

  /** Net force (eV/nm) on each site, grouped by molecule. */
  private computeSiteForces(sitePositions: Vec3[][]): Vec3[][] {
    const forces = sitePositions.map((sites) => sites.map(() => zero()));

    for (let i = 0; i < sitePositions.length; i += 1) {
      for (let j = i + 1; j < sitePositions.length; j += 1) {
        for (let a = 0; a < SPCE_SITES.length; a += 1) {
          for (let b = 0; b < SPCE_SITES.length; b += 1) {
            const pa = sitePositions[i][a];
            const pb = sitePositions[j][b];
            const d = vsub(pa, pb);
            const r = Math.max(vlen(d), 1e-6);
            const dir = vscale(d, 1 / r); // points from b toward a

            // Coulomb (eV/nm), positive = repulsive along dir (a pushed away from b).
            let fMag =
              (KE2_EV_NM * SPCE_SITES[a].chargeE * SPCE_SITES[b].chargeE) / (r * r);

            // Lennard-Jones between oxygens only.
            if (SPCE_SITES[a].isOxygen && SPCE_SITES[b].isOxygen) {
              const sr = SIGMA_OO_NM / r;
              const sr6 = sr ** 6;
              const sr12 = sr6 * sr6;
              fMag += (24 * EPSILON_OO_EV * (2 * sr12 - sr6)) / r;
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
    const sitePositions = this.molecules.map((mol) => this.worldSites(mol));
    const siteForces = this.computeSiteForces(sitePositions);

    this.molecules.forEach((mol, index) => {
      const sites = sitePositions[index];
      const forces = siteForces[index];

      // Net force and torque about the centre of mass.
      let netForce = zero();
      let torque = zero();
      for (let a = 0; a < SPCE_SITES.length; a += 1) {
        netForce = vadd(netForce, forces[a]);
        const arm = vsub(sites[a], mol.comNm);
        torque = vadd(torque, vcross(arm, forces[a]));
      }

      // --- Translation (symplectic Euler) ---
      const acc = vscale(netForce, FORCE_EV_NM_TO_ACC / TOTAL_MASS);
      mol.velNmPerFs = vadd(mol.velNmPerFs, vscale(acc, dt));
      if (this.dampingPerFs > 0) {
        mol.velNmPerFs = vscale(mol.velNmPerFs, Math.max(0, 1 - this.dampingPerFs * dt));
      }
      mol.comNm = vadd(mol.comNm, vscale(mol.velNmPerFs, dt));

      // --- Rotation (Euler's equations in the body frame) ---
      const torqueBody = qRotateInverse(mol.orientation, torque);
      const w = mol.angVelBodyRadPerFs;
      const Iw = { x: INERTIA.x * w.x, y: INERTIA.y * w.y, z: INERTIA.z * w.z };
      const gyro = vcross(w, Iw); // ω × (Iω)
      const angAcc = {
        x: (torqueBody.x * FORCE_EV_NM_TO_ACC - gyro.x) / INERTIA.x,
        y: (torqueBody.y * FORCE_EV_NM_TO_ACC - gyro.y) / INERTIA.y,
        z: (torqueBody.z * FORCE_EV_NM_TO_ACC - gyro.z) / INERTIA.z
      };
      mol.angVelBodyRadPerFs = vadd(w, vscale(angAcc, dt));
      if (this.dampingPerFs > 0) {
        mol.angVelBodyRadPerFs = vscale(
          mol.angVelBodyRadPerFs,
          Math.max(0, 1 - this.dampingPerFs * dt)
        );
      }

      // Advance the quaternion using world-frame angular velocity.
      const wWorld = qRotate(mol.orientation, mol.angVelBodyRadPerFs);
      const spin: Quat = { w: 0, x: wWorld.x, y: wWorld.y, z: wWorld.z };
      const dq = quatScale(quatMul(spin, mol.orientation), 0.5 * dt);
      mol.orientation = normalizeQuat(quatAdd(mol.orientation, dq));
    });

    this.elapsedFs += dt;
  }

  private potentialEnergy(sitePositions: Vec3[][]): number {
    let energy = 0;
    for (let i = 0; i < sitePositions.length; i += 1) {
      for (let j = i + 1; j < sitePositions.length; j += 1) {
        for (let a = 0; a < SPCE_SITES.length; a += 1) {
          for (let b = 0; b < SPCE_SITES.length; b += 1) {
            const r = Math.max(vlen(vsub(sitePositions[i][a], sitePositions[j][b])), 1e-6);
            energy += (KE2_EV_NM * SPCE_SITES[a].chargeE * SPCE_SITES[b].chargeE) / r;
            if (SPCE_SITES[a].isOxygen && SPCE_SITES[b].isOxygen) {
              const sr6 = (SIGMA_OO_NM / r) ** 6;
              energy += 4 * EPSILON_OO_EV * (sr6 * sr6 - sr6);
            }
          }
        }
      }
    }
    return energy;
  }

  private kineticEnergy(): number {
    return this.molecules.reduce((sum, mol) => {
      const transl = 0.5 * TOTAL_MASS * vdot(mol.velNmPerFs, mol.velNmPerFs);
      const w = mol.angVelBodyRadPerFs;
      const rot = 0.5 * (INERTIA.x * w.x * w.x + INERTIA.y * w.y * w.y + INERTIA.z * w.z * w.z);
      return sum + (transl + rot) / FORCE_EV_NM_TO_ACC;
    }, 0);
  }
}

// --- small vector / quaternion helpers ---

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
  return {
    x: a.y * b.z - a.z * b.y,
    y: a.z * b.x - a.x * b.z,
    z: a.x * b.y - a.y * b.x
  };
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

/** Rotate a vector by a quaternion: v' = q v q*. */
function qRotate(q: Quat, v: Vec3): Vec3 {
  const vq: Quat = { w: 0, x: v.x, y: v.y, z: v.z };
  const conj: Quat = { w: q.w, x: -q.x, y: -q.y, z: -q.z };
  const r = quatMul(quatMul(q, vq), conj);
  return { x: r.x, y: r.y, z: r.z };
}

/** Rotate a vector by the inverse (conjugate) of a quaternion. */
function qRotateInverse(q: Quat, v: Vec3): Vec3 {
  return qRotate({ w: q.w, x: -q.x, y: -q.y, z: -q.z }, v);
}

function cloneMolecule(mol: WaterMolecule): WaterMolecule {
  return {
    comNm: { ...mol.comNm },
    velNmPerFs: { ...mol.velNmPerFs },
    orientation: { ...mol.orientation },
    angVelBodyRadPerFs: { ...mol.angVelBodyRadPerFs }
  };
}
