from __future__ import annotations

from dataclasses import replace

from cell_engine.core.random import EngineRng
from cell_engine.core.state import CellEvent, CellState, PoolState
from cell_engine.organelles.base import BasicOrganelleModule, FunctionalCycle
from cell_engine.stochastic.hazard import clamp

ADENYLATE_TOTAL = 1.0


class PlasmaMembraneModule(BasicOrganelleModule):
    def functional_cycle(self, dt_s: float, state: CellState, rng: EngineRng) -> FunctionalCycle:
        pools = dict(state.pools)
        current = state.organelles[self.id]
        atp = _pool(pools, "ATP")
        membrane_stress = state.stress.get("membrane", 0.0)
        transport = _flux(0.22 * current.health * atp * (1.0 - 0.45 * membrane_stress), dt_s)
        export = _flux(0.20 * current.health * atp * (1.0 - 0.35 * state.stress.get("cholestatic", 0.0)), dt_s)
        endocytosis = _flux(0.045 * current.health * (0.5 + 0.5 * atp), dt_s)

        _add(pools, "oxygen", 0.85 * transport)
        _add(pools, "glucose", 0.55 * transport)
        _add(pools, "amino_acids", 0.45 * transport)
        _add(pools, "urea", -0.70 * export)
        _add(pools, "detoxified_xenobiotic", -0.45 * export)
        _add(pools, "endocytosed_cargo", endocytosis)
        _shift_adenylate(pools, -0.10 * (transport + export + endocytosis))

        return _cycle(
            pools,
            ("selective_transport", "receptor_signaling", "endocytosis", "exocytosis"),
            activity=transport + export + endocytosis,
            damage_delta=0.003 * membrane_stress * dt_s / 3600.0,
        )


class NucleusModule(BasicOrganelleModule):
    def functional_cycle(self, dt_s: float, state: CellState, rng: EngineRng) -> FunctionalCycle:
        pools = dict(state.pools)
        current = state.organelles[self.id]
        atp = _pool(pools, "ATP")
        genotoxic = state.stress.get("genotoxic", 0.0)
        oxidative = state.stress.get("oxidative", 0.0)
        transcription = _flux(0.20 * current.health * atp * (1.0 - 0.55 * genotoxic), dt_s)
        processing_error = transcription * clamp(0.025 + 0.20 * genotoxic + 0.08 * oxidative, 0.0, 0.45)
        repair = _flux(0.10 * current.health * atp * (genotoxic + oxidative), dt_s)

        _add(pools, "mRNA", transcription - processing_error)
        _add(pools, "misfolded_protein", 0.15 * processing_error)
        _shift_adenylate(pools, -0.12 * transcription - 0.08 * repair)

        events = _maybe_event(
            rng,
            state,
            self.id,
            "nuclear_processing_error",
            "warn",
            0.025 * processing_error + 0.010 * genotoxic,
            "Nuclear transcription/splicing cycle produced error-prone output.",
        )
        return _cycle(
            pools,
            ("transcription", "splicing", "mRNA_export", "DNA_damage_response"),
            activity=transcription + repair,
            damage_delta=max(0.0, 0.004 * (genotoxic + oxidative) * dt_s / 3600.0 - 0.5 * repair),
            events=events,
        )


class RibosomeModule(BasicOrganelleModule):
    def functional_cycle(self, dt_s: float, state: CellState, rng: EngineRng) -> FunctionalCycle:
        pools = dict(state.pools)
        current = state.organelles[self.id]
        atp = _pool(pools, "ATP")
        amino_acids = _pool(pools, "amino_acids")
        mRNA = _pool(pools, "mRNA")
        proteotoxic = state.stress.get("proteotoxic", 0.0)
        translation = _flux(0.42 * current.health * atp * amino_acids * mRNA * (1.0 - 0.35 * proteotoxic), dt_s)
        error_fraction = clamp(0.025 + 0.18 * proteotoxic + 0.12 * (1.0 - atp) + 0.08 * (1.0 - amino_acids), 0.0, 0.42)
        misfolded = translation * error_fraction
        useful = translation - misfolded

        _add(pools, "mRNA", -0.22 * translation)
        _add(pools, "amino_acids", -0.85 * translation)
        _add(pools, "cytosolic_protein", 0.48 * useful)
        _add(pools, "secretory_protein_cargo", 0.42 * useful)
        _add(pools, "misfolded_protein", misfolded)
        _shift_adenylate(pools, -0.28 * translation)

        return _cycle(
            pools,
            ("translation", "elongation", "ribosome_quality_control", "ER_targeting"),
            activity=translation,
            damage_delta=0.004 * proteotoxic * dt_s / 3600.0,
        )


