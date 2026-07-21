from __future__ import annotations

import pytest

from cell_engine.quantitative.cytosol_transport import (
    ReactionTransportInputs,
    assess_reaction_transport_coupling,
    cytosol_transport_snapshot,
    validate_cytosol_transport_snapshot,
)


def test_cytosol_contract_exposes_real_cross_context_data_without_promoting_it_to_phh() -> None:
    snapshot = cytosol_transport_snapshot()
    validate_cytosol_transport_snapshot(snapshot)
    summary = snapshot["summary"]
    assert summary["cross_context_reference_count"] == 8
    assert summary["healthy_phh_numeric_rheology_parameter_count"] == 0
    assert summary["quantitative_fluid_solver_count"] == 0
    assert summary["reaction_transport_coupling_count"] == 0
    assert all(value is None for value in snapshot["healthy_phh_parameter_slots"].values())
    assert all(
        not observation.may_parameterize_healthy_phh
        for observation in snapshot["cross_context_reference_observations"]
    )


def test_missing_transport_evidence_cannot_modify_a_reaction() -> None:
    decision = assess_reaction_transport_coupling(
        ReactionTransportInputs(
            reaction_id="test",
            apparent_diffusivity_um2_s=None,
            characteristic_length_um=None,
            intrinsic_rate_per_s=None,
            diffusion_limitation_demonstrated=False,
            spatial_concentration_field_validated=False,
            context_match_confirmed=False,
            heldout_validation_confirmed=False,
            validated_direct_correction_law=None,
            source_ids=(),
        )
    )
    assert decision.diffusive_mixing_time_s is None
    assert decision.damkohler_number is None
    assert decision.local_concentration_coupling_allowed is False
    assert decision.direct_rate_correction_allowed is False
    assert decision.direct_rate_multiplier is None


def test_complete_synthetic_evidence_computes_timescale_but_never_infers_multiplier() -> None:
    decision = assess_reaction_transport_coupling(
        ReactionTransportInputs(
            reaction_id="synthetic_gate_test",
            apparent_diffusivity_um2_s=10.0,
            characteristic_length_um=3.0,
            intrinsic_rate_per_s=2.0,
            diffusion_limitation_demonstrated=True,
            spatial_concentration_field_validated=True,
            context_match_confirmed=True,
            heldout_validation_confirmed=True,
            validated_direct_correction_law="source-defined test law",
            source_ids=("synthetic_test_source",),
        )
    )
    assert decision.diffusive_mixing_time_s == pytest.approx(0.15)
    assert decision.damkohler_number == pytest.approx(0.3)
    assert decision.local_concentration_coupling_allowed is True
    assert decision.direct_rate_correction_allowed is True
    assert decision.direct_rate_multiplier is None
