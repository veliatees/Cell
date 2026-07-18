from __future__ import annotations

from dataclasses import replace

import pytest

from cell_engine.quantitative.phh_glucose_validation import (
    load_healthy_phh_glucose_validation,
    validate_healthy_phh_glucose_validation,
)


def test_kemas_conditions_restore_exact_glucose_insulin_and_glucagon_bundle() -> None:
    state = load_healthy_phh_glucose_validation()
    conditions = {item.id: item for item in state.conditions}

    assert conditions["hi_hg"].glucose_mM == 11.0
    assert conditions["li_hg"].glucose_mM == 11.0
    assert conditions["hi_lg"].glucose_mM == 5.5
    assert conditions["li_lg"].insulin_pM == 100.0
    assert conditions["hi_lg"].insulin_pM == 1_700_000.0
    assert conditions["li_lg"].glucagon_nM == 100.0
    assert conditions["hi_lg"].glucagon_nM is None
    assert "unmeasured" in conditions["hi_lg"].glucagon_status
    assert all(item.glucose_mM != 25.0 for item in conditions.values())


def test_healthy_phh_table_one_retains_all_windows_sd_and_overlap_semantics() -> None:
    state = load_healthy_phh_glucose_validation()
    observations = {item.id: item for item in state.glucose_consumption_observations}

    assert len(observations) == 16
    assert observations["kemas_is_hi_hg_0_6h"].mean_fmol_per_cell_h == 10.0
    assert observations["kemas_is_hi_hg_0_6h"].sd_fmol_per_cell_h == 2.4
    assert observations["kemas_is_li_hg_0_6h"].mean_fmol_per_cell_h == 9.9
    assert observations["kemas_is_hi_lg_0_6h"].mean_fmol_per_cell_h == 6.1
    assert observations["kemas_is_li_lg_0_6h"].mean_fmol_per_cell_h == 3.0
    assert sum(item.overlaps_subwindows for item in observations.values()) == 4
    assert all(item.uncertainty_type == "SD" for item in observations.values())
    assert all(item.replicate_n == 6 for item in observations.values())
    assert all(not item.may_parameterize_fresh_phh_or_in_vivo_single_cell for item in observations.values())


def test_hormone_bundle_contrast_is_not_promoted_to_pure_insulin_effect() -> None:
    state = load_healthy_phh_glucose_validation()
    conditions = {item.id: item for item in state.conditions}

    assert conditions["li_lg"].glucagon_nM == 100.0
    assert conditions["hi_lg"].glucagon_nM is None
    assert any("cannot identify a pure insulin causal effect" in item for item in state.corrections_to_supplied_tables)
    assert not state.endocrine_kinetic_fit_ready
    assert not state.automatic_state_coupling


def test_measured_insulin_responses_close_part_of_chain_without_kinetic_fit() -> None:
    state = load_healthy_phh_glucose_validation()
    responses = {item.id: item for item in state.insulin_response_observations}

    pakt = responses["kemas_insulin_pakt_ser473_7min"]
    assert pakt.reported_fold_change == 3.5
    assert pakt.duration_min == 7.0
    assert pakt.reported_n_results == 4
    assert pakt.reported_n_figure_caption == 3
    assert responses["kemas_insulin_pck1_6h"].reported_fold_change == 4.1
    assert responses["kemas_insulin_g6pc_6h"].reported_fold_change == 3.9
    assert all(item.uncertainty_value is None for item in responses.values())
    assert all(not item.may_fit_quantitative_kinetics for item in responses.values())


def test_wilson_and_honka_scale_bridge_is_reproducible_but_contextual() -> None:
    state = load_healthy_phh_glucose_validation()
    hpgl = state.human_scale_bridge.hepatocytes_per_g_liver
    conversion = state.contextual_organ_to_cell_conversion

    assert (hpgl.geometric_mean, hpgl.low, hpgl.high, hpgl.sample_size) == (
        107_000_000.0,
        65_000_000.0,
        185_000_000.0,
        7,
    )
    assert conversion.mean_fmol_per_cell_h == pytest.approx(12.560747663551401)
    assert conversion.low_sensitivity_fmol_per_cell_h == pytest.approx(4.281081081081081)
    assert conversion.high_sensitivity_fmol_per_cell_h == pytest.approx(29.169230769230765)
    assert not conversion.direct_measurement
    assert not conversion.may_drive_cell_state
    assert not state.human_scale_bridge.supports_single_hepatocyte_geometry


def test_model_only_trajectory_and_conflicting_contract_remain_quarantined() -> None:
    state = load_healthy_phh_glucose_validation()
    reviews = {item.file: item for item in state.evidence_review.artifacts}

    assert "quarantined_model_predictions" in reviews["heldout_validation_trajectories.csv"].review_status
    assert "quarantined_conflicts" in reviews["integration_contract.json"].review_status
    assert state.evidence_review.contract_present_file_count == 7
    assert state.evidence_review.contract_required_file_count == 9
    assert state.independent_heldout_human_result_count == 0
    assert not state.predictive_ready

    with pytest.raises(ValueError, match="exceeded the evidence"):
        validate_healthy_phh_glucose_validation(replace(state, automatic_state_coupling=True))

