"""Human-liver-anchored apparent ATP turnover for the lumped PHH model."""

from __future__ import annotations

from cell_engine.core.provenance import ParameterProvenance
from cell_engine.quantitative.phh_profiles import phh_profile
from cell_engine.stochastic.reactions import ReactionNetwork, mass_action


APPARENT_ATP_SYNTHESIS_M_M_PER_MIN = 29.5
APPARENT_ATP_SYNTHESIS_M_M_PER_S = APPARENT_ATP_SYNTHESIS_M_M_PER_MIN / 60.0


def atp_turnover_rate_constants() -> tuple[float, float]:
    """Return synthesis-from-ADP and matched maintenance constants in 1/s.

    The 31P magnetization-transfer result is an apparent Pi-to-ATP exchange flux,
    not a claim about net mitochondrial production.  The reverse rate is derived
    so the measured baseline ATP and ADP pools are stationary in isolation.
    """
    profile = phh_profile()
    adp_M = profile.pools["ADP"].value_mM / 1000.0
    atp_M = profile.pools["ATP"].value_mM / 1000.0
    flux_M_per_s = APPARENT_ATP_SYNTHESIS_M_M_PER_S / 1000.0
    return flux_M_per_s / adp_M, flux_M_per_s / atp_M


def build_phh_atp_turnover_network(volume_l: float) -> ReactionNetwork:
    synthesis_k, maintenance_k = atp_turnover_rate_constants()
    common = dict(
        source_id="human_liver_atp_synthesis_2008",
        parameter_provenance=ParameterProvenance(
            name="apparent_hepatic_atp_exchange_flux",
            value=APPARENT_ATP_SYNTHESIS_M_M_PER_MIN,
            unit="mM_per_min",
            source_id="human_liver_atp_synthesis_2008",
            assumption_level="literature_derived",
            confidence=0.72,
            notes="In-vivo human-liver 31P saturation-transfer flux; first-order constants are derived around the PHH baseline pools.",
        ),
    )
    return ReactionNetwork(
        species=("ATP", "ADP", "AMP"),
        reactions=(
            mass_action("atp_regeneration", {"ADP": 1}, {"ATP": 1}, synthesis_k, notes="Apparent Pi-to-ATP exchange represented as lumped ADP-to-ATP regeneration.", **common),
            mass_action("atp_maintenance", {"ATP": 1}, {"ADP": 1}, maintenance_k, notes="Matched ATP demand keeps the measured baseline stationary before pathway loads.", **common),
        ),
        volume_l=volume_l,
    )
