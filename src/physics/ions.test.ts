import { describe, expect, it } from "vitest";
import { NACL_BOND_LENGTH_NM } from "./constants";
import {
  DEFAULT_SETTINGS,
  dielectricFor,
  IonSimulation,
  SCENE_PRESETS,
  type SimulationSnapshot,
  type Vec3
} from "./ions";

const preset = (id: string) => {
  const found = SCENE_PRESETS.find((entry) => entry.id === id);
  if (!found) {
    throw new Error(`Missing test preset: ${id}`);
  }
  return found;
};

const isFiniteVec = (v: Vec3) =>
  Number.isFinite(v.x) && Number.isFinite(v.y) && Number.isFinite(v.z);

const snapshotIsFinite = (s: SimulationSnapshot) =>
  s.ions.every((ion) => isFiniteVec(ion.positionNm) && isFiniteVec(ion.velocityNmPerFs)) &&
  Number.isFinite(s.totalEnergyEv);

describe("IonSimulation", () => {
  it("the Na-Cl bond settles at the MEASURED gas-phase length (0.236 nm)", () => {
    // The whole point: a sourced model, not a tuned one. The repulsion parameters
    // are derived from r0 and the Pauli energy, so the equilibrium must reproduce
    // the experimental NaCl bond length to high precision.
    const sim = new IonSimulation({ ...DEFAULT_SETTINGS, dampingPerFs: 0.03 });
    for (let i = 0; i < 1500; i += 1) {
      sim.step(5);
    }
    const settled = sim.snapshot().distanceNm;
    expect(settled).toBeCloseTo(NACL_BOND_LENGTH_NM, 2); // within 0.005 nm
  });

  it("opposite charges move closer after several steps", () => {
    const sim = new IonSimulation({ ...DEFAULT_SETTINGS, thermalNoise: false });
    const start = sim.snapshot().distanceNm;

    sim.step(700);

    expect(sim.snapshot().distanceNm).toBeLessThan(start);
  });

  it("like charges repel and drift apart", () => {
    const sim = new IonSimulation(
      { ...DEFAULT_SETTINGS, dampingPerFs: 0, thermalNoise: false },
      preset("na-k")
    );
    const start = sim.snapshot().distanceNm;

    sim.step(400);

    expect(sim.snapshot().distanceNm).toBeGreaterThan(start);
  });

  it("uses water as a weaker electrostatic environment than vacuum", () => {
    expect(dielectricFor("implicit-water")).toBeGreaterThan(dielectricFor("vacuum"));

    const water = new IonSimulation({ ...DEFAULT_SETTINGS, environment: "implicit-water" }).snapshot();
    const vacuum = new IonSimulation({ ...DEFAULT_SETTINGS, environment: "vacuum" }).snapshot();

    expect(Math.abs(water.potentialEnergyEv)).toBeLessThan(Math.abs(vacuum.potentialEnergyEv));
  });

  it("Coulomb force grows as the pair gets closer (1/r^2 law)", () => {
    // Isolate Coulomb by switching Pauli repulsion off; opposite charges then
    // accelerate together and the force must increase as the distance shrinks.
    const sim = new IonSimulation({
      ...DEFAULT_SETTINGS,
      pauliRepulsion: false,
      thermalNoise: false
    });
    const wideForce = sim.snapshot().forceN;
    const wideDist = sim.snapshot().distanceNm;

    sim.step(150);
    const closerForce = sim.snapshot().forceN;
    const closerDist = sim.snapshot().distanceNm;

    expect(closerDist).toBeLessThan(wideDist);
    expect(closerForce).toBeGreaterThan(wideForce);
  });

  it("stays numerically stable over a long run (no NaN / explosion)", () => {
    const sim = new IonSimulation({ ...DEFAULT_SETTINGS, thermalNoise: true });
    sim.step(5000);
    const snap = sim.snapshot();

    expect(snapshotIsFinite(snap)).toBe(true);
    snap.ions.forEach((ion) => {
      expect(Math.abs(ion.positionNm.x)).toBeLessThan(1e4);
      expect(Math.abs(ion.positionNm.y)).toBeLessThan(1e4);
    });
  });

  it("roughly conserves total energy without damping or noise", () => {
    // Use the smooth (Coulomb-only) like-charge scene so the stiff Pauli wall
    // does not interact with the force cap; the integrator should conserve energy.
    const sim = new IonSimulation(
      { ...DEFAULT_SETTINGS, dampingPerFs: 0, thermalNoise: false, timeStepFs: 0.1 },
      preset("na-k")
    );
    const start = sim.snapshot().totalEnergyEv;

    sim.step(3000);
    const end = sim.snapshot().totalEnergyEv;

    const drift = Math.abs((end - start) / Math.max(Math.abs(start), 1e-6));
    expect(drift).toBeLessThan(0.05);
  });

  it("damping removes kinetic energy relative to a conserving run", () => {
    const damped = new IonSimulation({ ...DEFAULT_SETTINGS, dampingPerFs: 0.05, thermalNoise: false });
    const conserving = new IonSimulation({ ...DEFAULT_SETTINGS, dampingPerFs: 0, thermalNoise: false });

    damped.step(800);
    conserving.step(800);

    expect(damped.snapshot().kineticEnergyEv).toBeLessThan(conserving.snapshot().kineticEnergyEv);
  });

  it("total energy equals kinetic plus potential", () => {
    const sim = new IonSimulation();
    sim.step(120);
    const snap = sim.snapshot();
    expect(snap.totalEnergyEv).toBeCloseTo(snap.kineticEnergyEv + snap.potentialEnergyEv, 9);
  });

  it("keeps hidden electron counts in the ion species model", () => {
    const snapshot = new IonSimulation().snapshot();
    expect(snapshot.ions[0].species.electronCount).toBe(10);
    expect(snapshot.ions[1].species.electronCount).toBe(18);
  });

  it("supports multi-ion clusters with one force vector per ion", () => {
    const sim = new IonSimulation(DEFAULT_SETTINGS, preset("nacl-cluster"));
    const snap = sim.snapshot();

    expect(snap.ions.length).toBe(6);
    expect(snap.forcesN.length).toBe(6);
    const netCharge = snap.ions.reduce((sum, ion) => sum + ion.species.chargeE, 0);
    expect(netCharge).toBe(0);
  });

  it("Pauli repulsion is what prevents collapse to r=0", () => {
    const withRepulsion = new IonSimulation({ ...DEFAULT_SETTINGS, dampingPerFs: 0.04 });
    const noRepulsion = new IonSimulation({
      ...DEFAULT_SETTINGS,
      dampingPerFs: 0.04,
      pauliRepulsion: false
    });
    for (let i = 0; i < 600; i += 1) {
      withRepulsion.step(20);
      noRepulsion.step(20);
    }

    expect(withRepulsion.snapshot().distanceNm).toBeCloseTo(NACL_BOND_LENGTH_NM, 2);
    expect(noRepulsion.snapshot().distanceNm).toBeLessThan(withRepulsion.snapshot().distanceNm);
  });

  it("temperature scales the thermal kick that perturbs velocities", () => {
    const cold = new IonSimulation({
      ...DEFAULT_SETTINGS,
      dampingPerFs: 0,
      thermalNoise: true,
      temperatureK: 1
    });
    const hot = new IonSimulation({
      ...DEFAULT_SETTINGS,
      dampingPerFs: 0,
      thermalNoise: true,
      temperatureK: 600
    });

    cold.step(300);
    hot.step(300);

    expect(hot.snapshot().kineticEnergyEv).toBeGreaterThan(cold.snapshot().kineticEnergyEv);
  });
});
