import type { MembraneSim } from "./membrane_mechanics";

export type IntracellularBoundaryContactResult = {
  contacted: boolean;
  correctedCenter: [number, number, number];
  faceIndex: number;
  penetrationWorld: number;
  dimensionlessPenaltyLoad: number;
};

export type IntracellularBoundaryLoadDiagnostics = {
  frameOrganelleContactCount: number;
  cumulativeOrganelleContactCount: number;
  maximumOrganellePenetrationWorld: number;
  dimensionlessOrganellePenaltyLoad: number;
  frameCytosolPressureUpdateCount: number;
  cumulativeCytosolPressureUpdateCount: number;
  cytosolPressureFaceCount: number;
  dimensionlessCytosolPressureRms: number;
  maximumDimensionlessCytosolPressureRms: number;
  dimensionlessMembraneLoadResultant: [number, number, number];
  dimensionlessInteriorReactionResultant: [number, number, number];
  dimensionlessActionReactionResidual: number;
  physicalForceN: null;
  physicalPressurePa: null;
  healthyPhhSustainableForceN: null;
  healthyPhhSustainablePressurePa: null;
  quantitativeHealthyPhhMechanicsEnabled: false;
};

export const INTRACELLULAR_BOUNDARY_MECHANICS_CONTRACT = Object.freeze({
  version: "intracellular_boundary_mechanics_v1",
  role: "dimensionless_runtime_geometry_and_reaction_diagnostics",
  organelleContactModel:
    "sphere_against_current_triangle_mesh_with_overdamped_nonpenetration_projection",
  organelleLoadModel:
    "penetration_penalty_using_existing_dimensionless_mesh_regularization_gain",
  cytosolLoadModel:
    "mean_removed_dimensionless_cut_cell_pressure_traction",
  loadDistribution:
    "closest_triangle_barycentric_weights_for_organelle_contact_and_equal_triangle_weights_for_pressure",
  actionReactionBalanced: true,
  biologicalForceAssigned: false,
  biologicalPressureAssigned: false,
  healthyPhhSustainableForceAssigned: false,
  healthyPhhSustainablePressureAssigned: false,
  quantitativeHealthyPhhMechanicsEnabled: false,
  blockers: [
    "matched healthy-adult PHH force-deformation trajectories are absent",
    "matched healthy-adult PHH membrane tension and cortex rheology are absent",
    "donor- and study-disjoint mechanics validation is absent"
  ] as const
});

type ClosestPoint = {
  faceIndex: number;
  point: [number, number, number];
  barycentric: [number, number, number];
  distance: number;
};

const EPSILON = 1e-12;

function faceVertex(sim: MembraneSim, faceIndex: number, localIndex: number): number {
  return sim.faces[faceIndex * 3 + localIndex];
}

function closestPointOnTriangle(
  px: number,
  py: number,
  pz: number,
  ax: number,
  ay: number,
  az: number,
  bx: number,
  by: number,
  bz: number,
  cx: number,
  cy: number,
  cz: number
): { point: [number, number, number]; barycentric: [number, number, number] } {
  const abx = bx - ax;
  const aby = by - ay;
  const abz = bz - az;
  const acx = cx - ax;
  const acy = cy - ay;
  const acz = cz - az;
  const apx = px - ax;
  const apy = py - ay;
  const apz = pz - az;
  const d1 = abx * apx + aby * apy + abz * apz;
  const d2 = acx * apx + acy * apy + acz * apz;
  if (d1 <= 0 && d2 <= 0) {
    return { point: [ax, ay, az], barycentric: [1, 0, 0] };
  }

  const bpx = px - bx;
  const bpy = py - by;
  const bpz = pz - bz;
  const d3 = abx * bpx + aby * bpy + abz * bpz;
  const d4 = acx * bpx + acy * bpy + acz * bpz;
  if (d3 >= 0 && d4 <= d3) {
    return { point: [bx, by, bz], barycentric: [0, 1, 0] };
  }

  const vc = d1 * d4 - d3 * d2;
  if (vc <= 0 && d1 >= 0 && d3 <= 0) {
    const v = d1 / (d1 - d3);
    return {
      point: [ax + v * abx, ay + v * aby, az + v * abz],
      barycentric: [1 - v, v, 0]
    };
  }

  const cpx = px - cx;
  const cpy = py - cy;
  const cpz = pz - cz;
  const d5 = abx * cpx + aby * cpy + abz * cpz;
  const d6 = acx * cpx + acy * cpy + acz * cpz;
  if (d6 >= 0 && d5 <= d6) {
    return { point: [cx, cy, cz], barycentric: [0, 0, 1] };
  }

  const vb = d5 * d2 - d1 * d6;
  if (vb <= 0 && d2 >= 0 && d6 <= 0) {
    const w = d2 / (d2 - d6);
    return {
      point: [ax + w * acx, ay + w * acy, az + w * acz],
      barycentric: [1 - w, 0, w]
    };
  }

  const va = d3 * d6 - d5 * d4;
  if (va <= 0 && d4 - d3 >= 0 && d5 - d6 >= 0) {
    const denominator = d4 - d3 + d5 - d6;
    const w = denominator > EPSILON ? (d4 - d3) / denominator : 0;
    return {
      point: [
        bx + w * (cx - bx),
        by + w * (cy - by),
        bz + w * (cz - bz)
      ],
      barycentric: [0, 1 - w, w]
    };
  }

  const denominator = va + vb + vc;
  const inverse = Math.abs(denominator) > EPSILON ? 1 / denominator : 0;
  const v = vb * inverse;
  const w = vc * inverse;
  const u = 1 - v - w;
  return {
    point: [
      u * ax + v * bx + w * cx,
      u * ay + v * by + w * cy,
      u * az + v * bz + w * cz
    ],
    barycentric: [u, v, w]
  };
}

