from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import math

import pytest

from cell_engine.quantitative.dynamic_fba_numerics import (
    BoundaryRateContribution,
    DynamicFbaBoundaryState,
    DynamicFbaNumericsError,
    ExchangeFluxContribution,
    ExternalPoolAmount,
    advance_dynamic_fba_boundary,
    dynamic_fba_numerics_snapshot,
    validate_dynamic_fba_boundary_state,
    validate_dynamic_fba_numerics_snapshot,
)


def _amount(step, pool_id: str) -> float:
    return next(
        pool.amount_fmol
        for pool in step.state_after.pools
        if pool.pool_id == pool_id
    )


def test_finite_uptake_preserves_exact_external_and_cell_ledgers() -> None:
    step = advance_dynamic_fba_boundary(
        DynamicFbaBoundaryState(
            time_h=0.0,
            cell_count=10,
            pools=(ExternalPoolAmount("glucose_e", 100.0),),
        ),
        requested_duration_h=2.0,
        exchange_fluxes=(
            ExchangeFluxContribution("EX_glucose", "glucose_e", -1.0, 2.0),
        ),
    )

    balance = step.pool_balances[0]
    assert step.advanced_duration_h == pytest.approx(2.0)
    assert step.requested_interval_completed is True
    assert step.requires_fba_resolve is False
    assert _amount(step, "glucose_e") == pytest.approx(60.0)
    assert balance.external_exchange_delta_fmol == pytest.approx(-40.0)
    assert balance.cell_exchange_ledger_delta_fmol == pytest.approx(40.0)
    assert balance.amount_balance_residual_fmol == pytest.approx(0.0)
    assert balance.exchange_pair_residual_fmol == pytest.approx(0.0)


def test_step_stops_at_first_depletion_without_rescaling_flux() -> None:
    step = advance_dynamic_fba_boundary(
        DynamicFbaBoundaryState(
            time_h=3.0,
            cell_count=10,
            pools=(ExternalPoolAmount("glucose_e", 100.0),),
        ),
        requested_duration_h=10.0,
        exchange_fluxes=(
            ExchangeFluxContribution("EX_glucose", "glucose_e", -1.0, 2.0),
        ),
    )

    assert step.advanced_duration_h == pytest.approx(5.0)
    assert step.state_after.time_h == pytest.approx(8.0)
    assert step.requested_interval_completed is False
    assert step.depletion_event_pool_ids == ("glucose_e",)
    assert step.event_zero_projection_pool_ids == ("glucose_e",)
    assert step.requires_fba_resolve is True
    assert _amount(step, "glucose_e") == pytest.approx(0.0)
    assert step.flux_rescaling_applied is False
    assert step.automatic_unit_conversion_applied is False


def test_simultaneous_depletion_events_are_reported_together() -> None:
    step = advance_dynamic_fba_boundary(
        DynamicFbaBoundaryState(
            time_h=0.0,
            cell_count=10,
            pools=(
                ExternalPoolAmount("glucose_e", 100.0),
                ExternalPoolAmount("ammonia_e", 50.0),
            ),
        ),
        requested_duration_h=8.0,
        exchange_fluxes=(
            ExchangeFluxContribution("EX_glucose", "glucose_e", -1.0, 2.0),
            ExchangeFluxContribution("EX_ammonia", "ammonia_e", -1.0, 1.0),
        ),
    )

    assert step.advanced_duration_h == pytest.approx(5.0)
    assert step.depletion_event_pool_ids == ("ammonia_e", "glucose_e")
    assert _amount(step, "ammonia_e") == pytest.approx(0.0)
    assert _amount(step, "glucose_e") == pytest.approx(0.0)


