import { describe, expect, it } from "vitest";
import { MEMBRANE_SCENES, MembraneSystem, membraneSystemFromPreset } from "./membrane";

describe("Cooke–Deserno lipid membrane", () => {
  it("builds 3-bead lipids (1 head + 2 tails) in two leaflets", () => {
    const sys = new MembraneSystem({ perSide: 4, mode: "bilayer" });
    const snap = sys.snapshot();
    expect(snap.lipids.length).toBe(4 * 4 * 2); // perSide² per leaflet × 2 leaflets
    expect(snap.beads.length).toBe(snap.lipids.length * 3);
    const heads = snap.beads.filter((b) => b.kind === "head").length;
    const tails = snap.beads.filter((b) => b.kind === "tail").length;
    expect(heads).toBe(snap.lipids.length);
    expect(tails).toBe(snap.lipids.length * 2);
  });

  it("starts as a real bilayer: heads out, tails toward the midplane, thickness ~5σ", () => {
    const sys = new MembraneSystem({ perSide: 6, mode: "bilayer" });
    const snap = sys.snapshot();

    const headAbsZ = avg(snap.beads.filter((b) => b.kind === "head").map((b) => Math.abs(b.pos.z)));
    const tailAbsZ = avg(snap.beads.filter((b) => b.kind === "tail").map((b) => Math.abs(b.pos.z)));
    expect(tailAbsZ).toBeLessThan(headAbsZ); // tails are inside, heads outside
    expect(snap.thicknessSigma).toBeGreaterThan(3);
    expect(snap.thicknessSigma).toBeLessThan(7);
  });

  it("stays a cohesive bilayer under thermal motion (does not fall apart)", () => {
    const sys = new MembraneSystem({ perSide: 6, mode: "bilayer", seed: 7 });
    sys.step(3000);
    const snap = sys.snapshot();

    expect(Number.isFinite(snap.potentialEnergy)).toBe(true);
    // Still two separated leaflets with tails clustered near the midplane.
    const headAbsZ = avg(snap.beads.filter((b) => b.kind === "head").map((b) => Math.abs(b.pos.z)));
    const tailAbsZ = avg(snap.beads.filter((b) => b.kind === "tail").map((b) => Math.abs(b.pos.z)));
    expect(tailAbsZ).toBeLessThan(headAbsZ);
    expect(snap.thicknessSigma).toBeGreaterThan(2.5);
    expect(snap.thicknessSigma).toBeLessThan(8);
    // Lipids remain orientationally ordered (a fluid/gel bilayer, not a gas).
    expect(snap.orderS).toBeGreaterThan(0.3);
  }, 30000);

  it("keeps every bead finite over a long run", () => {
    const sys = new MembraneSystem({ perSide: 5, mode: "bilayer", seed: 3 });
    sys.step(4000);
    for (const b of sys.snapshot().beads) {
      expect(Number.isFinite(b.pos.x) && Number.isFinite(b.pos.y) && Number.isFinite(b.pos.z)).toBe(true);
      expect(Math.abs(b.pos.z)).toBeLessThan(100);
    }
  }, 30000);

  it("exposes membrane scenes for the viewer", () => {
    const sys = membraneSystemFromPreset(MEMBRANE_SCENES[0]);
    expect(sys.snapshot().lipids.length).toBeGreaterThan(0);
    expect(MEMBRANE_SCENES.map((s) => s.id)).toContain("self-assembly");
  });

  it("opens the one-reality scene as a light, validated inside/outside membrane world", () => {
    const preset = MEMBRANE_SCENES.find((s) => s.id === "cell-reality");
    if (!preset) {
      throw new Error("missing cell-reality scene");
    }
    const sys = membraneSystemFromPreset(preset);
    const snap = sys.snapshot();

    expect(snap.beads.length).toBeLessThan(320);
    expect(snap.lipids.length).toBeGreaterThan(0);
    expect(snap.soluteAbove).toBeGreaterThan(0);
    expect(snap.soluteBelow).toBeGreaterThan(0);
    expect(snap.thicknessSigma).toBeGreaterThan(4);
    expect(snap.thicknessSigma).toBeLessThan(7);
    expect(snap.orderS).toBeGreaterThan(0.9);
    expect(Number.isFinite(snap.potentialEnergy)).toBe(true);
  });

  it("can initialize a finite closed-vesicle prototype without leaflet overlap", () => {
    const sys = new MembraneSystem({
      mode: "vesicle",
      vesicleRadiusSigma: 5.5,
      solutesInside: 8,
      seed: 13
    });
    const start = sys.snapshot();

    expect(start.beads.length).toBeLessThan(700);
    expect(start.thicknessSigma).toBeGreaterThan(4);
    expect(start.thicknessSigma).toBeLessThan(7);
    expect(start.orderS).toBeGreaterThan(0.9);
    expect(Number.isFinite(start.potentialEnergy)).toBe(true);

    sys.step(1);
    const after = sys.snapshot();
    expect(Number.isFinite(after.potentialEnergy)).toBe(true);
    for (const b of after.beads) {
      expect(Number.isFinite(b.pos.x) && Number.isFinite(b.pos.y) && Number.isFinite(b.pos.z)).toBe(true);
    }
  });

  it("an intact bilayer blocks solutes (barrier function)", () => {
    const sys = new MembraneSystem({ perSide: 6, mode: "bilayer", solutes: 16, seed: 5 });
    expect(sys.snapshot().soluteBelow).toBe(0); // all start above
    for (let i = 0; i < 2000; i += 1) {
      sys.step(2);
    }
    // None should have crossed the intact bilayer.
    expect(sys.snapshot().soluteBelow).toBe(0);
  }, 30000);

  it("a pore lets solutes cross (transport)", () => {
    const sys = new MembraneSystem({
      perSide: 6,
      mode: "bilayer",
      solutes: 16,
      poreRadiusSigma: 2.2,
      seed: 5
    });
    for (let i = 0; i < 2000; i += 1) {
      sys.step(2);
    }
    // With a pore, some solutes reach the other side.
    expect(sys.snapshot().soluteBelow).toBeGreaterThanOrEqual(1);
  }, 30000);
});

function avg(xs: number[]): number {
  return xs.reduce((s, x) => s + x, 0) / Math.max(xs.length, 1);
}
