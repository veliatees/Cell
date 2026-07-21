"""Evidence-gated cytosol transport and rheology contract.

The cytoplasm is represented as a porous solid phase (cytoskeleton, organelles
and macromolecules) coupled to an interstitial aqueous cytosol.  The contract
does not collapse this scale-dependent material into one viscosity or one global
reaction-rate multiplier.
"""

from __future__ import annotations

from dataclasses import dataclass

from cell_engine.core.provenance import SourceReference
from cell_engine.processes.hepatocyte import build_hepatocyte_definition
from cell_engine.quantitative.geometry import HEPATOCYTE_REFERENCE_VOLUME_UM3


DATE_VERIFIED = "2026-07-22"
VERSION = "cytosol_transport_rheology_contract_v2"

CYTOSOL_TRANSPORT_SOURCES: dict[str, SourceReference] = {
    "moeendarbary2013_poroelastic_cytoplasm": SourceReference(
        id="moeendarbary2013_poroelastic_cytoplasm",
        title="The cytoplasm of living cells behaves as a poroelastic material",
        url="https://doi.org/10.1038/nmat3517",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Microindentation in HeLa, HT1080 and MDCK cells supports a biphasic porous "
            "solid/interstitial-fluid description. These are not primary hepatocytes."
        ),
    ),
    "kwapiszewska2020_cytoplasm_nanoviscosity": SourceReference(
        id="kwapiszewska2020_cytoplasm_nanoviscosity",
        title="Nanoscale Viscosity of Cytoplasm Is Conserved in Human Cell Lines",
        url="https://doi.org/10.1021/acs.jpclett.0c01748",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "FCS with probes spanning 0.65-81 nm hydrodynamic radius in six human cell "
            "lines, including HepG2, demonstrates length-scale-dependent effective viscosity."
        ),
    ),
    "swaminathan1997_gfp_cytoplasmic_diffusion": SourceReference(
        id="swaminathan1997_gfp_cytoplasmic_diffusion",
        title="Photobleaching recovery and anisotropy decay of GFP in solution and cells",
        url="https://doi.org/10.1016/S0006-3495(97)78835-0",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "CHO-cell GFP rotation and translation report different effective relative "
            "viscosities, supporting probe- and interaction-dependent intracellular mobility."
        ),
    ),
    "guo2017_cytoplasm_size_speed_mechanics": SourceReference(
        id="guo2017_cytoplasm_size_speed_mechanics",
        title="Size- and speed-dependent mechanical behavior in living mammalian cytoplasm",
        url="https://doi.org/10.1073/pnas.1616310114",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Optical-tweezer measurements in NRK and HeLa cells distinguish viscous, "
            "viscoelastic and poroelastic regimes by probe size and strain rate."
        ),
    ),
    "jiang2020_human_hepatocyte_diffusion_mri": SourceReference(
        id="jiang2020_human_hepatocyte_diffusion_mri",
        title="Mapping hepatocyte size in vivo using temporal diffusion spectroscopy MRI",
        url="https://doi.org/10.1002/mrm.28299",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "IMPULSED diffusion MRI in three healthy human volunteers estimated "
            "hepatocyte restriction size and intracellular-water diffusion distributions. "
            "It is a tissue-voxel water-transport validation target, not a measurement "
            "of cytosolic viscosity, pressure, bulk flow, or metabolite diffusivity."
        ),
    ),
    "guo2014_motor_driven_cytoplasm": SourceReference(
        id="guo2014_motor_driven_cytoplasm",
        title="Probing the stochastic, motor-driven properties of the cytoplasm using force spectrum microscopy",
        url="https://doi.org/10.1016/j.cell.2014.06.051",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Force-spectrum microscopy separates ATP-dependent active fluctuations "
            "from equilibrium thermal transport in mammalian cell systems. It does "
            "not provide a healthy-PHH active-noise parameter."
        ),
    ),
    "fort2011_hepatocyte_connexin_kinesin_transport": SourceReference(
        id="fort2011_hepatocyte_connexin_kinesin_transport",
        title="In vitro motility of liver connexin vesicles along microtubules utilizes kinesin motors",
        url="https://doi.org/10.1074/jbc.M111.219709",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Reports microtubule-dependent Cx32 vesicle motion in WIF-B9 cells and "
            "ATP-dependent motility of vesicles isolated from rat liver. Neither "
            "context is a healthy primary-human-hepatocyte transport calibration."
        ),
    ),
    "murray2008_primary_rat_hepatocyte_endosome_transport": SourceReference(
        id="murray2008_primary_rat_hepatocyte_endosome_transport",
        title="Single vesicle analysis of endocytic fission on microtubules in vitro",
        url="https://doi.org/10.1111/j.1600-0854.2008.00725.x",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Primary cultured rat hepatocytes show microtubule-based endosome motion, "
            "fusion/fission and sorting. This authorizes active/passive mode separation, "
            "not a human numerical rate."
        ),
    ),
}


