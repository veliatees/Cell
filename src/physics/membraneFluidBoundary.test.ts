import { describe, expect, it } from "vitest";
import {
  applyVolumePreservingAffineContactShape,
  createHepatocyteMembraneSim,
  createMembraneSim,
  membraneRestRadiusAlongDirection
} from "./membrane_mechanics";
import { ReferenceMembraneRadialBoundary } from "./membraneFluidBoundary";

describe("reference-space membrane fluid boundary", () => {
  it("reproduces the undeformed rest boundary", () => {
    const sim = createHepatocyteMembraneSim(5, 3);
    const boundary = new ReferenceMembraneRadialBoundary();
    boundary.update(sim, null);

    for (const direction of [[1, 0, 0], [0, 1, 0], [1, 2, -3]] as const) {
      expect(boundary.radiusAtDirection(direction[0], direction[1], direction[2])).toBeCloseTo(
        membraneRestRadiusAlongDirection(sim, direction[0], direction[1], direction[2]),
        5
      );
    }
    expect(boundary.diagnostics().localStarShapedDeformationDetected).toBe(false);
  });

  it("transfers a local radial surface change into the fluid boundary", () => {
    const sim = createMembraneSim(5, 3);
    for (let vertex = 0; vertex < sim.n; vertex += 1) {
      const offset = vertex * 3;
      if (sim.restDir[offset] < 0.9) continue;
      sim.pos[offset] *= 1.08;
      sim.pos[offset + 1] *= 1.08;
      sim.pos[offset + 2] *= 1.08;
    }
    const boundary = new ReferenceMembraneRadialBoundary();
    boundary.update(sim, null);

    expect(boundary.radiusAtDirection(1, 0, 0)).toBeGreaterThan(5.1);
    expect(boundary.radiusAtDirection(-1, 0, 0)).toBeCloseTo(5, 2);
    expect(boundary.diagnostics().localStarShapedDeformationDetected).toBe(true);
    expect(boundary.diagnostics().topologyChangeSupported).toBe(false);
  });

  it("removes the shared affine contact map instead of applying it twice", () => {
    const sim = createHepatocyteMembraneSim(5, 3);
    const deformation = {
      normal: [0.3, 0.9, -0.2] as const,
      axialScale: 0.87
    };
    applyVolumePreservingAffineContactShape(
      sim,
      deformation.normal,
      deformation.axialScale
    );
    const boundary = new ReferenceMembraneRadialBoundary();
    boundary.update(sim, deformation);

    for (const direction of [[1, 0, 0], [0, 1, 0], [1, 2, -3]] as const) {
      expect(boundary.radiusAtDirection(direction[0], direction[1], direction[2])).toBeCloseTo(
        membraneRestRadiusAlongDirection(sim, direction[0], direction[1], direction[2]),
        4
      );
    }
    const diagnostics = boundary.diagnostics();
    expect(diagnostics.affineComponentRemoved).toBe(true);
    expect(diagnostics.maximumAbsoluteResidual).toBeLessThan(1e-4);
  });
});
