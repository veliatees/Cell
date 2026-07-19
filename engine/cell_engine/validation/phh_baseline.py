from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from cell_engine.core.provenance import SourceReference


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PHH_BASELINE_PATH = REPOSITORY_ROOT / "data" / "phh_baseline" / "curated" / "quantitative_anchors.json"


class PhhBaselineError(ValueError):
    pass


@dataclass(frozen=True)
class PhhMeasurement:
    value: float | None
    low: float | None
    high: float | None
    uncertainty_type: str | None
    uncertainty_value: float | None
    unit: str


@dataclass(frozen=True)
class PhhQuantitativeAnchor:
    id: str
    target: str
    measurement: PhhMeasurement
    biological_system: str
    assay: str
    sample_size: int | None
    source_id: str
    model_use: str
    applicability: str
    limitations: str


@dataclass(frozen=True)
class PhhBaselineRegistry:
    date_verified: str
    policy: str
    sources: Mapping[str, SourceReference]
    anchors: tuple[PhhQuantitativeAnchor, ...]
    direct_initialization_ready: bool
    metabolic_pool_initialization_ready: bool
    apparent_atp_exchange_observation_ready: bool
    energy_turnover_ready: bool
    whole_cell_transport_flux_ready: bool
    blocking_measurements: tuple[str, ...]


def _optional_number(value: object) -> float | None:
    if value is None:
        return None
    number = float(value)
    if not math.isfinite(number):
        raise PhhBaselineError("PHH measurements must be finite")
    return number


def load_phh_baseline(path: Path = PHH_BASELINE_PATH) -> PhhBaselineRegistry:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise PhhBaselineError("Unsupported PHH baseline schema")
    date_verified = str(payload.get("date_verified", ""))
    source_payload = payload.get("sources", {})
    sources = {
        source_id: SourceReference(
            id=source_id,
            title=str(item["title"]),
            url=str(item["url"]),
            source_type=str(item["source_type"]),  # type: ignore[arg-type]
            date_verified=date_verified,
            notes=str(item.get("notes", "")),
        )
        for source_id, item in source_payload.items()
    }
    anchors: list[PhhQuantitativeAnchor] = []
    for item in payload.get("anchors", ()):
        measurement = item["measurement"]
        anchor = PhhQuantitativeAnchor(
            id=str(item["id"]),
            target=str(item["target"]),
            measurement=PhhMeasurement(
                value=_optional_number(measurement.get("value")),
                low=_optional_number(measurement.get("low")),
                high=_optional_number(measurement.get("high")),
                uncertainty_type=str(measurement["uncertainty_type"]) if measurement.get("uncertainty_type") is not None else None,
                uncertainty_value=_optional_number(measurement.get("uncertainty_value")),
                unit=str(measurement["unit"]),
            ),
            biological_system=str(item["biological_system"]),
            assay=str(item["assay"]),
            sample_size=int(item["sample_size"]) if item.get("sample_size") is not None else None,
            source_id=str(item["source_id"]),
            model_use=str(item["model_use"]),
            applicability=str(item["applicability"]),
            limitations=str(item["limitations"]),
        )
        if anchor.source_id not in sources:
            raise PhhBaselineError(f"Unknown source for PHH anchor {anchor.id}")
        values = (anchor.measurement.value, anchor.measurement.low, anchor.measurement.high)
        if all(value is None for value in values):
            raise PhhBaselineError(f"PHH anchor {anchor.id} has no numeric measurement")
        if anchor.measurement.low is not None and anchor.measurement.high is not None and anchor.measurement.high < anchor.measurement.low:
            raise PhhBaselineError(f"PHH anchor {anchor.id} has descending bounds")
        anchors.append(anchor)
    ids = [anchor.id for anchor in anchors]
    if len(ids) != len(set(ids)):
        raise PhhBaselineError("Duplicate PHH baseline anchor IDs")
    readiness = payload.get("readiness", {})
    return PhhBaselineRegistry(
        date_verified=date_verified,
        policy=str(payload.get("policy", "")),
        sources=sources,
        anchors=tuple(anchors),
        direct_initialization_ready=bool(readiness.get("direct_initialization_ready", False)),
        metabolic_pool_initialization_ready=bool(readiness.get("metabolic_pool_initialization_ready", False)),
        apparent_atp_exchange_observation_ready=bool(
            readiness.get("apparent_atp_exchange_observation_ready", False)
        ),
        energy_turnover_ready=bool(readiness.get("energy_turnover_ready", False)),
        whole_cell_transport_flux_ready=bool(readiness.get("whole_cell_transport_flux_ready", False)),
        blocking_measurements=tuple(str(item) for item in readiness.get("blocking_measurements", ())),
    )


def phh_baseline_snapshot(registry: PhhBaselineRegistry | None = None) -> dict[str, object]:
    registry = registry or load_phh_baseline()
    return {
        "date_verified": registry.date_verified,
        "policy": registry.policy,
        "anchor_count": len(registry.anchors),
        "anchors": registry.anchors,
        "readiness": {
            "direct_initialization_ready": registry.direct_initialization_ready,
            "metabolic_pool_initialization_ready": registry.metabolic_pool_initialization_ready,
            "apparent_atp_exchange_observation_ready": registry.apparent_atp_exchange_observation_ready,
            "energy_turnover_ready": registry.energy_turnover_ready,
            "whole_cell_transport_flux_ready": registry.whole_cell_transport_flux_ready,
            "blocking_measurements": registry.blocking_measurements,
        },
    }
