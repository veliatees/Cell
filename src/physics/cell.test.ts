import { describe, expect, it } from "vitest";
import { LivingCell } from "./cell";

describe("living cell (metabolism ODEs)", () => {
  it("reaches energetic homeostasis when fed, with a bounded glucose pool", () => {
    const c = new LivingCell(undefined, 0.8);
    for (let i = 0; i < 3000; i += 1) c.step(0.02);
    const s = c.snapshot();
    expect(s.energyCharge).toBeGreaterThan(0.6); // a healthy, energised cell
    expect(s.glucoseIn).toBeLessThan(3); // respiration keeps glucose bounded
    expect(s.protein).toBeGreaterThan(0.5); // it is building protein
    expect(s.status).toBe("healthy");
  });

  it("conserves the ATP + ADP pool exactly", () => {
    const c = new LivingCell(undefined, 0.7);
    for (let i = 0; i < 500; i += 1) {
      c.step(0.02);
      const s = c.snapshot();
      expect(s.atp + s.adp).toBeCloseTo(c.params.atpTotal, 6);
    }
  });

  it("starves and dies when the nutrient supply is cut", () => {
    const c = new LivingCell(undefined, 0.8);
    for (let i = 0; i < 3000; i += 1) c.step(0.02);
    expect(c.snapshot().status).toBe("healthy");
    c.nutrient = 0;
    for (let i = 0; i < 1000; i += 1) c.step(0.02);
    const s = c.snapshot();
    expect(s.atp).toBeLessThan(0.15);
    expect(s.status).toBe("dying");
  });

  it("recovers when fed again", () => {
    const c = new LivingCell(undefined, 0);
    for (let i = 0; i < 1500; i += 1) c.step(0.02); // start starved
    expect(c.snapshot().atp).toBeLessThan(0.2);
    c.nutrient = 0.9;
    for (let i = 0; i < 2500; i += 1) c.step(0.02);
    expect(c.snapshot().atp).toBeGreaterThan(0.5);
    expect(c.snapshot().status).toBe("healthy");
  });

  it("a higher nutrient supply sustains a higher energy charge", () => {
    const low = new LivingCell(undefined, 0.12);
    const high = new LivingCell(undefined, 1.0);
    for (let i = 0; i < 3000; i += 1) {
      low.step(0.02);
      high.step(0.02);
    }
    expect(high.snapshot().energyCharge).toBeGreaterThan(low.snapshot().energyCharge);
  });
});
