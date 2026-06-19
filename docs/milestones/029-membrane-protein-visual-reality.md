# Milestone 029 - Membrane protein visual reality

Status: implemented

M029 fixes the plasma-membrane protein layer so it no longer reads as loose,
oversized tubes floating near the cell. The scene now uses true nanometre-scale
embedded protein sizes and a density model for hepatocyte-scale copy numbers.

## What Was Added

- Membrane proteins are anchored to the plasma membrane normal and stay attached
  while the cell turns.
- Anchored proteins get tiny lateral membrane drift, representing membrane-plane
  diffusion without detaching from the bilayer.
- Detailed channel/transporter/receptor meshes now use nanometre coordinates
  scaled into the cell scene; they are no longer enlarged inspection glyphs.
- The whole plasma membrane gets a true-size LOD point shell for millions of
  embedded proteins. The browser does not draw every copy as a mesh; each far
  shell dot represents a fixed number of real proteins.
- A small front membrane patch is rendered at true density with 1 dot = 1
  embedded protein so close zoom shows the expected local crowding.
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
scene, a true-size channel/carrier is almost invisible until the camera is pushed
close to the membrane.

For count scale, this milestone uses a conservative density estimate:

- hepatocyte plasma membrane area: ~2000 um², inferred from the BioNumbers
  hepatocyte internal membrane area entry noting internal membrane is ~50x plasma
  membrane area;
- protein area occupancy: 23% lower-bound area occupancy from measured red blood
  cell membrane protein occupancy;
- average embedded footprint diameter: 7 nm family-level estimate.

That gives roughly 12 million embedded plasma-membrane proteins for the current
hepatocyte-scale visual cell. The exact family split is still an explicit model
assumption, not a measured single-cell proteomics copy-number table.

The detailed meshes are still coarse-grained. They do not claim atomistic PDB
accuracy. They encode family-level structure and connection logic:

- channels and aquaporins form selective transmembrane pores;
- carriers bind a solute and expose the binding site alternately to outside and
  cytosol;
- pumps couple transport to intracellular ATP state;
- receptors couple extracellular recognition to cytosolic signaling/adaptor
  proteins.

## Boundaries

- Exact protein copy number and family distribution are still schematic; the
  total density is source-derived, but the family percentages are model
  assumptions until a hepatocyte membrane proteomics table is added.
- The carrier/aquaporin/channel glyphs are family-level visual models, not
  molecule-specific structures.
- Aquaporin water exchange is a coarse visual flow, not yet an osmotic pressure
  solver.
- Full-surface rendering uses LOD to avoid freezing the browser. The zoom patch
  is true density, one dot per embedded protein.
- Stochastic path variation is visual-route level. Individual engine cargo
  packets with wait, return, degradation and misrouting states remain M030.

## Verification

```bash
npm test -- --maxWorkers=1
npm run build
python -m unittest discover -s engine/tests -t engine
```
