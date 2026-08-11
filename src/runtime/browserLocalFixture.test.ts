import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import {
  assertBrowserLocalFixtureAuthority,
  browserLocalFixtureClockDisclosure,
  browserLocalFixtureElapsedLabel,
  browserLocalFixtureExecution
} from "./browserLocalFixture";

describe("browser-local fixture production firewall", () => {
  it("keeps the policy fail-closed", () => {
    expect(assertBrowserLocalFixtureAuthority).not.toThrow();
  });

  it("never executes in a production snapshot state", () => {
    expect(browserLocalFixtureExecution("loading").shouldAdvance).toBe(false);
    expect(browserLocalFixtureExecution("loaded").shouldAdvance).toBe(false);
    expect(browserLocalFixtureExecution("missing").shouldAdvance).toBe(false);
    expect(browserLocalFixtureExecution("missing").label).toContain(
      "no biological state substituted"
    );
  });

  it("discloses engine time without inventing a fallback clock", () => {
    expect(browserLocalFixtureClockDisclosure("loaded", 960)).toContain(
      "Python engine t=960 s"
    );
    expect(browserLocalFixtureClockDisclosure("loaded", 960)).toContain(
      "biological execution disabled"
    );
    expect(browserLocalFixtureElapsedLabel("missing", null)).toBe(
      "snapshot unavailable"
    );
  });

  it("keeps the test fixture and browser-local division out of main", () => {
    const mainSource = readFileSync(new URL("../main.ts", import.meta.url), "utf8");
    expect(mainSource).not.toContain("new NormalizedCellFixture");
    expect(mainSource).not.toContain("resolveVisualDivision");
    expect(mainSource).not.toContain("visualCytokinesisFailureRisk");
    expect(mainSource).not.toContain("data-action=\"divide\"");
  });
});
