"""Lossless healthy-human hepatic flux evidence bundle and scale audit."""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
HEPATIC_FLUX_ROOT = REPOSITORY_ROOT / "data" / "hepatic_flux"
DATASET_PATH = HEPATIC_FLUX_ROOT / "raw" / "hepatic_flux_dataset.json"
RECORDS_PATH = HEPATIC_FLUX_ROOT / "raw" / "measured_records.json"
FLAT_PATH = HEPATIC_FLUX_ROOT / "raw" / "hepatic_flux_flat.csv"
CONVERSION_PATH = HEPATIC_FLUX_ROOT / "raw" / "conversion_scaffold.json"


class HepaticFluxEvidenceError(ValueError):
    pass


@dataclass(frozen=True)
class HepaticFluxEvidenceRegistry:
    records: tuple[dict[str, Any], ...]
    conversion_scaffold: dict[str, Any]
    numeric_record_count: int
    healthy_numeric_record_count: int
    metabolite_counts: dict[str, int]
    nutritional_state_counts: dict[str, int]
    bed_scope_counts: dict[str, int]
    per_cell_applicable_count: int


def _nutritional_group(label: str) -> str:
    if label.startswith("fed"):
        return "fed"
    if label.startswith("prolonged_fast"):
        return "prolonged_fast"
    if label.startswith("postabsorptive"):
        return "postabsorptive"
    return "other"


def load_hepatic_flux_evidence() -> HepaticFluxEvidenceRegistry:
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    records = json.loads(RECORDS_PATH.read_text(encoding="utf-8"))
    scaffold = json.loads(CONVERSION_PATH.read_text(encoding="utf-8"))
    if not isinstance(records, list) or dataset.get("MEASURED_records") != records:
        raise HepaticFluxEvidenceError("combined and standalone measured records differ")
    with FLAT_PATH.open(encoding="utf-8", newline="") as handle:
        flat_records = list(csv.DictReader(handle))
    if len(flat_records) != len(records):
        raise HepaticFluxEvidenceError("CSV and JSON record counts differ")
    for json_record, csv_record in zip(records, flat_records):
        for field in ("pmid", "metabolite", "nutritional_state", "bed_scope"):
            if str(json_record.get(field, "")) != str(csv_record.get(field, "")):
                raise HepaticFluxEvidenceError(f"CSV/JSON mismatch for {field}")
    if any(record.get("applicable_to_single_hepatocyte") is not False for record in records):
        raise HepaticFluxEvidenceError("organ-scale record incorrectly marked as per-hepatocyte")
    conversion_policy = str(scaffold.get("_meta", {}).get("conversion_policy", ""))
    if "NO per-hepatocyte conversion" not in conversion_policy:
        raise HepaticFluxEvidenceError("conversion scaffold lost its non-execution policy")
    per_cell_formula = next(
        (item for item in scaffold.get("conversion_formulae", ()) if item.get("id") == "F3_per_gram_to_per_hepatocyte"),
        None,
    )
    if per_cell_formula is None or "NEVER executed" not in str(per_cell_formula.get("applicable", "")):
        raise HepaticFluxEvidenceError("per-cell conversion is not explicitly disabled")
    numeric = tuple(record for record in records if isinstance(record.get("value"), (int, float)))
    healthy_numeric = tuple(
        record for record in numeric if record.get("health_status") in ("healthy", "healthy_controls")
    )
    return HepaticFluxEvidenceRegistry(
        records=tuple(records),
        conversion_scaffold=scaffold,
        numeric_record_count=len(numeric),
        healthy_numeric_record_count=len(healthy_numeric),
        metabolite_counts=dict(Counter(str(record["metabolite"]) for record in records)),
        nutritional_state_counts=dict(Counter(_nutritional_group(str(record["nutritional_state"])) for record in records)),
        bed_scope_counts=dict(Counter(str(record["bed_scope"]) for record in records)),
        per_cell_applicable_count=0,
    )


def hepatic_flux_evidence_snapshot() -> dict[str, object]:
    registry = load_hepatic_flux_evidence()
    return {
        "status": "organ_scale_reference_evidence_not_single_cell_calibration",
        "record_count": len(registry.records),
        "numeric_record_count": registry.numeric_record_count,
        "healthy_numeric_record_count": registry.healthy_numeric_record_count,
        "metabolite_counts": registry.metabolite_counts,
        "nutritional_state_counts": registry.nutritional_state_counts,
        "bed_scope_counts": registry.bed_scope_counts,
        "per_cell_applicable_count": registry.per_cell_applicable_count,
        "readiness": {
            "organ_scale_reference_evidence_available": True,
            "single_cell_flux_ready": False,
            "healthy_portal_resolved_ready": False,
            "in_vivo_human_glut2_kinetics_ready": False,
        },
        "policy": "Measured organ, splanchnic and whole-body records may validate scale-matched outputs only; no per-hepatocyte conversion is executed.",
        "raw_paths": (
            "data/hepatic_flux/raw/hepatic_flux_dataset.json",
            "data/hepatic_flux/raw/hepatic_flux_flat.csv",
            "data/hepatic_flux/raw/measured_records.json",
            "data/hepatic_flux/raw/conversion_scaffold.json",
        ),
        "audit_paths": (
            "data/hepatic_flux/audit/source_audit.md",
            "data/hepatic_flux/audit/unidentifiable_parameters.md",
        ),
    }