def test_open_boundary_rate_is_separate_from_cell_exchange() -> None:
    step = advance_dynamic_fba_boundary(
        DynamicFbaBoundaryState(
            time_h=0.0,
            cell_count=5,
            pools=(ExternalPoolAmount("oxygen_e", 25.0),),
        ),
        requested_duration_h=3.0,
        exchange_fluxes=(
            ExchangeFluxContribution("EX_oxygen", "oxygen_e", -1.0, 2.0),
        ),
        boundary_rates=(
            BoundaryRateContribution("oxygen_feed", "oxygen_e", 10.0),
        ),
    )

    balance = step.pool_balances[0]
    assert balance.external_exchange_delta_fmol == pytest.approx(-30.0)
    assert balance.boundary_delta_fmol == pytest.approx(30.0)
    assert _amount(step, "oxygen_e") == pytest.approx(25.0)
    assert step.depletion_event_pool_ids == ()


def test_secretion_increases_external_amount() -> None:
    step = advance_dynamic_fba_boundary(
        DynamicFbaBoundaryState(
            time_h=0.0,
            cell_count=2,
            pools=(ExternalPoolAmount("urea_e", 1.0),),
        ),
        requested_duration_h=4.0,
        exchange_fluxes=(
            ExchangeFluxContribution("EX_urea", "urea_e", 1.0, 3.0),
        ),
    )

    assert _amount(step, "urea_e") == pytest.approx(25.0)
    assert step.positivity_preserved is True
    assert step.biological_flux_authority is False


def test_aggregation_is_permutation_invariant_and_canonically_ordered() -> None:
    state = DynamicFbaBoundaryState(
        time_h=0.0,
        cell_count=1,
        pools=(
            ExternalPoolAmount("B_e", 100.0),
            ExternalPoolAmount("A_e", 100.0),
        ),
    )
    terms = (
        ExchangeFluxContribution("R1", "A_e", -1.0, 1.0),
        ExchangeFluxContribution("R2", "A_e", -1.0, 2.0),
        ExchangeFluxContribution("R3", "B_e", 1.0, 3.0),
    )

    first = advance_dynamic_fba_boundary(
        state,
        requested_duration_h=2.0,
        exchange_fluxes=terms,
    )
    second = advance_dynamic_fba_boundary(
        state,
        requested_duration_h=2.0,
        exchange_fluxes=tuple(reversed(terms)),
    )

    assert first == second
    assert tuple(pool.pool_id for pool in first.state_after.pools) == ("A_e", "B_e")


def test_zero_pool_with_active_uptake_requests_immediate_resolve() -> None:
    step = advance_dynamic_fba_boundary(
        DynamicFbaBoundaryState(
            time_h=2.0,
            cell_count=1,
            pools=(ExternalPoolAmount("glucose_e", 0.0),),
        ),
        requested_duration_h=1.0,
        exchange_fluxes=(
            ExchangeFluxContribution("EX_glucose", "glucose_e", -1.0, 1.0),
        ),
    )

    assert step.advanced_duration_h == 0.0
    assert step.requested_interval_completed is False
    assert step.requires_fba_resolve is True
    assert step.state_after.time_h == 2.0


@pytest.mark.parametrize(
    "state",
    (
        DynamicFbaBoundaryState(
            time_h=-1.0,
            cell_count=1,
            pools=(ExternalPoolAmount("A", 1.0),),
        ),
        DynamicFbaBoundaryState(
            time_h=0.0,
            cell_count=0,
            pools=(ExternalPoolAmount("A", 1.0),),
        ),
        DynamicFbaBoundaryState(
            time_h=0.0,
            cell_count=True,
            pools=(ExternalPoolAmount("A", 1.0),),
        ),
        DynamicFbaBoundaryState(
            time_h=0.0,
            cell_count=1,
            pools=(ExternalPoolAmount("A", -1.0),),
        ),
        DynamicFbaBoundaryState(
            time_h=0.0,
            cell_count=1,
            pools=(
                ExternalPoolAmount("A", 1.0),
                ExternalPoolAmount("A", 2.0),
            ),
        ),
    ),
)
def test_invalid_boundary_states_fail_closed(state: DynamicFbaBoundaryState) -> None:
    with pytest.raises(DynamicFbaNumericsError):
        validate_dynamic_fba_boundary_state(state)


