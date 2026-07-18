import { describe, expect, it } from "vitest";

import { perspectiveFrameScale } from "./visualFraming";

describe("perspectiveFrameScale", () => {
  const common = {
    cameraDistance: 20,
    elevationFactor: 0.36,
    verticalFovDegrees: 48,
    margin: 0.82
  };

  it("uses more of a narrow viewport for one cell than the former fixed scale", () => {
    const scale = perspectiveFrameScale({ ...common, frameRadius: 6.6, aspect: 370 / 523 });
    expect(scale).toBeGreaterThan(0.75);
    expect(scale).toBeLessThan(0.9);
  });

  it("shrinks a two-cell field enough to keep its complete bounding sphere visible", () => {
    const scale = perspectiveFrameScale({ ...common, frameRadius: 13.2, aspect: 826 / 685 });
    expect(scale).toBeGreaterThan(0.5);
    expect(scale).toBeLessThan(0.7);
  });

  it("caps magnification for very small interaction bodies", () => {
    expect(perspectiveFrameScale({ ...common, frameRadius: 0.2, aspect: 1 })).toBe(1.05);
  });

  it("rejects non-physical viewport inputs", () => {
    expect(() => perspectiveFrameScale({ ...common, frameRadius: 1, aspect: 0 })).toThrow();
  });
});
