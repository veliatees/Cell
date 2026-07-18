import { describe, expect, it } from "vitest";
import {
  HEPATOCYTE_CANONICAL_POLARITY_AXIS,
  HEPATOCYTE_REFERENCE_EQUIVALENT_DIAMETER_UM,
  HEPATOCYTE_RENDER_RADIUS_WORLD,
  HEPATOCYTE_RENDER_UM_PER_WORLD_UNIT,
  HISTORICAL_IN_SITU_PHH_MEAN_VOLUME_UM3,
  HUMAN_NC_3D_HEPATOCYTE_MEDIAN_VOLUME_UM3,
  HUMAN_NC_3D_LIPID_DROPLET_VOLUME_FRACTION,
  HUMAN_LSEC_FENESTRA_MEAN_DIAMETER_NM,
  ISOLATED_PHH_MEDIAN_DIAMETER_UM,
  VISUAL_ANATOMY_REQUIREMENTS,
  VISUAL_ANATOMY_SOURCES,
  membraneDomainForDirection,
  normalizeDisplaySphereScalesToVolumeFraction,
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
    expect(HISTORICAL_IN_SITU_PHH_MEAN_VOLUME_UM3).toBe(2850);
    expect(HUMAN_NC_3D_HEPATOCYTE_MEDIAN_VOLUME_UM3).toBe(5657.07116);
    expect(ISOLATED_PHH_MEDIAN_DIAMETER_UM).toBe(18.4);
    expect(2 * HEPATOCYTE_RENDER_RADIUS_WORLD * HEPATOCYTE_RENDER_UM_PER_WORLD_UNIT)
      .toBeCloseTo(HEPATOCYTE_REFERENCE_EQUIVALENT_DIAMETER_UM, 12);
  });

  it("normalizes renderer lipid samples to the measured aggregate NC volume fraction", () => {
    const baseRadius = 0.5;
    const cellRadius = HEPATOCYTE_RENDER_RADIUS_WORLD;
    const scales = normalizeDisplaySphereScalesToVolumeFraction(
      [0.85, 0.9, 1, 1.1, 1.15],
      baseRadius,
      cellRadius,
      HUMAN_NC_3D_LIPID_DROPLET_VOLUME_FRACTION
    );
    const displayedVolume = scales.reduce(
      (sum, scale) => sum + (4 / 3) * Math.PI * (baseRadius * scale) ** 3,
      0
    );
    const cellVolume = (4 / 3) * Math.PI * cellRadius ** 3;
    expect(displayedVolume / cellVolume).toBeCloseTo(
      HUMAN_NC_3D_LIPID_DROPLET_VOLUME_FRACTION,
      14
    );
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
    expect(HEPATOCYTE_CANONICAL_POLARITY_AXIS).toEqual([1, 0, 0]);
    expect(membraneDomainForDirection(1, 0.18, 0.02)).toBe("apical");
    expect(membraneDomainForDirection(-1, 0, 0)).toBe("basolateral");
    expect(membraneDomainForDirection(0, 1, 0)).toBe("lateral");
    // Exact shared features are rendered as lateral while the engine exposes
    // both candidates and fails the biological domain gate closed.
    expect(membraneDomainForDirection(2, 0.5, 0.5)).toBe("lateral");
  });

  it("reduces ultrastructure load for distant and narrow views", () => {
    expect(visualAnatomyLod(18, 1200)).toBe("ultrastructure");
    expect(visualAnatomyLod(36, 1200)).toBe("cellular");
    expect(visualAnatomyLod(50, 1200)).toBe("overview");
    expect(visualAnatomyLod(45, 390)).toBe("overview");
  });
});
