from __future__ import annotations

from dataclasses import dataclass, replace
from math import dist, exp, isclose, isfinite

from cell_engine.core.state import CellState, MetabolicFlux, OrganelleState, PoolState
from cell_engine.stochastic.hazard import clamp

ATP_DIFFUSION_UM2_PER_S = 150.0
COARSE_MICRODOMAIN_DELAY_SCALE = 90.0
ADENYLATE_TOTAL = 1.0


@dataclass(frozen=True)
class MetabolismStepResult:
    pools: dict[str, PoolState]
    organelles: dict[str, OrganelleState]
    fluxes: tuple[MetabolicFlux, ...]


def step_hepatocyte_metabolism(state: CellState, dt_s: float) -> MetabolismStepResult:
    dt_h = dt_s / 3600.0
    pools = dict(state.pools)
    organelles = dict(state.organelles)
    fluxes: list[MetabolicFlux] = []

    atp = _pool(pools, "ATP")
    adp = _pool(pools, "ADP")
    amp = _pool(pools, "AMP")
    glucose = _pool(pools, "glucose")
    glycogen = _pool(pools, "glycogen")
    lactate = _pool(pools, "lactate")
    pyruvate = _pool(pools, "pyruvate")
    fatty_acids = _pool(pools, "fatty_acids")
    ammonia = _pool(pools, "ammonia")
    xenobiotic = _pool(pools, "xenobiotic")
    nadph = _pool(pools, "NADPH")
    gsh = _pool(pools, "GSH")
    bile_acids = _pool(pools, "bile_acids")
    bilirubin = _pool(pools, "bilirubin_conjugates")
    bsep_activity = _surface_activity(state, "bsep_surface_activity", "ABCB11")
    mrp2_activity = _surface_activity(state, "mrp2_surface_activity", "ABCC2")
    cyp7a1_activity = _expression_activity(state, "CYP7A1")
    cyp7a1_rate = _optional_nonnegative_control(state, "cyp7a1_bile_synthesis_rate_per_h")

    cytosol = _health(state, "cytosol_metabolism")
    mitochondria = _health(state, "mitochondria")
    smooth_er = _health(state, "smooth_er")
    membrane = _health(state, "plasma_membrane")
    golgi = _health(state, "golgi")

    energy_need = clamp((0.72 - atp) / 0.72 + 0.35 * amp, 0.0, 1.0)
    storage_signal = clamp((atp - 0.72) / 0.28, 0.0, 1.0)
    adp_drive = clamp(adp + 0.55 * amp, 0.0, 1.0)

    glycogen_breakdown = _flux_value(0.34 * glycogen * energy_need * cytosol, dt_h)
    glycogen_storage = _flux_value(0.18 * glucose * storage_signal * cytosol, dt_h)
    glycolysis = _flux_value(0.58 * glucose * (0.35 + 0.65 * adp_drive) * cytosol * (1.0 - 0.32 * atp), dt_h)
    lactate_to_pyruvate = _flux_value(0.20 * lactate * cytosol * clamp(_pool(pools, "NAD+") + 0.2, 0.0, 1.0), dt_h)
    pyruvate_to_lactate = _flux_value(0.10 * pyruvate * state.stress.get("oxidative", 0.0), dt_h)
    mito_oxidation = _flux_value(0.72 * pyruvate * adp_drive * mitochondria * (1.0 - 0.35 * state.stress.get("oxidative", 0.0)), dt_h)
    beta_oxidation = _flux_value(0.24 * fatty_acids * adp_drive * mitochondria, dt_h)
    urea_cycle = _flux_value(0.42 * ammonia * atp * mitochondria * cytosol, dt_h)
    detox = _flux_value(0.35 * xenobiotic * nadph * gsh * smooth_er, dt_h)
    # BSEP exports bile salts while MRP2 exports bilirubin conjugates. The
    # normalized base rate already present in this coarse metabolism layer is
    # retained; only experimentally supplied relative surface capacity scales it.
    bile_acid_export = _flux_value(0.20 * bile_acids * atp * membrane * golgi * bsep_activity, dt_h)
    bilirubin_export = _flux_value(0.20 * bilirubin * atp * membrane * golgi * mrp2_activity, dt_h)
    bile_acid_synthesis = (
        _flux_value(cyp7a1_rate * cyp7a1_activity * smooth_er, dt_h)
        if cyp7a1_rate is not None and cyp7a1_activity is not None
        else 0.0
    )
    bile_export = bile_acid_export + bilirubin_export
    maintenance = _flux_value((0.055 + 0.030 * _mean_activity(state)) * (0.4 + 0.6 * _mean_health(state)), dt_h)

    _add(pools, "glycogen", -glycogen_breakdown + glycogen_storage)
    _add(pools, "glucose", glycogen_breakdown - glycogen_storage - glycolysis)
    _add(pools, "pyruvate", 0.70 * glycolysis + lactate_to_pyruvate - pyruvate_to_lactate - mito_oxidation)
    _add(pools, "lactate", pyruvate_to_lactate - lactate_to_pyruvate)
    _add(pools, "fatty_acids", -beta_oxidation)
    _add(pools, "acetyl_CoA", 0.45 * mito_oxidation + 0.55 * beta_oxidation)
    _add(pools, "ammonia", -urea_cycle)
    _add(pools, "urea", urea_cycle)
    _add(pools, "xenobiotic", -detox)
    _add(pools, "detoxified_xenobiotic", detox)
    _add(pools, "NADPH", -0.85 * detox + 0.05 * beta_oxidation)
    _add(pools, "GSH", -0.60 * detox + 0.04 * _pool(pools, "NADPH"))
    _add(pools, "GSSG", 0.35 * detox)
    _add(pools, "ROS", 0.16 * mito_oxidation * (1.0 - mitochondria) + 0.20 * detox + 0.05 * beta_oxidation)
    _add(pools, "cholesterol", -bile_acid_synthesis)
    _add(pools, "bile_acids", bile_acid_synthesis)
    _add(pools, "bile_acids", -bile_acid_export)
    _add(pools, "canalicular_bile_acids", bile_acid_export)
    _add(pools, "bilirubin_conjugates", -bilirubin_export)
    _add(pools, "canalicular_bilirubin_conjugates", bilirubin_export)

    atp_delta = (
        0.42 * glycolysis
        + 2.20 * mito_oxidation
        + 1.15 * beta_oxidation
        - 1.10 * urea_cycle
        - 0.45 * detox
        - 0.55 * bile_export
        - maintenance
    )
    _apply_adenylate_delta(pools, atp_delta)
    organelles = _update_local_atp(organelles, pools["ATP"].value, dt_s)

    fluxes.extend(
        (
            _flux("glycogen-breakdown", "glycogen_storage_breakdown", "glycogen", "glucose", glycogen_breakdown, "cytosol_metabolism", "glycolysis", "glycogen mobilized under energy need"),
            _flux("glycogen-storage", "glycogen_storage_breakdown", "glucose", "glycogen", glycogen_storage, "cytosol_metabolism", "glycogen", "storage when ATP is abundant"),
            _flux("glycolysis", "glycolysis", "glucose", "pyruvate_ATP", glycolysis, "cytosol_metabolism", "mitochondria", "cytosolic ATP and pyruvate source"),
            _flux("lactate-pyruvate", "lactate_pyruvate", "lactate", "pyruvate", lactate_to_pyruvate, "cytosol_metabolism", "mitochondria", "redox-linked lactate handling"),
            _flux("mitochondrial-oxidation", "TCA_OXPHOS", "pyruvate_ADP", "ATP_ROS", mito_oxidation, "mitochondria", "cellular_ATP_consumers", "mitochondrial ATP with ROS side load"),
            _flux("beta-oxidation", "fatty_acid_oxidation", "fatty_acids_ADP", "ATP_acetyl_CoA", beta_oxidation, "mitochondria", "cellular_ATP_consumers", "fatty acid contribution to energy"),
            _flux("urea-cycle", "urea_cycle", "ammonia_ATP", "urea", urea_cycle, "mitochondria_cytosol", "sinusoidal_export", "ATP-costly ammonia detox"),
            _flux("detox", "CYP_detox", "xenobiotic_NADPH_GSH_ATP", "detoxified_xenobiotic_ROS", detox, "smooth_er", "export_transporters", "CYP-like detox consumes redox reserve and adds ROS"),
            _flux("cyp7a1-bile-acid-synthesis", "bile_acid_synthesis", "cholesterol", "intracellular_bile_acids", bile_acid_synthesis, "CYP7A1_smooth_er", "bile_acid_pool", "Disabled unless both a calibrated CYP7A1 functional scale and an explicit bile-synthesis rate are supplied; no default rate is invented"),
            _flux("bsep-bile-acid-export", "bile_export", "intracellular_bile_acids_ATP", "canalicular_bile_acids", bile_acid_export, "BSEP_canalicular_surface", "bile_canaliculus", "Mass-conserving intracellular-to-canalicular BSEP transfer; absolute base rate remains an existing normalized model rate"),
            _flux("mrp2-bilirubin-export", "bilirubin_export", "intracellular_bilirubin_conjugates_ATP", "canalicular_bilirubin_conjugates", bilirubin_export, "MRP2_canalicular_surface", "bile_canaliculus", "Mass-conserving intracellular-to-canalicular MRP2 transfer; absolute base rate remains an existing normalized model rate"),
            _flux("bile-export", "bile_export", "bile_acids_bilirubin_ATP", "bile_canaliculus", bile_export, "plasma_membrane_golgi", "bile_canaliculus", "Total ATP-dependent canalicular export abstraction"),
            _flux("maintenance", "ATP_maintenance", "ATP", "organelle_maintenance", maintenance, "shared_cell", "all_organelles", "baseline ATP spending"),
        )
    )
    return MetabolismStepResult(pools=pools, organelles=organelles, fluxes=tuple(fluxes))


