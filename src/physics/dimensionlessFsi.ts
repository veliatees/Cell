import {
  WatertightTriangleMeshBoundary,
  auditTriangleMesh,
  type MeshPoint3
} from "./watertightMeshBoundary";

export type DimensionlessFsiOptions = {
  normalCompliance: number;
  maximumVertexDisplacement: number;
  volumeToleranceFraction?: number;
  maximumLineSearchSteps?: number;
};

export type DimensionlessFsiResult = {
  accepted: boolean;
  reason: string;
  candidateBoundary: WatertightTriangleMeshBoundary | null;
  vertexDisplacements: Float64Array;
  surfaceMeanPressure: number;
  fluidResultant: MeshPoint3;
  membraneReaction: MeshPoint3;
  fluidTorqueAboutCentroid: MeshPoint3;
  dimensionlessPressureWork: number;
  initialVolume: number;
  candidateVolume: number;
  relativeVolumeChange: number;
  maximumAppliedDisplacement: number;
  lineSearchStep: number;
  selfIntersectionFree: boolean;
  biologicalUnitsAssigned: false;
  runtimeFeedbackApplied: false;
};

export const DIMENSIONLESS_FSI_CONTRACT = Object.freeze({
  version: "dimensionless_pressure_membrane_response_v1",
  role: "numerical_candidate_generation_only",
  tractionDiscretization: "triangle_pressure_times_oriented_area_distributed_to_vertices",
  shapeMode: "surface_mean_pressure_removed_vertex_normal_response",
  volumeConstraint: "isotropic_centroid_correction_plus_closed_mesh_audit",
  stabilityGuard: "backtracking_line_search_with_self_intersection_rejection",
  actionReactionDiagnostic: true,
  pressureWorkDiagnostic: true,
  forceEnergyConsistencyTested: true,
  volumePreservationTested: true,
  selfIntersectionRejectionTested: true,
  runtimeMembranePressureFeedbackEnabled: false,
  biologicalPressureAssigned: false,
  biologicalComplianceAssigned: false,
  healthyPhhMechanicsAssigned: false
});

const EPSILON = 1e-12;

function vertex(
  values: ArrayLike<number>,
  index: number
): [number, number, number] {
  const offset = index * 3;
  return [values[offset], values[offset + 1], values[offset + 2]];
}

function signedVolume(
  vertices: ArrayLike<number>,
  triangles: ArrayLike<number>
): number {
  let volume = 0;
  for (let offset = 0; offset < triangles.length; offset += 3) {
    const a = vertex(vertices, triangles[offset]);
    const b = vertex(vertices, triangles[offset + 1]);
    const c = vertex(vertices, triangles[offset + 2]);
    volume += (
      a[0] * (b[1] * c[2] - b[2] * c[1]) -
      a[1] * (b[0] * c[2] - b[2] * c[0]) +
      a[2] * (b[0] * c[1] - b[1] * c[0])
    ) / 6;
  }
  return volume;
}

function requireOptions(options: DimensionlessFsiOptions): {
  volumeToleranceFraction: number;
  maximumLineSearchSteps: number;
} {
  if (!Number.isFinite(options.normalCompliance) || options.normalCompliance < 0) {
    throw new RangeError("dimensionless normal compliance must be finite and non-negative");
  }
  if (
    !Number.isFinite(options.maximumVertexDisplacement) ||
    options.maximumVertexDisplacement <= 0
  ) {
    throw new RangeError("maximum vertex displacement must be finite and positive");
  }
  const volumeToleranceFraction = options.volumeToleranceFraction ?? 1e-9;
  if (
    !Number.isFinite(volumeToleranceFraction) ||
    volumeToleranceFraction <= 0 ||
    volumeToleranceFraction >= 1
  ) {
    throw new RangeError("volume tolerance fraction must lie in (0, 1)");
  }
  const maximumLineSearchSteps = options.maximumLineSearchSteps ?? 12;
  if (!Number.isInteger(maximumLineSearchSteps) || maximumLineSearchSteps < 1) {
    throw new RangeError("maximum line-search steps must be a positive integer");
  }
  return { volumeToleranceFraction, maximumLineSearchSteps };
}

