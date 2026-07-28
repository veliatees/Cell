"""Fail-closed authority boundary for the schematic whole-cell runtime.

The legacy whole-cell loop is useful for renderer integration, deterministic
software tests and exploratory control-flow experiments. Its relative pools,
rates, hazards and thresholds are not a calibrated primary-human-hepatocyte
model. Public execution therefore requires an explicit purpose, and every use
beyond schematic or exploratory execution is rejected.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from cell_engine.core.serialization import to_plain


VERSION = "whole_cell_runtime_authority_v1"

WholeCellRuntimePurpose = Literal[
    "schematic_visualization",
    "exploratory_execution",
    "quantitative_validation",
    "predictive_execution",
    "authoritative_cell_state_coupling",
]


@dataclass(frozen=True)
class LegacyWholeCellSurface:
    id: str
    code_surfaces: tuple[str, ...]
    current_role: str
    numerical_parameter_authority: str
    phh_context_match: bool
    quantitative_validation_allowed: bool
    predictive_execution_allowed: bool
    authoritative_cell_state_coupling_allowed: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class WholeCellRuntimeAuthority:
    version: str
    status: str
    surfaces: tuple[LegacyWholeCellSurface, ...]
    explicit_purpose_required: bool
    schematic_visualization_allowed: bool
    exploratory_execution_allowed: bool
    quantitative_validation_allowed: bool
    predictive_execution_allowed: bool
    authoritative_cell_state_coupling_allowed: bool
    policy: str

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


class WholeCellRuntimeAuthorityError(RuntimeError):
    """Raised when the schematic runtime is requested for an unsupported use."""


_LEGACY_SURFACES = (
    LegacyWholeCellSurface(
        id="normalized_pool_initial_state",
        code_surfaces=(
            "engine/cell_engine/processes/hepatocyte.py:build_hepatocyte_definition",
            "engine/cell_engine/processes/hepatocyte.py:initial_hepatocyte_state",
        ),
        current_role="schematic_visual_initial_state",
        numerical_parameter_authority="relative_pool_placeholders",
        phh_context_match=False,
        quantitative_validation_allowed=False,
        predictive_execution_allowed=False,
        authoritative_cell_state_coupling_allowed=False,
        blockers=(
            "The relative 0-1 pool initial values are project placeholders rather than matched PHH concentrations.",
            "Several physical compartments are collapsed into one runtime pool.",
            "No donor-resolved initialization and uncertainty model validates the complete state vector.",
        ),
    ),
    LegacyWholeCellSurface(
        id="heuristic_metabolism_and_stress",
        code_surfaces=(
            "engine/cell_engine/processes/metabolism.py:step_hepatocyte_metabolism",
            "engine/cell_engine/core/engine.py:_derive_stress",
            "engine/cell_engine/core/engine.py:_status_from_stress",
        ),
        current_role="schematic_dynamic_fixture",
        numerical_parameter_authority="normalized_illustrative_rates_and_thresholds",
        phh_context_match=False,
        quantitative_validation_allowed=False,
        predictive_execution_allowed=False,
        authoritative_cell_state_coupling_allowed=False,
        blockers=(
            "Normalized pathway rates and stress weights are not calibrated to one matched healthy-PHH protocol.",
            "Aggregate liver observations do not identify compartment-specific reaction rates or fate thresholds.",
            "No donor-disjoint held-out trajectory validates the integrated state transition.",
        ),
    ),
    LegacyWholeCellSurface(
        id="organelle_cargo_and_signaling_loops",
        code_surfaces=(
            "engine/cell_engine/organelles",
            "engine/cell_engine/cargo",
            "engine/cell_engine/processes/signaling.py",
            "engine/cell_engine/processes/cellular_response.py",
            "engine/cell_engine/processes/cellular_memory.py",
        ),
        current_role="schematic_event_and_routing_fixture",
        numerical_parameter_authority="mixed_structural_and_placeholder_dynamics",
        phh_context_match=False,
        quantitative_validation_allowed=False,
        predictive_execution_allowed=False,
        authoritative_cell_state_coupling_allowed=False,
        blockers=(
            "Organelle cycles, routing probabilities and response thresholds are not jointly calibrated in PHH.",
            "Receptor, active-protein, damage and memory trajectory gates currently authorize zero quantitative laws.",
            "A deterministic software response does not establish biological prediction.",
        ),
    ),
    LegacyWholeCellSurface(
        id="browser_local_living_cell",
        code_surfaces=("src/physics/cell.ts:LivingCell",),
        current_role="schematic_visual_animation",
        numerical_parameter_authority="normalized_illustrative_browser_dynamics",
        phh_context_match=False,
        quantitative_validation_allowed=False,
        predictive_execution_allowed=False,
        authoritative_cell_state_coupling_allowed=False,
        blockers=(
            "Browser-local rates and hazards are renderer assumptions.",
            "The local animation is not a Python quantitative-state trajectory.",
            "Visual activity, color and motion cannot serve as experimental validation.",
        ),
    ),
)


def build_whole_cell_runtime_authority() -> WholeCellRuntimeAuthority:
    authority = WholeCellRuntimeAuthority(
        version=VERSION,
        status="schematic_and_exploratory_execution_only",
        surfaces=_LEGACY_SURFACES,
        explicit_purpose_required=True,
        schematic_visualization_allowed=True,
        exploratory_execution_allowed=True,
        quantitative_validation_allowed=False,
        predictive_execution_allowed=False,
        authoritative_cell_state_coupling_allowed=False,
        policy=(
            "The legacy whole-cell loop may animate the renderer and exercise software behavior "
            "only after its caller declares that purpose. It may not validate, predict or "
            "authoritatively mutate a PHH state until the complete parameter, context, "
            "measurement-operator and donor-disjoint validation gates pass."
        ),
    )
    validate_whole_cell_runtime_authority(authority)
    return authority


def validate_whole_cell_runtime_authority(
    authority: WholeCellRuntimeAuthority,
) -> None:
    expected_ids = {
        "normalized_pool_initial_state",
        "heuristic_metabolism_and_stress",
        "organelle_cargo_and_signaling_loops",
        "browser_local_living_cell",
    }
    if (
        authority.version != VERSION
        or authority.status != "schematic_and_exploratory_execution_only"
    ):
        raise ValueError("whole-cell runtime authority identity changed")
    if {surface.id for surface in authority.surfaces} != expected_ids:
        raise ValueError("whole-cell runtime authority surface panel changed")
    if (
        not authority.explicit_purpose_required
        or not authority.schematic_visualization_allowed
        or not authority.exploratory_execution_allowed
    ):
        raise ValueError("whole-cell exploratory purpose gate changed")
    if (
        authority.quantitative_validation_allowed
        or authority.predictive_execution_allowed
        or authority.authoritative_cell_state_coupling_allowed
    ):
        raise ValueError("whole-cell runtime escaped its scientific authority gate")
    for surface in authority.surfaces:
        if (
            surface.phh_context_match
            or surface.quantitative_validation_allowed
            or surface.predictive_execution_allowed
            or surface.authoritative_cell_state_coupling_allowed
            or not surface.blockers
        ):
            raise ValueError("legacy whole-cell surface exceeded exploratory authority")


def assert_whole_cell_runtime_authority(
    purpose: WholeCellRuntimePurpose,
) -> WholeCellRuntimeAuthority:
    authority = build_whole_cell_runtime_authority()
    allowed = {
        "schematic_visualization": authority.schematic_visualization_allowed,
        "exploratory_execution": authority.exploratory_execution_allowed,
        "quantitative_validation": authority.quantitative_validation_allowed,
        "predictive_execution": authority.predictive_execution_allowed,
        "authoritative_cell_state_coupling": (
            authority.authoritative_cell_state_coupling_allowed
        ),
    }
    if purpose not in allowed:
        raise ValueError(f"Unsupported whole-cell runtime purpose: {purpose}")
    if not allowed[purpose]:
        blockers = tuple(
            dict.fromkeys(
                blocker
                for surface in authority.surfaces
                for blocker in surface.blockers
            )
        )
        raise WholeCellRuntimeAuthorityError(
            f"{purpose} is blocked for the schematic whole-cell runtime: "
            + "; ".join(blockers)
        )
    return authority


def whole_cell_runtime_authority_snapshot() -> dict[str, object]:
    authority = build_whole_cell_runtime_authority()
    payload = authority.to_dict()
    payload["summary"] = {
        "audited_legacy_surface_count": len(authority.surfaces),
        "phh_context_matched_surface_count": sum(
            surface.phh_context_match for surface in authority.surfaces
        ),
        "quantitative_authority_surface_count": sum(
            surface.quantitative_validation_allowed
            for surface in authority.surfaces
        ),
        "predictive_authority_surface_count": sum(
            surface.predictive_execution_allowed for surface in authority.surfaces
        ),
        "authoritative_state_coupling_surface_count": sum(
            surface.authoritative_cell_state_coupling_allowed
            for surface in authority.surfaces
        ),
    }
    return payload
