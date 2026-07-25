from __future__ import annotations

from dataclasses import replace

from cell_engine.quantitative.phh_injury_validation import (
    build_phh_injury_validation,
    evaluate_phh_injury_observations,
    phh_injury_validation_snapshot,
    protocol_query_from_protocol,
    validate_phh_injury_validation,
)


def test_injury_evidence_retains_exact_human_phh_protocols() -> None:
    state = build_phh_injury_validation()
    validate_phh_injury_validation(state)
    assert len(state.protocols) == 4
    assert len(state.observations) == 9
    assert {item.species for item in state.protocols} == {"Homo sapiens"}
    assert all("primary_human_hepatocytes" in item.biological_system for item in state.protocols)


def test_apap_timing_is_a_protocol_observation_not_a_universal_threshold() -> None:
    state = build_phh_injury_validation()
    observations = {item.id: item for item in state.observations}
    onset = observations["apap_necrosis_onset_24h"]
    assert (onset.time_low_h, onset.time_high_h, onset.death_mode) == (24.0, 48.0, "necrosis")
    assert observations["apap_nac_6h_almost_complete_protection"].result == "almost_complete_protection"
    assert observations["apap_nac_15h_partial_protection"].result == "partial_protection"
    assert all(not item.may_generalize and not item.may_drive_cell_state for item in state.observations)


def test_bile_acid_evidence_preserves_serum_versus_local_biliary_context() -> None:
    state = build_phh_injury_validation()
    protocols = {item.id: item for item in state.protocols}
    assert protocols["gcdc_serum_context_phh_24h"].challenge_low == 22.0
    assert protocols["gcdc_biliary_context_phh_24h"].challenge_low == 1000.0
    observations = {item.id: item for item in state.observations}
    assert observations["gcdc_serum_context_no_death_24h"].result == "no_detected_cell_death"
    assert observations["gcdc_biliary_context_necrosis"].death_mode == "necrosis"


def test_injury_observations_do_not_activate_fate_runtime() -> None:
    snapshot = phh_injury_validation_snapshot()
    assert snapshot["summary"]["matching_protocol_observation_count"] == 9
    assert snapshot["summary"]["healthy_baseline_parameter_count"] == 0
    assert snapshot["summary"]["general_fate_law_count"] == 0
    assert snapshot["summary"]["runtime_coupled_observation_count"] == 0
    assert snapshot["integration_gates"]["automatic_runtime_coupling"] is False
    assert snapshot["integration_gates"]["predictive_ready"] is False


def test_exact_protocol_operator_returns_only_matching_observation_windows() -> None:
    state = build_phh_injury_validation()
    protocol = next(
        item for item in state.protocols if item.id == "apap_10mM_fresh_phh_48h"
    )
    query = protocol_query_from_protocol(protocol)
    result = evaluate_phh_injury_observations(
        query,
        at_time_h=24.0,
        endpoint="necrotic_cell_death",
        state=state,
    )
    assert result.status == "matching_protocol_observations_available"
    assert result.protocol_id == protocol.id
    assert [item.id for item in result.observations] == [
        "apap_necrosis_onset_24h"
    ]
    assert result.interpolation_performed is False
    assert result.state_mutation_allowed is False


def test_exact_protocol_operator_rejects_dose_near_miss_without_conversion() -> None:
    state = build_phh_injury_validation()
    protocol = next(
        item for item in state.protocols if item.id == "apap_10mM_fresh_phh_48h"
    )
    query = protocol_query_from_protocol(protocol)
    mismatch = evaluate_phh_injury_observations(
        replace(query, challenge_low=9.0, challenge_high=9.0),
        state=state,
    )
    assert mismatch.status == "context_mismatch"
    assert mismatch.exact_protocol_match is False
    assert "challenge_low" in mismatch.mismatch_dimensions
    assert mismatch.unit_conversion_performed is False
    assert mismatch.observations == ()


def test_unobserved_endpoint_and_time_never_mean_no_effect() -> None:
    state = build_phh_injury_validation()
    protocol = next(
        item for item in state.protocols if item.id == "apap_10mM_fresh_phh_48h"
    )
    query = protocol_query_from_protocol(protocol)
    endpoint_gap = evaluate_phh_injury_observations(
        query,
        at_time_h=6.0,
        endpoint="unmeasured_endpoint",
        state=state,
    )
    time_gap = evaluate_phh_injury_observations(
        query,
        at_time_h=8.0,
        endpoint="necrotic_cell_death",
        state=state,
    )
    assert endpoint_gap.status == "unobserved_endpoint"
    assert time_gap.status == "unobserved_time_window"
    assert endpoint_gap.unknown_is_negative_result is False
    assert time_gap.unknown_is_negative_result is False


def test_snapshot_exposes_operator_authority_and_donor_data_contract() -> None:
    snapshot = phh_injury_validation_snapshot()
    operator = snapshot["observation_operator"]
    authority = snapshot["runtime_authority"]
    contract = snapshot["validation_data_contract"]
    assert operator["exact_protocol_replay_pass_count"] == 4
    assert operator["near_miss_rejection_count"] == 7
    assert operator["state_mutation_enabled"] is False
    assert authority["summary"]["audited_legacy_surface_count"] == 3
    assert authority["summary"]["quantitative_authority_surface_count"] == 0
    assert len(contract["required_columns"]) == 19
    assert len(contract["conditional_columns"]) == 10
    assert contract["current_delivery"]["donor_resolved_raw_record_count"] == 0
