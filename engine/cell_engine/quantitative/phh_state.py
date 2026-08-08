"""Static human-liver context retained without single-cell state authority.

The available adenylate, NAD+ and glycogen observations are whole-liver or
whole-tissue-equivalent measurements.  They are useful contextual references,
but they do not identify an isolated healthy-PHH cytosol volume, compartment
concentration or per-cell molecule count.  This module therefore preserves the
reported values while making every single-cell initialization, dynamic and
count-conversion route fail closed.
"""

from __future__ import annotations

from dataclasses import dataclass

from cell_engine.core.runtime_authority import (
    WholeCellRuntimePurpose,
    assert_whole_cell_runtime_authority,
)
from cell_engine.quantitative.geometry import (
    HEPATOCYTE_CELL_VOLUME_L,
    hepatocyte_geometry_reference_snapshot,
    validate_hepatocyte_geometry_reference,
)
from cell_engine.quantitative.phh_profiles import DEFAULT_PHH_PROFILE_ID, PhhNutritionalState, phh_profile


VERSION = "quantitative_phh_context_v2"
AUTHORITY = "source_backed_context_only"


@dataclass(frozen=True)
class QuantitativePoolState:
    id: str
    value: float
    unit: str
    biological_basis: str
    compartment: str
    low: float | None
    high: float | None
    evidence: str
    source_ids: tuple[str, ...]
    effective_lumped_model_count: float | None
    count_basis: str
    single_cell_initialization_allowed: bool
    dynamic_execution_allowed: bool
    notes: str


@dataclass(frozen=True)
class QuantitativePhhState:
    version: str
    profile_id: PhhNutritionalState
    profile_label: str
    status: str
    authority: str
    cell_volume_l: float
    cell_volume_role: str
    effective_cytosol_volume_fraction: float | None
    effective_cytosol_volume_l: float | None
    concentration_to_count_conversion_allowed: bool
    single_cell_initialization_allowed: bool
    dynamic_execution_allowed: bool
    single_cell_measured_pool_count: int
    count_converted_pool_count: int
    dynamic_pool_count: int
    geometry_reference: dict[str, object]
    energy_charge: float
    energy_charge_basis: str
    pools: dict[str, QuantitativePoolState]
    limitations: tuple[str, ...]


_COMPARTMENT_BY_POOL = {
    "ATP": "whole_tissue_equivalent",
    "ADP": "whole_tissue_equivalent",
    "AMP": "whole_tissue_equivalent",
    "NAD_plus": "whole_tissue_equivalent",
    "glycogen": "whole_liver_tissue",
    "glucose_blood": "blood_boundary",
}


def build_quantitative_phh_state(
    profile_id: PhhNutritionalState = DEFAULT_PHH_PROFILE_ID,
) -> QuantitativePhhState:
    profile = phh_profile(profile_id)
    geometry_reference = hepatocyte_geometry_reference_snapshot()
    validate_hepatocyte_geometry_reference(geometry_reference)
    pools: dict[str, QuantitativePoolState] = {}
    for pool_id, pool in profile.pools.items():
        is_blood = pool_id.endswith("_blood")
        count_basis = (
            "not_applicable_blood_boundary_without_anatomical_control_volume"
            if is_blood
            else "blocked_without_matched_single_cell_compartment_volume_and_denominator"
        )
        pools[pool_id] = QuantitativePoolState(
            id=pool_id,
            value=pool.value_mM,
            unit="mM",
            biological_basis=pool.basis,
            compartment=_COMPARTMENT_BY_POOL.get(pool_id, "unresolved"),
            low=pool.low_mM,
            high=pool.high_mM,
            evidence=pool.evidence,
            source_ids=pool.source_ids,
            effective_lumped_model_count=None,
            count_basis=count_basis,
            single_cell_initialization_allowed=False,
            dynamic_execution_allowed=False,
            notes=pool.notes,
        )
    state = QuantitativePhhState(
        version=VERSION,
        profile_id=profile.id,
        profile_label=profile.label,
        status="source_backed_liver_context_single_cell_state_blocked",
        authority=AUTHORITY,
        cell_volume_l=HEPATOCYTE_CELL_VOLUME_L,
        cell_volume_role="independent_geometry_reference_not_pool_denominator",
        effective_cytosol_volume_fraction=None,
        effective_cytosol_volume_l=None,
        concentration_to_count_conversion_allowed=False,
        single_cell_initialization_allowed=False,
        dynamic_execution_allowed=False,
        single_cell_measured_pool_count=0,
        count_converted_pool_count=0,
        dynamic_pool_count=0,
        geometry_reference=geometry_reference,
        energy_charge=profile.energy_charge(),
        energy_charge_basis="derived_from_whole_liver_tissue_equivalent_adenylates",
        pools=pools,
        limitations=(
            "Tissue-equivalent pools are not compartment-resolved isolated-PHH measurements.",
            "The aggregate cell-volume reference is not a valid denominator for whole-liver pool observations.",
            "The legacy 0.52 cytosol fraction is not used and no per-cell molecule count is emitted.",
            "This context is static; single-cell initialization, substrate transport and redox dynamics remain blocked.",
        ),
    )
    validate_quantitative_phh_state(state)
    return state


