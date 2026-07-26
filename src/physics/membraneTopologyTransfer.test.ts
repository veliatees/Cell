import { describe, expect, it } from "vitest";

import type { ClosedMembraneComponent } from "./membraneTopology";
import {
  MEMBRANE_TOPOLOGY_TRANSFER_CONTRACT,
  transferMembraneTopologyState,
  type MembraneFaceTransfer
} from "./membraneTopologyTransfer";

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

function fissionFaceMap(): MembraneFaceTransfer[] {
  return Array.from({ length: 12 }, (_, faceIndex) => ({
    source: { componentId: "parent", faceIndex },
    targets: faceIndex === 0
      ? [
        { componentId: "daughter-a", faceIndex, fraction: 0.25 },
        { componentId: "daughter-b", faceIndex, fraction: 0.75 }
      ]
      : [{
        componentId: faceIndex < 6 ? "daughter-a" : "daughter-b",
        faceIndex,
        fraction: 1
      }]
  }));
}

describe("conservative membrane topology state transfer", () => {
  it("conserves extensive lipid/cargo amounts and area-integrated protein density", () => {
    const result = transferMembraneTopologyState(
      [cube("parent", [0, 0, 0])],
      [cube("daughter-a", [-3, 0, 0], 0.8), cube("daughter-b", [3, 0, 0], 1.2)],
      fissionFaceMap(),
      {
        extensiveFields: [{
          name: "surface_lipid_amount",
          unit: "arbitrary_extensive_test_unit",
          valuesByComponent: { parent: Array(12).fill(2) }
        }],
        densityFields: [{
          name: "surface_protein_density",
          unit: "arbitrary_density_test_unit",
          valuesByComponent: { parent: Array(12).fill(3) }
        }]
      }
    );

    expect(result.extensiveFields[0].totalAmountBefore).toBeCloseTo(24, 12);
    expect(result.extensiveFields[0].totalAmountAfter).toBeCloseTo(24, 12);
    expect(result.densityFields[0].totalAmountBefore).toBeCloseTo(72, 12);
    expect(result.densityFields[0].totalAmountAfter).toBeCloseTo(72, 12);
    expect(result.maximumRelativeConservationError).toBeLessThan(1e-12);
    expect(result.surfaceInventoryConserved).toBe(true);
    expect(result.moleculeIdentityResolved).toBe(false);
  });

  it("preserves tracer identity only through an explicit target binding", () => {
    const result = transferMembraneTopologyState(
      [cube("parent", [0, 0, 0])],
      [cube("daughter-a", [-3, 0, 0]), cube("daughter-b", [3, 0, 0])],
      fissionFaceMap(),
      {
        sourceBindings: [{
          id: "BSEP:surface-copy-1",
          componentId: "parent",
          triangleIndex: 0,
          barycentric: [0.2, 0.3, 0.5]
        }],
        targetBindings: [{
          id: "BSEP:surface-copy-1",
          componentId: "daughter-b",
          triangleIndex: 0,
          barycentric: [0.2, 0.3, 0.5]
        }]
      }
    );
    expect(result.transferredBindings).toHaveLength(1);
    expect(result.transferredBindings[0].id).toBe("BSEP:surface-copy-1");
    expect(result.transferredBindings[0].componentId).toBe("daughter-b");
    expect(result.maximumBindingDisplacement).toBeGreaterThan(0);
    expect(result.bindingIdentityPreserved).toBe(true);
  });

  it("rejects missing faces, non-conservative fractions and implicit binding loss", () => {
    const before = [cube("parent", [0, 0, 0])];
    const after = [cube("daughter-a", [-3, 0, 0]), cube("daughter-b", [3, 0, 0])];
    expect(() => transferMembraneTopologyState(
      before,
      after,
      fissionFaceMap().slice(1)
    )).toThrow(/cover every source membrane face/);
    const badFractions = fissionFaceMap();
    badFractions[0] = {
      ...badFractions[0],
      targets: [
        { componentId: "daughter-a", faceIndex: 0, fraction: 0.2 },
        { componentId: "daughter-b", faceIndex: 0, fraction: 0.7 }
      ]
    };
    expect(() => transferMembraneTopologyState(
      before,
      after,
      badFractions
    )).toThrow(/sum to one/);
    expect(() => transferMembraneTopologyState(
      before,
      after,
      fissionFaceMap(),
      {
        sourceBindings: [{
          id: "MRP2:surface-copy-1",
          componentId: "parent",
          triangleIndex: 0,
          barycentric: [1, 0, 0]
        }]
      }
    )).toThrow(/requires exactly one explicit target/);
    expect(() => transferMembraneTopologyState(
      before,
      [
        { ...after[0], coordinateUnit: "um" },
        { ...after[1], coordinateUnit: "um" }
      ],
      fissionFaceMap()
    )).toThrow(/share one explicit coordinate unit/);
  });

  it("has no automatic correspondence or biological partition law", () => {
    expect(MEMBRANE_TOPOLOGY_TRANSFER_CONTRACT.automaticFaceCorrespondence).toBe(false);
    expect(MEMBRANE_TOPOLOGY_TRANSFER_CONTRACT.automaticBindingDestinationSelection).toBe(false);
    expect(MEMBRANE_TOPOLOGY_TRANSFER_CONTRACT.moleculeIdentityResolved).toBe(false);
    expect(MEMBRANE_TOPOLOGY_TRANSFER_CONTRACT.biologicalPartitionLawAssigned).toBe(false);
  });
});
