from __future__ import annotations

from copy import deepcopy

import pytest

from cell_engine.quantitative.geometry import (
    HEPATOCYTE_REFERENCE_EQUIVALENT_SPHERE_DIAMETER_UM,
    HEPATOCYTE_REFERENCE_VOLUME_UM3,
    hepatocyte_geometry_reference_snapshot,
    sphere_volume_um3_from_diameter,
)
from cell_engine.quantitative.human_hepatocyte_3d_morphometry import (
    HUMAN_NC_3D_HEPATOCYTE_MEDIAN_VOLUME_UM3,
    HUMAN_NC_3D_HEPATOCYTE_VOLUME_MAD_UM3,
    HUMAN_NC_3D_LIPID_DROPLET_VOLUME_FRACTION,
    human_hepatocyte_3d_morphometry_snapshot,
    load_human_hepatocyte_3d_morphometry,
    validate_human_hepatocyte_3d_morphometry,
)


def test_checksummed_source_and_study_scope_are_retained() -> None:
    payload = load_human_hepatocyte_3d_morphometry()
    artifact = payload["source_artifact"]
    study = payload["study_context"]
    assert artifact["downloaded_bytes"] == 104382
    assert artifact["md5"] == "7dcf837c391ae5433cbeb507d6baf534"
    assert artifact["sha256"] == (
        "ab282a593c9b66fd95f764271625f73cd3c5ab33746c8f757c6c60fa2b8ffc3f"
    )
    assert study["normal_control_reconstruction_count"] == 5
    assert study["all_group_reconstruction_count"] == 16
    assert study["all_group_analyzed_cell_count"] == 11278
    assert study["voxel_size_um"] == [0.3, 0.3, 0.3]


def test_normal_control_3d_measurements_drive_only_allowed_aggregates() -> None:
    snapshot = human_hepatocyte_3d_morphometry_snapshot()
    volume = snapshot["normal_control_cell_volume_um3"]
    lipid = snapshot["normal_control_lipid_droplet_volume_percent"]
    gates = snapshot["integration_gates"]
    assert volume["overall"] == HUMAN_NC_3D_HEPATOCYTE_MEDIAN_VOLUME_UM3
    assert volume["overall_mad"] == HUMAN_NC_3D_HEPATOCYTE_VOLUME_MAD_UM3
    assert len(volume["regional_medians"]) == 10
    assert lipid["fraction_of_cell_volume"] == HUMAN_NC_3D_LIPID_DROPLET_VOLUME_FRACTION
    assert lipid["may_define_droplet_count_or_size_distribution"] is False
    assert lipid["may_define_dynamic_nutritional_response"] is False
    assert gates["may_initialize_reference_volume"] is True
    assert gates["may_initialize_aggregate_lipid_fraction"] is True
    assert gates["individual_cell_boundary_mesh_available"] is False
    assert gates["may_calibrate_contact_patch_ground_truth"] is False


def test_direct_3d_reference_supersedes_but_does_not_average_stereology() -> None:
    reference = hepatocyte_geometry_reference_snapshot()
    canonical = reference["canonical_reference"]
    historical = reference["historical_in_situ_stereology_cross_check"]
    assert HEPATOCYTE_REFERENCE_VOLUME_UM3 == 5657.07116
    assert canonical["cell_volume_um3"] == HEPATOCYTE_REFERENCE_VOLUME_UM3
    assert historical["mean_cell_volume_um3"] == 2850.0
    assert historical["resolution_policy"] == "not_averaged_direct_3d_NC_median_is_active"
    assert historical["active_reference_to_historical_ratio"] == pytest.approx(
        1.9849372491228072
    )
    assert sphere_volume_um3_from_diameter(
        HEPATOCYTE_REFERENCE_EQUIVALENT_SPHERE_DIAMETER_UM
    ) == pytest.approx(HEPATOCYTE_REFERENCE_VOLUME_UM3)


def test_validator_rejects_synthetic_shape_or_dynamic_lipid_promotion() -> None:
    payload = deepcopy(load_human_hepatocyte_3d_morphometry())
    payload["integration_gates"]["individual_cell_boundary_mesh_available"] = True
    with pytest.raises(ValueError, match="evidence gates"):
        validate_human_hepatocyte_3d_morphometry(payload)

    payload = deepcopy(load_human_hepatocyte_3d_morphometry())
    payload["normal_control_lipid_droplet_volume_percent"][
        "may_define_dynamic_nutritional_response"
    ] = True
    with pytest.raises(ValueError, match="lipid-droplet"):
        validate_human_hepatocyte_3d_morphometry(payload)


def test_pooled_disease_study_classes_cannot_initialize_healthy_mixture() -> None:
    payload = deepcopy(load_human_hepatocyte_3d_morphometry())
    payload["pooled_all_group_cell_volume_classes_um3"][
        "may_initialize_healthy_population_mixture"
    ] = True
    with pytest.raises(ValueError, match="pooled disease-study"):
        validate_human_hepatocyte_3d_morphometry(payload)
