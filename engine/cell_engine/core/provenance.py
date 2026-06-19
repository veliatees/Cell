from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

AssumptionLevel = Literal["measured", "literature_derived", "fitted", "placeholder"]
SourceType = Literal["primary_paper", "textbook", "review", "database", "tool_doc", "project_assumption"]


@dataclass(frozen=True)
class SourceReference:
    id: str
    title: str
    url: str
    source_type: SourceType
    date_verified: str
    notes: str = ""


@dataclass(frozen=True)
class ParameterProvenance:
    name: str
    value: float | str
    unit: str
    source_id: str
    assumption_level: AssumptionLevel
    confidence: float
    notes: str = ""