function evaluateFace(
  sim: MembraneSim,
  faceIndex: number,
  x: number,
  y: number,
  z: number
): ClosestPoint {
  const ia = faceVertex(sim, faceIndex, 0) * 3;
  const ib = faceVertex(sim, faceIndex, 1) * 3;
  const ic = faceVertex(sim, faceIndex, 2) * 3;
  const closest = closestPointOnTriangle(
    x,
    y,
    z,
    sim.pos[ia],
    sim.pos[ia + 1],
    sim.pos[ia + 2],
    sim.pos[ib],
    sim.pos[ib + 1],
    sim.pos[ib + 2],
    sim.pos[ic],
    sim.pos[ic + 1],
    sim.pos[ic + 2]
  );
  return {
    faceIndex,
    point: closest.point,
    barycentric: closest.barycentric,
    distance: Math.hypot(
      x - closest.point[0],
      y - closest.point[1],
      z - closest.point[2]
    )
  };
}

function nearestRestFace(
  sim: MembraneSim,
  x: number,
  y: number,
  z: number
): number {
  const inverseLength = 1 / (Math.hypot(x, y, z) || 1);
  const nx = x * inverseLength;
  const ny = y * inverseLength;
  const nz = z * inverseLength;
  let bestFace = 0;
  let bestDot = -Infinity;
  for (let face = 0; face < sim.faces.length / 3; face += 1) {
    const ia = faceVertex(sim, face, 0) * 3;
    const ib = faceVertex(sim, face, 1) * 3;
    const ic = faceVertex(sim, face, 2) * 3;
    const cx = sim.restPos[ia] + sim.restPos[ib] + sim.restPos[ic];
    const cy = sim.restPos[ia + 1] + sim.restPos[ib + 1] + sim.restPos[ic + 1];
    const cz = sim.restPos[ia + 2] + sim.restPos[ib + 2] + sim.restPos[ic + 2];
    const inverseCenter = 1 / (Math.hypot(cx, cy, cz) || 1);
    const dot = nx * cx * inverseCenter + ny * cy * inverseCenter + nz * cz * inverseCenter;
    if (dot > bestDot) {
      bestDot = dot;
      bestFace = face;
    }
  }
  return bestFace;
}

function closestLocalSurfacePoint(
  sim: MembraneSim,
  x: number,
  y: number,
  z: number,
  faceHint: number
): ClosestPoint {
  const faceCount = sim.faces.length / 3;
  const seedFace =
    Number.isInteger(faceHint) && faceHint >= 0 && faceHint < faceCount
      ? faceHint
      : nearestRestFace(sim, x, y, z);
  const candidateFaces = new Set<number>([seedFace]);
  for (let local = 0; local < 3; local += 1) {
    const vertex = faceVertex(sim, seedFace, local);
    for (
      let offset = sim.vertFaceStart[vertex];
      offset < sim.vertFaceStart[vertex + 1];
      offset += 1
    ) {
      candidateFaces.add(sim.vertFaceList[offset]);
    }
  }
  let best = evaluateFace(sim, seedFace, x, y, z);
  for (const candidate of candidateFaces) {
    const value = evaluateFace(sim, candidate, x, y, z);
    if (value.distance < best.distance) best = value;
  }
  return best;
}

