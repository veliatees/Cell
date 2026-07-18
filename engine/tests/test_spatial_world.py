from __future__ import annotations

from dataclasses import replace
from math import sqrt

import pytest

from cell_engine import build_hepatocyte_definition, initial_hepatocyte_state
from cell_engine.multicell.spatial_world import (
    CONSERVATIVE_ELASTIC_AREA_STRAIN_CAP,
    HEPATOCYTE_REFERENCE_EQUIVALENT_SPHERE_DIAMETER_UM,
    CapsuleShape,
    ConvexPolyhedronShape,
    SpatialBody,
    SphereShape,
    apply_spatial_world_to_cell,
    build_canonical_hepatocyte_shape,
    build_hepatocyte_contact_diagnostic_world,
    build_intrinsic_hepatocyte_membrane_profile,
    build_reference_hepatocyte_pair_world,
    build_single_hepatocyte_world,
    cell_spatial_state_from_world,
    compute_pair_relation,
    body_support_distance_um,
    initialize_spatial_world,
    move_body,
    place_external_body_at_isotropic_approach,
    place_external_body_at_surface_gap,
    step_spatial_world,
    validate_spatial_world,
)


def _sphere(id: str, x: float, radius: float = 5.0) -> SpatialBody:
    return SpatialBody(id=id, biological_kind="cell", center_um=(x, 0.0, 0.0), shape=SphereShape(radius))


def test_sphere_pair_reports_signed_gap_and_closest_surface_points() -> None:
    separated = compute_pair_relation(_sphere("a", 0.0), _sphere("b", 12.0))
    tangent = compute_pair_relation(_sphere("a", 0.0), _sphere("b", 10.0))
    overlap = compute_pair_relation(_sphere("a", 0.0), _sphere("b", 9.0))

    assert separated.surface_gap_um == pytest.approx(2.0)
    assert separated.closest_point_a_um == pytest.approx((5.0, 0.0, 0.0))
    assert separated.closest_point_b_um == pytest.approx((7.0, 0.0, 0.0))
    assert separated.normal_a_to_b == pytest.approx((1.0, 0.0, 0.0))
    assert not separated.geometric_contact
    assert tangent.relation == "touching"
    assert tangent.surface_gap_um == pytest.approx(0.0)
    assert overlap.relation == "overlapping"
    assert overlap.overlap_depth_um == pytest.approx(1.0)
    assert overlap.contact_patch_area_um2 is None
    assert overlap.normal_load_nN is None


def test_sphere_capsule_and_capsule_capsule_use_finite_segments() -> None:
    capsule_a = SpatialBody(
        id="capsule_a",
        biological_kind="bacterium",
        center_um=(0.0, 0.0, 0.0),
        shape=CapsuleShape(radius_um=1.0, half_segment_length_um=2.0, axis=(0.0, 1.0, 0.0)),
    )
    sphere = SpatialBody(
        id="sphere",
        biological_kind="virus",
        center_um=(3.0, 0.0, 0.0),
        shape=SphereShape(radius_um=1.0),
    )
    capsule_b = SpatialBody(
        id="capsule_b",
        biological_kind="bacterium",
        center_um=(3.0, 0.0, 0.0),
        shape=CapsuleShape(radius_um=1.0, half_segment_length_um=2.0, axis=(0.0, 1.0, 0.0)),
    )

    sphere_capsule = compute_pair_relation(capsule_a, sphere)
    capsule_capsule = compute_pair_relation(capsule_a, capsule_b)

    assert sphere_capsule.surface_gap_um == pytest.approx(1.0)
    assert sphere_capsule.closest_point_a_um == pytest.approx((1.0, 0.0, 0.0))
    assert sphere_capsule.closest_point_b_um == pytest.approx((2.0, 0.0, 0.0))
    assert capsule_capsule.surface_gap_um == pytest.approx(1.0)


