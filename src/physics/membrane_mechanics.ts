// Coarse whole-cell plasma-membrane geometry.
//
// This mesh is an Eulerian shape coordinate at micrometre scale, not a lattice
// of lipid molecules and not a calibrated healthy-PHH rheology solver. Molecular
// fluidity lives in the membrane material contract and in the nanometre membrane
// scene. At whole-cell scale this module does only three auditable jobs:
//   1. keep one closed, non-inverted render surface;
//   2. preserve enclosed volume and cap direct resolved-area growth;
//   3. consume engine-authoritative kinematic contact deformation.
//
// The 1% area cap below is an engineering guard derived from cross-system human
// red-cell failure evidence. It is not a PHH stretch, rupture, tension, bending,
// viscosity or time parameter. Local folds, buds, membrane reservoirs and
// topology changes remain disabled until their inputs are identified.

import {
  evaluateSurfaceBinding,
  topologyPreservingAdaptiveRemesh,
  type AdaptiveRemeshResult,
  type FaceField,
  type SurfaceBinding,
  type VertexField
} from "./adaptiveRemeshing";

export type MembraneSim = {
  n: number; // vertex count
  radius: number;
  pos: Float32Array; // 3n current positions
  restPos: Float32Array; // 3n immutable geometric reference; not lipid identities
  // Eulerian surface-coordinate directions. Lipids/proteins are separate surface
  // tracers, so keeping this parameterization stable does not make the material rigid.
  restDir: Float32Array;
  restRadius: Float32Array; // per-vertex radius of the closed rest surface
  restShape: "sphere" | "canonical_hepatocyte_polyhedron";
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
  // Dimensionless mesh-repair gains. These are not biological parameters.
  kStretch: number;
  kBend: number;
  kVolume: number;
  gamma: number;
};

export type MembraneSimRemeshResult = {
  sim: MembraneSim;
  remesh: AdaptiveRemeshResult;
  runtimeCachesRebuilt: true;
  mechanicalReferenceAreaPreserved: true;
  mechanicalReferenceVolumePreserved: true;
  maximumRuntimeBindingPositionError: number;
  relativeRuntimeSurfaceAreaError: number;
  relativeRuntimeEnclosedVolumeError: number;
  automaticTriggerEnabled: false;
  biologicalMechanicsAssigned: false;
};

export type MembraneExternalLoadFrame = {
  vertexLoads: ArrayLike<number>;
  loadUnit: "dimensionless_numerical";
  biologicalForceAssigned: false;
};

export type MembraneStepDiagnostics = {
  externalLoadApplied: boolean;
  dimensionlessExternalLoadResultant: [number, number, number];
  physicalForceN: null;
  areaRatio: number;
  volumeRatio: number;
  engineeringAreaGuardUtilization: number;
  engineeringAreaGuardExceeded: boolean;
  quantitativeHealthyPhhMechanicsEnabled: false;
};

// Evans et al. reported 2-4% human red-cell membrane area expansion at lysis.
// One percent is the engine-wide conservative engineering guard: half the lower
// failure reference. It is not a PHH stretch or rupture measurement.
export const MEMBRANE_ELASTIC_AREA_STRAIN_LIMIT = 0.01;

const AREA_CORRECTION_ITERS = 6;

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

function canonicalHepatocyteRadius(radius: number, x: number, y: number, z: number): number {
  // A regular truncated octahedron has volume 32*s^3 in the coordinate form
  // |x|<=2s and |x|+|y|+|z|<=3s. Choose s so its volume equals the sphere
  // represented by `radius`; no fitted shape coefficient is introduced.
  const scale = Math.cbrt(((4 / 3) * Math.PI * radius ** 3) / 32);
  const ax = Math.abs(x), ay = Math.abs(y), az = Math.abs(z);
  return Math.min(
    ax > 1e-12 ? (2 * scale) / ax : Infinity,
    ay > 1e-12 ? (2 * scale) / ay : Infinity,
    az > 1e-12 ? (2 * scale) / az : Infinity,
    (3 * scale) / Math.max(ax + ay + az, 1e-12)
  );
}

