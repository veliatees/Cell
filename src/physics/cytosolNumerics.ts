// Dimensionless cytosol numerics for the whole-cell renderer.
//
// This module supplies a real numerical projection step, moving analytic
// obstacle boundaries and a conservative passive-scalar kernel. It does not
// supply healthy-primary-human-hepatocyte viscosity, pressure, velocity,
// diffusivity or reaction-rate parameters. Those biological units remain
// evidence-gated by the Python engine.

export type CytosolVector3 = readonly [number, number, number];
export type CytosolQuaternion = readonly [number, number, number, number];

type CytosolObstacleBase = {
  id: string;
  center: CytosolVector3;
  orientation?: CytosolQuaternion;
  velocity?: CytosolVector3;
  angularVelocity?: CytosolVector3;
  boundarySampling?: "cell_center" | "conservative_subgrid";
};

export type CytosolSphereObstacle = CytosolObstacleBase & {
  kind: "sphere";
  radius: number;
};

export type CytosolEllipsoidObstacle = CytosolObstacleBase & {
  kind: "ellipsoid";
  radii: CytosolVector3;
};

export type CytosolCapsuleObstacle = CytosolObstacleBase & {
  kind: "capsule";
  radius: number;
  halfLength: number;
};

export type CytosolBoxObstacle = CytosolObstacleBase & {
  kind: "box";
  halfExtents: CytosolVector3;
};

export type CytosolObstacle =
  | CytosolSphereObstacle
  | CytosolEllipsoidObstacle
  | CytosolCapsuleObstacle
  | CytosolBoxObstacle;

type StoredObstacle = CytosolObstacle & {
  resolvedVelocity: CytosolVector3;
  resolvedAngularVelocity: CytosolVector3;
  boundingRadius: number;
};

export type CytosolProjectionOptions = {
  resolution: number;
  halfExtent: number;
  seed: number;
  radiusAtDirection: (x: number, y: number, z: number) => number;
  safetyFraction?: number;
  projectionIterations?: number;
  visualModeCount?: number;
};

export type CytosolProjectionDeformation = {
  normal: CytosolVector3;
  axialScale: number;
};

export type CytosolProjectionDiagnostics = {
  fluidCellCount: number;
  solidCellCount: number;
  obstacleCount: number;
  rotatingObstacleCount: number;
  subgridObstacleCount: number;
  fractionalMembraneCellCount: number;
  fractionalObstacleCellCount: number;
  subgridInterceptedCellCount: number;
  fractionalMembraneFaceCount: number;
  closedMembraneFaceCount: number;
  fractionalOpenFaceCount: number;
  closedObstacleFaceCount: number;
  meanInternalMembraneFaceOpenFraction: number;
  meanInternalFaceOpenFraction: number;
  dimensionlessMembraneVolumeEstimate: number;
  dimensionlessMembraneVolumeChangeRate: number;
  movingMembraneCellCount: number;
  dimensionlessObstacleVolumeEstimate: number;
  divergenceRmsBefore: number;
  divergenceRmsAfter: number;
  divergenceMaxAfter: number;
  dimensionlessBoundaryPressureRms: number;
  dimensionlessBoundaryReaction: CytosolVector3;
  biologicalUnitsAssigned: false;
  membranePressureFeedbackEnabled: false;
};

export type PassiveScalarDomainRemapDiagnostics = {
  remapCount: number;
  displacedCellCount: number;
  exposedCellCount: number;
  faceRedistributedCellCount: number;
  nearestFluidFallbackCellCount: number;
  displacedDimensionlessMass: number;
  redistributedDimensionlessMass: number;
  absoluteMassResidual: number;
  relativeMassResidual: number;
};

export const CYTOSOL_NUMERICAL_CONTRACT = Object.freeze({
  version: "dimensionless_moving_boundary_projection_v6",
  numericalMethod: "cell_centered_eulerian_cut_cell_projection_with_discrete_geometric_conservation",
  movingObstacleShapes: ["sphere", "ellipsoid", "capsule", "box"] as const,
  movingObstacleKinematics: "rigid_translation_plus_quaternion_derived_rotation",
  passiveScalarMethod: "finite_volume_advection_diffusion_with_conservative_moving_domain_remap",
  movingDomainRemap: "face_neighbor_redistribution_with_deterministic_nearest_fluid_fallback",
  outerMembraneTreatment: "star_shaped_2x2x2_volume_fraction_plus_2x2_face_area_quadrature",
  outerMembraneGeometricConservation: "cell_local_volume_change_source_in_pressure_projection",
  membraneSubgridQuadratureSamplesPerCell: 8,
  membraneFaceApertureQuadratureSamples: 4,
  locallyConservativeMembraneFaceFlux: true,
  thinBoundaryTreatment: "conservative_subgrid_2x2x2_volume_quadrature_plus_2x2_analytic_face_channel_intersections",
  subgridQuadratureSamplesPerCell: 8,
  faceApertureQuadratureChannels: 4,
  faceAperturePressureWeighted: true,
  faceApertureScalarFluxWeighted: true,
  partialCellVolumeConservation: true,
  subgridGridConvergenceTested: true,
  rendererVelocityUnits: "world_units_per_render_second",
  rendererAngularVelocityUnits: "radians_per_render_second",
  biologicalVelocityClaim: false,
  biologicalPressureClaim: false,
  biologicalDiffusivityClaim: false,
  quantitativePoroelasticSolver: false,
  reactionCouplingEnabled: false,
  membranePressureFeedbackEnabled: false,
  boundaryReactionRole: "dimensionless_diagnostic_pending_PHH_mechanics"
});

const ZERO_VECTOR: CytosolVector3 = [0, 0, 0];
const IDENTITY_QUATERNION: CytosolQuaternion = [0, 0, 0, 1];

function finiteVector(vector: CytosolVector3, name: string): void {
  if (vector.length !== 3 || vector.some((value) => !Number.isFinite(value))) {
    throw new RangeError(`${name} must contain three finite values`);
  }
}

function normalizedQuaternion(raw?: CytosolQuaternion): CytosolQuaternion {
  const [x, y, z, w] = raw ?? IDENTITY_QUATERNION;
  const length = Math.hypot(x, y, z, w);
  if (!Number.isFinite(length) || length <= 1e-12) {
    throw new RangeError("obstacle orientation must be a finite non-zero quaternion");
  }
  return [x / length, y / length, z / length, w / length];
}

export function capsuleObstacleBetween(
  id: string,
  start: CytosolVector3,
  end: CytosolVector3,
  radius: number,
  boundarySampling: "cell_center" | "conservative_subgrid" = "cell_center"
): CytosolCapsuleObstacle {
  if (!id) throw new RangeError("capsule segment id must be non-empty");
  finiteVector(start, `${id} start`);
  finiteVector(end, `${id} end`);
  if (!Number.isFinite(radius) || radius <= 0) {
    throw new RangeError(`${id} radius must be positive`);
  }
  const dx = end[0] - start[0];
  const dy = end[1] - start[1];
  const dz = end[2] - start[2];
  const length = Math.hypot(dx, dy, dz);
  if (length <= 1e-12) throw new RangeError(`${id} segment length must be positive`);
  const nx = dx / length;
  const ny = dy / length;
  const nz = dz / length;
  const orientation: CytosolQuaternion = ny < -1 + 1e-12
    ? [1, 0, 0, 0]
    : normalizedQuaternion([nz, 0, -nx, 1 + ny]);
  return {
    id,
    kind: "capsule",
    center: [
      (start[0] + end[0]) * 0.5,
      (start[1] + end[1]) * 0.5,
      (start[2] + end[2]) * 0.5
    ],
    orientation,
    radius,
    halfLength: length * 0.5,
    boundarySampling
  };
}

function quaternionDot(a: CytosolQuaternion, b: CytosolQuaternion): number {
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3];
}

function resolvedAngularVelocity(
  previous: CytosolQuaternion | undefined,
  current: CytosolQuaternion,
  deltaS: number
): CytosolVector3 {
  if (!previous || deltaS <= 1e-9) return ZERO_VECTOR;
  const aligned: CytosolQuaternion = quaternionDot(previous, current) < 0
    ? [-current[0], -current[1], -current[2], -current[3]]
    : current;
  const [px, py, pz, pw] = previous;
  const [cx, cy, cz, cw] = aligned;
  let dx = cw * -px + cx * pw + cy * -pz - cz * -py;
  let dy = cw * -py - cx * -pz + cy * pw + cz * -px;
  let dz = cw * -pz + cx * -py - cy * -px + cz * pw;
  let dw = cw * pw - cx * -px - cy * -py - cz * -pz;
  if (dw < 0) {
    dx = -dx;
    dy = -dy;
    dz = -dz;
    dw = -dw;
  }
  const vectorLength = Math.hypot(dx, dy, dz);
  if (vectorLength <= 1e-12) return ZERO_VECTOR;
  const angle = 2 * Math.atan2(vectorLength, Math.max(-1, Math.min(1, dw)));
  const scale = angle / (vectorLength * deltaS);
  return [dx * scale, dy * scale, dz * scale];
}

function inverseRotate(
  x: number,
  y: number,
  z: number,
  quaternion?: CytosolQuaternion
): CytosolVector3 {
  const [qx, qy, qz, qw] = normalizedQuaternion(quaternion);
  // q^-1 * v * q, expanded to avoid renderer-library dependencies.
  const tx = 2 * (-qy * z + qz * y);
  const ty = 2 * (-qz * x + qx * z);
  const tz = 2 * (-qx * y + qy * x);
  return [
    x + qw * tx + (-qy * tz + qz * ty),
    y + qw * ty + (-qz * tx + qx * tz),
    z + qw * tz + (-qx * ty + qy * tx)
  ];
}

function obstacleBoundingRadius(obstacle: CytosolObstacle): number {
  if (obstacle.kind === "sphere") return obstacle.radius;
  if (obstacle.kind === "ellipsoid") return Math.max(...obstacle.radii);
  if (obstacle.kind === "capsule") return obstacle.radius + obstacle.halfLength;
  return Math.hypot(...obstacle.halfExtents);
}

