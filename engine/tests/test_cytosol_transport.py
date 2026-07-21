from __future__ import annotations

from copy import deepcopy

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
    assert summary["cross_context_reference_count"] == 10
    assert summary["human_in_vivo_validation_target_count"] == 1
    assert summary["healthy_phh_numeric_rheology_parameter_count"] == 0
    assert summary["dimensionless_projection_solver_count"] == 1
    assert summary["conservative_passive_scalar_kernel_count"] == 1
    assert summary["biological_species_bound_count"] == 0
    assert summary["moving_analytic_obstacle_layer_count"] == 1
    assert summary["membrane_pressure_feedback_count"] == 0
    assert summary["quantitative_fluid_solver_count"] == 0
    assert summary["reaction_transport_coupling_count"] == 0
    assert all(value is None for value in snapshot["healthy_phh_parameter_slots"].values())
    assert all(
        not observation.may_parameterize_healthy_phh
        for observation in snapshot["cross_context_reference_observations"]
    )
    target = snapshot["human_in_vivo_validation_targets"][0]
    assert target["participant_count"] == 3
    assert target["numeric_values_curated"] is False
    assert target["may_parameterize_viscosity_pressure_or_bulk_flow"] is False


@pytest.mark.parametrize(
    ("path", "unsafe_value"),
    (
        (("renderer_dimensionless_projection_grid", "biological_pressure_claim"), True),
        (("renderer_dimensionless_projection_grid", "membrane_pressure_feedback"), True),
        (("conservative_passive_scalar_kernel", "biological_species_bound_count"), 1),
    ),
)
def test_unvalidated_numerical_layer_cannot_escape_into_biology(
    path: tuple[str, str], unsafe_value: object
) -> None:
    snapshot = deepcopy(cytosol_transport_snapshot())
    snapshot["solver_layers"][path[0]][path[1]] = unsafe_value
    with pytest.raises(ValueError):
        validate_cytosol_transport_snapshot(snapshot)


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
