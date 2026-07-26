from __future__ import annotations

from copy import deepcopy

import pytest

from cell_engine.quantitative.cytosol_transport import (
    ReactionTransportInputs,
    assess_reaction_transport_coupling,
    cytosol_transport_snapshot,
    validate_cytosol_transport_snapshot,
)


def test_cytosol_contract_exposes_real_cross_context_data_without_promoting_it_to_phh() -> None:
    snapshot = cytosol_transport_snapshot()
    validate_cytosol_transport_snapshot(snapshot)
    summary = snapshot["summary"]
    assert summary["cross_context_reference_count"] == 10
    assert summary["human_in_vivo_validation_target_count"] == 1
    assert summary["healthy_phh_numeric_rheology_parameter_count"] == 0
    assert summary["dimensionless_projection_solver_count"] == 1
    assert summary["conservative_passive_scalar_kernel_count"] == 1
    assert summary["conservative_moving_domain_remap_count"] == 1
    assert summary["dimensionless_active_cargo_route_kernel_count"] == 1
    assert summary["healthy_phh_active_transport_kernel_count"] == 0
    assert summary["active_cargo_trajectory_intake_contract_count"] == 1
    assert summary["delivered_phh_active_cargo_route_count"] == 0
    assert summary["structurally_complete_phh_active_cargo_route_count"] == 0
    assert summary["quantitatively_authorized_phh_active_cargo_route_count"] == 0
    assert summary["biological_species_bound_count"] == 0
    assert summary["moving_analytic_obstacle_layer_count"] == 1
    assert summary["analytic_obstacle_shape_count"] == 4
    assert summary["rigid_body_boundary_kinematics_count"] == 1
    assert summary["renderer_geometry_boundary_adapter_count"] == 1
    assert summary["renderer_geometry_boundary_class_count"] == 10
    assert summary["conservative_subgrid_boundary_treatment_count"] == 1
    assert summary["subgrid_boundary_grid_convergence_test_count"] == 1
    assert summary["local_star_shaped_membrane_boundary_coupling_count"] == 1
    assert summary["local_membrane_topology_change_coupling_count"] == 0
    assert summary["locally_conservative_membrane_face_flux_count"] == 1
    assert summary["fractional_face_aperture_solver_count"] == 1
    assert summary["generic_watertight_mesh_boundary_kernel_count"] == 1
    assert summary["repository_mesh_self_intersection_audit_count"] == 1
    assert summary["non_star_shaped_closed_mesh_domain_kernel_count"] == 1
    assert summary["dimensionless_pressure_membrane_response_kernel_count"] == 1
    assert summary["force_energy_consistency_test_count"] == 1
    assert summary["volume_preserving_fsi_candidate_test_count"] == 1
    assert summary["full_watertight_mesh_boundary_count"] == 0
    assert summary["compound_boundary_conservation_test_count"] == 1
    assert summary["membrane_pressure_feedback_count"] == 0
    assert summary["quantitative_fluid_solver_count"] == 0
    assert summary["reaction_transport_coupling_count"] == 0
    assert all(value is None for value in snapshot["healthy_phh_parameter_slots"].values())
    assert all(
        not observation.may_parameterize_healthy_phh
        for observation in snapshot["cross_context_reference_observations"]
    )
    target = snapshot["human_in_vivo_validation_targets"][0]
    assert target["participant_count"] == 3
    assert target["numeric_values_curated"] is False
    assert target["may_parameterize_viscosity_pressure_or_bulk_flow"] is False
    scalar = snapshot["solver_layers"]["conservative_passive_scalar_kernel"]
    assert scalar["moving_domain_mass_conservation_tested"] is True
    assert scalar["fractional_face_aperture_flux_weighting"] is True
    assert scalar["partial_cell_volume_mass_conservation_tested"] is True
    renderer = snapshot["solver_layers"]["renderer_dimensionless_projection_grid"]
    assert renderer["analytic_obstacle_shapes"] == (
        "sphere",
        "ellipsoid",
        "capsule",
        "box",
    )
    assert renderer["quaternion_derived_rotation_boundary_velocity"] is True
    assert renderer["subgrid_quadrature_samples_per_cell"] == 8
    assert renderer["subgrid_grid_convergence_tested"] is True
    assert renderer["face_aperture_quadrature_channels"] == 4
    assert renderer["fractional_face_aperture_flux_weighting"] is True
    assert renderer["fractional_face_aperture_pressure_weighting"] is True
    assert renderer["partial_cell_volume_conservation"] is True
    assert renderer["generic_watertight_triangle_mesh_boundary_kernel"] is True
    assert renderer["mesh_self_intersection_detection"] is True
    assert renderer["non_star_shaped_closed_mesh_domain_kernel"] is True
    assert renderer["closed_mesh_domain_self_intersection_audit"] is True
    assert renderer["closed_mesh_domain_biological_registration_count"] == 0
    assert renderer["membrane_topology_change_support"] is False
    assert renderer["registered_biological_mesh_boundary_count"] == 0
    assert renderer["full_watertight_mesh_boundaries"] is False
    assert renderer["local_star_shaped_membrane_boundary_coupling"] is True
    assert renderer["local_boundary_reference_space"] is True
    assert renderer["local_boundary_angular_bin_count"] == 512
    assert renderer["locally_conservative_membrane_face_flux"] is True
    assert renderer["outer_membrane_subgrid_volume_samples_per_cell"] == 8
    assert renderer["outer_membrane_face_area_samples"] == 4
    assert renderer["outer_membrane_geometric_conservation_source"] is True
    assert renderer["outer_membrane_volume_fraction_mass_remap"] is True
    assert renderer["multi_intersection_fold_or_topology_change_support"] is False
    active = snapshot["solver_layers"]["dimensionless_active_cargo_route_kernel"]
    assert active["enabled"] is True
    assert active["independent_per_frame_random_walk"] is False
    assert active["biological_velocity_claim"] is False
    assert active["healthy_phh_route_bound_count"] == 0
    assert active["delivered_phh_route_count"] == 0
    assert active["quantitatively_authorized_phh_route_count"] == 0
    fsi = snapshot["solver_layers"]["dimensionless_pressure_membrane_response_candidate"]
    assert fsi["enabled"] is True
    assert fsi["force_energy_consistency_tested"] is True
    assert fsi["volume_preservation_tested"] is True
    assert fsi["self_intersection_rejection"] is True
    assert fsi["runtime_feedback_enabled"] is False
    assert fsi["biological_pressure_assigned"] is False
    assert fsi["biological_compliance_assigned"] is False


