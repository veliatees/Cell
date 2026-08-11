import { describe, expect, it } from "vitest";
import {
  BROWSER_RUNTIME_POLICY,
  accumulateCadencedStep,
  evaluateRenderWorkloadWindow,
  numericalGridRefreshIntervalS,
  renderSuspensionReason
} from "./renderCadence";

describe("browser render cadence policy", () => {
  it("is explicitly engineering-only", () => {
    expect(BROWSER_RUNTIME_POLICY.scientific_authority).toBe(false);
    expect(BROWSER_RUNTIME_POLICY.biological_parameter_activation).toBe(false);
    expect(BROWSER_RUNTIME_POLICY.local_fixture.public_unit_bearing_field_count).toBe(0);
    expect(BROWSER_RUNTIME_POLICY.local_fixture.projected_survival_output_enabled).toBe(false);
    expect(BROWSER_RUNTIME_POLICY.local_fixture.absolute_distance_transport_conversion_enabled).toBe(false);
    expect(BROWSER_RUNTIME_POLICY.local_fixture.production_runtime_import_enabled).toBe(false);
    expect(BROWSER_RUNTIME_POLICY.local_fixture.execute_when_python_snapshot_missing).toBe(false);
    expect(BROWSER_RUNTIME_POLICY.local_fixture.browser_local_division_enabled).toBe(false);
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

  it("contains no production fixture scheduler", () => {
    expect(Object.keys(BROWSER_RUNTIME_POLICY.clock)).toEqual([
      "maximum_visible_frame_delta_ms"
    ]);
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
