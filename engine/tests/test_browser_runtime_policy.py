from __future__ import annotations

from cell_engine.validation.browser_runtime_policy import (
    QUALITY_TIERS,
    browser_runtime_policy_snapshot,
)


def test_browser_runtime_policy_is_engineering_only_and_fail_closed() -> None:
    policy = browser_runtime_policy_snapshot()

    assert policy["scientific_authority"] is False
    assert policy["biological_parameter_activation"] is False
    assert all(policy["suspension"].values())
    assert tuple(policy["quality"]["tiers"]) == QUALITY_TIERS


def test_runtime_tiers_reduce_render_and_fluid_cadence_monotonically() -> None:
    tiers = browser_runtime_policy_snapshot()["quality"]["tiers"]
    delays = [tiers[tier]["frame_delay_ms"] for tier in QUALITY_TIERS]
    intervals = [
        tiers[tier]["fluid_step_interval_s"] for tier in QUALITY_TIERS
    ]

    assert delays == sorted(delays)
    assert intervals == sorted(intervals)
    assert intervals[0] >= 1 / 60
