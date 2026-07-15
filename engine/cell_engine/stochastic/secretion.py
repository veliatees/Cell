"""Explicitly parameterized albumin pulse-chase transport network.

This module does not synthesize albumin from an amino-acid pseudo-pool and it
does not provide a default PHH secretion rate.  The available literature is
sufficient to establish the ER -> Golgi -> extracellular route, but the legacy
numeric transit defaults came from hepatoma systems and were not calibrated to
primary human hepatocytes.  Callers must therefore provide the two transit
half-times and label their evidence role.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, log
from typing import Literal

from cell_engine.core.provenance import SourceReference
from cell_engine.core.random import EngineRng
from cell_engine.quantitative.geometry import AVOGADRO
from cell_engine.stochastic.cell_model import CellReactionModel
from cell_engine.stochastic.reactions import ReactionNetwork, mass_action

DATE_VERIFIED = "2026-07-14"

SECRETION_SOURCES: dict[str, SourceReference] = {
    "lodish1983_hepg2_secretory_transit": SourceReference(
        id="lodish1983_hepg2_secretory_transit",
        title=(
            "Hepatoma secretory proteins migrate from rough endoplasmic "
            "reticulum to Golgi at characteristic rates"
        ),
        url="https://doi.org/10.1038/304080a0",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Pulse-chase evidence for selective ER-to-Golgi transit in human HepG2 hepatoma cells. "
            "It establishes pathway structure and system-dependent rates; it is not a numeric PHH calibration."
        ),
    ),
}

# All reactions below are unimolecular, so volume cancels from their mass-action
# propensities.  This convention keeps ReactionNetwork's required positive volume
# without implying a measured hepatocyte or assay volume.
UNIMOLECULAR_REFERENCE_VOLUME_L = 1.0 / AVOGADRO

ParameterEvidenceRole = Literal["measured_external_system", "fitted_to_model", "software_fixture"]


@dataclass(frozen=True)
class AlbuminPulseChaseParameters:
    er_to_golgi_half_time_s: float
    golgi_to_medium_half_time_s: float
    source_id: str
    experimental_system: str
    evidence_role: ParameterEvidenceRole


def validate_albumin_pulse_chase_parameters(parameters: AlbuminPulseChaseParameters) -> None:
    half_times = (parameters.er_to_golgi_half_time_s, parameters.golgi_to_medium_half_time_s)
    if any(not isfinite(value) or value <= 0.0 for value in half_times):
        raise ValueError("albumin pulse-chase half-times must be finite and positive")
    if not parameters.source_id or not parameters.experimental_system:
        raise ValueError("albumin pulse-chase parameters require source and experimental-system labels")
    if parameters.evidence_role == "measured_external_system" and parameters.source_id not in SECRETION_SOURCES:
        raise ValueError("measured external-system parameters require a registered primary source")
    if parameters.evidence_role == "software_fixture" and parameters.experimental_system != "software_test_only":
        raise ValueError("software-fixture parameters must be labelled software_test_only")


def _rate_from_half_time(t_half_s: float) -> float:
    return log(2.0) / t_half_s


def build_albumin_pulse_chase_network(
    parameters: AlbuminPulseChaseParameters,
    volume_l: float = UNIMOLECULAR_REFERENCE_VOLUME_L,
) -> ReactionNetwork:
    """Build a tracer-transport network without claiming albumin production.

    Species represent a pre-existing pulse-labelled albumin cohort.  Translation,
    precursor processing stoichiometry, degradation and total secretion capacity
    remain outside this network until PHH-specific measurements identify them.
    """
    validate_albumin_pulse_chase_parameters(parameters)
    species = (
        "pulse_labeled_proalbumin_er",
        "pulse_labeled_albumin_golgi",
        "pulse_labeled_albumin_medium",
    )
    reactions = (
        mass_action(
            "pulse_albumin_er_to_golgi",
            {"pulse_labeled_proalbumin_er": 1},
            {"pulse_labeled_albumin_golgi": 1},
            _rate_from_half_time(parameters.er_to_golgi_half_time_s),
            source_id=parameters.source_id,
            notes=f"Explicit {parameters.evidence_role} parameter; system={parameters.experimental_system}.",
        ),
        mass_action(
            "pulse_albumin_golgi_to_medium",
            {"pulse_labeled_albumin_golgi": 1},
            {"pulse_labeled_albumin_medium": 1},
            _rate_from_half_time(parameters.golgi_to_medium_half_time_s),
            source_id=parameters.source_id,
            notes=f"Explicit {parameters.evidence_role} parameter; system={parameters.experimental_system}.",
        ),
    )
    return ReactionNetwork(species=species, reactions=reactions, volume_l=volume_l)


def run_albumin_pulse_chase(
    t_end_s: float,
    rng: EngineRng,
    *,
    parameters: AlbuminPulseChaseParameters,
    initial_labeled_proalbumin: float,
    dt_s: float = 1.0,
) -> dict[str, float]:
    """Advance one explicitly parameterized labelled-albumin cohort."""
    if not isfinite(initial_labeled_proalbumin) or initial_labeled_proalbumin < 0.0:
        raise ValueError("initial labelled proalbumin count must be finite and non-negative")
    network = build_albumin_pulse_chase_network(parameters)
    counts = {species: 0.0 for species in network.species}
    counts["pulse_labeled_proalbumin_er"] = initial_labeled_proalbumin
    return CellReactionModel(network=network, counts=counts).advance(
        t_end_s,
        rng,
        mode="cle",
        dt_s=dt_s,
    ).counts