class RoughErModule(BasicOrganelleModule):
    def functional_cycle(self, dt_s: float, state: CellState, rng: EngineRng) -> FunctionalCycle:
        pools = dict(state.pools)
        current = state.organelles[self.id]
        atp = _pool(pools, "ATP")
        ca_factor = clamp(_pool(pools, "Ca2+") + 0.35, 0.0, 1.0)
        proteotoxic = state.stress.get("proteotoxic", 0.0)
        ionic = state.stress.get("ionic", 0.0)
        folding = _flux(0.36 * current.health * atp * ca_factor * _pool(pools, "secretory_protein_cargo"), dt_s)
        success_fraction = clamp(0.86 - 0.30 * proteotoxic - 0.16 * ionic, 0.25, 0.95)
        folded = folding * success_fraction
        misfolded = folding - folded
        erad = _flux(0.24 * current.health * atp * _pool(pools, "misfolded_protein"), dt_s)
        upr_activity = clamp(_pool(pools, "misfolded_protein") + proteotoxic, 0.0, 1.0)

        _add(pools, "secretory_protein_cargo", -folding)
        _add(pools, "folded_cargo", folded)
        _add(pools, "misfolded_protein", misfolded - erad)
        _add(pools, "ubiquitinated_cargo", erad)
        _shift_adenylate(pools, -0.22 * folding - 0.10 * erad)

        events = _maybe_event(
            rng,
            state,
            self.id,
            "upr_pulse",
            "warn",
            0.018 * upr_activity,
            "Rough ER activated a UPR-like folding and ERAD response.",
        )
        return _cycle(
            pools,
            ("protein_folding", "glycosylation_start", "ER_quality_control", "ERAD"),
            activity=(folding + erad) * (1.0 - 0.45 * proteotoxic),
            damage_delta=0.010 * upr_activity * dt_s / 3600.0,
            capacity_delta=0.015 * upr_activity * dt_s / 3600.0,
            events=events,
        )


class SmoothErModule(BasicOrganelleModule):
    def functional_cycle(self, dt_s: float, state: CellState, rng: EngineRng) -> FunctionalCycle:
        pools = dict(state.pools)
        current = state.organelles[self.id]
        detox_stress = state.stress.get("detox", 0.0)
        nadph = _pool(pools, "NADPH")
        gsh = _pool(pools, "GSH")
        detox = _flux(0.20 * current.health * _pool(pools, "xenobiotic") * nadph * gsh, dt_s)
        lipid_synthesis = _flux(0.22 * current.health * _pool(pools, "fatty_acids") * nadph, dt_s)

        _add(pools, "xenobiotic", -detox)
        _add(pools, "detoxified_xenobiotic", detox)
        _add(pools, "NADPH", -0.70 * detox - 0.22 * lipid_synthesis)
        _add(pools, "GSH", -0.40 * detox)
        _add(pools, "GSSG", 0.25 * detox)
        _add(pools, "ROS", 0.12 * detox)
        _add(pools, "fatty_acids", -0.60 * lipid_synthesis)
        _add(pools, "lipids", 0.55 * lipid_synthesis)
        _add(pools, "cholesterol", 0.20 * lipid_synthesis)

        return _cycle(
            pools,
            ("CYP_detox", "lipid_synthesis", "cholesterol_bile_coupling", "calcium_storage"),
            activity=detox + lipid_synthesis,
            damage_delta=0.006 * detox_stress * dt_s / 3600.0,
        )


