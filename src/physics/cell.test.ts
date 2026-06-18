import { describe, it, expect } from "vitest";
import { LivingCell } from "./cell";

const settle = (c: LivingCell, seconds: number, dt = 0.04) => c.step(dt, Math.round(seconds / dt));

describe("LivingCell — organelle network", () => {
  it("reaches energetic homeostasis when fed", () => {
    const c = new LivingCell(undefined, 0.9);
    settle(c, 60);
    const s = c.snapshot();
    expect(s.energyCharge).toBeGreaterThan(0.5);
    expect(s.status).toBe("healthy");
    // pools stay bounded (no runaway accumulation)
    expect(s.pools.glucose).toBeLessThan(5);
    expect(s.pools.pyruvate).toBeLessThan(5);
  });

  it("runs every organelle's loop concurrently (all fluxes active)", () => {
    const c = new LivingCell(undefined, 0.9);
    settle(c, 40);
    const a = c.snapshot().activity;
    for (const k of Object.keys(a) as (keyof typeof a)[]) {
      expect(a[k]).toBeGreaterThan(0);
    }
  });

  it("mitochondria carry the pyruvate flux; the cell secretes protein", () => {
    const c = new LivingCell(undefined, 0.9);
    settle(c, 40);
    const s = c.snapshot();
    expect(s.activity.mitochondria).toBeGreaterThan(s.activity.glycolysis * 0.3);
    expect(s.pools.secreted).toBeGreaterThan(0.1);
  });

  it("conserves the ATP + ADP pool exactly", () => {
    const c = new LivingCell(undefined, 0.7);
    settle(c, 30);
    const s = c.snapshot();
    expect(s.atp + s.adp).toBeCloseTo(1, 6);
  });

  it("starves to death when the nutrient supply is cut", () => {
    const c = new LivingCell(undefined, 0.9);
    settle(c, 30);
    c.nutrient = 0;
    settle(c, 30);
    const s = c.snapshot();
    expect(s.atp).toBeLessThan(0.2);
    expect(s.status).toBe("dying");
  });

  it("recovers when fed again", () => {
    const c = new LivingCell(undefined, 0.9);
    settle(c, 20);
    c.nutrient = 0;
    settle(c, 25);
    c.nutrient = 0.9;
    settle(c, 40);
    const s = c.snapshot();
    expect(s.atp).toBeGreaterThan(0.45);
    expect(s.status).toBe("healthy");
  });

  it("higher nutrient sustains a higher energy charge", () => {
    const lo = new LivingCell(undefined, 0.25);
    const hi = new LivingCell(undefined, 1.0);
    settle(lo, 60);
    settle(hi, 60);
    expect(hi.snapshot().energyCharge).toBeGreaterThan(lo.snapshot().energyCharge);
  });
});
