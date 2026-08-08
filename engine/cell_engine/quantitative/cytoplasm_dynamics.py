"""Evidence boundary for healthy-PHH cytoplasm and organelle motion.

The registered studies establish that intracellular mobility depends on probe
size, interactions, active motors and biological context.  They do not identify
a healthy-primary-human-hepatocyte bulk-flow field or per-organelle motility
law.  In particular, a WIF-B9 Cx32 cargo velocity is not a cytosol velocity and
nanometre-probe mobility cannot be extrapolated into a micrometre-organelle
diffusion coefficient.

This module therefore exports observations and null parameter slots only.  The
browser may have a separate, explicitly dimensionless renderer-motion contract;
no value in this snapshot is allowed to parameterize it, reaction transport,
membrane mechanics or authoritative cell state.
"""

from __future__ import annotations

from dataclasses import dataclass, fields

from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain
from cell_engine.quantitative.cytosol_transport import CYTOSOL_TRANSPORT_SOURCES


DATE_VERIFIED = "2026-08-08"
VERSION = "cytoplasm_motion_authority_v2"

_SOURCE_IDS = (
    "kwapiszewska2020_cytoplasm_nanoviscosity",
    "swaminathan1997_gfp_cytoplasmic_diffusion",
    "fort2011_hepatocyte_connexin_kinesin_transport",
)

CYTOPLASM_DYNAMICS_SOURCES: dict[str, SourceReference] = {
    source_id: CYTOSOL_TRANSPORT_SOURCES[source_id]
    for source_id in _SOURCE_IDS
}


@dataclass(frozen=True)
class CytoplasmMotionObservation:
    id: str
    biological_system: str
    entity_or_probe: str
    observable: str
    value: float | tuple[float, float]
    uncertainty: float | None
    unit: str
    evidence_role: str
    interpretation: str
    healthy_phh_context_match: bool
    may_parameterize_healthy_phh_bulk_flow: bool
    may_parameterize_healthy_phh_organelle_motion: bool
    may_parameterize_reaction_transport: bool
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class HealthyPhhCytoplasmMotionParameterSlots:
    bulk_cytosol_velocity_um_s: None = None
    bulk_flow_coherence_length_um: None = None
    bulk_flow_coherence_time_s: None = None
    cytosol_dynamic_viscosity_pa_s: None = None
    organelle_diffusivity_um2_s: None = None
    organelle_active_velocity_um_s: None = None
    motor_engagement_fraction: None = None
    active_fluctuation_spectrum: None = None


OBSERVATIONS: tuple[CytoplasmMotionObservation, ...] = (
    CytoplasmMotionObservation(
        id="human_cell_line_nanoprobe_radius_range",
        biological_system=(
            "six human cell lines including HepG2; not primary human hepatocytes"
        ),
        entity_or_probe="FCS probes",
        observable="reported hydrodynamic-radius range",
        value=(0.65, 81.0),
        uncertainty=None,
        unit="nm",
        evidence_role="cross_context_scale_dependence_reference",
        interpretation=(
            "Supports probe-scale-dependent intracellular mobility; it does not "
            "identify micrometre-organelle diffusion or healthy-PHH rheology."
        ),
        healthy_phh_context_match=False,
        may_parameterize_healthy_phh_bulk_flow=False,
        may_parameterize_healthy_phh_organelle_motion=False,
        may_parameterize_reaction_transport=False,
        source_ids=("kwapiszewska2020_cytoplasm_nanoviscosity",),
    ),
    CytoplasmMotionObservation(
        id="cho_gfp_translational_relative_viscosity",
        biological_system="CHO cell cytoplasm",
        entity_or_probe="green fluorescent protein",
        observable="translational effective viscosity relative to aqueous saline",
        value=3.2,
        uncertainty=None,
        unit="dimensionless_ratio",
        evidence_role="cross_context_probe_specific_reference",
        interpretation=(
            "A CHO GFP mobility ratio is probe- and cell-context-specific and is "
            "not a whole-cytoplasm or organelle-scale viscosity."
        ),
        healthy_phh_context_match=False,
        may_parameterize_healthy_phh_bulk_flow=False,
        may_parameterize_healthy_phh_organelle_motion=False,
        may_parameterize_reaction_transport=False,
        source_ids=("swaminathan1997_gfp_cytoplasmic_diffusion",),
    ),
    CytoplasmMotionObservation(
        id="wif_b9_cx32_vesicle_speed",
        biological_system="polarized WIF-B9 hepatocyte cell line",
        entity_or_probe="microtubule-dependent Cx32 vesicle cargo",
        observable="directed cargo speed",
        value=0.246,
        uncertainty=0.032,
        unit="um/s",
        evidence_role="cross_context_cargo_transport_reference",
        interpretation=(
            "This is cargo-specific kinesin/microtubule transport, not bulk "
            "cytosol advection and not a universal organelle velocity."
        ),
        healthy_phh_context_match=False,
        may_parameterize_healthy_phh_bulk_flow=False,
        may_parameterize_healthy_phh_organelle_motion=False,
        may_parameterize_reaction_transport=False,
        source_ids=("fort2011_hepatocyte_connexin_kinesin_transport",),
    ),
)


