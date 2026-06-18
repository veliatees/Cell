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

  it("ATP transport takes longer for organelles further from the source", () => {
    const c = new LivingCell(undefined, 0.9);
    // distances in scene units; 0.7 µm per unit (cell radius ~10 µm)
    c.setGeometry({ mitochondria: 1, ribosome: 12 }, 0.7);
    const r = Object.fromEntries(c.snapshot().organelles.map((o) => [o.id, o]));
    expect(r.ribosome.transportMs).toBeGreaterThan(r.mitochondria.transportMs);
    expect(r.ribosome.transportMs).toBeGreaterThan(0);
  });

  it("is imperfect: under stress, organelles fault and the cell logs events", () => {
    const c = new LivingCell(undefined, 0.9, true); // noise + faults on
    settle(c, 20);
    c.nutrient = 0.05; // starve → stress → faults become likely
    settle(c, 60);
    const s = c.snapshot();
    const minEff = Math.min(...s.organelles.map((o) => o.efficiency));
    expect(minEff).toBeLessThan(1); // at least one organelle degraded
    expect(s.events.some((e) => e.severity === "warn" || e.severity === "crit")).toBe(true);
  });

  it("a healthy, well-fed cell mostly works (high efficiency) but is not guaranteed perfect", () => {
    const c = new LivingCell(undefined, 0.95, true);
    settle(c, 80);
    const s = c.snapshot();
    const meanEff = s.organelles.reduce((a, o) => a + o.efficiency, 0) / s.organelles.length;
    expect(meanEff).toBeGreaterThan(0.7); // mostly functional when conditions are good
  });

  it("deterministic mode never faults (reproducible for tests)", () => {
    const c = new LivingCell(undefined, 0.9, false);
    settle(c, 80);
    const s = c.snapshot();
    expect(s.organelles.every((o) => o.efficiency > 0.99)).toBe(true);
    // no probabilistic fault events in deterministic mode (status notes are fine)
    expect(s.events.some((e) => /faulted/.test(e.text))).toBe(false);
  });

  it("gives each organelle its own independent cycle (phases differ)", () => {
    const c = new LivingCell(undefined, 0.9);
    settle(c, 7);
    const ph = c.snapshot().organelles.map((o) => o.phase);
    const uniq = new Set(ph.map((x) => x.toFixed(3)));
    expect(uniq.size).toBeGreaterThan(4); // organelles are not in lockstep
    // periods are distinct per organelle (different lifestyles)
    const periods = new Set(c.snapshot().organelles.map((o) => o.periodS));
    expect(periods.size).toBeGreaterThan(4);
  });
});
