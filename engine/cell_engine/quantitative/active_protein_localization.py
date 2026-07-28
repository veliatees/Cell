"""Fail-closed intake for donor-matched active protein localization.

Total proteomic abundance, plasma-membrane localization, membrane-domain
localization, active fraction, denominator geometry, and function remain
separate measurements. A structurally complete delivery still cannot scale a
transporter, activate a receptor, or modify cell state automatically.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cell_engine.core.serialization import to_plain
from cell_engine.quantitative.phh_protein_functional_evidence import (
    build_phh_protein_functional_evidence,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "evidence_intake"
    / "phh_active_protein_localization_contract.v1.json"
)
DEFAULT_LOCALIZATION_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "evidence_intake"
    / "incoming"
    / "phh_active_protein_localization"
    / "latest"
    / "phh_active_protein_localization.csv"
)
CONTRACT_SCHEMA_VERSION = "cell.phh-active-protein-localization-contract.v1"
INTAKE_VERSION = "phh_active_protein_localization_intake_v1"
GATE_VERSION = "phh_active_protein_localization_gate_v1"

_NULL_TOKEN = "null"
_NUMBER_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
_INTEGER_RE = re.compile(r"^\d+$")
_SPLITS = frozenset({"calibration", "internal_validation", "independent_heldout"})
_SOURCE_TYPES = frozenset(
    {
        "primary_experiment",
        "primary_data_repository_record",
        "primary_model_with_traceable_measurement",
    }
)
_CONTEXT_ROLES = frozenset(
    {
        "direct_healthy_phh",
        "human_liver_bridge",
        "mechanistic_human_system_candidate",
        "independent_healthy_phh_validation",
    }
)
_REVIEW_STATUSES = frozenset({"pending", "verified"})
_OBSERVABLE_KINDS = frozenset(
    {
        "copies",
        "amount",
        "density",
        "fraction",
        "concentration",
        "area",
        "volume",
        "activity",
        "functional_response",
        "validation_result",
    }
)
_MEMBRANE_SLOTS = (
    "total_abundance",
    "plasma_membrane_localized_abundance",
    "membrane_domain_localized_abundance",
    "active_fraction",
    "domain_surface_area",
    "active_domain_copy_or_density",
    "same_assay_functional_readout",
    "independent_heldout_validation",
)
_CYTOSOLIC_SLOTS = (
    "total_abundance",
    "cytosol_localized_abundance",
    "active_fraction",
    "aqueous_cytosol_volume",
    "active_compartment_concentration",
    "same_assay_functional_readout",
    "independent_heldout_validation",
)


class ActiveProteinLocalizationError(ValueError):
    """Raised when active-protein evidence violates the intake contract."""


@dataclass(frozen=True)
class ActiveProteinLocalizationRecord:
    record_id: str
    protein_id: str
    gene: str
    slot_id: str
    series_id: str
    observable_id: str
    observable_kind: str
    split_role: str
    donor_id: str
    source_study_id: str
    source_locator: str
    source_type: str
    species: str
    cell_type: str
    biological_system: str
    culture_format: str
    health_state: str
    polarity_state: str
    biological_replicate_id: str
    assay: str
    compartment: str
    membrane_domain: str
    time_value: float
    time_unit: str
    reported_value: float
    reported_unit: str
    reported_statistic: str
    sample_size: int
    denominator_type: str
    manual_primary_source_review_status: str
    context_role: str
    notes: str
    denominator_value: float | None
    denominator_unit: str | None
    cell_count: int | None
    nucleus_count: int | None
    surface_area_value: float | None
    surface_area_unit: str | None
    compartment_volume_value: float | None
    compartment_volume_unit: str | None
    active_state_definition: str | None
    activity_probe_or_substrate: str | None
    probe_or_substrate_concentration: float | None
    probe_or_substrate_concentration_unit: str | None
    uncertainty_lower: float | None
    uncertainty_upper: float | None
    uncertainty_unit: str | None
    uncertainty_type: str | None
    validation_model_artifact_sha256: str | None
    validation_prediction_id: str | None
    validation_observation_id: str | None
    frozen_before_heldout_access: bool | None

    @property
    def donor_key(self) -> tuple[str, str]:
        return self.source_study_id, self.donor_id


@dataclass(frozen=True)
class ActiveProteinLocalizationAssessment:
    protein_id: str
    gene: str
    localization_class: str
    record_count: int
    required_slot_ids: tuple[str, ...]
    covered_slot_ids: tuple[str, ...]
    structurally_ready_slot_ids: tuple[str, ...]
    complete_calibration_donor_count: int
    structurally_complete: bool
    active_copy_or_concentration_authorized: bool
    functional_rate_authorized: bool
    cell_state_coupling_allowed: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class ActiveProteinLocalizationDataset:
    version: str
    contract_id: str
    delivery_path: str
    artifact_sha256: str
    contract_sha256: str
    records: tuple[ActiveProteinLocalizationRecord, ...]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPOSITORY_ROOT.resolve()))
    except ValueError:
        return str(path)


def _panel() -> dict[str, tuple[str, str]]:
    evidence = build_phh_protein_functional_evidence()
    panel: dict[str, tuple[str, str]] = {}
    for protein in evidence.proteins:
        panel[protein.protein_id] = (
            protein.gene,
            "cytosolic" if protein.protein_id == "glucokinase" else "membrane",
        )
    return panel


def _required_slots(localization_class: str) -> tuple[str, ...]:
    if localization_class == "membrane":
        return _MEMBRANE_SLOTS
    if localization_class == "cytosolic":
        return _CYTOSOLIC_SLOTS
    raise ActiveProteinLocalizationError(
        f"unknown protein localization class: {localization_class}"
    )


def load_active_protein_localization_contract(
    path: Path = CONTRACT_PATH,
) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ActiveProteinLocalizationError("active-protein contract must be one object")
    if payload.get("schema_version") != CONTRACT_SCHEMA_VERSION:
        raise ActiveProteinLocalizationError("unsupported active-protein contract schema")
    required = payload.get("required_columns")
    conditional = payload.get("conditional_columns")
    gate = payload.get("localization_gate")
    policy = payload.get("policy")
    if not all(
        (
            isinstance(required, list),
            isinstance(conditional, list),
            isinstance(gate, dict),
            isinstance(policy, dict),
        )
    ):
        raise ActiveProteinLocalizationError("active-protein contract is malformed")
    required_ids = tuple(
        str(item.get("id", "")) for item in required if isinstance(item, dict)
    )
    conditional_ids = tuple(
        str(item.get("id", "")) for item in conditional if isinstance(item, dict)
    )
    if (
        len(required_ids) != 32
        or len(set(required_ids)) != 32
        or not all(required_ids)
        or len(conditional_ids) != 20
        or len(set(conditional_ids)) != 20
        or not all(conditional_ids)
    ):
        raise ActiveProteinLocalizationError("active-protein field contract changed")
    panel = _panel()
    declared = {
        str(item["protein_id"]): (
            str(item["gene"]),
            str(item["localization_class"]),
        )
        for item in payload.get("target_proteins", ())
        if isinstance(item, dict)
    }
    if (
        payload.get("target_protein_count") != 8
        or payload.get("required_protein_slot_count") != 63
        or declared != panel
        or tuple(payload.get("required_slots_by_localization_class", {}).get("membrane", ()))
        != _MEMBRANE_SLOTS
        or tuple(payload.get("required_slots_by_localization_class", {}).get("cytosolic", ()))
        != _CYTOSOLIC_SLOTS
    ):
        raise ActiveProteinLocalizationError("active-protein target panel changed")
    if payload.get("canonical_null_token") != _NULL_TOKEN:
        raise ActiveProteinLocalizationError("active-protein null policy changed")
    allowed_sets = (
        ("allowed_split_roles", _SPLITS),
        ("allowed_source_types", _SOURCE_TYPES),
        ("allowed_context_roles", _CONTEXT_ROLES),
        ("allowed_manual_review_statuses", _REVIEW_STATUSES),
        ("allowed_observable_kinds", _OBSERVABLE_KINDS),
    )
    if any(frozenset(payload.get(key, ())) != expected for key, expected in allowed_sets):
        raise ActiveProteinLocalizationError("active-protein categorical contract changed")
    required_true = {
        "same_donor_total_localized_active_function_required",
        "same_assay_or_explicit_cross_assay_bridge_required",
        "surface_area_denominator_for_membrane_density_required",
        "aqueous_volume_denominator_for_cytosolic_concentration_required",
        "polarity_state_required_for_membrane_proteins",
        "operational_active_state_definition_required",
        "three_or_more_timepoints_for_functional_and_validation_series_required",
        "donor_disjoint_validation_required",
        "independent_heldout_study_required",
        "frozen_model_before_heldout_access_required",
    }
    required_false = {
        "automatic_unit_conversion",
        "automatic_total_to_surface_conversion",
        "automatic_surface_to_active_conversion",
        "automatic_flux_scaling",
        "automatic_cell_state_coupling",
    }
    if (
        gate.get("version") != GATE_VERSION
        or any(gate.get(key) is not True for key in required_true)
        or any(gate.get(key) is not False for key in required_false)
    ):
        raise ActiveProteinLocalizationError(
            "active-protein gate escaped fail-closed policy"
        )
    if policy.get("manual_primary_source_review_required") is not True or any(
        policy.get(key) is not False
        for key in (
            "cross_species_transfer_allowed",
            "cell_line_to_healthy_phh_transfer_allowed",
            "copies_per_nucleus_may_equal_copies_per_cell",
            "surface_capture_identity_may_equal_surface_abundance",
            "total_abundance_may_equal_active_abundance",
            "tissue_membrane_fraction_may_equal_canalicular_domain",
            "missing_slot_means_zero",
            "automatic_parameter_activation",
            "automatic_predictive_execution",
        )
    ):
        raise ActiveProteinLocalizationError(
            "active-protein policy escaped fail-closed state"
        )
    return payload


def _required_text(row: dict[str, str], field: str, row_number: int) -> str:
    value = row[field].strip()
    if not value or value.lower() == _NULL_TOKEN:
        raise ActiveProteinLocalizationError(f"row {row_number}: {field} is required")
    return value


def _optional_text(row: dict[str, str], field: str) -> str | None:
    value = row[field].strip()
    return None if not value or value.lower() == _NULL_TOKEN else value


def _number(token: str, field: str, row_number: int) -> float:
    if not _NUMBER_RE.fullmatch(token.strip()):
        raise ActiveProteinLocalizationError(
            f"row {row_number}: {field} must be one finite number"
        )
    value = float(token)
    if not math.isfinite(value):
        raise ActiveProteinLocalizationError(
            f"row {row_number}: {field} must be finite"
        )
    return value


def _optional_number(
    row: dict[str, str], field: str, row_number: int
) -> float | None:
    token = row[field].strip()
    if not token or token.lower() == _NULL_TOKEN:
        return None
    return _number(token, field, row_number)


def _optional_integer(
    row: dict[str, str], field: str, row_number: int
) -> int | None:
    token = row[field].strip()
    if not token or token.lower() == _NULL_TOKEN:
        return None
    if not _INTEGER_RE.fullmatch(token) or int(token) <= 0:
        raise ActiveProteinLocalizationError(
            f"row {row_number}: {field} must be a positive integer or null"
        )
    return int(token)


def _optional_boolean(
    row: dict[str, str], field: str, row_number: int
) -> bool | None:
    token = row[field].strip().lower()
    if not token or token == _NULL_TOKEN:
        return None
    if token not in {"true", "false"}:
        raise ActiveProteinLocalizationError(
            f"row {row_number}: {field} must be true, false, or null"
        )
    return token == "true"


def _paired(
    first: object | None,
    second: object | None,
    label: str,
    row_number: int,
) -> None:
    if (first is None) != (second is None):
        raise ActiveProteinLocalizationError(
            f"row {row_number}: {label} value and unit must be paired"
        )


def _record(
    row: dict[str, str],
    row_number: int,
    panel: dict[str, tuple[str, str]],
) -> ActiveProteinLocalizationRecord:
    protein_id = _required_text(row, "protein_id", row_number)
    gene = _required_text(row, "gene", row_number)
    if protein_id not in panel or panel[protein_id][0] != gene:
        raise ActiveProteinLocalizationError(
            f"row {row_number}: protein_id/gene pair is not in the target panel"
        )
    localization_class = panel[protein_id][1]
    slot_id = _required_text(row, "slot_id", row_number)
    if slot_id not in _required_slots(localization_class):
        raise ActiveProteinLocalizationError(
            f"row {row_number}: slot_id is invalid for {localization_class} protein"
        )
    observable_kind = _required_text(row, "observable_kind", row_number)
    split_role = _required_text(row, "split_role", row_number)
    source_type = _required_text(row, "source_type", row_number)
    context_role = _required_text(row, "context_role", row_number)
    review_status = _required_text(
        row, "manual_primary_source_review_status", row_number
    )
    categorical = (
        (observable_kind, _OBSERVABLE_KINDS, "observable_kind"),
        (split_role, _SPLITS, "split_role"),
        (source_type, _SOURCE_TYPES, "source_type"),
        (context_role, _CONTEXT_ROLES, "context_role"),
        (review_status, _REVIEW_STATUSES, "manual_primary_source_review_status"),
    )
    for value, allowed, field in categorical:
        if value not in allowed:
            raise ActiveProteinLocalizationError(
                f"row {row_number}: invalid {field}"
            )
    sample_token = _required_text(row, "sample_size", row_number)
    if not _INTEGER_RE.fullmatch(sample_token) or int(sample_token) <= 0:
        raise ActiveProteinLocalizationError(
            f"row {row_number}: sample_size must be a positive integer"
        )
    time_value = _number(
        _required_text(row, "time_value", row_number), "time_value", row_number
    )
    reported_value = _number(
        _required_text(row, "reported_value", row_number),
        "reported_value",
        row_number,
    )
    if time_value < 0 or reported_value < 0:
        raise ActiveProteinLocalizationError(
            f"row {row_number}: time and reported value must be non-negative"
        )
    denominator_value = _optional_number(row, "denominator_value", row_number)
    denominator_unit = _optional_text(row, "denominator_unit")
    surface_area_value = _optional_number(row, "surface_area_value", row_number)
    surface_area_unit = _optional_text(row, "surface_area_unit")
    compartment_volume_value = _optional_number(
        row, "compartment_volume_value", row_number
    )
    compartment_volume_unit = _optional_text(row, "compartment_volume_unit")
    probe_concentration = _optional_number(
        row, "probe_or_substrate_concentration", row_number
    )
    probe_concentration_unit = _optional_text(
        row, "probe_or_substrate_concentration_unit"
    )
    _paired(denominator_value, denominator_unit, "denominator", row_number)
    _paired(surface_area_value, surface_area_unit, "surface area", row_number)
    _paired(
        compartment_volume_value,
        compartment_volume_unit,
        "compartment volume",
        row_number,
    )
    _paired(
        probe_concentration,
        probe_concentration_unit,
        "probe/substrate concentration",
        row_number,
    )
    if slot_id in {
        "domain_surface_area",
        "active_domain_copy_or_density",
    } and (surface_area_value is None or surface_area_value <= 0):
        raise ActiveProteinLocalizationError(
            f"row {row_number}: membrane-domain slot requires measured surface area"
        )
    if slot_id in {
        "aqueous_cytosol_volume",
        "active_compartment_concentration",
    } and (
        compartment_volume_value is None or compartment_volume_value <= 0
    ):
        raise ActiveProteinLocalizationError(
            f"row {row_number}: cytosolic slot requires measured aqueous volume"
        )
    active_definition = _optional_text(row, "active_state_definition")
    if slot_id in {
        "active_fraction",
        "active_domain_copy_or_density",
        "active_compartment_concentration",
    } and active_definition is None:
        raise ActiveProteinLocalizationError(
            f"row {row_number}: active-protein slot requires an operational active-state definition"
        )
    if slot_id == "active_fraction" and (
        observable_kind != "fraction" or reported_value > 1
    ):
        raise ActiveProteinLocalizationError(
            f"row {row_number}: active_fraction must be a fraction in [0, 1]"
        )
    uncertainty_lower = _optional_number(row, "uncertainty_lower", row_number)
    uncertainty_upper = _optional_number(row, "uncertainty_upper", row_number)
    uncertainty_unit = _optional_text(row, "uncertainty_unit")
    uncertainty_type = _optional_text(row, "uncertainty_type")
    uncertainty_values = (
        uncertainty_lower,
        uncertainty_upper,
        uncertainty_unit,
        uncertainty_type,
    )
    if any(value is not None for value in uncertainty_values) and not all(
        value is not None for value in uncertainty_values
    ):
        raise ActiveProteinLocalizationError(
            f"row {row_number}: uncertainty fields must be supplied together"
        )
    validation_digest = _optional_text(row, "validation_model_artifact_sha256")
    validation_prediction = _optional_text(row, "validation_prediction_id")
    validation_observation = _optional_text(row, "validation_observation_id")
    frozen = _optional_boolean(row, "frozen_before_heldout_access", row_number)
    if split_role == "independent_heldout" and (
        slot_id != "independent_heldout_validation"
        or context_role != "independent_healthy_phh_validation"
        or validation_digest is None
        or not re.fullmatch(r"[0-9a-f]{64}", validation_digest)
        or validation_prediction is None
        or validation_observation is None
        or frozen is not True
    ):
        raise ActiveProteinLocalizationError(
            f"row {row_number}: held-out record lacks a frozen independent validation identity"
        )
    return ActiveProteinLocalizationRecord(
        record_id=_required_text(row, "record_id", row_number),
        protein_id=protein_id,
        gene=gene,
        slot_id=slot_id,
        series_id=_required_text(row, "series_id", row_number),
        observable_id=_required_text(row, "observable_id", row_number),
        observable_kind=observable_kind,
        split_role=split_role,
        donor_id=_required_text(row, "donor_id", row_number),
        source_study_id=_required_text(row, "source_study_id", row_number),
        source_locator=_required_text(row, "source_locator", row_number),
        source_type=source_type,
        species=_required_text(row, "species", row_number),
        cell_type=_required_text(row, "cell_type", row_number),
        biological_system=_required_text(row, "biological_system", row_number),
        culture_format=_required_text(row, "culture_format", row_number),
        health_state=_required_text(row, "health_state", row_number),
        polarity_state=_required_text(row, "polarity_state", row_number),
        biological_replicate_id=_required_text(
            row, "biological_replicate_id", row_number
        ),
        assay=_required_text(row, "assay", row_number),
        compartment=_required_text(row, "compartment", row_number),
        membrane_domain=_required_text(row, "membrane_domain", row_number),
        time_value=time_value,
        time_unit=_required_text(row, "time_unit", row_number),
        reported_value=reported_value,
        reported_unit=_required_text(row, "reported_unit", row_number),
        reported_statistic=_required_text(row, "reported_statistic", row_number),
        sample_size=int(sample_token),
        denominator_type=_required_text(row, "denominator_type", row_number),
        manual_primary_source_review_status=review_status,
        context_role=context_role,
        notes=_required_text(row, "notes", row_number),
        denominator_value=denominator_value,
        denominator_unit=denominator_unit,
        cell_count=_optional_integer(row, "cell_count", row_number),
        nucleus_count=_optional_integer(row, "nucleus_count", row_number),
        surface_area_value=surface_area_value,
        surface_area_unit=surface_area_unit,
        compartment_volume_value=compartment_volume_value,
        compartment_volume_unit=compartment_volume_unit,
        active_state_definition=active_definition,
        activity_probe_or_substrate=_optional_text(
            row, "activity_probe_or_substrate"
        ),
        probe_or_substrate_concentration=probe_concentration,
        probe_or_substrate_concentration_unit=probe_concentration_unit,
        uncertainty_lower=uncertainty_lower,
        uncertainty_upper=uncertainty_upper,
        uncertainty_unit=uncertainty_unit,
        uncertainty_type=uncertainty_type,
        validation_model_artifact_sha256=validation_digest,
        validation_prediction_id=validation_prediction,
        validation_observation_id=validation_observation,
        frozen_before_heldout_access=frozen,
    )


def load_active_protein_localization_dataset(
    path: Path = DEFAULT_LOCALIZATION_PATH,
) -> ActiveProteinLocalizationDataset:
    contract = load_active_protein_localization_contract()
    expected_fields = tuple(
        item["id"]
        for group in ("required_columns", "conditional_columns")
        for item in contract[group]
    )
    if not path.exists():
        raise ActiveProteinLocalizationError(
            f"active-protein delivery not found: {_display_path(path)}"
        )
    panel = _panel()
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != expected_fields:
            raise ActiveProteinLocalizationError(
                "active-protein CSV header must exactly match the versioned contract"
            )
        records = tuple(
            _record(row, index, panel)
            for index, row in enumerate(reader, start=2)
        )
    if not records:
        raise ActiveProteinLocalizationError(
            "active-protein delivery contains no records"
        )
    record_ids = [record.record_id for record in records]
    if len(set(record_ids)) != len(record_ids):
        raise ActiveProteinLocalizationError(
            "active-protein record_id values must be unique"
        )
    donor_splits: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    study_splits: defaultdict[str, set[str]] = defaultdict(set)
    for record in records:
        donor_splits[record.donor_key].add(record.split_role)
        study_splits[record.source_study_id].add(record.split_role)
    if any(len(splits) > 1 for splits in donor_splits.values()):
        raise ActiveProteinLocalizationError(
            "active-protein donor crosses split roles"
        )
    if any(
        "independent_heldout" in splits and len(splits) > 1
        for splits in study_splits.values()
    ):
        raise ActiveProteinLocalizationError(
            "active-protein held-out study crosses development splits"
        )
    return ActiveProteinLocalizationDataset(
        version=INTAKE_VERSION,
        contract_id=str(contract["contract_id"]),
        delivery_path=_display_path(path),
        artifact_sha256=_sha256(path),
        contract_sha256=_sha256(CONTRACT_PATH),
        records=records,
    )


def _has_dynamic_series(records: tuple[ActiveProteinLocalizationRecord, ...]) -> bool:
    by_series: defaultdict[str, list[float]] = defaultdict(list)
    for record in records:
        by_series[record.series_id].append(record.time_value)
    return any(
        len(times) >= 3
        and len(set(times)) == len(times)
        and times == sorted(times)
        for times in by_series.values()
    )


def _slot_ready(
    slot_id: str,
    localization_class: str,
    records: tuple[ActiveProteinLocalizationRecord, ...],
) -> bool:
    if not records or any(
        record.manual_primary_source_review_status != "verified"
        for record in records
    ):
        return False
    if slot_id == "independent_heldout_validation":
        return (
            all(
                record.split_role == "independent_heldout"
                and record.context_role == "independent_healthy_phh_validation"
                and record.frozen_before_heldout_access is True
                for record in records
            )
            and _has_dynamic_series(records)
        )
    if any(
        record.split_role != "calibration"
        or record.context_role != "direct_healthy_phh"
        or record.species != "Homo sapiens"
        for record in records
    ):
        return False
    if localization_class == "membrane" and any(
        record.polarity_state in {"unknown", "not_assessed"}
        for record in records
    ):
        return False
    if slot_id == "domain_surface_area":
        return any(
            record.observable_kind == "area"
            and record.surface_area_value is not None
            and record.surface_area_value > 0
            for record in records
        )
    if slot_id == "active_domain_copy_or_density":
        return any(
            record.observable_kind in {"copies", "amount", "density"}
            and record.surface_area_value is not None
            and record.active_state_definition is not None
            for record in records
        )
    if slot_id == "aqueous_cytosol_volume":
        return any(
            record.observable_kind == "volume"
            and record.compartment_volume_value is not None
            and record.compartment_volume_value > 0
            for record in records
        )
    if slot_id == "active_compartment_concentration":
        return any(
            record.observable_kind == "concentration"
            and record.compartment_volume_value is not None
            and record.active_state_definition is not None
            for record in records
        )
    if slot_id == "active_fraction":
        return any(
            record.observable_kind == "fraction"
            and 0 <= record.reported_value <= 1
            and record.active_state_definition is not None
            for record in records
        )
    if slot_id == "same_assay_functional_readout":
        return (
            _has_dynamic_series(records)
            and all(record.activity_probe_or_substrate is not None for record in records)
        )
    return True


def assess_active_protein_localization(
    protein_id: str,
    records: tuple[ActiveProteinLocalizationRecord, ...],
) -> ActiveProteinLocalizationAssessment:
    panel = _panel()
    if protein_id not in panel:
        raise ActiveProteinLocalizationError(f"unknown protein id: {protein_id}")
    gene, localization_class = panel[protein_id]
    required_slots = _required_slots(localization_class)
    selected = tuple(record for record in records if record.protein_id == protein_id)
    covered = frozenset(record.slot_id for record in selected)
    calibration_donors = sorted(
        {
            record.donor_key
            for record in selected
            if record.split_role == "calibration"
        }
    )
    complete_donors = 0
    ready_union: set[str] = set()
    for donor_key in calibration_donors:
        donor_records = tuple(
            record
            for record in selected
            if record.donor_key == donor_key
        )
        replicate_ids = {record.biological_replicate_id for record in donor_records}
        if len(replicate_ids) != 1:
            continue
        donor_ready = {
            slot_id
            for slot_id in required_slots[:-1]
            if _slot_ready(
                slot_id,
                localization_class,
                tuple(
                    record
                    for record in donor_records
                    if record.slot_id == slot_id
                ),
            )
        }
        ready_union.update(donor_ready)
        if donor_ready == set(required_slots[:-1]):
            complete_donors += 1
    heldout_ready = _slot_ready(
        "independent_heldout_validation",
        localization_class,
        tuple(
            record
            for record in selected
            if record.slot_id == "independent_heldout_validation"
        ),
    )
    if heldout_ready:
        ready_union.add("independent_heldout_validation")
    structurally_complete = complete_donors > 0 and heldout_ready
    blockers: list[str] = []
    if complete_donors == 0:
        blockers.append(
            "no single healthy-PHH donor/replicate links total, localized, active and functional measurements"
        )
    if not heldout_ready:
        blockers.append(
            "frozen donor- and study-disjoint functional PHH validation is absent"
        )
    blockers.extend(
        (
            "manual cross-assay identity, denominator, unit and polarity adjudication remains required",
            "no approved active-copy or active-concentration artifact has been promoted",
            "protein-rate scaling and cell-state coupling remain disabled",
        )
    )
    return ActiveProteinLocalizationAssessment(
        protein_id=protein_id,
        gene=gene,
        localization_class=localization_class,
        record_count=len(selected),
        required_slot_ids=required_slots,
        covered_slot_ids=tuple(sorted(covered)),
        structurally_ready_slot_ids=tuple(sorted(ready_union)),
        complete_calibration_donor_count=complete_donors,
        structurally_complete=structurally_complete,
        active_copy_or_concentration_authorized=False,
        functional_rate_authorized=False,
        cell_state_coupling_allowed=False,
        blockers=tuple(blockers),
    )


def active_protein_localization_snapshot(
    path: Path = DEFAULT_LOCALIZATION_PATH,
) -> dict[str, object]:
    contract = load_active_protein_localization_contract()
    panel = _panel()
    protein_ids = tuple(sorted(panel))
    expected_header_count = len(contract["required_columns"]) + len(
        contract["conditional_columns"]
    )
    required_slot_count = sum(
        len(_required_slots(localization_class))
        for _, localization_class in panel.values()
    )
    if not path.exists():
        return {
            "version": INTAKE_VERSION,
            "contract_id": contract["contract_id"],
            "protein_panel_id": contract["protein_panel_id"],
            "status": "awaiting_active_protein_localization_bundle",
            "delivery_path": _display_path(path),
            "contract_sha256": _sha256(CONTRACT_PATH),
            "expected_header_count": expected_header_count,
            "target_protein_count": len(protein_ids),
            "required_protein_slot_count": required_slot_count,
            "record_count": 0,
            "covered_protein_slot_count": 0,
            "structurally_ready_protein_slot_count": 0,
            "complete_calibration_donor_protein_count": 0,
            "structurally_complete_protein_count": 0,
            "active_copy_or_concentration_authorized_count": 0,
            "functional_rate_authorized_count": 0,
            "cell_state_coupling_allowed_count": 0,
            "automatic_total_to_surface_conversion": False,
            "automatic_surface_to_active_conversion": False,
            "automatic_flux_scaling": False,
            "blockers": (
                "versioned active-protein localization delivery is absent",
                "all 63 donor-matched localization/activity slots remain unfilled",
                "independent held-out PHH validation is absent",
            ),
        }
    dataset = load_active_protein_localization_dataset(path)
    assessments = tuple(
        assess_active_protein_localization(protein_id, dataset.records)
        for protein_id in protein_ids
    )
    covered = {
        (record.protein_id, record.slot_id) for record in dataset.records
    }
    ready = {
        (assessment.protein_id, slot_id)
        for assessment in assessments
        for slot_id in assessment.structurally_ready_slot_ids
    }
    return {
        "version": INTAKE_VERSION,
        "contract_id": dataset.contract_id,
        "protein_panel_id": contract["protein_panel_id"],
        "status": "active_protein_localization_structurally_audited_not_authoritative",
        "delivery_path": dataset.delivery_path,
        "artifact_sha256": dataset.artifact_sha256,
        "contract_sha256": dataset.contract_sha256,
        "expected_header_count": expected_header_count,
        "target_protein_count": len(protein_ids),
        "required_protein_slot_count": required_slot_count,
        "record_count": len(dataset.records),
        "record_count_by_split": dict(
            sorted(Counter(record.split_role for record in dataset.records).items())
        ),
        "covered_protein_slot_count": len(covered),
        "structurally_ready_protein_slot_count": len(ready),
        "complete_calibration_donor_protein_count": sum(
            assessment.complete_calibration_donor_count
            for assessment in assessments
        ),
        "structurally_complete_protein_count": sum(
            assessment.structurally_complete for assessment in assessments
        ),
        "active_copy_or_concentration_authorized_count": 0,
        "functional_rate_authorized_count": 0,
        "cell_state_coupling_allowed_count": 0,
        "automatic_total_to_surface_conversion": False,
        "automatic_surface_to_active_conversion": False,
        "automatic_flux_scaling": False,
        "protein_assessments": tuple(to_plain(item) for item in assessments),
        "blockers": (
            "structural completeness is not active-protein authority",
            "manual denominator and cross-assay adjudication plus an immutable approved artifact are required",
            "protein-rate scaling and cell-state coupling remain disabled",
        ),
    }