def _update_local_atp(organelles: dict[str, OrganelleState], global_atp: float, dt_s: float) -> dict[str, OrganelleState]:
    mitochondria_location = organelles.get("mitochondria").location_um if "mitochondria" in organelles else (0.0, 0.0, 0.0)
    updated: dict[str, OrganelleState] = {}
    for organelle_id, organelle in organelles.items():
        distance_um = dist(mitochondria_location, organelle.location_um)
        delay_s = max(0.25, (distance_um * distance_um) / (6.0 * ATP_DIFFUSION_UM2_PER_S) * COARSE_MICRODOMAIN_DELAY_SCALE)
        transfer = 1.0 - exp(-dt_s / delay_s)
        previous = organelle.local_atp if organelle.local_atp > 0 else global_atp
        local_atp = previous + (global_atp - previous) * transfer
        updated[organelle_id] = replace(organelle, local_atp=clamp(local_atp, 0.0, 1.0), transport_delay_s=delay_s)
    return updated


def _apply_adenylate_delta(pools: dict[str, PoolState], atp_delta: float) -> None:
    current_atp = _pool(pools, "ATP")
    next_atp = clamp(current_atp + atp_delta, 0.02, 0.96)
    low_energy = ADENYLATE_TOTAL - next_atp
    amp_fraction = clamp(0.10 + (0.72 - next_atp) * 0.35, 0.05, 0.45)
    next_amp = clamp(low_energy * amp_fraction, 0.01, 0.55)
    next_adp = clamp(ADENYLATE_TOTAL - next_atp - next_amp, 0.01, 0.97)
    correction = ADENYLATE_TOTAL - (next_atp + next_adp + next_amp)
    next_adp += correction
    _set(pools, "ATP", next_atp)
    _set(pools, "ADP", next_adp)
    _set(pools, "AMP", next_amp)


