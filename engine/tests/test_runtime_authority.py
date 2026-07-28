from __future__ import annotations

import pytest

from cell_engine import (
    EngineRng,
    build_hepatocyte_definition,
    initial_hepatocyte_state,
    run_cell,
    step_cell,
)
from cell_engine.core.runtime_authority import (
    WholeCellRuntimeAuthorityError,
    assert_whole_cell_runtime_authority,
    build_whole_cell_runtime_authority,
    whole_cell_runtime_authority_snapshot,
)


def test_whole_cell_runtime_is_schematic_and_exploratory_only() -> None:
    authority = build_whole_cell_runtime_authority()
    assert authority.explicit_purpose_required is True
    assert authority.schematic_visualization_allowed is True
    assert authority.exploratory_execution_allowed is True
    assert authority.quantitative_validation_allowed is False
    assert authority.predictive_execution_allowed is False
    assert authority.authoritative_cell_state_coupling_allowed is False
    assert all(not surface.phh_context_match for surface in authority.surfaces)
    assert all(surface.blockers for surface in authority.surfaces)


@pytest.mark.parametrize(
    "purpose",
    (
        "quantitative_validation",
        "predictive_execution",
        "authoritative_cell_state_coupling",
    ),
)
def test_authority_guard_blocks_scientific_purposes(purpose: str) -> None:
    with pytest.raises(WholeCellRuntimeAuthorityError, match=f"{purpose} is blocked"):
        assert_whole_cell_runtime_authority(purpose)  # type: ignore[arg-type]


def test_public_runtime_requires_explicit_purpose() -> None:
    definition = build_hepatocyte_definition()
    state = initial_hepatocyte_state(definition)
    with pytest.raises(TypeError, match="purpose"):
        step_cell(definition, state, 1.0)  # type: ignore[call-arg]
    with pytest.raises(TypeError, match="purpose"):
        run_cell(definition, state, dt_s=1.0, steps=1)  # type: ignore[call-arg]


def test_public_runtime_blocks_authoritative_state_coupling() -> None:
    definition = build_hepatocyte_definition()
    state = initial_hepatocyte_state(definition)
    with pytest.raises(
        WholeCellRuntimeAuthorityError,
        match="authoritative_cell_state_coupling is blocked",
    ):
        step_cell(
            definition,
            state,
            1.0,
            purpose="authoritative_cell_state_coupling",
            rng=EngineRng(1),
        )


def test_declared_schematic_execution_remains_available() -> None:
    definition = build_hepatocyte_definition()
    state = initial_hepatocyte_state(definition)
    advanced = step_cell(
        definition,
        state,
        1.0,
        purpose="schematic_visualization",
        rng=EngineRng(1),
    )
    assert advanced.elapsed_s == 1.0


def test_authority_snapshot_reports_zero_scientific_surfaces() -> None:
    summary = whole_cell_runtime_authority_snapshot()["summary"]
    assert summary["audited_legacy_surface_count"] == 4
    assert summary["phh_context_matched_surface_count"] == 0
    assert summary["quantitative_authority_surface_count"] == 0
    assert summary["predictive_authority_surface_count"] == 0
    assert summary["authoritative_state_coupling_surface_count"] == 0
