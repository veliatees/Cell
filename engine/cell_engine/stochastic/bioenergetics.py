"""Exploratory ATP-turnover fixture derived from a human-liver observation.

The source measurement is an in-vivo, whole-liver apparent Pi-to-ATP exchange
flux.  It does not identify mitochondrial ATP production, cellular ATP demand,
or first-order ADP/ATP rate constants.  The executable mapping in this module is
therefore retained only for legacy software demonstrations and is explicitly
marked ``placeholder`` in reaction-level provenance.
"""

from __future__ import annotations

from cell_engine.core.provenance import ParameterProvenance, SourceReference
from cell_engine.quantitative.phh_profiles import phh_profile
from cell_engine.stochastic.reactions import ReactionNetwork, mass_action


APPARENT_PI_TO_ATP_EXCHANGE_M_M_PER_MIN = 29.5
APPARENT_PI_TO_ATP_EXCHANGE_M_M_PER_S = APPARENT_PI_TO_ATP_EXCHANGE_M_M_PER_MIN / 60.0

DATE_VERIFIED = "2026-07-20"

BIOENERGETICS_SOURCES: dict[str, SourceReference] = {
    "legacy_atp_exchange_fixture_v1": SourceReference(
        id="legacy_atp_exchange_fixture_v1",
        title="Legacy apparent-exchange to first-order ATP fixture",
        url="",
        source_type="project_assumption",
        date_verified=DATE_VERIFIED,
        notes=(
            "Software-only mapping from a whole-liver Pi-to-ATP exchange observation "
            "to matched ADP-to-ATP and ATP-to-ADP first-order reactions. The mapping "
            "is not a measured biological kinetic law."
        ),
    ),
}


def atp_turnover_rate_constants() -> tuple[float, float]:
    """Return the two legacy first-order fixture constants in 1/s.

    The 31P magnetization-transfer result is an apparent Pi-to-ATP exchange flux,
    not a claim about net mitochondrial production. The conversion below is an
    exploratory closure chosen to make the tissue-equivalent ATP and ADP values
    stationary in isolation; it is not eligible for quantitative validation.
    """
    profile = phh_profile()
    adp_M = profile.pools["ADP"].value_mM / 1000.0
    atp_M = profile.pools["ATP"].value_mM / 1000.0
    flux_M_per_s = APPARENT_PI_TO_ATP_EXCHANGE_M_M_PER_S / 1000.0
    return flux_M_per_s / adp_M, flux_M_per_s / atp_M


def build_phh_atp_turnover_network(volume_l: float) -> ReactionNetwork:
    """Build the legacy ATP fixture; never treat it as PHH kinetic authority."""

    synthesis_k, maintenance_k = atp_turnover_rate_constants()
    return ReactionNetwork(
        species=("ATP", "ADP", "AMP"),
        reactions=(
            mass_action(
                "atp_regeneration",
                {"ADP": 1},
                {"ATP": 1},
                synthesis_k,
                source_id="human_liver_atp_synthesis_2008",
                notes=(
                    "EXPLORATORY FIXTURE: whole-liver apparent Pi-to-ATP exchange "
                    "represented as lumped ADP-to-ATP regeneration."
                ),
                parameter_provenance=ParameterProvenance(
                    name="exploratory_adp_to_atp_first_order_rate",
                    value=synthesis_k,
                    unit="1_per_s",
                    source_id="legacy_atp_exchange_fixture_v1",
                    assumption_level="placeholder",
                    confidence=0.0,
                    notes=(
                        "Runtime value exactly matches the executable constant, but "
                        "the conversion from Pi-to-ATP exchange to ADP turnover is unmeasured."
                    ),
                ),
            ),
            mass_action(
                "atp_maintenance",
                {"ATP": 1},
                {"ADP": 1},
                maintenance_k,
                source_id="human_liver_atp_synthesis_2008",
                notes=(
                    "EXPLORATORY FIXTURE: a matched ATP demand keeps the selected "
                    "tissue-equivalent baseline stationary."
                ),
                parameter_provenance=ParameterProvenance(
                    name="exploratory_atp_to_adp_first_order_rate",
                    value=maintenance_k,
                    unit="1_per_s",
                    source_id="legacy_atp_exchange_fixture_v1",
                    assumption_level="placeholder",
                    confidence=0.0,
                    notes="Matched closure; not measured ATP demand in a human hepatocyte.",
                ),
            ),
        ),
        volume_l=volume_l,
    )
