// Reference-space radial boundary shared by the rendered plasma membrane and
// the dimensionless cytosol solver.
//
// The global contact map is inverted before rasterization, so this field stores
// only the current non-affine residual relative to the canonical rest surface.
// It can represent smooth, star-shaped surface changes. Folds with multiple ray
// intersections, neck closure, budding and topology changes are deliberately
// outside this representation.

import {
  inverseVolumePreservingPoint,
  type CytosolProjectionDeformation
} from "./cytosolNumerics";
import {
  membraneRestRadiusAlongDirection,
  type MembraneSim
} from "./membrane_mechanics";

export type ReferenceMembraneBoundaryDiagnostics = {
  angularBinCount: number;
  sampledVertexCount: number;
  emptyBinCountBeforeFill: number;
  minimumResidualFactor: number;
  maximumResidualFactor: number;
  maximumAbsoluteResidual: number;
  localStarShapedDeformationDetected: boolean;
  affineComponentRemoved: boolean;
  biologicalMechanicsClaim: false;
  topologyChangeSupported: false;
};

export type ReferenceMembraneRadialBoundaryOptions = {
  longitudeBins?: number;
  latitudeBins?: number;
};

const DEFAULT_LONGITUDE_BINS = 32;
const DEFAULT_LATITUDE_BINS = 16;
const RESIDUAL_DETECTION_EPSILON = 1e-5;

function validateBinCount(value: number, label: string, minimum: number): void {
  if (!Number.isInteger(value) || value < minimum || value > 256) {
    throw new RangeError(`${label} must be an integer in [${minimum}, 256]`);
  }
}

export class ReferenceMembraneRadialBoundary {
  readonly longitudeBins: number;
  readonly latitudeBins: number;

  private readonly residualFactors: Float32Array;
  private readonly sampleCounts: Uint16Array;
  private readonly referencePoint = new Float32Array(3);
  private sim: MembraneSim | null = null;
  private currentDiagnostics: ReferenceMembraneBoundaryDiagnostics;

  constructor(options: ReferenceMembraneRadialBoundaryOptions = {}) {
    const longitudeBins = options.longitudeBins ?? DEFAULT_LONGITUDE_BINS;
    const latitudeBins = options.latitudeBins ?? DEFAULT_LATITUDE_BINS;
    validateBinCount(longitudeBins, "membrane boundary longitude bin count", 8);
    validateBinCount(latitudeBins, "membrane boundary latitude bin count", 4);
    this.longitudeBins = longitudeBins;
    this.latitudeBins = latitudeBins;
    this.residualFactors = new Float32Array(longitudeBins * latitudeBins);
    this.residualFactors.fill(1);
    this.sampleCounts = new Uint16Array(this.residualFactors.length);
    this.currentDiagnostics = {
      angularBinCount: this.residualFactors.length,
      sampledVertexCount: 0,
      emptyBinCountBeforeFill: this.residualFactors.length,
      minimumResidualFactor: 1,
      maximumResidualFactor: 1,
      maximumAbsoluteResidual: 0,
      localStarShapedDeformationDetected: false,
      affineComponentRemoved: false,
      biologicalMechanicsClaim: false,
      topologyChangeSupported: false
    };
  }

  update(
    sim: MembraneSim,
    deformation: CytosolProjectionDeformation | null
  ): void {
    this.sim = sim;
    this.residualFactors.fill(0);
    this.sampleCounts.fill(0);

    for (let vertex = 0; vertex < sim.n; vertex += 1) {
      const offset = vertex * 3;
      inverseVolumePreservingPoint(
        sim.pos[offset],
        sim.pos[offset + 1],
        sim.pos[offset + 2],
        deformation,
        this.referencePoint
      );
      const x = this.referencePoint[0];
      const y = this.referencePoint[1];
      const z = this.referencePoint[2];
      const radius = Math.hypot(x, y, z);
      if (!Number.isFinite(radius) || radius <= 0) {
        throw new RangeError("current membrane vertex must have a finite positive radius");
      }
      const nx = x / radius;
      const ny = y / radius;
      const nz = z / radius;
      const restRadius = membraneRestRadiusAlongDirection(sim, nx, ny, nz);
      const residual = radius / restRadius;
      if (!Number.isFinite(residual) || residual <= 0) {
        throw new RangeError("membrane residual radius factor must be finite and positive");
      }
      const index = this.binIndex(nx, ny, nz);
      this.residualFactors[index] += residual;
      this.sampleCounts[index] += 1;
    }

    let emptyBinCount = 0;
    for (let index = 0; index < this.residualFactors.length; index += 1) {
      const count = this.sampleCounts[index];
      if (count > 0) this.residualFactors[index] /= count;
      else emptyBinCount += 1;
    }
    this.fillEmptyBins();

    let minimumResidualFactor = Infinity;
    let maximumResidualFactor = 0;
    let maximumAbsoluteResidual = 0;
    for (const factor of this.residualFactors) {
      minimumResidualFactor = Math.min(minimumResidualFactor, factor);
      maximumResidualFactor = Math.max(maximumResidualFactor, factor);
      maximumAbsoluteResidual = Math.max(maximumAbsoluteResidual, Math.abs(factor - 1));
    }
    this.currentDiagnostics = {
      angularBinCount: this.residualFactors.length,
      sampledVertexCount: sim.n,
      emptyBinCountBeforeFill: emptyBinCount,
      minimumResidualFactor,
      maximumResidualFactor,
      maximumAbsoluteResidual,
      localStarShapedDeformationDetected:
        maximumAbsoluteResidual > RESIDUAL_DETECTION_EPSILON,
      affineComponentRemoved: deformation !== null,
      biologicalMechanicsClaim: false,
      topologyChangeSupported: false
    };
  }

