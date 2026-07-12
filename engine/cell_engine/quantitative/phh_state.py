"""Unified quantitative state for the source-backed PHH snapshot surface."""

from __future__ import annotations

from dataclasses import dataclass

from cell_engine.quantitative.geometry import HEPATOCYTE_CELL_VOLUME_L, molecules_from_concentration_mM
from cell_engine.quantitative.phh_profiles import DEFAULT_PHH_PROFILE_ID, PhhNutritionalState, phh_profile


# The current lumped CellDefinition assigns 52% of whole-cell volume to the
# soluble cytosol. This is a model compartment fraction, not a PHH measurement.
EFFECTIVE_CYTOSOL_VOLUME_FRACTION = 0.52


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
    notes: str


@dataclass(frozen=True)
class QuantitativePhhState:
    profile_id: PhhNutritionalState
    profile_label: str
    status: str
    authority: str
    cell_volume_l: float
    effective_cytosol_volume_l: float
    energy_charge: float
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
    cytosol_volume_l = HEPATOCYTE_CELL_VOLUME_L * EFFECTIVE_CYTOSOL_VOLUME_FRACTION
    pools: dict[str, QuantitativePoolState] = {}
    for pool_id, pool in profile.pools.items():
        is_blood = pool_id.endswith("_blood")
        effective_count = None if is_blood else molecules_from_concentration_mM(pool.value_mM, cytosol_volume_l)
        count_basis = (
            "unavailable_no_anatomical_blood_control_volume"
            if is_blood
            else "effective_lumped_cytosol_count_not_direct_single_cell_measurement"
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
            effective_lumped_model_count=effective_count,
            count_basis=count_basis,
            notes=pool.notes,
        )
    state = QuantitativePhhState(
        profile_id=profile.id,
        profile_label=profile.label,
        status="source_backed_baseline_not_dynamic",
        authority="authoritative_research_preview",
        cell_volume_l=HEPATOCYTE_CELL_VOLUME_L,
        effective_cytosol_volume_l=cytosol_volume_l,
        energy_charge=profile.energy_charge(),
        pools=pools,
        limitations=(
            "Tissue-equivalent pools are not compartment-resolved isolated-PHH measurements.",
            "Effective molecule counts use the lumped model cytosol and are not direct copy-number measurements.",
            "This baseline is static; source-backed substrate transport and redox dynamics remain blocked.",
        ),
    )
    validate_quantitative_phh_state(state)
    return state


def validate_quantitative_phh_state(state: QuantitativePhhState) -> None:
    if state.authority != "authoritative_research_preview":
        raise ValueError("quantitative PHH state must declare its authority")
    if not 0.0 <= state.energy_charge <= 1.0:
        raise ValueError("energy charge must be in [0, 1]")
    required = {"ATP", "ADP", "AMP", "NAD_plus", "glycogen"}
    if not required <= set(state.pools):
        raise ValueError("quantitative PHH state is missing required pools")
    for pool in state.pools.values():
        if pool.unit == "relative_pool_0_1":
            raise ValueError("relative schematic pool leaked into quantitative PHH state")
        if pool.value < 0 or not pool.source_ids:
            raise ValueError(f"invalid quantitative pool {pool.id}")
        if pool.effective_lumped_model_count is not None and pool.effective_lumped_model_count < 0:
            raise ValueError(f"negative effective count for {pool.id}")


def quantitative_phh_state_snapshot(
    profile_id: PhhNutritionalState = DEFAULT_PHH_PROFILE_ID,
) -> dict[str, object]:
    state = build_quantitative_phh_state(profile_id)
    return {
        "profile_id": state.profile_id,
        "profile_label": state.profile_label,
        "status": state.status,
        "authority": state.authority,
        "cell_volume_l": state.cell_volume_l,
        "effective_cytosol_volume_l": state.effective_cytosol_volume_l,
        "energy_charge": state.energy_charge,
        "pools": state.pools,
        "limitations": state.limitations,
    }


def schematic_visual_state_snapshot(pool_ids: tuple[str, ...]) -> dict[str, object]:
    return {
        "authority": "schematic_visual_only",
        "source_path": "state.pools",
        "unit": "relative_pool_0_1",
        "pool_ids": pool_ids,
        "may_drive_quantitative_validation": False,
    }
