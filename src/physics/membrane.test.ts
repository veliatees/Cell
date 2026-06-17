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

  it("opens the one-reality scene as a closed vesicle of a performant size", () => {
    const preset = MEMBRANE_SCENES.find((s) => s.id === "cell-reality");
    if (!preset) {
      throw new Error("missing cell-reality scene");
    }
    expect(preset.config.mode).toBe("vesicle");
    const sys = membraneSystemFromPreset(preset);
    const snap = sys.snapshot();

    expect(snap.lipids.length).toBeGreaterThan(0);
    // Small enough to run at one step/frame without lag.
    expect(snap.beads.length).toBeLessThan(1000);
    expect(snap.beads.some((b) => b.kind === "solute")).toBe(true);
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

  it("forms a stable closed vesicle (a recognizable cell) that traps its contents", () => {
    const sys = new MembraneSystem({ mode: "vesicle", vesicleRadiusSigma: 6, solutesInside: 24 });
    for (let i = 0; i < 600; i += 1) {
      sys.step(1);
    }
    const snap = sys.snapshot();
    const lipidBeads = snap.beads.filter((b) => b.kind !== "solute");
    const radii = lipidBeads.map((b) => Math.hypot(b.pos.x, b.pos.y, b.pos.z));
    // Finite and roughly spherical: all lipid beads sit in a shell, none flew off.
    expect(radii.every(Number.isFinite)).toBe(true);
    const meanR = radii.reduce((s, r) => s + r, 0) / radii.length;
    expect(meanR).toBeGreaterThan(3);
    expect(Math.max(...radii)).toBeLessThan(meanR + 6); // no escaped lipids
    // Most solutes stay enclosed inside the bag.
    const solutes = snap.beads.filter((b) => b.kind === "solute");
    const inside = solutes.filter((b) => Math.hypot(b.pos.x, b.pos.y, b.pos.z) < meanR).length;
    expect(inside).toBeGreaterThan(solutes.length * 0.6);
  }, 30000);

  it("a vesicle pore lets the cell exchange contents with its environment", () => {
    const rad = (b: { pos: { x: number; y: number; z: number } }) =>
      Math.hypot(b.pos.x, b.pos.y, b.pos.z);
    const sys = new MembraneSystem({
      mode: "vesicle",
      vesicleRadiusSigma: 6,
      vesiclePoreAngleDeg: 38,
      solutesInside: 22,
      solutesOutside: 14
    });
    const enclosed = (s: ReturnType<MembraneSystem["snapshot"]>) => {
      const shell = s.beads.filter((b) => b.kind !== "solute").map(rad);
      const meanR = shell.reduce((a, b) => a + b, 0) / shell.length;
      return s.beads.filter((b) => b.kind === "solute" && rad(b) < meanR).length;
    };
    const start = enclosed(sys.snapshot());
    for (let i = 0; i < 1000; i += 1) {
      sys.step(1);
    }
    const snap = sys.snapshot();
    expect(snap.beads.every((b) => Number.isFinite(b.pos.x))).toBe(true);
    // The interior count changes as material moves through the pore.
    expect(enclosed(snap)).toBeLessThan(start);
  }, 30000);

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
