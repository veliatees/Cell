// Qualitative intracellular transport field for the whole-cell renderer.
//
// The points are sparse tracers, not water molecules, concentrations or a
// calibrated primary-human-hepatocyte velocity field. Their seeded rotational
// modes are divergence-free in the unbounded domain and are used only to make
// a moving aqueous phase legible. Numerical reaction coupling remains owned by
// the Python evidence gate.

export type IntracellularFluidDeformation = {
  normal: readonly [number, number, number];
  axialScale: number;
};

export type IntracellularFluidCollision = (
  x: number,
  y: number,
  z: number,
  tracerRadius: number
) => boolean;

export type IntracellularFluidFieldOptions = {
  seed: number;
  initialPositions: Float32Array;
  radiusAtDirection: (x: number, y: number, z: number) => number;
  safetyFraction?: number;
  tracerRadius?: number;
  modeCount?: number;
};

type FlowMode = {
  centerX: number;
  centerY: number;
  centerZ: number;
  axisX: number;
  axisY: number;
  axisZ: number;
  influenceRadius: number;
  signedRate: number;
  modulationDepth: number;
  temporalRate: number;
  phase: number;
};

export const INTRACELLULAR_FLUID_VISUAL_CONTRACT = Object.freeze({
  representation: "seeded_sparse_transport_tracers",
  materialClass: "aqueous_mobile_phase_coupled_to_a_poroviscoelastic_scaffold",
  biologicalVelocityClaim: false,
  concentrationClaim: false,
  moleculeCountClaim: false,
  reactionRateCoupling: false,
  membraneMapping: "volume_preserving_affine_contact_map"
});

const DEFAULT_SAFETY_FRACTION = 0.9;
const DEFAULT_TRACER_RADIUS = 0.045;
const DEFAULT_MODE_COUNT = 7;
// Renderer-time motion coefficient. It has no micrometre/second or biological
// time interpretation and must not be copied into the quantitative engine.
const VISUAL_ROTATION_RATE_PER_RENDER_SECOND = 0.024;

function seededRandom(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state = (Math.imul(1_664_525, state) + 1_013_904_223) >>> 0;
    return state / 4_294_967_296;
  };
}

function normalizedRandomDirection(random: () => number): [number, number, number] {
  for (let attempt = 0; attempt < 32; attempt += 1) {
    const x = random() * 2 - 1;
    const y = random() * 2 - 1;
    const z = random() * 2 - 1;
    const length = Math.hypot(x, y, z);
    if (length > 1e-6 && length <= 1) return [x / length, y / length, z / length];
  }
  return [1, 0, 0];
}

export function applyVolumePreservingFluidDeformation(
  x: number,
  y: number,
  z: number,
  deformation: IntracellularFluidDeformation | null,
  target: Float32Array,
  offset = 0
): void {
  if (!deformation) {
    target[offset] = x;
    target[offset + 1] = y;
    target[offset + 2] = z;
    return;
  }
  const [rawX, rawY, rawZ] = deformation.normal;
  const normalLength = Math.hypot(rawX, rawY, rawZ);
  if (!Number.isFinite(normalLength) || normalLength <= 1e-12) {
    throw new RangeError("fluid deformation normal must be finite and non-zero");
  }
  if (!Number.isFinite(deformation.axialScale) || deformation.axialScale <= 0) {
    throw new RangeError("fluid deformation axial scale must be finite and positive");
  }
  const nx = rawX / normalLength;
  const ny = rawY / normalLength;
  const nz = rawZ / normalLength;
  const axial = deformation.axialScale;
  const tangential = 1 / Math.sqrt(axial);
  const projection = x * nx + y * ny + z * nz;
  const correction = (axial - tangential) * projection;
  target[offset] = tangential * x + correction * nx;
  target[offset + 1] = tangential * y + correction * ny;
  target[offset + 2] = tangential * z + correction * nz;
}

export function volumePreservingFluidMapDeterminant(axialScale: number): number {
  if (!Number.isFinite(axialScale) || axialScale <= 0) {
    throw new RangeError("fluid deformation axial scale must be finite and positive");
  }
  const tangential = 1 / Math.sqrt(axialScale);
  return axialScale * tangential * tangential;
}

