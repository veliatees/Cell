import { describe, expect, it } from "vitest";

import type { ClosedMembraneComponent } from "./membraneTopology";
import {
  MEMBRANE_TOPOLOGY_TRANSACTION_CONTRACT,
  prepareMembraneTopologyTransition
} from "./membraneTopologyTransaction";

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

describe("evidence-gated membrane topology transaction", () => {
  it("prepares a verified candidate without authorizing a runtime event", () => {
    const before = cube("parent", [0, 0, 0], 1.5);
    const after = [
      cube("daughter-a", [-2.5, 0, 0]),
      cube("daughter-b", [2.5, 0, 0])
    ];
    const candidate = prepareMembraneTopologyTransition({
      eventId: "test-fission-1",
      eventKind: "fission",
      beforeComponents: [before],
      afterComponents: after,
      lineages: [{
        sourceComponentIds: ["parent"],
        targetComponentIds: ["daughter-a", "daughter-b"]
      }],
      faceTransfers: Array.from({ length: 12 }, (_, faceIndex) => ({
        source: { componentId: "parent", faceIndex },
        targets: [{
          componentId: faceIndex < 6 ? "daughter-a" : "daughter-b",
          faceIndex,
          fraction: 1
        }]
      })),
      extensiveFields: [{
        name: "surface_cargo",
        unit: "arbitrary_extensive_test_unit",
        valuesByComponent: { parent: Array(12).fill(1) }
      }]
    });

    expect(candidate.candidatePrepared).toBe(true);
    expect(candidate.topology.eulerCharacteristicDelta).toBe(2);
    expect(candidate.stateTransfer.extensiveFields[0].totalAmountAfter).toBe(12);
    expect(candidate.numericalPreviewAllowed).toBe(true);
    expect(candidate.runtimeMeshReplacementAuthorized).toBe(false);
    expect(candidate.fluidDomainReplacementAuthorized).toBe(false);
    expect(candidate.biologicalEventActivationAuthorized).toBe(false);
    expect(candidate.blockers).toHaveLength(4);
  });

  it("exposes no automatic biological trigger, event time or neck threshold", () => {
    expect(MEMBRANE_TOPOLOGY_TRANSACTION_CONTRACT.automaticEventTrigger).toBe(false);
    expect(MEMBRANE_TOPOLOGY_TRANSACTION_CONTRACT.automaticEventTimeSelection).toBe(false);
    expect(MEMBRANE_TOPOLOGY_TRANSACTION_CONTRACT.automaticNeckThresholdSelection).toBe(false);
    expect(MEMBRANE_TOPOLOGY_TRANSACTION_CONTRACT.runtimeMeshReplacementAuthorized).toBe(false);
    expect(MEMBRANE_TOPOLOGY_TRANSACTION_CONTRACT.fluidDomainReplacementAuthorized).toBe(false);
    expect(MEMBRANE_TOPOLOGY_TRANSACTION_CONTRACT.biologicalEventActivationAuthorized).toBe(false);
  });
});