@dataclass(frozen=True)
class CytosolReferenceObservation:
    id: str
    biological_system: str
    observable: str
    value: float
    uncertainty: float | None
    unit: str
    evidence_role: str
    may_parameterize_healthy_phh: bool
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class ReactionTransportInputs:
    reaction_id: str
    apparent_diffusivity_um2_s: float | None
    characteristic_length_um: float | None
    intrinsic_rate_per_s: float | None
    diffusion_limitation_demonstrated: bool
    spatial_concentration_field_validated: bool
    context_match_confirmed: bool
    heldout_validation_confirmed: bool
    validated_direct_correction_law: str | None
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class ReactionTransportDecision:
    reaction_id: str
    diffusive_mixing_time_s: float | None
    damkohler_number: float | None
    local_concentration_coupling_allowed: bool
    direct_rate_correction_allowed: bool
    direct_rate_multiplier: None
    blockers: tuple[str, ...]


REFERENCE_OBSERVATIONS: tuple[CytosolReferenceObservation, ...] = (
    CytosolReferenceObservation(
        "hela_poroelastic_diffusivity",
        "HeLa cervical-cancer cell line",
        "poroelastic diffusion coefficient",
        41.0,
        11.0,
        "um2/s",
        "cross_cell_type_material_reference",
        False,
        ("moeendarbary2013_poroelastic_cytoplasm",),
    ),
    CytosolReferenceObservation(
        "ht1080_poroelastic_diffusivity",
        "HT1080 fibrosarcoma cell line",
        "poroelastic diffusion coefficient",
        40.0,
        10.0,
        "um2/s",
        "cross_cell_type_material_reference",
        False,
        ("moeendarbary2013_poroelastic_cytoplasm",),
    ),
    CytosolReferenceObservation(
        "mdck_poroelastic_diffusivity",
        "MDCK epithelial cell line",
        "poroelastic diffusion coefficient",
        61.0,
        10.0,
        "um2/s",
        "cross_species_cell_line_material_reference",
        False,
        ("moeendarbary2013_poroelastic_cytoplasm",),
    ),
    CytosolReferenceObservation(
        "human_cell_line_crowder_radius",
        "pooled fit across six human cell lines including HepG2; not primary hepatocytes",
        "length-scale-dependent-viscosity major-crowder hydrodynamic radius",
        20.0,
        11.0,
        "nm",
        "cross_context_nanostructure_reference",
        False,
        ("kwapiszewska2020_cytoplasm_nanoviscosity",),
    ),
    CytosolReferenceObservation(
        "human_cell_line_intercrowder_gap",
        "pooled fit across six human cell lines including HepG2; not primary hepatocytes",
        "length-scale-dependent-viscosity intercrowder gap",
        4.6,
        0.7,
        "nm",
        "cross_context_nanostructure_reference",
        False,
        ("kwapiszewska2020_cytoplasm_nanoviscosity",),
    ),
    CytosolReferenceObservation(
        "human_cell_line_lsdv_exponent",
        "pooled fit across six human cell lines including HepG2; not primary hepatocytes",
        "length-scale-dependent-viscosity exponent",
        0.57,
        0.14,
        "dimensionless",
        "cross_context_model_fit",
        False,
        ("kwapiszewska2020_cytoplasm_nanoviscosity",),
    ),
    CytosolReferenceObservation(
        "cho_gfp_translational_relative_viscosity",
        "CHO cell cytoplasm",
        "GFP translational effective viscosity relative to aqueous saline",
        3.2,
        None,
        "dimensionless_ratio",
        "probe_and_cell_line_specific_reference",
        False,
        ("swaminathan1997_gfp_cytoplasmic_diffusion",),
    ),
    CytosolReferenceObservation(
        "cho_gfp_rotational_relative_viscosity",
        "CHO cell cytoplasm",
        "GFP rotational effective viscosity relative to water",
        1.5,
        None,
        "dimensionless_ratio",
        "probe_and_cell_line_specific_reference",
        False,
        ("swaminathan1997_gfp_cytoplasmic_diffusion",),
    ),
    CytosolReferenceObservation(
        "wif_b9_cx32_vesicle_speed",
        "polarized WIF-B9 hepatocyte cell line",
        "microtubule-dependent Cx32 vesicle speed",
        0.246,
        0.032,
        "um/s",
        "cross_context_active_transport_reference",
        False,
        ("fort2011_hepatocyte_connexin_kinesin_transport",),
    ),
    CytosolReferenceObservation(
        "rat_liver_isolated_cx32_vesicle_speed_midpoint",
        "Cx32 vesicles isolated from rat liver on stabilized microtubules in vitro",
        "ATP-dependent kinesin vesicle-speed interval midpoint",
        0.45,
        0.05,
        "um/s",
        "cross_species_in_vitro_active_transport_reference",
        False,
        ("fort2011_hepatocyte_connexin_kinesin_transport",),
    ),
)


