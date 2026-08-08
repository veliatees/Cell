from __future__ import annotations

from dataclasses import replace
import json
from math import nan

import pytest

from cell_engine.quantitative.p53_dynamics import (
    EXPLORATORY_CANDIDATE_PARAMETERS,
    P53_DYNAMICS_SOURCES,
    P53DynamicsAuthorityError,
    build_p53_dynamics,
    p53_dynamics_snapshot,
    simulate_p53_response,
)


def test_public_contract_is_phh_fail_closed_and_does_not_run_scenarios() -> None:
    snapshot = p53_dynamics_snapshot()
    json.dumps(snapshot)
    assert snapshot["status"] == "cross_context_candidate_phh_execution_blocked"
    assert snapshot["explicit_purpose_required"] is True
    assert snapshot["healthy_phh_numeric_parameter_count"] == 0
    assert snapshot["healthy_phh_time_resolved_protein_trajectory_count"] == 0
    assert snapshot["public_simulated_scenario_count"] == 0
    assert snapshot["quantitative_validation_allowed"] is False
    assert snapshot["predictive_execution_allowed"] is False
    assert snapshot["authoritative_cell_state_coupling_allowed"] is False
    assert "responses" not in snapshot
    assert "model_pulse_period_h" not in snapshot


def test_heldring_phh_context_is_recorded_without_protein_authority() -> None:
    snapshot = p53_dynamics_snapshot()
    contexts = {context["id"]: context for context in snapshot["evidence_contexts"]}
    heldring = contexts["heldring_phh_cisplatin_transcript_panel"]
    assert heldring["donor_count"] == 50
    assert heldring["timepoints_h"] == [8.0, 24.0]
    assert heldring["healthy_phh_time_resolved_protein_dynamics"] is False
    assert heldring["quantitative_parameter_authority"] is False
    assert heldring["predictive_authority"] is False


@pytest.mark.parametrize(
    "purpose",
    (
        "quantitative_validation",
        "predictive_execution",
        "authoritative_cell_state_coupling",
    ),
)
def test_scientific_uses_fail_closed(purpose: str) -> None:
    with pytest.raises(P53DynamicsAuthorityError):
        simulate_p53_response(1.0, purpose=purpose)  # type: ignore[arg-type]


def test_explicit_software_fixture_is_deterministic_and_labelled() -> None:
    first = simulate_p53_response(1.5, purpose="software_fixture", hours=8.0)
    second = simulate_p53_response(1.5, purpose="software_fixture", hours=8.0)
    assert first == second
    assert first.purpose == "software_fixture"
    assert first.parameter_authority == "project_tuned_cross_context_candidate"
    assert first.candidate_fate_label.startswith("candidate_")
    assert first.cumulative_p53 > 0.0


def test_candidate_parameters_are_disclosed_but_not_public_outputs() -> None:
    authority = build_p53_dynamics()
    assert authority.project_tuned_candidate_parameter_count == len(
        EXPLORATORY_CANDIDATE_PARAMETERS.__dataclass_fields__
    )
    snapshot_text = json.dumps(authority.to_dict())
    assert '"ks_p_drive"' not in snapshot_text
    assert '"repair_capacity"' not in snapshot_text


def test_all_registered_sources_resolve() -> None:
    for source_id in p53_dynamics_snapshot()["source_ids"]:
        assert source_id in P53_DYNAMICS_SOURCES


def test_negative_damage_is_rejected() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        simulate_p53_response(-1.0, purpose="software_fixture")


def test_non_finite_candidate_parameter_is_rejected() -> None:
    parameters = replace(EXPLORATORY_CANDIDATE_PARAMETERS, ks_p_drive=nan)
    with pytest.raises(ValueError, match="finite"):
        simulate_p53_response(
            1.0,
            purpose="software_fixture",
            parameters=parameters,
        )