function validateObstacle(obstacle: CytosolObstacle): void {
  if (!obstacle.id) throw new RangeError("cytosol obstacle id must be non-empty");
  finiteVector(obstacle.center, `${obstacle.id} center`);
  if (obstacle.velocity) finiteVector(obstacle.velocity, `${obstacle.id} velocity`);
  if (obstacle.angularVelocity) {
    finiteVector(obstacle.angularVelocity, `${obstacle.id} angular velocity`);
  }
  normalizedQuaternion(obstacle.orientation);
  if (
    obstacle.boundarySampling !== undefined &&
    obstacle.boundarySampling !== "cell_center" &&
    obstacle.boundarySampling !== "conservative_subgrid"
  ) {
    throw new RangeError(`${obstacle.id} boundary sampling mode is invalid`);
  }
  if (obstacle.kind === "sphere") {
    if (!Number.isFinite(obstacle.radius) || obstacle.radius <= 0) {
      throw new RangeError(`${obstacle.id} sphere radius must be positive`);
    }
  } else if (obstacle.kind === "ellipsoid") {
    finiteVector(obstacle.radii, `${obstacle.id} radii`);
    if (obstacle.radii.some((value) => value <= 0)) {
      throw new RangeError(`${obstacle.id} ellipsoid radii must be positive`);
    }
  } else if (obstacle.kind === "capsule" && (
    !Number.isFinite(obstacle.radius) || obstacle.radius <= 0 ||
    !Number.isFinite(obstacle.halfLength) || obstacle.halfLength < 0
  )) {
    throw new RangeError(`${obstacle.id} capsule dimensions are invalid`);
  } else if (obstacle.kind === "box") {
    finiteVector(obstacle.halfExtents, `${obstacle.id} half extents`);
    if (obstacle.halfExtents.some((value) => value <= 0)) {
      throw new RangeError(`${obstacle.id} box half extents must be positive`);
    }
  }
}

function obstacleContains(
  obstacle: StoredObstacle,
  x: number,
  y: number,
  z: number,
  padding: number
): boolean {
  const dx = x - obstacle.center[0];
  const dy = y - obstacle.center[1];
  const dz = z - obstacle.center[2];
  if (dx * dx + dy * dy + dz * dz > (obstacle.boundingRadius + padding) ** 2) return false;
  const [lx, ly, lz] = inverseRotate(dx, dy, dz, obstacle.orientation);
  if (obstacle.kind === "sphere") {
    return lx * lx + ly * ly + lz * lz <= (obstacle.radius + padding) ** 2;
  }
  if (obstacle.kind === "ellipsoid") {
    const rx = obstacle.radii[0] + padding;
    const ry = obstacle.radii[1] + padding;
    const rz = obstacle.radii[2] + padding;
    return (lx / rx) ** 2 + (ly / ry) ** 2 + (lz / rz) ** 2 <= 1;
  }
  if (obstacle.kind === "capsule") {
    const closestY = Math.max(-obstacle.halfLength, Math.min(obstacle.halfLength, ly));
    return lx * lx + (ly - closestY) ** 2 + lz * lz <= (obstacle.radius + padding) ** 2;
  }
  return (
    Math.abs(lx) <= obstacle.halfExtents[0] + padding &&
    Math.abs(ly) <= obstacle.halfExtents[1] + padding &&
    Math.abs(lz) <= obstacle.halfExtents[2] + padding
  );
}

function dot3(a: CytosolVector3, b: CytosolVector3): number {
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}

