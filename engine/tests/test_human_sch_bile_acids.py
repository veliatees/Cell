from dataclasses import replace

import pytest

from cell_engine.quantitative.human_sch_bile_acids import (
    build_human_sch_bile_acids,
    calculate_matched_raw_bei_percent,
    human_sch_bile_acids_snapshot,
    validate_human_sch_bile_acids,
)


def test_human_sch_table4_preserves_donors_context_and_control_totals() -> None:
    state = build_human_sch_bile_acids()
    control = next(item for item in state.conditions if item.id == "vehicle_control")
    total = next(item for item in control.records if item.analyte == "Total")

    assert len(state.donors) == 4
    assert state.assay_contract.sampling_day == 7
    assert state.assay_contract.estimated_intracellular_volume_uL_per_well == 6.79
    assert total.cells_plus_bile_mean_uM == 281.0
    assert total.cells_mean_uM == 183.0
    assert total.cells_sd_uM == 55.6
    assert total.medium_mean_uM == 9.61
    assert total.bei_mean_percent is None


def test_published_bei_is_not_reconstructed_from_group_mean_concentrations() -> None:
    state = build_human_sch_bile_acids()
    control = next(item for item in state.conditions if item.id == "vehicle_control")
    tca = next(item for item in control.records if item.analyte == "TCA")
    ratio_of_group_means = calculate_matched_raw_bei_percent(
        tca.cells_plus_bile_mean_uM,
        tca.cells_mean_uM,
    )

    assert ratio_of_group_means == pytest.approx(44.3812233286)
    assert tca.bei_mean_percent == 41.7
    assert ratio_of_group_means != pytest.approx(tca.bei_mean_percent)
    assert not state.measurement_contract.may_reconstruct_published_bei_from_group_mean_concentrations


def test_human_sch_bile_acid_endpoint_fails_closed() -> None:
    state = build_human_sch_bile_acids()

    assert not state.healthy_in_vivo_initialization_ready
    assert not state.kinetic_parameter_fit_ready
    assert not state.true_canalicular_concentration_ready
    assert not state.automatic_state_coupling
    with pytest.raises(ValueError, match="readiness gates"):
        validate_human_sch_bile_acids(
            replace(state, healthy_in_vivo_initialization_ready=True)
        )
    with pytest.raises(ValueError, match="standard-buffer accumulation"):
        calculate_matched_raw_bei_percent(0.0, 0.0)


def test_human_sch_snapshot_counts_only_published_endpoints() -> None:
    snapshot = human_sch_bile_acids_snapshot()

    assert snapshot["summary"]["donor_count"] == 4
    assert snapshot["summary"]["condition_count"] == 2
    assert snapshot["summary"]["table_record_count"] == 10
    assert snapshot["summary"]["published_mean_endpoint_count"] == 38
    assert snapshot["summary"]["raw_donor_record_count"] == 0
    assert snapshot["summary"]["exact_model_prediction_count"] == 0
    assert snapshot["summary"]["pass_fail_count"] == 0
