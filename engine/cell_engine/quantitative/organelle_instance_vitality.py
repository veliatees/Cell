"""Per-instance organelle vitality — each individual organelle has its own life.

Until now the engine tracked ONE aggregate ``OrganelleState`` per organelle
*type* (all ~1000 mitochondria shared a single health value). Real organelle
populations are heterogeneous: individual mitochondria differ in membrane
potential and health, age independently, and are individually turned over
(mitophagy / pexophagy / autophagy) and replaced (biogenesis). This module gives
every drawn body its own **vitality** — a leaky-integrator "will-to-live" scalar
in ``[0, 1]`` that gates its activity, look and motion — so one mitochondrion can
be thriving while its neighbour declines, ages out and is cleared.

WHAT IS GROUNDED vs NOT
- Grounded (structure): organelle identities and counts (``hepatocyte_counts``),
  and the *existence* of per-organelle heterogeneity + individual turnover — both
  well-established cell biology (e.g. mitochondrial membrane-potential
  heterogeneity, mitophagy; peroxisome pexophagy; ER/Golgi as maintained
  networks rather than individually cleared bodies).
- NOT grounded (magnitudes): the baseline vitalities, per-instance spreads,
  turnover ages, leaky-integrator time constants, stress sensitivities and
  clearance thresholds are a **disclosed schematic model**, not calibrated to a
  matched PHH protocol. The per-instance values are a deterministic seeded
  realization, not a measured single-organelle fate trajectory.

FIREWALL: this is a **visual/kinematic** contract, exactly like
``cytoplasm_dynamics``. It sets no reaction rate, diffusivity or concentration
field; ``is_reaction_transport_authority`` is always ``False``. The magnitudes
here are the ones the pending donor injury / energy-redox trajectories would
calibrate.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log

from cell_engine.core.provenance import SourceReference
from cell_engine.core.random import EngineRng
from cell_engine.core.serialization import to_plain
from cell_engine.quantitative.organelle_placement import (
    PLACEMENT_SOURCES,
    build_organelle_placement,
)

DATE_VERIFIED = "2026-07-30"
VERSION = "organelle_instance_vitality_v1"


VITALITY_SOURCES: dict[str, SourceReference] = dict(PLACEMENT_SOURCES)
VITALITY_SOURCES["organelle_instance_vitality_model"] = SourceReference(
    id="organelle_instance_vitality_model",
    title="Per-instance organelle vitality as a disclosed leaky-integrator visual model",
    url="https://en.wikipedia.org/wiki/Mitophagy",
    source_type="project_assumption",
    date_verified=DATE_VERIFIED,
    notes=(
        "Per-organelle heterogeneity and individual turnover (mitophagy, "
        "pexophagy, autophagy, biogenesis) are established biology; the specific "
        "vitality baselines, spreads, turnover ages, time constants and clearance "
        "thresholds are an uncalibrated schematic model, not a matched PHH "
        "measurement. Per-instance values are a seeded realization."
    ),
)


def _clamp(value: float, low: float, high: float) -> float:
    return low if value < low else high if value > high else value


@dataclass(frozen=True)
class OrganelleVitalityModel:
    """Per-organelle-type vitality dynamics parameters (schematic magnitudes)."""

    organelle_id: str
    baseline_vitality: float  # target vitality of a healthy instance at rest (0..1)
    initial_vitality_spread: float  # per-instance heterogeneity (std, dimensionless)
    mean_turnover_age_h: float  # characteristic age at which turnover is likely
    recovery_time_constant_h: float  # leaky-integrator tau for vitality relaxation
    stress_sensitivity: float  # how strongly local stress lowers the vitality target
    clearance_vitality_threshold: float  # below this -> committed to autophagic clearance
    turns_over: bool  # whether cleared instances are replaced by biogenesis


# Per-type schematic model. Structure is grounded (which organelles turn over,
# relative fragility, network vs discrete bodies); magnitudes are disclosed.
_MODELS: tuple[OrganelleVitalityModel, ...] = (
    OrganelleVitalityModel("mitochondria", 0.85, 0.12, 120.0, 6.0, 0.60, 0.25, True),
    OrganelleVitalityModel("nucleus", 0.96, 0.02, 1.0e6, 24.0, 0.30, 0.05, False),
    OrganelleVitalityModel("lysosomes", 0.80, 0.15, 48.0, 4.0, 0.55, 0.22, True),
    OrganelleVitalityModel("peroxisomes", 0.82, 0.13, 60.0, 5.0, 0.50, 0.22, True),
    OrganelleVitalityModel("rough_er", 0.88, 0.08, 1.0e6, 8.0, 0.55, 0.05, False),
    OrganelleVitalityModel("smooth_er", 0.88, 0.08, 1.0e6, 8.0, 0.50, 0.05, False),
    OrganelleVitalityModel("golgi", 0.87, 0.08, 1.0e6, 8.0, 0.45, 0.05, False),
    OrganelleVitalityModel("ribosomes", 0.80, 0.10, 24.0, 3.0, 0.45, 0.20, True),
    OrganelleVitalityModel("centrosome", 0.90, 0.05, 1.0e6, 12.0, 0.35, 0.05, False),
)
_MODEL_BY_ID = {model.organelle_id: model for model in _MODELS}

# Organelle types the engine places as discrete solid bodies, so each body gets
# its own realized initial vitality. The others (ER/Golgi network, ribosomes,
# centrosome) carry only a type model; the renderer realizes their instances.
_DISCRETE_BODY_TYPES = ("nucleus", "mitochondria", "lysosomes", "peroxisomes")


@dataclass(frozen=True)
class OrganelleInstanceVitality:
    """One individual organelle body's own starting life."""

    organelle_id: str
    index: int
    vitality: float  # initial per-instance vitality (0..1)
    health: float  # initial per-instance health (0..1)
    age_h: float  # initial per-instance age
    decline_susceptibility: float  # per-instance fragility multiplier (~1)