def assess_reaction_transport_coupling(
    inputs: ReactionTransportInputs,
) -> ReactionTransportDecision:
    """Decide whether fluid transport may influence one reaction quantitatively.

    The characteristic diffusion time uses the three-dimensional mean-square
    displacement identity ``<r^2> = 6 D t``.  It is calculated only when the
    required measured quantities are positive.  No direct multiplier is ever
    inferred from this timescale or from a viscosity alone.
    """

    blockers: list[str] = []
    if not inputs.source_ids:
        blockers.append("transport evidence has no source ids")
    if inputs.apparent_diffusivity_um2_s is None or inputs.apparent_diffusivity_um2_s <= 0:
        blockers.append("positive context-matched apparent diffusivity is missing")
    if inputs.characteristic_length_um is None or inputs.characteristic_length_um <= 0:
        blockers.append("positive reaction-specific transport length is missing")
    if inputs.intrinsic_rate_per_s is None or inputs.intrinsic_rate_per_s < 0:
        blockers.append("non-negative intrinsic reaction timescale is missing")
    if not inputs.diffusion_limitation_demonstrated:
        blockers.append("diffusion limitation is not experimentally demonstrated")
    if not inputs.spatial_concentration_field_validated:
        blockers.append("spatial concentration field is not independently validated")
    if not inputs.context_match_confirmed:
        blockers.append("healthy-PHH biological and experimental context match is absent")
    if not inputs.heldout_validation_confirmed:
        blockers.append("donor-disjoint held-out validation is absent")

    numerical_inputs_ready = (
        inputs.apparent_diffusivity_um2_s is not None
        and inputs.apparent_diffusivity_um2_s > 0
        and inputs.characteristic_length_um is not None
        and inputs.characteristic_length_um > 0
        and inputs.intrinsic_rate_per_s is not None
        and inputs.intrinsic_rate_per_s >= 0
    )
    mixing_time = None
    damkohler = None
    if numerical_inputs_ready:
        mixing_time = (
            inputs.characteristic_length_um**2
            / (6.0 * inputs.apparent_diffusivity_um2_s)
        )
        damkohler = inputs.intrinsic_rate_per_s * mixing_time

    local_allowed = numerical_inputs_ready and not blockers
    if inputs.validated_direct_correction_law is None:
        blockers.append("validated reaction-specific direct correction law is absent")
    direct_allowed = local_allowed and inputs.validated_direct_correction_law is not None
    return ReactionTransportDecision(
        reaction_id=inputs.reaction_id,
        diffusive_mixing_time_s=mixing_time,
        damkohler_number=damkohler,
        local_concentration_coupling_allowed=local_allowed,
        direct_rate_correction_allowed=direct_allowed,
        direct_rate_multiplier=None,
        blockers=tuple(dict.fromkeys(blockers)),
    )


