import { describe, expect, it } from "vitest";

import {
  ADAPTIVE_REMESHING_CONTRACT,
  evaluateSurfaceBinding,
  topologyPreservingAdaptiveRemesh
} from "./adaptiveRemeshing";

const CUBE_VERTICES = [
  -1, -1, -1,
  1, -1, -1,
  1, 1, -1,
  -1, 1, -1,
  -1, -1, 1,
  1, -1, 1,
  1, 1, 1,
  -1, 1, 1
];

const CUBE_TRIANGLES = [
  0, 2, 1, 0, 3, 2,
  4, 5, 6, 4, 6, 7,
  0, 1, 5, 0, 5, 4,
  3, 7, 6, 3, 6, 2,
  0, 4, 7, 0, 7, 3,
  1, 2, 6, 1, 6, 5
];

describe("topology-preserving adaptive remeshing", () => {
  it("bisects a long closed-manifold edge without changing geometry or topology", () => {
    const result = topologyPreservingAdaptiveRemesh(
      CUBE_VERTICES,
      CUBE_TRIANGLES,
      {
        targetMaximumEdgeLength: 2.5,
        maximumSplitCount: 1
      }
    );

    expect(result.splitCount).toBe(1);
    expect(result.after.vertexCount).toBe(result.before.vertexCount + 1);
    expect(result.after.triangleCount).toBe(result.before.triangleCount + 2);
    expect(result.after.validClosedBoundary).toBe(true);
    expect(result.beforeEulerCharacteristic).toBe(2);
    expect(result.afterEulerCharacteristic).toBe(2);
    expect(result.relativeSurfaceAreaError).toBeLessThan(1e-12);
    expect(result.relativeEnclosedVolumeError).toBeLessThan(1e-12);
    expect(result.topologyPreserved).toBe(true);
    expect(result.topologyChangeAllowed).toBe(false);
  });

  it("transfers vertex, face and barycentric surface state exactly", () => {
    const binding = {
      id: "BSEP:surface-copy-1",
      triangleIndex: 0,
      barycentric: [0.6, 0.2, 0.2] as const
    };
    const beforePoint = evaluateSurfaceBinding(
      CUBE_VERTICES,
      CUBE_TRIANGLES,
      binding
    );
    const result = topologyPreservingAdaptiveRemesh(
      CUBE_VERTICES,
      CUBE_TRIANGLES,
      {
        targetMaximumEdgeLength: 2.5,
        maximumSplitCount: 1,
        bindings: [binding],
        vertexFields: [{
          name: "surface_state",
          components: 1,
          values: [0, 1, 2, 3, 4, 5, 6, 7]
        }],
        faceFields: [
          {
            name: "surface_density",
            components: 1,
            transfer: "density",
            values: Array(12).fill(10)
          },
          {
            name: "face_cargo_amount",
            components: 1,
            transfer: "extensive",
            values: Array(12).fill(2)
          }
        ]
      }
    );
    const afterPoint = evaluateSurfaceBinding(
      result.vertices,
      result.triangles,
      result.bindings[0]
    );

    expect(afterPoint[0]).toBeCloseTo(beforePoint[0], 12);
    expect(afterPoint[1]).toBeCloseTo(beforePoint[1], 12);
    expect(afterPoint[2]).toBeCloseTo(beforePoint[2], 12);
    expect(result.maximumBindingPositionError).toBeLessThan(1e-12);
    expect(result.vertexFields[0].values.at(-1)).toBeCloseTo(1, 12);
    expect(Array.from(result.faceFields[0].values).filter((value) => value === 10)).toHaveLength(14);
    expect(
      Array.from(result.faceFields[1].values).reduce((sum, value) => sum + value, 0)
    ).toBeCloseTo(24, 12);
  });

  it("refuses open meshes and invalid uncalibrated controls", () => {
    expect(() => topologyPreservingAdaptiveRemesh(
      CUBE_VERTICES,
      CUBE_TRIANGLES.slice(0, -3),
      {
        targetMaximumEdgeLength: 2.5,
        maximumSplitCount: 1
      }
    )).toThrow(/valid closed two-manifold/);
    expect(() => topologyPreservingAdaptiveRemesh(
      CUBE_VERTICES,
      CUBE_TRIANGLES,
      {
        targetMaximumEdgeLength: 0,
        maximumSplitCount: 1
      }
    )).toThrow(/finite and positive/);
  });

  it("keeps topology-changing and biological mechanics claims disabled", () => {
    expect(ADAPTIVE_REMESHING_CONTRACT.topologyChangeAllowed).toBe(false);
    expect(ADAPTIVE_REMESHING_CONTRACT.endocytosisOrFissionImplemented).toBe(false);
    expect(ADAPTIVE_REMESHING_CONTRACT.biologicalMechanicsAssigned).toBe(false);
    expect(ADAPTIVE_REMESHING_CONTRACT.runtimeMembraneCouplingEnabled).toBe(false);
    expect(ADAPTIVE_REMESHING_CONTRACT.refinementThresholdHasRuntimeDefault).toBe(false);
  });
});
