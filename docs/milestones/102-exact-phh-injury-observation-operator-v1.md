# Milestone 102: Exact PHH Injury Observation Operator v1

## Goal

Turn the curated APAP and bile-acid injury evidence into an executable,
read-only validation surface without inventing a generalized death or recovery
law.

## Exact-context operator

The operator requires exact equality across:

- species;
- biological system;
- challenge identity;
- challenge lower and upper bounds;
- reported dose unit;
- maximum exposure duration;
- temperature.

After a protocol match, endpoint, intervention condition and time window are
filtered without unit conversion or interpolation. An empty result means that
the requested quantity was not observed in the retained evidence. It never
means that the biological effect is absent.

The four source protocols replay through the operator. Seven single-dimension
software near-miss probes are rejected. These are software integrity checks,
not biological validation results.

## Legacy runtime firewall

Three legacy runtime surfaces are explicitly classified as exploratory:

- the apoptosis/necrosis switch;
- the detox-count to fate-signal projection;
- the synthetic tissue-injury population fixture.

Their executable weights, saturation scales, thresholds, heterogeneity and
timings are not calibrated to the curated PHH protocols. Public runtime calls
must declare a purpose and reject quantitative validation, predictive execution
and authoritative PHH state-coupling purposes.

## Donor-disjoint data contract

`data/evidence_intake/phh_injury_trajectory_contract.v1.json` defines 19
required and 10 conditional fields for future raw trajectories. It preserves
donor identity, split role, dose, time, assay, raw unit, replicate identity,
normalization, censoring, intervention, washout, recovery and fate labels.

No donor-resolved trajectory is currently loaded. General fate laws, automatic
parameter activation and automatic cell-state coupling remain at zero.

## Scientific boundary

This milestone makes existing evidence testable and prevents unsupported
runtime claims. It does not calibrate apoptosis, necrosis, senescence, recovery
or time-to-death. Those require raw donor-resolved dose-time trajectories,
commitment and washout experiments, a frozen model, and independent held-out
donors.

## Files

- `engine/cell_engine/quantitative/phh_injury_validation.py`
- `engine/cell_engine/core/injury_authority.py`
- `engine/cell_engine/stochastic/apoptosis.py`
- `engine/cell_engine/stochastic/tissue_injury.py`
- `data/evidence_intake/phh_injury_trajectory_contract.v1.json`
- `engine/tests/test_phh_injury_validation.py`
- `engine/tests/test_injury_authority.py`
