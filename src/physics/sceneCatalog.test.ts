import { describe, expect, it } from "vitest";
import { DIFFUSION_SCENES } from "./diffusion";
import { MEMBRANE_SCENES } from "./membrane";
import { REACTION_SCENES } from "./reactions";
import { SOLVATION_SCENES } from "./solvation";
import { WATER_SCENES } from "./water";
import {
  DIFFUSION_SCENE_CATALOG,
  MEMBRANE_SCENE_CATALOG,
  REACTION_SCENE_CATALOG,
  SOLVATION_SCENE_CATALOG,
  WATER_SCENE_CATALOG,
  type SceneCatalogEntry
} from "./sceneCatalog";

// The catalogue exists only so the scene selector can be built synchronously
// without pulling the simulators into the initial browser bundle. The simulator
// registries remain authoritative; this test fails if the display index drifts
// from them in id, label or order.
const registryView = (
  presets: readonly { id: string; label: string }[]
): SceneCatalogEntry[] => presets.map(({ id, label }) => ({ id, label }));

const catalogues: [string, readonly SceneCatalogEntry[], SceneCatalogEntry[]][] = [
  ["membrane", MEMBRANE_SCENE_CATALOG, registryView(MEMBRANE_SCENES)],
  ["water", WATER_SCENE_CATALOG, registryView(WATER_SCENES)],
  ["solvation", SOLVATION_SCENE_CATALOG, registryView(SOLVATION_SCENES)],
  ["diffusion", DIFFUSION_SCENE_CATALOG, registryView(DIFFUSION_SCENES)],
  ["reactions", REACTION_SCENE_CATALOG, registryView(REACTION_SCENES)]
];

describe("legacy scene catalogue", () => {
  it("mirrors every simulator scene registry in id, label and order", () => {
    for (const [name, catalog, registry] of catalogues) {
      expect(catalog, `${name} catalogue drifted from its simulator registry`).toEqual(registry);
    }
  });

  it("has globally unique scene ids across registries", () => {
    const ids = [
      ...MEMBRANE_SCENE_CATALOG,
      ...WATER_SCENE_CATALOG,
      ...SOLVATION_SCENE_CATALOG,
      ...DIFFUSION_SCENE_CATALOG,
      ...REACTION_SCENE_CATALOG
    ].map((entry) => entry.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("carries display text only, no simulation state", () => {
    for (const [, catalog] of catalogues) {
      for (const entry of catalog) {
        expect(Object.keys(entry).sort()).toEqual(["id", "label"]);
      }
    }
  });
});
