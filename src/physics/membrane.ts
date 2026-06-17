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
export type BeadKind = "head" | "tail" | "solute";

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
  /** Solute counts above (z>0) and below (z<0) the bilayer midplane. */
  soluteAbove: number;
  soluteBelow: number;
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
  /** Pre-assembled flat bilayer, a random gas, or a closed spherical vesicle. */
  mode?: "bilayer" | "gas" | "vesicle";
  boxSigma?: number; // box size for the gas mode
  vesicleRadiusSigma?: number; // mid-membrane radius for vesicle mode
  seed?: number;
  /** Number of solute particles placed above (outside) the membrane. */
  solutes?: number;
  /** Number of solute particles placed below (inside) the membrane. */
  solutesInside?: number;
  /** Cut a circular pore of this radius (σ) through the bilayer centre. */
  poreRadiusSigma?: number;
};

const B_SOLUTE = 1.0 * SIGMA; // solute WCA diameter (with lipids and each other)

export class MembraneSystem {
  private beads: Bead[];
  private lipids: [number, number, number][];
  private elapsedTau = 0;
  private seed: number;
  private geometry: "flat" | "vesicle" = "flat";

  wc: number;
  kT: number;
  dt: number;
  gamma: number;
  /** Lateral periodic box (σ) in x and y; z (the membrane normal) is free. */
  private lx: number;
  private ly: number;
  /** Flat sheets use x,y periodicity; a vesicle is a free 3D object. */
  private periodic = true;
  private stepCount = 0;
  private warmupSteps = 400;

  constructor(config: MembraneConfig = {}) {
    this.wc = config.wc ?? 1.6;
    this.kT = config.kT ?? 1.1;
    this.dt = config.dt ?? 0.01;
    this.gamma = config.gamma ?? 1.0;
    this.seed = (config.seed ?? 99_173) >>> 0;

    this.beads = [];
    this.lipids = [];
    if (config.mode === "vesicle") {
      this.geometry = "vesicle";
      this.periodic = false; // a vesicle is a free 3D object, not a periodic sheet
      this.lx = this.ly = 1e6; // unused
      const radius = config.vesicleRadiusSigma ?? 4;
      this.buildVesicle(radius);
      if (config.solutesInside) {
        this.buildSolutesSphere(config.solutesInside, Math.max(radius - 3.2, 0.8)); // inside the bag
      }
    } else if (config.mode === "gas") {
      const box = config.boxSigma ?? 14;
      this.lx = box;
      this.ly = box;
      this.buildGas(config.perSide ?? 8, box);
    } else {
      const perSide = config.perSide ?? 8;
      const spacing = config.spacingSigma ?? 1.25;
      this.lx = perSide * spacing;
      this.ly = perSide * spacing;
      this.buildBilayer(perSide, spacing, config.poreRadiusSigma ?? 0);
      if (config.solutes) {
        this.buildSolutes(config.solutes, 4.5); // outside (above)
      }
      if (config.solutesInside) {
        this.buildSolutes(config.solutesInside, -4.5); // inside (below)
      }
    }
    this.thermalizeVelocities();
  }