function emptyDiagnostics(
  cumulativeOrganelleContactCount: number,
  cumulativeCytosolPressureUpdateCount: number,
  maximumDimensionlessCytosolPressureRms: number
): IntracellularBoundaryLoadDiagnostics {
  return {
    frameOrganelleContactCount: 0,
    cumulativeOrganelleContactCount,
    maximumOrganellePenetrationWorld: 0,
    dimensionlessOrganellePenaltyLoad: 0,
    frameCytosolPressureUpdateCount: 0,
    cumulativeCytosolPressureUpdateCount,
    cytosolPressureFaceCount: 0,
    dimensionlessCytosolPressureRms: 0,
    maximumDimensionlessCytosolPressureRms,
    dimensionlessMembraneLoadResultant: [0, 0, 0],
    dimensionlessInteriorReactionResultant: [0, 0, 0],
    dimensionlessActionReactionResidual: 0,
    physicalForceN: null,
    physicalPressurePa: null,
    healthyPhhSustainableForceN: null,
    healthyPhhSustainablePressurePa: null,
    quantitativeHealthyPhhMechanicsEnabled: false
  };
}

export class IntracellularBoundaryMechanics {
  readonly vertexLoads: Float32Array;

  private pendingDiagnostics: IntracellularBoundaryLoadDiagnostics;
  private lastDiagnostics: IntracellularBoundaryLoadDiagnostics;
  private cumulativeOrganelleContactCount = 0;
  private cumulativeCytosolPressureUpdateCount = 0;
  private maximumDimensionlessCytosolPressureRms = 0;

  constructor(private readonly sim: MembraneSim) {
    this.vertexLoads = new Float32Array(sim.pos.length);
    this.pendingDiagnostics = emptyDiagnostics(0, 0, 0);
    this.lastDiagnostics = emptyDiagnostics(0, 0, 0);
  }