def test_convex_hepatocyte_supports_round_external_body_contact() -> None:
    shape = build_canonical_hepatocyte_shape()
    face_y = max(vertex[1] for vertex in shape.vertices_local_um)
    hepatocyte = SpatialBody(
        id="hepatocyte",
        biological_kind="hepatocyte",
        center_um=(0.0, 0.0, 0.0),
        shape=shape,
        membrane_material=build_intrinsic_hepatocyte_membrane_profile(),
    )
    virus_proxy = SpatialBody(
        id="virus_proxy",
        biological_kind="virus",
        center_um=(0.0, face_y + 0.5, 0.0),
        shape=SphereShape(0.5),
    )

    relation = compute_pair_relation(hepatocyte, virus_proxy)

    assert relation.relation == "touching"
    assert relation.contact_event == "enter"
    assert relation.contact_input_active
    assert relation.contact_patch_area_um2 is None
    assert relation.normal_a_to_b == pytest.approx((0.0, 1.0, 0.0))


def test_apical_and_basolateral_face_centres_resolve_to_unique_engine_domains() -> None:
    shape = build_canonical_hepatocyte_shape()
    support_x = max(vertex[0] for vertex in shape.vertices_local_um)
    hepatocyte = SpatialBody(
        id="hepatocyte",
        biological_kind="hepatocyte",
        center_um=(0.0, 0.0, 0.0),
        shape=shape,
        membrane_material=build_intrinsic_hepatocyte_membrane_profile(),
    )
    apical_probe = SpatialBody(
        id="apical_probe",
        biological_kind="virus",
        center_um=(support_x + 0.5, 0.0, 0.0),
        shape=SphereShape(0.5),
    )
    basolateral_probe = replace(
        apical_probe,
        id="basolateral_probe",
        center_um=(-(support_x + 0.5), 0.0, 0.0),
    )

    apical = compute_pair_relation(hepatocyte, apical_probe)
    basolateral = compute_pair_relation(hepatocyte, basolateral_probe)

    assert apical.membrane_domain_a == "apical"
    assert apical.contact_face_candidates_a == ("canalicular_pos_x",)
    assert apical.domain_assignment_status_a == "resolved_unique_face"
    assert basolateral.membrane_domain_a == "basolateral"
    assert basolateral.contact_face_candidates_a == ("sinusoidal_neg_x",)
    assert basolateral.domain_assignment_status_a == "resolved_unique_face"


def test_cross_domain_edge_contact_is_explicitly_ambiguous_and_fails_closed() -> None:
    shape = build_canonical_hepatocyte_shape()
    apical = next(face for face in shape.faces if face.id == "canalicular_pos_x")
    lateral = next(face for face in shape.faces if face.id == "lateral_hex_ppp")
    shared = tuple(set(apical.vertex_indices) & set(lateral.vertex_indices))
    edge_midpoint = tuple(
        sum(shape.vertices_local_um[index][axis] for index in shared) / len(shared)
        for axis in range(3)
    )
    inverse_sqrt_three = 1.0 / sqrt(3.0)
    raw_outward = (1.0 + inverse_sqrt_three, inverse_sqrt_three, inverse_sqrt_three)
    norm = sqrt(sum(value * value for value in raw_outward))
    outward = tuple(value / norm for value in raw_outward)
    radius = 0.5
    hepatocyte = SpatialBody(
        id="hepatocyte",
        biological_kind="hepatocyte",
        center_um=(0.0, 0.0, 0.0),
        shape=shape,
        membrane_material=build_intrinsic_hepatocyte_membrane_profile(),
    )
    probe = SpatialBody(
        id="edge_probe",
        biological_kind="virus",
        center_um=tuple(edge_midpoint[axis] + radius * outward[axis] for axis in range(3)),
        shape=SphereShape(radius),
    )

    relation = compute_pair_relation(hepatocyte, probe)

    assert relation.relation == "touching"
    assert relation.contact_face_a_id is None
    assert set(relation.contact_face_candidates_a) == {"canalicular_pos_x", "lateral_hex_ppp"}
    assert set(relation.membrane_domain_candidates_a) == {"apical", "lateral"}
    assert relation.membrane_domain_a is None
    assert relation.domain_assignment_status_a == "ambiguous_shared_feature_multiple_domains"