def _pool(pools: dict[str, PoolState], id: str) -> float:
    return pools[id].value if id in pools else 0.0


def _set(pools: dict[str, PoolState], id: str, value: float) -> None:
    if id in pools:
        pools[id] = replace(pools[id], value=clamp(value, 0.0, 1.25))


def _add(pools: dict[str, PoolState], id: str, delta: float) -> None:
    if id in pools:
        _set(pools, id, pools[id].value + delta)


def _health(state: CellState, organelle_id: str) -> float:
    organelle = state.organelles.get(organelle_id)
    return organelle.health if organelle is not None else 0.75


def _surface_activity(state: CellState, control_id: str, gene_symbol: str) -> float:
    expression_value = _expression_activity(state, gene_symbol)
    control_value = state.model_controls.get(control_id)
    if expression_value is not None and control_value is not None and not isclose(expression_value, float(control_value), rel_tol=0.0, abs_tol=1e-12):
        raise ValueError(f"{control_id} conflicts with {gene_symbol} expression activity")
    value = float(control_value) if control_value is not None else (expression_value if expression_value is not None else 1.0)
    if not isfinite(value) or value < 0:
        raise ValueError(f"{control_id} must be finite and non-negative")
    return value


def _expression_activity(state: CellState, gene_symbol: str) -> float | None:
    if state.gene_expression is None or gene_symbol not in state.gene_expression.genes:
        return None
    return state.gene_expression.genes[gene_symbol].functional_protein_scale


def _optional_nonnegative_control(state: CellState, control_id: str) -> float | None:
    if control_id not in state.model_controls:
        return None
    value = float(state.model_controls[control_id])
    if not isfinite(value) or value < 0:
        raise ValueError(f"{control_id} must be finite and non-negative")
    return value


def _mean_health(state: CellState) -> float:
    if not state.organelles:
        return 1.0
    return sum(organelle.health for organelle in state.organelles.values()) / len(state.organelles)


def _mean_activity(state: CellState) -> float:
    if not state.organelles:
        return 0.0
    return sum(organelle.activity for organelle in state.organelles.values()) / len(state.organelles)


def _flux_value(rate_per_h: float, dt_h: float) -> float:
    return clamp(rate_per_h * dt_h, 0.0, 0.25)


def _flux(
    id: str,
    process: str,
    source: str,
    target: str,
    value: float,
    produced_by: str,
    consumed_by: str,
    notes: str,
) -> MetabolicFlux:
    return MetabolicFlux(
        id=id,
        process=process,
        source=source,
        target=target,
        value=value,
        unit="relative_pool_delta",
        produced_by=produced_by,
        consumed_by=consumed_by,
        notes=notes,
    )
