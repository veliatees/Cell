import { describe, expect, it } from "vitest";
import {
  INTRACELLULAR_TRANSPORT_DISPLAY_CONTRACT,
  classifyTransportMode,
  deterministicDisplayJitter,
  dimensionlessRouteProgress
} from "./transportModes";

describe("transport-mode renderer contract", () => {
  it("keeps aqueous motion separate from active track cargo", () => {
    expect(classifyTransportMode("diffusion")).toBe("passive_aqueous_field");
    expect(classifyTransportMode("motor")).toBe("active_track_cargo");
    expect(classifyTransportMode("vesicle")).toBe("active_track_cargo");
    expect(classifyTransportMode("autophagy")).toBe("active_track_cargo");
    expect(classifyTransportMode("carrier")).toBe("membrane_crossing_display");
    expect(classifyTransportMode("pore")).toBe("membrane_crossing_display");
    expect(classifyTransportMode("signal")).toBe("signal_display");
  });

  it("advances only dimensionless display progress", () => {
    expect(dimensionlessRouteProgress(2, 0.25, 0.75, 2)).toEqual({
      cycle: 1,
      phase01: 0.75
    });
    expect(() => dimensionlessRouteProgress(-1, 0.25, 0)).toThrow(RangeError);
  });

  it("is deterministic and keeps display jitter inside its declared bound", () => {
    const first = deterministicDisplayJitter(41, 2.75, 0.3);
    const second = deterministicDisplayJitter(41, 2.75, 0.3);
    expect(first).toEqual(second);
    expect(Math.hypot(...first)).toBeLessThanOrEqual(0.3 + 1e-12);
    expect(deterministicDisplayJitter(42, 2.75, 0.3)).not.toEqual(first);
  });

  it("cannot masquerade as a PHH transport calibration", () => {
    expect(INTRACELLULAR_TRANSPORT_DISPLAY_CONTRACT.biologicalVelocityAssigned).toBe(false);
    expect(INTRACELLULAR_TRANSPORT_DISPLAY_CONTRACT.biologicalDiffusivityAssigned).toBe(false);
    expect(INTRACELLULAR_TRANSPORT_DISPLAY_CONTRACT.biologicalPauseOrReversalRateAssigned).toBe(false);
    expect(INTRACELLULAR_TRANSPORT_DISPLAY_CONTRACT.healthyPhhMotorRateBound).toBe(false);
    expect(INTRACELLULAR_TRANSPORT_DISPLAY_CONTRACT.reactionCouplingEnabled).toBe(false);
  });
});