def test_shared_edge_within_one_domain_keeps_domain_but_not_an_arbitrary_face() -> None:
    shape = build_canonical_hepatocyte_shape()
    square = next(face for face in shape.faces if face.id == "lateral_neg_y")
    hexagon = next(face for face in shape.faces if face.id == "lateral_hex_nnn")
    shared = tuple(set(square.vertex_indices) & set(hexagon.vertex_indices))
    edge_midpoint = tuple(
        sum(shape.vertices_local_um[index][axis] for index in shared) / len(shared)
        for axis in range(3)
    )
    inverse_sqrt_three = 1.0 / sqrt(3.0)
    raw_outward = (-inverse_sqrt_three, -(1.0 + inverse_sqrt_three), -inverse_sqrt_three)
    norm = sqrt(sum(value * value for value in raw_outward))
    outward = tuple(value / norm for value in raw_outward)
    radius = 0.5
    hepatocyte = SpatialBody(
        id="hepatocyte",
        biological_kind="hepatocyte",
        center_um=(0.0, 0.0, 0.0),
        shape=shape,
        membrane_material=build_intrinsic_hepatocyte_membrane_profile(),
    )
    probe = SpatialBody(
        id="lateral_edge_probe",
        biological_kind="virus",
        center_um=tuple(edge_midpoint[axis] + radius * outward[axis] for axis in range(3)),
        shape=SphereShape(radius),
    )

    relation = compute_pair_relation(hepatocyte, probe)

    assert relation.contact_face_a_id is None
    assert set(relation.contact_face_candidates_a) == {"lateral_neg_y", "lateral_hex_nnn"}
    assert relation.membrane_domain_candidates_a == ("lateral",)
    assert relation.membrane_domain_a == "lateral"
    assert relation.domain_assignment_status_a == "resolved_shared_feature_same_domain"


def test_mixed_shape_relation_is_order_symmetric_and_rotation_preserves_local_domain() -> None:
    shape = build_canonical_hepatocyte_shape()
    support_x = max(vertex[0] for vertex in shape.vertices_local_um)
    material = build_intrinsic_hepatocyte_membrane_profile()
    hepatocyte = SpatialBody(
        id="hepatocyte",
        biological_kind="hepatocyte",
        center_um=(0.0, 0.0, 0.0),
        shape=shape,
        membrane_material=material,
    )
    probe = SpatialBody(
        id="probe",
        biological_kind="virus",
        center_um=(support_x + 0.5, 0.0, 0.0),
        shape=SphereShape(0.5),
    )
    forward = compute_pair_relation(hepatocyte, probe)
    reverse = compute_pair_relation(probe, hepatocyte)

    assert reverse.surface_gap_um == pytest.approx(forward.surface_gap_um)
    assert reverse.closest_point_a_um == pytest.approx(forward.closest_point_b_um)
    assert reverse.closest_point_b_um == pytest.approx(forward.closest_point_a_um)
    assert reverse.normal_a_to_b == pytest.approx(tuple(-value for value in forward.normal_a_to_b))
    assert reverse.membrane_domain_b == forward.membrane_domain_a == "apical"
    assert reverse.domain_assignment_status_b == forward.domain_assignment_status_a

    rotated = replace(hepatocyte, orientation_xyzw=(0.0, 0.0, 1.0, 0.0))
    rotated_probe = replace(probe, center_um=(-(support_x + 0.5), 0.0, 0.0))
    rotated_relation = compute_pair_relation(rotated, rotated_probe)
    assert rotated_relation.membrane_domain_a == "apical"
    assert rotated_relation.contact_face_candidates_a == ("canalicular_pos_x",)


