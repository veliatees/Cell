import { describe, expect, it } from "vitest";
import {
  INTRACELLULAR_FLUID_VISUAL_CONTRACT,
  IntracellularFluidField,
  applyVolumePreservingFluidDeformation,
  createSeededSphereTracerPositions,
  volumePreservingFluidMapDeterminant
} from "./intracellularFluid";

describe("intracellular fluid renderer field", () => {
  it("reproduces the same tracer field from the same seed", () => {
    const initial = createSeededSphereTracerPositions(120, 8, 91);
    const options = {
      seed: 20260721,
      initialPositions: initial,
      radiusAtDirection: () => 10
    };
    const first = new IntracellularFluidField(options);
    const second = new IntracellularFluidField(options);

    for (let frame = 0; frame < 90; frame += 1) {
      first.step(1 / 60, null);
      second.step(1 / 60, null);
    }

    expect(Array.from(first.positions)).toEqual(Array.from(second.positions));
    expect(Array.from(first.positions)).not.toEqual(Array.from(initial));
  });

  it("keeps every reference tracer inside its moving-domain safety envelope", () => {
    const field = new IntracellularFluidField({
      seed: 7,
      initialPositions: createSeededSphereTracerPositions(240, 12, 8),
      radiusAtDirection: () => 10,
      safetyFraction: 0.86
    });

    for (let frame = 0; frame < 1_200; frame += 1) field.step(1 / 60, null);

    for (let index = 0; index < field.referencePositions.length; index += 3) {
      expect(Math.hypot(
        field.referencePositions[index],
        field.referencePositions[index + 1],
        field.referencePositions[index + 2]
      )).toBeLessThanOrEqual(8.60001);
    }
  });

  it("uses the same exactly volume-preserving affine map as contact deformation", () => {
    const target = new Float32Array(3);
    applyVolumePreservingFluidDeformation(2, -3, 4, {
      normal: [1, 0, 0],
      axialScale: 0.81
    }, target);

    expect(target[0]).toBeCloseTo(1.62, 6);
    expect(target[1]).toBeCloseTo(-3 / 0.9, 6);
    expect(target[2]).toBeCloseTo(4 / 0.9, 6);
    expect(volumePreservingFluidMapDeterminant(0.81)).toBeCloseTo(1, 12);
  });

  it("rejects obstacle-crossing steps without inventing penetrable organelles", () => {
    const initial = new Float32Array([2, 0, 0, -2, 0, 0]);
    const field = new IntracellularFluidField({
      seed: 41,
      initialPositions: initial,
      radiusAtDirection: () => 10
    });
    const before = new Float32Array(field.referencePositions);

    field.step(1 / 30, null, () => true);

    expect(Array.from(field.referencePositions)).toEqual(Array.from(before));
  });

  it("does not claim molecule counts, measured velocity or reaction coupling", () => {
    expect(INTRACELLULAR_FLUID_VISUAL_CONTRACT.moleculeCountClaim).toBe(false);
    expect(INTRACELLULAR_FLUID_VISUAL_CONTRACT.biologicalVelocityClaim).toBe(false);
    expect(INTRACELLULAR_FLUID_VISUAL_CONTRACT.reactionRateCoupling).toBe(false);
  });
});