function subtract3(a: CytosolVector3, b: CytosolVector3): CytosolVector3 {
  return [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
}

function pointSegmentDistanceSquared(
  point: CytosolVector3,
  start: CytosolVector3,
  end: CytosolVector3
): number {
  const segment = subtract3(end, start);
  const relative = subtract3(point, start);
  const denominator = dot3(segment, segment);
  const t = denominator > 1e-18
    ? Math.max(0, Math.min(1, dot3(relative, segment) / denominator))
    : 0;
  const dx = start[0] + segment[0] * t - point[0];
  const dy = start[1] + segment[1] * t - point[1];
  const dz = start[2] + segment[2] * t - point[2];
  return dx * dx + dy * dy + dz * dz;
}

function segmentIntersectsUnitSphere(start: CytosolVector3, end: CytosolVector3): boolean {
  if (dot3(start, start) <= 1 || dot3(end, end) <= 1) return true;
  const direction = subtract3(end, start);
  const a = dot3(direction, direction);
  if (a <= 1e-18) return false;
  const b = 2 * dot3(start, direction);
  const c = dot3(start, start) - 1;
  const discriminant = b * b - 4 * a * c;
  if (discriminant < 0) return false;
  const root = Math.sqrt(discriminant);
  const inverse = 1 / (2 * a);
  const first = (-b - root) * inverse;
  const second = (-b + root) * inverse;
  return (first >= 0 && first <= 1) || (second >= 0 && second <= 1);
}

function segmentIntersectsBox(
  start: CytosolVector3,
  end: CytosolVector3,
  halfExtents: CytosolVector3
): boolean {
  let minimum = 0;
  let maximum = 1;
  for (let axis = 0; axis < 3; axis += 1) {
    const direction = end[axis] - start[axis];
    const extent = halfExtents[axis];
    if (Math.abs(direction) <= 1e-18) {
      if (start[axis] < -extent || start[axis] > extent) return false;
      continue;
    }
    let first = (-extent - start[axis]) / direction;
    let second = (extent - start[axis]) / direction;
    if (first > second) [first, second] = [second, first];
    minimum = Math.max(minimum, first);
    maximum = Math.min(maximum, second);
    if (minimum > maximum) return false;
  }
  return true;
}

function segmentSegmentDistanceSquared(
  firstStart: CytosolVector3,
  firstEnd: CytosolVector3,
  secondStart: CytosolVector3,
  secondEnd: CytosolVector3
): number {
  const firstDirection = subtract3(firstEnd, firstStart);
  const secondDirection = subtract3(secondEnd, secondStart);
  const relative = subtract3(firstStart, secondStart);
  const firstLengthSquared = dot3(firstDirection, firstDirection);
  const secondLengthSquared = dot3(secondDirection, secondDirection);
  const secondProjection = dot3(secondDirection, relative);
  let firstParameter = 0;
  let secondParameter = 0;

  if (firstLengthSquared <= 1e-18 && secondLengthSquared <= 1e-18) {
    return dot3(relative, relative);
  }
  if (firstLengthSquared <= 1e-18) {
    secondParameter = Math.max(0, Math.min(1, secondProjection / secondLengthSquared));
  } else {
    const firstProjection = dot3(firstDirection, relative);
    if (secondLengthSquared <= 1e-18) {
      firstParameter = Math.max(0, Math.min(1, -firstProjection / firstLengthSquared));
    } else {
      const crossProjection = dot3(firstDirection, secondDirection);
      const denominator = firstLengthSquared * secondLengthSquared - crossProjection * crossProjection;
      firstParameter = denominator !== 0
        ? Math.max(0, Math.min(1, (
            crossProjection * secondProjection - firstProjection * secondLengthSquared
          ) / denominator))
        : 0;
      secondParameter = (
        crossProjection * firstParameter + secondProjection
      ) / secondLengthSquared;
      if (secondParameter < 0) {
        secondParameter = 0;
        firstParameter = Math.max(0, Math.min(1, -firstProjection / firstLengthSquared));
      } else if (secondParameter > 1) {
        secondParameter = 1;
        firstParameter = Math.max(
          0,
          Math.min(1, (crossProjection - firstProjection) / firstLengthSquared)
        );
      }
    }
  }

  const dx = (
    firstStart[0] + firstDirection[0] * firstParameter -
    secondStart[0] - secondDirection[0] * secondParameter
  );
  const dy = (
    firstStart[1] + firstDirection[1] * firstParameter -
    secondStart[1] - secondDirection[1] * secondParameter
  );
  const dz = (
    firstStart[2] + firstDirection[2] * firstParameter -
    secondStart[2] - secondDirection[2] * secondParameter
  );
  return dx * dx + dy * dy + dz * dz;
}

function obstacleIntersectsSegment(
  obstacle: StoredObstacle,
  start: CytosolVector3,
  end: CytosolVector3
): boolean {
  if (
    pointSegmentDistanceSquared(obstacle.center, start, end) >
    obstacle.boundingRadius ** 2
  ) {
    return false;
  }
  const localStart = inverseRotate(
    start[0] - obstacle.center[0],
    start[1] - obstacle.center[1],
    start[2] - obstacle.center[2],
    obstacle.orientation
  );
  const localEnd = inverseRotate(
    end[0] - obstacle.center[0],
    end[1] - obstacle.center[1],
    end[2] - obstacle.center[2],
    obstacle.orientation
  );
  if (obstacle.kind === "sphere") {
    return segmentIntersectsUnitSphere(
      [localStart[0] / obstacle.radius, localStart[1] / obstacle.radius, localStart[2] / obstacle.radius],
      [localEnd[0] / obstacle.radius, localEnd[1] / obstacle.radius, localEnd[2] / obstacle.radius]
    );
  }
  if (obstacle.kind === "ellipsoid") {
    return segmentIntersectsUnitSphere(
      [
        localStart[0] / obstacle.radii[0],
        localStart[1] / obstacle.radii[1],
        localStart[2] / obstacle.radii[2]
      ],
      [
        localEnd[0] / obstacle.radii[0],
        localEnd[1] / obstacle.radii[1],
        localEnd[2] / obstacle.radii[2]
      ]
    );
  }
  if (obstacle.kind === "box") {
    return segmentIntersectsBox(localStart, localEnd, obstacle.halfExtents);
  }
  return segmentSegmentDistanceSquared(
    localStart,
    localEnd,
    [0, -obstacle.halfLength, 0],
    [0, obstacle.halfLength, 0]
  ) <= obstacle.radius ** 2;
}

export class DynamicCytosolObstacleField {
  readonly cellSize: number;
  private obstacles: StoredObstacle[] = [];
  private readonly buckets = new Map<string, number[]>();
  private readonly previousCenters = new Map<string, CytosolVector3>();
  private readonly previousOrientations = new Map<string, CytosolQuaternion>();
  private readonly sampleVelocity = new Float32Array(3);
  private subgridObstacleCount = 0;

  constructor(cellSize: number) {
    if (!Number.isFinite(cellSize) || cellSize <= 0) {
      throw new RangeError("cytosol obstacle hash cell size must be positive");
    }
    this.cellSize = cellSize;
  }

  get count(): number {
    return this.obstacles.length;
  }

  get rotatingCount(): number {
    return this.obstacles.reduce((count, obstacle) => (
      Math.hypot(...obstacle.resolvedAngularVelocity) > 1e-9 ? count + 1 : count
    ), 0);
  }

  get subgridCount(): number {
    return this.subgridObstacleCount;
  }

  setObstacles(obstacles: readonly CytosolObstacle[], deltaS: number): void {
    if (!Number.isFinite(deltaS) || deltaS < 0) {
      throw new RangeError("obstacle update delta must be finite and non-negative");
    }
    const ids = new Set<string>();
    const next: StoredObstacle[] = [];
    for (const obstacle of obstacles) {
      validateObstacle(obstacle);
      if (ids.has(obstacle.id)) throw new RangeError(`duplicate cytosol obstacle id: ${obstacle.id}`);
      ids.add(obstacle.id);
      const previous = this.previousCenters.get(obstacle.id);
      const orientation = normalizedQuaternion(obstacle.orientation);
      const previousOrientation = this.previousOrientations.get(obstacle.id);
      const resolvedVelocity: CytosolVector3 = obstacle.velocity ?? (
        previous && deltaS > 1e-9
          ? [
              (obstacle.center[0] - previous[0]) / deltaS,
              (obstacle.center[1] - previous[1]) / deltaS,
              (obstacle.center[2] - previous[2]) / deltaS
            ]
          : ZERO_VECTOR
      );
      const angularVelocity = obstacle.angularVelocity ?? resolvedAngularVelocity(
        previousOrientation,
        orientation,
        deltaS
      );
      next.push({
        ...obstacle,
        orientation,
        resolvedVelocity,
        resolvedAngularVelocity: angularVelocity,
        boundingRadius: obstacleBoundingRadius(obstacle)
      });
      this.previousCenters.set(obstacle.id, [...obstacle.center]);
      this.previousOrientations.set(obstacle.id, orientation);
    }
    for (const id of this.previousCenters.keys()) {
      if (!ids.has(id)) {
        this.previousCenters.delete(id);
        this.previousOrientations.delete(id);
      }
    }
    this.obstacles = next;
    this.subgridObstacleCount = next.reduce((count, obstacle) => (
      obstacle.boundarySampling === "conservative_subgrid" ? count + 1 : count
    ), 0);
    this.rebuildHash();
  }

  collides(x: number, y: number, z: number, padding = 0): boolean {
    return this.findContaining(x, y, z, padding) !== null;
  }

  solidVelocityAt(
    x: number,
    y: number,
    z: number,
    target: Float32Array,
    offset = 0
  ): boolean {
    const obstacle = this.findContaining(x, y, z, 0);
    if (!obstacle) return false;
    this.writeObstacleVelocity(obstacle, x, y, z, target, offset);
    return true;
  }

  cellCenteredSolidVelocityAt(
    x: number,
    y: number,
    z: number,
    target: Float32Array,
    offset = 0
  ): boolean {
    const obstacle = this.findContaining(x, y, z, 0, "cell_center");
    if (!obstacle) return false;
    this.writeObstacleVelocity(obstacle, x, y, z, target, offset);
    return true;
  }

  sampleSubgridCell(
    x: number,
    y: number,
    z: number,
    cellWidth: number,
    targetVelocity: Float32Array,
    target: { solidFraction: number; centerContained: boolean; conservativeIntercept: boolean }
  ): void {
    if (![x, y, z, cellWidth].every(Number.isFinite) || cellWidth <= 0) {
      throw new RangeError("subgrid obstacle sample must be finite with positive cell width");
    }
    target.solidFraction = 0;
    target.centerContained = false;
    target.conservativeIntercept = false;
    targetVelocity[0] = 0;
    targetVelocity[1] = 0;
    targetVelocity[2] = 0;
    if (this.subgridCount === 0) return;

    const centerObstacle = this.findContaining(x, y, z, 0, "subgrid");
    target.centerContained = centerObstacle !== null;
    const quarter = cellWidth * 0.25;
    let sampleCount = 0;
    for (const dz of [-quarter, quarter]) {
      for (const dy of [-quarter, quarter]) {
        for (const dx of [-quarter, quarter]) {
          const sx = x + dx;
          const sy = y + dy;
          const sz = z + dz;
          const obstacle = this.findContaining(sx, sy, sz, 0, "subgrid");
          if (!obstacle) continue;
          this.writeObstacleVelocity(obstacle, sx, sy, sz, this.sampleVelocity, 0);
          targetVelocity[0] += this.sampleVelocity[0];
          targetVelocity[1] += this.sampleVelocity[1];
          targetVelocity[2] += this.sampleVelocity[2];
          sampleCount += 1;
        }
      }
    }
    if (sampleCount > 0) {
      target.solidFraction = sampleCount / 8;
      targetVelocity[0] /= sampleCount;
      targetVelocity[1] /= sampleCount;
      targetVelocity[2] /= sampleCount;
      target.conservativeIntercept = !target.centerContained;
      return;
    }

    // A membrane thinner than the quadrature spacing can still fall between all
    // eight samples. The half-cell diagonal gives a conservative intersection
    // test; assigning one subcell of occupancy keeps that boundary represented
    // while its excess volume shrinks under grid refinement.
    const halfDiagonal = Math.sqrt(3) * cellWidth * 0.5;
    const intersecting = this.findContaining(x, y, z, halfDiagonal, "subgrid");
    if (!intersecting) return;
    target.solidFraction = 1 / 8;
    target.conservativeIntercept = !target.centerContained;
    this.writeObstacleVelocity(intersecting, x, y, z, targetVelocity, 0);
  }

  sampleFaceOpenFraction(
    start: CytosolVector3,
    end: CytosolVector3,
    axis: 0 | 1 | 2,
    cellWidth: number
  ): number {
    finiteVector(start, "face aperture start");
    finiteVector(end, "face aperture end");
    if (!Number.isFinite(cellWidth) || cellWidth <= 0) {
      throw new RangeError("face aperture cell width must be positive");
    }
    if (this.obstacles.length === 0) return 1;

    const tangentialAxes = axis === 0 ? [1, 2] : axis === 1 ? [0, 2] : [0, 1];
    const quarter = cellWidth * 0.25;
    let blockedChannels = 0;
    for (const firstOffset of [-quarter, quarter]) {
      for (const secondOffset of [-quarter, quarter]) {
        const shiftedStart: [number, number, number] = [...start];
        const shiftedEnd: [number, number, number] = [...end];
        shiftedStart[tangentialAxes[0]] += firstOffset;
        shiftedEnd[tangentialAxes[0]] += firstOffset;
        shiftedStart[tangentialAxes[1]] += secondOffset;
        shiftedEnd[tangentialAxes[1]] += secondOffset;
        if (this.segmentIntersectsObstacle(shiftedStart, shiftedEnd)) {
          blockedChannels += 1;
        }
      }
    }
    if (blockedChannels === 0 && this.segmentIntersectsObstacle(start, end)) {
      // The centerline catches a feature narrower than the four midpoint
      // channels. One quarter-face is the conservative unresolved aperture.
      blockedChannels = 1;
    }
    return 1 - blockedChannels / 4;
  }

  private writeObstacleVelocity(
    obstacle: StoredObstacle,
    x: number,
    y: number,
    z: number,
    target: Float32Array,
    offset: number
  ): void {
    const rx = x - obstacle.center[0];
    const ry = y - obstacle.center[1];
    const rz = z - obstacle.center[2];
    const [wx, wy, wz] = obstacle.resolvedAngularVelocity;
    target[offset] = obstacle.resolvedVelocity[0] + wy * rz - wz * ry;
    target[offset + 1] = obstacle.resolvedVelocity[1] + wz * rx - wx * rz;
    target[offset + 2] = obstacle.resolvedVelocity[2] + wx * ry - wy * rx;
  }

  private gridCoordinate(value: number): number {
    return Math.floor(value / this.cellSize);
  }

  private key(ix: number, iy: number, iz: number): string {
    return `${ix}:${iy}:${iz}`;
  }

  private rebuildHash(): void {
    this.buckets.clear();
    for (let index = 0; index < this.obstacles.length; index += 1) {
      const obstacle = this.obstacles[index];
      const radius = obstacle.boundingRadius;
      const minX = this.gridCoordinate(obstacle.center[0] - radius);
      const maxX = this.gridCoordinate(obstacle.center[0] + radius);
      const minY = this.gridCoordinate(obstacle.center[1] - radius);
      const maxY = this.gridCoordinate(obstacle.center[1] + radius);
      const minZ = this.gridCoordinate(obstacle.center[2] - radius);
      const maxZ = this.gridCoordinate(obstacle.center[2] + radius);
      for (let iz = minZ; iz <= maxZ; iz += 1) {
        for (let iy = minY; iy <= maxY; iy += 1) {
          for (let ix = minX; ix <= maxX; ix += 1) {
            const key = this.key(ix, iy, iz);
            const bucket = this.buckets.get(key);
            if (bucket) bucket.push(index);
            else this.buckets.set(key, [index]);
          }
        }
      }
    }
  }

  private segmentIntersectsObstacle(
    start: CytosolVector3,
    end: CytosolVector3
  ): boolean {
    const minX = this.gridCoordinate(Math.min(start[0], end[0]));
    const maxX = this.gridCoordinate(Math.max(start[0], end[0]));
    const minY = this.gridCoordinate(Math.min(start[1], end[1]));
    const maxY = this.gridCoordinate(Math.max(start[1], end[1]));
    const minZ = this.gridCoordinate(Math.min(start[2], end[2]));
    const maxZ = this.gridCoordinate(Math.max(start[2], end[2]));
    const visited = new Set<number>();
    for (let iz = minZ; iz <= maxZ; iz += 1) {
      for (let iy = minY; iy <= maxY; iy += 1) {
        for (let ix = minX; ix <= maxX; ix += 1) {
          const bucket = this.buckets.get(this.key(ix, iy, iz));
          if (!bucket) continue;
          for (const index of bucket) {
            if (visited.has(index)) continue;
            visited.add(index);
            if (obstacleIntersectsSegment(this.obstacles[index], start, end)) return true;
          }
        }
      }
    }
    return false;
  }

  private findContaining(
    x: number,
    y: number,
    z: number,
    padding: number,
    samplingFilter: "all" | "subgrid" | "cell_center" = "all"
  ): StoredObstacle | null {
    if (![x, y, z, padding].every(Number.isFinite) || padding < 0) {
      throw new RangeError("cytosol obstacle query must be finite with non-negative padding");
    }
    const range = Math.max(0, Math.ceil(padding / this.cellSize));
    const cx = this.gridCoordinate(x);
    const cy = this.gridCoordinate(y);
    const cz = this.gridCoordinate(z);
    const visited = new Set<number>();
    for (let dz = -range; dz <= range; dz += 1) {
      for (let dy = -range; dy <= range; dy += 1) {
        for (let dx = -range; dx <= range; dx += 1) {
          const bucket = this.buckets.get(this.key(cx + dx, cy + dy, cz + dz));
          if (!bucket) continue;
          for (const index of bucket) {
            if (visited.has(index)) continue;
            visited.add(index);
            const obstacle = this.obstacles[index];
            if (
              samplingFilter === "subgrid" &&
              obstacle.boundarySampling !== "conservative_subgrid"
            ) continue;
            if (
              samplingFilter === "cell_center" &&
              obstacle.boundarySampling === "conservative_subgrid"
            ) continue;
            if (obstacleContains(obstacle, x, y, z, padding)) return obstacle;
          }
        }
      }
    }
    return null;
  }
}

type ProjectionMode = {
  center: CytosolVector3;
  axis: CytosolVector3;
  influenceRadius: number;
  signedRate: number;
  temporalRate: number;
  phase: number;
};

function seededRandom(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state = (Math.imul(1_664_525, state) + 1_013_904_223) >>> 0;
    return state / 4_294_967_296;
  };
}