def cytosol_transport_snapshot() -> dict[str, object]:
    definition = build_hepatocyte_definition()
    cytosol = next(compartment for compartment in definition.compartments if compartment.id == "cytosol")
    if cytosol.volume_fraction is None:
        raise ValueError("legacy cytosol fraction unexpectedly disappeared without migration review")
    if any(observation.may_parameterize_healthy_phh for observation in REFERENCE_OBSERVATIONS):
        raise ValueError("cross-context rheology reference was promoted to healthy PHH")

    return {
        "version": VERSION,
        "status": "two_phase_transport_contract_active_healthy_phh_parameters_blocked",
        "material_model": {
            "model": "poroelastic_two_phase_cytoplasm",
            "fluid_phase": "aqueous cytosol carrying ions, metabolites and soluble macromolecules",
            "solid_phase": "cytoskeleton, organelles, membranes and macromolecular obstacles",
            "scale_dependence_required": True,
            "single_newtonian_viscosity_for_all_probes_prohibited": True,
            "source_ids": (
                "moeendarbary2013_poroelastic_cytoplasm",
                "kwapiszewska2020_cytoplasm_nanoviscosity",
                "guo2017_cytoplasm_size_speed_mechanics",
            ),
        },
        "governing_contract": {
            "species_balance": "partial_t(c_i) + div(u*c_i) = div(D_i*grad(c_i)) + R_i(c)",
            "incompressible_visual_mapping": "div(u) = 0 and det(F) = 1 for the affine moving-domain display map",
            "poroelastic_scaling": "D_p scales with E*xi^2/mu; no coefficient is assigned for healthy PHH",
            "advection_changes_reaction_state_via": "local reactant/product concentrations and boundary fluxes",
            "direct_viscosity_rate_multiplier": None,
            "global_crowding_multiplier_allowed": False,
        },
        "healthy_phh_parameter_slots": {
            "intracellular_water_volume_fraction": None,
            "aqueous_cytosol_volume_um3": None,
            "cytosol_dynamic_viscosity_Pa_s": None,
            "poroelastic_diffusivity_um2_s": None,
            "hydraulic_permeability_m2": None,
            "cytoskeletal_elastic_modulus_Pa": None,
            "crowder_size_distribution_nm": None,
            "species_apparent_diffusivity_um2_s": None,
            "intracellular_velocity_field_um_s": None,
            "pressure_field_Pa": None,
        },
        "measured_cell_geometry_context": {
            "normal_control_cell_volume_um3": HEPATOCYTE_REFERENCE_VOLUME_UM3,
            "value_role": "whole_cell_domain_scale_only",
            "may_initialize_aqueous_cytosol_volume": False,
            "source_id": "segovia_miranda2019_human_liver_3d_morphometry",
        },
        "human_in_vivo_validation_targets": (
            {
                "id": "healthy_human_liver_restricted_water_mri",
                "biological_system": "healthy adult human liver in vivo",
                "participant_count": 3,
                "measured_readouts": (
                    "hepatocyte restriction-size distribution",
                    "intracellular-water diffusion distribution",
                ),
                "numeric_values_curated": False,
                "validation_role": (
                    "future tissue-scale restricted-water and cell-size validation; "
                    "not a cytosol constitutive calibration"
                ),
                "may_parameterize_viscosity_pressure_or_bulk_flow": False,
                "source_ids": ("jiang2020_human_hepatocyte_diffusion_mri",),
            },
        ),
        "legacy_runtime_conflict": {
            "cytosol_volume_fraction": cytosol.volume_fraction,
            "authority": "legacy_model_fraction_without_healthy_human_morphometric_source",
            "used_by_exploratory_reaction_volume": True,
            "may_parameterize_quantitative_fluid_or_reaction_model": False,
            "migration_required": True,
        },
        "cross_context_reference_observations": REFERENCE_OBSERVATIONS,
        "transport_mode_contract": {
            "aqueous_passive_transport": {
                "carriers": "ions, metabolites and soluble macromolecules",
                "mechanisms": ("advection", "species-specific diffusion"),
                "numerical_kernel_available": True,
                "healthy_phh_species_bound": False,
            },
            "active_cargo_transport": {
                "carriers": "vesicles and organelle-associated cargo",
                "mechanisms": (
                    "ATP-dependent motor transport on cytoskeletal tracks",
                    "fusion, fission and sorting",
                ),
                "numerical_kernel_available": False,
                "healthy_phh_rate_bound": False,
                "cross_context_reference_only": True,
            },
            "mode_interchange_prohibited": True,
        },
        "solver_layers": {
            "renderer_dimensionless_projection_grid": {
                "enabled": True,
                "role": "dimensionless moving-domain visualization and numerical test bed",
                "membrane_volume_mapping": "same volume-preserving affine deformation as the rendered membrane",
                "moving_analytic_obstacle_boundaries": True,
                "static_anatomy_proxy_boundaries": True,
                "pressure_reaction_diagnostic_only": True,
                "biological_time_or_velocity_claim": False,
                "biological_pressure_claim": False,
                "membrane_pressure_feedback": False,
            },
            "conservative_passive_scalar_kernel": {
                "enabled": True,
                "role": "mass-conservation and non-negativity test bed",
                "boundary_condition": "no flux through analytic solid faces",
                "biological_species_bound_count": 0,
                "biological_diffusivity_claim": False,
            },
            "quantitative_poroelastic_solver": {
                "enabled": False,
                "reason": "healthy-PHH constitutive parameters and validation trajectories are unavailable",
            },
            "advection_diffusion_reaction_coupling": {
                "enabled": False,
                "reason": "species fields and reaction-specific transport gates are not validated",
            },
        },
        "reaction_coupling_policy": {
            "local_concentration_coupling": "allowed only per reaction after transport-gate validation",
            "direct_rate_correction": "requires a separate reaction-specific measured correction law",
            "global_rate_multiplier": "prohibited",
            "currently_coupled_reaction_count": 0,
        },
        "source_ids": tuple(CYTOSOL_TRANSPORT_SOURCES),
        "summary": {
            "cross_context_reference_count": len(REFERENCE_OBSERVATIONS),
            "human_in_vivo_validation_target_count": 1,
            "healthy_phh_numeric_rheology_parameter_count": 0,
            "dimensionless_projection_solver_count": 1,
            "conservative_passive_scalar_kernel_count": 1,
            "biological_species_bound_count": 0,
            "moving_analytic_obstacle_layer_count": 1,
            "membrane_pressure_feedback_count": 0,
            "quantitative_fluid_solver_count": 0,
            "reaction_transport_coupling_count": 0,
            "visual_fluid_layer_count": 1,
        },
        "blockers": (
            "No matched healthy primary-human-hepatocyte intracellular rheology dataset was identified.",
            "Whole-cell volume does not identify aqueous cytosol volume after organelle and macromolecule exclusion.",
            "HepG2 nanoviscosity is cancer-cell-line context and cannot initialize healthy PHH.",
            "Species-specific apparent diffusion and reaction-specific diffusion limitation are missing.",
            "Healthy-PHH motor-cargo rates and route-resolved validation trajectories are missing.",
            "Membrane pressure feedback requires measured PHH permeability, modulus and hydraulic boundary data.",
        ),
    }


