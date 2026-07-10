// Source-bounded whole-cell plasma-membrane surface model.
//
// The visible hepatocyte scene is a 10 um-scale surface, not a molecular bilayer
// patch. At this scale, individual 100-200 nm endocytic pits are below render
// resolution, and a real plasma membrane cannot elastically balloon by 10%+.
// Therefore the production renderer treats the membrane as a radial graph over
// the rest sphere and enforces source-backed geometric bounds:
//   - lipid bilayers are nearly area-incompressible; micropipette aspiration
//     measurements put elastic stretch before failure at only a few percent
//     (Needham & Nunn, Biophys J 1990; Rawicz et al., Biophys J 2000),
//   - local clathrin/caveolar buds are nanoscopic relative to a whole hepatocyte
//     (~100-200 nm vs ~10 um radius), so whole-cell radial deviations are capped
//     at the corresponding percent-scale depth.
//
// Dynamics are OVERDAMPED (the cell is deep in the low-Reynolds regime — inertia
// is negligible), but the stiffness numbers below are dimensionless solver gains,
// not measured physical constants. The measured constraints are the area/radial
// bounds, and the code is careful not to present solver gains as biology.

export type MembraneEventKind = "endocytosis" | "exocytosis";

export type MembraneEvent = {
  kind: MembraneEventKind;
  dir: [number, number, number]; // unit direction of the patch centre
  t: number; // 0..1 life progress
  duration: number; // seconds (sim)
  radius: number; // angular patch radius (cos threshold)
  strength: number; // spontaneous-curvature drive magnitude
  budded: boolean; // endocytosis: has the vesicle pinched off yet
};

export type MembraneSim = {
  n: number; // vertex count
  radius: number;
  pos: Float32Array; // 3n current positions
  restDir: Float32Array; // 3n immutable outward directions; prevents surface fold-over
  vel: Float32Array; // 3n (kept for optional light inertia / diagnostics)
  force: Float32Array; // 3n scratch
  faces: Int32Array; // 3f
  // undirected edges with the two opposite vertices (closed surface → always 2)
  edgeA: Int32Array;
  edgeB: Int32Array;
  edgeOpp1: Int32Array;
  edgeOpp2: Int32Array;
  restLen: Float32Array; // per edge
  degree: Float32Array; // per-vertex valence (for the umbrella Laplacian)
  restLap: Float32Array; // 3n rest Laplacian (spontaneous-curvature / rest-shape ref)
  normals: Float32Array; // 3n outward vertex normals
  vertFaceStart: Int32Array; // CSR: incident faces per vertex
  vertFaceList: Int32Array;
  a0: number; // rest surface area
  v0: number; // rest enclosed volume
  events: MembraneEvent[];
  // Dimensionless numerical gains. These are not biological parameters.
  kStretch: number;
  kBend: number;
  kVolume: number;
  kEvent: number;
  gamma: number;
};

// Lipid bilayers tolerate only a few percent elastic area dilation before failure.
// We use 3% as a conservative visible-scene cap, sourced from micropipette
// aspiration bilayer mechanics (Needham & Nunn 1990; Rawicz et al. 2000).
export const MEMBRANE_ELASTIC_AREA_STRAIN_LIMIT = 0.03;

// 100-200 nm endocytic pits over a representative 10 um hepatocyte radius are
// order 1-2% of radius. This cap keeps whole-cell deformations in that regime.
export const MEMBRANE_WHOLE_CELL_RADIAL_DEVIATION_LIMIT = 0.015;

const MEMBRANE_RADIAL_MAX = Math.sqrt(1 + MEMBRANE_ELASTIC_AREA_STRAIN_LIMIT);
const MEMBRANE_RADIAL_MIN = 1 - MEMBRANE_WHOLE_CELL_RADIAL_DEVIATION_LIMIT;
const AREA_CORRECTION_ITERS = 9;

// ---- Icosphere construction -------------------------------------------------