function randomDirection(random: () => number): CytosolVector3 {
  for (let attempt = 0; attempt < 32; attempt += 1) {
    const x = random() * 2 - 1;
    const y = random() * 2 - 1;
    const z = random() * 2 - 1;
    const length = Math.hypot(x, y, z);
    if (length > 1e-6 && length <= 1) return [x / length, y / length, z / length];
  }
  return [1, 0, 0];
}

function validateDeformation(deformation: CytosolProjectionDeformation | null): void {
  if (!deformation) return;
  finiteVector(deformation.normal, "cytosol deformation normal");
  if (Math.hypot(...deformation.normal) <= 1e-12) {
    throw new RangeError("cytosol deformation normal must be non-zero");
  }
  if (!Number.isFinite(deformation.axialScale) || deformation.axialScale <= 0) {
    throw new RangeError("cytosol deformation axial scale must be positive");
  }
}

export function inverseVolumePreservingPoint(
  x: number,
  y: number,
  z: number,
  deformation: CytosolProjectionDeformation | null,
  target: Float32Array,
  offset = 0
): void {
  if (!deformation) {
    target[offset] = x;
    target[offset + 1] = y;
    target[offset + 2] = z;
    return;
  }
  validateDeformation(deformation);
  const length = Math.hypot(...deformation.normal);
  const nx = deformation.normal[0] / length;
  const ny = deformation.normal[1] / length;
  const nz = deformation.normal[2] / length;
  const inverseAxial = 1 / deformation.axialScale;
  const inverseTangential = Math.sqrt(deformation.axialScale);
  const projection = x * nx + y * ny + z * nz;
  const correction = (inverseAxial - inverseTangential) * projection;
  target[offset] = inverseTangential * x + correction * nx;
  target[offset + 1] = inverseTangential * y + correction * ny;
  target[offset + 2] = inverseTangential * z + correction * nz;
}

export class CytosolProjectionGrid {
  readonly resolution: number;
  readonly halfExtent: number;
  readonly spacing: number;
  readonly fluidMask: Uint8Array;
  readonly fluidVolumeFraction: Float32Array;
  readonly membraneFluidFraction: Float32Array;
  readonly obstacleSolidFraction: Float32Array;
  readonly membraneFaceOpenFractionX: Float32Array;
  readonly membraneFaceOpenFractionY: Float32Array;
  readonly membraneFaceOpenFractionZ: Float32Array;
  readonly faceOpenFractionX: Float32Array;
  readonly faceOpenFractionY: Float32Array;
  readonly faceOpenFractionZ: Float32Array;
  readonly velocityX: Float32Array;
  readonly velocityY: Float32Array;
  readonly velocityZ: Float32Array;

  private readonly radiusAtDirection: CytosolProjectionOptions["radiusAtDirection"];
  private readonly safetyFraction: number;
  private readonly projectionIterations: number;
  private readonly pressure: Float32Array;
  private readonly nextPressure: Float32Array;
  private readonly divergence: Float32Array;
  private readonly previousMembraneFluidFraction: Float32Array;
  private readonly membraneTargetDivergence: Float32Array;
  private readonly obstacleVelocityX: Float32Array;
  private readonly obstacleVelocityY: Float32Array;
  private readonly obstacleVelocityZ: Float32Array;
  private readonly subgridSample = {
    solidFraction: 0,
    centerContained: false,
    conservativeIntercept: false
  };
  private domainInitialized = false;
  private fractionalMembraneCellCount = 0;
  private fractionalObstacleCellCount = 0;
  private subgridInterceptedCellCount = 0;
  private fractionalMembraneFaceCount = 0;
  private closedMembraneFaceCount = 0;
  private fractionalOpenFaceCount = 0;
  private closedObstacleFaceCount = 0;
  private meanInternalMembraneFaceOpenFraction = 0;
  private meanInternalFaceOpenFraction = 0;
  private dimensionlessMembraneVolumeChangeRate = 0;
  private movingMembraneCellCount = 0;
  private readonly modes: ProjectionMode[];
  private elapsedRenderS = 0;
  private currentDiagnostics: CytosolProjectionDiagnostics = {
    fluidCellCount: 0,
    solidCellCount: 0,
    obstacleCount: 0,
    rotatingObstacleCount: 0,
    subgridObstacleCount: 0,
    fractionalMembraneCellCount: 0,
    fractionalObstacleCellCount: 0,
    subgridInterceptedCellCount: 0,
    fractionalMembraneFaceCount: 0,
    closedMembraneFaceCount: 0,
    fractionalOpenFaceCount: 0,
    closedObstacleFaceCount: 0,
    meanInternalMembraneFaceOpenFraction: 0,
    meanInternalFaceOpenFraction: 0,
    dimensionlessMembraneVolumeEstimate: 0,
    dimensionlessMembraneVolumeChangeRate: 0,
    movingMembraneCellCount: 0,
    dimensionlessObstacleVolumeEstimate: 0,
    divergenceRmsBefore: 0,
    divergenceRmsAfter: 0,
    divergenceMaxAfter: 0,
    dimensionlessBoundaryPressureRms: 0,
    dimensionlessBoundaryReaction: [0, 0, 0],
    biologicalUnitsAssigned: false,
    membranePressureFeedbackEnabled: false
  };

  constructor(options: CytosolProjectionOptions) {
    if (!Number.isInteger(options.resolution) || options.resolution < 6 || options.resolution > 64) {
      throw new RangeError("cytosol grid resolution must be an integer in [6, 64]");
    }
    if (!Number.isFinite(options.halfExtent) || options.halfExtent <= 0) {
      throw new RangeError("cytosol grid half extent must be positive");
    }
    const safetyFraction = options.safetyFraction ?? 0.9;
    if (!Number.isFinite(safetyFraction) || safetyFraction <= 0 || safetyFraction > 1) {
      throw new RangeError("cytosol grid safety fraction must be in (0, 1]");
    }
    const projectionIterations = options.projectionIterations ?? 24;
    if (!Number.isInteger(projectionIterations) || projectionIterations <= 0) {
      throw new RangeError("cytosol projection iterations must be positive");
    }
    const visualModeCount = options.visualModeCount ?? 5;
    if (!Number.isInteger(visualModeCount) || visualModeCount < 0) {
      throw new RangeError("cytosol visual mode count must be non-negative");
    }

    this.resolution = options.resolution;
    this.halfExtent = options.halfExtent;
    this.spacing = (2 * options.halfExtent) / options.resolution;
    this.radiusAtDirection = options.radiusAtDirection;
    this.safetyFraction = safetyFraction;
    this.projectionIterations = projectionIterations;
    const count = options.resolution ** 3;
    this.fluidMask = new Uint8Array(count);
    this.fluidVolumeFraction = new Float32Array(count);
    this.membraneFluidFraction = new Float32Array(count);
    this.obstacleSolidFraction = new Float32Array(count);
    this.membraneFaceOpenFractionX = new Float32Array(count);
    this.membraneFaceOpenFractionY = new Float32Array(count);
    this.membraneFaceOpenFractionZ = new Float32Array(count);
    this.faceOpenFractionX = new Float32Array(count);
    this.faceOpenFractionY = new Float32Array(count);
    this.faceOpenFractionZ = new Float32Array(count);
    this.velocityX = new Float32Array(count);
    this.velocityY = new Float32Array(count);
    this.velocityZ = new Float32Array(count);
    this.obstacleVelocityX = new Float32Array(count);
    this.obstacleVelocityY = new Float32Array(count);
    this.obstacleVelocityZ = new Float32Array(count);
    this.pressure = new Float32Array(count);
    this.nextPressure = new Float32Array(count);
    this.divergence = new Float32Array(count);
    this.previousMembraneFluidFraction = new Float32Array(count);
    this.membraneTargetDivergence = new Float32Array(count);

    const random = seededRandom(options.seed);
    this.modes = Array.from({ length: visualModeCount }, () => {
      const centerDirection = randomDirection(random);
      return {
        center: [
          centerDirection[0] * options.halfExtent * random() * 0.3,
          centerDirection[1] * options.halfExtent * random() * 0.3,
          centerDirection[2] * options.halfExtent * random() * 0.3
        ],
        axis: randomDirection(random),
        influenceRadius: options.halfExtent * (0.38 + random() * 0.42),
        // Renderer coefficient only. It has no micrometre/second interpretation.
        signedRate: (random() < 0.5 ? -1 : 1) * (0.018 + random() * 0.018),
        temporalRate: 0.12 + random() * 0.28,
        phase: random() * Math.PI * 2
      };
    });
  }