class GolgiModule(BasicOrganelleModule):
    def functional_cycle(self, dt_s: float, state: CellState, rng: EngineRng) -> FunctionalCycle:
        pools = dict(state.pools)
        current = state.organelles[self.id]
        atp = _pool(pools, "ATP")
        trafficking = state.stress.get("trafficking", 0.0)
        cholestatic = state.stress.get("cholestatic", 0.0)
        processing = _flux(0.34 * current.health * atp * _pool(pools, "folded_cargo") * (1.0 - 0.42 * trafficking), dt_s)
        error_fraction = clamp(0.03 + 0.22 * trafficking + 0.12 * cholestatic, 0.0, 0.38)
        sorted_cargo = processing * (1.0 - error_fraction)
        sorting_error = processing - sorted_cargo

        _add(pools, "folded_cargo", -processing)
        _add(pools, "albumin", 0.42 * sorted_cargo)
        _add(pools, "membrane_cargo", 0.24 * sorted_cargo)
        _add(pools, "lysosome_enzyme_cargo", 0.16 * sorted_cargo)
        _add(pools, "canalicular_cargo", 0.18 * sorted_cargo)
        _add(pools, "misfolded_protein", 0.30 * sorting_error)
        _add(pools, "endocytosed_cargo", 0.20 * sorting_error)
        _shift_adenylate(pools, -0.18 * processing)

        events = _maybe_event(
            rng,
            state,
            self.id,
            "golgi_sorting_error",
            "warn",
            0.020 * sorting_error + 0.008 * trafficking,
            "Golgi sorting/glycosylation cycle produced a misrouted fraction.",
        )
        return _cycle(
            pools,
            ("glycosylation_maturation", "sorting", "vesicle_budding", "polarized_delivery"),
            activity=processing,
            damage_delta=0.006 * trafficking * dt_s / 3600.0,
            events=events,
        )


class MitochondriaModule(BasicOrganelleModule):
    def functional_cycle(self, dt_s: float, state: CellState, rng: EngineRng) -> FunctionalCycle:
        pools = dict(state.pools)
        current = state.organelles[self.id]
        oxygen = _pool(pools, "oxygen")
        substrate = clamp(0.55 * _pool(pools, "pyruvate") + 0.30 * _pool(pools, "fatty_acids") + 0.15 * _pool(pools, "NADH"), 0.0, 1.0)
        adp_drive = clamp(_pool(pools, "ADP") + 0.55 * _pool(pools, "AMP"), 0.0, 1.0)
        oxidative = state.stress.get("oxidative", 0.0)
        oxidation = _flux(0.28 * current.health * oxygen * substrate * adp_drive * (1.0 - 0.35 * oxidative), dt_s)
        mitophagy_commit = _flux(0.14 * (current.damage + oxidative) * _pool(pools, "ATP"), dt_s)

        _add(pools, "oxygen", -0.60 * oxidation)
        _add(pools, "pyruvate", -0.42 * oxidation)
        _add(pools, "fatty_acids", -0.22 * oxidation)
        _add(pools, "NADH", -0.18 * oxidation)
        _add(pools, "NAD+", 0.18 * oxidation)
        _add(pools, "ROS", 0.05 * oxidation * (0.30 + oxidative))
        _add(pools, "autophagy_cargo", mitophagy_commit)
        _add(pools, "damaged_organelle_mass", -0.25 * mitophagy_commit)
        _shift_adenylate(pools, 1.15 * oxidation - 0.10 * mitophagy_commit)

        events = _maybe_event(
            rng,
            state,
            self.id,
            "mitochondrial_quality_control",
            "info",
            0.012 * mitophagy_commit,
            "Mitochondria committed damaged material to mitophagy/autophagy cargo.",
        )
        return _cycle(
            pools,
            ("TCA", "OXPHOS", "ATP_production", "ROS_balance", "mitophagy_commit"),
            activity=oxidation + mitophagy_commit,
            damage_delta=0.004 * oxidative * dt_s / 3600.0 - 0.20 * mitophagy_commit,
            events=events,
        )