export function proposeDimensionlessPressureResponse(
  boundary: WatertightTriangleMeshBoundary,
  trianglePressures: ArrayLike<number>,
  options: DimensionlessFsiOptions
): DimensionlessFsiResult {
  if (!(boundary instanceof WatertightTriangleMeshBoundary)) {
    throw new TypeError("pressure response requires a validated closed mesh boundary");
  }
  const triangleCount = boundary.triangles.length / 3;
  if (trianglePressures.length !== triangleCount) {
    throw new RangeError("one finite dimensionless pressure is required per triangle");
  }
  const pressures = Float64Array.from(trianglePressures);
  if (pressures.some((value) => !Number.isFinite(value))) {
    throw new RangeError("triangle pressures must be finite");
  }
  const { volumeToleranceFraction, maximumLineSearchSteps } = requireOptions(options);
  const vertexCount = boundary.vertices.length / 3;
  const orientation = Math.sign(boundary.audit.signedVolume) || 1;
  const vertexArea = new Float64Array(vertexCount);
  const vertexNormal = new Float64Array(vertexCount * 3);
  const vertexPressureNumerator = new Float64Array(vertexCount);
  const pressureForce = new Float64Array(vertexCount * 3);
  const centroid: [number, number, number] = [0, 0, 0];
  for (let index = 0; index < vertexCount; index += 1) {
    centroid[0] += boundary.vertices[index * 3];
    centroid[1] += boundary.vertices[index * 3 + 1];
    centroid[2] += boundary.vertices[index * 3 + 2];
  }
  centroid[0] /= vertexCount;
  centroid[1] /= vertexCount;
  centroid[2] /= vertexCount;

  let pressureArea = 0;
  let surfaceArea = 0;
  const fluidResultant: [number, number, number] = [0, 0, 0];
  const fluidTorque: [number, number, number] = [0, 0, 0];
  for (let triangle = 0; triangle < triangleCount; triangle += 1) {
    const offset = triangle * 3;
    const indices = [
      boundary.triangles[offset],
      boundary.triangles[offset + 1],
      boundary.triangles[offset + 2]
    ];
    const a = vertex(boundary.vertices, indices[0]);
    const b = vertex(boundary.vertices, indices[1]);
    const c = vertex(boundary.vertices, indices[2]);
    const edge1 = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
    const edge2 = [c[0] - a[0], c[1] - a[1], c[2] - a[2]];
    const areaVector: [number, number, number] = [
      orientation * 0.5 * (edge1[1] * edge2[2] - edge1[2] * edge2[1]),
      orientation * 0.5 * (edge1[2] * edge2[0] - edge1[0] * edge2[2]),
      orientation * 0.5 * (edge1[0] * edge2[1] - edge1[1] * edge2[0])
    ];
    const area = Math.hypot(...areaVector);
    const pressure = pressures[triangle];
    surfaceArea += area;
    pressureArea += pressure * area;
    const triangleForce: [number, number, number] = [
      pressure * areaVector[0],
      pressure * areaVector[1],
      pressure * areaVector[2]
    ];
    fluidResultant[0] += triangleForce[0];
    fluidResultant[1] += triangleForce[1];
    fluidResultant[2] += triangleForce[2];
    const center: [number, number, number] = [
      (a[0] + b[0] + c[0]) / 3 - centroid[0],
      (a[1] + b[1] + c[1]) / 3 - centroid[1],
      (a[2] + b[2] + c[2]) / 3 - centroid[2]
    ];
    fluidTorque[0] += center[1] * triangleForce[2] - center[2] * triangleForce[1];
    fluidTorque[1] += center[2] * triangleForce[0] - center[0] * triangleForce[2];
    fluidTorque[2] += center[0] * triangleForce[1] - center[1] * triangleForce[0];
    for (const index of indices) {
      vertexArea[index] += area / 3;
      vertexPressureNumerator[index] += pressure * area / 3;
      pressureForce[index * 3] += triangleForce[0] / 3;
      pressureForce[index * 3 + 1] += triangleForce[1] / 3;
      pressureForce[index * 3 + 2] += triangleForce[2] / 3;
      vertexNormal[index * 3] += areaVector[0];
      vertexNormal[index * 3 + 1] += areaVector[1];
      vertexNormal[index * 3 + 2] += areaVector[2];
    }
  }
  const surfaceMeanPressure = surfaceArea > EPSILON ? pressureArea / surfaceArea : 0;
  const initialVolume = boundary.audit.enclosedVolume;
  const zeroDisplacements = new Float64Array(boundary.vertices.length);
  let lastReason = "no stable self-intersection-free candidate found";
  let lastMaximumDisplacement = 0;
  let lastVolume = initialVolume;
  let lastRelativeVolumeChange = 0;

  for (let lineSearchStep = 0; lineSearchStep < maximumLineSearchSteps; lineSearchStep += 1) {
    const compliance = options.normalCompliance * 0.5 ** lineSearchStep;
    const candidate = new Float64Array(boundary.vertices.length);
    const rawDisplacements = new Float64Array(boundary.vertices.length);
    for (let index = 0; index < vertexCount; index += 1) {
      const normalOffset = index * 3;
      const normalLength = Math.hypot(
        vertexNormal[normalOffset],
        vertexNormal[normalOffset + 1],
        vertexNormal[normalOffset + 2]
      );
      const localPressure = vertexArea[index] > EPSILON
        ? vertexPressureNumerator[index] / vertexArea[index]
        : surfaceMeanPressure;
      const rawMagnitude = compliance * (localPressure - surfaceMeanPressure);
      const magnitude = Math.max(
        -options.maximumVertexDisplacement,
        Math.min(options.maximumVertexDisplacement, rawMagnitude)
      );
      const inverseNormal = normalLength > EPSILON ? 1 / normalLength : 0;
      rawDisplacements[normalOffset] =
        vertexNormal[normalOffset] * inverseNormal * magnitude;
      rawDisplacements[normalOffset + 1] =
        vertexNormal[normalOffset + 1] * inverseNormal * magnitude;
      rawDisplacements[normalOffset + 2] =
        vertexNormal[normalOffset + 2] * inverseNormal * magnitude;
      candidate[normalOffset] =
        boundary.vertices[normalOffset] + rawDisplacements[normalOffset];
      candidate[normalOffset + 1] =
        boundary.vertices[normalOffset + 1] + rawDisplacements[normalOffset + 1];
      candidate[normalOffset + 2] =
        boundary.vertices[normalOffset + 2] + rawDisplacements[normalOffset + 2];
    }
    const rawVolume = Math.abs(signedVolume(candidate, boundary.triangles));
    if (!Number.isFinite(rawVolume) || rawVolume <= EPSILON) {
      lastReason = "candidate collapsed or inverted its enclosed volume";
      continue;
    }
    const correctionScale = (initialVolume / rawVolume) ** (1 / 3);
    for (let index = 0; index < vertexCount; index += 1) {
      const offset = index * 3;
      candidate[offset] = centroid[0] + (candidate[offset] - centroid[0]) * correctionScale;
      candidate[offset + 1] = centroid[1] + (candidate[offset + 1] - centroid[1]) * correctionScale;
      candidate[offset + 2] = centroid[2] + (candidate[offset + 2] - centroid[2]) * correctionScale;
    }
    const displacements = new Float64Array(boundary.vertices.length);
    let maximumAppliedDisplacement = 0;
    for (let index = 0; index < vertexCount; index += 1) {
      const offset = index * 3;
      displacements[offset] = candidate[offset] - boundary.vertices[offset];
      displacements[offset + 1] = candidate[offset + 1] - boundary.vertices[offset + 1];
      displacements[offset + 2] = candidate[offset + 2] - boundary.vertices[offset + 2];
      maximumAppliedDisplacement = Math.max(
        maximumAppliedDisplacement,
        Math.hypot(
          displacements[offset],
          displacements[offset + 1],
          displacements[offset + 2]
        )
      );
    }
    lastMaximumDisplacement = maximumAppliedDisplacement;
    if (maximumAppliedDisplacement > options.maximumVertexDisplacement * (1 + 1e-9)) {
      lastReason = "volume correction exceeded the maximum vertex displacement";
      continue;
    }
    const audit = auditTriangleMesh(candidate, boundary.triangles);
    lastVolume = audit.enclosedVolume;
    lastRelativeVolumeChange = Math.abs(lastVolume - initialVolume) / initialVolume;
    if (!audit.validClosedBoundary) {
      lastReason = "candidate failed topology or self-intersection audit";
      continue;
    }
    if (lastRelativeVolumeChange > volumeToleranceFraction) {
      lastReason = "candidate failed the enclosed-volume tolerance";
      continue;
    }
    const candidateBoundary = new WatertightTriangleMeshBoundary(
      candidate,
      boundary.triangles
    );
    let dimensionlessPressureWork = 0;
    for (let index = 0; index < vertexCount; index += 1) {
      const offset = index * 3;
      dimensionlessPressureWork += (
        pressureForce[offset] * displacements[offset] +
        pressureForce[offset + 1] * displacements[offset + 1] +
        pressureForce[offset + 2] * displacements[offset + 2]
      );
    }
    return {
      accepted: true,
      reason: "dimensionless candidate passed force, volume and mesh-validity checks",
      candidateBoundary,
      vertexDisplacements: displacements,
      surfaceMeanPressure,
      fluidResultant,
      membraneReaction: [
        -fluidResultant[0],
        -fluidResultant[1],
        -fluidResultant[2]
      ],
      fluidTorqueAboutCentroid: fluidTorque,
      dimensionlessPressureWork,
      initialVolume,
      candidateVolume: lastVolume,
      relativeVolumeChange: lastRelativeVolumeChange,
      maximumAppliedDisplacement,
      lineSearchStep,
      selfIntersectionFree: true,
      biologicalUnitsAssigned: false,
      runtimeFeedbackApplied: false
    };
  }

  return {
    accepted: false,
    reason: lastReason,
    candidateBoundary: null,
    vertexDisplacements: zeroDisplacements,
    surfaceMeanPressure,
    fluidResultant,
    membraneReaction: [
      -fluidResultant[0],
      -fluidResultant[1],
      -fluidResultant[2]
    ],
    fluidTorqueAboutCentroid: fluidTorque,
    dimensionlessPressureWork: 0,
    initialVolume,
    candidateVolume: lastVolume,
    relativeVolumeChange: lastRelativeVolumeChange,
    maximumAppliedDisplacement: lastMaximumDisplacement,
    lineSearchStep: maximumLineSearchSteps,
    selfIntersectionFree: false,
    biologicalUnitsAssigned: false,
    runtimeFeedbackApplied: false
  };
}
