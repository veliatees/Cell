"""Generic event-driven boundary numerics for future dynamic FBA.

For an external pool ``i`` the kernel advances the explicit amount balance

    n_i(t + dt) = n_i(t) + dt * (b_i + N * sum_r(nu_ir * v_r))

where amounts are fmol, time is hours, ``N`` is an integer cell count,
``b_i`` is a non-cellular boundary rate in fmol/h, ``nu_ir`` is the signed
external stoichiometric coefficient and ``v_r`` is a canonicalized exchange
flux in fmol/cell/h.

The operator never invents a unit conversion, rescales a flux or clips a
negative pool.  It advances only to the earliest depletion event and requires
the caller to re-solve the constraint problem before continuing.  This is a
software/mathematical kernel; it supplies no Human-GEM context, measured bound,
biological objective, PHH scale bridge or runtime cell-state authority.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Sequence


VERSION = "dynamic_fba_boundary_numerics_v1"
AMOUNT_UNIT = "fmol"
CELL_EXCHANGE_FLUX_UNIT = "fmol_per_cell_h"
BOUNDARY_RATE_UNIT = "fmol_per_h"
TIME_UNIT = "h"
TIME_ABSOLUTE_TOLERANCE_H = 1e-12
AMOUNT_ABSOLUTE_TOLERANCE_FMOL = 1e-12
RELATIVE_NUMERICAL_TOLERANCE = 1e-12
ANALYTIC_FIXTURE_COUNT = 6
STATUS = "generic_event_driven_amount_balance_kernel_ready"
EQUATION = "n_i_next = n_i + dt * (b_i + N * sum_r(nu_ir * v_r))"
SIGN_CONVENTION = (
    "positive nu_ir * v_r adds amount to the external pool; negative removes it"
)
EVENT_POLICY = (
    "advance to the earliest nonnegative-pool depletion event and require FBA re-solve"
)
ANALYTIC_FIXTURE_IDS = (
    "finite_uptake_balance",
    "earliest_depletion_event",
    "simultaneous_depletion_event",
    "open_boundary_feed_cancellation",
    "secretion_increases_external_amount",
    "permutation_invariant_aggregation",
)
SCIENTIFIC_BLOCKERS = (
    "no healthy-PHH context model or measured exchange-bound trajectory is loaded",
    "no reviewed Human-GEM-to-fmol/cell/h scale operator is loaded",
    "no donor-resolved objective or independent dynamic flux validation is loaded",
    "the generic update kernel cannot mutate authoritative cell state",
)
_SNAPSHOT_FIELDS = frozenset(
    {
        "version",
        "status",
        "equation",
        "canonical_units",
        "sign_convention",
        "event_policy",
        "analytic_fixtures",
        "summary",
        "generic_dynamic_update_kernel_ready",
        "external_amount_balance_verified",
        "positivity_preserving_event_stepper_ready",
        "flux_rescaling_allowed",
        "automatic_unit_conversion",
        "human_gem_loaded",
        "healthy_phh_context_loaded",
        "measured_exchange_bounds_loaded",
        "biological_flux_authority",
        "runtime_state_coupling_allowed",
        "blockers",
    }
)
_SUMMARY_FIELDS = frozenset(
    {
        "registered_dynamic_fba_update_law_count",
        "analytic_fixture_count",
        "analytic_fixture_pass_count",
        "amount_balance_residual_check_count",
        "exchange_pair_ledger_check_count",
        "depletion_event_fixture_count",
        "open_boundary_fixture_count",
        "permutation_invariance_fixture_count",
    }
)


class DynamicFbaNumericsError(ValueError):
    """Raised when a boundary state or amount update is invalid."""


@dataclass(frozen=True)
class ExternalPoolAmount:
    pool_id: str
    amount_fmol: float


@dataclass(frozen=True)
class ExchangeFluxContribution:
    reaction_id: str
    pool_id: str
    external_stoichiometric_coefficient: float
    flux_fmol_per_cell_h: float


@dataclass(frozen=True)
class BoundaryRateContribution:
    process_id: str
    pool_id: str
    rate_fmol_per_h: float


@dataclass(frozen=True)
class DynamicFbaBoundaryState:
    time_h: float
    cell_count: int
    pools: tuple[ExternalPoolAmount, ...]


@dataclass(frozen=True)
class PoolAmountBalance:
    pool_id: str
    amount_before_fmol: float
    cell_exchange_rate_fmol_per_h: float
    boundary_rate_fmol_per_h: float
    external_exchange_delta_fmol: float
    cell_exchange_ledger_delta_fmol: float
    boundary_delta_fmol: float
    amount_after_fmol: float
    amount_balance_residual_fmol: float
    exchange_pair_residual_fmol: float


@dataclass(frozen=True)
class DynamicFbaBoundaryStep:
    requested_duration_h: float
    advanced_duration_h: float
    requested_interval_completed: bool
    depletion_event_pool_ids: tuple[str, ...]
    event_zero_projection_pool_ids: tuple[str, ...]
    requires_fba_resolve: bool
    pool_balances: tuple[PoolAmountBalance, ...]
    state_after: DynamicFbaBoundaryState
    maximum_amount_balance_residual_fmol: float
    maximum_exchange_pair_residual_fmol: float
    positivity_preserved: bool
    flux_rescaling_applied: bool
    automatic_unit_conversion_applied: bool
    biological_flux_authority: bool


def _identifier(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DynamicFbaNumericsError(f"{label} must be a non-empty string")
    return value


def _finite(value: object, *, label: str) -> float:
    if isinstance(value, bool):
        raise DynamicFbaNumericsError(f"{label} must be a finite number")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise DynamicFbaNumericsError(
            f"{label} must be a finite number"
        ) from exc
    if not math.isfinite(numeric):
        raise DynamicFbaNumericsError(f"{label} must be finite")
    return numeric


def _numerical_tolerance(*values: float) -> float:
    return max(
        AMOUNT_ABSOLUTE_TOLERANCE_FMOL,
        RELATIVE_NUMERICAL_TOLERANCE
        * max((1.0, *(abs(value) for value in values))),
    )


def validate_dynamic_fba_boundary_state(state: DynamicFbaBoundaryState) -> None:
    time_h = _finite(state.time_h, label="state.time_h")
    if time_h < 0.0:
        raise DynamicFbaNumericsError("state.time_h cannot be negative")
    if (
        isinstance(state.cell_count, bool)
        or not isinstance(state.cell_count, int)
        or state.cell_count <= 0
    ):
        raise DynamicFbaNumericsError("state.cell_count must be a positive integer")
    if not isinstance(state.pools, tuple) or not state.pools:
        raise DynamicFbaNumericsError("state.pools must be a non-empty tuple")
    pool_ids: list[str] = []
    for index, pool in enumerate(state.pools):
        if not isinstance(pool, ExternalPoolAmount):
            raise DynamicFbaNumericsError(
                f"state.pools[{index}] must be an ExternalPoolAmount"
            )
        pool_id = _identifier(pool.pool_id, label=f"state.pools[{index}].pool_id")
        amount = _finite(
            pool.amount_fmol,
            label=f"state.pools[{index}].amount_fmol",
        )
        if amount < 0.0:
            raise DynamicFbaNumericsError(
                f"external pool {pool_id!r} cannot have a negative amount"
            )
        pool_ids.append(pool_id)
    if len(pool_ids) != len(set(pool_ids)):
        raise DynamicFbaNumericsError("external pool identifiers must be unique")


def _validate_exchange_contributions(
    contributions: Sequence[ExchangeFluxContribution],
    pool_ids: frozenset[str],
) -> None:
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(contributions):
        if not isinstance(item, ExchangeFluxContribution):
            raise DynamicFbaNumericsError(
                f"exchange_fluxes[{index}] must be an ExchangeFluxContribution"
            )
        reaction_id = _identifier(
            item.reaction_id,
            label=f"exchange_fluxes[{index}].reaction_id",
        )
        pool_id = _identifier(
            item.pool_id,
            label=f"exchange_fluxes[{index}].pool_id",
        )
        if pool_id not in pool_ids:
            raise DynamicFbaNumericsError(
                f"exchange reaction {reaction_id!r} references unknown pool {pool_id!r}"
            )
        coefficient = _finite(
            item.external_stoichiometric_coefficient,
            label=(
                f"exchange_fluxes[{index}]."
                "external_stoichiometric_coefficient"
            ),
        )
        _finite(
            item.flux_fmol_per_cell_h,
            label=f"exchange_fluxes[{index}].flux_fmol_per_cell_h",
        )
        if coefficient == 0.0:
            raise DynamicFbaNumericsError(
                f"exchange reaction {reaction_id!r} has a zero external coefficient"
            )
        identity = (reaction_id, pool_id)
        if identity in seen:
            raise DynamicFbaNumericsError(
                "exchange reaction/pool identities must be unique"
            )
        seen.add(identity)


def _validate_boundary_rates(
    contributions: Sequence[BoundaryRateContribution],
    pool_ids: frozenset[str],
) -> None:
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(contributions):
        if not isinstance(item, BoundaryRateContribution):
            raise DynamicFbaNumericsError(
                f"boundary_rates[{index}] must be a BoundaryRateContribution"
            )
        process_id = _identifier(
            item.process_id,
            label=f"boundary_rates[{index}].process_id",
        )
        pool_id = _identifier(
            item.pool_id,
            label=f"boundary_rates[{index}].pool_id",
        )
        if pool_id not in pool_ids:
            raise DynamicFbaNumericsError(
                f"boundary process {process_id!r} references unknown pool {pool_id!r}"
            )
        _finite(
            item.rate_fmol_per_h,
            label=f"boundary_rates[{index}].rate_fmol_per_h",
        )
        identity = (process_id, pool_id)
        if identity in seen:
            raise DynamicFbaNumericsError(
                "boundary process/pool identities must be unique"
            )
        seen.add(identity)


def _stable_sum(values: Iterable[float]) -> float:
    return math.fsum(sorted(float(value) for value in values))


def advance_dynamic_fba_boundary(
    state: DynamicFbaBoundaryState,
    *,
    requested_duration_h: float,
    exchange_fluxes: Sequence[ExchangeFluxContribution],
    boundary_rates: Sequence[BoundaryRateContribution] = (),
) -> DynamicFbaBoundaryStep:
    """Advance one fixed-flux interval, stopping at first pool depletion."""

    validate_dynamic_fba_boundary_state(state)
    duration = _finite(requested_duration_h, label="requested_duration_h")
    if duration <= 0.0:
        raise DynamicFbaNumericsError("requested_duration_h must be positive")
    if not isinstance(exchange_fluxes, (tuple, list)):
        raise DynamicFbaNumericsError("exchange_fluxes must be a sequence")
    if not isinstance(boundary_rates, (tuple, list)):
        raise DynamicFbaNumericsError("boundary_rates must be a sequence")

    pools_by_id = {pool.pool_id: pool for pool in state.pools}
    pool_ids = frozenset(pools_by_id)
    _validate_exchange_contributions(exchange_fluxes, pool_ids)
    _validate_boundary_rates(boundary_rates, pool_ids)

    exchange_terms: dict[str, list[float]] = {
        pool_id: [] for pool_id in pool_ids
    }
    for item in exchange_fluxes:
        exchange_terms[item.pool_id].append(
            state.cell_count
            * float(item.external_stoichiometric_coefficient)
            * float(item.flux_fmol_per_cell_h)
        )
    boundary_terms: dict[str, list[float]] = {
        pool_id: [] for pool_id in pool_ids
    }
    for item in boundary_rates:
        boundary_terms[item.pool_id].append(float(item.rate_fmol_per_h))

    exchange_rate = {
        pool_id: _finite(
            _stable_sum(exchange_terms[pool_id]),
            label=f"{pool_id}.cell_exchange_rate_fmol_per_h",
        )
        for pool_id in pool_ids
    }
    boundary_rate = {
        pool_id: _finite(
            _stable_sum(boundary_terms[pool_id]),
            label=f"{pool_id}.boundary_rate_fmol_per_h",
        )
        for pool_id in pool_ids
    }
    net_rate = {
        pool_id: _finite(
            exchange_rate[pool_id] + boundary_rate[pool_id],
            label=f"{pool_id}.net_rate_fmol_per_h",
        )
        for pool_id in pool_ids
    }

    depletion_times = {
        pool_id: pools_by_id[pool_id].amount_fmol / -net_rate[pool_id]
        for pool_id in pool_ids
        if net_rate[pool_id] < 0.0
    }
    earliest_depletion = min(depletion_times.values(), default=math.inf)
    event_within_interval = earliest_depletion <= (
        duration + TIME_ABSOLUTE_TOLERANCE_H
    )
    advanced_duration = (
        min(duration, max(0.0, earliest_depletion))
        if event_within_interval
        else duration
    )
    event_time_tolerance = max(
        TIME_ABSOLUTE_TOLERANCE_H,
        RELATIVE_NUMERICAL_TOLERANCE
        * max(1.0, abs(advanced_duration)),
    )
    depletion_event_pool_ids = tuple(
        sorted(
            pool_id
            for pool_id, event_time in depletion_times.items()
            if event_within_interval
            and abs(event_time - earliest_depletion) <= event_time_tolerance
        )
    )
    event_pool_set = frozenset(depletion_event_pool_ids)

    balances: list[PoolAmountBalance] = []
    next_pools: list[ExternalPoolAmount] = []
    projected_to_zero: list[str] = []
    for pool_id in sorted(pool_ids):
        before = float(pools_by_id[pool_id].amount_fmol)
        external_delta = exchange_rate[pool_id] * advanced_duration
        boundary_delta = boundary_rate[pool_id] * advanced_duration
        raw_after = before + external_delta + boundary_delta
        tolerance = _numerical_tolerance(
            before,
            external_delta,
            boundary_delta,
            raw_after,
        )
        if raw_after < -tolerance:
            raise DynamicFbaNumericsError(
                f"pool {pool_id!r} became negative before a depletion event"
            )
        after = raw_after
        if pool_id in event_pool_set and abs(raw_after) <= tolerance:
            after = 0.0
            projected_to_zero.append(pool_id)
        elif raw_after < 0.0:
            after = 0.0
            projected_to_zero.append(pool_id)
        cell_ledger_delta = -external_delta
        amount_residual = after - before - external_delta - boundary_delta
        exchange_pair_residual = external_delta + cell_ledger_delta
        if abs(amount_residual) > tolerance:
            raise DynamicFbaNumericsError(
                f"pool {pool_id!r} amount balance exceeded numerical tolerance"
            )
        balances.append(
            PoolAmountBalance(
                pool_id=pool_id,
                amount_before_fmol=before,
                cell_exchange_rate_fmol_per_h=exchange_rate[pool_id],
                boundary_rate_fmol_per_h=boundary_rate[pool_id],
                external_exchange_delta_fmol=external_delta,
                cell_exchange_ledger_delta_fmol=cell_ledger_delta,
                boundary_delta_fmol=boundary_delta,
                amount_after_fmol=after,
                amount_balance_residual_fmol=amount_residual,
                exchange_pair_residual_fmol=exchange_pair_residual,
            )
        )
        next_pools.append(ExternalPoolAmount(pool_id, after))

    maximum_amount_residual = max(
        abs(item.amount_balance_residual_fmol) for item in balances
    )
    maximum_exchange_pair_residual = max(
        abs(item.exchange_pair_residual_fmol) for item in balances
    )
    interval_tolerance = max(
        TIME_ABSOLUTE_TOLERANCE_H,
        RELATIVE_NUMERICAL_TOLERANCE * max(1.0, duration),
    )
    state_after = DynamicFbaBoundaryState(
        time_h=float(state.time_h) + advanced_duration,
        cell_count=state.cell_count,
        pools=tuple(next_pools),
    )
    validate_dynamic_fba_boundary_state(state_after)
    return DynamicFbaBoundaryStep(
        requested_duration_h=duration,
        advanced_duration_h=advanced_duration,
        requested_interval_completed=(
            duration - advanced_duration <= interval_tolerance
        ),
        depletion_event_pool_ids=depletion_event_pool_ids,
        event_zero_projection_pool_ids=tuple(projected_to_zero),
        requires_fba_resolve=bool(depletion_event_pool_ids),
        pool_balances=tuple(balances),
        state_after=state_after,
        maximum_amount_balance_residual_fmol=maximum_amount_residual,
        maximum_exchange_pair_residual_fmol=maximum_exchange_pair_residual,
        positivity_preserved=all(pool.amount_fmol >= 0.0 for pool in next_pools),
        flux_rescaling_applied=False,
        automatic_unit_conversion_applied=False,
        biological_flux_authority=False,
    )


def _pool_amount(step: DynamicFbaBoundaryStep, pool_id: str) -> float:
    return next(
        pool.amount_fmol
        for pool in step.state_after.pools
        if pool.pool_id == pool_id
    )


def _analytic_fixture_results() -> tuple[dict[str, object], ...]:
    finite_uptake = advance_dynamic_fba_boundary(
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
    depletion = advance_dynamic_fba_boundary(
        DynamicFbaBoundaryState(
            time_h=0.0,
            cell_count=10,
            pools=(ExternalPoolAmount("glucose_e", 100.0),),
        ),
        requested_duration_h=10.0,
        exchange_fluxes=(
            ExchangeFluxContribution("EX_glucose", "glucose_e", -1.0, 2.0),
        ),
    )
    simultaneous = advance_dynamic_fba_boundary(
        DynamicFbaBoundaryState(
            time_h=1.0,
            cell_count=10,
            pools=(
                ExternalPoolAmount("ammonia_e", 50.0),
                ExternalPoolAmount("glucose_e", 100.0),
            ),
        ),
        requested_duration_h=8.0,
        exchange_fluxes=(
            ExchangeFluxContribution("EX_glucose", "glucose_e", -1.0, 2.0),
            ExchangeFluxContribution("EX_ammonia", "ammonia_e", -1.0, 1.0),
        ),
    )
    feed_cancellation = advance_dynamic_fba_boundary(
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
    secretion = advance_dynamic_fba_boundary(
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
    permutation_state = DynamicFbaBoundaryState(
        time_h=0.0,
        cell_count=1,
        pools=(
            ExternalPoolAmount("B_e", 100.0),
            ExternalPoolAmount("A_e", 100.0),
        ),
    )
    permutation_terms = (
        ExchangeFluxContribution("R1", "A_e", -1.0, 1.0),
        ExchangeFluxContribution("R2", "A_e", -1.0, 2.0),
        ExchangeFluxContribution("R3", "B_e", 1.0, 3.0),
    )
    ordered = advance_dynamic_fba_boundary(
        permutation_state,
        requested_duration_h=2.0,
        exchange_fluxes=permutation_terms,
    )
    reversed_order = advance_dynamic_fba_boundary(
        permutation_state,
        requested_duration_h=2.0,
        exchange_fluxes=tuple(reversed(permutation_terms)),
    )

    fixture_passes = (
        (
            "finite_uptake_balance",
            abs(_pool_amount(finite_uptake, "glucose_e") - 60.0) <= 1e-12
            and not finite_uptake.requires_fba_resolve,
        ),
        (
            "earliest_depletion_event",
            abs(depletion.advanced_duration_h - 5.0) <= 1e-12
            and depletion.depletion_event_pool_ids == ("glucose_e",)
            and _pool_amount(depletion, "glucose_e") == 0.0
            and depletion.requires_fba_resolve,
        ),
        (
            "simultaneous_depletion_event",
            simultaneous.depletion_event_pool_ids
            == ("ammonia_e", "glucose_e")
            and abs(simultaneous.advanced_duration_h - 5.0) <= 1e-12,
        ),
        (
            "open_boundary_feed_cancellation",
            abs(_pool_amount(feed_cancellation, "oxygen_e") - 25.0) <= 1e-12
            and not feed_cancellation.requires_fba_resolve,
        ),
        (
            "secretion_increases_external_amount",
            abs(_pool_amount(secretion, "urea_e") - 25.0) <= 1e-12,
        ),
        (
            "permutation_invariant_aggregation",
            ordered == reversed_order,
        ),
    )
    if not all(passed for _, passed in fixture_passes):
        raise DynamicFbaNumericsError(
            "dynamic-FBA boundary analytic self-test failed"
        )
    return tuple(
        {"id": fixture_id, "passed": passed}
        for fixture_id, passed in fixture_passes
    )


def dynamic_fba_numerics_snapshot() -> dict[str, object]:
    fixtures = _analytic_fixture_results()
    payload = {
        "version": VERSION,
        "status": STATUS,
        "equation": EQUATION,
        "canonical_units": {
            "external_amount": AMOUNT_UNIT,
            "cell_exchange_flux": CELL_EXCHANGE_FLUX_UNIT,
            "noncell_boundary_rate": BOUNDARY_RATE_UNIT,
            "time": TIME_UNIT,
        },
        "sign_convention": SIGN_CONVENTION,
        "event_policy": EVENT_POLICY,
        "analytic_fixtures": fixtures,
        "summary": {
            "registered_dynamic_fba_update_law_count": 1,
            "analytic_fixture_count": len(fixtures),
            "analytic_fixture_pass_count": sum(
                bool(item["passed"]) for item in fixtures
            ),
            "amount_balance_residual_check_count": 6,
            "exchange_pair_ledger_check_count": 6,
            "depletion_event_fixture_count": 2,
            "open_boundary_fixture_count": 1,
            "permutation_invariance_fixture_count": 1,
        },
        "generic_dynamic_update_kernel_ready": True,
        "external_amount_balance_verified": True,
        "positivity_preserving_event_stepper_ready": True,
        "flux_rescaling_allowed": False,
        "automatic_unit_conversion": False,
        "human_gem_loaded": False,
        "healthy_phh_context_loaded": False,
        "measured_exchange_bounds_loaded": False,
        "biological_flux_authority": False,
        "runtime_state_coupling_allowed": False,
        "blockers": SCIENTIFIC_BLOCKERS,
    }
    validate_dynamic_fba_numerics_snapshot(payload)
    return payload


def validate_dynamic_fba_numerics_snapshot(payload: dict[str, object]) -> None:
    if frozenset(payload) != _SNAPSHOT_FIELDS:
        raise ValueError("dynamic-FBA numerics snapshot fields changed")
    if payload.get("version") != VERSION:
        raise ValueError("unexpected dynamic-FBA numerics version")
    if (
        payload.get("status") != STATUS
        or payload.get("equation") != EQUATION
        or payload.get("sign_convention") != SIGN_CONVENTION
        or payload.get("event_policy") != EVENT_POLICY
    ):
        raise ValueError("dynamic-FBA numerical contract changed")
    units = payload.get("canonical_units")
    summary = payload.get("summary")
    fixtures = payload.get("analytic_fixtures")
    if (
        not isinstance(units, dict)
        or not isinstance(summary, dict)
        or not isinstance(fixtures, (list, tuple))
    ):
        raise ValueError("dynamic-FBA numerics snapshot is malformed")
    if units != {
        "external_amount": AMOUNT_UNIT,
        "cell_exchange_flux": CELL_EXCHANGE_FLUX_UNIT,
        "noncell_boundary_rate": BOUNDARY_RATE_UNIT,
        "time": TIME_UNIT,
    }:
        raise ValueError("dynamic-FBA canonical units changed")
    if (
        frozenset(summary) != _SUMMARY_FIELDS
        or summary.get("amount_balance_residual_check_count") != 6
        or summary.get("exchange_pair_ledger_check_count") != 6
        or summary.get("depletion_event_fixture_count") != 2
        or summary.get("open_boundary_fixture_count") != 1
        or summary.get("permutation_invariance_fixture_count") != 1
        or summary.get("registered_dynamic_fba_update_law_count") != 1
        or summary.get("analytic_fixture_count") != ANALYTIC_FIXTURE_COUNT
        or summary.get("analytic_fixture_pass_count") != ANALYTIC_FIXTURE_COUNT
        or len(fixtures) != ANALYTIC_FIXTURE_COUNT
        or tuple(
            item.get("id") for item in fixtures if isinstance(item, dict)
        )
        != ANALYTIC_FIXTURE_IDS
        or any(
            not isinstance(item, dict)
            or set(item) != {"id", "passed"}
            or item.get("passed") is not True
            for item in fixtures
        )
    ):
        raise ValueError("dynamic-FBA analytic fixture coverage changed")
    if any(
        payload.get(key) is not True
        for key in (
            "generic_dynamic_update_kernel_ready",
            "external_amount_balance_verified",
            "positivity_preserving_event_stepper_ready",
        )
    ):
        raise ValueError("dynamic-FBA generic numerical readiness changed")
    if any(
        payload.get(key) is not False
        for key in (
            "flux_rescaling_allowed",
            "automatic_unit_conversion",
            "human_gem_loaded",
            "healthy_phh_context_loaded",
            "measured_exchange_bounds_loaded",
            "biological_flux_authority",
            "runtime_state_coupling_allowed",
        )
    ):
        raise ValueError("dynamic-FBA numerics escaped its biological firewall")
    blockers = payload.get("blockers")
    if (
        not isinstance(blockers, (list, tuple))
        or tuple(blockers) != SCIENTIFIC_BLOCKERS
    ):
        raise ValueError("dynamic-FBA scientific blockers changed")


__all__ = (
    "AMOUNT_UNIT",
    "BOUNDARY_RATE_UNIT",
    "CELL_EXCHANGE_FLUX_UNIT",
    "TIME_UNIT",
    "BoundaryRateContribution",
    "DynamicFbaBoundaryState",
    "DynamicFbaBoundaryStep",
    "DynamicFbaNumericsError",
    "ExchangeFluxContribution",
    "ExternalPoolAmount",
    "PoolAmountBalance",
    "advance_dynamic_fba_boundary",
    "dynamic_fba_numerics_snapshot",
    "validate_dynamic_fba_boundary_state",
    "validate_dynamic_fba_numerics_snapshot",
)