  /** Minimum-image displacement in the periodic x,y plane (z untouched). */
  private minImage(d: Vec3): Vec3 {
    if (!this.periodic) {
      return d;
    }
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
      soluteAbove: this.beads.filter((b) => b.kind === "solute" && b.pos.z > 0).length,
      soluteBelow: this.beads.filter((b) => b.kind === "solute" && b.pos.z < 0).length,
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

  private buildBilayer(perSide: number, spacing: number, poreRadius: number) {
    const offset = ((perSide - 1) * spacing) / 2;
    const headZ = 2.6; // outer head height; tails reach toward the midplane (z≈0)
    for (let i = 0; i < perSide; i += 1) {
      for (let j = 0; j < perSide; j += 1) {
        const x = i * spacing - offset;
        const y = j * spacing - offset;
        if (poreRadius > 0 && Math.hypot(x, y) < poreRadius) {
          continue; // leave a hole through the bilayer
        }
        // upper leaflet: head up (+z), tails pointing down toward midplane
        this.addLipid({ x, y, z: headZ }, { x: 0, y: 0, z: -1 });
        // lower leaflet: head down (−z), tails pointing up toward midplane
        this.addLipid({ x, y, z: -headZ }, { x: 0, y: 0, z: 1 });
      }
    }
  }

  /** Lipids tiled on a sphere: two leaflets, heads out/in, tails meeting at radius R. */
  private buildVesicle(radius: number) {
    // Match the flat bilayer's relaxed geometry: heads are ~2.6σ from the
    // midplane and second-tail beads sit at ±0.6σ, avoiding an artificial
    // overlap of both leaflets at one spherical surface.
    const headOffset = 2.6;
    const areaPerLipid = 4.5;
    const headOuter = radius + headOffset; // outer leaflet heads
    const headInner = Math.max(radius - headOffset, 1.2); // inner leaflet heads
    const nOuter = Math.max(12, Math.round((4 * Math.PI * headOuter * headOuter) / areaPerLipid));
    const nInner = Math.max(6, Math.round((4 * Math.PI * headInner * headInner) / areaPerLipid));
    this.placeLeaflet(nOuter, headOuter, -1); // outer: axis points inward
    this.placeLeaflet(nInner, headInner, +1); // inner: axis points outward
  }

  private placeLeaflet(n: number, headRadius: number, sign: number) {
    for (let i = 0; i < n; i += 1) {
      const u = fibonacciPoint(i, n);
      const headPos = { x: u.x * headRadius, y: u.y * headRadius, z: u.z * headRadius };
      const axis = { x: u.x * sign, y: u.y * sign, z: u.z * sign }; // unit radial
      this.addLipid(headPos, axis);
    }
  }

  private buildSolutesSphere(count: number, maxR: number) {
    for (let n = 0; n < count; n += 1) {
      let pos = zero();
      for (let attempt = 0; attempt < 400; attempt += 1) {
        const u = randomUnit(() => this.nextRandom());
        const r = maxR * Math.cbrt(this.nextRandom()) * 0.92;
        pos = { x: u.x * r, y: u.y * r, z: u.z * r };
        const clear = this.beads.every(
          (b) => b.kind !== "solute" || vlen(vsub(pos, b.pos)) > B_SOLUTE * 1.08
        );
        if (clear) {
          break;
        }
      }
      this.beads.push({
        kind: "solute",
        lipid: -1 - this.beads.length - n,
        pos,
        vel: zero()
      });
    }
  }

  private buildSolutes(count: number, baseZ: number) {
    // Spread solutes on a grid on one side of the bilayer (baseZ sign = side).
    const cols = Math.ceil(Math.sqrt(count));
    const sign = Math.sign(baseZ) || 1;
    const tag = this.beads.length; // unique negative lipid ids for every solute
    for (let n = 0; n < count; n += 1) {
      const i = n % cols;
      const j = Math.floor(n / cols);
      const x = (i / Math.max(cols - 1, 1) - 0.5) * this.lx * 0.8;
      const y = (j / Math.max(cols - 1, 1) - 0.5) * this.ly * 0.8;
      const z = baseZ + sign * (n % 3) * 0.8;
      this.beads.push({ kind: "solute", lipid: -1 - tag - n, pos: { x, y, z }, vel: zero() });
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
    // Soft start: for the first steps, cap forces so any initial bead overlaps
    // (unavoidable when tiling lipids on a sphere) relax gently instead of
    // exploding through the steep WCA wall. Standard MD warm-up; it does not
    // affect the equilibrium physics that follows.
    const warming = this.stepCount < this.warmupSteps;
    const forces = this.computeForces();
    if (warming) {
      capForces(forces, 80);
    }
    // B (half kick) + A (drift)
    this.beads.forEach((b, i) => {
      b.vel = vadd(b.vel, vscale(forces[i], 0.5 * dt));
      b.pos = vadd(b.pos, vscale(b.vel, dt));
    });
    const forces2 = this.computeForces();
    if (warming) {
      capForces(forces2, 80);
    }
    this.stepCount += 1;
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
    this.wrapPeriodic();
    this.elapsedTau += dt;
  }

  /**
   * Fold coordinates back into the periodic x,y box so they stay bounded (raw
   * unwrapped coordinates grow without limit as particles diffuse). Whole lipids
   * are shifted together — keyed on the head bead — so intramolecular bonds are
   * never split across the boundary; solutes wrap individually. z is untouched.
   */
  private wrapPeriodic() {
    if (!this.periodic) {
      return;
    }
    for (const [h] of this.lipids) {
      const head = this.beads[h];
      const sx = this.lx * Math.round(head.pos.x / this.lx);
      const sy = this.ly * Math.round(head.pos.y / this.ly);
      if (sx !== 0 || sy !== 0) {
        for (let k = 0; k < 3; k += 1) {
          this.beads[h + k].pos.x -= sx;
          this.beads[h + k].pos.y -= sy;
        }
      }
    }
    for (const b of this.beads) {
      if (b.kind === "solute") {
        b.pos.x -= this.lx * Math.round(b.pos.x / this.lx);
        b.pos.y -= this.ly * Math.round(b.pos.y / this.ly);
      }
    }
  }

  private computeForces(): Vec3[] {
    const forces: Vec3[] = this.beads.map(() => zero());

    // Non-bonded interactions, accelerated with a cell (neighbor) list so the
    // cost is O(N) instead of O(N²). The 3 intramolecular pairs per lipid are
    // excluded (handled by the FENE/bend springs below).
    this.forEachNonbondedPair((i, j) => this.pairForce(i, j, forces));

    // Bonded springs per lipid.
    for (const [h, t1, t2] of this.lipids) {
      this.applyPairForce(forces, h, t1, feneForceOverR);
      this.applyPairForce(forces, t1, t2, feneForceOverR);
      this.applyPairForce(forces, h, t2, bendForceOverR);
    }
    return forces;
  }

  /** WCA (+ tail attraction) force for one non-bonded pair, added into `forces`. */
  private pairForce(i: number, j: number, forces: Vec3[]) {
    if (this.beads[i].lipid === this.beads[j].lipid) {
      return;
    }
    const d = this.minImage(vsub(this.beads[i].pos, this.beads[j].pos));
    const r = Math.max(vlen(d), 1e-6);
    const involvesSolute = this.beads[i].kind === "solute" || this.beads[j].kind === "solute";
    const bothTail = this.beads[i].kind === "tail" && this.beads[j].kind === "tail";
    const b = involvesSolute ? B_SOLUTE : bothTail ? B_TAIL : B_HEAD;

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

  private forEachNonbondedPair(visit: (i: number, j: number) => void) {
    const n = this.beads.length;
    const rc = RC_ATTR + this.wc + 0.3; // interaction cutoff + small skin

    // For a small periodic box (fewer than 3 cells per side) the wrapped cell
    // list would double-count, so fall back to the direct O(N²) loop there.
    let ncx = 0;
    let ncy = 0;
    if (this.periodic) {
      ncx = Math.floor(this.lx / rc);
      ncy = Math.floor(this.ly / rc);
      if (ncx < 3 || ncy < 3) {
        for (let i = 0; i < n; i += 1) {
          for (let j = i + 1; j < n; j += 1) {
            visit(i, j);
          }
        }
        return;
      }
    }
    const csx = this.periodic ? this.lx / ncx : rc;
    const csy = this.periodic ? this.ly / ncy : rc;

    const cells = new Map<string, number[]>();
    const coords: Array<[number, number, number]> = new Array(n);
    for (let i = 0; i < n; i += 1) {
      const p = this.beads[i].pos;
      let cx: number;
      let cy: number;
      if (this.periodic) {
        cx = (((Math.floor((p.x + this.lx / 2) / csx) % ncx) + ncx) % ncx) | 0;
        cy = (((Math.floor((p.y + this.ly / 2) / csy) % ncy) + ncy) % ncy) | 0;
      } else {
        cx = Math.floor(p.x / csx);
        cy = Math.floor(p.y / csy);
      }
      const cz = Math.floor(p.z / rc);
      coords[i] = [cx, cy, cz];
      const k = `${cx},${cy},${cz}`;
      const arr = cells.get(k);
      if (arr) {
        arr.push(i);
      } else {
        cells.set(k, [i]);
      }
    }

    for (let i = 0; i < n; i += 1) {
      const [cx, cy, cz] = coords[i];
      for (let dx = -1; dx <= 1; dx += 1) {
        for (let dy = -1; dy <= 1; dy += 1) {
          for (let dz = -1; dz <= 1; dz += 1) {
            let nx = cx + dx;
            let ny = cy + dy;
            if (this.periodic) {
              nx = ((nx % ncx) + ncx) % ncx;
              ny = ((ny % ncy) + ncy) % ncy;
            }
            const arr = cells.get(`${nx},${ny},${cz + dz}`);
            if (!arr) {
              continue;
            }
            for (const j of arr) {
              if (j > i) {
                visit(i, j);
              }
            }
          }
        }
      }
    }
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
    this.forEachNonbondedPair((i, j) => {
      if (this.beads[i].lipid === this.beads[j].lipid) {
        return;
      }
      const r = Math.max(vlen(this.minImage(vsub(this.beads[i].pos, this.beads[j].pos))), 1e-6);
      const involvesSolute = this.beads[i].kind === "solute" || this.beads[j].kind === "solute";
      const bothTail = this.beads[i].kind === "tail" && this.beads[j].kind === "tail";
      e += wcaEnergy(r, involvesSolute ? B_SOLUTE : bothTail ? B_TAIL : B_HEAD);
      if (bothTail) {
        e += this.attractionEnergy(r);
      }
    });
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
    // S = ½⟨3 (a·n)² − 1⟩; flat membranes use z, vesicles use the local radial normal.
    let sum = 0;
    const center = this.geometry === "vesicle" ? this.vesicleCenter() : zero();
    for (const [h, , t2] of this.lipids) {
      const a = vsub(this.beads[t2].pos, this.beads[h].pos);
      const len = vlen(a) || 1;
      let cos = a.z / len;
      if (this.geometry === "vesicle") {
        const n = vsub(this.beads[h].pos, center);
        const nLen = vlen(n) || 1;
        cos = (a.x * n.x + a.y * n.y + a.z * n.z) / (len * nLen);
      }
      sum += 0.5 * (3 * cos * cos - 1);
    }
    return sum / Math.max(this.lipids.length, 1);
  }

  private thickness(): number {
    const headZ = this.beads.filter((b) => b.kind === "head").map((b) => b.pos.z);
    if (this.geometry === "vesicle") {
      const center = this.vesicleCenter();
      const radii = this.beads.filter((b) => b.kind === "head").map((b) => vlen(vsub(b.pos, center)));
      if (radii.length < 2) {
        return 0;
      }
      let inner = Math.min(...radii);
      let outer = Math.max(...radii);
      for (let i = 0; i < 8; i += 1) {
        const innerSet = radii.filter((r) => Math.abs(r - inner) <= Math.abs(r - outer));
        const outerSet = radii.filter((r) => Math.abs(r - outer) < Math.abs(r - inner));
        inner = mean(innerSet);
        outer = mean(outerSet);
      }
      return outer - inner;
    }
    const upper = headZ.filter((z) => z > 0);
    const lower = headZ.filter((z) => z < 0);
    if (!upper.length || !lower.length) {
      return 0;
    }
    return mean(upper) - mean(lower);
  }

  private vesicleCenter(): Vec3 {
    const heads = this.beads.filter((b) => b.kind === "head");
    if (!heads.length) {
      return zero();
    }
    return vscale(
      heads.reduce((sum, bead) => vadd(sum, bead.pos), zero()),
      1 / heads.length
    );
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
    id: "cell-reality",
    label: "Cell — one reality (vesicle)",
    description:
      "A whole closed cell: a spherical lipid membrane (vesicle) enclosing an interior, with particles trapped inside. One world, one clock — coarse-grained at the cell scale, but every rule is grounded in the atomic/chemical physics from the earlier milestones.",
    config: { mode: "vesicle", vesicleRadiusSigma: 6, solutesInside: 30 }
  },
  {
    id: "cell-flat",
    label: "Membrane boundary (flat slice)",
    description:
      "A flat membrane separating an inside from an outside, with particles in both compartments — a cut-through slice of a cell boundary.",
    config: { perSide: 8, mode: "bilayer", solutes: 18, solutesInside: 10 }
  },
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
  },
  {
    id: "membrane-barrier",
    label: "Barrier (intact bilayer)",
    description:
      "Solute particles (green) sit above an intact bilayer and cannot get through — the membrane's barrier function. Watch the above/below counts stay put.",
    config: { perSide: 8, mode: "bilayer", solutes: 24 }
  },
  {
    id: "membrane-pore",
    label: "Transport through a pore",
    description:
      "The same solutes, but the bilayer has a central pore — now they diffuse across to the other side. Transport through a channel.",
    config: { perSide: 8, mode: "bilayer", solutes: 24, poreRadiusSigma: 2.2 }
  }
];

export function membraneSystemFromPreset(preset: MembraneScenePreset): MembraneSystem {
  return new MembraneSystem(preset.config);
}

// --- vector helpers ---

function capForces(forces: Vec3[], maxMag: number) {
  const max2 = maxMag * maxMag;
  for (let i = 0; i < forces.length; i += 1) {
    const f = forces[i];
    const m2 = f.x * f.x + f.y * f.y + f.z * f.z;
    if (m2 > max2) {
      const s = maxMag / Math.sqrt(m2);
      forces[i] = { x: f.x * s, y: f.y * s, z: f.z * s };
    }
  }
}

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

/** i-th of n evenly distributed points on the unit sphere (Fibonacci spiral). */
function fibonacciPoint(i: number, n: number): Vec3 {
  const y = 1 - (2 * (i + 0.5)) / n;
  const radial = Math.sqrt(Math.max(0, 1 - y * y));
  const phi = Math.PI * (3 - Math.sqrt(5)) * i;
  return { x: Math.cos(phi) * radial, y, z: Math.sin(phi) * radial };
}
