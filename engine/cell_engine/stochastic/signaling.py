from __future__ import annotations

from dataclasses import dataclass

from cell_engine.core.provenance import SourceReference
from cell_engine.core.random import EngineRng
from cell_engine.processes.hepatocyte import build_hepatocyte_definition
from cell_engine.quantitative.geometry import (
    build_hepatocyte_geometry,
    molecules_from_concentration_mM,
)
from cell_engine.stochastic.cell_model import CYTOSOL, CellReactionModel
from cell_engine.stochastic.reactions import ReactionNetwork, mass_action

DATE_VERIFIED = "2026-06-21"

SIGNALING_SOURCES: dict[str, SourceReference] = {
    "hepatic_glucose_control": SourceReference(
        id="hepatic_glucose_control",
        title="Hormonal control of hepatic glucose metabolism (Koenig 2012; AMPK/CRTC2 axis, JCI)",
        url="https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1002577",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Insulin activates glycogen synthase and suppresses glucose output (fed); glucagon activates glycogen phosphorylase + gluconeogenesis (fasted); AMPK (low ATP/high AMP) drives catabolism. Enzymes switch between phospho/dephospho forms.",
    ),
}

# Real cytosolic volume of the canonical hepatocyte (same approach as
# glycolysis.seed_glycolysis_model and lipid.py): build the geometry from the
# hepatocyte definition and take the cytosol compartment volume (~1.77e-12 L).
# This puts seeded counts and concentrations on the real molar /
# hepatocyte-volume scale.
# NOTE: every reaction in build_glycogen_control_network is FIRST-ORDER
# mass_action, whose rate constant is volume-independent ((N_A*V)^(order-1) = 1),
# so the per-second rate constants and the hormone-activity logic are unchanged
# by this rescaling -- only the volume constant and the seed magnitudes change.
TRANSPORT_VOLUME_L = build_hepatocyte_geometry(build_hepatocyte_definition()).volume_of(CYTOSOL)


def _clamp01(x: float) -> float:
    return min(1.0, max(0.0, x))


@dataclass(frozen=True)
class HormoneState:
    insulin: float = 0.0   # 0..1 (fed signal)
    glucagon: float = 0.0  # 0..1 (fasted signal)
    ampk: float = 0.0      # 0..1 (energy stress; high AMP/low ATP)


FED = HormoneState(insulin=1.0, glucagon=0.0, ampk=0.0)
FASTED = HormoneState(insulin=0.0, glucagon=1.0, ampk=0.2)


def build_glycogen_control_network(hormones: HormoneState, volume_l: float = TRANSPORT_VOLUME_L) -> ReactionNetwork:
    """Hormone-controlled hepatic glycogen / glucose handling.

    Insulin -> glycogen synthase (store glucose). Glucagon + AMPK -> glycogen
    phosphorylase (mobilize glucose) and glucose export. Enzyme *activities* are
    set by the hormone state, the way phosphorylation switches the real enzymes.
    """
    synth_activity = _clamp01(hormones.insulin * (1.0 - hormones.ampk))
    break_activity = _clamp01(hormones.glucagon + hormones.ampk)
    export_activity = _clamp01(hormones.glucagon)

    species = ("glucose_cyto", "glycogen", "glucose_blood")
    reactions = (
        mass_action("glycogen_synthesis", {"glucose_cyto": 1}, {"glycogen": 1},
                    0.20 * synth_activity, source_id="hepatic_glucose_control",
                    notes="Glycogen synthase (insulin-activated, AMPK-inhibited)."),
        mass_action("glycogen_breakdown", {"glycogen": 1}, {"glucose_cyto": 1},
                    0.20 * break_activity, source_id="hepatic_glucose_control",
                    notes="Glycogen phosphorylase (glucagon/AMPK-activated)."),
        mass_action("glucose_export", {"glucose_cyto": 1}, {"glucose_blood": 1},
                    0.15 * export_activity, source_id="hepatic_glucose_control",
                    notes="Hepatic glucose output (fasted)."),
    )
    return ReactionNetwork(species=species, reactions=reactions, volume_l=volume_l)


def run_glycogen_control(hormones: HormoneState, t_end_s: float, rng: EngineRng,
                         *, glycogen_mM: float = 75.0, glucose_cyto_mM: float = 5.0,
                         dt_s: float = 0.05) -> dict[str, float]:
    """Run the hepatic glycogen/glucose control network on the real molar scale.

    ``glycogen_mM`` is the hepatic glycogen pool expressed in glucosyl units;
    the liver stores a large glycogen reserve, ~50-100 mM glucosyl equivalents
    (default 75 mM). ``glucose_cyto_mM`` is the free cytosolic glucose pool
    (~5 mM; default 5 mM). Both are converted to molecule counts in the real
    cytosolic volume via ``molecules_from_concentration_mM``.
    """
    network = build_glycogen_control_network(hormones)
    volume_l = network.volume_l
    counts = {
        "glucose_cyto": molecules_from_concentration_mM(glucose_cyto_mM, volume_l),
        "glycogen": molecules_from_concentration_mM(glycogen_mM, volume_l),
        "glucose_blood": 0.0,
    }
    return CellReactionModel(network=network, counts=counts).advance(t_end_s, rng, mode="cle", dt_s=dt_s).counts
