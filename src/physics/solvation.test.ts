import { describe, expect, it } from "vitest";
import { SOLVATION_SCENES, solvationSystemFromPreset } from "./solvation";
import type { Vec3 } from "./water";

const dist = (a: Vec3, b: Vec3) =>
  Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2);

const preset = (id: string) => {
  const p = SOLVATION_SCENES.find((s) => s.id === id);
  if (!p) {
    throw new Error(`missing solvation preset ${id}`);
  }
  return p;
};

describe("solvation (ions + SPC/E water)", () => {
  it("forms a Na+ hydration shell at the measured Na–O distance (~0.24 nm)", () => {
    const sys = solvationSystemFromPreset(preset("na-hydration"));
    const start = sys.snapshot().minIonOxygenNm ?? 0;

    for (let i = 0; i < 1500; i += 1) {
      sys.step(5);
    }
    const snap = sys.snapshot();
    const settled = snap.minIonOxygenNm ?? 0;

    // Waters move inward and settle near the experimental first-shell Na–O distance.
    expect(settled).toBeLessThan(start);
    expect(settled).toBeGreaterThan(0.21);
    expect(settled).toBeLessThan(0.27);
  });

  it("keeps water rigid and the system finite during solvation", () => {
    const sys = solvationSystemFromPreset(preset("na-hydration"));
    sys.step(6000);
    const snap = sys.snapshot();

    expect(Number.isFinite(snap.totalEnergyEv)).toBe(true);
    for (const w of snap.waters) {
      const [o, h1, h2] = w.sitePositionsNm;
      expect(dist(o, h1)).toBeCloseTo(0.1, 3); // SPC/E O–H bond length
      expect(dist(o, h2)).toBeCloseTo(0.1, 3);
    }
  });

  it("Lennard-Jones repulsion stops water collapsing onto the ion", () => {
    const sys = solvationSystemFromPreset(preset("na-hydration"));
    sys.step(8000);
    const settled = sys.snapshot().minIonOxygenNm ?? 0;
    expect(settled).toBeGreaterThan(0.18);
  });

  it("represents NaCl in water as two ions plus a water bath", () => {
    const sys = solvationSystemFromPreset(preset("nacl-in-water"));
    const snap = sys.snapshot();
    expect(snap.ions.length).toBe(2);
    expect(snap.waters.length).toBe(8);
    const charges = snap.ions.map((i) => i.label);
    expect(charges).toContain("Na+");
    expect(charges).toContain("Cl-");
  });
});