function buildMembraneSimFromMesh(
  radius: number,
  restShape: MembraneSim["restShape"],
  currentPositions: ArrayLike<number>,
  restPositions: ArrayLike<number>,
  rawFaces: ArrayLike<number>,
  velocity?: ArrayLike<number>,
  reference?: {
    area: number;
    volume: number;
    kStretch: number;
    kBend: number;
    kVolume: number;
    gamma: number;
  }
): MembraneSim {
  if (
    currentPositions.length < 12 ||
    currentPositions.length % 3 !== 0 ||
    restPositions.length !== currentPositions.length ||
    rawFaces.length < 12 ||
    rawFaces.length % 3 !== 0 ||
    (velocity !== undefined && velocity.length !== currentPositions.length)
  ) {
    throw new RangeError("membrane mesh arrays have incompatible dimensions");
  }
  const n = currentPositions.length / 3;
  const current = Float32Array.from(currentPositions);
  const restPos = Float32Array.from(restPositions);
  if (
    !Array.from(current).every(Number.isFinite) ||
    !Array.from(restPos).every(Number.isFinite)
  ) {
    throw new RangeError("membrane mesh positions must be finite");
  }
  const faces = Int32Array.from(rawFaces);
  for (const vertex of faces) {
    if (!Number.isInteger(vertex) || vertex < 0 || vertex >= n) {
      throw new RangeError("membrane face references an invalid vertex");
    }
  }

  const restDir = new Float32Array(restPos.length);
  const restRadius = new Float32Array(n);
  for (let vertex = 0; vertex < n; vertex += 1) {
    const offset = vertex * 3;
    const localRadius = Math.hypot(
      restPos[offset],
      restPos[offset + 1],
      restPos[offset + 2]
    );
    if (!Number.isFinite(localRadius) || localRadius <= 0) {
      throw new RangeError("membrane rest vertices must have positive radius");
    }
    restRadius[vertex] = localRadius;
    restDir[offset] = restPos[offset] / localRadius;
    restDir[offset + 1] = restPos[offset + 1] / localRadius;
    restDir[offset + 2] = restPos[offset + 2] / localRadius;
  }

  const faceCount = faces.length / 3;
  const edgeMap = new Map<string, { a: number; b: number; opp: number[] }>();
  const addEdge = (a: number, b: number, opposite: number): void => {
    const first = Math.min(a, b);
    const second = Math.max(a, b);
    const edgeKey = `${first}:${second}`;
    const existing = edgeMap.get(edgeKey);
    if (existing) existing.opp.push(opposite);
    else edgeMap.set(edgeKey, { a: first, b: second, opp: [opposite] });
  };
  for (let face = 0; face < faceCount; face += 1) {
    const i = faces[face * 3];
    const j = faces[face * 3 + 1];
    const k = faces[face * 3 + 2];
    if (i === j || j === k || k === i) {
      throw new RangeError("membrane mesh contains a degenerate face");
    }
    addEdge(i, j, k);
    addEdge(j, k, i);
    addEdge(k, i, j);
  }

  const edgeCount = edgeMap.size;
  const edgeA = new Int32Array(edgeCount);
  const edgeB = new Int32Array(edgeCount);
  const edgeOpp1 = new Int32Array(edgeCount);
  const edgeOpp2 = new Int32Array(edgeCount);
  const restLen = new Float32Array(edgeCount);
  let edgeIndex = 0;
  for (const edge of edgeMap.values()) {
    if (edge.opp.length !== 2) {
      throw new RangeError("membrane mesh must be a closed two-manifold");
    }
    edgeA[edgeIndex] = edge.a;
    edgeB[edgeIndex] = edge.b;
    edgeOpp1[edgeIndex] = edge.opp[0];
    edgeOpp2[edgeIndex] = edge.opp[1];
    const a = edge.a * 3;
    const b = edge.b * 3;
    restLen[edgeIndex] = Math.hypot(
      restPos[a] - restPos[b],
      restPos[a + 1] - restPos[b + 1],
      restPos[a + 2] - restPos[b + 2]
    );
    edgeIndex += 1;
  }

  const counts = new Int32Array(n);
  for (const vertex of faces) counts[vertex] += 1;
  const vertFaceStart = new Int32Array(n + 1);
  for (let vertex = 0; vertex < n; vertex += 1) {
    vertFaceStart[vertex + 1] = vertFaceStart[vertex] + counts[vertex];
  }
  const vertFaceList = new Int32Array(vertFaceStart[n]);
  const cursor = Int32Array.from(vertFaceStart);
  for (let face = 0; face < faceCount; face += 1) {
    for (let local = 0; local < 3; local += 1) {
      const vertex = faces[face * 3 + local];
      vertFaceList[cursor[vertex]++] = face;
    }
  }

  const sim: MembraneSim = {
    n,
    radius,
    pos: new Float32Array(restPos),
    restPos,
    restDir,
    restRadius,
    restShape,
    vel: velocity === undefined
      ? new Float32Array(n * 3)
      : Float32Array.from(velocity),
    force: new Float32Array(n * 3),
    faces,
    edgeA,
    edgeB,
    edgeOpp1,
    edgeOpp2,
    restLen,
    degree: new Float32Array(n),
    restLap: new Float32Array(n * 3),
    normals: new Float32Array(n * 3),
    vertFaceStart,
    vertFaceList,
    a0: 0,
    v0: 0,
    kStretch: reference?.kStretch ?? 8.0,
    kBend: reference?.kBend ?? 6.0,
    kVolume: reference?.kVolume ?? 8.0,
    gamma: reference?.gamma ?? 1.0
  };
  for (let edge = 0; edge < edgeCount; edge += 1) {
    sim.degree[edgeA[edge]] += 1;
    sim.degree[edgeB[edge]] += 1;
  }
  sim.a0 = reference?.area ?? membraneSurfaceArea(sim);
  sim.v0 = reference?.volume ?? enclosedVolume(sim);
  if (
    !Number.isFinite(sim.a0) ||
    !Number.isFinite(sim.v0) ||
    sim.a0 <= 0 ||
    sim.v0 <= 0
  ) {
    throw new RangeError("membrane rest geometry has invalid area or volume");
  }
  computeLaplacian(sim, sim.restLap);
  sim.pos.set(current);
  computeNormals(sim);
  return sim;
}

