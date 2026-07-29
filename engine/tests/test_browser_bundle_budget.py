from __future__ import annotations

import json
from pathlib import Path

from cell_engine.validation.browser_bundle_budget import (
    BUDGET_PATH,
    browser_bundle_budget_snapshot,
)


ROOT = Path(__file__).resolve().parents[2]


def test_browser_bundle_budget_is_measured_and_scientifically_inert() -> None:
    budget = browser_bundle_budget_snapshot()
    verified = budget["last_verified_build"]
    limits = budget["limits"]
    assert budget["scientific_authority"] is False
    assert verified["initial_js_chunk_count"] == 2
    assert verified["required_deferred_entry_count"] == 6
    assert verified["initial_js_raw_bytes"] <= limits[
        "maximum_initial_js_raw_bytes"
    ]
    assert verified["initial_js_gzip_bytes"] <= limits[
        "maximum_initial_js_gzip_bytes"
    ]
    assert verified["largest_initial_js_chunk_raw_bytes"] <= limits[
        "maximum_initial_js_chunk_raw_bytes"
    ]
    assert verified["budget_gate_passed"] is True


def test_production_build_executes_the_bundle_gate() -> None:
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    assert "node scripts/check_browser_bundle.mjs" in package["scripts"]["build"]
    assert (ROOT / "scripts/check_browser_bundle.mjs").is_file()
    assert BUDGET_PATH.is_file()
