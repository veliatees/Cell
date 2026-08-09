import { describe, expect, it } from "vitest";
import { LivingCell } from "../physics/cell";
import {
  assertBrowserLocalFixtureAuthority,
  browserLocalFixtureClockDisclosure,
  browserLocalFixtureEventText,
  browserLocalFixtureExecution,
  browserLocalFixtureFlowMeta,
  browserLocalFixtureFlowValue,
  browserLocalFixtureGeometryScale,
  browserLocalFixtureOrganelleMeta,
  browserLocalFixtureStatusView
} from "./browserLocalFixture";

describe("browser-local fixture authority", () => {
  it("keeps the policy fail-closed", () => {
    expect(assertBrowserLocalFixtureAuthority).not.toThrow();
  });

  it("runs only when the Python snapshot is unavailable", () => {
    expect(browserLocalFixtureExecution("loading").shouldAdvance).toBe(false);
    expect(browserLocalFixtureExecution("loaded").shouldAdvance).toBe(false);
    expect(browserLocalFixtureExecution("missing").shouldAdvance).toBe(true);
  });

  it("cannot scale canonical geometry", () => {
    expect(browserLocalFixtureGeometryScale("loaded", true, 8)).toBe(1);
    expect(browserLocalFixtureGeometryScale("loading", true, 8)).toBe(1);
    expect(browserLocalFixtureGeometryScale("missing", false, 8)).toBe(1);
    expect(browserLocalFixtureGeometryScale("missing", true, 8)).toBe(2);
  });

  it("presents local state without biological time, rate, survival, or ETA claims", () => {
    const cell = new LivingCell(undefined, 0.85, false);
    cell.step(0.04, 1);
    const snapshot = cell.snapshot();
    const execution = browserLocalFixtureExecution("missing");
    const status = browserLocalFixtureStatusView(snapshot, execution);
    const organelle = browserLocalFixtureOrganelleMeta(snapshot.organelles[0]);
    const flow = browserLocalFixtureFlowMeta(snapshot.flows[0]);
    const flowValue = browserLocalFixtureFlowValue(snapshot.flows[0]);
    const event = browserLocalFixtureEventText({
      id: 1,
      t: 3600,
      severity: "crit",
      text: "Cell is dying - ATP has collapsed"
    });
    const publicText = [
      status.executionLabel,
      status.stateLabel,
      ...status.channels,
      organelle,
      flow,
      flowValue,
      event
    ].join(" | ");

    expect(publicText).not.toMatch(/%\/h|median fate|local ETA|projected survival/i);
    expect(publicText).not.toMatch(/\b\d+(?:\.\d+)?\s*(?:ms|s|h|min)\b/i);
    expect(publicText).toContain("fixture step");
    expect(publicText).toContain("relative");
  });

  it("discloses the independent wall-clock renderer while a snapshot is active", () => {
    const text = browserLocalFixtureClockDisclosure("loaded", 960);
    expect(text).toContain("Python engine t=960 s");
    expect(text).toContain("biochemical fixture paused");
    expect(text).toContain("wall-clock only");
  });
});
