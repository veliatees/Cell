from __future__ import annotations

from dataclasses import dataclass
from math import exp

from cell_engine.core.state import CellState, OrganelleState


@dataclass(frozen=True)
class HazardResult:
    organelle_id: str
    probability_per_hour: float
    stress_load: float
    dominant_axis: str
    event_probability: float


# Placeholder base probabilities until literature-derived hepatocyte rates are
# curated. The important M016 contract is that these are modulated by state.
BASE_PROBABILITY_PER_HOUR = {
    "plasma_membrane": 0.0020,
    "nucleus": 0.0012,
    "ribosome": 0.0015,
    "rough_er": 0.0020,
    "smooth_er": 0.0018,
    "golgi": 0.0017,
    "mitochondria": 0.0025,
    "lysosome_endosome": 0.0018,
    "peroxisome": 0.0015,
    "proteasome": 0.0013,
    "cytoskeleton": 0.0016,
    "cytosol_metabolism": 0.0014,
}

STRESS_WEIGHTS = {
    "plasma_membrane": {"energy": 0.5, "membrane": 1.2, "ionic": 0.9, "oxidative": 0.35, "cholestatic": 0.55},
    "nucleus": {"genotoxic": 1.4, "oxidative": 0.55, "senescence": 0.7, "energy": 0.25, "detox": 0.25},
    "ribosome": {"proteotoxic": 1.3, "energy": 0.55, "oxidative": 0.35},
    "rough_er": {"proteotoxic": 1.2, "trafficking": 0.75, "energy": 0.45, "ionic": 0.35, "detox": 1.05},
    "smooth_er": {"detox": 1.25, "oxidative": 0.65, "energy": 0.35, "ionic": 0.35, "cholestatic": 0.55},
    "golgi": {"trafficking": 1.4, "proteotoxic": 0.55, "energy": 0.45, "cholestatic": 0.5},
    "mitochondria": {"oxidative": 1.3, "energy": 0.6, "senescence": 0.45, "detox": 0.35},
    "lysosome_endosome": {"autophagy": 1.4, "oxidative": 0.55, "energy": 0.35, "senescence": 0.3, "detox": 0.3},
    "peroxisome": {"oxidative": 1.2, "detox": 0.75, "autophagy": 0.45, "senescence": 0.35},
    "proteasome": {"proteotoxic": 1.3, "energy": 0.55, "oxidative": 0.35, "autophagy": 0.25},
    "cytoskeleton": {"energy": 0.8, "membrane": 0.55, "trafficking": 0.75, "ionic": 0.45},
    "cytosol_metabolism": {"energy": 1.0, "ionic": 0.55, "oxidative": 0.35, "senescence": 0.3},
}


def state_conditioned_hazard(
    organelle_id: str,
    organelle: OrganelleState,
    state: CellState,
    *,
    dt_s: float,
) -> HazardResult:
    weights = STRESS_WEIGHTS.get(organelle_id, {})
    weighted = {axis: state.stress.get(axis, 0.0) * weight for axis, weight in weights.items()}
    dominant_axis = max(weighted, key=weighted.get) if weighted else "baseline"
    weight_total = sum(weights.values()) or 1.0
    stress_load = clamp(sum(weighted.values()) / weight_total, 0.0, 1.0)

    age_factor = clamp(organelle.age_h / (24.0 * 30.0), 0.0, 1.0)
    damage_factor = clamp(organelle.damage, 0.0, 1.0)
    low_health_factor = clamp(1.0 - organelle.health, 0.0, 1.0)

    base = BASE_PROBABILITY_PER_HOUR.get(organelle_id, 0.0015)
    probability_per_hour = base * (1.0 + 14.0 * stress_load + 7.0 * damage_factor + 3.0 * low_health_factor + 0.8 * age_factor)
    probability_per_hour = clamp(probability_per_hour, 0.0, 0.95)
    event_probability = 1.0 - exp(-probability_per_hour * max(dt_s, 0.0) / 3600.0)

    return HazardResult(
        organelle_id=organelle_id,
        probability_per_hour=probability_per_hour,
        stress_load=stress_load,
        dominant_axis=dominant_axis,
        event_probability=event_probability,
    )


def clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))