def validate_quantitative_phh_state(state: QuantitativePhhState) -> None:
    if state.version != VERSION or state.authority != AUTHORITY:
        raise ValueError("human-liver context must declare its restricted authority")
    if state.status != "source_backed_liver_context_single_cell_state_blocked":
        raise ValueError("human-liver context status changed")
    if not 0.0 <= state.energy_charge <= 1.0:
        raise ValueError("energy charge must be in [0, 1]")
    validate_hepatocyte_geometry_reference(state.geometry_reference)
    canonical = state.geometry_reference["canonical_reference"]
    if not isinstance(canonical, dict) or state.cell_volume_l != float(canonical["cell_volume_um3"]) * 1.0e-15:
        raise ValueError("quantitative PHH volume diverged from its geometry reference")
    required = {"ATP", "ADP", "AMP", "NAD_plus", "glycogen"}
    if not required <= set(state.pools):
        raise ValueError("human-liver context is missing required pools")
    if (
        state.cell_volume_role
        != "independent_geometry_reference_not_pool_denominator"
        or state.effective_cytosol_volume_fraction is not None
        or state.effective_cytosol_volume_l is not None
        or state.concentration_to_count_conversion_allowed
        or state.single_cell_initialization_allowed
        or state.dynamic_execution_allowed
        or state.single_cell_measured_pool_count != 0
        or state.count_converted_pool_count != 0
        or state.dynamic_pool_count != 0
    ):
        raise ValueError("aggregate liver context escaped into single-cell state")
    for pool in state.pools.values():
        if pool.unit == "relative_pool_0_1":
            raise ValueError("relative schematic pool leaked into human-liver context")
        if pool.value < 0 or not pool.source_ids:
            raise ValueError(f"invalid contextual pool {pool.id}")
        if (
            pool.effective_lumped_model_count is not None
            or pool.single_cell_initialization_allowed
            or pool.dynamic_execution_allowed
        ):
            raise ValueError(f"contextual pool {pool.id} gained single-cell authority")


def quantitative_phh_state_snapshot(
    profile_id: PhhNutritionalState = DEFAULT_PHH_PROFILE_ID,
) -> dict[str, object]:
    state = build_quantitative_phh_state(profile_id)
    return {
        "version": state.version,
        "profile_id": state.profile_id,
        "profile_label": state.profile_label,
        "status": state.status,
        "authority": state.authority,
        "cell_volume_l": state.cell_volume_l,
        "cell_volume_role": state.cell_volume_role,
        "effective_cytosol_volume_fraction": state.effective_cytosol_volume_fraction,
        "effective_cytosol_volume_l": state.effective_cytosol_volume_l,
        "concentration_to_count_conversion_allowed": state.concentration_to_count_conversion_allowed,
        "single_cell_initialization_allowed": state.single_cell_initialization_allowed,
        "dynamic_execution_allowed": state.dynamic_execution_allowed,
        "single_cell_measured_pool_count": state.single_cell_measured_pool_count,
        "count_converted_pool_count": state.count_converted_pool_count,
        "dynamic_pool_count": state.dynamic_pool_count,
        "geometry_reference": state.geometry_reference,
        "energy_charge": state.energy_charge,
        "energy_charge_basis": state.energy_charge_basis,
        "pools": state.pools,
        "limitations": state.limitations,
    }


def schematic_visual_state_snapshot(
    pool_ids: tuple[str, ...],
    *,
    runtime_purpose: WholeCellRuntimePurpose,
    executed_step_count: int,
    elapsed_s: float,
) -> dict[str, object]:
    assert_whole_cell_runtime_authority(runtime_purpose)
    if executed_step_count < 0 or elapsed_s < 0:
        raise ValueError("schematic execution counts and time must be non-negative")
    return {
        "authority": "schematic_visual_only",
        "source_path": "state.pools",
        "unit": "relative_pool_0_1",
        "pool_ids": pool_ids,
        "runtime_purpose": runtime_purpose,
        "dynamics_executed": executed_step_count > 0,
        "executed_step_count": executed_step_count,
        "elapsed_s": elapsed_s,
        "biological_parameter_authority": False,
        "may_drive_quantitative_validation": False,
        "may_drive_predictive_execution": False,
        "may_authoritatively_couple_cell_state": False,
    }
