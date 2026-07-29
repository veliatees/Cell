// Shared stochastic cytoplasmic flow field (active-stirring model).
//
// Real hepatocyte organelles move mostly by active, motor-driven cytoplasmic
// stirring, and they move *together* — the cytoplasm is a medium, not a bag of
// independent jitterers. This field supplies that coherent motion: a smooth,
// slowly time-varying, INCOMPRESSIBLE velocity field that all organelles are
// advected by, so they stream together while preserving cytoplasmic volume.
//
// Incompressibility is exact by construction: the field is the curl of a smooth
// vector potential built from a few seeded sinusoidal modes, and the curl of any
// field is divergence-free. For a single mode Psi = A*cos(k·x + w t + p), the
// curl is (k × A)*(-sin(k·x + w t + p)); summing modes stays divergence-free.
//
// The field is dimensionless (RMS ~ 1); the caller scales it by the grounded
// active-transport speed (Fort 2011 WIF-B9 hepatocyte, ~0.246 um/s) from the
// engine's cytoplasm_dynamics contract. Coherence length/time are a disclosed
// visual model, not a measured cytoplasmic velocity field.

type Vec3 = { x: number; y: number; z: number };

type FlowMode = {
  // k × A (mode velocity direction/amplitude), and wavevector k, temporal w, phase p.
  cx: number; cy: number; cz: number; // (k × A) * normalization
  kx: number; ky: number; kz: number;
  w: number;
  p: number;
};

// Small deterministic PRNG (mulberry32) so a seed fully reproduces the field.
function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export class CytoplasmFlowField {
  private readonly modes: FlowMode[];

  // coherenceLength: characteristic spatial scale of the stirring (world units).
  // coherenceTime: characteristic time over which the pattern evolves (seconds).
  constructor(
    seed: number,
    coherenceLength: number,
    coherenceTime: number,
    modeCount = 6
  ) {
    const rnd = mulberry32(seed);
    const kMag = 1 / Math.max(coherenceLength, 1e-6);
    const wMag = (2 * Math.PI) / Math.max(coherenceTime, 1e-6);
    const raw: FlowMode[] = [];
    for (let i = 0; i < modeCount; i += 1) {
      // Random unit wavevector, magnitude near 1/coherenceLength.
      const kdir = randUnit(rnd);
      const kscale = kMag * (0.6 + 0.8 * rnd());
      const kx = kdir.x * kscale, ky = kdir.y * kscale, kz = kdir.z * kscale;
      // Random potential amplitude direction (unit); k × A gives the velocity.
      const a = randUnit(rnd);
      const cx = ky * a.z - kz * a.y;
      const cy = kz * a.x - kx * a.z;
      const cz = kx * a.y - ky * a.x;
      raw.push({
        cx, cy, cz, kx, ky, kz,
        w: wMag * (0.6 + 0.8 * rnd()),
        p: rnd() * Math.PI * 2
      });
    }
    // Normalize so the field's spatial RMS speed is ~1 (dimensionless).
    const rms = estimateRms(raw, coherenceLength);
    const norm = rms > 1e-9 ? 1 / rms : 1;
    this.modes = raw.map((m) => ({ ...m, cx: m.cx * norm, cy: m.cy * norm, cz: m.cz * norm }));
  }

  // Write the dimensionless velocity at (x,y,z,t) into `out`.
  sampleInto(out: Vec3, x: number, y: number, z: number, t: number): void {
    let vx = 0, vy = 0, vz = 0;
    for (const m of this.modes) {
      const phase = m.kx * x + m.ky * y + m.kz * z + m.w * t + m.p;
      const s = -Math.sin(phase); // curl of A*cos(phase) -> (k×A)*(-sin(phase))
      vx += m.cx * s;
      vy += m.cy * s;
      vz += m.cz * s;
    }
    out.x = vx;
    out.y = vy;
    out.z = vz;
  }
}

function randUnit(rnd: () => number): Vec3 {
  // Marsaglia: uniform on the unit sphere.
  let x = 0, y = 0, s = 2;
  while (s >= 1 || s === 0) {
    x = 2 * rnd() - 1;
    y = 2 * rnd() - 1;
    s = x * x + y * y;
  }
  const f = 2 * Math.sqrt(1 - s);
  return { x: x * f, y: y * f, z: 1 - 2 * s };
}

function estimateRms(modes: FlowMode[], coherenceLength: number): number {
  const rnd = mulberry32(0x9e3779b9);
  const span = coherenceLength * 4;
  let acc = 0;
  const samples = 512;
  for (let i = 0; i < samples; i += 1) {
    const x = (rnd() - 0.5) * span;
    const y = (rnd() - 0.5) * span;
    const z = (rnd() - 0.5) * span;
    const t = rnd() * 10;
    let vx = 0, vy = 0, vz = 0;
    for (const m of modes) {
      const s = -Math.sin(m.kx * x + m.ky * y + m.kz * z + m.w * t + m.p);
      vx += m.cx * s; vy += m.cy * s; vz += m.cz * s;
    }
    acc += vx * vx + vy * vy + vz * vz;
  }
  return Math.sqrt(acc / samples);
}