class LysosomeEndosomeModule(BasicOrganelleModule):
    def functional_cycle(self, dt_s: float, state: CellState, rng: EngineRng) -> FunctionalCycle:
        pools = dict(state.pools)
        current = state.organelles[self.id]
        atp = _pool(pools, "ATP")
        cargo_load = _pool(pools, "endocytosed_cargo") + _pool(pools, "autophagy_cargo")
        autophagy_stress = state.stress.get("autophagy", 0.0)
        degradation = _flux(0.40 * current.health * atp * cargo_load * (1.0 - 0.30 * autophagy_stress), dt_s)
        endocytic_fraction = _pool(pools, "endocytosed_cargo") / max(cargo_load, 1e-9)

        _add(pools, "endocytosed_cargo", -degradation * endocytic_fraction)
        _add(pools, "autophagy_cargo", -degradation * (1.0 - endocytic_fraction))
        _add(pools, "amino_acids", 0.42 * degradation)
        _add(pools, "lipids", 0.20 * degradation)
        _add(pools, "damaged_organelle_mass", -0.35 * degradation)
        _shift_adenylate(pools, -0.12 * degradation)

        return _cycle(
            pools,
            ("endocytosed_cargo_degradation", "autophagy_completion", "organelle_turnover", "receptor_recycling"),
            activity=degradation,
            damage_delta=0.008 * autophagy_stress * dt_s / 3600.0,
        )


class PeroxisomeModule(BasicOrganelleModule):
    def functional_cycle(self, dt_s: float, state: CellState, rng: EngineRng) -> FunctionalCycle:
        pools = dict(state.pools)
        current = state.organelles[self.id]
        oxidative = state.stress.get("oxidative", 0.0)
        oxygen = _pool(pools, "oxygen")
        lipid_load = _pool(pools, "very_long_chain_fatty_acids") + 0.35 * _pool(pools, "fatty_acids")
        beta_oxidation = _flux(0.26 * current.health * oxygen * lipid_load, dt_s)
        catalase = _flux(0.32 * current.health * _pool(pools, "ROS") * (_pool(pools, "GSH") + 0.25), dt_s)

        _add(pools, "very_long_chain_fatty_acids", -0.65 * beta_oxidation)
        _add(pools, "fatty_acids", -0.22 * beta_oxidation)
        _add(pools, "acetyl_CoA", 0.30 * beta_oxidation)
        _add(pools, "ROS", 0.06 * beta_oxidation - catalase)
        _add(pools, "GSH", -0.08 * catalase)
        _add(pools, "GSSG", 0.05 * catalase)

        return _cycle(
            pools,
            ("very_long_chain_fatty_acid_oxidation", "H2O2_catalase_balance", "lipid_metabolism", "ROS_buffering"),
            activity=beta_oxidation + catalase,
            damage_delta=max(0.0, 0.003 * oxidative * dt_s / 3600.0 - 0.12 * catalase),
        )


class ProteasomeModule(BasicOrganelleModule):
    def functional_cycle(self, dt_s: float, state: CellState, rng: EngineRng) -> FunctionalCycle:
        pools = dict(state.pools)
        current = state.organelles[self.id]
        atp = _pool(pools, "ATP")
        proteotoxic = state.stress.get("proteotoxic", 0.0)
        substrate_load = _pool(pools, "ubiquitinated_cargo") + 0.55 * _pool(pools, "misfolded_protein")
        degradation = _flux(0.46 * current.health * atp * substrate_load * (1.0 - 0.25 * proteotoxic), dt_s)
        ubiquitinated_fraction = _pool(pools, "ubiquitinated_cargo") / max(substrate_load, 1e-9)

        _add(pools, "ubiquitinated_cargo", -degradation * ubiquitinated_fraction)
        _add(pools, "misfolded_protein", -0.55 * degradation * (1.0 - ubiquitinated_fraction))
        _add(pools, "amino_acids", 0.62 * degradation)
        _shift_adenylate(pools, -0.14 * degradation)

        events = _maybe_event(
            rng,
            state,
            self.id,
            "proteasome_saturation",
            "warn",
            0.010 * substrate_load * proteotoxic,
            "Proteasome degradation load approached saturation.",
        )
        return _cycle(
            pools,
            ("misfolded_protein_degradation", "ERAD_degradation", "regulatory_protein_turnover"),
            activity=degradation,
            damage_delta=0.006 * proteotoxic * dt_s / 3600.0,
            events=events,
        )