@dataclass(frozen=True)
class OrganelleInstanceVitalityField:
    version: str
    is_reaction_transport_authority: bool
    models: tuple[OrganelleVitalityModel, ...]
    instances: tuple[OrganelleInstanceVitality, ...]
    instance_count_by_organelle: dict[str, int]
    honesty_status: str
    grounded: tuple[str, ...]
    not_grounded: tuple[str, ...]
    blockers: tuple[str, ...]
    source_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def _realize_instance(
    rng: EngineRng, model: OrganelleVitalityModel, organelle_id: str, index: int
) -> OrganelleInstanceVitality:
    # Age: exponential steady-state turnover distribution, mean = turnover age.
    u = _clamp(rng.random(), 1e-9, 1.0 - 1e-9)
    age_h = -model.mean_turnover_age_h * log(1.0 - u)
    # Older bodies sit a little lower; plus per-instance Gaussian heterogeneity.
    age_penalty = 0.15 * (age_h / (age_h + model.mean_turnover_age_h))
    vitality = _clamp(
        model.baseline_vitality + rng.gauss(0.0, model.initial_vitality_spread) - age_penalty,
        0.05,
        1.0,
    )
    # Health co-starts near vitality and diverges at runtime.
    health = _clamp(vitality * (0.94 + 0.06 * rng.random()), 0.05, 1.0)
    # Fragility multiplier, lognormal around 1 (some bodies decline faster).
    decline_susceptibility = _clamp(2.718281828 ** rng.gauss(0.0, 0.25), 0.4, 2.5)
    return OrganelleInstanceVitality(
        organelle_id=organelle_id,
        index=index,
        vitality=vitality,
        health=health,
        age_h=age_h,
        decline_susceptibility=decline_susceptibility,
    )


def build_organelle_instance_vitality(*, seed: int = 0) -> OrganelleInstanceVitalityField:
    """Per-instance starting vitality for every discrete organelle body, plus the
    per-type vitality dynamics model the renderer/engine steps at runtime."""
    placement = build_organelle_placement(seed=seed)
    rng = EngineRng(seed ^ 0x0173A17)  # disjoint stream from placement
    instances: list[OrganelleInstanceVitality] = []
    counts: dict[str, int] = {}
    for body in placement.bodies:
        model = _MODEL_BY_ID.get(body.organelle_id)
        if model is None or body.organelle_id not in _DISCRETE_BODY_TYPES:
            continue
        instances.append(_realize_instance(rng, model, body.organelle_id, body.index))
        counts[body.organelle_id] = counts.get(body.organelle_id, 0) + 1

    return OrganelleInstanceVitalityField(
        version=VERSION,
        is_reaction_transport_authority=False,
        models=_MODELS,
        instances=tuple(instances),
        instance_count_by_organelle=counts,
        honesty_status="per_instance_visual_vitality_grounded_structure_schematic_magnitudes",
        grounded=(
            "organelle identities and counts (hepatocyte_counts)",
            "existence of per-organelle heterogeneity and individual turnover "
            "(mitophagy/pexophagy/autophagy/biogenesis) — established cell biology",
        ),
        not_grounded=(
            "vitality baselines, per-instance spreads, turnover ages, time "
            "constants, stress sensitivities and clearance thresholds (schematic)",
            "each body's vitality/age is a seeded realization, not a measured "
            "single-organelle fate",
        ),
        blockers=(
            "not a reaction-transport authority: sets no rate, diffusivity or concentration",
            "magnitudes uncalibrated — pending donor injury / energy-redox trajectories",
        ),
        source_ids=tuple(VITALITY_SOURCES),
    )


def organelle_instance_vitality_snapshot(*, seed: int = 0) -> dict[str, object]:
    return build_organelle_instance_vitality(seed=seed).to_dict()
