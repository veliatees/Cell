from __future__ import annotations

from copy import deepcopy

import pytest

from cell_engine.quantitative.phh_proteome_atlas import (
    canonical_gene_reference,
    detected_donor_copy_summary,
    donor_reference_nucleus_inventory,
    load_phh_proteome_atlas,
    phh_proteome_atlas_snapshot,
    protein_groups_for_gene,
    validate_phh_proteome_atlas,
)


def test_atlas_preserves_source_rows_donors_and_per_nucleus_semantics() -> None:
    atlas = load_phh_proteome_atlas()

    assert atlas["cohort"]["donor_count"] == 7
    assert atlas["cohort"]["not_healthy_volunteers"] is True
    assert atlas["measurement_contract"]["copy_number_denominator"] == "per_nucleus"
    assert atlas["measurement_contract"]["source_zero_or_blank_policy"] == (
        "nonquantified_null_no_imputation"
    )
    assert atlas["source_audit"]["source_rows"] == 9_565
    assert atlas["source_audit"]["quantified_target_rows"] == 8_689
    assert atlas["source_audit"]["contaminant_only_rows"] == 179
    assert len(atlas["protein_groups"]) == 8_689


def test_canonical_transporter_observations_are_donor_resolved_not_surface_counts() -> None:
    bsep = canonical_gene_reference("ABCB11")
    mrp2 = canonical_gene_reference("ABCC2")
    bsep_summary = detected_donor_copy_summary(bsep)

    assert bsep_summary["detected_donor_count"] == 7
    assert bsep_summary["mean_copies_per_nucleus"] == pytest.approx(
        502_854.5641050257
    )
    assert bsep_summary["median_copies_per_nucleus"] == 419_353.48438855633
    assert bsep_summary["minimum_copies_per_nucleus"] == 354_513.4563163131
    assert bsep_summary["maximum_copies_per_nucleus"] == 750_964.5402311614
    assert detected_donor_copy_summary(mrp2)["median_copies_per_nucleus"] == (
        129_918.86133753612
    )
    assert load_phh_proteome_atlas()["integration_gates"][
        "surface_localized_copy_number_ready"
    ] is False


def test_gene_query_does_not_silently_merge_distinct_protein_groups() -> None:
    glut2_groups = protein_groups_for_gene("SLC2A2")

    assert len(glut2_groups) == 2
    assert {record["group_id"] for record in glut2_groups} == {"C9J0E8", "P11168"}
    assert canonical_gene_reference("SLC2A2")["group_id"] == "P11168"


def test_donor_inventory_matches_audited_group_count_and_copy_sum() -> None:
    atlas = load_phh_proteome_atlas()
    donor_a = atlas["cohort"]["donors"][0]
    inventory = donor_reference_nucleus_inventory("A")

    assert len(inventory) == donor_a["quantified_target_group_count"] == 6_829
    assert sum(inventory.values()) == pytest.approx(
        donor_a["sum_of_quantified_target_group_copies_per_nucleus"]
    )
    assert all(value > 0.0 for value in inventory.values())


def test_snapshot_is_compact_and_reports_zero_imputation_and_zero_kinetics() -> None:
    snapshot = phh_proteome_atlas_snapshot()

    assert "protein_groups" not in snapshot
    assert snapshot["summary"]["quantified_in_all_seven_donors_count"] == 5_110
    assert snapshot["summary"]["canonical_gene_panel_count"] == 28
    assert snapshot["summary"]["imputed_value_count"] == 0
    assert snapshot["summary"]["turnover_parameter_count"] == 0
    assert snapshot["summary"]["flux_parameter_count"] == 0


def test_atlas_fails_closed_if_a_surface_gate_is_promoted() -> None:
    altered = deepcopy(load_phh_proteome_atlas())
    altered["integration_gates"]["surface_localized_copy_number_ready"] = True

    with pytest.raises(ValueError, match="gates exceeded"):
        validate_phh_proteome_atlas(altered)
