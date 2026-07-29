from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
BUDGET_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "validation"
    / "browser_bundle_budget.v1.json"
)
BUDGET_SCHEMA_VERSION = "cell.browser-bundle-budget.v1"


def browser_bundle_budget_snapshot() -> dict[str, object]:
    payload = json.loads(BUDGET_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("browser bundle budget must be an object")
    if payload.get("schema_version") != BUDGET_SCHEMA_VERSION:
        raise ValueError("unsupported browser bundle budget schema")
    if payload.get("scientific_authority") is not False:
        raise ValueError("browser bundle budget cannot carry scientific authority")

    limits = payload.get("limits")
    verified = payload.get("last_verified_build")
    deferred = payload.get("required_deferred_entries")
    if not isinstance(limits, Mapping) or not isinstance(verified, Mapping):
        raise ValueError("browser bundle budget requires limits and a verified build")
    if (
        not isinstance(deferred, list)
        or not deferred
        or not all(isinstance(entry, str) and entry for entry in deferred)
        or len(set(deferred)) != len(deferred)
    ):
        raise ValueError("browser bundle deferred entries must be unique strings")

    pairs = (
        ("initial_js_raw_bytes", "maximum_initial_js_raw_bytes"),
        ("initial_js_gzip_bytes", "maximum_initial_js_gzip_bytes"),
        (
            "largest_initial_js_chunk_raw_bytes",
            "maximum_initial_js_chunk_raw_bytes",
        ),
        ("initial_css_raw_bytes", "maximum_initial_css_raw_bytes"),
    )
    for observed_key, limit_key in pairs:
        observed = verified.get(observed_key)
        limit = limits.get(limit_key)
        if (
            not isinstance(observed, int)
            or isinstance(observed, bool)
            or observed < 0
            or not isinstance(limit, int)
            or isinstance(limit, bool)
            or limit <= 0
            or observed > limit
        ):
            raise ValueError(
                f"browser bundle measurement escaped its budget: {observed_key}"
            )
    if verified.get("required_deferred_entry_count") != len(deferred):
        raise ValueError("browser bundle deferred-entry count is inconsistent")
    if verified.get("budget_gate_passed") is not True:
        raise ValueError("browser bundle budget gate has not passed")
    return payload