@dataclass(frozen=True)
class CytoplasmDynamics:
    version: str
    status: str
    is_reaction_transport_authority: bool
    quantitative_runtime_enabled: bool
    biological_renderer_motion_enabled: bool
    authoritative_state_coupling_allowed: bool
    cross_context_cargo_speed_applied_to_bulk_flow: bool
    nanoprobe_viscosity_extrapolated_to_micron_organelles: bool
    stokes_einstein_organelle_diffusion_emitted: bool
    renderer_numeric_parameter_count: int
    healthy_phh_numeric_motion_parameter_count: int
    healthy_phh_organelle_motility_record_count: int
    cross_context_observations: tuple[CytoplasmMotionObservation, ...]
    healthy_phh_parameter_slots: HealthyPhhCytoplasmMotionParameterSlots
    grounded: tuple[str, ...]
    not_grounded: tuple[str, ...]
    blockers: tuple[str, ...]
    source_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def build_cytoplasm_dynamics(*, seed: int | None = None) -> CytoplasmDynamics:
    """Build the fail-closed evidence snapshot.

    ``seed`` remains accepted for compatibility with the retired visual model,
    but it cannot alter an evidence snapshot and has no numerical effect.
    """

    del seed
    result = CytoplasmDynamics(
        version=VERSION,
        status="cross_context_observations_healthy_phh_motion_blocked",
        is_reaction_transport_authority=False,
        quantitative_runtime_enabled=False,
        biological_renderer_motion_enabled=False,
        authoritative_state_coupling_allowed=False,
        cross_context_cargo_speed_applied_to_bulk_flow=False,
        nanoprobe_viscosity_extrapolated_to_micron_organelles=False,
        stokes_einstein_organelle_diffusion_emitted=False,
        renderer_numeric_parameter_count=0,
        healthy_phh_numeric_motion_parameter_count=0,
        healthy_phh_organelle_motility_record_count=0,
        cross_context_observations=OBSERVATIONS,
        healthy_phh_parameter_slots=HealthyPhhCytoplasmMotionParameterSlots(),
        grounded=(
            "probe-scale dependence in the source-specific human-cell-line context",
            "CHO GFP translational mobility in its source assay",
            "WIF-B9 Cx32 vesicle cargo speed in its source assay",
            "mechanistic separation of passive mobility, active cargo and bulk flow",
        ),
        not_grounded=(
            "healthy-PHH bulk cytosol velocity or coherent flow field",
            "healthy-PHH cytosol viscosity or poroelastic constitutive law",
            "per-organelle healthy-PHH diffusion or active-transport velocity",
            "motor engagement, pause, reversal or confinement distributions",
            "organelle-motion-to-membrane physical force calibration",
        ),
        blockers=(
            "matched healthy-PHH 3D intracellular particle/organelle trajectories are absent",
            "cargo- and organelle-resolved motor engagement measurements are absent",
            "matched PHH rheology, geometry and force-deformation trajectories are absent",
            "donor- and study-disjoint held-out motion validation is absent",
        ),
        source_ids=_SOURCE_IDS,
    )
    validate_cytoplasm_dynamics(result)
    return result


def validate_cytoplasm_dynamics(payload: CytoplasmDynamics) -> None:
    if payload.version != VERSION:
        raise ValueError("unexpected cytoplasm-motion authority version")
    if (
        payload.is_reaction_transport_authority
        or payload.quantitative_runtime_enabled
        or payload.biological_renderer_motion_enabled
        or payload.authoritative_state_coupling_allowed
    ):
        raise ValueError("cytoplasm motion escaped its healthy-PHH authority firewall")
    if (
        payload.cross_context_cargo_speed_applied_to_bulk_flow
        or payload.nanoprobe_viscosity_extrapolated_to_micron_organelles
        or payload.stokes_einstein_organelle_diffusion_emitted
    ):
        raise ValueError("cross-context cytoplasm evidence was extrapolated")
    if (
        payload.renderer_numeric_parameter_count != 0
        or payload.healthy_phh_numeric_motion_parameter_count != 0
        or payload.healthy_phh_organelle_motility_record_count != 0
    ):
        raise ValueError("unreviewed cytoplasm-motion numbers were promoted")
    if any(
        getattr(payload.healthy_phh_parameter_slots, field.name) is not None
        for field in fields(HealthyPhhCytoplasmMotionParameterSlots)
    ):
        raise ValueError("healthy-PHH cytoplasm-motion parameter slot is not null")
    for observation in payload.cross_context_observations:
        if (
            observation.healthy_phh_context_match
            or observation.may_parameterize_healthy_phh_bulk_flow
            or observation.may_parameterize_healthy_phh_organelle_motion
            or observation.may_parameterize_reaction_transport
        ):
            raise ValueError("cross-context observation gained PHH parameter authority")
        if not observation.source_ids or any(
            source_id not in CYTOPLASM_DYNAMICS_SOURCES
            for source_id in observation.source_ids
        ):
            raise ValueError("cytoplasm-motion observation has invalid provenance")
    if set(payload.source_ids) != set(CYTOPLASM_DYNAMICS_SOURCES):
        raise ValueError("cytoplasm-motion source registry is incomplete")


def cytoplasm_dynamics_snapshot(*, seed: int | None = None) -> dict[str, object]:
    return build_cytoplasm_dynamics(seed=seed).to_dict()
