import { describe, expect, it } from "vitest";
import { REACTION_SCENES, ReactionSystem, reactionSystemFromPreset } from "./reactions";

describe("reaction–diffusion (A + B → C)", () => {
  it("conserves atoms: every C came from one A and one B", () => {
    const sys = new ReactionSystem({ countA: 70, countB: 70, boxNm: 8, seed: 5 });
    for (let i = 0; i < 300; i += 1) {
      sys.step(1);
    }
    const s = sys.snapshot();
    expect(s.countA + s.countC).toBe(70);
    expect(s.countB + s.countC).toBe(70);
    expect(s.reactions).toBe(s.countC);
  });

  it("the reaction proceeds: reactants fall, product rises", () => {
    const sys = new ReactionSystem({ countA: 70, countB: 70, boxNm: 8, seed: 5 });
    const before = sys.snapshot();
    for (let i = 0; i < 300; i += 1) {
      sys.step(1);
    }
    const after = sys.snapshot();
    expect(after.countA).toBeLessThan(before.countA);
    expect(after.countC).toBeGreaterThan(0);
  });

  it("a larger reaction radius gives more product (rate ∝ R, Smoluchowski)", () => {
    const small = new ReactionSystem({ countA: 70, countB: 70, reactionRadiusNm: 0.5, seed: 5 });
    const large = new ReactionSystem({ countA: 70, countB: 70, reactionRadiusNm: 1.0, seed: 5 });
    for (let i = 0; i < 300; i += 1) {
      small.step(1);
      large.step(1);
    }
    expect(large.snapshot().countC).toBeGreaterThan(small.snapshot().countC);
  });

  it("faster diffusion gives more product in the same time", () => {
    const slow = new ReactionSystem({ countA: 70, countB: 70, diffusionM2PerS: 1e-9, seed: 5 });
    const fast = new ReactionSystem({ countA: 70, countB: 70, diffusionM2PerS: 4e-9, seed: 5 });
    for (let i = 0; i < 250; i += 1) {
      slow.step(1);
      fast.step(1);
    }
    expect(fast.snapshot().countC).toBeGreaterThan(slow.snapshot().countC);
  });

  it("reports a positive Smoluchowski rate constant and exposes a scene", () => {
    const sys = reactionSystemFromPreset(REACTION_SCENES[0]);
    expect(sys.smoluchowskiRate()).toBeGreaterThan(0);
    expect(sys.snapshot().countA).toBeGreaterThan(0);
  });
});
