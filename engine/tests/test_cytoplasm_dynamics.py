from __future__ import annotations

from dataclasses import replace
import json

import pytest

from cell_engine.quantitative.cytoplasm_dynamics import (
    CYTOPLASM_DYNAMICS_SOURCES,
    HealthyPhhCytoplasmMotionParameterSlots,
    build_cytoplasm_dynamics,
    cytoplasm_dynamics_snapshot,
    validate_cytoplasm_dynamics,
)


def test_cross_context_observations_are_preserved_without_phh_authority() -> None:
    dynamics = build_cytoplasm_dynamics()
    by_id = {observation.id: observation for observation in dynamics.cross_context_observations}

    assert by_id["human_cell_line_nanoprobe_radius_range"].value == (0.65, 81.0)
    assert by_id["cho_gfp_translational_relative_viscosity"].value == 3.2
    cx32 = by_id["wif_b9_cx32_vesicle_speed"]
    assert cx32.value == 0.246
    assert cx32.uncertainty == 0.032
    assert all(not observation.healthy_phh_context_match for observation in by_id.values())
    assert all(
        not observation.may_parameterize_healthy_phh_bulk_flow
        and not observation.may_parameterize_healthy_phh_organelle_motion
        and not observation.may_parameterize_reaction_transport
        for observation in by_id.values()
    )


def test_no_cross_context_value_is_converted_into_runtime_motion() -> None:
    dynamics = build_cytoplasm_dynamics()

    assert dynamics.quantitative_runtime_enabled is False
    assert dynamics.biological_renderer_motion_enabled is False
    assert dynamics.authoritative_state_coupling_allowed is False
    assert dynamics.cross_context_cargo_speed_applied_to_bulk_flow is False
    assert dynamics.nanoprobe_viscosity_extrapolated_to_micron_organelles is False
    assert dynamics.stokes_einstein_organelle_diffusion_emitted is False
    assert dynamics.renderer_numeric_parameter_count == 0
    assert dynamics.healthy_phh_numeric_motion_parameter_count == 0
    assert dynamics.healthy_phh_organelle_motility_record_count == 0


def test_healthy_phh_parameter_slots_are_all_null() -> None:
    slots = build_cytoplasm_dynamics().healthy_phh_parameter_slots
    assert slots == HealthyPhhCytoplasmMotionParameterSlots()
    assert all(value is None for value in vars(slots).values())


def test_validator_rejects_authority_or_extrapolation() -> None:
    dynamics = build_cytoplasm_dynamics()
    with pytest.raises(ValueError, match="authority firewall"):
        validate_cytoplasm_dynamics(
            replace(dynamics, biological_renderer_motion_enabled=True)
        )
    with pytest.raises(ValueError, match="extrapolated"):
        validate_cytoplasm_dynamics(
            replace(dynamics, cross_context_cargo_speed_applied_to_bulk_flow=True)
        )


def test_snapshot_is_deterministic_json_and_has_complete_provenance() -> None:
    first = cytoplasm_dynamics_snapshot(seed=1)
    second = cytoplasm_dynamics_snapshot(seed=999)
    assert first == second
    restored = json.loads(json.dumps(first))
    assert restored["version"] == "cytoplasm_motion_authority_v2"
    assert restored["healthy_phh_parameter_slots"]["bulk_cytosol_velocity_um_s"] is None
    assert set(restored["source_ids"]) == set(CYTOPLASM_DYNAMICS_SOURCES)
