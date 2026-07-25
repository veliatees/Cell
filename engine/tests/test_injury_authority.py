from __future__ import annotations

import pytest

from cell_engine.stochastic.apoptosis import StressSignals, run_death
from cell_engine.stochastic.tissue_injury import expose_tissue_to_toxin
from cell_engine.core.injury_authority import (
    InjuryRuntimeAuthorityError,
    assert_injury_runtime_authority,
    build_injury_runtime_authority,
    injury_runtime_authority_snapshot,
)


def test_legacy_injury_surfaces_are_exploratory_only() -> None:
    authority = build_injury_runtime_authority()
    assert authority.explicit_purpose_required is True
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
def test_authority_guard_blocks_non_exploratory_purposes(purpose: str) -> None:
    with pytest.raises(InjuryRuntimeAuthorityError, match=f"{purpose} is blocked"):
        assert_injury_runtime_authority(purpose)  # type: ignore[arg-type]


def test_public_legacy_runtimes_enforce_the_authority_guard() -> None:
    with pytest.raises(InjuryRuntimeAuthorityError, match="quantitative_validation"):
        run_death(
            StressSignals(),
            1.0,
            purpose="quantitative_validation",
        )
    with pytest.raises(
        InjuryRuntimeAuthorityError,
        match="authoritative_cell_state_coupling",
    ):
        expose_tissue_to_toxin(
            1,
            1.0,
            1,
            purpose="authoritative_cell_state_coupling",
        )


def test_public_legacy_runtimes_require_an_explicit_purpose() -> None:
    with pytest.raises(TypeError, match="purpose"):
        run_death(StressSignals(), 1.0)  # type: ignore[call-arg]
    with pytest.raises(TypeError, match="purpose"):
        expose_tissue_to_toxin(1, 1.0, 1)  # type: ignore[call-arg]


def test_authority_snapshot_reports_zero_quantitative_surfaces() -> None:
    summary = injury_runtime_authority_snapshot()["summary"]
    assert summary["audited_legacy_surface_count"] == 3
    assert summary["phh_context_matched_surface_count"] == 0
    assert summary["quantitative_authority_surface_count"] == 0
    assert summary["predictive_authority_surface_count"] == 0
    assert summary["authoritative_state_coupling_surface_count"] == 0
