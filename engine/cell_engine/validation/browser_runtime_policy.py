from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
POLICY_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "validation"
    / "browser_runtime_policy.v1.json"
)
POLICY_SCHEMA_VERSION = "cell.browser-runtime-policy.v1"
QUALITY_TIERS = ("full", "balanced", "essential")


def _finite_number(
    mapping: Mapping[str, object],
    key: str,
    *,
    positive: bool = False,
) -> float:
    value = mapping.get(key)
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(float(value))
        or (positive and value <= 0)
        or (not positive and value < 0)
    ):
        raise ValueError(f"invalid browser runtime policy value: {key}")
    return float(value)


def browser_runtime_policy_snapshot() -> dict[str, object]:
    payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    validate_browser_runtime_policy(payload)
    return payload


def validate_browser_runtime_policy(payload: object) -> None:
    if not isinstance(payload, dict):
        raise ValueError("browser runtime policy must be an object")
    if payload.get("schema_version") != POLICY_SCHEMA_VERSION:
        raise ValueError("unsupported browser runtime policy schema")
    if (
        payload.get("scientific_authority") is not False
        or payload.get("biological_parameter_activation") is not False
    ):
        raise ValueError("browser runtime policy cannot carry biological authority")

    suspension = payload.get("suspension")
    clock = payload.get("clock")
    quality = payload.get("quality")
    if not all(
        isinstance(section, Mapping)
        for section in (suspension, clock, quality)
    ):
        raise ValueError("browser runtime policy sections are required")
    assert isinstance(suspension, Mapping)
    assert isinstance(clock, Mapping)
    assert isinstance(quality, Mapping)

    required_suspension_guards = (
        "when_document_hidden",
        "when_viewport_not_intersecting",
        "discard_suspended_elapsed_time_on_resume",
        "single_pending_frame_or_timer",
    )
    if any(suspension.get(key) is not True for key in required_suspension_guards):
        raise ValueError("browser runtime suspension guard is disabled")

    _finite_number(clock, "maximum_visible_frame_delta_ms", positive=True)
    _finite_number(
        clock,
        "visual_cell_seconds_per_real_second",
        positive=True,
    )
    _finite_number(clock, "maximum_visual_cell_substep_s", positive=True)
    minimum_substeps = clock.get("minimum_visual_cell_substeps")
    if (
        not isinstance(minimum_substeps, int)
        or isinstance(minimum_substeps, bool)
        or minimum_substeps < 1
    ):
        raise ValueError("browser visual-cell minimum substeps must be positive")

    _finite_number(quality, "measurement_window_ms", positive=True)
    grace_windows = quality.get("initial_grace_windows")
    breach_windows = quality.get("consecutive_breach_windows_before_degrade")
    tiers = quality.get("tiers")
    if (
        not isinstance(grace_windows, int)
        or isinstance(grace_windows, bool)
        or grace_windows < 0
        or not isinstance(breach_windows, int)
        or isinstance(breach_windows, bool)
        or breach_windows < 1
        or not isinstance(tiers, Mapping)
        or tuple(tiers) != QUALITY_TIERS
    ):
        raise ValueError("browser quality governor structure is invalid")

    frame_delays: list[float] = []
    fluid_intervals: list[float] = []
    work_budgets: list[float] = []
    for tier_id in QUALITY_TIERS:
        tier = tiers.get(tier_id)
        if not isinstance(tier, Mapping):
            raise ValueError(f"browser runtime tier is missing: {tier_id}")
        frame_delays.append(_finite_number(tier, "frame_delay_ms"))
        fluid_intervals.append(
            _finite_number(tier, "fluid_step_interval_s", positive=True)
        )
        work_budgets.append(
            _finite_number(tier, "maximum_average_work_ms", positive=True)
        )
        long_ratio = _finite_number(
            tier,
            "maximum_long_frame_ratio",
            positive=True,
        )
        _finite_number(tier, "long_frame_threshold_ms", positive=True)
        if long_ratio > 1:
            raise ValueError("browser long-frame ratio must not exceed one")

    if (
        frame_delays != sorted(frame_delays)
        or fluid_intervals != sorted(fluid_intervals)
        or work_budgets != sorted(work_budgets)
    ):
        raise ValueError("browser quality tiers must reduce work monotonically")
