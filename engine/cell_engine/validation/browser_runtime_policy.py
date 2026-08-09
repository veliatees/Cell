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
LOCAL_FIXTURE_PUBLIC_CONTRACT_VERSION = "dimensionless_browser_cell_fixture_v2"
QUALITY_TIERS = ("full", "balanced", "essential")
LOCAL_FIXTURE_FALSE_GATES = (
    "execute_when_python_snapshot_loading",
    "execute_when_python_snapshot_loaded",
    "canonical_geometry_coupling",
    "canonical_engine_state_coupling",
    "engine_division_state_coupling",
    "quantitative_output_authority",
    "predictive_authority",
    "biological_time_authority",
    "biological_rate_authority",
    "display_biological_time_units",
    "display_biological_rate_units",
    "unit_bearing_public_fields_allowed",
    "projected_survival_output_enabled",
    "absolute_distance_transport_conversion_enabled",
    "biological_fate_output_enabled",
)


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

    local_fixture = payload.get("local_fixture")
    suspension = payload.get("suspension")
    clock = payload.get("clock")
    quality = payload.get("quality")
    if not all(
        isinstance(section, Mapping)
        for section in (local_fixture, suspension, clock, quality)
    ):
        raise ValueError("browser runtime policy sections are required")
    assert isinstance(local_fixture, Mapping)
    assert isinstance(suspension, Mapping)
    assert isinstance(clock, Mapping)
    assert isinstance(quality, Mapping)

    if (
        local_fixture.get("public_contract_version")
        != LOCAL_FIXTURE_PUBLIC_CONTRACT_VERSION
        or local_fixture.get("runtime_role")
        != "normalized_schematic_fallback_only"
        or local_fixture.get("execute_when_python_snapshot_missing") is not True
        or type(local_fixture.get("public_unit_bearing_field_count")) is not int
        or local_fixture.get("public_unit_bearing_field_count") != 0
        or any(local_fixture.get(key) is not False for key in LOCAL_FIXTURE_FALSE_GATES)
    ):
        raise ValueError("browser-local fixture authority boundary is invalid")

    required_suspension_guards = (
        "when_document_hidden",
        "when_viewport_not_intersecting",
        "discard_suspended_elapsed_time_on_resume",
        "single_pending_frame_or_timer",
    )
    if any(suspension.get(key) is not True for key in required_suspension_guards):
        raise ValueError("browser runtime suspension guard is disabled")

    legacy_fixture_clock_keys = (
        "visual_cell_seconds_per_real_second",
        "maximum_visual_cell_substep_s",
        "minimum_visual_cell_substeps",
    )
    if any(key in clock for key in legacy_fixture_clock_keys):
        raise ValueError("unit-bearing browser fixture clock key is forbidden")

    _finite_number(clock, "maximum_visible_frame_delta_ms", positive=True)
    _finite_number(
        clock,
        "fixture_steps_per_render_second",
        positive=True,
    )
    _finite_number(clock, "maximum_fixture_substep", positive=True)
    minimum_substeps = clock.get("minimum_fixture_substeps")
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
    grid_refresh_intervals: list[float] = []
    work_budgets: list[float] = []
    for tier_id in QUALITY_TIERS:
        tier = tiers.get(tier_id)
        if not isinstance(tier, Mapping):
            raise ValueError(f"browser runtime tier is missing: {tier_id}")
        frame_delays.append(_finite_number(tier, "frame_delay_ms"))
        fluid_intervals.append(
            _finite_number(tier, "fluid_step_interval_s", positive=True)
        )
        grid_refresh_intervals.append(
            _finite_number(
                tier,
                "numerical_grid_refresh_interval_s",
                positive=True,
            )
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
        or grid_refresh_intervals != sorted(grid_refresh_intervals)
        or work_budgets != sorted(work_budgets)
    ):
        raise ValueError("browser quality tiers must reduce work monotonically")
