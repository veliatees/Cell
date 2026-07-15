import { describe, expect, it } from "vitest";
import {
  HUMAN_LSEC_FENESTRA_MEAN_DIAMETER_NM,
  VISUAL_ANATOMY_REQUIREMENTS,
  VISUAL_ANATOMY_SOURCES,
  membraneDomainForDirection,
  visualAnatomyCoverage,
  visualAnatomyLod
} from "./visualAnatomy";

describe("visual anatomy contract", () => {
  it("reports the explicit rubric instead of a biological realism percentage", () => {
    expect(VISUAL_ANATOMY_REQUIREMENTS.reduce((sum, item) => sum + item.weight, 0)).toBe(100);
    expect(visualAnatomyCoverage()).toBeCloseTo(93.2);
    expect(VISUAL_ANATOMY_REQUIREMENTS.find((item) => item.id === "image-validation")?.completion).toBeLessThan(1);
  });

  it("keeps the human fenestra dimension in nanometres", () => {
    expect(HUMAN_LSEC_FENESTRA_MEAN_DIAMETER_NM).toBe(105);
  });

  it("keeps every anatomy source explicit and uniquely addressable", () => {
    const sources = Object.values(VISUAL_ANATOMY_SOURCES);
    expect(new Set(sources.map((source) => source.id)).size).toBe(sources.length);
    for (const source of sources) {
      expect(source.url.startsWith("https://")).toBe(true);
      expect(source.supports.length).toBeGreaterThan(0);
    }
  });

  it("classifies normalized membrane poles deterministically", () => {
    expect(membraneDomainForDirection(1, 0.18, 0.02)).toBe("apical");
    expect(membraneDomainForDirection(-1, 0, 0)).toBe("basolateral");
    expect(membraneDomainForDirection(0, 1, 0)).toBe("lateral");
  });

  it("reduces ultrastructure load for distant and narrow views", () => {
    expect(visualAnatomyLod(18, 1200)).toBe("ultrastructure");
    expect(visualAnatomyLod(36, 1200)).toBe("cellular");
    expect(visualAnatomyLod(50, 1200)).toBe("overview");
    expect(visualAnatomyLod(45, 390)).toBe("overview");
  });
});
