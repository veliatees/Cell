"""Fail-closed donor-resolved intake for hepatocyte receptor signal chains.

The communication atlas supplies mechanism topology and contact geometry. This
module accepts measurements needed to turn that topology into a quantitative
signal chain, while deliberately withholding receptor activation, kinetic
fitting, and cell-state authority.
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
from cell_engine.multicell.communication import build_hepatocyte_communication_atlas


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "evidence_intake"
    / "phh_receptor_signaling_trajectory_contract.v1.json"
)
DEFAULT_TRAJECTORY_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "evidence_intake"
    / "incoming"
    / "phh_receptor_signaling"
    / "latest"
    / "phh_receptor_signaling_trajectories.csv"
)
CONTRACT_SCHEMA_VERSION = "cell.phh-receptor-signaling-trajectory-contract.v1"
INTAKE_VERSION = "phh_receptor_signaling_trajectory_intake_v1"
GATE_VERSION = "phh_receptor_signaling_trajectory_gate_v1"

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
_MEASUREMENT_GEOMETRIES = frozenset(
    {
        "soluble_3d",
        "membrane_2d",
        "contact_patch_2d",
        "cell_internal",
        "whole_cell_output",
    }
)
_OBSERVABLE_KINDS = frozenset(
    {
        "concentration",
        "surface_density",
        "occupancy_fraction",
        "active_fraction",
        "kon_2d",
        "kon_3d",
        "koff",
        "internalized_fraction",
        "recycled_fraction",
        "gate_open_fraction",
        "phosphorylation_fraction",
        "abundance",
        "flux",
        "functional_response",
        "junction_permeability",
        "force",
        "validation_result",
    }
)
_STAGE_IDS = (
    "ligand_or_partner_exposure",
    "receptor_or_channel_surface_density",
    "active_fraction_or_occupancy",
    "association_dissociation",
    "internalization_recycling_or_gate_turnover",
    "proximal_signal",
    "downstream_functional_response",
    "independent_heldout_validation",
)
_DYNAMIC_STAGE_IDS = frozenset(
    {
        "active_fraction_or_occupancy",
        "internalization_recycling_or_gate_turnover",
        "proximal_signal",
        "downstream_functional_response",
        "independent_heldout_validation",
    }
)
_CONTACT_PATHWAY_IDS = frozenset(
    {
        "hbv_pres1_ntcp_egfr_entry",
        "cdh1_adherens_contact",
        "gjb1_connexin32_gap_junction",
    }
)


class ReceptorSignalingTrajectoryError(ValueError):
    """Raised when a signal-chain delivery violates the versioned contract."""


@dataclass(frozen=True)
class ReceptorSignalingRecord:
    record_id: str
    pathway_id: str
    stage_slot_id: str
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
    medium_context: str
    ligand_or_partner: str
    receptor_or_channel: str
    membrane_domain: str
    measurement_geometry: str
    assay: str
    biological_replicate_id: str
    time_value: float
    time_unit: str
    reported_value: float
    reported_unit: str
    reported_statistic: str
    sample_size: int
    manual_primary_source_review_status: str
    context_role: str
    notes: str
    surface_area_value: float | None
    surface_area_unit: str | None
    local_contact_patch_area_um2: float | None
    ligand_exposure_value: float | None
    ligand_exposure_unit: str | None
    assay_temperature_c: float | None
    assay_ph: float | None
    uncertainty_lower: float | None
    uncertainty_upper: float | None
    uncertainty_unit: str | None
    uncertainty_type: str | None
    binding_dimension: str | None
    validation_model_artifact_sha256: str | None
    validation_prediction_id: str | None
    validation_observation_id: str | None
    frozen_before_heldout_access: bool | None

    @property
    def donor_key(self) -> tuple[str, str]:
        return self.source_study_id, self.donor_id


@dataclass(frozen=True)
class ReceptorSignalingAssessment:
    pathway_id: str
    record_count: int
    covered_stage_slot_ids: tuple[str, ...]
    structurally_ready_stage_slot_ids: tuple[str, ...]
    complete_calibration_donor_count: int
    structurally_complete: bool
    receptor_activation_allowed: bool
    signal_execution_allowed: bool
    cell_state_coupling_allowed: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class ReceptorSignalingDataset:
    version: str
    contract_id: str
    delivery_path: str
    artifact_sha256: str
    contract_sha256: str
    records: tuple[ReceptorSignalingRecord, ...]


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


def _atlas_pathway_ids() -> frozenset[str]:
    return frozenset(pathway.id for pathway in build_hepatocyte_communication_atlas())


def load_receptor_signaling_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ReceptorSignalingTrajectoryError("signal-chain contract must be one object")
    if payload.get("schema_version") != CONTRACT_SCHEMA_VERSION:
        raise ReceptorSignalingTrajectoryError("unsupported signal-chain contract schema")
    required = payload.get("required_columns")
    conditional = payload.get("conditional_columns")
    gate = payload.get("trajectory_gate")
    policy = payload.get("policy")
    if not all(
        (
            isinstance(required, list),
            isinstance(conditional, list),
            isinstance(gate, dict),
            isinstance(policy, dict),
        )
    ):
        raise ReceptorSignalingTrajectoryError("signal-chain contract is malformed")
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
        or len(conditional_ids) != 16
        or len(set(conditional_ids)) != 16
        or not all(conditional_ids)
    ):
        raise ReceptorSignalingTrajectoryError("signal-chain field contract changed")
    atlas_ids = _atlas_pathway_ids()
    if (
        payload.get("target_pathway_count") != 8
        or payload.get("stage_slot_count_per_pathway") != 8
        or payload.get("required_stage_slot_count") != 64
        or frozenset(payload.get("target_pathway_ids", ())) != atlas_ids
        or tuple(payload.get("stage_slot_ids", ())) != _STAGE_IDS
    ):
        raise ReceptorSignalingTrajectoryError("signal-chain target atlas changed")
    if payload.get("canonical_null_token") != _NULL_TOKEN:
        raise ReceptorSignalingTrajectoryError("signal-chain null policy changed")
    allowed_sets = (
        ("allowed_split_roles", _SPLITS),
        ("allowed_source_types", _SOURCE_TYPES),
        ("allowed_context_roles", _CONTEXT_ROLES),
        ("allowed_manual_review_statuses", _REVIEW_STATUSES),
        ("allowed_measurement_geometries", _MEASUREMENT_GEOMETRIES),
        ("allowed_observable_kinds", _OBSERVABLE_KINDS),
    )
    if any(frozenset(payload.get(key, ())) != expected for key, expected in allowed_sets):
        raise ReceptorSignalingTrajectoryError("signal-chain categorical contract changed")
    required_true = {
        "same_donor_chain_required",
        "three_or_more_timepoints_for_dynamic_slots_required",
        "strictly_increasing_time_required",
        "surface_area_denominator_for_density_required",
        "two_dimensional_kinetics_for_contact_pathways_required",
        "matched_exposure_for_soluble_pathways_required",
        "internalization_recycling_or_gate_turnover_required",
        "donor_disjoint_validation_required",
        "independent_heldout_study_required",
        "frozen_model_before_heldout_access_required",
    }
    required_false = {
        "automatic_unit_conversion",
        "automatic_kinetic_fitting",
        "automatic_receptor_activation",
        "automatic_signal_execution",
        "automatic_cell_state_coupling",
    }
    if (
        gate.get("version") != GATE_VERSION
        or any(gate.get(key) is not True for key in required_true)
        or any(gate.get(key) is not False for key in required_false)
    ):
        raise ReceptorSignalingTrajectoryError("signal-chain gate escaped fail-closed policy")
    if policy.get("manual_primary_source_review_required") is not True or any(
        policy.get(key) is not False
        for key in (
            "cross_species_transfer_allowed",
            "cell_line_to_healthy_phh_transfer_allowed",
            "three_dimensional_kon_may_replace_two_dimensional_kon",
            "surfaceome_identity_may_replace_density",
            "whole_cell_abundance_may_replace_surface_density",
            "geometry_contact_may_replace_molecular_binding",
            "missing_stage_means_zero",
            "automatic_parameter_activation",
            "automatic_predictive_execution",
        )
    ):
        raise ReceptorSignalingTrajectoryError("signal-chain policy escaped fail-closed state")
    return payload


def _required_text(row: dict[str, str], field: str, row_number: int) -> str:
    value = row[field].strip()
    if not value or value.lower() == _NULL_TOKEN:
        raise ReceptorSignalingTrajectoryError(f"row {row_number}: {field} is required")
    return value


def _optional_text(row: dict[str, str], field: str) -> str | None:
    value = row[field].strip()
    return None if not value or value.lower() == _NULL_TOKEN else value


def _number(token: str, field: str, row_number: int) -> float:
    if not _NUMBER_RE.fullmatch(token.strip()):
        raise ReceptorSignalingTrajectoryError(
            f"row {row_number}: {field} must be one finite number"
        )
    value = float(token)
    if not math.isfinite(value):
        raise ReceptorSignalingTrajectoryError(f"row {row_number}: {field} must be finite")
    return value


def _optional_number(row: dict[str, str], field: str, row_number: int) -> float | None:
    token = row[field].strip()
    if not token or token.lower() == _NULL_TOKEN:
        return None
    return _number(token, field, row_number)


def _optional_boolean(row: dict[str, str], field: str, row_number: int) -> bool | None:
    token = row[field].strip().lower()
    if not token or token == _NULL_TOKEN:
        return None
    if token not in {"true", "false"}:
        raise ReceptorSignalingTrajectoryError(
            f"row {row_number}: {field} must be true, false, or null"
        )
    return token == "true"


def _record(
    row: dict[str, str],
    row_number: int,
    pathway_ids: frozenset[str],
) -> ReceptorSignalingRecord:
    pathway_id = _required_text(row, "pathway_id", row_number)
    stage_slot_id = _required_text(row, "stage_slot_id", row_number)
    observable_kind = _required_text(row, "observable_kind", row_number)
    split_role = _required_text(row, "split_role", row_number)
    source_type = _required_text(row, "source_type", row_number)
    context_role = _required_text(row, "context_role", row_number)
    review_status = _required_text(
        row, "manual_primary_source_review_status", row_number
    )
    geometry = _required_text(row, "measurement_geometry", row_number)
    if pathway_id not in pathway_ids:
        raise ReceptorSignalingTrajectoryError(
            f"row {row_number}: pathway_id is not in the communication atlas"
        )
    if stage_slot_id not in _STAGE_IDS:
        raise ReceptorSignalingTrajectoryError(
            f"row {row_number}: unknown signal-chain stage slot"
        )
    categorical = (
        (observable_kind, _OBSERVABLE_KINDS, "observable_kind"),
        (split_role, _SPLITS, "split_role"),
        (source_type, _SOURCE_TYPES, "source_type"),
        (context_role, _CONTEXT_ROLES, "context_role"),
        (review_status, _REVIEW_STATUSES, "manual_primary_source_review_status"),
        (geometry, _MEASUREMENT_GEOMETRIES, "measurement_geometry"),
    )
    for value, allowed, field in categorical:
        if value not in allowed:
            raise ReceptorSignalingTrajectoryError(
                f"row {row_number}: invalid {field}"
            )
    sample_token = _required_text(row, "sample_size", row_number)
    if not _INTEGER_RE.fullmatch(sample_token) or int(sample_token) <= 0:
        raise ReceptorSignalingTrajectoryError(
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
    if time_value < 0:
        raise ReceptorSignalingTrajectoryError(
            f"row {row_number}: time_value cannot be negative"
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
        raise ReceptorSignalingTrajectoryError(
            f"row {row_number}: uncertainty fields must be supplied together"
        )
    surface_area_value = _optional_number(row, "surface_area_value", row_number)
    surface_area_unit = _optional_text(row, "surface_area_unit")
    if (surface_area_value is None) != (surface_area_unit is None):
        raise ReceptorSignalingTrajectoryError(
            f"row {row_number}: surface-area value and unit must be paired"
        )
    if observable_kind == "surface_density" and (
        surface_area_value is None or surface_area_value <= 0
    ):
        raise ReceptorSignalingTrajectoryError(
            f"row {row_number}: surface density requires a positive measured area"
        )
    binding_dimension = _optional_text(row, "binding_dimension")
    if observable_kind == "kon_2d" and binding_dimension != "2d":
        raise ReceptorSignalingTrajectoryError(
            f"row {row_number}: kon_2d requires binding_dimension=2d"
        )
    if observable_kind == "kon_3d" and binding_dimension != "3d":
        raise ReceptorSignalingTrajectoryError(
            f"row {row_number}: kon_3d requires binding_dimension=3d"
        )
    validation_digest = _optional_text(row, "validation_model_artifact_sha256")
    validation_prediction = _optional_text(row, "validation_prediction_id")
    validation_observation = _optional_text(row, "validation_observation_id")
    frozen = _optional_boolean(row, "frozen_before_heldout_access", row_number)
    if split_role == "independent_heldout" and (
        stage_slot_id != "independent_heldout_validation"
        or context_role != "independent_healthy_phh_validation"
        or validation_digest is None
        or not re.fullmatch(r"[0-9a-f]{64}", validation_digest)
        or validation_prediction is None
        or validation_observation is None
        or frozen is not True
    ):
        raise ReceptorSignalingTrajectoryError(
            f"row {row_number}: held-out record lacks a frozen independent validation identity"
        )
    return ReceptorSignalingRecord(
        record_id=_required_text(row, "record_id", row_number),
        pathway_id=pathway_id,
        stage_slot_id=stage_slot_id,
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
        medium_context=_required_text(row, "medium_context", row_number),
        ligand_or_partner=_required_text(row, "ligand_or_partner", row_number),
        receptor_or_channel=_required_text(row, "receptor_or_channel", row_number),
        membrane_domain=_required_text(row, "membrane_domain", row_number),
        measurement_geometry=geometry,
        assay=_required_text(row, "assay", row_number),
        biological_replicate_id=_required_text(
            row, "biological_replicate_id", row_number
        ),
        time_value=time_value,
        time_unit=_required_text(row, "time_unit", row_number),
        reported_value=reported_value,
        reported_unit=_required_text(row, "reported_unit", row_number),
        reported_statistic=_required_text(row, "reported_statistic", row_number),
        sample_size=int(sample_token),
        manual_primary_source_review_status=review_status,
        context_role=context_role,
        notes=_required_text(row, "notes", row_number),
        surface_area_value=surface_area_value,
        surface_area_unit=surface_area_unit,
        local_contact_patch_area_um2=_optional_number(
            row, "local_contact_patch_area_um2", row_number
        ),
        ligand_exposure_value=_optional_number(
            row, "ligand_exposure_value", row_number
        ),
        ligand_exposure_unit=_optional_text(row, "ligand_exposure_unit"),
        assay_temperature_c=_optional_number(row, "assay_temperature_c", row_number),
        assay_ph=_optional_number(row, "assay_ph", row_number),
        uncertainty_lower=uncertainty_lower,
        uncertainty_upper=uncertainty_upper,
        uncertainty_unit=uncertainty_unit,
        uncertainty_type=uncertainty_type,
        binding_dimension=binding_dimension,
        validation_model_artifact_sha256=validation_digest,
        validation_prediction_id=validation_prediction,
        validation_observation_id=validation_observation,
        frozen_before_heldout_access=frozen,
    )


def load_receptor_signaling_dataset(
    path: Path = DEFAULT_TRAJECTORY_PATH,
) -> ReceptorSignalingDataset:
    contract = load_receptor_signaling_contract()
    expected_fields = tuple(
        item["id"]
        for group in ("required_columns", "conditional_columns")
        for item in contract[group]
    )
    if not path.exists():
        raise ReceptorSignalingTrajectoryError(
            f"signal-chain delivery not found: {_display_path(path)}"
        )
    pathway_ids = _atlas_pathway_ids()
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != expected_fields:
            raise ReceptorSignalingTrajectoryError(
                "signal-chain CSV header must exactly match the versioned contract"
            )
        records = tuple(
            _record(row, index, pathway_ids)
            for index, row in enumerate(reader, start=2)
        )
    if not records:
        raise ReceptorSignalingTrajectoryError("signal-chain delivery contains no records")
    record_ids = [record.record_id for record in records]
    if len(set(record_ids)) != len(record_ids):
        raise ReceptorSignalingTrajectoryError(
            "signal-chain record_id values must be unique"
        )
    donor_splits: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    study_splits: defaultdict[str, set[str]] = defaultdict(set)
    for record in records:
        donor_splits[record.donor_key].add(record.split_role)
        study_splits[record.source_study_id].add(record.split_role)
    if any(len(splits) > 1 for splits in donor_splits.values()):
        raise ReceptorSignalingTrajectoryError(
            "signal-chain donor crosses split roles"
        )
    if any(
        "independent_heldout" in splits and len(splits) > 1
        for splits in study_splits.values()
    ):
        raise ReceptorSignalingTrajectoryError(
            "signal-chain held-out study crosses development splits"
        )
    return ReceptorSignalingDataset(
        version=INTAKE_VERSION,
        contract_id=str(contract["contract_id"]),
        delivery_path=_display_path(path),
        artifact_sha256=_sha256(path),
        contract_sha256=_sha256(CONTRACT_PATH),
        records=records,
    )


def _has_dynamic_series(records: tuple[ReceptorSignalingRecord, ...]) -> bool:
    by_series: defaultdict[str, list[float]] = defaultdict(list)
    for record in records:
        by_series[record.series_id].append(record.time_value)
    return any(
        len(times) >= 3
        and len(set(times)) == len(times)
        and times == sorted(times)
        for times in by_series.values()
    )


def _stage_ready(
    pathway_id: str,
    stage_id: str,
    records: tuple[ReceptorSignalingRecord, ...],
) -> bool:
    if not records or any(
        record.manual_primary_source_review_status != "verified"
        for record in records
    ):
        return False
    if stage_id == "independent_heldout_validation":
        return (
            all(record.split_role == "independent_heldout" for record in records)
            and all(
                record.context_role == "independent_healthy_phh_validation"
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
    if stage_id == "ligand_or_partner_exposure":
        if pathway_id in _CONTACT_PATHWAY_IDS:
            return any(
                record.measurement_geometry == "contact_patch_2d"
                and record.local_contact_patch_area_um2 is not None
                and record.local_contact_patch_area_um2 > 0
                for record in records
            )
        return any(
            record.measurement_geometry == "soluble_3d"
            and (
                record.ligand_exposure_value is not None
                or record.observable_kind == "concentration"
            )
            for record in records
        )
    if stage_id == "receptor_or_channel_surface_density":
        return any(
            record.observable_kind == "surface_density"
            and record.surface_area_value is not None
            and record.surface_area_value > 0
            and record.measurement_geometry in {"membrane_2d", "contact_patch_2d"}
            for record in records
        )
    if stage_id == "association_dissociation":
        kinds = {record.observable_kind for record in records}
        if pathway_id in _CONTACT_PATHWAY_IDS:
            return (
                {"kon_2d", "koff"} <= kinds
                and all(
                    record.binding_dimension == "2d"
                    for record in records
                    if record.observable_kind == "kon_2d"
                )
            )
        return {"kon_3d", "koff"} <= kinds or _has_dynamic_series(
            tuple(
                record
                for record in records
                if record.observable_kind in {"occupancy_fraction", "active_fraction"}
            )
        )
    if stage_id in _DYNAMIC_STAGE_IDS:
        return _has_dynamic_series(records)
    return True


def assess_receptor_signaling_pathway(
    pathway_id: str,
    records: tuple[ReceptorSignalingRecord, ...],
) -> ReceptorSignalingAssessment:
    if pathway_id not in _atlas_pathway_ids():
        raise ReceptorSignalingTrajectoryError(f"unknown pathway id: {pathway_id}")
    selected = tuple(record for record in records if record.pathway_id == pathway_id)
    covered = frozenset(record.stage_slot_id for record in selected)
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
        donor_ready = {
            stage_id
            for stage_id in _STAGE_IDS[:-1]
            if _stage_ready(
                pathway_id,
                stage_id,
                tuple(
                    record
                    for record in donor_records
                    if record.stage_slot_id == stage_id
                ),
            )
        }
        ready_union.update(donor_ready)
        if donor_ready == set(_STAGE_IDS[:-1]):
            complete_donors += 1
    heldout_ready = _stage_ready(
        pathway_id,
        "independent_heldout_validation",
        tuple(
            record
            for record in selected
            if record.stage_slot_id == "independent_heldout_validation"
        ),
    )
    if heldout_ready:
        ready_union.add("independent_heldout_validation")
    structurally_complete = complete_donors > 0 and heldout_ready
    blockers: list[str] = []
    if complete_donors == 0:
        blockers.append(
            "no single healthy-PHH donor contains the seven matched quantitative chain stages"
        )
    if not heldout_ready:
        blockers.append(
            "frozen donor- and study-disjoint dynamic PHH validation is absent"
        )
    blockers.extend(
        (
            "manual cross-stage identity, unit, geometry and measurement-operator adjudication remains required",
            "no approved kinetic model artifact has been promoted",
            "receptor activation, signal execution and cell-state coupling remain disabled",
        )
    )
    return ReceptorSignalingAssessment(
        pathway_id=pathway_id,
        record_count=len(selected),
        covered_stage_slot_ids=tuple(sorted(covered)),
        structurally_ready_stage_slot_ids=tuple(sorted(ready_union)),
        complete_calibration_donor_count=complete_donors,
        structurally_complete=structurally_complete,
        receptor_activation_allowed=False,
        signal_execution_allowed=False,
        cell_state_coupling_allowed=False,
        blockers=tuple(blockers),
    )


def receptor_signaling_trajectory_snapshot(
    path: Path = DEFAULT_TRAJECTORY_PATH,
) -> dict[str, object]:
    contract = load_receptor_signaling_contract()
    pathway_ids = tuple(sorted(_atlas_pathway_ids()))
    expected_header_count = len(contract["required_columns"]) + len(
        contract["conditional_columns"]
    )
    if not path.exists():
        return {
            "version": INTAKE_VERSION,
            "contract_id": contract["contract_id"],
            "atlas_id": contract["atlas_id"],
            "status": "awaiting_receptor_signaling_trajectory_bundle",
            "delivery_path": _display_path(path),
            "contract_sha256": _sha256(CONTRACT_PATH),
            "expected_header_count": expected_header_count,
            "target_pathway_count": len(pathway_ids),
            "required_stage_slot_count": len(pathway_ids) * len(_STAGE_IDS),
            "record_count": 0,
            "covered_stage_slot_count": 0,
            "structurally_ready_stage_slot_count": 0,
            "complete_calibration_donor_pathway_count": 0,
            "structurally_complete_pathway_count": 0,
            "receptor_activation_allowed_count": 0,
            "signal_execution_allowed_count": 0,
            "cell_state_coupling_allowed_count": 0,
            "automatic_unit_conversion": False,
            "automatic_kinetic_fitting": False,
            "blockers": (
                "versioned receptor/signaling trajectory delivery is absent",
                "all 64 donor-matched signal-chain evidence slots remain unfilled",
                "independent held-out PHH validation is absent",
            ),
        }
    dataset = load_receptor_signaling_dataset(path)
    assessments = tuple(
        assess_receptor_signaling_pathway(pathway_id, dataset.records)
        for pathway_id in pathway_ids
    )
    covered = {
        (record.pathway_id, record.stage_slot_id) for record in dataset.records
    }
    ready = {
        (assessment.pathway_id, stage_id)
        for assessment in assessments
        for stage_id in assessment.structurally_ready_stage_slot_ids
    }
    return {
        "version": INTAKE_VERSION,
        "contract_id": dataset.contract_id,
        "atlas_id": contract["atlas_id"],
        "status": "receptor_signaling_trajectories_structurally_audited_not_authoritative",
        "delivery_path": dataset.delivery_path,
        "artifact_sha256": dataset.artifact_sha256,
        "contract_sha256": dataset.contract_sha256,
        "expected_header_count": expected_header_count,
        "target_pathway_count": len(pathway_ids),
        "required_stage_slot_count": len(pathway_ids) * len(_STAGE_IDS),
        "record_count": len(dataset.records),
        "record_count_by_split": dict(
            sorted(Counter(record.split_role for record in dataset.records).items())
        ),
        "covered_stage_slot_count": len(covered),
        "structurally_ready_stage_slot_count": len(ready),
        "complete_calibration_donor_pathway_count": sum(
            assessment.complete_calibration_donor_count
            for assessment in assessments
        ),
        "structurally_complete_pathway_count": sum(
            assessment.structurally_complete for assessment in assessments
        ),
        "receptor_activation_allowed_count": 0,
        "signal_execution_allowed_count": 0,
        "cell_state_coupling_allowed_count": 0,
        "automatic_unit_conversion": False,
        "automatic_kinetic_fitting": False,
        "pathway_assessments": tuple(to_plain(item) for item in assessments),
        "blockers": (
            "structural completeness is not model authority",
            "manual semantic adjudication and an approved immutable kinetic artifact are required",
            "receptor activation, signal execution and cell-state coupling remain disabled",
        ),
    }
