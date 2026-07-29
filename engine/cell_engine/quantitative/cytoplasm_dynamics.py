"""Visual/kinematic cytoplasm dynamics for organelle motion.

Real hepatocyte organelle motion is dominated NOT by thermal Brownian diffusion
(which at the micrometre scale is tiny, because the cytoplasm's effective
viscosity grows strongly with probe size) but by **active, motor-driven
transport / cytoplasmic stirring**. This module supplies the grounded numbers a
renderer needs to move organelles the way a hepatocyte actually stirs them:

- a **length-scale-dependent effective viscosity** (Kwapiszewska 2020, measured
  in six human cell lines including the liver-derived HepG2), anchored at the
  small-probe end by GFP effective viscosity (Swaminathan 1997), giving a
  size-dependent **thermal** diffusion coefficient via Stokes-Einstein; and
- an **active-transport characteristic speed** taken from measured microtubule /
  kinesin vesicle speeds in a hepatocyte cell line (Fort 2011, WIF-B9, Cx32
  vesicles at 0.246 um/s), which sets the magnitude of the coherent stirring
  field that carries organelles together.

HONESTY / firewall:
- This is a **visual, kinematic** contract. It is NOT a reaction-transport
  authority: it never sets a reaction rate, a metabolite diffusivity, or a
  spatial concentration field. ``cytosol_transport`` deliberately forbids
  collapsing the scale-dependent cytoplasm into one viscosity *for reaction
  coupling*; that firewall is respected here because these numbers only animate
  geometry. ``is_reaction_transport_authority`` is always ``False``.
- The measured viscosity probes span 0.65-81 nm; applying the fit to
  micrometre organelles is an **explicit extrapolation** (flagged).
- The stirring field's coherence length/time are a disclosed visual model, not a
  measured cytoplasmic velocity field. The *speed* is grounded; the exact
  per-organelle engagement is not claimed.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, log, pi, sqrt

from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain
from cell_engine.quantitative.cytosol_transport import CYTOSOL_TRANSPORT_SOURCES
from cell_engine.quantitative.hepatocyte_counts import CELL_VOLUME_UM3
from cell_engine.quantitative.organelle_placement import build_organelle_placement

DATE_VERIFIED = "2026-07-29"
VERSION = "cytoplasm_dynamics_visual_v1"

# --- physical constants ------------------------------------------------------
BOLTZMANN_J_PER_K = 1.380649e-23  # exact (SI 2019)
BODY_TEMPERATURE_K = 310.15  # 37 C
# Water dynamic viscosity at 37 C (Pa*s). Reference physical property.
WATER_VISCOSITY_PA_S = 0.6913e-3

# --- grounded length-scale-dependent viscosity (Kwapiszewska 2020) -----------
# Major-crowder hydrodynamic radius and the length-scale-dependent-viscosity
# exponent are the pooled human-cell-line fits carried in cytosol_transport.
CROWDER_RADIUS_NM = 20.0
LSDV_EXPONENT = 0.57
# Small-probe anchor: GFP translational effective viscosity ~3.2x aqueous
# (Swaminathan 1997), GFP hydrodynamic radius ~2.5 nm. Used only to fix the
# single prefactor of the saturating viscosity law below.
GFP_HYDRODYNAMIC_RADIUS_NM = 2.5
GFP_RELATIVE_VISCOSITY = 3.2

# --- grounded active-transport speed (Fort 2011, WIF-B9 hepatocyte) ----------
ACTIVE_TRANSPORT_SPEED_UM_S = 0.246  # microtubule-dependent Cx32 vesicle speed
ACTIVE_TRANSPORT_SPEED_UNCERTAINTY_UM_S = 0.032

# --- disclosed visual stirring-field parameters (NOT measured) ---------------
# Coherence length as a fraction of the cell radius, and coherence time (s): a
# large, slowly-varying, incompressible field so organelles move together like a
# stirred medium rather than as independent noise.
STIR_COHERENCE_LENGTH_CELL_RADIUS_FRACTION = 0.35
STIR_COHERENCE_TIME_S = 6.0

CYTOPLASM_DYNAMICS_SOURCES: dict[str, SourceReference] = dict(CYTOSOL_TRANSPORT_SOURCES)


def _prefactor_b() -> float:
    """Fix the viscosity-law prefactor from the GFP small-probe anchor."""
    ratio = _effective_radius_nm(GFP_HYDRODYNAMIC_RADIUS_NM) / CROWDER_RADIUS_NM
    return log(GFP_RELATIVE_VISCOSITY) / (ratio ** LSDV_EXPONENT)


def _effective_radius_nm(probe_radius_nm: float) -> float:
    """Saturating effective radius: -> probe size for small probes, -> crowder
    size for large probes, so the viscosity law stays bounded at large scale."""
    return 1.0 / sqrt(1.0 / probe_radius_nm**2 + 1.0 / CROWDER_RADIUS_NM**2)


def relative_effective_viscosity(probe_radius_nm: float) -> float:
    """Effective cytoplasm viscosity relative to water for a probe of the given
    hydrodynamic radius (Kwapiszewska-style saturating length-scale law)."""
    if probe_radius_nm <= 0.0:
        raise ValueError("probe_radius_nm must be positive")
    ratio = _effective_radius_nm(probe_radius_nm) / CROWDER_RADIUS_NM
    return exp(_prefactor_b() * ratio ** LSDV_EXPONENT)


def thermal_diffusion_um2_s(radius_um: float) -> float:
    """Stokes-Einstein thermal diffusion coefficient (um^2/s) for a sphere of the
    given radius in the size-dependent cytoplasm. Tiny at the organelle scale."""
    if radius_um <= 0.0:
        raise ValueError("radius_um must be positive")
    radius_m = radius_um * 1.0e-6
    eta = relative_effective_viscosity(radius_um * 1000.0) * WATER_VISCOSITY_PA_S
    d_m2_s = BOLTZMANN_J_PER_K * BODY_TEMPERATURE_K / (6.0 * pi * eta * radius_m)
    return d_m2_s * 1.0e12  # m^2/s -> um^2/s


@dataclass(frozen=True)
class OrganelleMotility:
    organelle_id: str
    radius_um: float
    relative_effective_viscosity: float
    thermal_diffusion_um2_s: float


@dataclass(frozen=True)
class CytoplasmDynamics:
    version: str
    is_reaction_transport_authority: bool
    temperature_k: float
    water_viscosity_pa_s: float
    crowder_radius_nm: float
    lsdv_exponent: float
    active_transport_speed_um_s: float
    active_transport_speed_uncertainty_um_s: float
    stir_coherence_length_um: float
    stir_coherence_time_s: float
    organelle_motility: tuple[OrganelleMotility, ...]
    honesty_status: str
    grounded: tuple[str, ...]
    not_grounded: tuple[str, ...]
    blockers: tuple[str, ...]
    source_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def build_cytoplasm_dynamics(*, seed: int = 0) -> CytoplasmDynamics:
    """Per-organelle thermal motility plus the coherent active-stirring field
    magnitude, derived from the same grounded placement radii the renderer draws."""
    placement = build_organelle_placement(seed=seed)
    # One representative radius per discrete organelle type (all bodies of a type
    # share the equivalent-sphere radius).
    seen: dict[str, float] = {}
    for body in placement.bodies:
        seen.setdefault(body.organelle_id, body.radius_um)
    motility = tuple(
        OrganelleMotility(
            organelle_id=organelle_id,
            radius_um=radius_um,
            relative_effective_viscosity=relative_effective_viscosity(radius_um * 1000.0),
            thermal_diffusion_um2_s=thermal_diffusion_um2_s(radius_um),
        )
        for organelle_id, radius_um in sorted(seen.items())
    )
    cell_radius_um = placement.cell_envelope_radius_um
    return CytoplasmDynamics(
        version=VERSION,
        is_reaction_transport_authority=False,
        temperature_k=BODY_TEMPERATURE_K,
        water_viscosity_pa_s=WATER_VISCOSITY_PA_S,
        crowder_radius_nm=CROWDER_RADIUS_NM,
        lsdv_exponent=LSDV_EXPONENT,
        active_transport_speed_um_s=ACTIVE_TRANSPORT_SPEED_UM_S,
        active_transport_speed_uncertainty_um_s=ACTIVE_TRANSPORT_SPEED_UNCERTAINTY_UM_S,
        stir_coherence_length_um=STIR_COHERENCE_LENGTH_CELL_RADIUS_FRACTION * cell_radius_um,
        stir_coherence_time_s=STIR_COHERENCE_TIME_S,
        organelle_motility=motility,
        honesty_status=(
            "visual_kinematic_motion_grounded_in_hepatocyte_viscosity_and_active_transport_speed"
        ),
        grounded=(
            "length-scale-dependent effective viscosity (Kwapiszewska 2020, incl. HepG2)",
            "GFP small-probe effective-viscosity anchor (Swaminathan 1997)",
            "active-transport characteristic speed (Fort 2011, WIF-B9 hepatocyte, 0.246 um/s)",
            "Stokes-Einstein thermal diffusion law",
        ),
        not_grounded=(
            "effective viscosity extrapolated from 0.65-81 nm probes to um organelles",
            "coherent stirring-field length and time scales (disclosed visual model)",
            "per-organelle active-transport engagement (only the speed is measured)",
        ),
        blockers=(
            "not a reaction-transport authority: sets no rate, diffusivity or concentration field",
            "motion is a visual realization, not a measured per-organelle trajectory",
        ),
        source_ids=tuple(CYTOPLASM_DYNAMICS_SOURCES),
    )


def cytoplasm_dynamics_snapshot(*, seed: int = 0) -> dict[str, object]:
    return build_cytoplasm_dynamics(seed=seed).to_dict()
