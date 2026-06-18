# Milestone 010: The Eukaryotic Cell (organelles)

## Objective

Show a whole animal cell with its organelles — the thing most people picture when
they hear "cell". Until now the project lived at the molecular scale (you saw
individual lipids). A real eukaryotic cell is ~10–30 µm across with organelles of
0.1–6 µm; at that scale you cannot see individual lipids, so this is a new,
coarser view: the **cell layer** of the multiscale plan.

## What it shows

A translucent plasma membrane (so you can see inside) enclosing:

- **Nucleus** (largest organelle, ~6 µm) with a **nucleolus**, wrapped by the
- **Endoplasmic reticulum** — a network contiguous with the nuclear envelope;
- **Golgi apparatus** — a stack of flattened cisternae;
- **Mitochondria** — bean-shaped, scattered through the cytoplasm;
- **Lysosomes / peroxisomes** — small spheres;
- **Ribosomes** — a haze of tiny dots (free and on the rough ER);
- **Centrosome** — a pair of perpendicular centrioles by the nucleus.

The view turns slowly so the 3-D interior reads clearly, and the readout reports
the cell scale (~20 µm). A legend names each organelle by colour.

## Honest scope

This is a **structural / anatomical** model, not a molecular-dynamics simulation:
you cannot MD-simulate a whole cell (~10¹⁴ atoms). Organelle **relative sizes,
counts, and spatial relationships are sourced** (NIGMS, LibreTexts, Molecular
Biology of the Cell — see `docs/sources.md`); very small organelles (ribosomes)
are drawn slightly enlarged for visibility, as in any textbook diagram. The
molecular physics that *grounds* this scale lives one zoom-in below, in the
ion / water / membrane / chemistry "building-block" scenes.

This is exactly the multiscale contract: at the cell scale, organelles are
objects with properties; their internal detail is abstracted, not deleted.

## Why the molecular vesicle is different

The earlier "Cell — one reality (vesicle)" is the *membrane at the molecular
scale* (individual lipids, real fluid bilayer). This eukaryotic-cell scene is the
*whole cell at the cell scale*. Same cell, two zoom levels — that is the point of
a multiscale model.

## Next (frontier)

- Organelle **interactions** as processes: ER → Golgi → membrane vesicle traffic,
  mitochondria producing ATP, lysosomal degradation — shown as rule-based flows.
- Couple to the chemistry engine so reactions run in cytoplasmic compartments.
- These remain grounded: any rate or interaction must trace to data.