export function createSeededSphereTracerPositions(
  count: number,
  radius: number,
  seed: number
): Float32Array {
  if (!Number.isInteger(count) || count < 0) throw new RangeError("tracer count must be a non-negative integer");
  if (!Number.isFinite(radius) || radius <= 0) throw new RangeError("tracer radius must be finite and positive");
  const random = seededRandom(seed);
  const positions = new Float32Array(count * 3);
  for (let index = 0; index < count; index += 1) {
    const [x, y, z] = normalizedRandomDirection(random);
    const distance = Math.cbrt(random()) * radius;
    positions[index * 3] = x * distance;
    positions[index * 3 + 1] = y * distance;
    positions[index * 3 + 2] = z * distance;
  }
  return positions;
}

export class IntracellularFluidField {
  readonly count: number;
  readonly referencePositions: Float32Array;
  readonly positions: Float32Array;
  readonly previousPositions: Float32Array;

  private readonly radiusAtDirection: IntracellularFluidFieldOptions["radiusAtDirection"];
  private readonly safetyFraction: number;
  private readonly tracerRadius: number;
  private readonly modes: FlowMode[];
  private readonly domainScale: number;
  private elapsedRenderS = 0;

  constructor(options: IntracellularFluidFieldOptions) {
    if (options.initialPositions.length % 3 !== 0) {
      throw new RangeError("fluid tracer positions must contain xyz triples");
    }
    const safetyFraction = options.safetyFraction ?? DEFAULT_SAFETY_FRACTION;
    if (!Number.isFinite(safetyFraction) || safetyFraction <= 0 || safetyFraction > 1) {
      throw new RangeError("fluid safety fraction must be in (0, 1]");
    }
    const tracerRadius = options.tracerRadius ?? DEFAULT_TRACER_RADIUS;
    if (!Number.isFinite(tracerRadius) || tracerRadius < 0) {
      throw new RangeError("fluid tracer radius must be finite and non-negative");
    }
    const modeCount = options.modeCount ?? DEFAULT_MODE_COUNT;
    if (!Number.isInteger(modeCount) || modeCount <= 0) {
      throw new RangeError("fluid mode count must be a positive integer");
    }

    this.count = options.initialPositions.length / 3;
    this.referencePositions = new Float32Array(options.initialPositions);
    this.positions = new Float32Array(options.initialPositions);
    this.previousPositions = new Float32Array(options.initialPositions);
    this.radiusAtDirection = options.radiusAtDirection;
    this.safetyFraction = safetyFraction;
    this.tracerRadius = tracerRadius;

    let maximumRadius = 0;
    for (let index = 0; index < this.referencePositions.length; index += 3) {
      maximumRadius = Math.max(
        maximumRadius,
        Math.hypot(
          this.referencePositions[index],
          this.referencePositions[index + 1],
          this.referencePositions[index + 2]
        )
      );
    }
    this.domainScale = Math.max(maximumRadius / Math.max(safetyFraction, 1e-6), 1);

    const random = seededRandom(options.seed);
    this.modes = Array.from({ length: modeCount }, () => {
      const [centerX, centerY, centerZ] = normalizedRandomDirection(random);
      const [axisX, axisY, axisZ] = normalizedRandomDirection(random);
      return {
        centerX: centerX * this.domainScale * random() * 0.38,
        centerY: centerY * this.domainScale * random() * 0.38,
        centerZ: centerZ * this.domainScale * random() * 0.38,
        axisX,
        axisY,
        axisZ,
        influenceRadius: this.domainScale * (0.42 + random() * 0.45),
        signedRate: (random() < 0.5 ? -1 : 1) * VISUAL_ROTATION_RATE_PER_RENDER_SECOND * (0.55 + random() * 0.9),
        modulationDepth: 0.18 + random() * 0.28,
        temporalRate: 0.11 + random() * 0.31,
        phase: random() * Math.PI * 2
      };
    });
    this.projectEveryReferencePointInside();
  }

