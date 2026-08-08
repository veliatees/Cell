import { describe, expect, it } from "vitest";

import {
  CYTOPLASM_RENDERER_MOTION_CONTRACT,
  createCytoplasmRendererRng,
  populationRendererNoiseScaleWorld,
  validateCytoplasmRendererMotionContract
} from "./cytoplasmRendererMotion";

describe("cytoplasm renderer motion authority", () => {
  it("is explicitly visual and cannot supply biological state", () => {
    const contract = CYTOPLASM_RENDERER_MOTION_CONTRACT;
    expect(() => validateCytoplasmRendererMotionContract(contract)).not.toThrow();
    expect(contract.role).toBe("renderer_staging_only");
    expect(contract.timeBasis).toBe("elapsed_real_render_seconds");
    expect(contract.scientificAuthority).toBe(false);
    expect(contract.biologicalTimeClaim).toBe(false);
    expect(contract.biologicalVelocityClaim).toBe(false);
    expect(contract.healthyPhhParameterCount).toBe(0);
    expect(contract.engineEvidenceValueConsumedCount).toBe(0);
    expect(contract.mayDriveDimensionlessGeometryProjection).toBe(true);
    expect(contract.mayDriveBiologicalMembraneForce).toBe(false);
    expect(contract.mayDriveReactionTransport).toBe(false);
    expect(contract.mayDriveBiochemicalState).toBe(false);
  });

  it("uses a reproducible renderer-only random stream", () => {
    const first = createCytoplasmRendererRng(42);
    const second = createCytoplasmRendererRng(42);
    const a = Array.from({ length: 12 }, () => first());
    const b = Array.from({ length: 12 }, () => second());
    expect(a).toEqual(b);
    expect(new Set(a).size).toBeGreaterThan(1);
    expect(a.every((value) => value >= 0 && value < 1)).toBe(true);
  });

  it("keeps population staging values in one disclosed contract", () => {
    expect(populationRendererNoiseScaleWorld("mitochondria")).toBe(0.035);
    expect(populationRendererNoiseScaleWorld("peroxisomes")).toBe(0.045);
    expect(populationRendererNoiseScaleWorld("unknown")).toBe(0.03);
    expect(populationRendererNoiseScaleWorld(null)).toBe(0.03);
  });

  it("rejects a contract promoted to scientific authority", () => {
    expect(() => validateCytoplasmRendererMotionContract({
      ...CYTOPLASM_RENDERER_MOTION_CONTRACT,
      scientificAuthority: true as false
    })).toThrow(/scientific-authority boundary/);
  });
});