@pytest.mark.parametrize(
    ("path", "unsafe_value"),
    (
        (("renderer_dimensionless_projection_grid", "biological_pressure_claim"), True),
        (("renderer_dimensionless_projection_grid", "membrane_pressure_feedback"), True),
        (("renderer_dimensionless_projection_grid", "full_watertight_mesh_boundaries"), True),
        (("dimensionless_pressure_membrane_response_candidate", "runtime_feedback_enabled"), True),
        (("conservative_passive_scalar_kernel", "biological_species_bound_count"), 1),
        (("dimensionless_active_cargo_route_kernel", "biological_velocity_claim"), True),
    ),
)
def test_unvalidated_numerical_layer_cannot_escape_into_biology(
    path: tuple[str, str], unsafe_value: object
) -> None:
    snapshot = deepcopy(cytosol_transport_snapshot())
    snapshot["solver_layers"][path[0]][path[1]] = unsafe_value
    with pytest.raises(ValueError):
        validate_cytosol_transport_snapshot(snapshot)


def test_missing_transport_evidence_cannot_modify_a_reaction() -> None:
    decision = assess_reaction_transport_coupling(
        ReactionTransportInputs(
            reaction_id="test",
            apparent_diffusivity_um2_s=None,
            characteristic_length_um=None,
            intrinsic_rate_per_s=None,
            diffusion_limitation_demonstrated=False,
            spatial_concentration_field_validated=False,
            context_match_confirmed=False,
            heldout_validation_confirmed=False,
            validated_direct_correction_law=None,
            source_ids=(),
        )
    )
    assert decision.diffusive_mixing_time_s is None
    assert decision.damkohler_number is None
    assert decision.local_concentration_coupling_allowed is False
    assert decision.direct_rate_correction_allowed is False
    assert decision.direct_rate_multiplier is None


def test_complete_synthetic_evidence_computes_timescale_but_never_infers_multiplier() -> None:
    decision = assess_reaction_transport_coupling(
        ReactionTransportInputs(
            reaction_id="synthetic_gate_test",
            apparent_diffusivity_um2_s=10.0,
            characteristic_length_um=3.0,
            intrinsic_rate_per_s=2.0,
            diffusion_limitation_demonstrated=True,
            spatial_concentration_field_validated=True,
            context_match_confirmed=True,
            heldout_validation_confirmed=True,
            validated_direct_correction_law="source-defined test law",
            source_ids=("synthetic_test_source",),
        )
    )
    assert decision.diffusive_mixing_time_s == pytest.approx(0.15)
    assert decision.damkohler_number == pytest.approx(0.3)
    assert decision.local_concentration_coupling_allowed is True
    assert decision.direct_rate_correction_allowed is True
    assert decision.direct_rate_multiplier is None
