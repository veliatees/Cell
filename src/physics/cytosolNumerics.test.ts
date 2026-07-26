import { describe, expect, it } from "vitest";
import { applyVolumePreservingFluidDeformation } from "./intracellularFluid";
import {
  CYTOSOL_NUMERICAL_CONTRACT,
  ConservativePassiveScalar3D,
  CytosolProjectionGrid,
  DynamicCytosolObstacleField,
  capsuleObstacleBetween,
  inverseVolumePreservingPoint,
  type CytosolObstacle
} from "./cytosolNumerics";

describe("dimensionless cytosol numerical kernel", () => {
  it("uses analytic moving sphere, ellipsoid, capsule and box boundaries", () => {
    const field = new DynamicCytosolObstacleField(1);
    const obstacles: CytosolObstacle[] = [
      { id: "sphere", kind: "sphere", center: [0, 0, 0], radius: 1 },
      { id: "ellipsoid", kind: "ellipsoid", center: [4, 0, 0], radii: [2, 1, 0.5] },
      { id: "capsule", kind: "capsule", center: [-4, 0, 0], radius: 0.5, halfLength: 1.5 },
      {
        id: "box",
        kind: "box",
        center: [0, 4, 0],
        orientation: [0, 0, Math.sin(Math.PI / 4), Math.cos(Math.PI / 4)],
        halfExtents: [1.5, 0.25, 0.5]
      }
    ];
    field.setObstacles(obstacles, 0);

    expect(field.collides(0.9, 0, 0)).toBe(true);
    expect(field.collides(1.1, 0, 0)).toBe(false);
    expect(field.collides(5.8, 0, 0)).toBe(true);
    expect(field.collides(4, 0, 0.6)).toBe(false);
    expect(field.collides(-4, 1.8, 0)).toBe(true);
    expect(field.collides(-4, 2.1, 0)).toBe(false);
    expect(field.collides(0, 5.3, 0)).toBe(true);
    expect(field.collides(0.4, 5.3, 0)).toBe(false);

    field.setObstacles(obstacles.map((obstacle) => (
      obstacle.id === "sphere" ? { ...obstacle, center: [0.2, 0, 0] as const } : obstacle
    )), 0.1);
    const velocity = new Float32Array(3);
    expect(field.solidVelocityAt(0.2, 0, 0, velocity)).toBe(true);
    expect(velocity[0]).toBeCloseTo(2, 6);
    expect(velocity[1]).toBe(0);
  });

  it("derives rigid rotational boundary velocity from quaternion motion", () => {
    const field = new DynamicCytosolObstacleField(1);
    field.setObstacles([
      {
        id: "rotating-capsule",
        kind: "capsule",
        center: [0, 0, 0],
        orientation: [0, 0, 0, 1],
        radius: 0.4,
        halfLength: 1.2
      }
    ], 0);
    const halfTurnAboutZ = Math.sin(-Math.PI / 4);
    field.setObstacles([
      {
        id: "rotating-capsule",
        kind: "capsule",
        center: [0, 0, 0],
        orientation: [0, 0, halfTurnAboutZ, Math.cos(-Math.PI / 4)],
        radius: 0.4,
        halfLength: 1.2
      }
    ], 0.5);

    const velocity = new Float32Array(3);
    expect(field.solidVelocityAt(0.8, 0, 0, velocity)).toBe(true);
    expect(velocity[0]).toBeCloseTo(0, 6);
    expect(velocity[1]).toBeCloseTo(-Math.PI * 0.8, 5);
    expect(velocity[2]).toBeCloseTo(0, 6);
    expect(field.rotatingCount).toBe(1);
  });

  it("treats opposite quaternion signs as the same orientation", () => {
    const field = new DynamicCytosolObstacleField(1);
    field.setObstacles([
      { id: "sign-stable", kind: "ellipsoid", center: [0, 0, 0], orientation: [0, 0, 0, 1], radii: [1, 2, 1] }
    ], 0);
    field.setObstacles([
      { id: "sign-stable", kind: "ellipsoid", center: [0, 0, 0], orientation: [0, 0, 0, -1], radii: [1, 2, 1] }
    ], 0.1);

    const velocity = new Float32Array(3);
    expect(field.solidVelocityAt(0, 1, 0, velocity)).toBe(true);
    expect(Array.from(velocity)).toEqual([0, 0, 0]);
    expect(field.rotatingCount).toBe(0);
  });

  it("inverts the exact volume-preserving membrane map", () => {
    const deformation = { normal: [1, 2, -1] as const, axialScale: 0.84 };
    const mapped = new Float32Array(3);
    const restored = new Float32Array(3);
    applyVolumePreservingFluidDeformation(2.5, -1.2, 0.8, deformation, mapped);
    inverseVolumePreservingPoint(mapped[0], mapped[1], mapped[2], deformation, restored);

    expect(restored[0]).toBeCloseTo(2.5, 5);
    expect(restored[1]).toBeCloseTo(-1.2, 5);
    expect(restored[2]).toBeCloseTo(0.8, 5);
  });

  it("builds a capsule chain segment on the supplied renderer centerline", () => {
    const obstacle = capsuleObstacleBetween(
      "er-segment",
      [1, -2, 0.5],
      [4, -2, 4.5],
      0.2
    );
    const field = new DynamicCytosolObstacleField(1);
    field.setObstacles([obstacle], 0);

    expect(obstacle.center).toEqual([2.5, -2, 2.5]);
    expect(obstacle.halfLength).toBeCloseTo(2.5, 12);
    expect(field.collides(2.5, -2, 2.5)).toBe(true);
    expect(field.collides(2.5, -1.7, 2.5)).toBe(false);
  });

  it("projects a seeded bounded field and reports numerical divergence", () => {
    const first = new CytosolProjectionGrid({
      resolution: 16,
      halfExtent: 6,
      seed: 91,
      radiusAtDirection: () => 5,
      projectionIterations: 36
    });
    const second = new CytosolProjectionGrid({
      resolution: 16,
      halfExtent: 6,
      seed: 91,
      radiusAtDirection: () => 5,
      projectionIterations: 36
    });

    first.step(1 / 30, null);
    second.step(1 / 30, null);
    const diagnostics = first.diagnostics();

    expect(Array.from(first.velocityX)).toEqual(Array.from(second.velocityX));
    expect(diagnostics.fluidCellCount).toBeGreaterThan(0);
    expect(diagnostics.solidCellCount).toBeGreaterThan(0);
    expect(diagnostics.rotatingObstacleCount).toBe(0);
    expect(diagnostics.divergenceRmsAfter).toBeLessThan(diagnostics.divergenceRmsBefore);
    expect(diagnostics.divergenceMaxAfter).toBeGreaterThanOrEqual(0);
    expect(diagnostics.biologicalUnitsAssigned).toBe(false);
  });

  it("rebuilds the fluid domain around moving organelle volumes", () => {
    const obstacles = new DynamicCytosolObstacleField(1);
    obstacles.setObstacles([
      { id: "nucleus", kind: "ellipsoid", center: [0, 0, 0], radii: [2.2, 1.8, 1.6] }
    ], 0);
    const grid = new CytosolProjectionGrid({
      resolution: 14,
      halfExtent: 6,
      seed: 4,
      radiusAtDirection: () => 5
    });
    grid.step(1 / 60, null, obstacles);
    const withObstacle = grid.diagnostics();

    obstacles.setObstacles([], 1 / 60);
    grid.step(1 / 60, null, obstacles);
    const withoutObstacle = grid.diagnostics();

    expect(withObstacle.obstacleCount).toBe(1);
    expect(withObstacle.fluidCellCount).toBeLessThan(withoutObstacle.fluidCellCount);
  });

  it("conserves passive-scalar mass across no-flux fluid faces", () => {
    const grid = new CytosolProjectionGrid({
      resolution: 12,
      halfExtent: 5,
      seed: 8,
      radiusAtDirection: () => 4.4,
      visualModeCount: 0
    });
    grid.step(1 / 60, null);
    const scalar = new ConservativePassiveScalar3D(grid, {
      id: "numerical_validation_pulse",
      dimensionlessDiffusivity: 0.04
    });
    scalar.initialize((x, y, z) => Math.hypot(x + 1, y, z) < 1.2 ? 1 : 0);
    const before = scalar.totalMass();

    scalar.step(0.5);
    const after = scalar.totalMass();

    expect(after).toBeCloseTo(before, 5);
    expect(Math.min(...scalar.values)).toBeGreaterThanOrEqual(0);
    expect(Math.max(...scalar.values)).toBeLessThan(1);
  });

  it("conservatively remaps scalar mass when a moving organelle changes the fluid mask", () => {
    const obstacles = new DynamicCytosolObstacleField(1);
    obstacles.setObstacles([
      { id: "moving-organelle", kind: "sphere", center: [-1.8, 0, 0], radius: 1.35 }
    ], 0);
    const grid = new CytosolProjectionGrid({
      resolution: 16,
      halfExtent: 6,
      seed: 12,
      radiusAtDirection: () => 5,
      visualModeCount: 0
    });
    grid.step(1 / 60, null, obstacles);
    const scalar = new ConservativePassiveScalar3D(grid, {
      id: "moving_domain_validation_pulse",
      dimensionlessDiffusivity: 0
    });
    scalar.initialize(() => 1);
    const before = scalar.totalMass();

    obstacles.setObstacles([
      { id: "moving-organelle", kind: "sphere", center: [1.8, 0, 0], radius: 1.35 }
    ], 0.1);
    grid.step(0.1, null, obstacles);
    scalar.step(0);

    const after = scalar.totalMass();
    const diagnostics = scalar.domainRemapDiagnostics();
    expect(diagnostics.remapCount).toBe(1);
    expect(diagnostics.displacedCellCount).toBeGreaterThan(0);
    expect(diagnostics.exposedCellCount).toBeGreaterThan(0);
    expect(diagnostics.displacedDimensionlessMass).toBeGreaterThan(0);
    expect(diagnostics.redistributedDimensionlessMass).toBeCloseTo(
      diagnostics.displacedDimensionlessMass,
      12
    );
    expect(diagnostics.absoluteMassResidual).toBeLessThan(1e-10);
    expect(after).toBeCloseTo(before, 12);
    expect(Math.min(...scalar.values)).toBeGreaterThanOrEqual(0);
  });

  it("conserves scalar mass around a translating and rotating compound boundary", () => {
    const obstacles = new DynamicCytosolObstacleField(0.75);
    obstacles.setObstacles([
      {
        id: "golgi-envelope",
        kind: "box",
        center: [-1.2, 0, 0],
        orientation: [0, 0, 0, 1],
        halfExtents: [1.1, 0.45, 0.8]
      },
      capsuleObstacleBetween("er-branch", [0.2, -1.8, 0], [0.2, 1.8, 0], 0.28)
    ], 0);
    const grid = new CytosolProjectionGrid({
      resolution: 18,
      halfExtent: 6,
      seed: 44,
      radiusAtDirection: () => 5.2,
      visualModeCount: 0
    });
    grid.step(1 / 60, null, obstacles);
    const scalar = new ConservativePassiveScalar3D(grid, {
      id: "compound_boundary_validation_pulse",
      dimensionlessDiffusivity: 0
    });
    scalar.initialize((x) => x < 0 ? 0.8 : 0.2);
    const before = scalar.totalMass();

    const quarterTurn = Math.PI / 4;
    obstacles.setObstacles([
      {
        id: "golgi-envelope",
        kind: "box",
        center: [1.2, 0, 0],
        orientation: [0, 0, Math.sin(quarterTurn), Math.cos(quarterTurn)],
        halfExtents: [1.1, 0.45, 0.8]
      },
      {
        ...capsuleObstacleBetween("er-branch", [-1.8, 0.2, 0], [1.8, 0.2, 0], 0.28)
      }
    ], 0.2);
    grid.step(0.2, null, obstacles);
    scalar.step(0);

    const diagnostics = scalar.domainRemapDiagnostics();
    expect(obstacles.rotatingCount).toBe(2);
    expect(diagnostics.displacedCellCount).toBeGreaterThan(0);
    expect(diagnostics.exposedCellCount).toBeGreaterThan(0);
    expect(diagnostics.absoluteMassResidual).toBeLessThan(1e-10);
    expect(scalar.totalMass()).toBeCloseTo(before, 11);
    expect(Math.min(...scalar.values)).toBeGreaterThanOrEqual(0);
  });

  it("retains a membrane thinner than one grid cell with conservative subgrid sampling", () => {
    const obstacles = new DynamicCytosolObstacleField(1);
    obstacles.setObstacles([
      {
        id: "subgrid-cisterna",
        kind: "box",
        center: [0, 0.23, 0],
        halfExtents: [2, 0.015, 1],
        boundarySampling: "conservative_subgrid"
      }
    ], 0);
    const grid = new CytosolProjectionGrid({
      resolution: 12,
      halfExtent: 6,
      seed: 55,
      radiusAtDirection: () => 5.5,
      visualModeCount: 0
    });
    grid.step(1 / 60, null, obstacles);
    const diagnostics = grid.diagnostics();

    expect(obstacles.collides(0, 0.5, 0)).toBe(false);
    expect(diagnostics.subgridObstacleCount).toBe(1);
    expect(diagnostics.subgridInterceptedCellCount).toBeGreaterThan(0);
    expect(diagnostics.fractionalObstacleCellCount).toBeGreaterThan(0);
    expect(diagnostics.dimensionlessObstacleVolumeEstimate).toBeGreaterThan(0);
  });

  it("reduces thin-boundary volume error under deterministic grid refinement", () => {
    const exactVolume = 3.4 * 0.12 * 2.2;
    const estimate = (resolution: number) => {
      const obstacles = new DynamicCytosolObstacleField(0.5);
      obstacles.setObstacles([
        {
          id: "refined-cisterna",
          kind: "box",
          center: [0, 0.23, 0],
          halfExtents: [1.7, 0.06, 1.1],
          boundarySampling: "conservative_subgrid"
        }
      ], 0);
      const grid = new CytosolProjectionGrid({
        resolution,
        halfExtent: 4,
        seed: 91,
        radiusAtDirection: () => 3.8,
        visualModeCount: 0
      });
      grid.step(0, null, obstacles);
      return grid.obstacleVolumeEstimate();
    };
    const coarseError = Math.abs(estimate(12) - exactVolume);
    const mediumError = Math.abs(estimate(24) - exactVolume);
    const fineError = Math.abs(estimate(48) - exactVolume);

    expect(mediumError).toBeLessThan(coarseError);
    expect(fineError).toBeLessThan(mediumError);
  });

  it("keeps biological units and reaction feedback disabled", () => {
    expect(CYTOSOL_NUMERICAL_CONTRACT.biologicalVelocityClaim).toBe(false);
    expect(CYTOSOL_NUMERICAL_CONTRACT.biologicalPressureClaim).toBe(false);
    expect(CYTOSOL_NUMERICAL_CONTRACT.biologicalDiffusivityClaim).toBe(false);
    expect(CYTOSOL_NUMERICAL_CONTRACT.movingDomainRemap).toContain("deterministic_nearest_fluid");
    expect(CYTOSOL_NUMERICAL_CONTRACT.thinBoundaryTreatment).toContain("conservative_subgrid");
    expect(CYTOSOL_NUMERICAL_CONTRACT.subgridQuadratureSamplesPerCell).toBe(8);
    expect(CYTOSOL_NUMERICAL_CONTRACT.subgridGridConvergenceTested).toBe(true);
    expect(CYTOSOL_NUMERICAL_CONTRACT.quantitativePoroelasticSolver).toBe(false);
    expect(CYTOSOL_NUMERICAL_CONTRACT.reactionCouplingEnabled).toBe(false);
    expect(CYTOSOL_NUMERICAL_CONTRACT.membranePressureFeedbackEnabled).toBe(false);
  });
});