class CytoskeletonModule(BasicOrganelleModule):
    def functional_cycle(self, dt_s: float, state: CellState, rng: EngineRng) -> FunctionalCycle:
        pools = dict(state.pools)
        current = state.organelles[self.id]
        atp = _pool(pools, "ATP")
        trafficking = state.stress.get("trafficking", 0.0)
        motor_work = _flux(0.18 * current.health * atp * (1.0 - 0.35 * trafficking), dt_s)
        _shift_adenylate(pools, -0.08 * motor_work)
        return _cycle(
            pools,
            ("organelle_positioning", "vesicle_transport", "cell_polarity", "mechanical_integrity"),
            activity=motor_work,
            damage_delta=0.005 * trafficking * dt_s / 3600.0,
            capacity_delta=(0.010 * atp - 0.012 * trafficking) * dt_s / 3600.0,
        )


class CytosolMetabolismModule(BasicOrganelleModule):
    def functional_cycle(self, dt_s: float, state: CellState, rng: EngineRng) -> FunctionalCycle:
        pools = dict(state.pools)
        current = state.organelles[self.id]
        energy = state.stress.get("energy", 0.0)
        buffering = _flux(0.12 * current.health * _pool(pools, "ATP") * (1.0 - 0.45 * energy), dt_s)
        _add(pools, "lactate", -0.10 * buffering)
        _add(pools, "pyruvate", 0.08 * buffering)
        _shift_adenylate(pools, -0.04 * buffering)
        return _cycle(
            pools,
            ("glycolysis", "pH_buffering", "metabolite_diffusion", "local_availability"),
            activity=buffering,
            damage_delta=0.002 * energy * dt_s / 3600.0,
        )


def _cycle(
    pools: dict[str, PoolState],
    active_processes: tuple[str, ...],
    *,
    activity: float,
    damage_delta: float = 0.0,
    capacity_delta: float = 0.0,
    events: tuple[CellEvent, ...] = (),
) -> FunctionalCycle:
    return FunctionalCycle(
        pools=pools,
        active_processes=active_processes,
        activity=clamp(0.20 + 4.2 * activity, 0.0, 1.25),
        damage_delta=damage_delta,
        capacity_delta=capacity_delta,
        events=events,
    )


def _pool(pools: dict[str, PoolState], id: str) -> float:
    pool = pools.get(id)
    return pool.value if pool is not None else 0.0


def _add(pools: dict[str, PoolState], id: str, delta: float) -> None:
    if id not in pools or delta == 0.0:
        return
    pool = pools[id]
    pools[id] = replace(pool, value=clamp(pool.value + delta, 0.0, 1.25))


def _set(pools: dict[str, PoolState], id: str, value: float) -> None:
    if id in pools:
        pool = pools[id]
        pools[id] = replace(pool, value=clamp(value, 0.0, 1.25))


def _shift_adenylate(pools: dict[str, PoolState], atp_delta: float) -> None:
    if not {"ATP", "ADP", "AMP"}.issubset(pools):
        return
    next_atp = clamp(_pool(pools, "ATP") + atp_delta, 0.02, 0.96)
    low_energy = ADENYLATE_TOTAL - next_atp
    amp_fraction = clamp(0.10 + (0.72 - next_atp) * 0.35, 0.05, 0.45)
    next_amp = clamp(low_energy * amp_fraction, 0.01, 0.55)
    next_adp = clamp(ADENYLATE_TOTAL - next_atp - next_amp, 0.01, 0.97)
    correction = ADENYLATE_TOTAL - (next_atp + next_adp + next_amp)
    next_adp += correction
    _set(pools, "ATP", next_atp)
    _set(pools, "ADP", next_adp)
    _set(pools, "AMP", next_amp)


def _flux(rate_per_h: float, dt_s: float) -> float:
    return clamp(rate_per_h * dt_s / 3600.0, 0.0, 0.18)


def _maybe_event(
    rng: EngineRng,
    state: CellState,
    organelle_id: str,
    suffix: str,
    severity: str,
    probability: float,
    text: str,
) -> tuple[CellEvent, ...]:
    if rng.random() >= clamp(probability, 0.0, 0.35):
        return ()
    return (
        CellEvent(
            id=f"{organelle_id}_{suffix}_{int(state.elapsed_s)}",
            t_s=state.elapsed_s,
            severity=severity,
            text=text,
        ),
    )
