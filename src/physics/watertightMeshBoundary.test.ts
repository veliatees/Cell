import { describe, expect, it } from "vitest";

import {
  WatertightTriangleMeshBoundary,
  auditTriangleMesh,
  WATERTIGHT_MESH_BOUNDARY_CONTRACT
} from "./watertightMeshBoundary";

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

describe("watertight triangle mesh boundary", () => {
  it("audits a consistently wound closed cube", () => {
    const audit = auditTriangleMesh(CUBE_VERTICES, CUBE_TRIANGLES);
    expect(audit.topologicallyWatertight).toBe(true);
    expect(audit.boundaryEdgeCount).toBe(0);
    expect(audit.nonManifoldEdgeCount).toBe(0);
    expect(audit.inconsistentWindingEdgeCount).toBe(0);
    expect(audit.connectedComponentCount).toBe(1);
    expect(audit.surfaceArea).toBeCloseTo(24, 12);
    expect(audit.enclosedVolume).toBeCloseTo(8, 12);
    expect(audit.selfIntersectionTested).toBe(false);
  });

  it("fails closed for an open or inconsistently wound surface", () => {
    const openAudit = auditTriangleMesh(
      CUBE_VERTICES,
      CUBE_TRIANGLES.slice(0, -3)
    );
    expect(openAudit.topologicallyWatertight).toBe(false);
    expect(openAudit.boundaryEdgeCount).toBeGreaterThan(0);
    expect(() => new WatertightTriangleMeshBoundary(
      CUBE_VERTICES,
      CUBE_TRIANGLES.slice(0, -3)
    )).toThrow(/closed two-manifold/);

    const reversed = [...CUBE_TRIANGLES];
    [reversed[0], reversed[1]] = [reversed[1], reversed[0]];
    const windingAudit = auditTriangleMesh(CUBE_VERTICES, reversed);
    expect(windingAudit.topologicallyWatertight).toBe(false);
    expect(windingAudit.inconsistentWindingEdgeCount).toBeGreaterThan(0);
  });

  it("supports containment, padding and segment interception", () => {
    const boundary = new WatertightTriangleMeshBoundary(
      CUBE_VERTICES,
      CUBE_TRIANGLES
    );
    expect(boundary.containsPoint(0, 0, 0)).toBe(true);
    expect(boundary.containsPoint(1.05, 0, 0)).toBe(false);
    expect(boundary.containsPoint(1.05, 0, 0, 0.1)).toBe(true);
    expect(boundary.intersectsSegment([-2, 0, 0], [2, 0, 0])).toBe(true);
    expect(boundary.intersectsSegment([-2, 2, 0], [2, 2, 0])).toBe(false);
  });

  it("keeps biological claims disabled in the numerical contract", () => {
    expect(WATERTIGHT_MESH_BOUNDARY_CONTRACT.biologicalMeshRegistered).toBe(false);
    expect(WATERTIGHT_MESH_BOUNDARY_CONTRACT.biologicalUnitsAssigned).toBe(false);
    expect(WATERTIGHT_MESH_BOUNDARY_CONTRACT.selfIntersectionTested).toBe(false);
  });
});