  diagnostics(): CytosolProjectionDiagnostics {
    return { ...this.currentDiagnostics };
  }

  step(
    renderDeltaS: number,
    deformation: CytosolProjectionDeformation | null,
    obstacles?: DynamicCytosolObstacleField
  ): void {
    if (!Number.isFinite(renderDeltaS) || renderDeltaS < 0) {
      throw new RangeError("cytosol projection delta must be finite and non-negative");
    }
    validateDeformation(deformation);
    const dt = Math.min(renderDeltaS, 0.05);
    this.elapsedRenderS += dt;
    this.rebuildDomainAndTentativeVelocity(
      deformation,
      obstacles,
      renderDeltaS
    );
    const before = this.measureAndStoreDivergence();
    this.projectVelocity();
    const after = this.measureAndStoreDivergence();
    const boundary = this.boundaryReactionDiagnostic();
    const fluidCellCount = this.fluidMask.reduce((sum, value) => sum + value, 0);
    this.currentDiagnostics = {
      fluidCellCount,
      solidCellCount: this.fluidMask.length - fluidCellCount,
      obstacleCount: obstacles?.count ?? 0,
      rotatingObstacleCount: obstacles?.rotatingCount ?? 0,
      subgridObstacleCount: obstacles?.subgridCount ?? 0,
      fractionalMembraneCellCount: this.fractionalMembraneCellCount,
      fractionalObstacleCellCount: this.fractionalObstacleCellCount,
      subgridInterceptedCellCount: this.subgridInterceptedCellCount,
      fractionalMembraneFaceCount: this.fractionalMembraneFaceCount,
      closedMembraneFaceCount: this.closedMembraneFaceCount,
      fractionalOpenFaceCount: this.fractionalOpenFaceCount,
      closedObstacleFaceCount: this.closedObstacleFaceCount,
      meanInternalMembraneFaceOpenFraction:
        this.meanInternalMembraneFaceOpenFraction,
      meanInternalFaceOpenFraction: this.meanInternalFaceOpenFraction,
      dimensionlessMembraneVolumeEstimate: this.membraneVolumeEstimate(),
      dimensionlessMembraneVolumeChangeRate:
        this.dimensionlessMembraneVolumeChangeRate,
      movingMembraneCellCount: this.movingMembraneCellCount,
      dimensionlessObstacleVolumeEstimate: this.obstacleVolumeEstimate(),
      divergenceRmsBefore: before.rms,
      divergenceRmsAfter: after.rms,
      divergenceMaxAfter: after.max,
      dimensionlessBoundaryPressureRms: boundary.pressureRms,
      dimensionlessBoundaryReaction: boundary.reaction,
      biologicalUnitsAssigned: false,
      membranePressureFeedbackEnabled: false
    };
  }

  sampleVelocity(x: number, y: number, z: number, target: Float32Array, offset = 0): boolean {
    if (![x, y, z].every(Number.isFinite)) throw new RangeError("velocity sample must be finite");
    const gx = (x + this.halfExtent) / this.spacing - 0.5;
    const gy = (y + this.halfExtent) / this.spacing - 0.5;
    const gz = (z + this.halfExtent) / this.spacing - 0.5;
    const i0 = Math.floor(gx);
    const j0 = Math.floor(gy);
    const k0 = Math.floor(gz);
    if (i0 < 0 || j0 < 0 || k0 < 0 || i0 >= this.resolution - 1 || j0 >= this.resolution - 1 || k0 >= this.resolution - 1) {
      target[offset] = 0;
      target[offset + 1] = 0;
      target[offset + 2] = 0;
      return false;
    }
    const tx = gx - i0;
    const ty = gy - j0;
    const tz = gz - k0;
    let weightSum = 0;
    let vx = 0;
    let vy = 0;
    let vz = 0;
    for (let dz = 0; dz <= 1; dz += 1) {
      for (let dy = 0; dy <= 1; dy += 1) {
        for (let dx = 0; dx <= 1; dx += 1) {
          const index = this.index(i0 + dx, j0 + dy, k0 + dz);
          if (!this.fluidMask[index]) continue;
          const weight = (dx ? tx : 1 - tx) * (dy ? ty : 1 - ty) * (dz ? tz : 1 - tz);
          weightSum += weight;
          vx += this.velocityX[index] * weight;
          vy += this.velocityY[index] * weight;
          vz += this.velocityZ[index] * weight;
        }
      }
    }
    if (weightSum <= 1e-12) {
      target[offset] = 0;
      target[offset + 1] = 0;
      target[offset + 2] = 0;
      return false;
    }
    target[offset] = vx / weightSum;
    target[offset + 1] = vy / weightSum;
    target[offset + 2] = vz / weightSum;
    return true;
  }

  cellCenter(index: number, target: Float32Array, offset = 0): void {
    if (!Number.isInteger(index) || index < 0 || index >= this.fluidMask.length) {
      throw new RangeError("cytosol cell index is out of range");
    }
    const plane = this.resolution * this.resolution;
    const k = Math.floor(index / plane);
    const remainder = index - k * plane;
    const j = Math.floor(remainder / this.resolution);
    const i = remainder - j * this.resolution;
    target[offset] = -this.halfExtent + (i + 0.5) * this.spacing;
    target[offset + 1] = -this.halfExtent + (j + 0.5) * this.spacing;
    target[offset + 2] = -this.halfExtent + (k + 0.5) * this.spacing;
  }

  obstacleVolumeEstimate(): number {
    const cellVolume = this.spacing ** 3;
    let fractionSum = 0;
    for (const fraction of this.obstacleSolidFraction) fractionSum += fraction;
    return fractionSum * cellVolume;
  }

  membraneVolumeEstimate(): number {
    const cellVolume = this.spacing ** 3;
    let fractionSum = 0;
    for (const fraction of this.membraneFluidFraction) fractionSum += fraction;
    return fractionSum * cellVolume;
  }

  private index(i: number, j: number, k: number): number {
    return i + this.resolution * (j + this.resolution * k);
  }

  private insideGrid(i: number, j: number, k: number): boolean {
    return i >= 0 && j >= 0 && k >= 0 && i < this.resolution && j < this.resolution && k < this.resolution;
  }

  private membraneContainsPoint(
    x: number,
    y: number,
    z: number,
    deformation: CytosolProjectionDeformation | null,
    reference: Float32Array
  ): boolean {
    inverseVolumePreservingPoint(x, y, z, deformation, reference);
    const length = Math.hypot(reference[0], reference[1], reference[2]);
    if (length <= 1e-12) return true;
    const radius = this.radiusAtDirection(
      reference[0] / length,
      reference[1] / length,
      reference[2] / length
    );
    if (!Number.isFinite(radius) || radius <= 0) {
      throw new RangeError("cytosol domain radius must be finite and positive");
    }
    return length <= radius * this.safetyFraction;
  }

  private sampleMembraneCellFluidFraction(
    x: number,
    y: number,
    z: number,
    deformation: CytosolProjectionDeformation | null,
    reference: Float32Array
  ): number {
    const offset = this.spacing * 0.25;
    let insideCount = 0;
    for (const dz of [-offset, offset]) {
      for (const dy of [-offset, offset]) {
        for (const dx of [-offset, offset]) {
          if (this.membraneContainsPoint(
            x + dx,
            y + dy,
            z + dz,
            deformation,
            reference
          )) {
            insideCount += 1;
          }
        }
      }
    }
    return insideCount / 8;
  }

  private sampleMembraneFaceOpenFraction(
    first: Float32Array,
    second: Float32Array,
    axis: 0 | 1 | 2,
    deformation: CytosolProjectionDeformation | null,
    reference: Float32Array
  ): number {
    const center: CytosolVector3 = [
      (first[0] + second[0]) * 0.5,
      (first[1] + second[1]) * 0.5,
      (first[2] + second[2]) * 0.5
    ];
    const offset = this.spacing * 0.25;
    const tangentA = axis === 0 ? 1 : 0;
    const tangentB = axis === 2 ? 1 : 2;
    let insideCount = 0;
    for (const firstOffset of [-offset, offset]) {
      for (const secondOffset of [-offset, offset]) {
        const point: [number, number, number] = [
          center[0],
          center[1],
          center[2]
        ];
        point[tangentA] += firstOffset;
        point[tangentB] += secondOffset;
        if (this.membraneContainsPoint(
          point[0],
          point[1],
          point[2],
          deformation,
          reference
        )) {
          insideCount += 1;
        }
      }
    }
    return insideCount / 4;
  }

