from __future__ import annotations

import copy

import pytest

from cell_engine.validation.browser_runtime_policy import (
    LOCAL_FIXTURE_PUBLIC_CONTRACT_VERSION,
    LOCAL_FIXTURE_FALSE_GATES,
    QUALITY_TIERS,
    browser_runtime_policy_snapshot,
    validate_browser_runtime_policy,
)


def test_browser_runtime_policy_is_engineering_only_and_fail_closed() -> None:
    policy = browser_runtime_policy_snapshot()

    assert policy["scientific_authority"] is False
    assert policy["biological_parameter_activation"] is False
    fixture = policy["local_fixture"]
    assert fixture["public_contract_version"] == LOCAL_FIXTURE_PUBLIC_CONTRACT_VERSION
    assert fixture["runtime_role"] == "isolated_test_fixture_only"
    assert fixture["execute_when_python_snapshot_missing"] is False
    assert fixture["production_runtime_import_enabled"] is False
    assert fixture["browser_local_division_enabled"] is False
    assert fixture["public_unit_bearing_field_count"] == 0
    assert all(fixture[key] is False for key in LOCAL_FIXTURE_FALSE_GATES)
    assert all(policy["suspension"].values())
    assert tuple(policy["quality"]["tiers"]) == QUALITY_TIERS


def test_runtime_tiers_reduce_render_and_fluid_cadence_monotonically() -> None:
    tiers = browser_runtime_policy_snapshot()["quality"]["tiers"]
    delays = [tiers[tier]["frame_delay_ms"] for tier in QUALITY_TIERS]
    intervals = [
        tiers[tier]["fluid_step_interval_s"] for tier in QUALITY_TIERS
    ]
    grid_refresh_intervals = [
        tiers[tier]["numerical_grid_refresh_interval_s"]
        for tier in QUALITY_TIERS
    ]

    assert delays == sorted(delays)
    assert intervals == sorted(intervals)
    assert intervals[0] >= 1 / 60
    assert grid_refresh_intervals == sorted(grid_refresh_intervals)
    assert grid_refresh_intervals == [0.25, 0.5, 1.0]


def test_browser_runtime_has_no_fixture_scheduler() -> None:
    clock = browser_runtime_policy_snapshot()["clock"]

    assert clock == {"maximum_visible_frame_delta_ms": 80}

    policy = copy.deepcopy(browser_runtime_policy_snapshot())
    policy["clock"]["fixture_steps_per_render_second"] = 5
    with pytest.raises(ValueError, match="fixture scheduler"):
        validate_browser_runtime_policy(policy)


@pytest.mark.parametrize("gate", LOCAL_FIXTURE_FALSE_GATES)
def test_local_fixture_authority_promotions_are_rejected(gate: str) -> None:
    policy = copy.deepcopy(browser_runtime_policy_snapshot())
    policy["local_fixture"][gate] = True

    with pytest.raises(ValueError, match="local fixture authority"):
        validate_browser_runtime_policy(policy)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("public_contract_version", "legacy_unit_bearing_fixture"),
        ("public_unit_bearing_field_count", 1),
    ),
)
def test_local_fixture_public_contract_drift_is_rejected(
    field: str,
    value: object,
) -> None:
    policy = copy.deepcopy(browser_runtime_policy_snapshot())
    policy["local_fixture"][field] = value

    with pytest.raises(ValueError, match="local fixture authority"):
        validate_browser_runtime_policy(policy)