function createMembraneSimWithRestShape(
  radius: number,
  subdiv: number,
  restShape: MembraneSim["restShape"]
): MembraneSim {
  const ico = buildIcosphere(radius, subdiv);
  const restPositions = Float32Array.from(ico.pos);
  for (let i = 0; i < restPositions.length; i += 3) {
    const length = Math.hypot(
      restPositions[i],
      restPositions[i + 1],
      restPositions[i + 2]
    ) || 1;
    const x = restPositions[i] / length;
    const y = restPositions[i + 1] / length;
    const z = restPositions[i + 2] / length;
    const localRadius = restShape === "canonical_hepatocyte_polyhedron"
      ? canonicalHepatocyteRadius(radius, x, y, z)
      : radius;
    restPositions[i] = x * localRadius;
    restPositions[i + 1] = y * localRadius;
    restPositions[i + 2] = z * localRadius;
  }
  return buildMembraneSimFromMesh(
    radius,
    restShape,
    restPositions,
    restPositions,
    ico.faces
  );
}

export function createMembraneSim(radius: number, subdiv = 3): MembraneSim {
  return createMembraneSimWithRestShape(radius, subdiv, "sphere");
}

export function createHepatocyteMembraneSim(radius: number, subdiv = 3): MembraneSim {
  return createMembraneSimWithRestShape(radius, subdiv, "canonical_hepatocyte_polyhedron");
}

