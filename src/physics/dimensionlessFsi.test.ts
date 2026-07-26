import { describe, expect, it } from "vitest";

import {
  DIMENSIONLESS_FSI_CONTRACT,
  proposeDimensionlessPressureResponse
} from "./dimensionlessFsi";
import { WatertightTriangleMeshBoundary } from "./watertightMeshBoundary";

const CUBE = new WatertightTriangleMeshBoundary(
  [
    -1, -1, -1,
    1, -1, -1,
    1, 1, -1,
    -1, 1, -1,
    -1, -1, 1,
    1, -1, 1,
    1, 1, 1,
    -1, 1, 1
  ],
  [
    0, 2, 1, 0, 3, 2,
    4, 5, 6, 4, 6, 7,
    0, 1, 5, 0, 5, 4,
    3, 7, 6, 3, 6, 2,
    0, 4, 7, 0, 7, 3,
    1, 2, 6, 1, 6, 5
  ]
);

function triangleCentroidX(boundary: WatertightTriangleMeshBoundary): number[] {
  const result: number[] = [];
  for (let offset = 0; offset < boundary.triangles.length; offset += 3) {
    const first = boundary.triangles[offset] * 3;
    const second = boundary.triangles[offset + 1] * 3;
    const third = boundary.triangles[offset + 2] * 3;
    result.push((
      boundary.vertices[first] +
      boundary.vertices[second] +
      boundary.vertices[third]
    ) / 3);
  }
  return result;
}

describe("dimensionless pressure-to-membrane response", () => {
  it("balances uniform pressure on a closed mesh without inventing expansion", () => {
    const pressures = new Float64Array(CUBE.triangles.length / 3).fill(2);
    const result = proposeDimensionlessPressureResponse(CUBE, pressures, {
      normalCompliance: 0.1,
      maximumVertexDisplacement: 0.2
    });

    expect(result.accepted).toBe(true);
    expect(Math.hypot(...result.fluidResultant)).toBeLessThan(1e-12);
    expect(result.maximumAppliedDisplacement).toBeLessThan(1e-12);
    expect(result.relativeVolumeChange).toBeLessThan(1e-12);
    expect(result.dimensionlessPressureWork).toBeCloseTo(0, 12);
    expect(result.runtimeFeedbackApplied).toBe(false);
  });

  it("produces a volume-conserving self-intersection-free shape response", () => {
    const pressures = triangleCentroidX(CUBE).map((x) => 1 + 0.35 * x);
    const result = proposeDimensionlessPressureResponse(CUBE, pressures, {
      normalCompliance: 0.14,
      maximumVertexDisplacement: 0.22,
      volumeToleranceFraction: 1e-10
    });

    expect(result.accepted).toBe(true);
    expect(result.candidateBoundary).not.toBeNull();
    expect(result.maximumAppliedDisplacement).toBeGreaterThan(0);
    expect(result.maximumAppliedDisplacement).toBeLessThanOrEqual(0.22);
    expect(result.relativeVolumeChange).toBeLessThan(1e-10);
    expect(result.selfIntersectionFree).toBe(true);
    expect(result.dimensionlessPressureWork).toBeGreaterThan(0);
    expect(result.membraneReaction[0]).toBeCloseTo(-result.fluidResultant[0], 12);
    expect(result.biologicalUnitsAssigned).toBe(false);
    expect(result.runtimeFeedbackApplied).toBe(false);
  });

  it("rejects incomplete or non-finite pressure inputs", () => {
    expect(() => proposeDimensionlessPressureResponse(CUBE, [1], {
      normalCompliance: 0.1,
      maximumVertexDisplacement: 0.2
    })).toThrow(/one finite dimensionless pressure/);
    const pressures = new Float64Array(CUBE.triangles.length / 3).fill(1);
    pressures[0] = Number.NaN;
    expect(() => proposeDimensionlessPressureResponse(CUBE, pressures, {
      normalCompliance: 0.1,
      maximumVertexDisplacement: 0.2
    })).toThrow(/pressures must be finite/);
  });

  it("keeps biological and runtime authority disabled", () => {
    expect(DIMENSIONLESS_FSI_CONTRACT.forceEnergyConsistencyTested).toBe(true);
    expect(DIMENSIONLESS_FSI_CONTRACT.volumePreservationTested).toBe(true);
    expect(DIMENSIONLESS_FSI_CONTRACT.selfIntersectionRejectionTested).toBe(true);
    expect(DIMENSIONLESS_FSI_CONTRACT.runtimeMembranePressureFeedbackEnabled).toBe(false);
    expect(DIMENSIONLESS_FSI_CONTRACT.biologicalPressureAssigned).toBe(false);
    expect(DIMENSIONLESS_FSI_CONTRACT.biologicalComplianceAssigned).toBe(false);
    expect(DIMENSIONLESS_FSI_CONTRACT.healthyPhhMechanicsAssigned).toBe(false);
  });
});