  resolveSphere(
    center: readonly [number, number, number],
    radiusWorld: number,
    faceHint = -1
  ): IntracellularBoundaryContactResult {
    if (center.length !== 3 || center.some((value) => !Number.isFinite(value))) {
      throw new RangeError("intracellular body center must contain three finite values");
    }
    if (!Number.isFinite(radiusWorld) || radiusWorld <= 0) {
      throw new RangeError("intracellular body radius must be finite and positive");
    }
    const closest = closestLocalSurfacePoint(
      this.sim,
      center[0],
      center[1],
      center[2],
      faceHint
    );
    const faceOffset = closest.faceIndex * 3;
    const ia = this.sim.faces[faceOffset] * 3;
    const ib = this.sim.faces[faceOffset + 1] * 3;
    const ic = this.sim.faces[faceOffset + 2] * 3;
    const abx = this.sim.pos[ib] - this.sim.pos[ia];
    const aby = this.sim.pos[ib + 1] - this.sim.pos[ia + 1];
    const abz = this.sim.pos[ib + 2] - this.sim.pos[ia + 2];
    const acx = this.sim.pos[ic] - this.sim.pos[ia];
    const acy = this.sim.pos[ic + 1] - this.sim.pos[ia + 1];
    const acz = this.sim.pos[ic + 2] - this.sim.pos[ia + 2];
    let outwardX = aby * acz - abz * acy;
    let outwardY = abz * acx - abx * acz;
    let outwardZ = abx * acy - aby * acx;
    let outwardLength = Math.hypot(outwardX, outwardY, outwardZ) || 1;
    outwardX /= outwardLength;
    outwardY /= outwardLength;
    outwardZ /= outwardLength;
    const faceCenterX =
      (this.sim.pos[ia] + this.sim.pos[ib] + this.sim.pos[ic]) / 3;
    const faceCenterY =
      (this.sim.pos[ia + 1] + this.sim.pos[ib + 1] + this.sim.pos[ic + 1]) / 3;
    const faceCenterZ =
      (this.sim.pos[ia + 2] + this.sim.pos[ib + 2] + this.sim.pos[ic + 2]) / 3;
    if (
      outwardX * faceCenterX +
      outwardY * faceCenterY +
      outwardZ * faceCenterZ <
      0
    ) {
      outwardX *= -1;
      outwardY *= -1;
      outwardZ *= -1;
    }
    const centerFromSurfaceX = center[0] - closest.point[0];
    const centerFromSurfaceY = center[1] - closest.point[1];
    const centerFromSurfaceZ = center[2] - closest.point[2];
    const signedSide =
      centerFromSurfaceX * outwardX +
      centerFromSurfaceY * outwardY +
      centerFromSurfaceZ * outwardZ;
    const centerIsOutside = signedSide > 0;
    const penetration = centerIsOutside
      ? radiusWorld + closest.distance
      : radiusWorld - closest.distance;
    if (penetration <= this.sim.radius * 1e-7) {
      return {
        contacted: false,
        correctedCenter: [center[0], center[1], center[2]],
        faceIndex: closest.faceIndex,
        penetrationWorld: 0,
        dimensionlessPenaltyLoad: 0
      };
    }

    let inwardX = centerFromSurfaceX;
    let inwardY = centerFromSurfaceY;
    let inwardZ = centerFromSurfaceZ;
    let inwardLength = Math.hypot(inwardX, inwardY, inwardZ);
    if (inwardLength <= EPSILON) {
      inwardX = -outwardX;
      inwardY = -outwardY;
      inwardZ = -outwardZ;
      inwardLength = 1;
    } else if (centerIsOutside) {
      inwardX *= -1;
      inwardY *= -1;
      inwardZ *= -1;
    }
    inwardX /= inwardLength;
    inwardY /= inwardLength;
    inwardZ /= inwardLength;
    const numericalClearance = this.sim.radius * 1e-7;
    const correction = penetration + numericalClearance;
    const correctedCenter: [number, number, number] = [
      center[0] + inwardX * correction,
      center[1] + inwardY * correction,
      center[2] + inwardZ * correction
    ];

    // This penalty magnitude is in the same dimensionless numerical units as
    // the mesh regularizer. It is deliberately not converted to newtons.
    const penaltyLoad = this.sim.kStretch * penetration;
    const membraneX = -inwardX * penaltyLoad;
    const membraneY = -inwardY * penaltyLoad;
    const membraneZ = -inwardZ * penaltyLoad;
    for (let local = 0; local < 3; local += 1) {
      const vertex = this.sim.faces[faceOffset + local] * 3;
      const weight = closest.barycentric[local];
      this.vertexLoads[vertex] += membraneX * weight;
      this.vertexLoads[vertex + 1] += membraneY * weight;
      this.vertexLoads[vertex + 2] += membraneZ * weight;
    }
    this.recordBalancedLoad(membraneX, membraneY, membraneZ);
    this.cumulativeOrganelleContactCount += 1;
    this.pendingDiagnostics.frameOrganelleContactCount += 1;
    this.pendingDiagnostics.cumulativeOrganelleContactCount =
      this.cumulativeOrganelleContactCount;
    this.pendingDiagnostics.maximumOrganellePenetrationWorld = Math.max(
      this.pendingDiagnostics.maximumOrganellePenetrationWorld,
      penetration
    );
    this.pendingDiagnostics.dimensionlessOrganellePenaltyLoad += penaltyLoad;

    return {
      contacted: true,
      correctedCenter,
      faceIndex: closest.faceIndex,
      penetrationWorld: penetration,
      dimensionlessPenaltyLoad: penaltyLoad
    };
  }