def test_contact_lifecycle_is_edge_driven_without_a_duration_parameter() -> None:
    a = _sphere("a", 0.0)
    b = _sphere("b", 10.0)
    world = initialize_spatial_world((a, b))
    assert world.pair_relations[0].contact_event == "enter"
    assert world.pair_relations[0].contact_input_active
    assert not hasattr(world.pair_relations[0], "contact_duration_s")

    world = step_spatial_world(world, 2.0)
    assert world.pair_relations[0].contact_event == "stay"
    assert world.pair_relations[0].contact_input_active

    world = step_spatial_world(world, 3.0, bodies=(a, move_body(b, (12.0, 0.0, 0.0))))
    assert not world.pair_relations[0].geometric_contact
    assert world.pair_relations[0].contact_event == "exit"
    assert not world.pair_relations[0].contact_input_active

    world = step_spatial_world(world, 1.0, bodies=(a, b))
    assert world.pair_relations[0].geometric_contact
    assert world.pair_relations[0].contact_event == "enter"


def test_geometry_changes_cell_spatial_state_without_inventing_biochemistry() -> None:
    definition = build_hepatocyte_definition()
    initial = initial_hepatocyte_state(definition)
    contact_world = build_reference_hepatocyte_pair_world(time_s=initial.elapsed_s)
    contact_state = apply_spatial_world_to_cell(initial, contact_world, "hepatocyte_primary")

    neighbor = contact_world.bodies[1]
    separated_world = step_spatial_world(
        contact_world,
        1.0,
        bodies=(contact_world.bodies[0], move_body(neighbor, (30.0, 0.0, 0.0))),
    )
    separated_state = apply_spatial_world_to_cell(contact_state, separated_world, "hepatocyte_primary")

    assert contact_state.spatial_state is not None
    assert contact_state.spatial_state.active_contact_count == 1
    assert separated_state.spatial_state is not None
    assert separated_state.spatial_state.active_contact_count == 0
    assert separated_state.spatial_state.nearest_surface_gap_um > 0.0
    assert contact_state.pools == initial.pools == separated_state.pools
    assert contact_state.stress == initial.stress == separated_state.stress
    assert not contact_state.spatial_state.quantitative_biological_effects_enabled
    assert "blocked" in contact_state.spatial_state.biochemical_coupling_status


def test_reference_pair_uses_measured_in_situ_volume_scale_but_not_observed_arrangement() -> None:
    world = build_reference_hepatocyte_pair_world()
    body_a, body_b = world.bodies

    assert isinstance(body_a.shape, ConvexPolyhedronShape)
    assert body_a.shape.equivalent_sphere_radius_um * 2.0 == pytest.approx(
        HEPATOCYTE_REFERENCE_EQUIVALENT_SPHERE_DIAMETER_UM
    )
    assert len(body_a.shape.vertices_local_um) == 24
    assert len(body_a.shape.faces) == 14
    assert body_a.shape.deformation is not None
    assert body_b.shape.deformation is not None
    assert body_a.shape.deformation.axial_scale == pytest.approx(0.8635065679319692)
    assert body_a.shape.deformation.tangential_scale == pytest.approx(1.076136042851915)
    assert body_a.shape.deformation.volume_ratio == pytest.approx(1.0)
    assert body_a.shape.deformation.elastic_area_strain == pytest.approx(CONSERVATIVE_ELASTIC_AREA_STRAIN_CAP)
    assert body_b.center_um[1] < HEPATOCYTE_REFERENCE_EQUIVALENT_SPHERE_DIAMETER_UM
    assert world.pair_relations[0].relation == "touching"
    assert world.pair_relations[0].contact_patch_area_um2 == pytest.approx(72.95562674499428)
    assert len(world.pair_relations[0].contact_patch_polygon_um) == 4
    assert world.pair_relations[0].membrane_domain_a == "lateral"
    assert world.pair_relations[0].membrane_domain_b == "lateral"
    assert "fixture" in world.evidence_status
    assert world.geometry_drives_runtime_state
    assert not world.quantitative_biological_effects_enabled
    validate_spatial_world(world)