  step(
    realDeltaS: number,
    deformation: IntracellularFluidDeformation | null,
    collides?: IntracellularFluidCollision
  ): void {
    if (!Number.isFinite(realDeltaS) || realDeltaS < 0) {
      throw new RangeError("fluid renderer delta must be finite and non-negative");
    }
    this.previousPositions.set(this.positions);
    if (realDeltaS === 0) {
      this.writeDeformedPositions(deformation);
      this.previousPositions.set(this.positions);
      return;
    }

    const dt = Math.min(realDeltaS, 0.05);
    this.elapsedRenderS += dt;
    const candidate = new Float32Array(3);
    const renderedCandidate = new Float32Array(3);
    for (let index = 0; index < this.referencePositions.length; index += 3) {
      const x = this.referencePositions[index];
      const y = this.referencePositions[index + 1];
      const z = this.referencePositions[index + 2];
      let velocityX = 0;
      let velocityY = 0;
      let velocityZ = 0;
      for (const mode of this.modes) {
        const rx = x - mode.centerX;
        const ry = y - mode.centerY;
        const rz = z - mode.centerZ;
        const inverseInfluenceSq = 1 / (mode.influenceRadius * mode.influenceRadius);
        const weight = Math.exp(-(rx * rx + ry * ry + rz * rz) * inverseInfluenceSq);
        const modulation = 1 + mode.modulationDepth * Math.sin(mode.phase + this.elapsedRenderS * mode.temporalRate);
        const strength = mode.signedRate * modulation * weight;
        velocityX += (mode.axisY * rz - mode.axisZ * ry) * strength;
        velocityY += (mode.axisZ * rx - mode.axisX * rz) * strength;
        velocityZ += (mode.axisX * ry - mode.axisY * rx) * strength;
      }
      const trialX = x + velocityX * dt;
      const trialY = y + velocityY * dt;
      const trialZ = z + velocityZ * dt;
      candidate[0] = trialX;
      candidate[1] = trialY;
      candidate[2] = trialZ;
      this.projectPointInside(candidate, 0);
      applyVolumePreservingFluidDeformation(
        candidate[0], candidate[1], candidate[2], deformation, renderedCandidate
      );
      if (!collides?.(
        renderedCandidate[0], renderedCandidate[1], renderedCandidate[2], this.tracerRadius
      )) {
        this.referencePositions[index] = candidate[0];
        this.referencePositions[index + 1] = candidate[1];
        this.referencePositions[index + 2] = candidate[2];
      }
    }
    this.writeDeformedPositions(deformation);
  }

  synchronizeDeformation(deformation: IntracellularFluidDeformation | null): void {
    this.writeDeformedPositions(deformation);
    this.previousPositions.set(this.positions);
  }

  private writeDeformedPositions(deformation: IntracellularFluidDeformation | null): void {
    for (let index = 0; index < this.referencePositions.length; index += 3) {
      applyVolumePreservingFluidDeformation(
        this.referencePositions[index],
        this.referencePositions[index + 1],
        this.referencePositions[index + 2],
        deformation,
        this.positions,
        index
      );
    }
  }

  private projectEveryReferencePointInside(): void {
    for (let index = 0; index < this.referencePositions.length; index += 3) {
      this.projectPointInside(this.referencePositions, index);
    }
    this.positions.set(this.referencePositions);
    this.previousPositions.set(this.referencePositions);
  }

  private projectPointInside(points: Float32Array, index: number): void {
    const x = points[index];
    const y = points[index + 1];
    const z = points[index + 2];
    const length = Math.hypot(x, y, z);
    if (length <= 1e-12) return;
    const localRadius = this.radiusAtDirection(x / length, y / length, z / length);
    if (!Number.isFinite(localRadius) || localRadius <= 0) {
      throw new RangeError("fluid domain radius must be finite and positive");
    }
    const maximum = localRadius * this.safetyFraction;
    if (length <= maximum) return;
    const scale = maximum / length;
    points[index] = x * scale;
    points[index + 1] = y * scale;
    points[index + 2] = z * scale;
  }
}
