import { describe, expect, it } from "vitest";
import {
  advanceMembraneEvents,
  createMembraneSim,
  MEMBRANE_ELASTIC_AREA_STRAIN_LIMIT,
  MEMBRANE_WHOLE_CELL_RADIAL_DEVIATION_LIMIT,
  membraneGeometryMetrics,
  spawnMembraneEvent,
  stepMembrane
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
    expect(metrics.minRadius).toBeGreaterThanOrEqual(sim.radius * (1 - MEMBRANE_WHOLE_CELL_RADIAL_DEVIATION_LIMIT) - 1e-4);
    expect(metrics.maxRadius).toBeLessThanOrEqual(sim.radius * Math.sqrt(1 + MEMBRANE_ELASTIC_AREA_STRAIN_LIMIT) + 1e-4);
  });

  it("does not accumulate excess area or inverted faces over a long run", () => {
    const sim = createMembraneSim(14, 3);
    let seed = 17;
    const rand = () => {
      seed = (seed * 1664525 + 1013904223) >>> 0;
      return seed / 0xffffffff;
    };

    for (let i = 0; i < 900; i += 1) {
      if (i % 90 === 0) spawnMembraneEvent(sim, i % 180 === 0 ? "endocytosis" : "exocytosis", rand);
      stepMembrane(sim, 0.012);
      advanceMembraneEvents(sim, 0.012);
    }

    const metrics = membraneGeometryMetrics(sim);
    expect(metrics.invertedFaces).toBe(0);
    expect(metrics.areaRatio).toBeLessThanOrEqual(1 + MEMBRANE_ELASTIC_AREA_STRAIN_LIMIT + 1e-4);
    expect(metrics.minRadius).toBeGreaterThanOrEqual(sim.radius * (1 - MEMBRANE_WHOLE_CELL_RADIAL_DEVIATION_LIMIT) - 1e-4);
    expect(metrics.maxRadius).toBeLessThanOrEqual(sim.radius * Math.sqrt(1 + MEMBRANE_ELASTIC_AREA_STRAIN_LIMIT) + 1e-4);
  });
});
