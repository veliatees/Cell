from __future__ import annotations

from copy import deepcopy

import pytest

from cell_engine.quantitative.human_liver_open_atlas import (
    HUMAN_LIVER_OPEN_ATLAS_SOURCES,
    human_liver_open_atlas_snapshot,
    load_human_liver_open_atlas,
    ranked_hepatocyte_interaction_hypotheses,
    spatial_protein_observations,
    surface_protein_observation,
    validate_human_liver_open_atlas,
)


def test_open_atlas_retains_checksummed_primary_human_sources() -> None:
    atlas = load_human_liver_open_atlas()
    artifacts = atlas["source_artifacts"]

    assert {item["id"] for item in artifacts} == set(HUMAN_LIVER_OPEN_ATLAS_SOURCES)
    assert all(item["license"] == "CC-BY-4.0" for item in artifacts)
    assert all(len(item["md5"]) == 32 for item in artifacts)
    assert all(len(item["sha256"]) == 64 for item in artifacts)


def test_2d_morphometry_is_loaded_without_becoming_3d_geometry() -> None:
    atlas = load_human_liver_open_atlas()
    morphometry = atlas["hepatocyte_morphometry_2d"]
    all_area = morphometry["segmented_area_um2"]["all"]
    snapshot = human_liver_open_atlas_snapshot("midlobular")
    context = snapshot["morphometry_2d"]["canonical_geometry_context_check"]

    assert morphometry["cell_count"] == 56_055
    assert all_area["median"] == pytest.approx(463.3)
    assert all_area["p05"] == pytest.approx(155.8)
    assert all_area["p95"] == pytest.approx(862.0)
    assert sum(morphometry["detected_nuclei_count"]["counts"].values()) == 56_055
    assert morphometry["detected_nuclei_count"][
        "zero_is_segmentation_nonassignment_not_biological_anucleation"
    ]
    assert context["within_in_situ_segmented_area_p05_p95"]
    assert context["comparison_role"] == "contextual_range_check_only"
    assert not context["may_calibrate_3d_geometry"]
    assert not morphometry["may_replace_3d_cell_geometry"]
    assert morphometry["source_reported_cluster_to_zone"] == {
        "Hep_1": "periportal",
        "Hep_2": "midlobular",
        "Hep_3": "pericentral",
    }


def test_tissue_architecture_remains_separate_from_single_cell_geometry() -> None:
    atlas = load_human_liver_open_atlas()
    tissue = atlas["tissue_architecture"]

    assert tissue["reconstructed_tissue_extent_um"] == [4000.0, 4000.0, 500.0]
    assert tissue["healthy_lobule_polygonal_radius_um"] == {
        "count": 17,
        "median": 595.0,
        "minimum": 428.0,
        "maximum": 717.0,
        "value_status": "source_reported_3d_human_tissue",
    }
    assert len(tissue["central_vein_network_source_rows"]["healthy_control"]) == 6
    assert len(tissue["central_vein_network_source_rows"]["cirrhotic_context_only"]) == 3
    assert not tissue["healthy_initialization_may_use_cirrhotic_rows"]


def test_surfaceome_adds_identity_but_not_density_domain_or_orientation() -> None:
    atlas = load_human_liver_open_atlas()
    surfaceome = atlas["surface_nglycoproteome"]

    assert surfaceome["observed_protein_count"] == 300
    assert surfaceome["reported_cd_molecule_count"] == 66
    assert surfaceome["reported_transmembrane_count"] == 228
    for gene in ("SLC10A1", "EGFR", "INSR", "MET", "IL6ST", "ABCB11", "ABCC2", "ABCB1"):
        observation = surface_protein_observation(gene)
        assert observation is not None
        assert observation["observed_by_cell_surface_capture"]
        assert observation["surface_density_per_um2"] is None
        assert observation["membrane_domain"] is None
        assert observation["orientation"] is None
    assert surface_protein_observation("CDH1") is None
    assert surfaceome["pathway_relevant_gene_observation"]["CDH1"] == "not_detected_in_this_assay"
    assert not surfaceome["absence_is_proof_of_biological_absence"]


def test_spatial_proteome_supplies_measured_gradients_without_flux_scaling() -> None:
    atlas = load_human_liver_open_atlas()
    proteome = atlas["spatial_proteome"]
    portal = spatial_protein_observations("periportal")
    central = spatial_protein_observations("pericentral")

    assert proteome["protein_count"] == 1_736
    assert proteome["article_reported_protein_count_at_70pct_completeness"] == 1_741
    assert proteome["supplement_table_record_count"] == 1_736
    assert proteome["article_minus_supplement_record_count"] == 5
    assert proteome["strong_zonated_count"] == 171
    assert len(portal) == 102
    assert len(central) == 69
    assert spatial_protein_observations("midlobular") == ()
    assert all(item.coefficient > 0 and len(item.binned_expression_percent) == 20 for item in portal)
    assert all(item.coefficient < 0 and len(item.binned_expression_percent) == 20 for item in central)
    assert "SUCLG2" in {item.protein for item in portal}
    assert "ACSL5" in {item.protein for item in central}
    assert not proteome["may_scale_metabolic_flux"]


def test_cellphonedb_scores_remain_nonactivating_hypotheses() -> None:
    atlas = load_human_liver_open_atlas()
    interactions = atlas["hepatocyte_interaction_hypotheses"]
    ranked = ranked_hepatocyte_interaction_hypotheses()

    assert interactions["source_interaction_count"] == 1_679
    assert interactions["retained_hepatocyte_interaction_count"] == 209
    assert interactions["nonzero_hepatocyte_edge_count"] == 1_806
    assert len(ranked) == 209
    assert ranked[0]["maximum_source_score"] >= ranked[-1]["maximum_source_score"]
    assert all(0 < item["maximum_source_score"] <= 100 for item in ranked)
    assert not interactions["score_is_binding_probability"]
    assert not interactions["score_is_kinetic_rate"]
    assert not interactions["may_activate_contact_chain"]


def test_source_reported_clusters_bind_morphometry_and_hypotheses_to_zone() -> None:
    expected = {
        "periportal": ("Hep_1", 456.75, 194, 712),
        "midlobular": ("Hep_2", 454.1, 173, 614),
        "pericentral": ("Hep_3", 494.2, 195, 733),
    }
    for zone, (cluster, median_area, interaction_count, edge_count) in expected.items():
        snapshot = human_liver_open_atlas_snapshot(zone)
        assert snapshot["morphometry_2d"]["selected_zone_cluster"] == cluster
        assert snapshot["morphometry_2d"]["selected_zone_segmented_area_um2"][
            "median"
        ] == pytest.approx(median_area)
        assert snapshot["interaction_hypotheses"]["selected_zone_cluster"] == cluster
        assert snapshot["interaction_hypotheses"][
            "selected_zone_interaction_count"
        ] == interaction_count
        assert snapshot["interaction_hypotheses"][
            "selected_zone_nonzero_edge_count"
        ] == edge_count


def test_fail_closed_gates_reject_promoted_interaction_scores() -> None:
    atlas = deepcopy(load_human_liver_open_atlas())
    atlas["integration_gates"]["may_activate_interaction_from_score"] = True

    with pytest.raises(ValueError, match="fail-closed atlas gates"):
        validate_human_liver_open_atlas(atlas)