  private rebuildDomainAndTentativeVelocity(
    deformation: CytosolProjectionDeformation | null,
    obstacles?: DynamicCytosolObstacleField,
    boundaryDeltaS = 0
  ): void {
    const point = new Float32Array(3);
    const reference = new Float32Array(3);
    const solidVelocity = new Float32Array(3);
    if (this.domainInitialized) {
      this.previousMembraneFluidFraction.set(this.membraneFluidFraction);
    }
    this.fractionalMembraneCellCount = 0;
    this.fractionalObstacleCellCount = 0;
    this.subgridInterceptedCellCount = 0;
    this.dimensionlessMembraneVolumeChangeRate = 0;
    this.movingMembraneCellCount = 0;
    this.membraneTargetDivergence.fill(0);
    const cellVolume = this.spacing ** 3;
    for (let index = 0; index < this.fluidMask.length; index += 1) {
      this.cellCenter(index, point);
      const membraneFraction = this.sampleMembraneCellFluidFraction(
        point[0],
        point[1],
        point[2],
        deformation,
        reference
      );
      this.membraneFluidFraction[index] = membraneFraction;
      if (membraneFraction > 1e-9 && membraneFraction < 1 - 1e-9) {
        this.fractionalMembraneCellCount += 1;
      }
      let obstacleFraction = 0;
      let insideObstacle = false;
      solidVelocity[0] = 0;
      solidVelocity[1] = 0;
      solidVelocity[2] = 0;
      if (membraneFraction > 1e-9 && obstacles) {
        obstacles.sampleSubgridCell(
          point[0],
          point[1],
          point[2],
          this.spacing,
          solidVelocity,
          this.subgridSample
        );
        obstacleFraction = this.subgridSample.solidFraction;
        insideObstacle = obstacleFraction >= 1 - 1e-9;
        if (this.subgridSample.conservativeIntercept) {
          this.subgridInterceptedCellCount += 1;
        }
        if (!insideObstacle) {
          insideObstacle = obstacles.cellCenteredSolidVelocityAt(
            point[0], point[1], point[2], solidVelocity
          );
          if (insideObstacle) obstacleFraction = 1;
        }
      }
      this.obstacleSolidFraction[index] = obstacleFraction;
      if (obstacleFraction > 0 && obstacleFraction < 1) {
        this.fractionalObstacleCellCount += 1;
      }
      const fluidVolumeFraction = Math.max(
        0,
        Math.min(1, membraneFraction * (1 - obstacleFraction))
      );
      this.fluidVolumeFraction[index] = fluidVolumeFraction;
      this.fluidMask[index] = fluidVolumeFraction > 1e-9 && !insideObstacle ? 1 : 0;
      this.obstacleVelocityX[index] = solidVelocity[0];
      this.obstacleVelocityY[index] = solidVelocity[1];
      this.obstacleVelocityZ[index] = solidVelocity[2];
      if (!this.fluidMask[index]) {
        this.velocityX[index] = insideObstacle ? solidVelocity[0] : 0;
        this.velocityY[index] = insideObstacle ? solidVelocity[1] : 0;
        this.velocityZ[index] = insideObstacle ? solidVelocity[2] : 0;
        continue;
      }
      let vx = 0;
      let vy = 0;
      let vz = 0;
      for (const mode of this.modes) {
        const rx = point[0] - mode.center[0];
        const ry = point[1] - mode.center[1];
        const rz = point[2] - mode.center[2];
        const weight = Math.exp(-(rx * rx + ry * ry + rz * rz) / (mode.influenceRadius ** 2));
        const modulation = 1 + 0.24 * Math.sin(mode.phase + this.elapsedRenderS * mode.temporalRate);
        const strength = mode.signedRate * modulation * weight;
        vx += (mode.axis[1] * rz - mode.axis[2] * ry) * strength;
        vy += (mode.axis[2] * rx - mode.axis[0] * rz) * strength;
        vz += (mode.axis[0] * ry - mode.axis[1] * rx) * strength;
      }
      this.velocityX[index] = vx;
      this.velocityY[index] = vy;
      this.velocityZ[index] = vz;
    }
    if (this.domainInitialized && boundaryDeltaS > 1e-9) {
      for (let index = 0; index < this.fluidMask.length; index += 1) {
        const membraneVolumeFractionChange = (
          this.membraneFluidFraction[index] -
          this.previousMembraneFluidFraction[index]
        );
        if (Math.abs(membraneVolumeFractionChange) <= 1e-9) continue;
        this.movingMembraneCellCount += 1;
        const availableFraction = Math.max(
          0,
          1 - this.obstacleSolidFraction[index]
        );
        const availableVolumeChangeRate = (
          membraneVolumeFractionChange *
          availableFraction /
          boundaryDeltaS
        );
        this.dimensionlessMembraneVolumeChangeRate += (
          availableVolumeChangeRate * cellVolume
        );
        if (this.fluidVolumeFraction[index] > 1e-9) {
          this.membraneTargetDivergence[index] = (
            -availableVolumeChangeRate /
            this.fluidVolumeFraction[index]
          );
        }
      }
    }
    this.domainInitialized = true;
    this.rebuildFaceApertures(deformation, obstacles);
  }

  private rebuildFaceApertures(
    deformation: CytosolProjectionDeformation | null,
    obstacles?: DynamicCytosolObstacleField
  ): void {
    this.membraneFaceOpenFractionX.fill(0);
    this.membraneFaceOpenFractionY.fill(0);
    this.membraneFaceOpenFractionZ.fill(0);
    this.faceOpenFractionX.fill(0);
    this.faceOpenFractionY.fill(0);
    this.faceOpenFractionZ.fill(0);
    this.fractionalMembraneFaceCount = 0;
    this.closedMembraneFaceCount = 0;
    this.fractionalOpenFaceCount = 0;
    this.closedObstacleFaceCount = 0;
    this.meanInternalMembraneFaceOpenFraction = 0;
    this.meanInternalFaceOpenFraction = 0;
    const n = this.resolution;
    const first = new Float32Array(3);
    const second = new Float32Array(3);
    const reference = new Float32Array(3);
    let internalFaceCount = 0;
    let membraneOpenFractionSum = 0;
    let openFractionSum = 0;
    const sample = (
      index: number,
      neighbor: number,
      axis: 0 | 1 | 2,
      membraneTarget: Float32Array,
      target: Float32Array
    ) => {
      if (!this.fluidMask[index] || !this.fluidMask[neighbor]) return;
      this.cellCenter(index, first);
      this.cellCenter(neighbor, second);
      const membraneOpenFraction = this.sampleMembraneFaceOpenFraction(
        first,
        second,
        axis,
        deformation,
        reference
      );
      membraneTarget[index] = membraneOpenFraction;
      let obstacleOpenFraction = 1;
      if (obstacles && obstacles.count > 0) {
        obstacleOpenFraction = obstacles.sampleFaceOpenFraction(
          [first[0], first[1], first[2]],
          [second[0], second[1], second[2]],
          axis,
          this.spacing
        );
      }
      const openFraction = membraneOpenFraction * obstacleOpenFraction;
      target[index] = openFraction;
      internalFaceCount += 1;
      membraneOpenFractionSum += membraneOpenFraction;
      openFractionSum += openFraction;
      if (
        membraneOpenFraction > 1e-9 &&
        membraneOpenFraction < 1 - 1e-9
      ) {
        this.fractionalMembraneFaceCount += 1;
      } else if (membraneOpenFraction <= 1e-9) {
        this.closedMembraneFaceCount += 1;
      }
      if (openFraction > 1e-9 && openFraction < 1 - 1e-9) {
        this.fractionalOpenFaceCount += 1;
      }
      if (obstacleOpenFraction <= 1e-9) {
        this.closedObstacleFaceCount += 1;
      }
    };
    for (let k = 0; k < n; k += 1) {
      for (let j = 0; j < n; j += 1) {
        for (let i = 0; i < n; i += 1) {
          const index = this.index(i, j, k);
          if (i + 1 < n) sample(
            index,
            index + 1,
            0,
            this.membraneFaceOpenFractionX,
            this.faceOpenFractionX
          );
          if (j + 1 < n) sample(
            index,
            index + n,
            1,
            this.membraneFaceOpenFractionY,
            this.faceOpenFractionY
          );
          if (k + 1 < n) sample(
            index,
            index + n * n,
            2,
            this.membraneFaceOpenFractionZ,
            this.faceOpenFractionZ
          );
        }
      }
    }
    this.meanInternalMembraneFaceOpenFraction = internalFaceCount > 0
      ? membraneOpenFractionSum / internalFaceCount
      : 0;
    this.meanInternalFaceOpenFraction = internalFaceCount > 0
      ? openFractionSum / internalFaceCount
      : 0;
  }

  private faceAperture(
    i: number,
    j: number,
    k: number,
    axis: 0 | 1 | 2,
    direction: -1 | 1
  ): number {
    const ni = i + (axis === 0 ? direction : 0);
    const nj = j + (axis === 1 ? direction : 0);
    const nk = k + (axis === 2 ? direction : 0);
    if (!this.insideGrid(ni, nj, nk)) return 0;
    const source = direction > 0 ? this.index(i, j, k) : this.index(ni, nj, nk);
    return axis === 0
      ? this.faceOpenFractionX[source]
      : axis === 1
        ? this.faceOpenFractionY[source]
        : this.faceOpenFractionZ[source];
  }

  private faceNormalVelocity(
    i: number,
    j: number,
    k: number,
    axis: 0 | 1 | 2,
    direction: -1 | 1
  ): number {
    const centerIndex = this.index(i, j, k);
    const ni = i + (axis === 0 ? direction : 0);
    const nj = j + (axis === 1 ? direction : 0);
    const nk = k + (axis === 2 ? direction : 0);
    const aperture = this.faceAperture(i, j, k, axis, direction);
    const velocity = axis === 0
      ? this.velocityX
      : axis === 1
        ? this.velocityY
        : this.velocityZ;
    const obstacleVelocity = axis === 0
      ? this.obstacleVelocityX
      : axis === 1
        ? this.obstacleVelocityY
        : this.obstacleVelocityZ;
    let fluidVelocity = velocity[centerIndex];
    let wallVelocity = obstacleVelocity[centerIndex];
    if (this.insideGrid(ni, nj, nk)) {
      const neighborIndex = this.index(ni, nj, nk);
      if (this.fluidMask[neighborIndex]) {
        fluidVelocity = 0.5 * (fluidVelocity + velocity[neighborIndex]);
      }
      const centerSolid = this.obstacleSolidFraction[centerIndex];
      const neighborSolid = this.obstacleSolidFraction[neighborIndex];
      const solidWeight = centerSolid + neighborSolid;
      wallVelocity = solidWeight > 1e-12
        ? (
            obstacleVelocity[centerIndex] * centerSolid +
            obstacleVelocity[neighborIndex] * neighborSolid
          ) / solidWeight
        : 0;
    }
    return aperture * fluidVelocity + (1 - aperture) * wallVelocity;
  }