/**
 * Refine a live membrane mesh and rebuild every MembraneSim topology cache.
 *
 * Both controls are mandatory because the project has no evidence-backed PHH
 * refinement threshold or runtime split budget. Edge bisection does not change
 * the represented piecewise-linear surface, and does not model budding,
 * endocytosis, fission, lipid insertion or any other biological topology event.
 */
export function remeshMembraneSim(
  sim: MembraneSim,
  options: {
    targetMaximumEdgeLength: number;
    maximumSplitCount: number;
    bindings?: readonly SurfaceBinding[];
    vertexFields?: readonly VertexField[];
    faceFields?: readonly FaceField[];
  }
): MembraneSimRemeshResult {
  const internalRestFieldName = "__membrane_sim_rest_position";
  const internalVelocityFieldName = "__membrane_sim_velocity";
  const externalNames = [
    ...(options.vertexFields ?? []).map((field) => field.name),
    ...(options.faceFields ?? []).map((field) => field.name)
  ];
  if (
    externalNames.includes(internalRestFieldName) ||
    externalNames.includes(internalVelocityFieldName)
  ) {
    throw new RangeError("surface field name is reserved by MembraneSim");
  }

  const beforeBindingPoints = new Map(
    (options.bindings ?? []).map((binding) => [
      binding.id,
      evaluateSurfaceBinding(sim.pos, sim.faces, binding)
    ])
  );
  const beforeArea = membraneSurfaceArea(sim);
  const beforeVolume = enclosedVolume(sim);
  const remesh = topologyPreservingAdaptiveRemesh(
    sim.pos,
    sim.faces,
    {
      targetMaximumEdgeLength: options.targetMaximumEdgeLength,
      maximumSplitCount: options.maximumSplitCount,
      bindings: options.bindings,
      vertexFields: [
        {
          name: internalRestFieldName,
          components: 3,
          values: sim.restPos
        },
        {
          name: internalVelocityFieldName,
          components: 3,
          values: sim.vel
        },
        ...(options.vertexFields ?? [])
      ],
      faceFields: options.faceFields
    }
  );
  const remeshedRestPositions = remesh.vertexFields.find(
    (field) => field.name === internalRestFieldName
  );
  const remeshedVelocity = remesh.vertexFields.find(
    (field) => field.name === internalVelocityFieldName
  );
  if (!remeshedRestPositions || !remeshedVelocity) {
    throw new Error("MembraneSim remeshing lost required vertex state");
  }
  const rebuilt = buildMembraneSimFromMesh(
    sim.radius,
    sim.restShape,
    remesh.vertices,
    remeshedRestPositions.values,
    remesh.triangles,
    remeshedVelocity.values,
    {
      area: sim.a0,
      volume: sim.v0,
      kStretch: sim.kStretch,
      kBend: sim.kBend,
      kVolume: sim.kVolume,
      gamma: sim.gamma
    }
  );

  let maximumRuntimeBindingPositionError = 0;
  for (const binding of remesh.bindings) {
    const before = beforeBindingPoints.get(binding.id);
    if (!before) throw new Error("MembraneSim remeshing lost a surface binding");
    const after = evaluateSurfaceBinding(rebuilt.pos, rebuilt.faces, binding);
    maximumRuntimeBindingPositionError = Math.max(
      maximumRuntimeBindingPositionError,
      Math.hypot(
        before[0] - after[0],
        before[1] - after[1],
        before[2] - after[2]
      )
    );
  }
  const relativeRuntimeSurfaceAreaError = Math.abs(
    membraneSurfaceArea(rebuilt) - beforeArea
  ) / Math.max(Math.abs(beforeArea), Number.EPSILON);
  const relativeRuntimeEnclosedVolumeError = Math.abs(
    enclosedVolume(rebuilt) - beforeVolume
  ) / Math.max(Math.abs(beforeVolume), Number.EPSILON);
  const numericalTolerance = Math.max(sim.radius, 1) * 1e-6;
  if (
    maximumRuntimeBindingPositionError > numericalTolerance ||
    relativeRuntimeSurfaceAreaError > 1e-6 ||
    relativeRuntimeEnclosedVolumeError > 1e-6
  ) {
    throw new Error(
      "MembraneSim Float32 cache rebuild exceeded numerical preservation tolerance"
    );
  }
  return {
    sim: rebuilt,
    remesh,
    runtimeCachesRebuilt: true,
    mechanicalReferenceAreaPreserved: true,
    mechanicalReferenceVolumePreserved: true,
    maximumRuntimeBindingPositionError,
    relativeRuntimeSurfaceAreaError,
    relativeRuntimeEnclosedVolumeError,
    automaticTriggerEnabled: false,
    biologicalMechanicsAssigned: false
  };
}

