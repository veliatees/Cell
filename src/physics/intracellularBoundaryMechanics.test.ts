import { describe, expect, it } from "vitest";

import {
  INTRACELLULAR_BOUNDARY_MECHANICS_CONTRACT,
  IntracellularBoundaryMechanics
} from "./intracellularBoundaryMechanics";
import {
  createMembraneSim,
  MEMBRANE_ELASTIC_AREA_STRAIN_LIMIT,
  membraneGeometryMetrics,
  stepMembrane,
  type MembraneSim
} from "./membrane_mechanics";

function faceCenterAndNormal(
  sim: MembraneSim,
  faceIndex: number
): {
  center: [number, number, number];
  normal: [number, number, number];
} {
  const offset = faceIndex * 3;
  const ia = sim.faces[offset] * 3;
  const ib = sim.faces[offset + 1] * 3;
  const ic = sim.faces[offset + 2] * 3;
  const center: [number, number, number] = [
    (sim.pos[ia] + sim.pos[ib] + sim.pos[ic]) / 3,
    (sim.pos[ia + 1] + sim.pos[ib + 1] + sim.pos[ic + 1]) / 3,
    (sim.pos[ia + 2] + sim.pos[ib + 2] + sim.pos[ic + 2]) / 3
  ];
  const abx = sim.pos[ib] - sim.pos[ia];
  const aby = sim.pos[ib + 1] - sim.pos[ia + 1];
  const abz = sim.pos[ib + 2] - sim.pos[ia + 2];
  const acx = sim.pos[ic] - sim.pos[ia];
  const acy = sim.pos[ic + 1] - sim.pos[ia + 1];
  const acz = sim.pos[ic + 2] - sim.pos[ia + 2];
  let nx = aby * acz - abz * acy;
  let ny = abz * acx - abx * acz;
  let nz = abx * acy - aby * acx;
  const inverse = 1 / (Math.hypot(nx, ny, nz) || 1);
  nx *= inverse;
  ny *= inverse;
  nz *= inverse;
  if (nx * center[0] + ny * center[1] + nz * center[2] < 0) {
    nx *= -1;
    ny *= -1;
    nz *= -1;
  }
  return { center, normal: [nx, ny, nz] };
}

function summedLoads(loads: Float32Array): [number, number, number] {
  const result: [number, number, number] = [0, 0, 0];
  for (let offset = 0; offset < loads.length; offset += 3) {
    result[0] += loads[offset];
    result[1] += loads[offset + 1];
    result[2] += loads[offset + 2];
  }
  return result;
}

