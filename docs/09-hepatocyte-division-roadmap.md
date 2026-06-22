# Hepatocyte Division Roadmap

This roadmap exists because fake division visuals are not allowed in this project.
If the screen shows two cells, the engine must actually contain two daughter cell
states. No ghost cells, no decorative split animation, no visual-only daughter.

## Literature Baseline

Animal-cell cytokinesis is not a simple visual separation. The required chain is:

1. G1/S commitment: nutrients, size, growth factors, and DNA integrity.
2. S phase: genome replication.
3. G2/M checkpoint: replicated and undamaged DNA.
4. Mitosis: rounding, centrosome/spindle organization, chromosome alignment,
   chromosome segregation, and nuclear-envelope reformation.
5. Cytokinesis: spindle-positioned division plane, RhoA-driven actomyosin
   contractile ring, cleavage-furrow ingression, membrane insertion, intercellular
   bridge, midbody, and abscission.
6. Inheritance: each daughter must receive a genome, cytoplasm, membrane, and
   enough essential organelles. Organelles are not optional decoration.

Mechanistic anchors now encoded:

- The division plane is not random. The mitotic spindle sets the plane; the
  contractile ring forms at the metaphase-plate/equatorial plane, perpendicular
  to the spindle axis.
- The first visible animal-cell cytokinesis feature is the cleavage furrow. It is
  driven by an actomyosin ring under the plasma membrane and requires additional
  membrane insertion.
- Late cytokinesis is a bridge/midbody state, not two free cells. Abscission
  requires bridge maturation, local cytoskeletal clearance and membrane scission;
  high bridge tension can delay abscission.
- Mitosis redistributes organelles. Mitochondria fragment/disperse for daughter
  inheritance; Golgi disassembles/fragments; ER fragments with nuclear-envelope
  breakdown; endosome/lysosome populations remain mostly intact; peroxisome
  positioning can affect spindle orientation.
- Centrosomes duplicate once per cycle so a normal successful division gives one
  centrosome to each daughter.

Hepatocytes are special. A hepatocyte entering M phase does not always produce two
daughter hepatocytes. Liver polyploidy commonly arises from incomplete cytokinesis
or endomitosis, producing binucleated or mononuclear polyploid hepatocytes. That
means a realistic hepatocyte division module must model both outcomes:

- successful cytokinesis -> two daughter hepatocytes;
- cytokinesis failure/regression -> one binucleated/polyploid hepatocyte.

Equally important: division is not the default visual purpose of the cell. Adult
hepatocytes are normally quiescent (G0/G1). Nutrients and ATP are necessary for
growth, but they are not sufficient to force proliferation. The simulation must
require regeneration/mitogen signalling plus checkpoint clearance before biomass
growth, S phase, mitosis, or cytokinesis visuals are allowed to start.

## Sources To Encode

- Molecular Biology of the Cell, NCBI Bookshelf, "Cytokinesis":
  https://www.ncbi.nlm.nih.gov/books/NBK26831/
- Cytokinesis in Animal Cells:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC4382743/
- Animal Cell Cytokinesis: Rho-dependent actomyosin contractile ring:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC7575755/
- Hepatocytes Polyploidization and Cell Cycle Control in Liver:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC3485502/
- The origins and functions of hepatic polyploidy:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC6592246/
- Liver cell polyploidization: a pivotal role for binuclear hepatocytes:
  https://pubmed.ncbi.nlm.nih.gov/12626502/
- Binucleated human hepatocytes arise through late cytokinetic regression:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC11090133/
- Mechanics and regulation of cytokinetic abscission:
  https://www.frontiersin.org/journals/cell-and-developmental-biology/articles/10.3389/fcell.2022.1046617/full
- Organelle inheritance control of mitotic entry and progression:
  https://www.frontiersin.org/journals/cell-and-developmental-biology/articles/10.3389/fcell.2019.00133/full
- The multifaceted regulation of mitochondrial dynamics during mitosis:
  https://www.frontiersin.org/journals/cell-and-developmental-biology/articles/10.3389/fcell.2021.767221/full
- Duplication and segregation of centrosomes during cell division:
  https://www.mdpi.com/2073-4409/11/15/2445
- BioNumbers / Cell Biology by the Numbers, mammalian phase timings:
  https://book.bionumbers.org/how-long-do-the-different-stages-of-the-cell-cycle-take/
- BioNumbers BNID 106404, HeLa phase-duration benchmark:
  https://bionumbers.hms.harvard.edu/bionumber.aspx?id=106404&s=n&v=2
- Rat hepatocyte post-partial-hepatectomy timing:
  https://www.nature.com/articles/emm199629

## Reality Rules

