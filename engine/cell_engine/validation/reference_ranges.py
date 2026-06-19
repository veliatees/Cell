from __future__ import annotations

from dataclasses import dataclass

from cell_engine.core.cell_definition import CellDefinition
from cell_engine.core.provenance import AssumptionLevel


@dataclass(frozen=True)
class ReferenceRange:
    id: str
    target: str
    low: float
    high: float
    unit: str
    source_id: str
    assumption_level: AssumptionLevel
    notes: str = ""


def build_reference_registry(definition: CellDefinition) -> tuple[ReferenceRange, ...]:
    ranges: list[ReferenceRange] = []
    for pool in definition.pools:
        ranges.append(
            ReferenceRange(
                id=f"pool:{pool.id}",
                target=pool.id,
                low=pool.normal_range[0],
                high=pool.normal_range[1],
                unit=pool.unit,
                source_id=pool.source_id,
                assumption_level=pool.assumption_level,
                notes=pool.notes,
            )
        )
    for parameter in definition.parameters.values():
        if isinstance(parameter.value, (float, int)):
            ranges.append(
                ReferenceRange(
                    id=f"parameter:{parameter.name}",
                    target=parameter.name,
                    low=float(parameter.value),
                    high=float(parameter.value),
                    unit=parameter.unit,
                    source_id=parameter.source_id,
                    assumption_level=parameter.assumption_level,
                    notes=parameter.notes,
                )
            )
    return tuple(ranges)

