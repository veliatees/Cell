from __future__ import annotations

import copy

import pytest

from cell_engine.validation.browser_runtime_policy import (
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
    assert fixture["runtime_role"] == "normalized_schematic_fallback_only"
    assert fixture["execute_when_python_snapshot_missing"] is True
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


@pytest.mark.parametrize("gate", LOCAL_FIXTURE_FALSE_GATES)
def test_local_fixture_authority_promotions_are_rejected(gate: str) -> None:
    policy = copy.deepcopy(browser_runtime_policy_snapshot())
    policy["local_fixture"][gate] = True

    with pytest.raises(ValueError, match="local fixture authority"):
        validate_browser_runtime_policy(policy)
