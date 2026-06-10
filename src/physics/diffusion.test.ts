import { describe, expect, it } from "vitest";
import { ION_DIFFUSION_M2_S, WATER_VISCOSITY_PA_S } from "./constants";
import {
  DIFFUSION_SCENES,
  DiffusionSystem,
  diffusionSystemFromPreset,
  stokesEinsteinM2PerS,
  type DiffusionConfig
} from "./diffusion";

const cloud = (n: number, dM2PerS: number): DiffusionConfig[] =>
  Array.from({ length: n }, () => ({
    label: "p",
    color: "#fff",
    diffusionM2PerS: dM2PerS,
    posNm: { x: 0, y: 0, z: 0 }
  }));

describe("Brownian diffusion", () => {
  it("recovers the input D from the mean-squared displacement (⟨r²⟩ = 6 D t)", () => {
    const dInput = ION_DIFFUSION_M2_S["sodium-ion"]; // 1.334e-9 m²/s
    const sys = new DiffusionSystem(cloud(4000, dInput), 100);

    sys.step(2000); // 200,000 fs = 0.2 ns
    const snap = sys.snapshot();

    // ⟨r²⟩ = 6 D t  ⇒  D = ⟨r²⟩ / (6 t). Convert nm²/fs back to m²/s (÷1e3).
    const dMeasuredNm2PerFs = snap.msdNm2 / (6 * snap.elapsedFs);
    const dMeasuredM2PerS = dMeasuredNm2PerFs / 1e3;

    expect(dMeasuredM2PerS).toBeGreaterThan(dInput * 0.9);
    expect(dMeasuredM2PerS).toBeLessThan(dInput * 1.1);
  });

  it("faster D spreads wider in the same time", () => {
    const slow = new DiffusionSystem(cloud(3000, 1.0e-9), 100, 11);
    const fast = new DiffusionSystem(cloud(3000, 2.0e-9), 100, 11);
    slow.step(1500);
    fast.step(1500);
    expect(fast.snapshot().msdNm2).toBeGreaterThan(slow.snapshot().msdNm2);
  });

  it("MSD grows linearly in time (diffusive, not ballistic)", () => {
    const sys = new DiffusionSystem(cloud(3000, 1.5e-9), 100);
    sys.step(500);
    const a = sys.snapshot();
    sys.step(500);
    const b = sys.snapshot();
    // Doubling the time should roughly double the MSD (slope constant).
    const ratio = b.msdNm2 / a.msdNm2;
    expect(ratio).toBeGreaterThan(1.8);
    expect(ratio).toBeLessThan(2.2);
  });

  it("Stokes–Einstein gives a physically reasonable D for a nm-scale sphere", () => {
    // A ~0.18 nm radius solute in water at 25 °C → D of order 1e-9 m²/s.
    const d = stokesEinsteinM2PerS(0.18e-9, 298, WATER_VISCOSITY_PA_S);
    expect(d).toBeGreaterThan(0.5e-9);
    expect(d).toBeLessThan(3e-9);
  });

  it("Stokes–Einstein: bigger particles diffuse more slowly (D ∝ 1/r)", () => {
    const small = stokesEinsteinM2PerS(0.1e-9);
    const big = stokesEinsteinM2PerS(0.4e-9);
    expect(small).toBeGreaterThan(big);
    expect(small / big).toBeCloseTo(4, 1); // D ∝ 1/r
  });

  it("exposes diffusion scenes for the viewer", () => {
    const sys = diffusionSystemFromPreset(DIFFUSION_SCENES[1]);
    const snap = sys.snapshot();
    expect(snap.particles.length).toBe(240);
    expect(snap.particles.some((p) => p.label === "Na+")).toBe(true);
    expect(snap.particles.some((p) => p.label === "Cl-")).toBe(true);
  });
});
