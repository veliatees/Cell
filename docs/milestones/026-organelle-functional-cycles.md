# Milestone 026 - Organelle functional cycles v1

Status: implemented

M026 replaces the previous "same stub for every organelle" behavior with the
first organelle-specific functional cycles. The model is still coarse-grained,
but each major hepatocyte organelle now changes cell state through a distinct
biological job instead of only aging and accumulating risk.

## Research Basis

Sources used for this implementation:

- NCBI Bookshelf, Molecular Biology of the Cell, "From DNA to RNA":
  https://www.ncbi.nlm.nih.gov/books/NBK26887/
- NCBI Bookshelf, The Cell, "RNA Processing and Turnover":
  https://www.ncbi.nlm.nih.gov/books/NBK9864/
- NCBI Bookshelf, Molecular Biology of the Cell, "The Endoplasmic Reticulum":
  https://www.ncbi.nlm.nih.gov/books/NBK26841/
- NCBI Bookshelf, Molecular Biology of the Cell, "Transport from the ER through
  the Golgi Apparatus": https://www.ncbi.nlm.nih.gov/books/NBK26941/
- NCBI Bookshelf, Molecular Biology of the Cell, "Transport from the Trans
  Golgi Network to the Cell Exterior": https://www.ncbi.nlm.nih.gov/books/NBK26892/
- NCBI Bookshelf, Molecular Biology of the Cell, "Transport from the Trans
  Golgi Network to Lysosomes": https://www.ncbi.nlm.nih.gov/books/NBK26844/
- NCBI Bookshelf, Molecular Biology of the Cell, "The Mitochondrion":
  https://www.ncbi.nlm.nih.gov/books/NBK26894/
- NCBI Bookshelf, The Cell, "Lysosomes":
  https://www.ncbi.nlm.nih.gov/books/NBK9953/
- NCBI Bookshelf, Molecular Biology of the Cell, "Peroxisomes":
  https://www.ncbi.nlm.nih.gov/books/NBK26858/
- NCBI Bookshelf, The Cell, "Protein Degradation":
  https://www.ncbi.nlm.nih.gov/books/NBK9957/
- "Hepatocyte Polarity", PMC:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC3697931/
- "Bile acid transporters", Journal of Lipid Research / PMC:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC2781307/

## What Was Added

- `engine/cell_engine/organelles/base.py`
  - organelle step results can now carry pool updates;
  - `FunctionalCycle` allows each organelle to report active processes,
    activity, damage/capacity changes and events.
- `engine/cell_engine/core/engine.py`
  - the main cell step now carries organelle-produced pool changes forward.
- `engine/cell_engine/organelles/modules.py`
  - plasma membrane nutrient/oxygen entry, export and endocytosis;
  - nucleus transcription, splicing/export error and repair load;
  - ribosome translation and mistranslation/misfolding;
  - rough ER folding, ER quality control and ERAD handoff;
  - smooth ER lipid synthesis and CYP-like detox side load;
  - Golgi glycosylation/sorting and polarized cargo partitioning;
  - mitochondria oxidative ATP support, ROS side load and mitophagy commitment;
  - lysosome/endosome degradation, autophagy completion and recycling;
  - peroxisome VLCFA oxidation and catalase-like ROS buffering;
  - proteasome ubiquitin/protein degradation and amino-acid recycling;
  - cytoskeleton ATP-consuming motor/positioning work.
- `engine/cell_engine/processes/hepatocyte.py`
  - added intermediate pools for oxygen, cytosolic protein, folded cargo,
    ubiquitinated cargo, Golgi-sorted cargo, endocytosed/autophagy cargo and
    very-long-chain fatty acids.

## New Coarse Pools

- oxygen
- cytosolic protein
- folded cargo
- ubiquitinated cargo
- membrane cargo
- lysosome enzyme cargo
- canalicular cargo
- endocytosed cargo
- autophagy cargo
- very-long-chain fatty acids

## Contract

- Organelles now have distinct state-changing work, not only generic health
  updates.
- ATP/ADP/AMP conservation remains enforced after organelle cycles.
- ER -> Golgi -> membrane/lysosome/proteasome coupling leaves measurable pool
  traces.
- Mitochondria, lysosome and peroxisome now participate in damage turnover and
  redox balance.

## Boundaries

- Rates are still normalized placeholders, not fitted hepatocyte constants.
- Protein classes are coarse pools, not individual genes/proteins.
- Organelle cycles run in deterministic engine order, while stochastic outcomes
  still come from seeded hazards/events.
- Real organelle morphology, movement and live visual changes are not part of
  this milestone.

## Verification

```bash
python -m unittest discover -s engine/tests -t engine
npm test -- --maxWorkers=1
npm run build
```