  queueDimensionlessCytosolPressure(
    trianglePressures: ArrayLike<number>
  ): void {
    const faceCount = this.sim.faces.length / 3;
    if (trianglePressures.length !== faceCount) {
      throw new RangeError("one dimensionless cytosol pressure is required per membrane face");
    }
    let areaSum = 0;
    let pressureAreaSum = 0;
    const faceAreas = new Float64Array(faceCount);
    const areaVectors = new Float64Array(faceCount * 3);
    for (let face = 0; face < faceCount; face += 1) {
      const pressure = trianglePressures[face];
      if (!Number.isFinite(pressure)) {
        throw new RangeError("dimensionless cytosol pressures must be finite");
      }
      const offset = face * 3;
      const ia = this.sim.faces[offset] * 3;
      const ib = this.sim.faces[offset + 1] * 3;
      const ic = this.sim.faces[offset + 2] * 3;
      const abx = this.sim.pos[ib] - this.sim.pos[ia];
      const aby = this.sim.pos[ib + 1] - this.sim.pos[ia + 1];
      const abz = this.sim.pos[ib + 2] - this.sim.pos[ia + 2];
      const acx = this.sim.pos[ic] - this.sim.pos[ia];
      const acy = this.sim.pos[ic + 1] - this.sim.pos[ia + 1];
      const acz = this.sim.pos[ic + 2] - this.sim.pos[ia + 2];
      const ax = 0.5 * (aby * acz - abz * acy);
      const ay = 0.5 * (abz * acx - abx * acz);
      const az = 0.5 * (abx * acy - aby * acx);
      const area = Math.hypot(ax, ay, az);
      faceAreas[face] = area;
      areaVectors[offset] = ax;
      areaVectors[offset + 1] = ay;
      areaVectors[offset + 2] = az;
      areaSum += area;
      pressureAreaSum += pressure * area;
    }
    const meanPressure = areaSum > EPSILON ? pressureAreaSum / areaSum : 0;
    let pressureSqAreaSum = 0;
    for (let face = 0; face < faceCount; face += 1) {
      const offset = face * 3;
      const pressure = trianglePressures[face] - meanPressure;
      pressureSqAreaSum += pressure * pressure * faceAreas[face];
      const loadX = pressure * areaVectors[offset];
      const loadY = pressure * areaVectors[offset + 1];
      const loadZ = pressure * areaVectors[offset + 2];
      for (let local = 0; local < 3; local += 1) {
        const vertex = this.sim.faces[offset + local] * 3;
        this.vertexLoads[vertex] += loadX / 3;
        this.vertexLoads[vertex + 1] += loadY / 3;
        this.vertexLoads[vertex + 2] += loadZ / 3;
      }
      this.recordBalancedLoad(loadX, loadY, loadZ);
    }
    const pressureRms =
      areaSum > EPSILON ? Math.sqrt(pressureSqAreaSum / areaSum) : 0;
    this.cumulativeCytosolPressureUpdateCount += 1;
    this.maximumDimensionlessCytosolPressureRms = Math.max(
      this.maximumDimensionlessCytosolPressureRms,
      pressureRms
    );
    this.pendingDiagnostics.frameCytosolPressureUpdateCount += 1;
    this.pendingDiagnostics.cumulativeCytosolPressureUpdateCount =
      this.cumulativeCytosolPressureUpdateCount;
    this.pendingDiagnostics.cytosolPressureFaceCount = faceCount;
    this.pendingDiagnostics.dimensionlessCytosolPressureRms = pressureRms;
    this.pendingDiagnostics.maximumDimensionlessCytosolPressureRms =
      this.maximumDimensionlessCytosolPressureRms;
  }

  drainVertexLoads(target: Float32Array): IntracellularBoundaryLoadDiagnostics {
    if (target.length !== this.vertexLoads.length) {
      throw new RangeError("intracellular boundary load target has the wrong size");
    }
    target.set(this.vertexLoads);
    this.vertexLoads.fill(0);
    const membrane = this.pendingDiagnostics.dimensionlessMembraneLoadResultant;
    const interior = this.pendingDiagnostics.dimensionlessInteriorReactionResultant;
    this.pendingDiagnostics.dimensionlessActionReactionResidual = Math.hypot(
      membrane[0] + interior[0],
      membrane[1] + interior[1],
      membrane[2] + interior[2]
    );
    this.lastDiagnostics = {
      ...this.pendingDiagnostics,
      dimensionlessMembraneLoadResultant: [...membrane],
      dimensionlessInteriorReactionResultant: [...interior]
    };
    this.pendingDiagnostics = emptyDiagnostics(
      this.cumulativeOrganelleContactCount,
      this.cumulativeCytosolPressureUpdateCount,
      this.maximumDimensionlessCytosolPressureRms
    );
    return this.diagnostics();
  }

  diagnostics(): IntracellularBoundaryLoadDiagnostics {
    return {
      ...this.lastDiagnostics,
      dimensionlessMembraneLoadResultant: [
        ...this.lastDiagnostics.dimensionlessMembraneLoadResultant
      ],
      dimensionlessInteriorReactionResultant: [
        ...this.lastDiagnostics.dimensionlessInteriorReactionResultant
      ]
    };
  }

  private recordBalancedLoad(x: number, y: number, z: number): void {
    const membrane = this.pendingDiagnostics.dimensionlessMembraneLoadResultant;
    membrane[0] += x;
    membrane[1] += y;
    membrane[2] += z;
    const interior = this.pendingDiagnostics.dimensionlessInteriorReactionResultant;
    interior[0] -= x;
    interior[1] -= y;
    interior[2] -= z;
  }
}
