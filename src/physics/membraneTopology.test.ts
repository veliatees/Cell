import { describe, expect, it } from "vitest";

import {
  MEMBRANE_TOPOLOGY_AUDIT_CONTRACT,
  auditMembraneTopologyTransition,
  type ClosedMembraneComponent
} from "./membraneTopology";

const CUBE_TRIANGLES = [
  0, 2, 1, 0, 3, 2,
  4, 5, 6, 4, 6, 7,
  0, 1, 5, 0, 5, 4,
  3, 7, 6, 3, 6, 2,
  0, 4, 7, 0, 7, 3,
  1, 2, 6, 1, 6, 5
];

function cube(
  id: string,
  center: readonly [number, number, number],
  halfExtent = 1
): ClosedMembraneComponent {
  const [cx, cy, cz] = center;
  return {
    id,
    coordinateUnit: "numerical_length_unit",
    vertices: [
      cx - halfExtent, cy - halfExtent, cz - halfExtent,
      cx + halfExtent, cy - halfExtent, cz - halfExtent,
      cx + halfExtent, cy + halfExtent, cz - halfExtent,
      cx - halfExtent, cy + halfExtent, cz - halfExtent,
      cx - halfExtent, cy - halfExtent, cz + halfExtent,
      cx + halfExtent, cy - halfExtent, cz + halfExtent,
      cx + halfExtent, cy + halfExtent, cz + halfExtent,
      cx - halfExtent, cy + halfExtent, cz + halfExtent
    ],
    triangles: CUBE_TRIANGLES
  };
}

describe("closed membrane topology transition audit", () => {
  it("accepts topology-preserving bud and neck stages only as one-to-one lineages", () => {
    for (const event of ["bud_growth", "neck_formation"] as const) {
      const result = auditMembraneTopologyTransition(
        event,
        [cube("plasma-before", [0, 0, 0])],
        [cube("plasma-after", [0, 0, 0], 1.1)],
        [{
          sourceComponentIds: ["plasma-before"],
          targetComponentIds: ["plasma-after"]
        }]
      );
      expect(result.componentCountDelta).toBe(0);
      expect(result.eulerCharacteristicDelta).toBe(0);
      expect(result.topologyEventConsistent).toBe(true);
      expect(result.before[0].orientableGenus).toBe(0);
      expect(result.after[0].orientableGenus).toBe(0);
    }
  });

  it("accepts one-to-two fission and two-to-one fusion with exact topology changes", () => {
    const parent = cube("parent", [0, 0, 0], 1.5);
    const first = cube("daughter-a", [-2, 0, 0]);
    const second = cube("daughter-b", [2, 0, 0]);
    const fission = auditMembraneTopologyTransition(
      "fission",
      [parent],
      [first, second],
      [{
        sourceComponentIds: ["parent"],
        targetComponentIds: ["daughter-a", "daughter-b"]
      }]
    );
    expect(fission.componentCountDelta).toBe(1);
    expect(fission.eulerCharacteristicDelta).toBe(2);

    const fusion = auditMembraneTopologyTransition(
      "fusion",
      [first, second],
      [parent],
      [{
        sourceComponentIds: ["daughter-a", "daughter-b"],
        targetComponentIds: ["parent"]
      }]
    );
    expect(fusion.componentCountDelta).toBe(-1);
    expect(fusion.eulerCharacteristicDelta).toBe(-2);
  });

  it("rejects event labels, incomplete lineages and intersecting child surfaces", () => {
    const parent = cube("parent", [0, 0, 0], 1.5);
    const first = cube("first", [-2, 0, 0]);
    const second = cube("second", [2, 0, 0]);
    expect(() => auditMembraneTopologyTransition(
      "fusion",
      [parent],
      [first, second],
      [{
        sourceComponentIds: ["parent"],
        targetComponentIds: ["first", "second"]
      }]
    )).toThrow(/fusion requires/);
    expect(() => auditMembraneTopologyTransition(
      "fission",
      [parent],
      [first, second],
      [{
        sourceComponentIds: ["parent"],
        targetComponentIds: ["first"]
      }]
    )).toThrow(/cover every source and target/);
    expect(() => auditMembraneTopologyTransition(
      "fission",
      [parent],
      [cube("first", [0, 0, 0]), cube("second", [0.5, 0, 0])],
      [{
        sourceComponentIds: ["parent"],
        targetComponentIds: ["first", "second"]
      }]
    )).toThrow(/cross-component intersections/);
    expect(() => auditMembraneTopologyTransition(
      "neck_formation",
      [parent],
      [{ ...cube("after", [0, 0, 0]), coordinateUnit: "um" }],
      [{
        sourceComponentIds: ["parent"],
        targetComponentIds: ["after"]
      }]
    )).toThrow(/share one explicit coordinate unit/);
  });

  it("keeps detection, mesh surgery, runtime activation and mechanics disabled", () => {
    expect(MEMBRANE_TOPOLOGY_AUDIT_CONTRACT.automaticEventDetection).toBe(false);
    expect(MEMBRANE_TOPOLOGY_AUDIT_CONTRACT.automaticMeshSurgery).toBe(false);
    expect(MEMBRANE_TOPOLOGY_AUDIT_CONTRACT.automaticRuntimeActivation).toBe(false);
    expect(MEMBRANE_TOPOLOGY_AUDIT_CONTRACT.biologicalMechanicsAssigned).toBe(false);
  });
});
