from dataclasses import replace

import pytest

from cell_engine.quantitative.phh_transporter_inventory import (
    build_phh_transporter_inventory,
    copies_from_pmol_per_mg_and_pg_per_reference_nucleus,
    phh_transporter_inventory_snapshot,
    validate_phh_transporter_inventory,
)


def test_bsep_and_mrp2_have_direct_total_per_nucleus_observations() -> None:
    state = build_phh_transporter_inventory()
    by_id = {item.id: item for item in state.transporters}
    bsep = by_id["ABCB11_BSEP"]
    mrp2 = by_id["ABCC2_MRP2"]

    assert bsep.direct_total_summary.median_copies_per_nucleus == 419_353.48438855633
    assert mrp2.direct_total_summary.median_copies_per_nucleus == 129_918.86133753612
    assert len(bsep.direct_total_abundance) == len(mrp2.direct_total_abundance) == 7
    assert bsep.direct_total_summary.copy_number_denominator == "per_nucleus"
    assert state.bsep_total_per_nucleus_observation_ready
    assert state.mrp2_total_per_nucleus_observation_ready


def test_rounded_bsep_arithmetic_is_only_a_cross_check() -> None:
    state = build_phh_transporter_inventory()
    bsep = next(item for item in state.transporters if item.id == "ABCB11_BSEP")
    cross_check = bsep.rounded_headline_arithmetic_cross_check

    assert copies_from_pmol_per_mg_and_pg_per_reference_nucleus(
        1.4, 600.0
    ) == pytest.approx(505_859.82384)
    assert cross_check is not None
    assert cross_check.derived_copies_per_reference_nucleus == pytest.approx(
        505_859.82384
    )
    assert "cross_check_not_primary" in cross_check.evidence_role


def test_mrp2_independent_membrane_fraction_keeps_its_denominator() -> None:
    state = build_phh_transporter_inventory()
    mrp2 = next(item for item in state.transporters if item.id == "ABCC2_MRP2")
    external = mrp2.independent_membrane_fraction_abundance

    assert external is not None
    assert external.value == 1.54
    assert external.sd == 0.64
    assert external.denominator == "isolated_liver_membrane_fraction_protein"
    assert mrp2.rounded_headline_arithmetic_cross_check is None


def test_transporter_inventory_rejects_unmeasured_surface_population() -> None:
    state = build_phh_transporter_inventory()
    bsep, mrp2 = state.transporters
    altered_bsep = replace(bsep, canalicular_surface_copies_per_hepatocyte=100_000.0)

    with pytest.raises(ValueError, match="unmeasured transporter surface"):
        validate_phh_transporter_inventory(
            replace(state, transporters=(altered_bsep, mrp2))
        )
    with pytest.raises(ValueError, match="finite and positive"):
        copies_from_pmol_per_mg_and_pg_per_reference_nucleus(1.4, 0.0)


def test_transporter_snapshot_exposes_totals_and_keeps_kinetics_empty() -> None:
    snapshot = phh_transporter_inventory_snapshot()

    assert snapshot["summary"]["direct_total_per_nucleus_observation_count"] == 2
    assert snapshot["summary"]["bsep_median_copies_per_nucleus"] == pytest.approx(
        419_353.48438855633
    )
    assert snapshot["summary"]["mrp2_median_copies_per_nucleus"] == pytest.approx(
        129_918.86133753612
    )
    assert snapshot["summary"]["surface_localized_copy_count_record_count"] == 0
    assert snapshot["summary"]["active_copy_count_record_count"] == 0
    assert snapshot["summary"]["flux_parameter_count"] == 0
