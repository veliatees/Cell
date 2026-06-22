"""Integrated hepatic fasting response — the liver's coordinated fuel output.

Fasting is not one pathway but a coordinated program. When insulin falls and
glucagon/AMPK rise, the hepatocyte simultaneously:

- breaks down glycogen and exports glucose (``signaling.py``),
- makes new glucose from lactate/alanine and exports it (``gluconeogenesis.py``),
- oxidises fat and pours out ketone bodies (``ketogenesis.py``).

This module composes those three already-validated, hormone-gated networks into one
system with :func:`cell_engine.stochastic.reactions.compose_networks` — the
intended way scope grows here ("compose validated pathways rather than hand-write
one monolith"). Coupling is by shared species names:

- ``glucose_blood`` is shared, so glycogenolysis and gluconeogenesis **add** to the
  same blood-glucose output.
- ``NADH``/``NAD_plus`` are shared, so gluconeogenesis (which spends NADH at the
  reverse-GAPDH step) and beta-oxidation/ketogenesis (which makes NADH) draw on one
  redox pool. (A single matrix/cytosol redox pool is a deliberate simplification;
  the compartment distinction is flagged for a later split.)

The emergent, tested result: a FASTED hormone state raises **both** blood glucose
and ketone bodies; a FED state raises neither. This is the real integrated fasting
physiology of the liver.
"""

from __future__ import annotations

from dataclasses import dataclass

from cell_engine.core.random import EngineRng
from cell_engine.stochastic.cell_model import CellReactionModel
from cell_engine.stochastic.gluconeogenesis import (
    GluconeogenesisParams,
    build_gluconeogenesis_network,
)
from cell_engine.stochastic.ketogenesis import (
    FastingKetogenesisParams,
    build_hepatic_ketogenic_response,
    total_ketones,
)
from cell_engine.stochastic.reactions import ReactionNetwork, compose_networks
from cell_engine.stochastic.signaling import HormoneState, build_glycogen_control_network

GNG_VOLUME_L = build_gluconeogenesis_network(HormoneState()).volume_l


@dataclass(frozen=True)
class FastingResponseParams:
    gng: GluconeogenesisParams = GluconeogenesisParams()
    keto: FastingKetogenesisParams = FastingKetogenesisParams()


def build_fasting_fuel_response(
    hormones: HormoneState,
    params: FastingResponseParams = FastingResponseParams(),
    volume_l: float = GNG_VOLUME_L,
) -> ReactionNetwork:
    """Compose glycogenolysis + gluconeogenesis + ketogenesis under one hormone state."""
    return compose_networks(
        build_glycogen_control_network(hormones, volume_l),
        build_gluconeogenesis_network(hormones, params.gng, volume_l),
        build_hepatic_ketogenic_response(hormones, params.keto, volume_l),
        volume_l=volume_l,
    )


def run_fasting_response(
    hormones: HormoneState,
    t_end_s: float,
    rng: EngineRng,
    *,
    glycogen: float = 4000.0,
    glucose_cyto: float = 1000.0,
    lactate: float = 5000.0,
    fatty_acids: float = 6000.0,
    atp: float = 30000.0,
    nad_pool: float = 5000.0,
    params: FastingResponseParams = FastingResponseParams(),
    dt_s: float = 0.05,
) -> dict[str, float]:
    """Run the whole hepatic fuel program from glycogen, gluconeogenic substrate and
    fatty-acid stores at a given hormone state."""
    network = build_fasting_fuel_response(hormones, params)
    counts = {s: 0.0 for s in network.species}
    counts["glycogen"] = glycogen
    counts["glucose_cyto"] = glucose_cyto
    counts["lactate"] = lactate
    counts["fatty_acids"] = fatty_acids
    counts["ATP"] = atp
    counts["NAD_plus"] = nad_pool
    counts["NADH"] = nad_pool * 0.25
    return CellReactionModel(network=network, counts=counts).advance(
        t_end_s, rng, mode="cle", dt_s=dt_s
    ).counts


def blood_glucose(counts: dict[str, float]) -> float:
    """Glucose exported to blood (from glycogenolysis + gluconeogenesis)."""
    return counts["glucose_blood"]


def ketone_output(counts: dict[str, float]) -> float:
    """Total ketone bodies produced."""
    return total_ketones(counts)
