from __future__ import annotations

from cell_engine.quantitative.human_gem_phh_fastcore_scaling import (
    load_committed_human_gem_phh_fastcore_scaling_comparison,
)


def test_committed_fastcore_scaling_comparison_is_fail_closed() -> None:
    report = load_committed_human_gem_phh_fastcore_scaling_comparison()
    fixed = report["fixed_scaling_trial"]
    adaptive = report["adaptive_scaling_trial"]
    boundary = report["scientific_boundary"]

    assert fixed["lp10_strategy"] == "official_fixed_1e4"
    assert (
        adaptive["lp10_strategy"]
        == "official_adaptive_with_fixed_fallback"
    )
    assert fixed["core_reactions_retained"] is True
    assert adaptive["core_reactions_retained"] is True
    assert adaptive["lp10_adaptive_solve_count"] > 0
    assert boundary["numerical_method_sensitivity_quantified"] is True
    assert boundary["context_model_accepted"] is False
    assert boundary["fba_execution_allowed"] is False
    assert boundary["runtime_flux_coupling_allowed"] is False