  private measureAndStoreDivergence(): { rms: number; max: number } {
    const n = this.resolution;
    let sumSquares = 0;
    let max = 0;
    let count = 0;
    for (let k = 0; k < n; k += 1) {
      for (let j = 0; j < n; j += 1) {
        for (let i = 0; i < n; i += 1) {
          const index = this.index(i, j, k);
          if (!this.fluidMask[index]) {
            this.divergence[index] = 0;
            continue;
          }
          const fluidVolume = Math.max(this.fluidVolumeFraction[index], 1e-6);
          const rawDivergence = (
            this.faceNormalVelocity(i, j, k, 0, 1) -
            this.faceNormalVelocity(i, j, k, 0, -1) +
            this.faceNormalVelocity(i, j, k, 1, 1) -
            this.faceNormalVelocity(i, j, k, 1, -1) +
            this.faceNormalVelocity(i, j, k, 2, 1) -
            this.faceNormalVelocity(i, j, k, 2, -1)
          ) / (this.spacing * fluidVolume);
          const div = rawDivergence - this.membraneTargetDivergence[index];
          this.divergence[index] = div;
          const absolute = Math.abs(div);
          sumSquares += div * div;
          max = Math.max(max, absolute);
          count += 1;
        }
      }
    }
    return { rms: count > 0 ? Math.sqrt(sumSquares / count) : 0, max };
  }

  private projectVelocity(): void {
    this.pressure.fill(0);
    this.nextPressure.fill(0);
    const n = this.resolution;
    const h2 = this.spacing * this.spacing;
    let pressure = this.pressure;
    let next = this.nextPressure;
    for (let iteration = 0; iteration < this.projectionIterations; iteration += 1) {
      for (let k = 0; k < n; k += 1) {
        for (let j = 0; j < n; j += 1) {
          for (let i = 0; i < n; i += 1) {
            const index = this.index(i, j, k);
            if (!this.fluidMask[index]) {
              next[index] = 0;
              continue;
            }
            let weightedPressure = 0;
            let apertureSum = 0;
            const neighbors = [
              [i - 1, j, k, 0, -1], [i + 1, j, k, 0, 1],
              [i, j - 1, k, 1, -1], [i, j + 1, k, 1, 1],
              [i, j, k - 1, 2, -1], [i, j, k + 1, 2, 1]
            ] as const;
            for (const [ni, nj, nk, axis, direction] of neighbors) {
              if (!this.insideGrid(ni, nj, nk)) continue;
              const neighbor = this.index(ni, nj, nk);
              if (!this.fluidMask[neighbor]) continue;
              const aperture = this.faceAperture(i, j, k, axis, direction);
              if (aperture <= 0) continue;
              weightedPressure += pressure[neighbor] * aperture;
              apertureSum += aperture;
            }
            next[index] = apertureSum > 0
              ? (
                  weightedPressure -
                  this.divergence[index] * h2 * this.fluidVolumeFraction[index]
                ) / apertureSum
              : 0;
          }
        }
      }
      const swap = pressure;
      pressure = next;
      next = swap;
    }
    if (pressure !== this.pressure) this.pressure.set(pressure);

    for (let k = 0; k < n; k += 1) {
      for (let j = 0; j < n; j += 1) {
        for (let i = 0; i < n; i += 1) {
          const index = this.index(i, j, k);
          if (!this.fluidMask[index]) continue;
          const center = this.pressure[index];
          const weightedGradient = (axis: 0 | 1 | 2): number => {
            const minusAperture = this.faceAperture(i, j, k, axis, -1);
            const plusAperture = this.faceAperture(i, j, k, axis, 1);
            const minusCoordinates: [number, number, number] = [
              i - (axis === 0 ? 1 : 0),
              j - (axis === 1 ? 1 : 0),
              k - (axis === 2 ? 1 : 0)
            ];
            const plusCoordinates: [number, number, number] = [
              i + (axis === 0 ? 1 : 0),
              j + (axis === 1 ? 1 : 0),
              k + (axis === 2 ? 1 : 0)
            ];
            const minus = minusAperture > 0
              ? this.pressure[this.index(...minusCoordinates)]
              : center;
            const plus = plusAperture > 0
              ? this.pressure[this.index(...plusCoordinates)]
              : center;
            const denominator = minusAperture + plusAperture;
            return denominator > 0
              ? (
                  plusAperture * (plus - center) +
                  minusAperture * (center - minus)
                ) / (this.spacing * denominator)
              : 0;
          };
          this.velocityX[index] -= weightedGradient(0);
          this.velocityY[index] -= weightedGradient(1);
          this.velocityZ[index] -= weightedGradient(2);
        }
      }
    }
  }

  private boundaryReactionDiagnostic(): { pressureRms: number; reaction: CytosolVector3 } {
    const n = this.resolution;
    let pressureSq = 0;
    let samples = 0;
    let rx = 0;
    let ry = 0;
    let rz = 0;
    const faceArea = this.spacing * this.spacing;
    const directions = [
      [-1, 0, 0], [1, 0, 0], [0, -1, 0],
      [0, 1, 0], [0, 0, -1], [0, 0, 1]
    ] as const;
    for (let k = 0; k < n; k += 1) {
      for (let j = 0; j < n; j += 1) {
        for (let i = 0; i < n; i += 1) {
          const index = this.index(i, j, k);
          if (!this.fluidMask[index]) continue;
          const pressure = this.pressure[index];
          for (const [dx, dy, dz] of directions) {
            const ni = i + dx;
            const nj = j + dy;
            const nk = k + dz;
            const axis = dx !== 0 ? 0 : dy !== 0 ? 1 : 2;
            const direction = (dx + dy + dz) as -1 | 1;
            const aperture = this.faceAperture(i, j, k, axis, direction);
            const blockedFraction = 1 - aperture;
            if (blockedFraction <= 1e-12) continue;
            pressureSq += pressure * pressure * blockedFraction;
            samples += blockedFraction;
            rx -= pressure * dx * faceArea * blockedFraction;
            ry -= pressure * dy * faceArea * blockedFraction;
            rz -= pressure * dz * faceArea * blockedFraction;
          }
        }
      }
    }
    return {
      pressureRms: samples > 0 ? Math.sqrt(pressureSq / samples) : 0,
      reaction: [rx, ry, rz]
    };
  }
}

export type PassiveScalarOptions = {
  id: string;
  dimensionlessDiffusivity: number;
};

export class ConservativePassiveScalar3D {
  readonly id: string;
  readonly values: Float64Array;
  readonly dimensionlessDiffusivity: number;
  private readonly delta: Float64Array;
  private readonly remappedValues: Float64Array;
  private readonly trackedFluidMask: Uint8Array;
  private readonly trackedFluidVolumeFraction: Float32Array;
  private readonly nearestFluidDestination: Int32Array;
  private currentRemapDiagnostics: PassiveScalarDomainRemapDiagnostics = {
    remapCount: 0,
    displacedCellCount: 0,
    exposedCellCount: 0,
    faceRedistributedCellCount: 0,
    nearestFluidFallbackCellCount: 0,
    displacedDimensionlessMass: 0,
    redistributedDimensionlessMass: 0,
    absoluteMassResidual: 0,
    relativeMassResidual: 0
  };

  constructor(private readonly grid: CytosolProjectionGrid, options: PassiveScalarOptions) {
    if (!options.id) throw new RangeError("passive scalar id must be non-empty");
    if (!Number.isFinite(options.dimensionlessDiffusivity) || options.dimensionlessDiffusivity < 0) {
      throw new RangeError("dimensionless diffusivity must be finite and non-negative");
    }
    this.id = options.id;
    this.dimensionlessDiffusivity = options.dimensionlessDiffusivity;
    this.values = new Float64Array(grid.fluidMask.length);
    this.delta = new Float64Array(grid.fluidMask.length);
    this.remappedValues = new Float64Array(grid.fluidMask.length);
    this.trackedFluidMask = new Uint8Array(grid.fluidMask);
    this.trackedFluidVolumeFraction = new Float32Array(grid.fluidVolumeFraction);
    this.nearestFluidDestination = new Int32Array(grid.fluidMask.length);
  }

  initialize(initializer: (x: number, y: number, z: number) => number): void {
    this.trackedFluidMask.set(this.grid.fluidMask);
    this.trackedFluidVolumeFraction.set(this.grid.fluidVolumeFraction);
    const point = new Float32Array(3);
    for (let index = 0; index < this.values.length; index += 1) {
      if (!this.grid.fluidMask[index]) {
        this.values[index] = 0;
        continue;
      }
      this.grid.cellCenter(index, point);
      const value = initializer(point[0], point[1], point[2]);
      if (!Number.isFinite(value) || value < 0) {
        throw new RangeError("passive scalar initializer must return a finite non-negative value");
      }
      this.values[index] = value;
    }
  }

  domainRemapDiagnostics(): PassiveScalarDomainRemapDiagnostics {
    return { ...this.currentRemapDiagnostics };
  }

  totalMass(): number {
    this.synchronizeDomain();
    return this.massForVolumeFractions(this.grid.fluidVolumeFraction, this.values);
  }