def test_contact_deformation_relaxes_to_rest_on_exit_without_a_contact_timer() -> None:
    world = build_hepatocyte_contact_diagnostic_world()
    primary, neighbor = world.bodies

    separated = step_spatial_world(
        world,
        1.0,
        bodies=(primary, move_body(neighbor, (0.0, 30.0, 0.0))),
    )

    assert separated.pair_relations[0].contact_event == "exit"
    assert not separated.pair_relations[0].contact_input_active
    assert isinstance(separated.bodies[0].shape, ConvexPolyhedronShape)
    assert isinstance(separated.bodies[1].shape, ConvexPolyhedronShape)
    assert separated.bodies[0].shape.deformation is None
    assert separated.bodies[1].shape.deformation is None
    assert not hasattr(separated.pair_relations[0], "contact_duration_s")


def test_excess_overlap_is_projected_out_instead_of_overstretching_surface() -> None:
    shape = build_canonical_hepatocyte_shape()
    material = build_intrinsic_hepatocyte_membrane_profile()
    primary = SpatialBody("primary", "hepatocyte", (0.0, 0.0, 0.0), shape, membrane_material=material)
    neighbor = SpatialBody("neighbor", "hepatocyte", (0.0, 8.0, 0.0), shape, membrane_material=material)

    world = initialize_spatial_world((primary, neighbor))

    assert world.pair_relations[0].relation == "touching"
    assert world.pair_relations[0].overlap_depth_um == pytest.approx(0.0)
    for body in world.bodies:
        assert isinstance(body.shape, ConvexPolyhedronShape)
        assert body.shape.deformation is not None
        assert body.shape.deformation.elastic_area_strain <= CONSERVATIVE_ELASTIC_AREA_STRAIN_CAP + 1.0e-9
        assert body.shape.deformation.volume_ratio == pytest.approx(1.0)
        assert "surface_cap_reached" in body.shape.deformation.status


def test_normal_runtime_has_one_hepatocyte_and_no_invented_neighbor() -> None:
    world = build_single_hepatocyte_world(time_s=12.0)

    assert world.scenario_kind == "single_hepatocyte"
    assert [body.id for body in world.bodies] == ["hepatocyte_primary"]
    assert world.pair_relations == ()
    material = world.bodies[0].membrane_material
    assert material is not None
    assert material.intrinsic_fluidity_enabled
    assert material.surface_representation == "deformable_area_constrained_mesh_plus_barycentric_surface_tracers"
    assert material.bilayer_thickness_nm is None
    assert material.area_compressibility_mN_per_m is None
    assert material.bending_rigidity_J is None
    assert material.lipid_lateral_diffusion_um2_s is None
    assert material.protein_lateral_diffusion_um2_s is None
    assert not material.quantitative_phh_mechanics_enabled
    assert all(not item.may_parameterize_healthy_phh for item in material.reference_measurements)
    thickness = {
        measurement.id: measurement
        for measurement in material.reference_measurements
        if "bilayer_thickness" in measurement.id
    }
    assert thickness["rat_hepatocyte_basolateral_bilayer_thickness"].value == pytest.approx(3.56)
    assert thickness["rat_hepatocyte_apical_bilayer_thickness"].value == pytest.approx(4.25)
    assert all(not measurement.may_parameterize_healthy_phh for measurement in thickness.values())
    state = cell_spatial_state_from_world(world, "hepatocyte_primary")
    assert state.active_contact_count == 0
    assert state.nearest_body_id is None
    assert state.contact_events == ()
    validate_spatial_world(world)


def test_external_body_placement_uses_declared_size_without_a_generic_contact_radius() -> None:
    primary = build_single_hepatocyte_world().bodies[0]
    direction = (0.0, 1.0, 0.0)
    small = SpatialBody("small", "virus", (0.0, 0.0, 0.0), SphereShape(0.5))
    large = SpatialBody("large", "cell", (0.0, 0.0, 0.0), SphereShape(4.0))

    placed_small = place_external_body_at_surface_gap(primary, small, direction)
    placed_large = place_external_body_at_surface_gap(primary, large, direction)
    small_relation = compute_pair_relation(primary, placed_small)
    large_relation = compute_pair_relation(primary, placed_large)

    assert placed_large.center_um[1] - placed_small.center_um[1] == pytest.approx(3.5)
    assert body_support_distance_um(small, direction) == pytest.approx(0.5)
    assert body_support_distance_um(large, direction) == pytest.approx(4.0)
    assert small_relation.surface_gap_um == pytest.approx(0.0, abs=1.0e-8)
    assert large_relation.surface_gap_um == pytest.approx(0.0, abs=1.0e-8)
    assert small_relation.contact_input_active
    assert large_relation.contact_input_active
    assert small_relation.contact_patch_area_um2 is None
    assert large_relation.contact_patch_area_um2 is None
    assert small_relation.contact_patch_polygon_um == ()
    assert large_relation.contact_patch_polygon_um == ()


