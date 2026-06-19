# Milestone 018 - Hepatocyte metabolism v1

Status: implemented

M018 gives the Python engine a first hepatocyte-specific metabolic runtime. It
is still normalized and coarse-grained, but it is no longer just a static pool
list. The cell now produces and spends ATP through named processes, tracks
redox/detox cost, and carries local ATP availability per organelle.

## What Was Added

- `engine/cell_engine/processes/metabolism.py`
  - glycogen breakdown/storage;
  - glycolysis;
  - lactate/pyruvate handling;
  - mitochondrial pyruvate oxidation;
  - fatty-acid oxidation;
  - simplified urea cycle;
  - CYP-like detox with NADPH/GSH cost and ROS side effect;
  - simplified canalicular bile export;
  - baseline ATP maintenance cost;
  - local ATP transport delay per organelle.
- `MetabolicFlux` in `CellState`
  - every step reports named process fluxes and producer/consumer roles.
- `OrganelleState.local_atp`
  - ATP is not treated as instantly usable everywhere.
- `OrganelleState.transport_delay_s`
  - delay is derived from distance to mitochondria using ATP diffusion and a
    coarse-grained microdomain delay scale.

## Biological Contract

- ATP/ADP/AMP are conserved as a normalized adenylate pool.
- Energy production and consumption have explicit sources.
- Detox load consumes NADPH/GSH and increases ROS.
- Urea-cycle flux consumes ATP and ammonia.
- Bile export consumes ATP and depends on membrane/Golgi health.
- Local organelle ATP can lag the global ATP pool.

## Boundaries

- Values remain normalized relative pools.
- Flux coefficients are structural placeholders until quantitative hepatocyte
  data are curated.
- No SBML/libRoadRunner pathway execution yet; that is M019.

## Verification

```bash
python -m unittest discover -s engine/tests -t engine
npm test -- --maxWorkers=1
npm run build
```

