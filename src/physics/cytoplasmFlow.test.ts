import { describe, expect, it } from "vitest";
import { CytoplasmFlowField } from "./cytoplasmFlow";

const sample = (f: CytoplasmFlowField, x: number, y: number, z: number, t: number) => {
  const out = { x: 0, y: 0, z: 0 };
  f.sampleInto(out, x, y, z, t);
  return out;
};

describe("CytoplasmFlowField", () => {
  it("is incompressible: divergence is ~0 everywhere", () => {
    const f = new CytoplasmFlowField(1234, 5, 6);
    const h = 1e-4;
    let maxDiv = 0;
    for (let i = 0; i < 40; i += 1) {
      const x = (Math.random() - 0.5) * 20;
      const y = (Math.random() - 0.5) * 20;
      const z = (Math.random() - 0.5) * 20;
      const t = Math.random() * 10;
      const dvx = (sample(f, x + h, y, z, t).x - sample(f, x - h, y, z, t).x) / (2 * h);
      const dvy = (sample(f, x, y + h, z, t).y - sample(f, x, y - h, z, t).y) / (2 * h);
      const dvz = (sample(f, x, y, z + h, t).z - sample(f, x, y, z - h, t).z) / (2 * h);
      maxDiv = Math.max(maxDiv, Math.abs(dvx + dvy + dvz));
    }
    // Curl-of-potential construction => divergence-free to numerical precision.
    expect(maxDiv).toBeLessThan(1e-3);
  });

  it("has a bounded, order-unity RMS magnitude", () => {
    const f = new CytoplasmFlowField(42, 4, 5);
    let acc = 0;
    const n = 400;
    for (let i = 0; i < n; i += 1) {
      const v = sample(f, (Math.random() - 0.5) * 16, (Math.random() - 0.5) * 16, (Math.random() - 0.5) * 16, Math.random() * 8);
      acc += v.x * v.x + v.y * v.y + v.z * v.z;
    }
    const rms = Math.sqrt(acc / n);
    expect(rms).toBeGreaterThan(0.2);
    expect(rms).toBeLessThan(5);
  });

  it("is deterministic for a given seed and evolves in time", () => {
    const a = new CytoplasmFlowField(7, 4, 5);
    const b = new CytoplasmFlowField(7, 4, 5);
    expect(sample(a, 1, 2, 3, 0)).toEqual(sample(b, 1, 2, 3, 0));
    // The pattern changes over time (not a frozen field).
    const t0 = sample(a, 1, 2, 3, 0);
    const t1 = sample(a, 1, 2, 3, 5);
    expect(t0).not.toEqual(t1);
  });
});