  readonly radiusAtDirection = (x: number, y: number, z: number): number => {
    const sim = this.sim;
    if (!sim) throw new Error("membrane fluid boundary must be updated before sampling");
    const length = Math.hypot(x, y, z);
    if (!Number.isFinite(length) || length <= 1e-12) {
      throw new RangeError("membrane boundary direction must be finite and non-zero");
    }
    const nx = x / length;
    const ny = y / length;
    const nz = z / length;
    return membraneRestRadiusAlongDirection(sim, nx, ny, nz)
      * this.interpolateResidual(nx, ny, nz);
  };

  diagnostics(): ReferenceMembraneBoundaryDiagnostics {
    return { ...this.currentDiagnostics };
  }

  private binIndex(nx: number, ny: number, nz: number): number {
    const latitude = Math.acos(Math.max(-1, Math.min(1, ny)));
    const longitude = Math.atan2(nz, nx) + Math.PI;
    const latitudeIndex = Math.min(
      this.latitudeBins - 1,
      Math.floor((latitude / Math.PI) * this.latitudeBins)
    );
    const longitudeIndex = Math.min(
      this.longitudeBins - 1,
      Math.floor((longitude / (2 * Math.PI)) * this.longitudeBins)
    );
    return latitudeIndex * this.longitudeBins + longitudeIndex;
  }

  private fillEmptyBins(): void {
    const maximumSearchRadius = Math.max(this.longitudeBins, this.latitudeBins);
    for (let latitude = 0; latitude < this.latitudeBins; latitude += 1) {
      for (let longitude = 0; longitude < this.longitudeBins; longitude += 1) {
        const index = latitude * this.longitudeBins + longitude;
        if (this.sampleCounts[index] > 0) continue;
        let resolved = false;
        for (let radius = 1; radius <= maximumSearchRadius && !resolved; radius += 1) {
          let sum = 0;
          let count = 0;
          for (let latitudeOffset = -radius; latitudeOffset <= radius; latitudeOffset += 1) {
            for (let longitudeOffset = -radius; longitudeOffset <= radius; longitudeOffset += 1) {
              if (
                Math.abs(latitudeOffset) !== radius
                && Math.abs(longitudeOffset) !== radius
              ) continue;
              const candidateLatitude = latitude + latitudeOffset;
              if (candidateLatitude < 0 || candidateLatitude >= this.latitudeBins) continue;
              const candidateLongitude =
                (longitude + longitudeOffset + this.longitudeBins) % this.longitudeBins;
              const candidateIndex =
                candidateLatitude * this.longitudeBins + candidateLongitude;
              if (this.sampleCounts[candidateIndex] === 0) continue;
              sum += this.residualFactors[candidateIndex];
              count += 1;
            }
          }
          if (count > 0) {
            this.residualFactors[index] = sum / count;
            resolved = true;
          }
        }
        if (!resolved) this.residualFactors[index] = 1;
      }
    }
  }

  private interpolateResidual(nx: number, ny: number, nz: number): number {
    const latitude = Math.acos(Math.max(-1, Math.min(1, ny)));
    const longitude = Math.atan2(nz, nx) + Math.PI;
    const latitudeCoordinate =
      (latitude / Math.PI) * this.latitudeBins - 0.5;
    const longitudeCoordinate =
      (longitude / (2 * Math.PI)) * this.longitudeBins - 0.5;
    const latitude0 = Math.max(
      0,
      Math.min(this.latitudeBins - 1, Math.floor(latitudeCoordinate))
    );
    const latitude1 = Math.max(
      0,
      Math.min(this.latitudeBins - 1, latitude0 + 1)
    );
    const longitudeFloor = Math.floor(longitudeCoordinate);
    const longitude0 =
      (longitudeFloor + this.longitudeBins) % this.longitudeBins;
    const longitude1 = (longitude0 + 1) % this.longitudeBins;
    const latitudeWeight = Math.max(
      0,
      Math.min(1, latitudeCoordinate - Math.floor(latitudeCoordinate))
    );
    const longitudeWeight = Math.max(
      0,
      Math.min(1, longitudeCoordinate - longitudeFloor)
    );
    const f00 = this.residualFactors[
      latitude0 * this.longitudeBins + longitude0
    ];
    const f01 = this.residualFactors[
      latitude0 * this.longitudeBins + longitude1
    ];
    const f10 = this.residualFactors[
      latitude1 * this.longitudeBins + longitude0
    ];
    const f11 = this.residualFactors[
      latitude1 * this.longitudeBins + longitude1
    ];
    const upper = f00 + (f01 - f00) * longitudeWeight;
    const lower = f10 + (f11 - f10) * longitudeWeight;
    return upper + (lower - upper) * latitudeWeight;
  }
}