export function membraneRestRadiusAlongDirection(sim: MembraneSim, x: number, y: number, z: number): number {
  const length = Math.hypot(x, y, z) || 1;
  const nx = x / length, ny = y / length, nz = z / length;
  return sim.restShape === "canonical_hepatocyte_polyhedron"
    ? canonicalHepatocyteRadius(sim.radius, nx, ny, nz)
    : sim.radius;
}

export function writeBarycentricMembranePoint(
  sim: MembraneSim,
  faceIndex: number,
  wa: number,
  wb: number,
  wc: number,
  target: Float32Array,
  targetOffset = 0
): void {
  const face = faceIndex * 3;
  if (faceIndex < 0 || face + 2 >= sim.faces.length) throw new RangeError("membrane face index is out of range");
  const sum = wa + wb + wc;
  if (![wa, wb, wc, sum].every(Number.isFinite) || Math.abs(sum - 1) > 1e-5) {
    throw new RangeError("barycentric membrane weights must be finite and sum to one");
  }
  if (targetOffset < 0 || targetOffset + 2 >= target.length) throw new RangeError("membrane point target is too small");
  writePrevalidatedBarycentricMembranePoint(sim, faceIndex, wa, wb, wc, target, targetOffset);
}

/** Hot-path writer for bindings validated when they are constructed. */
export function writePrevalidatedBarycentricMembranePoint(
  sim: MembraneSim,
  faceIndex: number,
  wa: number,
  wb: number,
  wc: number,
  target: Float32Array,
  targetOffset = 0
): void {
  const face = faceIndex * 3;
  const ia = sim.faces[face] * 3;
  const ib = sim.faces[face + 1] * 3;
  const ic = sim.faces[face + 2] * 3;
  target[targetOffset] = sim.pos[ia] * wa + sim.pos[ib] * wb + sim.pos[ic] * wc;
  target[targetOffset + 1] = sim.pos[ia + 1] * wa + sim.pos[ib + 1] * wb + sim.pos[ic + 1] * wc;
  target[targetOffset + 2] = sim.pos[ia + 2] * wa + sim.pos[ib + 2] * wb + sim.pos[ic + 2] * wc;
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
  minRestRadiusRatio: number;
  maxRestRadiusRatio: number;
  invertedFaces: number;
} {
  let minRadius = Infinity;
  let maxRadius = 0;
  let minRestRadiusRatio = Infinity;
  let maxRestRadiusRatio = 0;
  for (let v = 0; v < sim.n; v += 1) {
    const r = Math.hypot(sim.pos[v * 3], sim.pos[v * 3 + 1], sim.pos[v * 3 + 2]);
    minRadius = Math.min(minRadius, r);
    maxRadius = Math.max(maxRadius, r);
    const ratio = r / sim.restRadius[v];
    minRestRadiusRatio = Math.min(minRestRadiusRatio, ratio);
    maxRestRadiusRatio = Math.max(maxRestRadiusRatio, ratio);
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
    minRestRadiusRatio,
    maxRestRadiusRatio,
    invertedFaces
  };
}

/**
 * Apply an engine-authoritative, volume-preserving affine contact shape.
 *
 * This is a geometric mapping, not a force or relaxation-time law. The axial
 * scale must come from an external contact solver whose evidence boundary is
 * serialized with the engine snapshot. Every bound surface tracer follows the
 * resulting triangles through barycentric coordinates.
 */