- Do not display daughter cells unless the engine created daughter cell states.
- Do not label a cell "divided" until abscission succeeds or a true daughter split
  has happened in the model.
- If cytokinesis reaches the late stage but abscission is not modelled yet, show
  "abscission pending" or "not implemented", not fake separation.
- If cytokinesis fails, show one cell with two nuclei or increased ploidy, not two
  cells.
- Every division outcome must conserve or explicitly partition molecule counts,
  organelle counts, biomass/volume, membrane area, and genome/ploidy.
- Hepatocyte-specific polyploidy is a feature, not an error.

## Milestone D0 - Remove Fake Division

Status: completed in code.

Work:

- Remove the two translucent daughter ghost meshes.
- Stop showing "divided" in the browser unless the data model has actually split.
- Allow the split-state badge to report "abscission pending" while the true
  daughter model is not implemented.

Acceptance:

- Searching the TypeScript scene has no ghost daughter meshes.
- The viewport never shows two cells from a one-cell state.
- The split-state readout can stop at "abscission pending" instead of pretending
  that a true daughter model already exists.

## Milestone D1 - Engine State Model

Goal: represent cell division as real state, not a UI flag.

Status: partially implemented and expanded. `WholeCellPopulation` and
`WholeCellDivisionEvent` now preserve all result cells. Successful abscission
returns two real `WholeCell` states; forced cytokinesis failure returns one real
binucleated/polyploid `WholeCell` state. `CellCycleState` now carries
`PloidyState`, `CytokinesisState`, and `OrganelleInventory`.

Add:

- `CellInstance`: id, parent id, generation, geometry, ploidy, nuclei,
  organelles, pools/counts, cycle state.
- `CellPopulation`: one or more `CellInstance` objects, even before multicellular
  tissue simulation.
- `DivisionOutcome`: `none`, `mitotic_progress`, `abscission_success`,
  `cytokinesis_failure`, `checkpoint_arrest`, `apoptosis_or_death`.
- `PloidyState`: chromosome sets per nucleus and number of nuclei.
- `CytokinesisState`: furrow depth, ring activity, bridge state, midbody state,
  abscission readiness, failure reason.
- `OrganelleInventory`: mitochondria, mitochondrial fragments, lysosomes,
  peroxisomes, ribosomes, Golgi stacks/fragments, ER mass, membrane area and
  centrosomes.

Acceptance:

- Population stepping no longer silently keeps daughter A and discards daughter B.
- A successful division returns two real cells.
- A failed cytokinesis returns one real binucleated/polyploid cell.
- Successful division conserves tracked organelle inventory and gives one
  centrosome to each daughter.
- Failed cytokinesis conserves tracked organelle inventory in one cell and keeps
  two nuclei / two centrosomes.
- Remaining: replace legacy single-lineage helpers with population-first APIs and
  give each cell a stable external id/parent id for browser binding.

## Milestone D2 - Biological Checkpoints

Goal: make division possible only when biology permits it.

Add gates for:

- nutrient and energy sufficiency;
- mitogen/growth-factor signal;
- DNA-damage and p53/p21 checkpoint pressure;
- genome replication completion;
- spindle assembly / chromosome alignment;
- ATP-dependent apoptosis-vs-necrosis interaction if failure is severe.

Acceptance:

- Starved cells arrest before division.
- DNA-damaged cells arrest or die.
- Oncogene/checkpoint-bypass cells divide under conditions where normal cells
  should not.
- Tests cover normal, arrested, cancer-like, and death outcomes.

Status: expanded. The engine now separates compressed visualization timing from
source-traced biological timing profiles. `compressed_demo` remains available for
explicit fast browser/test demonstrations, but normal browser exports default to
`rat_hepatocyte_phx_reference`, which blocks G1/S for the first ~18 h after PHx
and carries its source ids into the Python snapshot. This means an 80-160 second
demo cannot be mistaken for real hepatocyte regeneration time.

## Milestone D3 - Hepatocyte Polyploidy / Binucleation

Goal: make hepatocyte-specific outcomes real.

Add:

- probability/rule layer for cytokinesis success vs failure;
- species/context flags for rat/mouse/human assumptions;
- binucleated 2x2n hepatocyte state;
- mononuclear 4n and higher ploidy transitions;
- regulators/conditions that modulate failure: actin ring function, RhoA,
  Anillin, RacGAP1, SEPT9, CIT-K, Aurora B, WNT/E2F7/E2F8, ERK/Mkp1 where
  supported by source evidence.

Acceptance:

- Failed cytokinesis creates a binucleated/polyploid hepatocyte with conserved
  contents.
- Successful cytokinesis creates two daughters.
- The UI distinguishes "successful cytokinesis" from "cytokinesis regression".

