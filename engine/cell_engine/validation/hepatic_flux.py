"""Lossless healthy-human hepatic flux evidence bundle and scale audit."""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cell_engine.core.serialization import to_plain
from cell_engine.quantitative.endocrine import endocrine_profile_status
from cell_engine.quantitative.phh_profiles import PhhNutritionalState, phh_profile


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


@dataclass(frozen=True)
class NutritionalFluxObservation:
    pmid: str
    metabolite: str
    nutritional_state: str
    site: str
    measure_type: str
    value: float
    unit: str
    dispersion: str | None
    sample_size: int | None
    bed_scope: str
    source_locator: str


@dataclass(frozen=True)
class UnifiedNutritionalContext:
    profile_id: PhhNutritionalState
    profile_label: str
    status: str
    glycogen_value: float
    glycogen_unit: str
    glycogen_low: float | None
    glycogen_high: float | None
    energy_charge: float
    blood_glucose_boundary_status: str
    blood_glucose_target_mM: float | None
    hormone_concentrations_status: str
    ketone_concentration_status: str
    organ_flux_observations: tuple[NutritionalFluxObservation, ...]
    observation_units: tuple[str, ...]
    flux_consolidation_status: str
    per_cell_flux_ready: bool
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def nutritional_group(label: str) -> str:
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
        nutritional_state_counts=dict(Counter(nutritional_group(str(record["nutritional_state"])) for record in records)),
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


def build_unified_nutritional_context(profile_id: PhhNutritionalState) -> UnifiedNutritionalContext:
    registry = load_hepatic_flux_evidence()
    profile = phh_profile(profile_id)
    group = {
        "fed_peak": "fed",
        "postabsorptive": "postabsorptive",
        "prolonged_fasted": "prolonged_fast",
    }[profile_id]
    observations = tuple(
        NutritionalFluxObservation(
            pmid=str(record["pmid"]),
            metabolite=str(record["metabolite"]),
            nutritional_state=str(record["nutritional_state"]),
            site=str(record["site"]),
            measure_type=str(record["measure_type"]),
            value=float(record["value"]),
            unit=str(record["unit"]),
            dispersion=str(record["dispersion_SD_SEM_range"]) if record.get("dispersion_SD_SEM_range") else None,
            sample_size=int(record["sample_size_n"]) if record.get("sample_size_n") is not None else None,
            bed_scope=str(record["bed_scope"]),
            source_locator=str(record["source_locator"]),
        )
        for record in registry.records
        if nutritional_group(str(record["nutritional_state"])) == group
        and record.get("health_status") in ("healthy", "healthy_controls")
        and isinstance(record.get("value"), (int, float))
    )
    glucose = profile.pools.get("glucose_blood")
    glycogen = profile.pools["glycogen"]
    context = UnifiedNutritionalContext(
        profile_id=profile_id,
        profile_label=profile.label,
        status="source_backed_profile_with_organ_flux_reference",
        glycogen_value=glycogen.value_mM,
        glycogen_unit="mM_liver_tissue_equivalent",
        glycogen_low=glycogen.low_mM,
        glycogen_high=glycogen.high_mM,
        energy_charge=profile.energy_charge(),
        blood_glucose_boundary_status=("source_backed" if glucose else "blocked_no_profile_specific_blood_target"),
        blood_glucose_target_mM=(glucose.value_mM if glucose else None),
        hormone_concentrations_status=endocrine_profile_status(profile_id),
        ketone_concentration_status="not_loaded_no_scale_matched_profile_concentration",
        organ_flux_observations=observations,
        observation_units=tuple(sorted({item.unit for item in observations})),
        flux_consolidation_status="not_consolidated_heterogeneous_methods_units_and_scopes",
        per_cell_flux_ready=False,
        limitations=(
            "Organ, splanchnic and whole-body observations are retained verbatim and are not averaged.",
            "No organ-scale observation is divided into a single-hepatocyte flux.",
            "Only postabsorptive glucose currently has a source-backed blood concentration boundary.",
            "Measured peripheral hormones do not enable portal receptor occupancy or uncalibrated reaction rates.",
        ),
    )
    validate_unified_nutritional_context(context)
    return context


def validate_unified_nutritional_context(context: UnifiedNutritionalContext) -> None:
    if context.per_cell_flux_ready:
        raise HepaticFluxEvidenceError("nutritional context cannot enable per-cell flux")
    if context.profile_id == "postabsorptive":
        if context.blood_glucose_target_mM is None:
            raise HepaticFluxEvidenceError("postabsorptive context requires its sourced glucose boundary")
    elif context.blood_glucose_target_mM is not None:
        raise HepaticFluxEvidenceError("unsourced fed/fasted blood glucose target leaked into context")
    if not context.organ_flux_observations:
        raise HepaticFluxEvidenceError(f"no healthy numeric organ observations for {context.profile_id}")
    if context.flux_consolidation_status.startswith("consolidated"):
        raise HepaticFluxEvidenceError("heterogeneous organ observations cannot be silently consolidated")


def unified_nutritional_context_snapshot(profile_id: PhhNutritionalState) -> dict[str, object]:
    return build_unified_nutritional_context(profile_id).to_dict()