function buildIcosphere(radius: number, subdiv: number): { pos: number[]; faces: number[] } {
  const t = (1 + Math.sqrt(5)) / 2;
  let verts: number[][] = [
    [-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0],
    [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t],
    [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1],
  ];
  let faces: number[][] = [
    [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
    [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
    [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
    [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1],
  ];
  for (let s = 0; s < subdiv; s += 1) {
    const mid = new Map<number, number>();
    const newFaces: number[][] = [];
    const midpoint = (a: number, b: number): number => {
      const key = a < b ? a * 100000 + b : b * 100000 + a;
      const found = mid.get(key);
      if (found !== undefined) return found;
      const m = [
        (verts[a][0] + verts[b][0]) / 2,
        (verts[a][1] + verts[b][1]) / 2,
        (verts[a][2] + verts[b][2]) / 2,
      ];
      const idx = verts.length;
      verts.push(m);
      mid.set(key, idx);
      return idx;
    };
    for (const [a, b, c] of faces) {
      const ab = midpoint(a, b), bc = midpoint(b, c), ca = midpoint(c, a);
      newFaces.push([a, ab, ca], [b, bc, ab], [c, ca, bc], [ab, bc, ca]);
    }
    faces = newFaces;
  }
  // project to the sphere
  const pos: number[] = [];
  for (const v of verts) {
    const L = Math.hypot(v[0], v[1], v[2]) || 1;
    pos.push((v[0] / L) * radius, (v[1] / L) * radius, (v[2] / L) * radius);
  }
  return { pos, faces: faces.flat() };
}

// ---- Topology: edges with opposite vertices, vertex→faces (CSR) --------------

export function createMembraneSim(radius: number, subdiv = 3): MembraneSim {
  const ico = buildIcosphere(radius, subdiv);
  const n = ico.pos.length / 3;
  const pos = new Float32Array(ico.pos);
  const restDir = new Float32Array(pos.length);
  for (let i = 0; i < pos.length; i += 3) {
    const L = Math.hypot(pos[i], pos[i + 1], pos[i + 2]) || 1;
    restDir[i] = pos[i] / L;
    restDir[i + 1] = pos[i + 1] / L;
    restDir[i + 2] = pos[i + 2] / L;
  }
  const faces = new Int32Array(ico.faces);
  const nf = faces.length / 3;

  // edge -> the (up to two) opposite vertices, from the faces sharing it
  const edgeMap = new Map<number, { a: number; b: number; opp: number[] }>();
  const key = (a: number, b: number) => (a < b ? a * 1_000_000 + b : b * 1_000_000 + a);
  for (let f = 0; f < nf; f += 1) {
    const i = faces[f * 3], j = faces[f * 3 + 1], k = faces[f * 3 + 2];
    const addEdge = (a: number, b: number, opp: number) => {
      const kk = key(a, b);
      const e = edgeMap.get(kk);
      if (e) e.opp.push(opp);
      else edgeMap.set(kk, { a: Math.min(a, b), b: Math.max(a, b), opp: [opp] });
    };
    addEdge(i, j, k);
    addEdge(j, k, i);
    addEdge(k, i, j);
  }
  const ne = edgeMap.size;
  const edgeA = new Int32Array(ne), edgeB = new Int32Array(ne);
  const edgeOpp1 = new Int32Array(ne), edgeOpp2 = new Int32Array(ne);
  const restLen = new Float32Array(ne);
  let ei = 0;
  for (const e of edgeMap.values()) {
    edgeA[ei] = e.a; edgeB[ei] = e.b;
    edgeOpp1[ei] = e.opp[0];
    edgeOpp2[ei] = e.opp.length > 1 ? e.opp[1] : e.opp[0];
    const dx = pos[e.a * 3] - pos[e.b * 3];
    const dy = pos[e.a * 3 + 1] - pos[e.b * 3 + 1];
    const dz = pos[e.a * 3 + 2] - pos[e.b * 3 + 2];
    restLen[ei] = Math.hypot(dx, dy, dz);
    ei += 1;
  }

  // vertex -> incident faces (CSR)
  const counts = new Int32Array(n);
  for (let f = 0; f < nf; f += 1) {
    counts[faces[f * 3]] += 1; counts[faces[f * 3 + 1]] += 1; counts[faces[f * 3 + 2]] += 1;
  }
  const vertFaceStart = new Int32Array(n + 1);
  for (let v = 0; v < n; v += 1) vertFaceStart[v + 1] = vertFaceStart[v] + counts[v];
  const vertFaceList = new Int32Array(vertFaceStart[n]);
  const cursor = Int32Array.from(vertFaceStart);
  for (let f = 0; f < nf; f += 1) {
    for (let t = 0; t < 3; t += 1) {
      const v = faces[f * 3 + t];
      vertFaceList[cursor[v]++] = f;
    }
  }

  const sim: MembraneSim = {
    n, radius,
    pos,
    restDir,
    vel: new Float32Array(n * 3),
    force: new Float32Array(n * 3),
    faces,
    edgeA, edgeB, edgeOpp1, edgeOpp2, restLen,
    degree: new Float32Array(n),
    restLap: new Float32Array(n * 3),
    normals: new Float32Array(n * 3),
    vertFaceStart, vertFaceList,
    a0: 0,
    v0: 0,
    events: [],
    // Dimensionless solver gains. Geometry is bounded by measured area/radius
    // constraints below; these gains only control numerical relaxation.
    kStretch: 8.0,
    kBend: 6.0,
    kVolume: 8.0,
    kEvent: 5.0,
    gamma: 1.0,
  };
  for (let e = 0; e < ne; e += 1) { sim.degree[edgeA[e]] += 1; sim.degree[edgeB[e]] += 1; }
  sim.a0 = membraneSurfaceArea(sim);
  sim.v0 = enclosedVolume(sim);
  computeLaplacian(sim, sim.restLap); // rest-shape reference (spontaneous curvature)
  computeNormals(sim);
  return sim;
}

// ---- Geometry helpers -------------------------------------------------------

function enclosedVolume(sim: MembraneSim): number {
  const { pos, faces } = sim;
  let v = 0;
  for (let f = 0; f < faces.length; f += 3) {
    const a = faces[f] * 3, b = faces[f + 1] * 3, c = faces[f + 2] * 3;
    const ax = pos[a], ay = pos[a + 1], az = pos[a + 2];
    const bx = pos[b], by = pos[b + 1], bz = pos[b + 2];
    const cx = pos[c], cy = pos[c + 1], cz = pos[c + 2];
    // signed volume of tetrahedron (origin, a, b, c) = a · (b x c) / 6
    const crx = by * cz - bz * cy;
    const cry = bz * cx - bx * cz;
    const crz = bx * cy - by * cx;
    v += (ax * crx + ay * cry + az * crz);
  }
  return v / 6;
}

export function membraneSurfaceArea(sim: MembraneSim): number {
  const { pos, faces } = sim;
  let area = 0;
  for (let f = 0; f < faces.length; f += 3) {
    const a = faces[f] * 3, b = faces[f + 1] * 3, c = faces[f + 2] * 3;
    const ux = pos[b] - pos[a], uy = pos[b + 1] - pos[a + 1], uz = pos[b + 2] - pos[a + 2];
    const vx = pos[c] - pos[a], vy = pos[c + 1] - pos[a + 1], vz = pos[c + 2] - pos[a + 2];
    const nx = uy * vz - uz * vy;
    const ny = uz * vx - ux * vz;
    const nz = ux * vy - uy * vx;
    area += 0.5 * Math.hypot(nx, ny, nz);
  }
  return area;
}

export function membraneGeometryMetrics(sim: MembraneSim): {
  area: number;
  areaRatio: number;
  volume: number;
  volumeRatio: number;
  minRadius: number;
  maxRadius: number;
  invertedFaces: number;
} {
  let minRadius = Infinity;
  let maxRadius = 0;
  for (let v = 0; v < sim.n; v += 1) {
    const r = Math.hypot(sim.pos[v * 3], sim.pos[v * 3 + 1], sim.pos[v * 3 + 2]);
    minRadius = Math.min(minRadius, r);
    maxRadius = Math.max(maxRadius, r);
  }
  let invertedFaces = 0;
  const { pos, faces } = sim;
  for (let f = 0; f < faces.length; f += 3) {
    const a = faces[f] * 3, b = faces[f + 1] * 3, c = faces[f + 2] * 3;
    const ux = pos[b] - pos[a], uy = pos[b + 1] - pos[a + 1], uz = pos[b + 2] - pos[a + 2];
    const vx = pos[c] - pos[a], vy = pos[c + 1] - pos[a + 1], vz = pos[c + 2] - pos[a + 2];
    const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
    const cx = (pos[a] + pos[b] + pos[c]) / 3;
    const cy = (pos[a + 1] + pos[b + 1] + pos[c + 1]) / 3;
    const cz = (pos[a + 2] + pos[b + 2] + pos[c + 2]) / 3;
    if (nx * cx + ny * cy + nz * cz <= 0) invertedFaces += 1;
  }
  const area = membraneSurfaceArea(sim);
  const volume = enclosedVolume(sim);
  return {
    area,
    areaRatio: area / sim.a0,
    volume,
    volumeRatio: volume / sim.v0,
    minRadius,
    maxRadius,
    invertedFaces
  };
}

// Umbrella (uniform-weight) Laplacian: L_i = (1/deg_i) Σ_{j~i} (x_j − x_i). This
// approximates the mean-curvature vector on a near-uniform mesh (the icosphere is
// very uniform) while being purely diffusive — non-negative weights, so explicit
// integration stays stable (no obtuse-triangle anti-diffusion / wrinkle blow-up
// that the cotangent weights can cause under large deformation). Penalising its
// deviation from the rest shape gives a stable Helfrich-like bending force.
function computeLaplacian(sim: MembraneSim, out: Float32Array): void {
  const { pos, edgeA, edgeB, degree } = sim;
  out.fill(0);
  for (let e = 0; e < edgeA.length; e += 1) {
    const a = edgeA[e], b = edgeB[e];
    const dx = pos[b * 3] - pos[a * 3];
    const dy = pos[b * 3 + 1] - pos[a * 3 + 1];
    const dz = pos[b * 3 + 2] - pos[a * 3 + 2];
    out[a * 3] += dx; out[a * 3 + 1] += dy; out[a * 3 + 2] += dz;
    out[b * 3] -= dx; out[b * 3 + 1] -= dy; out[b * 3 + 2] -= dz;
  }
  const n = sim.n;
  for (let v = 0; v < n; v += 1) {
    const d = degree[v] || 1;
    out[v * 3] /= d; out[v * 3 + 1] /= d; out[v * 3 + 2] /= d;
  }
}

export function computeNormals(sim: MembraneSim): void {
  const { pos, faces, normals, n } = sim;
  normals.fill(0);
  for (let f = 0; f < faces.length; f += 3) {
    const a = faces[f] * 3, b = faces[f + 1] * 3, c = faces[f + 2] * 3;
    const ux = pos[b] - pos[a], uy = pos[b + 1] - pos[a + 1], uz = pos[b + 2] - pos[a + 2];
    const vx = pos[c] - pos[a], vy = pos[c + 1] - pos[a + 1], vz = pos[c + 2] - pos[a + 2];
    const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
    normals[a] += nx; normals[a + 1] += ny; normals[a + 2] += nz;
    normals[b] += nx; normals[b + 1] += ny; normals[b + 2] += nz;
    normals[c] += nx; normals[c + 1] += ny; normals[c + 2] += nz;
  }
  for (let v = 0; v < n; v += 1) {
    const L = Math.hypot(normals[v * 3], normals[v * 3 + 1], normals[v * 3 + 2]) || 1;
    normals[v * 3] /= L; normals[v * 3 + 1] /= L; normals[v * 3 + 2] /= L;
  }
}

// ---- One overdamped step ----------------------------------------------------

const _lap = { arr: new Float32Array(0) };

export function stepMembrane(sim: MembraneSim, dt: number): void {
  const { n, pos, force, edgeA, edgeB, restLen, restLap, normals } = sim;
  force.fill(0);

  // 1) Stretch / area elasticity → membrane tension (stiff, near-inextensible).
  for (let e = 0; e < edgeA.length; e += 1) {
    const a = edgeA[e], b = edgeB[e];
    const dx = pos[b * 3] - pos[a * 3];
    const dy = pos[b * 3 + 1] - pos[a * 3 + 1];
    const dz = pos[b * 3 + 2] - pos[a * 3 + 2];
    const L = Math.hypot(dx, dy, dz) || 1e-9;
    const f = (sim.kStretch * (L - restLen[e])) / L;
    force[a * 3] += f * dx; force[a * 3 + 1] += f * dy; force[a * 3 + 2] += f * dz;
    force[b * 3] -= f * dx; force[b * 3 + 1] -= f * dy; force[b * 3 + 2] -= f * dz;
  }

  // 2) Helfrich bending → penalise deviation of the mean-curvature vector from the
  //    spontaneous-curvature reference (rest sphere, shifted locally by events).
  if (_lap.arr.length !== n * 3) _lap.arr = new Float32Array(n * 3);
  const lap = _lap.arr;
  computeLaplacian(sim, lap);
  for (let i = 0; i < n * 3; i += 1) {
    force[i] -= sim.kBend * (lap[i] - restLap[i]);
  }

  // 2b) Endo/exocytosis: a coat-driven bud on a patch. Modelled as a bounded spring
  //     that pulls the patch toward a target radial offset (inward pit for endo,
  //     outward bulge for exo) — SELF-LIMITING, so it forms a dimple of set depth
  //     and heals, never collapsing to the centre.
  for (const ev of sim.events) {
    const [dx, dy, dz] = ev.dir;
    const env = Math.sin(Math.PI * Math.min(1, ev.t)); // ramp up then heal
    const sign = ev.kind === "endocytosis" ? -1 : 1; // inward vs outward
    const targetOffset = sign * ev.strength * sim.radius * env; // world units
    for (let v = 0; v < n; v += 1) {
      const x = pos[v * 3], y = pos[v * 3 + 1], z = pos[v * 3 + 2];
      const r = Math.hypot(x, y, z) || 1e-9;
      const c = (x * dx + y * dy + z * dz) / r; // cosine to patch centre
      if (c <= ev.radius) continue;
      const w = (c - ev.radius) / (1 - ev.radius); // 0..1 across the patch
      const want = sim.radius + targetOffset * w * w; // desired radius here
      const f = sim.kEvent * (want - r); // spring toward the target radius
      const nx = x / r, ny = y / r, nz = z / r;
      force[v * 3] += f * nx; force[v * 3 + 1] += f * ny; force[v * 3 + 2] += f * nz;
    }
  }
  computeNormals(sim);

  // 3) Volume conservation → incompressible cytoplasm (nearly rigid pressure).
  const v = enclosedVolume(sim);
  const pressure = (-sim.kVolume * (v - sim.v0)) / sim.v0;
  // ∂V/∂x_i = (1/6) Σ_{faces around i} (x_j × x_k) — an outward area-weighted normal
  const { faces } = sim;
  for (let f = 0; f < faces.length; f += 3) {
    const ia = faces[f], ib = faces[f + 1], ic = faces[f + 2];
    const a = ia * 3, b = ib * 3, cc = ic * 3;
    // gradient contribution for vertex a is (x_b × x_c)/6, etc. (cyclic)
    const addGrad = (vi: number, p: number, q: number) => {
      const gx = (pos[p + 1] * pos[q + 2] - pos[p + 2] * pos[q + 1]) / 6;
      const gy = (pos[p + 2] * pos[q] - pos[p] * pos[q + 2]) / 6;
      const gz = (pos[p] * pos[q + 1] - pos[p + 1] * pos[q]) / 6;
      force[vi] += pressure * gx; force[vi + 1] += pressure * gy; force[vi + 2] += pressure * gz;
    };
    addGrad(a, b, cc);
    addGrad(b, cc, a);
    addGrad(cc, a, b);
  }

  // 4) Overdamped integration (low-Reynolds): x ← x + (dt/γ)·F, with a per-step
  //    displacement cap for safety against any transient force spike.
  const scale = dt / sim.gamma;
  const cap = sim.radius * 0.01;
  for (let i = 0; i < n; i += 1) {
    let dx = force[i * 3] * scale, dy = force[i * 3 + 1] * scale, dz = force[i * 3 + 2] * scale;
    const d = Math.hypot(dx, dy, dz);
    if (d > cap) { const s = cap / d; dx *= s; dy *= s; dz *= s; }
    pos[i * 3] += dx; pos[i * 3 + 1] += dy; pos[i * 3 + 2] += dz;
  }
  enforceWholeCellMembraneGeometry(sim);
  computeNormals(sim);
}

function enforceWholeCellMembraneGeometry(sim: MembraneSim): void {
  projectToRadialShell(sim);
  capElasticSurfaceArea(sim);
}

function projectToRadialShell(sim: MembraneSim): void {
  const { n, pos, restDir, radius } = sim;
  const minR = radius * MEMBRANE_RADIAL_MIN;
  const maxR = radius * MEMBRANE_RADIAL_MAX;
  for (let v = 0; v < n; v += 1) {
    const i = v * 3;
    const dx = restDir[i], dy = restDir[i + 1], dz = restDir[i + 2];
    let r = pos[i] * dx + pos[i + 1] * dy + pos[i + 2] * dz;
    if (!Number.isFinite(r)) r = radius;
    r = Math.min(maxR, Math.max(minR, r));
    pos[i] = dx * r;
    pos[i + 1] = dy * r;
    pos[i + 2] = dz * r;
  }
}

function capElasticSurfaceArea(sim: MembraneSim): void {
  const maxArea = sim.a0 * (1 + MEMBRANE_ELASTIC_AREA_STRAIN_LIMIT);
  if (membraneSurfaceArea(sim) <= maxArea) return;

  const deviations = sim.force; // scratch: first n entries store radial deviation
  const { n, pos, restDir, radius } = sim;
  for (let v = 0; v < n; v += 1) {
    const i = v * 3;
    deviations[v] = Math.hypot(pos[i], pos[i + 1], pos[i + 2]) - radius;
  }

  let lo = 0;
  let hi = 1;
  let best = 0;
  for (let iter = 0; iter < AREA_CORRECTION_ITERS; iter += 1) {
    const s = (lo + hi) / 2;
    writeRadialDeviationScale(sim, deviations, s);
    if (membraneSurfaceArea(sim) <= maxArea) {
      best = s;
      lo = s;
    } else {
      hi = s;
    }
  }
  writeRadialDeviationScale(sim, deviations, best);
}

function writeRadialDeviationScale(sim: MembraneSim, deviations: Float32Array, scale: number): void {
  const { n, pos, restDir, radius } = sim;
  for (let v = 0; v < n; v += 1) {
    const i = v * 3;
    const r = radius + deviations[v] * scale;
    pos[i] = restDir[i] * r;
    pos[i + 1] = restDir[i + 1] * r;
    pos[i + 2] = restDir[i + 2] * r;
  }
}

// ---- Events ------------------------------------------------------------------

export function spawnMembraneEvent(sim: MembraneSim, kind: MembraneEventKind, rand: () => number): void {
  // random unit direction
  let x = rand() * 2 - 1, y = rand() * 2 - 1, z = rand() * 2 - 1;
  const L = Math.hypot(x, y, z) || 1;
  x /= L; y /= L; z /= L;
  sim.events.push({
    kind,
    dir: [x, y, z],
    t: 0,
    duration: 2.2 + rand() * 1.8, // visual solver lifetime, not a biological rate
    radius: Math.cos(MEMBRANE_WHOLE_CELL_RADIAL_DEVIATION_LIMIT),
    strength: MEMBRANE_WHOLE_CELL_RADIAL_DEVIATION_LIMIT * (0.55 + rand() * 0.35),
    budded: false,
  });
}

export function advanceMembraneEvents(sim: MembraneSim, dt: number): void {
  for (const ev of sim.events) ev.t += dt / ev.duration;
  sim.events = sim.events.filter((ev) => ev.t < 1);
}
