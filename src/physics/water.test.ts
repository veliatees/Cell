import { describe, expect, it } from "vitest";
import { SPCE_WATER } from "./constants";
import { SPCE_SITES, spceDipoleDebye, WaterSystem, type Vec3 } from "./water";

const dist = (a: Vec3, b: Vec3) =>
  Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2);

describe("SPC/E water model", () => {
  it("reproduces the SPC/E dipole moment (2.35 D)", () => {
    expect(spceDipoleDebye()).toBeCloseTo(SPCE_WATER.dipoleDebye, 2);
  });

  it("is electrically neutral", () => {
    const total = SPCE_SITES.reduce((sum, s) => sum + s.chargeE, 0);
    expect(total).toBeCloseTo(0, 6);
  });

  it("has the correct O-H bond length and H-O-H angle", () => {
    const [o, h1, h2] = SPCE_SITES.map((s) => s.offset);
    const oh1 = dist(o, h1);
    const oh2 = dist(o, h2);
    expect(oh1).toBeCloseTo(SPCE_WATER.bondLengthOhNm, 6);
    expect(oh2).toBeCloseTo(SPCE_WATER.bondLengthOhNm, 6);

    const v1 = { x: h1.x - o.x, y: h1.y - o.y, z: h1.z - o.z };
    const v2 = { x: h2.x - o.x, y: h2.y - o.y, z: h2.z - o.z };
    const cos = (v1.x * v2.x + v1.y * v2.y + v1.z * v2.z) / (oh1 * oh2);
    const angleDeg = (Math.acos(cos) * 180) / Math.PI;
    expect(angleDeg).toBeCloseTo(SPCE_WATER.angleHohDeg, 1);
  });

  it("keeps the molecule perfectly rigid while translating and spinning", () => {
    const sys = new WaterSystem([
      {
        comNm: { x: 0, y: 0, z: 0 },
        velNmPerFs: { x: 0.001, y: 0, z: 0 },
        angVelBodyRadPerFs: { x: 0.02, y: 0.01, z: 0 }
      }
    ]);
    const before = sys.snapshot().sitePositionsNm[0];
    const oh0 = dist(before[0], before[1]);
    const hh0 = dist(before[1], before[2]);

    sys.step(4000);
    const after = sys.snapshot().sitePositionsNm[0];

    expect(dist(after[0], after[1])).toBeCloseTo(oh0, 6);
    expect(dist(after[1], after[2])).toBeCloseTo(hh0, 6);
  });

  it("conserves energy for a freely spinning molecule (NVE)", () => {
    const sys = new WaterSystem([
      {
        comNm: { x: 0, y: 0, z: 0 },
        velNmPerFs: { x: 0.0005, y: 0, z: 0 },
        angVelBodyRadPerFs: { x: 0.03, y: 0, z: 0 }
      }
    ]);
    const start = sys.snapshot().totalEnergyEv;
    sys.step(8000);
    const end = sys.snapshot().totalEnergyEv;
    // A single isolated molecule has no potential energy, so KE must be constant.
    expect(end).toBeCloseTo(start, 6);
  });

  it("two molecules attract into a hydrogen-bonded dimer at a realistic O-O distance", () => {
    // Start ~0.45 nm apart, second molecule rotated so an H points toward the first.
    const sys = new WaterSystem(
      [
        { comNm: { x: -0.225, y: 0, z: 0 } },
        {
          comNm: { x: 0.225, y: 0, z: 0 },
          orientation: { w: Math.cos(Math.PI / 2), x: 0, y: Math.sin(Math.PI / 2), z: 0 }
        }
      ],
      0.25,
      0.01 // gentle damping so the dimer settles
    );
    const startOO = dist(sys.snapshot().sitePositionsNm[0][0], sys.snapshot().sitePositionsNm[1][0]);

    for (let i = 0; i < 400; i += 1) {
      sys.step(20);
    }
    const snap = sys.snapshot();
    const endOO = dist(snap.sitePositionsNm[0][0], snap.sitePositionsNm[1][0]);

    // They should bind (come closer) and settle near the H-bond O–O distance (~0.28 nm).
    expect(endOO).toBeLessThan(startOO);
    expect(endOO).toBeGreaterThan(0.24);
    expect(endOO).toBeLessThan(0.34);
    // Bound state has negative interaction energy.
    expect(snap.potentialEnergyEv).toBeLessThan(0);
  });

  it("conserves energy for an interacting pair without damping", () => {
    const sys = new WaterSystem(
      [
        { comNm: { x: -0.18, y: 0, z: 0 } },
        {
          comNm: { x: 0.18, y: 0, z: 0 },
          orientation: { w: Math.cos(Math.PI / 2), x: 0, y: Math.sin(Math.PI / 2), z: 0 }
        }
      ],
      0.1
    );
    const start = sys.snapshot().totalEnergyEv;
    sys.step(6000);
    const end = sys.snapshot().totalEnergyEv;
    const drift = Math.abs((end - start) / Math.max(Math.abs(start), 1e-6));
    expect(drift).toBeLessThan(0.05);
  });
});
