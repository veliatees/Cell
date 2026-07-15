from __future__ import annotations

from dataclasses import replace

import pytest

from cell_engine import build_hepatocyte_definition, initial_hepatocyte_state
from cell_engine.multicell.spatial_world import (
    CONSERVATIVE_ELASTIC_AREA_STRAIN_CAP,
    ISOLATED_PHH_MEDIAN_DIAMETER_UM,
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
    initialize_spatial_world,
    move_body,
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


def test_reference_pair_uses_measured_isolated_phh_size_but_not_observed_arrangement() -> None:
    world = build_reference_hepatocyte_pair_world()
    body_a, body_b = world.bodies

    assert isinstance(body_a.shape, ConvexPolyhedronShape)
    assert body_a.shape.equivalent_sphere_radius_um * 2.0 == pytest.approx(ISOLATED_PHH_MEDIAN_DIAMETER_UM)
    assert len(body_a.shape.vertices_local_um) == 24
    assert len(body_a.shape.faces) == 14
    assert body_a.shape.deformation is not None
    assert body_b.shape.deformation is not None
    assert body_a.shape.deformation.axial_scale == pytest.approx(0.8635065679319692)
    assert body_a.shape.deformation.tangential_scale == pytest.approx(1.076136042851915)
    assert body_a.shape.deformation.volume_ratio == pytest.approx(1.0)
    assert body_a.shape.deformation.elastic_area_strain == pytest.approx(CONSERVATIVE_ELASTIC_AREA_STRAIN_CAP)
    assert body_b.center_um[1] < ISOLATED_PHH_MEDIAN_DIAMETER_UM
    assert world.pair_relations[0].relation == "touching"
    assert world.pair_relations[0].contact_patch_area_um2 == pytest.approx(50.53967278624878)
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
    state = cell_spatial_state_from_world(world, "hepatocyte_primary")
    assert state.active_contact_count == 0
    assert state.nearest_body_id is None
    assert state.contact_events == ()
    validate_spatial_world(world)


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
