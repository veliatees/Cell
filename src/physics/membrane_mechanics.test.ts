import { describe, expect, it } from "vitest";
import {
  applyVolumePreservingAffineContactShape,
  createHepatocyteMembraneSim,
  createMembraneSim,
  MEMBRANE_ELASTIC_AREA_STRAIN_LIMIT,
  membraneGeometryMetrics,
  stepMembrane,
  writeBarycentricMembranePoint,
  writePrevalidatedBarycentricMembranePoint
} from "./membrane_mechanics";

describe("whole-cell membrane mechanics", () => {
  it("projects a distorted mesh back to a non-folding radial shell", () => {
    const sim = createMembraneSim(14, 3);

    for (let v = 0; v < sim.n; v += 1) {
      const i = v * 3;
      const dx = sim.restDir[i], dy = sim.restDir[i + 1], dz = sim.restDir[i + 2];
      const tx = -dz;
      const ty = 0;
      const tz = dx;
      const tLen = Math.hypot(tx, ty, tz) || 1;
      const radial = sim.radius * (v % 2 === 0 ? 1.22 : 0.82);
      const tangential = sim.radius * 0.28 * (v % 3 === 0 ? 1 : -1);
      sim.pos[i] = dx * radial + (tx / tLen) * tangential;
      sim.pos[i + 1] = dy * radial + (ty / tLen) * tangential;
      sim.pos[i + 2] = dz * radial + (tz / tLen) * tangential;
    }

    stepMembrane(sim, 0.016);
    const metrics = membraneGeometryMetrics(sim);
    expect(metrics.invertedFaces).toBe(0);
    expect(metrics.areaRatio).toBeLessThanOrEqual(1 + MEMBRANE_ELASTIC_AREA_STRAIN_LIMIT + 1e-4);
    expect(metrics.volumeRatio).toBeCloseTo(1, 3);
  });

  it("does not accumulate excess area or inverted faces under repeated numerical perturbation", () => {
    const sim = createMembraneSim(14, 3);

    for (let i = 0; i < 900; i += 1) {
      if (i % 90 === 0) {
        for (let vertex = 0; vertex < sim.n; vertex += 1) {
          const index = vertex * 3;
          const phase = Math.sin(vertex * 0.73 + i * 0.11);
          const scale = 1 + phase * 0.006;
          sim.pos[index] *= scale;
          sim.pos[index + 1] *= scale;
          sim.pos[index + 2] *= scale;
        }
      }
      stepMembrane(sim, 0.012);
    }

    const metrics = membraneGeometryMetrics(sim);
    expect(metrics.invertedFaces).toBe(0);
    expect(metrics.areaRatio).toBeLessThanOrEqual(1 + MEMBRANE_ELASTIC_AREA_STRAIN_LIMIT + 1e-4);
    expect(metrics.volumeRatio).toBeCloseTo(1, 3);
  });

  it("keeps the canonical polyhedral hepatocyte surface closed and bounded", () => {
    const sim = createHepatocyteMembraneSim(14, 3);
    const initial = membraneGeometryMetrics(sim);

    expect(sim.restShape).toBe("canonical_hepatocyte_polyhedron");
    expect(initial.invertedFaces).toBe(0);
    expect(initial.minRadius).toBeLessThan(initial.maxRadius);
    expect(initial.minRestRadiusRatio).toBeCloseTo(1, 5);
    expect(initial.maxRestRadiusRatio).toBeCloseTo(1, 5);

    for (let i = 0; i < 360; i += 1) stepMembrane(sim, 0.012);
    const settled = membraneGeometryMetrics(sim);
    expect(settled.invertedFaces).toBe(0);
    expect(settled.areaRatio).toBeLessThanOrEqual(1 + MEMBRANE_ELASTIC_AREA_STRAIN_LIMIT + 1e-4);
    expect(settled.volumeRatio).toBeCloseTo(1, 3);
  });

  it("maps an authoritative contact shape with exact affine volume preservation", () => {
    const sim = createHepatocyteMembraneSim(14, 3);
    const before = membraneGeometryMetrics(sim);

    applyVolumePreservingAffineContactShape(sim, [0, 1, 0], 0.9);
    const after = membraneGeometryMetrics(sim);

    expect(after.volumeRatio).toBeCloseTo(before.volumeRatio, 5);
    expect(after.invertedFaces).toBe(0);
    expect(after.maxRadius - after.minRadius).toBeGreaterThan(before.maxRadius - before.minRadius);
    expect(Array.from(sim.pos)).not.toEqual(Array.from(sim.restPos));
  });

  it("advects a surface tracer with its saved face and barycentric coordinates", () => {
    const sim = createHepatocyteMembraneSim(14, 2);
    const before = new Float32Array(3);
    const after = new Float32Array(3);
    writeBarycentricMembranePoint(sim, 0, 0.2, 0.3, 0.5, before);

    applyVolumePreservingAffineContactShape(sim, [1, 0, 0], 0.9);
    writeBarycentricMembranePoint(sim, 0, 0.2, 0.3, 0.5, after);

    expect(Array.from(after)).not.toEqual(Array.from(before));
    expect(Array.from(after).every(Number.isFinite)).toBe(true);
    expect(() => writeBarycentricMembranePoint(sim, 0, 0.2, 0.3, 0.4, after)).toThrow(/sum to one/);

    const hotPath = new Float32Array(3);
    writePrevalidatedBarycentricMembranePoint(sim, 0, 0.2, 0.3, 0.5, hotPath);
    expect(Array.from(hotPath)).toEqual(Array.from(after));
  });

  it("does not expose uncalibrated whole-cell thermal forcing", () => {
    const sim = createHepatocyteMembraneSim(14, 2);
    expect("noise" in sim).toBe(false);
  });
});