describe("intracellular boundary mechanics", () => {
  it("projects an overlapping organelle inward and queues the opposite membrane load", () => {
    const sim = createMembraneSim(10, 2);
    const mechanics = new IntracellularBoundaryMechanics(sim);
    const faceIndex = 0;
    const { center: surface, normal } = faceCenterAndNormal(sim, faceIndex);
    const radius = 0.7;
    const expectedPenetration = 0.08;
    const center: [number, number, number] = [
      surface[0] - normal[0] * (radius - expectedPenetration),
      surface[1] - normal[1] * (radius - expectedPenetration),
      surface[2] - normal[2] * (radius - expectedPenetration)
    ];

    const contact = mechanics.resolveSphere(center, radius, faceIndex);
    expect(contact.contacted).toBe(true);
    expect(contact.penetrationWorld).toBeCloseTo(expectedPenetration, 4);
    const correction = [
      contact.correctedCenter[0] - center[0],
      contact.correctedCenter[1] - center[1],
      contact.correctedCenter[2] - center[2]
    ];
    expect(
      correction[0] * normal[0] +
      correction[1] * normal[1] +
      correction[2] * normal[2]
    ).toBeLessThan(0);

    const loads = new Float32Array(sim.pos.length);
    const diagnostics = mechanics.drainVertexLoads(loads);
    const membraneResultant = summedLoads(loads);
    expect(membraneResultant[0]).toBeCloseTo(
      diagnostics.dimensionlessMembraneLoadResultant[0],
      6
    );
    expect(diagnostics.frameOrganelleContactCount).toBe(1);
    expect(diagnostics.dimensionlessActionReactionResidual).toBeLessThan(1e-12);
    expect(diagnostics.physicalForceN).toBeNull();
    expect(diagnostics.healthyPhhSustainableForceN).toBeNull();
  });

  it("lets local contact deform the mesh while preserving area, volume and winding", () => {
    const sim = createMembraneSim(10, 2);
    const mechanics = new IntracellularBoundaryMechanics(sim);
    const faceIndex = 0;
    const before = faceCenterAndNormal(sim, faceIndex);
    const radius = 0.8;
    mechanics.resolveSphere(
      [
        before.center[0] - before.normal[0] * (radius - 0.2),
        before.center[1] - before.normal[1] * (radius - 0.2),
        before.center[2] - before.normal[2] * (radius - 0.2)
      ],
      radius,
      faceIndex
    );
    const loads = new Float32Array(sim.pos.length);
    mechanics.drainVertexLoads(loads);
    const step = stepMembrane(sim, 0.02, {
      vertexLoads: loads,
      loadUnit: "dimensionless_numerical",
      biologicalForceAssigned: false
    });
    const after = faceCenterAndNormal(sim, faceIndex);
    const displacementAlongNormal =
      (after.center[0] - before.center[0]) * before.normal[0] +
      (after.center[1] - before.center[1]) * before.normal[1] +
      (after.center[2] - before.center[2]) * before.normal[2];
    const metrics = membraneGeometryMetrics(sim);

    expect(displacementAlongNormal).toBeGreaterThan(0);
    expect(step.externalLoadApplied).toBe(true);
    expect(step.physicalForceN).toBeNull();
    expect(metrics.invertedFaces).toBe(0);
    expect(metrics.volumeRatio).toBeCloseTo(1, 3);
    expect(metrics.areaRatio).toBeLessThanOrEqual(
      1 + MEMBRANE_ELASTIC_AREA_STRAIN_LIMIT + 1e-4
    );
  });

  it("recovers a body center that numerically crossed outside the membrane", () => {
    const sim = createMembraneSim(10, 2);
    const mechanics = new IntracellularBoundaryMechanics(sim);
    const faceIndex = 3;
    const { center: surface, normal } = faceCenterAndNormal(sim, faceIndex);
    const radius = 0.4;
    const outsideCenter: [number, number, number] = [
      surface[0] + normal[0] * 0.05,
      surface[1] + normal[1] * 0.05,
      surface[2] + normal[2] * 0.05
    ];
    const contact = mechanics.resolveSphere(
      outsideCenter,
      radius,
      faceIndex
    );
    const correctedSide =
      (contact.correctedCenter[0] - surface[0]) * normal[0] +
      (contact.correctedCenter[1] - surface[1]) * normal[1] +
      (contact.correctedCenter[2] - surface[2]) * normal[2];

    expect(contact.contacted).toBe(true);
    expect(correctedSide).toBeLessThan(-radius);
  });

  it("removes uniform pressure and balances nonuniform cytosol traction", () => {
    const sim = createMembraneSim(10, 1);
    const mechanics = new IntracellularBoundaryMechanics(sim);
    const faceCount = sim.faces.length / 3;
    const loads = new Float32Array(sim.pos.length);

    mechanics.queueDimensionlessCytosolPressure(
      new Float64Array(faceCount).fill(3)
    );
    const uniform = mechanics.drainVertexLoads(loads);
    expect(Math.max(...Array.from(loads, Math.abs))).toBeLessThan(1e-10);
    expect(uniform.dimensionlessCytosolPressureRms).toBeLessThan(1e-12);
    expect(uniform.cumulativeCytosolPressureUpdateCount).toBe(1);

    const pressures = new Float64Array(faceCount);
    for (let face = 0; face < faceCount; face += 1) {
      pressures[face] = faceCenterAndNormal(sim, face).center[0] / sim.radius;
    }
    mechanics.queueDimensionlessCytosolPressure(pressures);
    const nonuniform = mechanics.drainVertexLoads(loads);
    expect(nonuniform.dimensionlessCytosolPressureRms).toBeGreaterThan(0);
    expect(nonuniform.cytosolPressureFaceCount).toBe(faceCount);
    expect(nonuniform.cumulativeCytosolPressureUpdateCount).toBe(2);
    expect(nonuniform.maximumDimensionlessCytosolPressureRms).toBeGreaterThan(0);
    expect(nonuniform.dimensionlessActionReactionResidual).toBeLessThan(1e-12);
    expect(nonuniform.physicalPressurePa).toBeNull();
    expect(nonuniform.healthyPhhSustainablePressurePa).toBeNull();
  });

  it("keeps the PHH force and sustainability claims fail-closed", () => {
    expect(
      INTRACELLULAR_BOUNDARY_MECHANICS_CONTRACT.actionReactionBalanced
    ).toBe(true);
    expect(
      INTRACELLULAR_BOUNDARY_MECHANICS_CONTRACT.biologicalForceAssigned
    ).toBe(false);
    expect(
      INTRACELLULAR_BOUNDARY_MECHANICS_CONTRACT.biologicalPressureAssigned
    ).toBe(false);
    expect(
      INTRACELLULAR_BOUNDARY_MECHANICS_CONTRACT
        .quantitativeHealthyPhhMechanicsEnabled
    ).toBe(false);
    expect(
      INTRACELLULAR_BOUNDARY_MECHANICS_CONTRACT
        .rendererStagingLoadAcceptedAsDimensionlessGeometryInput
    ).toBe(true);
    expect(
      INTRACELLULAR_BOUNDARY_MECHANICS_CONTRACT
        .rendererStagingLoadCanClaimBiologicalMechanics
    ).toBe(false);
  });
});
