from dataclasses import replace

import pytest

from cell_engine.quantitative.phh_transporter_inventory import (
    build_phh_transporter_inventory,
    copies_from_pmol_per_mg_and_pg_per_cell,
    phh_transporter_inventory_snapshot,
    validate_phh_transporter_inventory,
)


def test_bsep_same_cohort_denominator_bridge_yields_total_copies_only() -> None:
    state = build_phh_transporter_inventory()
    bsep = next(item for item in state.transporters if item.id == "ABCB11_BSEP")

    assert copies_from_pmol_per_mg_and_pg_per_cell(1.4, 600.0) == pytest.approx(
        505_859.82384
    )
    assert bsep.total_copies_per_hepatocyte == pytest.approx(505_859.82384)
    assert bsep.matched_denominator_bridge is not None
    assert bsep.matched_denominator_bridge.display_precision_total_copies_per_cell == 510_000
    assert bsep.canalicular_surface_copies_per_cell is None
    assert bsep.transport_active_copies_per_cell is None


def test_mrp2_retains_tissue_membrane_denominator_without_per_cell_bridge() -> None:
    state = build_phh_transporter_inventory()
    mrp2 = next(item for item in state.transporters if item.id == "ABCC2_MRP2")

    assert mrp2.abundance.value == 1.54
    assert mrp2.abundance.sd == 0.64
    assert mrp2.exact_unit_equivalent is not None
    assert mrp2.exact_unit_equivalent.value == 1.54
    assert mrp2.matched_denominator_bridge is None
    assert mrp2.total_copies_per_hepatocyte is None
    assert not state.mrp2_total_copy_bridge_ready


def test_transporter_inventory_rejects_unmeasured_surface_population() -> None:
    state = build_phh_transporter_inventory()
    bsep, mrp2 = state.transporters
    altered_bsep = replace(bsep, canalicular_surface_copies_per_cell=100_000.0)

    with pytest.raises(ValueError, match="unmeasured transporter surface"):
        validate_phh_transporter_inventory(
            replace(state, transporters=(altered_bsep, mrp2))
        )
    with pytest.raises(ValueError, match="finite and positive"):
        copies_from_pmol_per_mg_and_pg_per_cell(1.4, 0.0)


def test_transporter_snapshot_exposes_bridge_and_all_remaining_zeros() -> None:
    snapshot = phh_transporter_inventory_snapshot()

    assert snapshot["summary"]["same_cohort_total_copy_bridge_count"] == 1
    assert snapshot["summary"]["bsep_total_copies_per_cell"] == pytest.approx(505_859.82384)
    assert snapshot["summary"]["surface_localized_copy_count_record_count"] == 0
    assert snapshot["summary"]["active_copy_count_record_count"] == 0
    assert snapshot["summary"]["flux_parameter_count"] == 0
