"""Fail-closed donor-resolved PHH energy/redox trajectory intake.

The intake binds observations to exact compartmental pool IDs and preserves raw
units, uncertainty, oxygen/nutrient context, targeting validation, donor splits
and sealed held-out provenance. It does not initialize a pool or fit a rate.
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
from cell_engine.quantitative.compartmental_energy_redox import (
    build_compartmental_energy_redox_contract,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "evidence_intake"
    / "phh_energy_redox_trajectory_contract.v1.json"
)
DEFAULT_TRAJECTORY_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "evidence_intake"
    / "incoming"
    / "phh_energy_redox"
    / "latest"
    / "phh_energy_redox_trajectories.csv"
)
CONTRACT_SCHEMA_VERSION = "cell.phh-energy-redox-trajectory-contract.v1"
INTAKE_VERSION = "phh_energy_redox_trajectory_intake_v1"
TRAJECTORY_GATE_VERSION = "phh_energy_redox_trajectory_gate_v1"

_NULL_TOKEN = "null"
_NUMBER_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
_INTEGER_RE = re.compile(r"^\d+$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_SPLITS = frozenset(
    {"calibration", "internal_validation", "independent_heldout"}
)
_ALLOWED_MEASUREMENT_KINDS = frozenset(
    {
        "absolute_concentration",
        "calibrated_ratio",
        "calibrated_fluorescence",
        "partial_pressure",
        "redox_potential",
        "membrane_potential",
    }
)
_ALLOWED_TARGETING_METHODS = frozenset(
    {
        "genetically_encoded_compartment_sensor",
        "validated_organelle_targeted_probe",
        "validated_subcellular_fractionation",
        "validated_spatial_mass_spectrometry",
        "validated_microelectrode_or_optode",
    }
)
_ALLOWED_TARGETING_VALIDATION = frozenset(
    {"directly_validated", "reported_not_independently_validated"}
)
_ALLOWED_CALIBRATION_STATUS = frozenset(
    {"same_assay_calibrated", "source_calibration_reported", "uncalibrated"}
)
_ALLOWED_ACCESS_STATES = frozenset({"development_open", "sealed_heldout"})


class EnergyRedoxTrajectoryError(ValueError):
    """Raised when energy/redox observations violate the intake contract."""


@dataclass(frozen=True)
class EnergyRedoxTrajectoryRecord:
    record_id: str
    donor_id: str
    split_role: str
    source_study_id: str
    source_locator: str
    raw_artifact_sha256: str
    predeclared_split_manifest_sha256: str
    data_access_state: str
    species: str
    biological_system: str
    culture_format: str
    health_state: str
    biological_replicate_id: str
    trajectory_id: str
    pool_id: str
    molecule: str
    compartment_id: str
    compartment_targeting_method: str
    compartment_targeting_validation: str
    assay: str
    sensor_or_probe: str
    sensor_calibration_status: str
    time_from_trajectory_start_s: float
    reported_value: float
    reported_unit: str
    measurement_kind: str
    reported_statistic: str
    uncertainty_value: float
    uncertainty_unit: str
    uncertainty_type: str
    sample_size: int
    extracellular_oxygen_value: float
    extracellular_oxygen_unit: str
    nutrient_context: str
    cell_viability_context: str
    position_or_region_context: str
    assay_temperature_c: float | None
    assay_ph: float | None
    perturbation_identity: str | None
    perturbation_value: float | None
    perturbation_unit: str | None
    baseline_definition: str | None
    censoring_or_missingness: str | None
    simultaneous_measurement_group_id: str | None
    intracellular_volume_value: float | None
    intracellular_volume_unit: str | None
    notes: str | None

    @property
    def donor_key(self) -> tuple[str, str]:
        return self.source_study_id, self.donor_id

    @property
    def trajectory_key(self) -> tuple[str, str, str, str]:
        return (
            self.source_study_id,
            self.donor_id,
            self.trajectory_id,
            self.pool_id,
        )


@dataclass(frozen=True)
class EnergyRedoxTrajectoryAssessment:
    trajectory_key: tuple[str, str, str, str]
    split_role: str
    raw_timepoint_count: int
    strictly_increasing_time: bool
    same_measurement_context: bool
    exact_pool_mapping: bool
    compartment_targeting_ready: bool
    same_assay_calibrated: bool
    structurally_complete: bool
    compartment_initialization_allowed: bool
    rate_fitting_allowed: bool
    automatic_state_coupling: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class EnergyRedoxTrajectoryDataset:
    version: str
    contract_id: str
    delivery_path: str
    artifact_sha256: str
    contract_sha256: str
    records: tuple[EnergyRedoxTrajectoryRecord, ...]


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


def _pool_registry() -> dict[str, tuple[str, str]]:
    contract = build_compartmental_energy_redox_contract()
    return {
        pool.id: (pool.molecule, pool.compartment_id)
        for pool in contract.pools
    }


def load_energy_redox_trajectory_contract(
    path: Path = CONTRACT_PATH,
) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise EnergyRedoxTrajectoryError("energy/redox contract must be one object")
    if payload.get("schema_version") != CONTRACT_SCHEMA_VERSION:
        raise EnergyRedoxTrajectoryError("unsupported energy/redox contract schema")
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
        raise EnergyRedoxTrajectoryError("energy/redox contract is malformed")
    required_ids = tuple(
        str(item.get("id", "")) for item in required if isinstance(item, dict)
    )
    conditional_ids = tuple(
        str(item.get("id", "")) for item in conditional if isinstance(item, dict)
    )
    if (
        len(required_ids) != 36
        or len(set(required_ids)) != 36
        or not all(required_ids)
        or len(conditional_ids) != 11
        or len(set(conditional_ids)) != 11
        or not all(conditional_ids)
    ):
        raise EnergyRedoxTrajectoryError("energy/redox field contract changed")
    if payload.get("canonical_null_token") != _NULL_TOKEN:
        raise EnergyRedoxTrajectoryError("energy/redox null policy changed")
    if set(payload.get("allowed_split_roles", ())) != _ALLOWED_SPLITS:
        raise EnergyRedoxTrajectoryError("energy/redox split roles changed")
    if (
        set(payload.get("allowed_measurement_kinds", ()))
        != _ALLOWED_MEASUREMENT_KINDS
        or set(payload.get("allowed_targeting_methods", ()))
        != _ALLOWED_TARGETING_METHODS
        or set(payload.get("allowed_targeting_validation", ()))
        != _ALLOWED_TARGETING_VALIDATION
        or set(payload.get("allowed_sensor_calibration_status", ()))
        != _ALLOWED_CALIBRATION_STATUS
        or set(payload.get("allowed_data_access_states", ()))
        != _ALLOWED_ACCESS_STATES
    ):
        raise EnergyRedoxTrajectoryError("energy/redox categorical contract changed")
    required_true = {
        "strictly_increasing_time_required",
        "exact_pool_molecule_compartment_match_required",
        "direct_compartment_targeting_validation_required",
        "same_assay_calibration_required",
        "donor_disjoint_validation_required",
        "independent_heldout_study_required",
        "predeclared_sealed_heldout_required",
    }
    required_false = {
        "automatic_unit_conversion",
        "automatic_compartment_initialization",
        "automatic_rate_fitting",
        "automatic_state_coupling",
        "automatic_predictive_activation",
    }
    if (
        gate.get("version") != TRAJECTORY_GATE_VERSION
        or gate.get("minimum_raw_timepoint_count") != 3
        or any(gate.get(key) is not True for key in required_true)
        or any(gate.get(key) is not False for key in required_false)
    ):
        raise EnergyRedoxTrajectoryError("energy/redox gate escaped fail-closed policy")
    if policy.get("manual_primary_source_review_required") is not True or any(
        policy.get(key) is not False
        for key in (
            "whole_tissue_value_may_be_allocated_to_compartments",
            "cross_species_transfer_allowed",
            "cell_line_transfer_to_healthy_phh_allowed",
            "uncalibrated_signal_is_absolute_concentration",
            "reported_mean_may_replace_raw_donor_trajectory",
            "missing_timepoint_means_zero",
            "renderer_signal_is_measurement",
            "automatic_parameter_activation",
            "automatic_cell_state_coupling",
        )
    ):
        raise EnergyRedoxTrajectoryError("energy/redox policy escaped fail-closed state")
    return payload


def _required_text(row: dict[str, str], field: str, row_number: int) -> str:
    value = row[field].strip()
    if not value or value.lower() == _NULL_TOKEN:
        raise EnergyRedoxTrajectoryError(f"row {row_number}: {field} is required")
    return value


def _optional_text(row: dict[str, str], field: str) -> str | None:
    value = row[field].strip()
    return None if not value or value.lower() == _NULL_TOKEN else value


def _number(
    row: dict[str, str],
    field: str,
    row_number: int,
    *,
    optional: bool = False,
    nonnegative: bool = False,
) -> float | None:
    token = row[field].strip()
    if optional and (not token or token.lower() == _NULL_TOKEN):
        return None
    if not _NUMBER_RE.fullmatch(token):
        raise EnergyRedoxTrajectoryError(
            f"row {row_number}: {field} must be one finite number"
        )
    value = float(token)
    if not math.isfinite(value):
        raise EnergyRedoxTrajectoryError(f"row {row_number}: {field} must be finite")
    if nonnegative and value < 0:
        raise EnergyRedoxTrajectoryError(
            f"row {row_number}: {field} must be non-negative"
        )
    return value


def _paired_optional_value_unit(
    row: dict[str, str],
    value_field: str,
    unit_field: str,
    row_number: int,
) -> tuple[float | None, str | None]:
    value = _number(row, value_field, row_number, optional=True)
    unit = _optional_text(row, unit_field)
    if (value is None) != (unit is None):
        raise EnergyRedoxTrajectoryError(
            f"row {row_number}: {value_field} and {unit_field} must be supplied together"
        )
    return value, unit


def _record(
    row: dict[str, str],
    row_number: int,
    pool_registry: dict[str, tuple[str, str]],
) -> EnergyRedoxTrajectoryRecord:
    split_role = _required_text(row, "split_role", row_number)
    if split_role not in _ALLOWED_SPLITS:
        raise EnergyRedoxTrajectoryError(
            f"row {row_number}: unsupported split_role {split_role!r}"
        )
    access_state = _required_text(row, "data_access_state", row_number)
    if access_state not in _ALLOWED_ACCESS_STATES:
        raise EnergyRedoxTrajectoryError(
            f"row {row_number}: unsupported data_access_state {access_state!r}"
        )
    if (
        split_role == "independent_heldout" and access_state != "sealed_heldout"
    ) or (
        split_role != "independent_heldout" and access_state != "development_open"
    ):
        raise EnergyRedoxTrajectoryError(
            f"row {row_number}: split role and data-access state are inconsistent"
        )
    for field in ("raw_artifact_sha256", "predeclared_split_manifest_sha256"):
        if not _SHA256_RE.fullmatch(_required_text(row, field, row_number)):
            raise EnergyRedoxTrajectoryError(
                f"row {row_number}: {field} must be a lowercase SHA-256 digest"
            )
    if _required_text(row, "species", row_number) != "Homo sapiens":
        raise EnergyRedoxTrajectoryError(
            f"row {row_number}: non-human record cannot enter PHH energy/redox intake"
        )
    biological_system = _required_text(row, "biological_system", row_number)
    if "primary_human_hepatocyte" not in biological_system.lower():
        raise EnergyRedoxTrajectoryError(
            f"row {row_number}: biological_system is outside primary human hepatocytes"
        )
    pool_id = _required_text(row, "pool_id", row_number)
    if pool_id not in pool_registry:
        raise EnergyRedoxTrajectoryError(
            f"row {row_number}: unknown compartmental energy/redox pool {pool_id!r}"
        )
    molecule = _required_text(row, "molecule", row_number)
    compartment_id = _required_text(row, "compartment_id", row_number)
    if (molecule, compartment_id) != pool_registry[pool_id]:
        raise EnergyRedoxTrajectoryError(
            f"row {row_number}: pool, molecule, and compartment do not match"
        )
    targeting_method = _required_text(
        row, "compartment_targeting_method", row_number
    )
    if targeting_method not in _ALLOWED_TARGETING_METHODS:
        raise EnergyRedoxTrajectoryError(
            f"row {row_number}: unsupported compartment-targeting method"
        )
    targeting_validation = _required_text(
        row, "compartment_targeting_validation", row_number
    )
    if targeting_validation not in _ALLOWED_TARGETING_VALIDATION:
        raise EnergyRedoxTrajectoryError(
            f"row {row_number}: unsupported targeting-validation status"
        )
    calibration_status = _required_text(
        row, "sensor_calibration_status", row_number
    )
    if calibration_status not in _ALLOWED_CALIBRATION_STATUS:
        raise EnergyRedoxTrajectoryError(
            f"row {row_number}: unsupported sensor-calibration status"
        )
    measurement_kind = _required_text(row, "measurement_kind", row_number)
    if measurement_kind not in _ALLOWED_MEASUREMENT_KINDS:
        raise EnergyRedoxTrajectoryError(
            f"row {row_number}: unsupported measurement_kind {measurement_kind!r}"
        )
    sample_size = _required_text(row, "sample_size", row_number)
    if not _INTEGER_RE.fullmatch(sample_size):
        raise EnergyRedoxTrajectoryError(
            f"row {row_number}: sample_size must be a non-negative integer"
        )
    perturbation_value, perturbation_unit = _paired_optional_value_unit(
        row, "perturbation_value", "perturbation_unit", row_number
    )
    perturbation_identity = _optional_text(row, "perturbation_identity")
    if perturbation_value is not None and perturbation_identity is None:
        raise EnergyRedoxTrajectoryError(
            f"row {row_number}: perturbation value requires an identity"
        )
    volume_value, volume_unit = _paired_optional_value_unit(
        row, "intracellular_volume_value", "intracellular_volume_unit", row_number
    )
    return EnergyRedoxTrajectoryRecord(
        record_id=_required_text(row, "record_id", row_number),
        donor_id=_required_text(row, "donor_id", row_number),
        split_role=split_role,
        source_study_id=_required_text(row, "source_study_id", row_number),
        source_locator=_required_text(row, "source_locator", row_number),
        raw_artifact_sha256=_required_text(
            row, "raw_artifact_sha256", row_number
        ),
        predeclared_split_manifest_sha256=_required_text(
            row, "predeclared_split_manifest_sha256", row_number
        ),
        data_access_state=access_state,
        species="Homo sapiens",
        biological_system=biological_system,
        culture_format=_required_text(row, "culture_format", row_number),
        health_state=_required_text(row, "health_state", row_number),
        biological_replicate_id=_required_text(
            row, "biological_replicate_id", row_number
        ),
        trajectory_id=_required_text(row, "trajectory_id", row_number),
        pool_id=pool_id,
        molecule=molecule,
        compartment_id=compartment_id,
        compartment_targeting_method=targeting_method,
        compartment_targeting_validation=targeting_validation,
        assay=_required_text(row, "assay", row_number),
        sensor_or_probe=_required_text(row, "sensor_or_probe", row_number),
        sensor_calibration_status=calibration_status,
        time_from_trajectory_start_s=float(
            _number(
                row,
                "time_from_trajectory_start_s",
                row_number,
                nonnegative=True,
            )
        ),
        reported_value=float(_number(row, "reported_value", row_number)),
        reported_unit=_required_text(row, "reported_unit", row_number),
        measurement_kind=measurement_kind,
        reported_statistic=_required_text(
            row, "reported_statistic", row_number
        ),
        uncertainty_value=float(
            _number(row, "uncertainty_value", row_number, nonnegative=True)
        ),
        uncertainty_unit=_required_text(row, "uncertainty_unit", row_number),
        uncertainty_type=_required_text(row, "uncertainty_type", row_number),
        sample_size=int(sample_size),
        extracellular_oxygen_value=float(
            _number(
                row,
                "extracellular_oxygen_value",
                row_number,
                nonnegative=True,
            )
        ),
        extracellular_oxygen_unit=_required_text(
            row, "extracellular_oxygen_unit", row_number
        ),
        nutrient_context=_required_text(row, "nutrient_context", row_number),
        cell_viability_context=_required_text(
            row, "cell_viability_context", row_number
        ),
        position_or_region_context=_required_text(
            row, "position_or_region_context", row_number
        ),
        assay_temperature_c=_number(
            row, "assay_temperature_c", row_number, optional=True
        ),
        assay_ph=_number(row, "assay_ph", row_number, optional=True),
        perturbation_identity=perturbation_identity,
        perturbation_value=perturbation_value,
        perturbation_unit=perturbation_unit,
        baseline_definition=_optional_text(row, "baseline_definition"),
        censoring_or_missingness=_optional_text(
            row, "censoring_or_missingness"
        ),
        simultaneous_measurement_group_id=_optional_text(
            row, "simultaneous_measurement_group_id"
        ),
        intracellular_volume_value=volume_value,
        intracellular_volume_unit=volume_unit,
        notes=_optional_text(row, "notes"),
    )


def load_energy_redox_trajectory_dataset(
    path: Path = DEFAULT_TRAJECTORY_PATH,
) -> EnergyRedoxTrajectoryDataset:
    contract = load_energy_redox_trajectory_contract()
    expected_fields = tuple(
        item["id"]
        for group in ("required_columns", "conditional_columns")
        for item in contract[group]
    )
    if not path.exists():
        raise EnergyRedoxTrajectoryError(
            f"energy/redox trajectory delivery not found: {_display_path(path)}"
        )
    pool_registry = _pool_registry()
    if len(pool_registry) != 38:
        raise EnergyRedoxTrajectoryError("compartmental energy/redox pool registry changed")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != expected_fields:
            raise EnergyRedoxTrajectoryError(
                "energy/redox CSV header must exactly match the versioned contract"
            )
        records = tuple(
            _record(row, index, pool_registry)
            for index, row in enumerate(reader, start=2)
        )
    if not records:
        raise EnergyRedoxTrajectoryError("energy/redox delivery contains no records")
    record_ids = [record.record_id for record in records]
    if len(set(record_ids)) != len(record_ids):
        raise EnergyRedoxTrajectoryError(
            "energy/redox record_id values must be unique"
        )
    donor_splits: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    study_splits: defaultdict[str, set[str]] = defaultdict(set)
    trajectory_times: defaultdict[tuple[str, str, str, str], set[float]] = defaultdict(set)
    split_manifests = {record.predeclared_split_manifest_sha256 for record in records}
    if len(split_manifests) != 1:
        raise EnergyRedoxTrajectoryError(
            "energy/redox records do not share one predeclared split manifest"
        )
    for record in records:
        donor_splits[record.donor_key].add(record.split_role)
        study_splits[record.source_study_id].add(record.split_role)
        if (
            record.time_from_trajectory_start_s
            in trajectory_times[record.trajectory_key]
        ):
            raise EnergyRedoxTrajectoryError(
                f"trajectory {record.trajectory_key!r} repeats a time point"
            )
        trajectory_times[record.trajectory_key].add(
            record.time_from_trajectory_start_s
        )
    leaking_donors = [key for key, splits in donor_splits.items() if len(splits) > 1]
    if leaking_donors:
        raise EnergyRedoxTrajectoryError(
            f"energy/redox donor crosses split roles: {leaking_donors!r}"
        )
    leaking_studies = [
        study
        for study, splits in study_splits.items()
        if "independent_heldout" in splits and len(splits) > 1
    ]
    if leaking_studies:
        raise EnergyRedoxTrajectoryError(
            f"independent-heldout study crosses development splits: {leaking_studies!r}"
        )
    return EnergyRedoxTrajectoryDataset(
        version=INTAKE_VERSION,
        contract_id=str(contract["contract_id"]),
        delivery_path=_display_path(path),
        artifact_sha256=_sha256(path),
        contract_sha256=_sha256(CONTRACT_PATH),
        records=records,
    )


def assess_energy_redox_trajectory(
    records: tuple[EnergyRedoxTrajectoryRecord, ...],
) -> EnergyRedoxTrajectoryAssessment:
    if not records:
        raise EnergyRedoxTrajectoryError("cannot assess an empty energy/redox trajectory")
    keys = {record.trajectory_key for record in records}
    if len(keys) != 1:
        raise EnergyRedoxTrajectoryError(
            "one energy/redox assessment cannot mix trajectory keys"
        )
    ordered = sorted(records, key=lambda record: record.time_from_trajectory_start_s)
    times = [record.time_from_trajectory_start_s for record in ordered]
    strictly_increasing = all(
        later > earlier for earlier, later in zip(times, times[1:], strict=False)
    )
    contexts = {
        (
            record.split_role,
            record.biological_replicate_id,
            record.pool_id,
            record.molecule,
            record.compartment_id,
            record.compartment_targeting_method,
            record.compartment_targeting_validation,
            record.assay,
            record.sensor_or_probe,
            record.sensor_calibration_status,
            record.reported_unit,
            record.measurement_kind,
            record.extracellular_oxygen_value,
            record.extracellular_oxygen_unit,
            record.nutrient_context,
            record.position_or_region_context,
        )
        for record in ordered
    }
    same_context = len(contexts) == 1
    exact_mapping = all(
        (record.molecule, record.compartment_id)
        == _pool_registry()[record.pool_id]
        for record in ordered
    )
    targeting_ready = all(
        record.compartment_targeting_validation == "directly_validated"
        for record in ordered
    )
    calibration_ready = all(
        record.sensor_calibration_status == "same_assay_calibrated"
        for record in ordered
    )
    blockers: list[str] = []
    if len(ordered) < 3:
        blockers.append("fewer than three raw time points")
    if not strictly_increasing:
        blockers.append("trajectory time is not strictly increasing")
    if not same_context:
        blockers.append("assay, pool, oxygen, nutrient, or spatial context changes within trajectory")
    if not exact_mapping:
        blockers.append("pool, molecule, and compartment mapping is inconsistent")
    if not targeting_ready:
        blockers.append("compartment targeting is not directly validated")
    if not calibration_ready:
        blockers.append("sensor is not calibrated in the same assay")
    structurally_complete = not blockers
    blockers.extend(
        (
            "manual primary-source and raw-artifact review is incomplete",
            "measurement operator and covariance model are not approved",
            "compartment initialization, rate fitting, and state coupling remain disabled",
        )
    )
    return EnergyRedoxTrajectoryAssessment(
        trajectory_key=next(iter(keys)),
        split_role=ordered[0].split_role,
        raw_timepoint_count=len(ordered),
        strictly_increasing_time=strictly_increasing,
        same_measurement_context=same_context,
        exact_pool_mapping=exact_mapping,
        compartment_targeting_ready=targeting_ready,
        same_assay_calibrated=calibration_ready,
        structurally_complete=structurally_complete,
        compartment_initialization_allowed=False,
        rate_fitting_allowed=False,
        automatic_state_coupling=False,
        blockers=tuple(blockers),
    )


def energy_redox_trajectory_intake_snapshot(
    path: Path = DEFAULT_TRAJECTORY_PATH,
) -> dict[str, object]:
    contract = load_energy_redox_trajectory_contract()
    pool_registry = _pool_registry()
    expected_header_count = len(contract["required_columns"]) + len(
        contract["conditional_columns"]
    )
    if not path.exists():
        return {
            "version": INTAKE_VERSION,
            "contract_id": contract["contract_id"],
            "status": "awaiting_donor_resolved_compartment_energy_redox_trajectories",
            "delivery_path": _display_path(path),
            "contract_sha256": _sha256(CONTRACT_PATH),
            "expected_header_count": expected_header_count,
            "registered_pool_count": len(pool_registry),
            "record_count": 0,
            "donor_count": 0,
            "trajectory_count": 0,
            "structurally_complete_trajectory_count": 0,
            "calibration_and_heldout_complete_pool_count": 0,
            "compartment_initialization_allowed_count": 0,
            "rate_fitting_allowed_count": 0,
            "automatic_state_coupling": False,
            "blockers": (
                "versioned donor-resolved compartment trajectory delivery is absent",
                "all 38 registered pools retain null initial values",
                "donor- and study-disjoint held-out trajectories are absent",
            ),
        }
    dataset = load_energy_redox_trajectory_dataset(path)
    grouped: defaultdict[
        tuple[str, str, str, str], list[EnergyRedoxTrajectoryRecord]
    ] = defaultdict(list)
    for record in dataset.records:
        grouped[record.trajectory_key].append(record)
    assessments = tuple(
        assess_energy_redox_trajectory(tuple(records))
        for records in grouped.values()
    )
    complete_roles_by_pool: defaultdict[str, set[str]] = defaultdict(set)
    for assessment in assessments:
        if assessment.structurally_complete:
            complete_roles_by_pool[assessment.trajectory_key[3]].add(
                assessment.split_role
            )
    complete_pools = {
        pool_id
        for pool_id, roles in complete_roles_by_pool.items()
        if "calibration" in roles and "independent_heldout" in roles
    }
    return {
        "version": INTAKE_VERSION,
        "contract_id": dataset.contract_id,
        "status": "energy_redox_trajectories_structurally_audited_not_authoritative",
        "delivery_path": dataset.delivery_path,
        "artifact_sha256": dataset.artifact_sha256,
        "contract_sha256": dataset.contract_sha256,
        "expected_header_count": expected_header_count,
        "registered_pool_count": len(pool_registry),
        "record_count": len(dataset.records),
        "donor_count": len({record.donor_key for record in dataset.records}),
        "trajectory_count": len(assessments),
        "record_count_by_split": dict(
            sorted(Counter(record.split_role for record in dataset.records).items())
        ),
        "structurally_complete_trajectory_count": sum(
            assessment.structurally_complete for assessment in assessments
        ),
        "calibration_and_heldout_complete_pool_count": len(complete_pools),
        "compartment_initialization_allowed_count": 0,
        "rate_fitting_allowed_count": 0,
        "automatic_state_coupling": False,
        "trajectory_assessments": tuple(to_plain(item) for item in assessments),
        "blockers": (
            "manual primary-source and raw-artifact review is incomplete",
            "measurement operators and covariance-aware acceptance rules are absent",
            "compartment initialization, rate fitting, and predictive coupling remain disabled",
        ),
    }
