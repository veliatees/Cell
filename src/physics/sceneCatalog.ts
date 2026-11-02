/**
 * Static catalogue of the legacy ("building blocks / zoom-in") browser scenes.
 *
 * The scene selector in `main.ts` is built synchronously at module evaluation
 * time, before the first frame. The simulator modules themselves are heavy and
 * are only needed once a visitor actually selects one of these scenes, so they
 * are loaded through cached dynamic imports. This file is the small, synchronous
 * part: ids and labels only.
 *
 * It intentionally contains no simulation code, no numeric parameter and no
 * biological claim. It is a display index.
 *
 * `sceneCatalog.test.ts` statically imports the real simulator modules (test
 * code never enters the production browser graph) and fails if this catalogue
 * drifts from them in id, label or order. That is the guard against duplicated
 * truth: the simulator registries stay authoritative.
 */

export type SceneCatalogEntry = {
  readonly id: string;
  readonly label: string;
};

/** Mirrors `MEMBRANE_SCENES` in `membrane.ts`. */
export const MEMBRANE_SCENE_CATALOG: readonly SceneCatalogEntry[] = [
  { id: "cell-reality", label: "Cell — one reality (vesicle)" },
  { id: "cell-pore", label: "Cell with a pore (exchange)" },
  { id: "cell-flat", label: "Membrane boundary (flat slice)" },
  { id: "bilayer-patch", label: "Lipid bilayer patch" },
  { id: "self-assembly", label: "Membrane self-assembly" },
  { id: "membrane-barrier", label: "Barrier (intact bilayer)" },
  { id: "membrane-pore", label: "Transport through a pore" }
];

/** Mirrors `WATER_SCENES` in `water.ts`. */
export const WATER_SCENE_CATALOG: readonly SceneCatalogEntry[] = [
  { id: "water-single", label: "Water molecule (SPC/E)" },
  { id: "water-dimer", label: "Water dimer (hydrogen bond)" },
  { id: "water-cluster", label: "Water cluster (5)" }
];

/** Mirrors `SOLVATION_SCENES` in `solvation.ts`. */
export const SOLVATION_SCENE_CATALOG: readonly SceneCatalogEntry[] = [
  { id: "na-hydration", label: "Na+ hydration shell" },
  { id: "nacl-in-water", label: "NaCl in water" }
];

/** Mirrors `DIFFUSION_SCENES` in `diffusion.ts`. */
export const DIFFUSION_SCENE_CATALOG: readonly SceneCatalogEntry[] = [
  { id: "ink-drop", label: "Diffusion (ink drop)" },
  { id: "na-vs-cl", label: "Na+ vs Cl- diffusion" }
];

/** Mirrors `REACTION_SCENES` in `reactions.ts`. */
export const REACTION_SCENE_CATALOG: readonly SceneCatalogEntry[] = [
  { id: "reaction-abc", label: "Reaction A + B → C" }
];