def test_isotropic_approach_is_seeded_reproducible_and_not_a_fixed_surface_anchor() -> None:
    primary = build_single_hepatocyte_world().bodies[0]
    external = SpatialBody("probe", "other", (0.0, 0.0, 0.0), SphereShape(0.75))

    first = place_external_body_at_isotropic_approach(primary, external, random_seed=17)
    repeated = place_external_body_at_isotropic_approach(primary, external, random_seed=17)
    directions = [
        place_external_body_at_isotropic_approach(primary, external, random_seed=seed).outward_direction
        for seed in range(12)
    ]

    assert first == repeated
    assert sqrt(sum(component * component for component in first.outward_direction)) == pytest.approx(1.0)
    assert len({tuple(round(component, 8) for component in direction) for direction in directions}) == len(directions)
    assert any(direction[0] < 0.0 for direction in directions)
    assert any(direction[0] > 0.0 for direction in directions)
    assert any(direction[2] < 0.0 for direction in directions)
    assert any(direction[2] > 0.0 for direction in directions)
    assert compute_pair_relation(primary, first.body).surface_gap_um == pytest.approx(0.0, abs=1.0e-8)


def test_contact_placement_rejects_missing_size_or_invalid_direction() -> None:
    primary = build_single_hepatocyte_world().bodies[0]
    missing_size = SpatialBody("missing_size", "other", (0.0, 0.0, 0.0), SphereShape(0.0))
    probe = SpatialBody("probe", "other", (0.0, 0.0, 0.0), SphereShape(1.0))

    with pytest.raises(ValueError, match="radius_um"):
        place_external_body_at_surface_gap(primary, missing_size, (1.0, 0.0, 0.0))
    with pytest.raises(ValueError, match="non-zero"):
        place_external_body_at_surface_gap(primary, probe, (0.0, 0.0, 0.0))
    with pytest.raises(ValueError, match="random_seed"):
        place_external_body_at_isotropic_approach(primary, probe, random_seed=True)


def test_hepatocyte_body_without_intrinsic_membrane_material_fails_closed() -> None:
    body = SpatialBody(
        id="invalid_hepatocyte",
        biological_kind="hepatocyte",
        center_um=(0.0, 0.0, 0.0),
        shape=build_canonical_hepatocyte_shape(),
    )

    with pytest.raises(ValueError, match="intrinsic membrane material"):
        initialize_spatial_world((body,))


def test_world_validation_rejects_geometry_that_does_not_match_bodies() -> None:
    world = build_reference_hepatocyte_pair_world()
    relation = replace(world.pair_relations[0], closest_point_a_um=(8.0, 0.0, 0.0))

    with pytest.raises(ValueError, match="closest_point_a_um"):
        validate_spatial_world(replace(world, pair_relations=(relation,)))


def test_invalid_geometry_fails_closed() -> None:
    with pytest.raises(ValueError, match="radius_um"):
        initialize_spatial_world((_sphere("a", 0.0, radius=0.0),))
    with pytest.raises(ValueError, match="axis"):
        initialize_spatial_world(
            (
                SpatialBody(
                    id="bacterium",
                    biological_kind="bacterium",
                    center_um=(0.0, 0.0, 0.0),
                    shape=CapsuleShape(0.5, 1.0, (0.0, 0.0, 0.0)),
                ),
            )
        )
    with pytest.raises(ValueError, match="finite"):
        initialize_spatial_world((_sphere("nan", float("nan")),))
