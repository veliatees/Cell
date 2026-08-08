from __future__ import annotations

from dataclasses import replace
import json
from math import nan

import pytest

from cell_engine.quantitative.cell_population import (
    CELL_POPULATION_SOURCES,
    CellPopulationAuthorityError,
    CellPopulationCandidateParameters,
    build_cell_population,
    cell_population_snapshot,
    population_fate_from_damage,
    simulate_cell_population,
)


def _software_fixture_parameters() -> CellPopulationCandidateParameters:
    return CellPopulationCandidateParameters(
        initial_cells=24,
        initial_checkpoint_null_fraction=0.125,
        carrying_capacity=48,
        cycles=8,
        stress_relative_sigma=0.1,
        division_partition_noise=0.05,
        repair_fraction_per_cycle=0.5,
        division_safe_damage=0.2,
        repair_capacity=2.0,
        senescence_arrest_limit=2,
        checkpoint_null_lethal_damage=4.0,
    )


def test_public_snapshot_contains_no_built_in_scenario_or_transformation_claim() -> None:
    snapshot = cell_population_snapshot()
    json.dumps(snapshot)
    assert snapshot["status"] == "software_kernel_only_no_phh_population_execution"
    assert snapshot["bundled_biological_parameter_set_count"] == 0
    assert snapshot["canonical_simulated_scenario_count"] == 0
    assert snapshot["canonical_transformation_claim_count"] == 0
    assert snapshot["healthy_phh_calibrated_population_parameter_count"] == 0
    assert snapshot["quantitative_validation_allowed"] is False
    assert snapshot["predictive_execution_allowed"] is False
    assert "transformation_emerged" not in json.dumps(snapshot)


@pytest.mark.parametrize(
    "purpose",
    (
        "quantitative_validation",
        "predictive_execution",
        "authoritative_cell_state_coupling",
    ),
)
def test_scientific_population_uses_fail_closed(purpose: str) -> None:
    with pytest.raises(CellPopulationAuthorityError):
        simulate_cell_population(
            purpose=purpose,  # type: ignore[arg-type]
            parameters=_software_fixture_parameters(),
            scenario="blocked-purpose-test",
            genotoxic_stress_per_cycle=0.0,
            seed=2,
        )


def test_fixture_fate_ladder_requires_explicit_parameters_and_purpose() -> None:
    parameters = _software_fixture_parameters()
    assert (
        population_fate_from_damage(
            0.1,
            checkpoint_functional=True,
            consecutive_arrests=0,
            parameters=parameters,
            purpose="software_fixture",
        )
        == "candidate_divide"
    )
    assert (
        population_fate_from_damage(
            3.0,
            checkpoint_functional=True,
            consecutive_arrests=0,
            parameters=parameters,
            purpose="software_fixture",
        )
        == "candidate_death"
    )


def test_fixture_kernel_is_deterministic_and_non_authoritative() -> None:
    arguments = {
        "purpose": "software_fixture",
        "parameters": _software_fixture_parameters(),
        "scenario": "bookkeeping-fixture",
        "genotoxic_stress_per_cycle": 0.3,
        "seed": 7,
    }
    first = simulate_cell_population(**arguments)  # type: ignore[arg-type]
    second = simulate_cell_population(**arguments)  # type: ignore[arg-type]
    assert first == second
    assert first.parameter_authority == "caller_supplied_non_authoritative_candidate"
    assert first.is_reaction_transport_authority is False
    assert len(first.timeline) <= _software_fixture_parameters().cycles


def test_invalid_candidate_parameters_are_rejected() -> None:
    parameters = _software_fixture_parameters()
    invalid = CellPopulationCandidateParameters(
        **{
            **parameters.__dict__,
            "initial_checkpoint_null_fraction": 1.5,
        }
    )
    with pytest.raises(ValueError, match="within"):
        simulate_cell_population(
            purpose="software_fixture",
            parameters=invalid,
            scenario="invalid-fixture",
            genotoxic_stress_per_cycle=0.0,
            seed=0,
        )


def test_non_finite_population_parameter_is_rejected() -> None:
    invalid = replace(_software_fixture_parameters(), stress_relative_sigma=nan)
    with pytest.raises(ValueError, match="finite"):
        simulate_cell_population(
            purpose="software_fixture",
            parameters=invalid,
            scenario="non-finite-fixture",
            genotoxic_stress_per_cycle=0.0,
            seed=0,
        )


def test_authority_contract_and_sources_are_complete() -> None:
    authority = build_cell_population()
    assert authority.required_evidence
    assert authority.blockers
    for source_id in authority.source_ids:
        assert source_id in CELL_POPULATION_SOURCES
