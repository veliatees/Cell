import { describe, expect, it } from "vitest";
import {
  BROWSER_RUNTIME_POLICY,
  accumulateCadencedStep,
  evaluateRenderWorkloadWindow,
  numericalGridRefreshIntervalS,
  renderSuspensionReason,
  visualSimulationStepPlan
} from "./renderCadence";

describe("browser render cadence policy", () => {
  it("is explicitly engineering-only", () => {
    expect(BROWSER_RUNTIME_POLICY.scientific_authority).toBe(false);
    expect(BROWSER_RUNTIME_POLICY.biological_parameter_activation).toBe(false);
  });

  it("suspends hidden and off-viewport rendering", () => {
    expect(renderSuspensionReason(true, true)).toBe("document_hidden");
    expect(renderSuspensionReason(false, false)).toBe(
      "viewport_not_intersecting"
    );
    expect(renderSuspensionReason(false, true)).toBeNull();
  });

  it("consumes accumulated visual-fluid time only at cadence boundaries", () => {
    const first = accumulateCadencedStep(0, 0.016, 1 / 30);
    expect(first.stepDeltaS).toBeNull();
    const second = accumulateCadencedStep(
      first.accumulatedS,
      0.018,
      1 / 30
    );
    expect(second.accumulatedS).toBe(0);
    expect(second.stepDeltaS).toBeCloseTo(0.034);
  });

  it("forces a fluid update when geometry changes", () => {
    expect(accumulateCadencedStep(0.01, 0.005, 1 / 30, true)).toEqual({
      accumulatedS: 0,
      stepDeltaS: 0.015
    });
  });

  it("reduces projected-grid refresh work with the quality tier", () => {
    expect(numericalGridRefreshIntervalS("full")).toBe(0.25);
    expect(numericalGridRefreshIntervalS("balanced")).toBe(0.5);
    expect(numericalGridRefreshIntervalS("essential")).toBe(1);
  });

  it("preserves visual-cell elapsed time across lower frame rates", () => {
    const plan = visualSimulationStepPlan(1 / 15);
    expect(plan.totalSimulationS).toBeCloseTo(1 / 3);
    expect(plan.stepS * plan.iterations).toBeCloseTo(plan.totalSimulationS);
    expect(plan.stepS).toBeLessThanOrEqual(
      BROWSER_RUNTIME_POLICY.clock.maximum_visual_cell_substep_s
    );
  });

  it("degrades only after consecutive total-work breaches", () => {
    const first = evaluateRenderWorkloadWindow("full", 0, {
      averageWorkMs: 16,
      longFrameRatio: 0.02
    });
    expect(first).toEqual({
      tier: "full",
      consecutiveBreachWindows: 1,
      degraded: false
    });
    const second = evaluateRenderWorkloadWindow(
      "full",
      first.consecutiveBreachWindows,
      {
        averageWorkMs: 16,
        longFrameRatio: 0.02
      }
    );
    expect(second).toEqual({
      tier: "balanced",
      consecutiveBreachWindows: 0,
      degraded: true
    });
  });

  it("clears a workload breach streak after a healthy window", () => {
    const decision = evaluateRenderWorkloadWindow("balanced", 1, {
      averageWorkMs: 8,
      longFrameRatio: 0
    });
    expect(decision.consecutiveBreachWindows).toBe(0);
    expect(decision.tier).toBe("balanced");
    expect(decision.degraded).toBe(false);
  });
});
