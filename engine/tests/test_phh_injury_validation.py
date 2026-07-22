from __future__ import annotations

from cell_engine.quantitative.phh_injury_validation import (
    build_phh_injury_validation,
    phh_injury_validation_snapshot,
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