Status: started. The current `cytokinesis_failure_risk()` combines a base
hepatocyte failure probability with context factors: RhoA activity, midbody
anchoring, WNT activity, TGFbeta/Src pressure, membrane supply and bridge
tension. The coefficients are explicitly modelling assumptions, not measured
constants; they exist so later calibration can replace them.

## Milestone D4 - Real Visual Sequence

Goal: show only model-backed structures and phases.

Visuals allowed only when corresponding state exists:

- G2/M: mitotic rounding and cortical reorganization.
- Prophase/prometaphase: condensed chromosomes, nuclear-envelope breakdown.
- Metaphase: spindle and aligned chromosomes.
- Anaphase: segregating chromatids.
- Telophase: two reforming nuclei.
- Cytokinesis: contractile ring and cleavage furrow only if ring activity > 0.
- Late cytokinesis: intercellular bridge and midbody only if daughter cells are
  still connected.
- Abscission success: two separate `CellInstance` visuals.
- Abscission failure: bridge regression, one binucleated/polyploid cell.

Acceptance:

- There is no purely decorative "daughter outline".
- Daughter positions, organelle distributions, and labels come from actual
  daughter objects.
- Cytokinesis failure visually remains one cell.

Status: expanded. The browser now shows a model-backed mitotic overlay:
centrosomes/spindle, metaphase chromosomes, equatorial contractile ring,
cleavage-furrow ingression, intercellular bridge/midbody, reforming daughter
nuclei and an abscission checkpoint. After the checkpoint resolves, the browser
creates either two real visual daughter `VisualCellInstance` states with
partitioned organelle inventories, or one binucleated cytokinesis-regression
state. The old decorative ghost split remains forbidden.

## Milestone D5 - Partitioning

Goal: make daughter inheritance credible.

Partition:

- genome exactly when chromosome segregation succeeds;
- cytosolic molecule pools stochastically or volume-weighted;
- mitochondria, lysosomes, peroxisomes, vesicles, and ribosomes by spatial
  location plus stochastic noise;
- ER/Golgi by fragmentation/reassembly state rather than arbitrary halves;
- membrane area and transporter counts by membrane-domain geometry.

Acceptance:

- Conservation tests exist for all tracked pools.
- Daughter asymmetry is possible but bounded.
- A daughter lacking essential organelle inheritance is stressed or nonviable.

Status: started. Molecule counts and tracked organelle inventory have
conservation tests. Mitochondria/lysosomes/peroxisomes/ribosomes partition with
binomial noise; ER and membrane area split as continuous mass/area pools; Golgi
fragments repartition then reassemble as stacks; centrosomes segregate exactly
when the parent has the expected two.

## Milestone D6 - Browser Binding

Goal: show division state without lying.

Add:

- split-state badge driven by engine `DivisionOutcome`, not a standalone TS clock;
- phase-specific tooltips explaining what is actually modelled;
- no "divided" text unless `CellPopulation.count` increased or binucleation
  state changed;
- browser tests for success, arrest, and cytokinesis failure.

Acceptance:

- The browser can show one normal hepatocyte, two daughters, or one binucleated
  hepatocyte depending on engine state.
- The UI never invents cells.

Status: expanded and corrected. Browser-local `VisualCellInstance` and
`VisualDivisionEvent` state now back the post-abscission view, and the Python
snapshot exporter can serialize `WholeCellPopulation` / `WholeCellDivisionEvent`
under `state.division`. The TypeScript snapshot client recognizes that payload
and the browser applies the latest engine division event when present. Default
adult-hepatocyte snapshots remain quiescent unless an explicit division demo /
regeneration-cycle parameter is used. Remaining work is full live streaming,
browser-level success/failure/arrest tests, and replacing the fallback visual
clock entirely with engine phase data.

## Milestone D7 - Validation Targets

Initial validation targets:

- checkpoint behavior: starvation/DNA damage arrests;
- binucleation/polyploidy route exists and is not treated as impossible;
- molecule-count conservation across division;
- ploidy/nuclei state transitions are explicit;
- division outcome probabilities are source-tagged as measured, fitted, or
  assumption.

## Immediate Next Implementation Order

1. Add browser tests for engine-driven abscission success, cytokinesis regression, and
   checkpoint arrest.
2. Replace the remaining browser-local phase clock with engine-driven phase and
   outcome data for pre-abscission states.
3. Add spatial organelle partitioning so daughter inheritance depends on where
   organelles were at the cleavage plane, not only binomial count noise.
4. Add membrane-domain partitioning: transporter counts and basolateral/apical
   identity must split from actual membrane geometry.
5. Add live snapshot streaming so division can progress continuously instead of
   loading a static JSON event.
