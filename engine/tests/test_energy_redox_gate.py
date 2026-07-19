from __future__ import annotations

import pytest

from cell_engine.validation.energy_redox_gate import (
    EnergyRedoxCalibrationError,
    assert_energy_redox_predictive_activation,
    assert_energy_redox_reaction_fit_allowed,
    build_energy_redox_calibration_validation_gate,
    energy_redox_calibration_validation_snapshot,
    validate_energy_redox_calibration_validation_gate,
)


def test_all_legacy_numeric_reactions_are_placeholder_and_fit_blocked() -> None:
    gate = build_energy_redox_calibration_validation_gate()
    validate_energy_redox_calibration_validation_gate(gate)

    assert len(gate.reaction_fit_eligibility) == 9
    by_network: dict[str, int] = {}
    for item in gate.reaction_fit_eligibility:
        by_network[item.network_id] = by_network.get(item.network_id, 0) + 1
        assert item.current_authority == "placeholder"
        assert item.parameter_provenance_documented
        assert not item.compartment_context_match
        assert not item.aggregate_observation_identifies_rate
        assert not item.fit_allowed
        assert not item.quantitative_validation_allowed
        assert not item.predictive_execution_allowed
    assert by_network == {
        "legacy_atp_turnover_fixture": 2,
        "legacy_redox_fixture": 4,
        "legacy_oxphos_fixture": 3,
    }


def test_only_apparent_exchange_has_a_same_assay_observation_role() -> None:
    gate = build_energy_redox_calibration_validation_gate()
    same_assay = [
        item
        for item in gate.observation_use_audit
        if item.same_assay_comparison_allowed
    ]

    assert len(gate.observation_use_audit) == 7
    assert [item.observation_id for item in same_assay] == [
        "human_liver_apparent_atp_synthesis"
    ]
    assert all(item.aggregate_reference_allowed for item in gate.observation_use_audit)
    assert not any(
        item.compartment_initialization_allowed
        for item in gate.observation_use_audit
    )
    assert not any(
        item.kinetic_parameter_fit_allowed
        for item in gate.observation_use_audit
    )
    assert not any(
        item.independent_heldout_eligible
        for item in gate.observation_use_audit
    )


def test_every_numerical_activation_requirement_is_explicit_and_unsatisfied() -> None:
    gate = build_energy_redox_calibration_validation_gate()
    assert len(gate.validation_requirements) == 9
    assert not any(item.satisfied for item in gate.validation_requirements)
    assert gate.structural_topology_ready
    assert gate.aggregate_reference_ready
    assert not gate.compartment_state_initialization_ready
    assert not gate.same_assay_descriptive_comparison_ready
    assert not gate.reaction_parameter_calibration_ready
    assert not gate.donor_disjoint_split_ready
    assert not gate.independent_heldout_validation_ready
    assert not gate.uncertainty_qualified_pass_fail_ready
    assert not gate.predictive_parameter_activation_allowed
    assert not gate.automatic_state_coupling
    assert not gate.predictive_ready


def test_fit_and_predictive_guards_fail_closed() -> None:
    with pytest.raises(EnergyRedoxCalibrationError, match="placeholder"):
        assert_energy_redox_reaction_fit_allowed("atp_regeneration")
    with pytest.raises(
        EnergyRedoxCalibrationError,
        match="predictive energy/redox activation blocked",
    ):
        assert_energy_redox_predictive_activation()
    with pytest.raises(KeyError):
        assert_energy_redox_reaction_fit_allowed("not_a_reaction")


def test_snapshot_reports_zero_fits_holdouts_and_activations() -> None:
    summary = energy_redox_calibration_validation_snapshot()["summary"]
    assert summary == {
        "audited_legacy_reaction_count": 9,
        "placeholder_reaction_count": 9,
        "fit_eligible_reaction_count": 0,
        "aggregate_observation_count": 7,
        "same_assay_observation_count": 1,
        "satisfied_validation_requirement_count": 0,
        "independent_heldout_result_count": 0,
        "activated_parameter_count": 0,
    }