@pytest.mark.parametrize("duration", (0.0, -1.0, math.nan, math.inf, True))
def test_invalid_step_durations_fail_closed(duration: object) -> None:
    with pytest.raises(DynamicFbaNumericsError):
        advance_dynamic_fba_boundary(
            DynamicFbaBoundaryState(
                time_h=0.0,
                cell_count=1,
                pools=(ExternalPoolAmount("A", 1.0),),
            ),
            requested_duration_h=duration,
            exchange_fluxes=(),
        )


def test_unknown_pool_duplicate_exchange_and_nonfinite_flux_are_rejected() -> None:
    state = DynamicFbaBoundaryState(
        time_h=0.0,
        cell_count=1,
        pools=(ExternalPoolAmount("A", 10.0),),
    )
    with pytest.raises(DynamicFbaNumericsError, match="unknown pool"):
        advance_dynamic_fba_boundary(
            state,
            requested_duration_h=1.0,
            exchange_fluxes=(
                ExchangeFluxContribution("R", "B", -1.0, 1.0),
            ),
        )
    duplicate = ExchangeFluxContribution("R", "A", -1.0, 1.0)
    with pytest.raises(DynamicFbaNumericsError, match="identities"):
        advance_dynamic_fba_boundary(
            state,
            requested_duration_h=1.0,
            exchange_fluxes=(duplicate, duplicate),
        )
    with pytest.raises(DynamicFbaNumericsError, match="finite"):
        advance_dynamic_fba_boundary(
            state,
            requested_duration_h=1.0,
            exchange_fluxes=(replace(duplicate, flux_fmol_per_cell_h=math.nan),),
        )


def test_snapshot_closes_numerics_but_not_biological_authority() -> None:
    snapshot = dynamic_fba_numerics_snapshot()
    validate_dynamic_fba_numerics_snapshot(snapshot)

    assert snapshot["summary"]["registered_dynamic_fba_update_law_count"] == 1
    assert snapshot["summary"]["analytic_fixture_pass_count"] == 6
    assert snapshot["generic_dynamic_update_kernel_ready"] is True
    assert snapshot["external_amount_balance_verified"] is True
    assert snapshot["positivity_preserving_event_stepper_ready"] is True
    assert snapshot["automatic_unit_conversion"] is False
    assert snapshot["human_gem_loaded"] is False
    assert snapshot["measured_exchange_bounds_loaded"] is False
    assert snapshot["biological_flux_authority"] is False
    assert snapshot["runtime_state_coupling_allowed"] is False


def test_snapshot_rejects_changed_fixture_identity() -> None:
    snapshot = deepcopy(dynamic_fba_numerics_snapshot())
    snapshot["analytic_fixtures"][0]["id"] = "replacement_fixture"

    with pytest.raises(ValueError, match="fixture coverage"):
        validate_dynamic_fba_numerics_snapshot(snapshot)


def test_snapshot_rejects_undeclared_fields() -> None:
    snapshot = deepcopy(dynamic_fba_numerics_snapshot())
    snapshot["runtime_override"] = True

    with pytest.raises(ValueError, match="fields changed"):
        validate_dynamic_fba_numerics_snapshot(snapshot)


def test_snapshot_rejects_changed_or_extended_summary() -> None:
    changed = deepcopy(dynamic_fba_numerics_snapshot())
    changed["summary"]["exchange_pair_ledger_check_count"] = 5
    with pytest.raises(ValueError, match="fixture coverage"):
        validate_dynamic_fba_numerics_snapshot(changed)

    extended = deepcopy(dynamic_fba_numerics_snapshot())
    extended["summary"]["undeclared_check_count"] = 1
    with pytest.raises(ValueError, match="fixture coverage"):
        validate_dynamic_fba_numerics_snapshot(extended)
