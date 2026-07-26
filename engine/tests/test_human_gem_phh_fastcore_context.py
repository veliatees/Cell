from __future__ import annotations

from cell_engine.quantitative.human_gem_phh_fastcore_context import (
    load_committed_human_gem_phh_fastcore_context_audit,
)


def test_committed_phh_fastcore_trial_is_diagnostic_and_fail_closed() -> None:
    report = load_committed_human_gem_phh_fastcore_context_audit()
    extraction = report["extraction"]
    closure = report["consistency_closure_diagnostic"]
    boundary = report["scientific_boundary"]

    assert extraction["core_reaction_count"] == 4_555
    assert extraction["core_reactions_retained"] is True
    assert extraction["source_fastcore_selected_reaction_count"] == 7_320
    assert extraction["source_fastcore_output_blocked_reaction_count"] == 408
    assert extraction["extracted_network_flux_consistent"] is True
    assert closure["reaction_count"] == 11_639
    assert closure["bounds_modified_from_generic_human_gem"] is False
    assert closure["accepted_as_context_model"] is False
    assert boundary["source_defined_FASTCORE_trial_executed"] is True
    assert boundary["source_FASTCORE_output_flux_consistent"] is False
    assert boundary["structural_context_candidate_extracted"] is False
    assert boundary["healthy_phh_context_model_claimed"] is False
    assert boundary["fluxes_computed"] is False
    assert boundary["runtime_flux_coupling_allowed"] is False