def validate_cytosol_transport_snapshot(payload: dict[str, object]) -> None:
    if payload.get("version") != VERSION:
        raise ValueError("unexpected cytosol transport contract version")
    slots = payload.get("healthy_phh_parameter_slots")
    solvers = payload.get("solver_layers")
    coupling = payload.get("reaction_coupling_policy")
    conflict = payload.get("legacy_runtime_conflict")
    if not all(isinstance(item, dict) for item in (slots, solvers, coupling, conflict)):
        raise ValueError("cytosol transport contract is malformed")
    if any(value is not None for value in slots.values()):
        raise ValueError("healthy-PHH cytosol parameter was filled without evidence review")
    if solvers["quantitative_poroelastic_solver"]["enabled"] is not False:
        raise ValueError("quantitative cytosol solver cannot be active")
    if solvers["advection_diffusion_reaction_coupling"]["enabled"] is not False:
        raise ValueError("reaction-fluid coupling cannot be active")
    projection = solvers.get("renderer_dimensionless_projection_grid")
    scalar = solvers.get("conservative_passive_scalar_kernel")
    if not isinstance(projection, dict) or projection.get("enabled") is not True:
        raise ValueError("dimensionless projection layer is missing")
    if projection.get("biological_time_or_velocity_claim") is not False:
        raise ValueError("dimensionless projection escaped into a biological velocity claim")
    if projection.get("biological_pressure_claim") is not False:
        raise ValueError("dimensionless pressure escaped into a biological pressure claim")
    if projection.get("membrane_pressure_feedback") is not False:
        raise ValueError("unvalidated cytosol pressure feeds the membrane")
    if not isinstance(scalar, dict) or scalar.get("enabled") is not True:
        raise ValueError("conservative passive-scalar kernel is missing")
    if scalar.get("biological_species_bound_count") != 0:
        raise ValueError("passive-scalar kernel was bound to an unvalidated biological species")
    if scalar.get("biological_diffusivity_claim") is not False:
        raise ValueError("dimensionless scalar diffusion escaped into a biological claim")
    if coupling.get("currently_coupled_reaction_count") != 0:
        raise ValueError("cytosol transport contract activated a reaction")
    if conflict.get("may_parameterize_quantitative_fluid_or_reaction_model") is not False:
        raise ValueError("legacy cytosol fraction escaped quarantine")
