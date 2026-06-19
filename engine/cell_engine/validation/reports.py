from __future__ import annotations

from dataclasses import dataclass

from cell_engine.core.cell_definition import CellDefinition
from cell_engine.core.provenance import AssumptionLevel
from cell_engine.core.state import CellState
from cell_engine.validation.reference_ranges import ReferenceRange, build_reference_registry


@dataclass(frozen=True)
class AssumptionReport:
    definition_id: str
    counts: dict[str, int]
    placeholder_pools: tuple[str, ...]
    placeholder_parameters: tuple[str, ...]
    reference_ranges: tuple[ReferenceRange, ...]
    runtime_sections: dict[str, int]


def build_assumption_report(definition: CellDefinition, state: CellState | None = None) -> AssumptionReport:
    counts: dict[str, int] = {level: 0 for level in ("measured", "literature_derived", "fitted", "placeholder")}
    placeholder_pools: list[str] = []
    placeholder_parameters: list[str] = []

    def add(level: AssumptionLevel) -> None:
        counts[level] = counts.get(level, 0) + 1

    for pool in definition.pools:
        add(pool.assumption_level)
        if pool.assumption_level == "placeholder":
            placeholder_pools.append(pool.id)

    for parameter in definition.parameters.values():
        add(parameter.assumption_level)
        if parameter.assumption_level == "placeholder":
            placeholder_parameters.append(parameter.name)

    runtime_sections = {
        "cargo_packets": len(state.cargo_packets) if state else 0,
        "metabolic_fluxes": len(state.metabolic_fluxes) if state else 0,
        "pathway_results": len(state.pathway_results) if state else 0,
        "signaling_results": len(state.signaling_results) if state else 0,
        "membrane_state": 1 if state and state.membrane_state is not None else 0,
    }

    return AssumptionReport(
        definition_id=definition.id,
        counts=counts,
        placeholder_pools=tuple(placeholder_pools),
        placeholder_parameters=tuple(placeholder_parameters),
        reference_ranges=build_reference_registry(definition),
        runtime_sections=runtime_sections,
    )

