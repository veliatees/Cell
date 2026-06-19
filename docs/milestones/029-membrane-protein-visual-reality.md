# Milestone 029 - Membrane protein visual reality

Status: implemented

M029 fixes the plasma-membrane protein layer so it no longer reads as loose,
oversized tubes floating near the cell. The scene now separates biological scale
truth from inspectable glyph scale.

## What Was Added

- Membrane proteins are anchored to the plasma membrane normal and stay attached
  while the cell turns.
- Anchored proteins get tiny lateral membrane drift, representing membrane-plane
  diffusion without detaching from the bilayer.
- Each protein shows two scales:
  - a true-scale nanometre footprint on the membrane;
  - a magnified inspection glyph at the same membrane site.
- Aquaporins are shown as tetrameric water-channel glyphs with four narrow
  monomer pores and single-file water beads.
- Carrier transporters are shown as a 12-helix alternating-access bundle with an
  extracellular nutrient-binding cleft and cytosolic release side.
- Ion channels have a central pore and cytosolic vestibule.
- ATP-driven pumps now show cytosolic ATP-binding lobes instead of looking like
  passive open tubes.
- Glycoprotein receptors now show extracellular glycan/ligand-facing structure,
  a membrane span, a cytosolic tail and adaptor protein.
- Visual flow targets now route extracellular glucose, amino acids, fatty acids,
  bile acids, water and signals to the relevant membrane protein port instead of
  a generic membrane point.
- Flow particles now re-sample their route curve per cycle, so visible cargo
  does not always trace the exact same path.

## Biological Reality

Most membrane proteins are only a few nanometres wide. In a 10 um hepatocyte-scale
scene, a true-scale channel/carrier would be almost invisible. The model therefore
uses a dual representation: true-scale footprint plus a magnified, labelled glyph.

The glyphs are still coarse-grained. They do not claim atomistic PDB accuracy.
They encode family-level structure and connection logic:

- channels and aquaporins form selective transmembrane pores;
- carriers bind a solute and expose the binding site alternately to outside and
  cytosol;
- pumps couple transport to intracellular ATP state;
- receptors couple extracellular recognition to cytosolic signaling/adaptor
  proteins.

## Boundaries

- Protein copy number and exact distribution are still schematic.
- The carrier/aquaporin/channel glyphs are family-level visual models, not
  molecule-specific structures.
- Aquaporin water exchange is a coarse visual flow, not yet an osmotic pressure
  solver.
- Stochastic path variation is visual-route level. Individual engine cargo
  packets with wait, return, degradation and misrouting states remain M030.

## Verification

```bash
npm test -- --maxWorkers=1
npm run build
python -m unittest discover -s engine/tests -t engine
```