  step(renderDeltaS: number): void {
    if (!Number.isFinite(renderDeltaS) || renderDeltaS < 0) {
      throw new RangeError("passive scalar delta must be finite and non-negative");
    }
    this.synchronizeDomain();
    if (renderDeltaS === 0) return;
    const h = this.grid.spacing;
    let maximumSpeed = 0;
    let minimumFluidVolumeFraction = 1;
    for (let index = 0; index < this.values.length; index += 1) {
      if (!this.grid.fluidMask[index]) continue;
      maximumSpeed = Math.max(maximumSpeed, Math.hypot(
        this.grid.velocityX[index], this.grid.velocityY[index], this.grid.velocityZ[index]
      ));
      minimumFluidVolumeFraction = Math.min(
        minimumFluidVolumeFraction,
        this.grid.fluidVolumeFraction[index]
      );
    }
    const advectiveLimit = maximumSpeed > 1e-12
      ? 0.32 * h * minimumFluidVolumeFraction / maximumSpeed
      : Number.POSITIVE_INFINITY;
    const diffusiveLimit = this.dimensionlessDiffusivity > 0
      ? 0.12 * h * h * minimumFluidVolumeFraction / this.dimensionlessDiffusivity
      : Number.POSITIVE_INFINITY;
    const stableStep = Math.max(1e-6, Math.min(advectiveLimit, diffusiveLimit, 0.05));
    const substeps = Math.max(1, Math.ceil(renderDeltaS / stableStep));
    const dt = renderDeltaS / substeps;
    for (let substep = 0; substep < substeps; substep += 1) this.conservativeSubstep(dt);
  }

  synchronizeDomain(): PassiveScalarDomainRemapDiagnostics {
    const nextMask = this.grid.fluidMask;
    const nextVolumeFraction = this.grid.fluidVolumeFraction;
    let displacedCellCount = 0;
    let exposedCellCount = 0;
    for (let index = 0; index < nextMask.length; index += 1) {
      const previous = this.trackedFluidVolumeFraction[index];
      const next = nextVolumeFraction[index];
      if (previous > next + 1e-9) displacedCellCount += 1;
      else if (next > previous + 1e-9) exposedCellCount += 1;
    }
    if (displacedCellCount === 0 && exposedCellCount === 0) {
      return this.domainRemapDiagnostics();
    }

    const cellVolume = this.grid.spacing ** 3;
    const massBefore = this.massForVolumeFractions(
      this.trackedFluidVolumeFraction,
      this.values
    );
    this.remappedValues.fill(0);
    const displaced: Array<{ index: number; mass: number }> = [];
    let displacedDimensionlessMass = 0;
    for (let index = 0; index < nextMask.length; index += 1) {
      const previousFraction = this.trackedFluidVolumeFraction[index];
      const nextFraction = nextVolumeFraction[index];
      const retainedFraction = Math.min(previousFraction, nextFraction);
      this.remappedValues[index] = this.values[index] * retainedFraction * cellVolume;
      const displacedMass = (
        this.values[index] * (previousFraction - retainedFraction) * cellVolume
      );
      if (displacedMass > 0) {
        displaced.push({ index, mass: displacedMass });
        displacedDimensionlessMass += displacedMass;
      }
    }

    let faceRedistributedCellCount = 0;
    let nearestFluidFallbackCellCount = 0;
    let redistributedDimensionlessMass = 0;
    const faceDestinations: number[] = [];
    let nearestMapReady = false;
    for (const { index: source, mass } of displaced) {
      faceDestinations.length = 0;
      this.appendFluidFaceNeighbours(source, nextMask, faceDestinations);
      if (faceDestinations.length > 0) {
        const share = mass / faceDestinations.length;
        for (const destination of faceDestinations) this.remappedValues[destination] += share;
        faceRedistributedCellCount += 1;
      } else {
        if (!nearestMapReady) {
          this.buildNearestFluidDestinationMap(nextMask);
          nearestMapReady = true;
        }
        const destination = this.nearestFluidDestination[source];
        if (destination < 0) {
          throw new Error("passive scalar cannot conserve mass because the fluid domain is empty");
        }
        this.remappedValues[destination] += mass;
        nearestFluidFallbackCellCount += 1;
      }
      redistributedDimensionlessMass += mass;
    }

    for (let index = 0; index < this.values.length; index += 1) {
      const availableVolume = nextVolumeFraction[index] * cellVolume;
      this.values[index] = availableVolume > 0
        ? this.remappedValues[index] / availableVolume
        : 0;
    }
    this.trackedFluidMask.set(nextMask);
    this.trackedFluidVolumeFraction.set(nextVolumeFraction);
    let massAfter = this.massForVolumeFractions(nextVolumeFraction, this.values);
    const correction = massBefore - massAfter;
    if (correction !== 0) {
      let correctionTarget = -1;
      let largestConcentration = -1;
      for (let index = 0; index < nextMask.length; index += 1) {
        if (nextMask[index] && this.values[index] > largestConcentration) {
          correctionTarget = index;
          largestConcentration = this.values[index];
        }
      }
      if (correctionTarget < 0) {
        if (massBefore !== 0) {
          throw new Error("passive scalar cannot apply conservation correction without fluid cells");
        }
      } else {
        const corrected = this.values[correctionTarget] + (
          correction /
          (cellVolume * nextVolumeFraction[correctionTarget])
        );
        if (corrected < -1e-12) {
          throw new Error("passive scalar moving-domain correction would create negative mass");
        }
        this.values[correctionTarget] = Math.max(0, corrected);
        massAfter = this.massForVolumeFractions(nextVolumeFraction, this.values);
      }
    }

    const residual = massAfter - massBefore;
    this.currentRemapDiagnostics = {
      remapCount: this.currentRemapDiagnostics.remapCount + 1,
      displacedCellCount,
      exposedCellCount,
      faceRedistributedCellCount,
      nearestFluidFallbackCellCount,
      displacedDimensionlessMass,
      redistributedDimensionlessMass,
      absoluteMassResidual: Math.abs(residual),
      relativeMassResidual: massBefore !== 0 ? Math.abs(residual) / Math.abs(massBefore) : Math.abs(residual)
    };
    return this.domainRemapDiagnostics();
  }

  private massForVolumeFractions(
    volumeFractions: Float32Array,
    values: Float64Array
  ): number {
    const cellVolume = this.grid.spacing ** 3;
    let sum = 0;
    for (let index = 0; index < values.length; index += 1) {
      sum += values[index] * volumeFractions[index] * cellVolume;
    }
    return sum;
  }

  private appendFluidFaceNeighbours(index: number, mask: Uint8Array, target: number[]): void {
    const n = this.grid.resolution;
    const plane = n * n;
    const k = Math.floor(index / plane);
    const remainder = index - k * plane;
    const j = Math.floor(remainder / n);
    const i = remainder - j * n;
    if (i > 0 && mask[index - 1]) target.push(index - 1);
    if (i + 1 < n && mask[index + 1]) target.push(index + 1);
    if (j > 0 && mask[index - n]) target.push(index - n);
    if (j + 1 < n && mask[index + n]) target.push(index + n);
    if (k > 0 && mask[index - plane]) target.push(index - plane);
    if (k + 1 < n && mask[index + plane]) target.push(index + plane);
  }

  private buildNearestFluidDestinationMap(mask: Uint8Array): void {
    const nearest = this.nearestFluidDestination;
    nearest.fill(-1);
    const queue = new Int32Array(mask.length);
    let head = 0;
    let tail = 0;
    for (let index = 0; index < mask.length; index += 1) {
      if (!mask[index]) continue;
      nearest[index] = index;
      queue[tail] = index;
      tail += 1;
    }
    const n = this.grid.resolution;
    const plane = n * n;
    const visit = (from: number, neighbour: number) => {
      if (nearest[neighbour] >= 0) return;
      nearest[neighbour] = nearest[from];
      queue[tail] = neighbour;
      tail += 1;
    };
    while (head < tail) {
      const index = queue[head];
      head += 1;
      const k = Math.floor(index / plane);
      const remainder = index - k * plane;
      const j = Math.floor(remainder / n);
      const i = remainder - j * n;
      if (i > 0) visit(index, index - 1);
      if (i + 1 < n) visit(index, index + 1);
      if (j > 0) visit(index, index - n);
      if (j + 1 < n) visit(index, index + n);
      if (k > 0) visit(index, index - plane);
      if (k + 1 < n) visit(index, index + plane);
    }
  }

  private conservativeSubstep(dt: number): void {
    this.delta.fill(0);
    const n = this.grid.resolution;
    const h = this.grid.spacing;
    for (let k = 0; k < n; k += 1) {
      for (let j = 0; j < n; j += 1) {
        for (let i = 0; i < n; i += 1) {
          const a = i + n * (j + n * k);
          if (!this.grid.fluidMask[a]) continue;
          if (i + 1 < n) this.transferAcrossFace(a, a + 1, 0, dt, h);
          if (j + 1 < n) this.transferAcrossFace(a, a + n, 1, dt, h);
          if (k + 1 < n) this.transferAcrossFace(a, a + n * n, 2, dt, h);
        }
      }
    }
    for (let index = 0; index < this.values.length; index += 1) {
      if (!this.grid.fluidMask[index]) {
        this.values[index] = 0;
        continue;
      }
      const next = this.values[index] + this.delta[index];
      this.values[index] = next > 0 ? next : 0;
    }
  }

  private transferAcrossFace(a: number, b: number, axis: 0 | 1 | 2, dt: number, h: number): void {
    if (!this.grid.fluidMask[b]) return;
    const aperture = axis === 0
      ? this.grid.faceOpenFractionX[a]
      : axis === 1
        ? this.grid.faceOpenFractionY[a]
        : this.grid.faceOpenFractionZ[a];
    if (aperture <= 1e-12) return;
    const velocityArray = axis === 0
      ? this.grid.velocityX
      : axis === 1
        ? this.grid.velocityY
        : this.grid.velocityZ;
    const faceVelocity = 0.5 * (velocityArray[a] + velocityArray[b]);
    const upwind = faceVelocity >= 0 ? this.values[a] : this.values[b];
    const advectiveFlux = faceVelocity * upwind;
    const diffusiveFlux = -this.dimensionlessDiffusivity * (this.values[b] - this.values[a]) / h;
    const transferPerFullCellVolume = (
      (advectiveFlux + diffusiveFlux) * aperture * dt / h
    );
    this.delta[a] -= transferPerFullCellVolume / this.grid.fluidVolumeFraction[a];
    this.delta[b] += transferPerFullCellVolume / this.grid.fluidVolumeFraction[b];
  }
}
