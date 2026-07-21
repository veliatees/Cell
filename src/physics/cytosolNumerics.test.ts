import { describe, expect, it } from "vitest";
import { applyVolumePreservingFluidDeformation } from "./intracellularFluid";
import {
  CYTOSOL_NUMERICAL_CONTRACT,
  ConservativePassiveScalar3D,
  CytosolProjectionGrid,
  DynamicCytosolObstacleField,
  inverseVolumePreservingPoint,
  type CytosolObstacle
} from "./cytosolNumerics";

describe("dimensionless cytosol numerical kernel", () => {
  it("uses analytic moving sphere, ellipsoid and capsule boundaries", () => {
    const field = new DynamicCytosolObstacleField(1);
    const obstacles: CytosolObstacle[] = [
      { id: "sphere", kind: "sphere", center: [0, 0, 0], radius: 1 },
      { id: "ellipsoid", kind: "ellipsoid", center: [4, 0, 0], radii: [2, 1, 0.5] },
      { id: "capsule", kind: "capsule", center: [-4, 0, 0], radius: 0.5, halfLength: 1.5 }
    ];
    field.setObstacles(obstacles, 0);

    expect(field.collides(0.9, 0, 0)).toBe(true);
    expect(field.collides(1.1, 0, 0)).toBe(false);
    expect(field.collides(5.8, 0, 0)).toBe(true);
    expect(field.collides(4, 0, 0.6)).toBe(false);
    expect(field.collides(-4, 1.8, 0)).toBe(true);
    expect(field.collides(-4, 2.1, 0)).toBe(false);

    field.setObstacles(obstacles.map((obstacle) => (
      obstacle.id === "sphere" ? { ...obstacle, center: [0.2, 0, 0] as const } : obstacle
    )), 0.1);
    const velocity = new Float32Array(3);
    expect(field.solidVelocityAt(0.2, 0, 0, velocity)).toBe(true);
    expect(velocity[0]).toBeCloseTo(2, 6);
    expect(velocity[1]).toBe(0);
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

  it("keeps biological units and reaction feedback disabled", () => {
    expect(CYTOSOL_NUMERICAL_CONTRACT.biologicalVelocityClaim).toBe(false);
    expect(CYTOSOL_NUMERICAL_CONTRACT.biologicalPressureClaim).toBe(false);
    expect(CYTOSOL_NUMERICAL_CONTRACT.biologicalDiffusivityClaim).toBe(false);
    expect(CYTOSOL_NUMERICAL_CONTRACT.quantitativePoroelasticSolver).toBe(false);
    expect(CYTOSOL_NUMERICAL_CONTRACT.reactionCouplingEnabled).toBe(false);
    expect(CYTOSOL_NUMERICAL_CONTRACT.membranePressureFeedbackEnabled).toBe(false);
  });
});
