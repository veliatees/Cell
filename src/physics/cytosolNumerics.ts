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

export type CytosolObstacle =
  | CytosolSphereObstacle
  | CytosolEllipsoidObstacle
  | CytosolCapsuleObstacle;

type StoredObstacle = CytosolObstacle & {
  resolvedVelocity: CytosolVector3;
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
  version: "dimensionless_moving_boundary_projection_v2",
  numericalMethod: "cell_centered_eulerian_pressure_projection",
  movingObstacleShapes: ["sphere", "ellipsoid", "capsule"] as const,
  passiveScalarMethod: "finite_volume_advection_diffusion_with_conservative_moving_domain_remap",
  movingDomainRemap: "face_neighbor_redistribution_with_deterministic_nearest_fluid_fallback",
  rendererVelocityUnits: "world_units_per_render_second",
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
  return obstacle.radius + obstacle.halfLength;
}

function validateObstacle(obstacle: CytosolObstacle): void {
  if (!obstacle.id) throw new RangeError("cytosol obstacle id must be non-empty");
  finiteVector(obstacle.center, `${obstacle.id} center`);
  if (obstacle.velocity) finiteVector(obstacle.velocity, `${obstacle.id} velocity`);
  normalizedQuaternion(obstacle.orientation);
  if (obstacle.kind === "sphere") {
    if (!Number.isFinite(obstacle.radius) || obstacle.radius <= 0) {
      throw new RangeError(`${obstacle.id} sphere radius must be positive`);
    }
  } else if (obstacle.kind === "ellipsoid") {
    finiteVector(obstacle.radii, `${obstacle.id} radii`);
    if (obstacle.radii.some((value) => value <= 0)) {
      throw new RangeError(`${obstacle.id} ellipsoid radii must be positive`);
    }
  } else if (
    !Number.isFinite(obstacle.radius) || obstacle.radius <= 0 ||
    !Number.isFinite(obstacle.halfLength) || obstacle.halfLength < 0
  ) {
    throw new RangeError(`${obstacle.id} capsule dimensions are invalid`);
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
  const closestY = Math.max(-obstacle.halfLength, Math.min(obstacle.halfLength, ly));
  return lx * lx + (ly - closestY) ** 2 + lz * lz <= (obstacle.radius + padding) ** 2;
}

export class DynamicCytosolObstacleField {
  readonly cellSize: number;
  private obstacles: StoredObstacle[] = [];
  private readonly buckets = new Map<string, number[]>();
  private readonly previousCenters = new Map<string, CytosolVector3>();

  constructor(cellSize: number) {
    if (!Number.isFinite(cellSize) || cellSize <= 0) {
      throw new RangeError("cytosol obstacle hash cell size must be positive");
    }
    this.cellSize = cellSize;
  }

  get count(): number {
    return this.obstacles.length;
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
      const resolvedVelocity: CytosolVector3 = obstacle.velocity ?? (
        previous && deltaS > 1e-9
          ? [
              (obstacle.center[0] - previous[0]) / deltaS,
              (obstacle.center[1] - previous[1]) / deltaS,
              (obstacle.center[2] - previous[2]) / deltaS
            ]
          : ZERO_VECTOR
      );
      next.push({
        ...obstacle,
        orientation: normalizedQuaternion(obstacle.orientation),
        resolvedVelocity,
        boundingRadius: obstacleBoundingRadius(obstacle)
      });
      this.previousCenters.set(obstacle.id, [...obstacle.center]);
    }
    for (const id of this.previousCenters.keys()) {
      if (!ids.has(id)) this.previousCenters.delete(id);
    }
    this.obstacles = next;
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
    target[offset] = obstacle.resolvedVelocity[0];
    target[offset + 1] = obstacle.resolvedVelocity[1];
    target[offset + 2] = obstacle.resolvedVelocity[2];
    return true;
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

  private findContaining(x: number, y: number, z: number, padding: number): StoredObstacle | null {
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
  readonly velocityX: Float32Array;
  readonly velocityY: Float32Array;
  readonly velocityZ: Float32Array;

  private readonly radiusAtDirection: CytosolProjectionOptions["radiusAtDirection"];
  private readonly safetyFraction: number;
  private readonly projectionIterations: number;
  private readonly pressure: Float32Array;
  private readonly nextPressure: Float32Array;
  private readonly divergence: Float32Array;
  private readonly modes: ProjectionMode[];
  private elapsedRenderS = 0;
  private currentDiagnostics: CytosolProjectionDiagnostics = {
    fluidCellCount: 0,
    solidCellCount: 0,
    obstacleCount: 0,
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
    this.velocityX = new Float32Array(count);
    this.velocityY = new Float32Array(count);
    this.velocityZ = new Float32Array(count);
    this.pressure = new Float32Array(count);
    this.nextPressure = new Float32Array(count);
    this.divergence = new Float32Array(count);

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
    this.rebuildDomainAndTentativeVelocity(deformation, obstacles);
    const before = this.measureAndStoreDivergence();
    this.projectVelocity();
    const after = this.measureAndStoreDivergence();
    const boundary = this.boundaryReactionDiagnostic();
    const fluidCellCount = this.fluidMask.reduce((sum, value) => sum + value, 0);
    this.currentDiagnostics = {
      fluidCellCount,
      solidCellCount: this.fluidMask.length - fluidCellCount,
      obstacleCount: obstacles?.count ?? 0,
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

  private index(i: number, j: number, k: number): number {
    return i + this.resolution * (j + this.resolution * k);
  }

  private insideGrid(i: number, j: number, k: number): boolean {
    return i >= 0 && j >= 0 && k >= 0 && i < this.resolution && j < this.resolution && k < this.resolution;
  }

  private rebuildDomainAndTentativeVelocity(
    deformation: CytosolProjectionDeformation | null,
    obstacles?: DynamicCytosolObstacleField
  ): void {
    const point = new Float32Array(3);
    const reference = new Float32Array(3);
    const solidVelocity = new Float32Array(3);
    for (let index = 0; index < this.fluidMask.length; index += 1) {
      this.cellCenter(index, point);
      inverseVolumePreservingPoint(point[0], point[1], point[2], deformation, reference);
      const length = Math.hypot(reference[0], reference[1], reference[2]);
      let insideMembrane = length <= 1e-12;
      if (!insideMembrane) {
        const radius = this.radiusAtDirection(reference[0] / length, reference[1] / length, reference[2] / length);
        if (!Number.isFinite(radius) || radius <= 0) {
          throw new RangeError("cytosol domain radius must be finite and positive");
        }
        insideMembrane = length <= radius * this.safetyFraction;
      }
      const insideObstacle = insideMembrane && Boolean(obstacles?.solidVelocityAt(
        point[0], point[1], point[2], solidVelocity
      ));
      this.fluidMask[index] = insideMembrane && !insideObstacle ? 1 : 0;
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
  }

  private neighborVelocity(
    array: Float32Array,
    i: number,
    j: number,
    k: number,
    fallback: number
  ): number {
    if (!this.insideGrid(i, j, k)) return fallback;
    return array[this.index(i, j, k)];
  }

  private measureAndStoreDivergence(): { rms: number; max: number } {
    const n = this.resolution;
    const inverseTwoH = 1 / (2 * this.spacing);
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
          const div = (
            this.neighborVelocity(this.velocityX, i + 1, j, k, 0) -
            this.neighborVelocity(this.velocityX, i - 1, j, k, 0) +
            this.neighborVelocity(this.velocityY, i, j + 1, k, 0) -
            this.neighborVelocity(this.velocityY, i, j - 1, k, 0) +
            this.neighborVelocity(this.velocityZ, i, j, k + 1, 0) -
            this.neighborVelocity(this.velocityZ, i, j, k - 1, 0)
          ) * inverseTwoH;
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
            let sum = 0;
            let count = 0;
            const neighbors = [
              [i - 1, j, k], [i + 1, j, k],
              [i, j - 1, k], [i, j + 1, k],
              [i, j, k - 1], [i, j, k + 1]
            ] as const;
            for (const [ni, nj, nk] of neighbors) {
              if (!this.insideGrid(ni, nj, nk)) continue;
              const neighbor = this.index(ni, nj, nk);
              if (!this.fluidMask[neighbor]) continue;
              sum += pressure[neighbor];
              count += 1;
            }
            next[index] = count > 0 ? (sum - this.divergence[index] * h2) / count : 0;
          }
        }
      }
      const swap = pressure;
      pressure = next;
      next = swap;
    }
    if (pressure !== this.pressure) this.pressure.set(pressure);

    const inverseTwoH = 1 / (2 * this.spacing);
    for (let k = 0; k < n; k += 1) {
      for (let j = 0; j < n; j += 1) {
        for (let i = 0; i < n; i += 1) {
          const index = this.index(i, j, k);
          if (!this.fluidMask[index]) continue;
          const center = this.pressure[index];
          const pXm = this.fluidPressure(i - 1, j, k, center);
          const pXp = this.fluidPressure(i + 1, j, k, center);
          const pYm = this.fluidPressure(i, j - 1, k, center);
          const pYp = this.fluidPressure(i, j + 1, k, center);
          const pZm = this.fluidPressure(i, j, k - 1, center);
          const pZp = this.fluidPressure(i, j, k + 1, center);
          this.velocityX[index] -= (pXp - pXm) * inverseTwoH;
          this.velocityY[index] -= (pYp - pYm) * inverseTwoH;
          this.velocityZ[index] -= (pZp - pZm) * inverseTwoH;
        }
      }
    }
  }

  private fluidPressure(i: number, j: number, k: number, fallback: number): number {
    if (!this.insideGrid(i, j, k)) return fallback;
    const index = this.index(i, j, k);
    return this.fluidMask[index] ? this.pressure[index] : fallback;
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
            const neighborIsFluid = this.insideGrid(ni, nj, nk) && this.fluidMask[this.index(ni, nj, nk)] === 1;
            if (neighborIsFluid) continue;
            pressureSq += pressure * pressure;
            samples += 1;
            rx -= pressure * dx * faceArea;
            ry -= pressure * dy * faceArea;
            rz -= pressure * dz * faceArea;
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
    this.nearestFluidDestination = new Int32Array(grid.fluidMask.length);
  }

  initialize(initializer: (x: number, y: number, z: number) => number): void {
    this.trackedFluidMask.set(this.grid.fluidMask);
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
    return this.massForMask(this.grid.fluidMask, this.values);
  }

  step(renderDeltaS: number): void {
    if (!Number.isFinite(renderDeltaS) || renderDeltaS < 0) {
      throw new RangeError("passive scalar delta must be finite and non-negative");
    }
    this.synchronizeDomain();
    if (renderDeltaS === 0) return;
    const h = this.grid.spacing;
    let maximumSpeed = 0;
    for (let index = 0; index < this.values.length; index += 1) {
      if (!this.grid.fluidMask[index]) continue;
      maximumSpeed = Math.max(maximumSpeed, Math.hypot(
        this.grid.velocityX[index], this.grid.velocityY[index], this.grid.velocityZ[index]
      ));
    }
    const advectiveLimit = maximumSpeed > 1e-12 ? 0.32 * h / maximumSpeed : Number.POSITIVE_INFINITY;
    const diffusiveLimit = this.dimensionlessDiffusivity > 0
      ? 0.12 * h * h / this.dimensionlessDiffusivity
      : Number.POSITIVE_INFINITY;
    const stableStep = Math.max(1e-6, Math.min(advectiveLimit, diffusiveLimit, 0.05));
    const substeps = Math.max(1, Math.ceil(renderDeltaS / stableStep));
    const dt = renderDeltaS / substeps;
    for (let substep = 0; substep < substeps; substep += 1) this.conservativeSubstep(dt);
  }

  synchronizeDomain(): PassiveScalarDomainRemapDiagnostics {
    const nextMask = this.grid.fluidMask;
    let displacedCellCount = 0;
    let exposedCellCount = 0;
    for (let index = 0; index < nextMask.length; index += 1) {
      if (this.trackedFluidMask[index] && !nextMask[index]) displacedCellCount += 1;
      else if (!this.trackedFluidMask[index] && nextMask[index]) exposedCellCount += 1;
    }
    if (displacedCellCount === 0 && exposedCellCount === 0) {
      return this.domainRemapDiagnostics();
    }

    const cellVolume = this.grid.spacing ** 3;
    const massBefore = this.massForMask(this.trackedFluidMask, this.values);
    this.remappedValues.fill(0);
    const displacedIndices: number[] = [];
    let displacedDimensionlessMass = 0;
    for (let index = 0; index < nextMask.length; index += 1) {
      if (this.trackedFluidMask[index] && nextMask[index]) {
        this.remappedValues[index] = this.values[index];
      } else if (this.trackedFluidMask[index] && !nextMask[index]) {
        displacedIndices.push(index);
        displacedDimensionlessMass += this.values[index] * cellVolume;
      }
    }

    let faceRedistributedCellCount = 0;
    let nearestFluidFallbackCellCount = 0;
    let redistributedDimensionlessMass = 0;
    const faceDestinations: number[] = [];
    let nearestMapReady = false;
    for (const source of displacedIndices) {
      const concentration = this.values[source];
      if (concentration <= 0) continue;
      faceDestinations.length = 0;
      this.appendFluidFaceNeighbours(source, nextMask, faceDestinations);
      if (faceDestinations.length > 0) {
        const share = concentration / faceDestinations.length;
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
        this.remappedValues[destination] += concentration;
        nearestFluidFallbackCellCount += 1;
      }
      redistributedDimensionlessMass += concentration * cellVolume;
    }

    this.values.set(this.remappedValues);
    this.trackedFluidMask.set(nextMask);
    let massAfter = this.massForMask(nextMask, this.values);
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
        const corrected = this.values[correctionTarget] + correction / cellVolume;
        if (corrected < -1e-12) {
          throw new Error("passive scalar moving-domain correction would create negative mass");
        }
        this.values[correctionTarget] = Math.max(0, corrected);
        massAfter = this.massForMask(nextMask, this.values);
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

  private massForMask(mask: Uint8Array, values: Float64Array): number {
    const cellVolume = this.grid.spacing ** 3;
    let sum = 0;
    for (let index = 0; index < values.length; index += 1) {
      if (mask[index]) sum += values[index] * cellVolume;
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
    const velocityArray = axis === 0
      ? this.grid.velocityX
      : axis === 1
        ? this.grid.velocityY
        : this.grid.velocityZ;
    const faceVelocity = 0.5 * (velocityArray[a] + velocityArray[b]);
    const upwind = faceVelocity >= 0 ? this.values[a] : this.values[b];
    const advectiveFlux = faceVelocity * upwind;
    const diffusiveFlux = -this.dimensionlessDiffusivity * (this.values[b] - this.values[a]) / h;
    const transfer = (advectiveFlux + diffusiveFlux) * dt / h;
    this.delta[a] -= transfer;
    this.delta[b] += transfer;
  }
}