export function applyVolumePreservingAffineContactShape(
  sim: MembraneSim,
  normal: readonly [number, number, number],
  axialScale: number
): void {
  if (!Number.isFinite(axialScale) || axialScale <= 0 || axialScale > 1) {
    throw new Error("axialScale must be finite and in (0, 1]");
  }
  const length = Math.hypot(normal[0], normal[1], normal[2]);
  if (!Number.isFinite(length) || length <= 1e-12) throw new Error("contact normal must be non-zero");
  const nx = normal[0] / length;
  const ny = normal[1] / length;
  const nz = normal[2] / length;
  const tangentialScale = 1 / Math.sqrt(axialScale);
  for (let vertex = 0; vertex < sim.n; vertex += 1) {
    const index = vertex * 3;
    const rx = sim.restPos[index];
    const ry = sim.restPos[index + 1];
    const rz = sim.restPos[index + 2];
    const parallel = rx * nx + ry * ny + rz * nz;
    sim.pos[index] = tangentialScale * rx + (axialScale - tangentialScale) * parallel * nx;
    sim.pos[index + 1] = tangentialScale * ry + (axialScale - tangentialScale) * parallel * ny;
    sim.pos[index + 2] = tangentialScale * rz + (axialScale - tangentialScale) * parallel * nz;
  }
  computeNormals(sim);
}

export function restoreMembraneRestShape(sim: MembraneSim): void {
  sim.pos.set(sim.restPos);
  sim.vel.fill(0);
  computeNormals(sim);
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

export function stepMembrane(
  sim: MembraneSim,
  dt: number,
  externalLoad?: MembraneExternalLoadFrame
): MembraneStepDiagnostics {
  if (!Number.isFinite(dt) || dt < 0) {
    throw new RangeError("membrane step must be finite and non-negative");
  }
  if (
    externalLoad !== undefined &&
    (
      externalLoad.loadUnit !== "dimensionless_numerical" ||
      externalLoad.biologicalForceAssigned !== false ||
      externalLoad.vertexLoads.length !== sim.pos.length
    )
  ) {
    throw new RangeError(
      "external membrane load must be a dimensionless, size-matched vertex field"
    );
  }
  const { n, pos, force, edgeA, edgeB, restLen, restLap, normals } = sim;
  force.fill(0);

  // 1) Edge-length regularization keeps the Eulerian triangulation usable. It is
  //    a mesh-quality term, not a lipid spring network or membrane shear modulus.
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

  // 2) Curvature regularization restores a numerically damaged rest mesh. The
  //    gain is not the healthy-PHH Helfrich bending modulus, which remains null.
  if (_lap.arr.length !== n * 3) _lap.arr = new Float32Array(n * 3);
  const lap = _lap.arr;
  computeLaplacian(sim, lap);
  for (let i = 0; i < n * 3; i += 1) {
    force[i] -= sim.kBend * (lap[i] - restLap[i]);
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

  // 4) Optional intracellular loading. This input is explicitly dimensionless:
  //    organelle contact penalties and cut-cell pressure tractions may deform
  //    the renderer, but cannot become healthy-PHH newtons without calibration.
  const loadResultant: [number, number, number] = [0, 0, 0];
  if (externalLoad) {
    for (let vertex = 0; vertex < n; vertex += 1) {
      const offset = vertex * 3;
      const fx = externalLoad.vertexLoads[offset];
      const fy = externalLoad.vertexLoads[offset + 1];
      const fz = externalLoad.vertexLoads[offset + 2];
      if (![fx, fy, fz].every(Number.isFinite)) {
        throw new RangeError("external membrane vertex loads must be finite");
      }
      force[offset] += fx;
      force[offset + 1] += fy;
      force[offset + 2] += fz;
      loadResultant[0] += fx;
      loadResultant[1] += fy;
      loadResultant[2] += fz;
    }
  }

  // 5) Overdamped integration (low-Reynolds): x ← x + (dt/γ)·F, with a per-step
  //    displacement cap for safety against any transient force spike.
  const scale = dt / sim.gamma;
  const cap = sim.radius * 0.015;
  for (let i = 0; i < n; i += 1) {
    let dx = force[i * 3] * scale, dy = force[i * 3 + 1] * scale, dz = force[i * 3 + 2] * scale;
    const d = Math.hypot(dx, dy, dz);
    if (d > cap) { const s = cap / d; dx *= s; dy *= s; dz *= s; }
    pos[i * 3] += dx; pos[i * 3 + 1] += dy; pos[i * 3 + 2] += dz;
  }
  enforceWholeCellMembraneGeometry(sim);
  computeNormals(sim);
  const metrics = membraneGeometryMetrics(sim);
  const areaStrain = Math.max(0, metrics.areaRatio - 1);
  return {
    externalLoadApplied: externalLoad !== undefined,
    dimensionlessExternalLoadResultant: loadResultant,
    physicalForceN: null,
    areaRatio: metrics.areaRatio,
    volumeRatio: metrics.volumeRatio,
    engineeringAreaGuardUtilization:
      areaStrain / MEMBRANE_ELASTIC_AREA_STRAIN_LIMIT,
    engineeringAreaGuardExceeded:
      metrics.areaRatio >
      1 + MEMBRANE_ELASTIC_AREA_STRAIN_LIMIT + 1e-6,
    quantitativeHealthyPhhMechanicsEnabled: false
  };
}

function enforceWholeCellMembraneGeometry(sim: MembraneSim): void {
  projectToRadialShell(sim);
  capElasticSurfaceArea(sim);
  projectEnclosedVolume(sim);
  capElasticSurfaceArea(sim);
}

function projectEnclosedVolume(sim: MembraneSim): void {
  const volume = enclosedVolume(sim);
  if (!Number.isFinite(volume) || volume <= 1e-12) {
    sim.pos.set(sim.restPos);
    return;
  }
  const scale = Math.cbrt(sim.v0 / volume);
  if (!Number.isFinite(scale)) return;
  for (let index = 0; index < sim.pos.length; index += 1) sim.pos[index] *= scale;
}

function projectToRadialShell(sim: MembraneSim): void {
  const { n, pos, restDir, restRadius } = sim;
  for (let v = 0; v < n; v += 1) {
    const i = v * 3;
    const dx = restDir[i], dy = restDir[i + 1], dz = restDir[i + 2];
    const localRest = restRadius[v];
    let r = pos[i] * dx + pos[i + 1] * dy + pos[i + 2] * dz;
    if (!Number.isFinite(r)) r = localRest;
    // Positive-radius projection is only a coarse-renderer non-inversion guard.
    // It is not a biological lower or upper deformation limit.
    r = Math.max(localRest * 1.0e-6, r);
    pos[i] = dx * r;
    pos[i + 1] = dy * r;
    pos[i + 2] = dz * r;
  }
}

function capElasticSurfaceArea(sim: MembraneSim): void {
  const maxArea = sim.a0 * (1 + MEMBRANE_ELASTIC_AREA_STRAIN_LIMIT);
  if (membraneSurfaceArea(sim) <= maxArea) return;

  const deviations = sim.force; // scratch: first n entries store radial deviation
  const { n, pos, restDir, restRadius } = sim;
  for (let v = 0; v < n; v += 1) {
    const i = v * 3;
    deviations[v] = Math.hypot(pos[i], pos[i + 1], pos[i + 2]) - restRadius[v];
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
  const { n, pos, restDir, restRadius } = sim;
  for (let v = 0; v < n; v += 1) {
    const i = v * 3;
    const r = restRadius[v] + deviations[v] * scale;
    pos[i] = restDir[i] * r;
    pos[i + 1] = restDir[i + 1] * r;
    pos[i + 2] = restDir[i + 2] * r;
  }
}
