"""Fail-closed intake for donor-resolved PHH mechanics calibration data.

This module accepts source-linked raw deformation/relaxation observations and
reported constitutive parameters without converting units, fitting laws, or
coupling them to the runtime membrane. A renderer deformation, aggregate liver
measurement, cell-line assay, or non-human experiment cannot satisfy the gate.
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


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "evidence_intake"
    / "phh_mechanics_calibration_contract.v1.json"
)
DEFAULT_DELIVERY_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "evidence_intake"
    / "incoming"
    / "phh_mechanics"
    / "latest"
    / "phh_mechanics_calibration.csv"
)
CONTRACT_SCHEMA_VERSION = "cell.phh-mechanics-calibration-contract.v1"
INTAKE_VERSION = "phh_mechanics_calibration_intake_v1"
TRAJECTORY_GATE_VERSION = "phh_mechanics_trajectory_gate_v1"

_NULL_TOKEN = "null"
_NUMBER_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
_INTEGER_RE = re.compile(r"^\d+$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_SPLIT_ROLES = frozenset(
    {"calibration", "internal_validation", "independent_heldout"}
)
_ALLOWED_RECORD_KINDS = frozenset({"raw_observation", "reported_parameter"})
_ALLOWED_ASSAY_TYPES = frozenset(
    {
        "atomic_force_microscopy",
        "micropipette_aspiration",
        "osmotic_challenge",
        "optical_tweezer",
        "microfluidic_deformation",
        "particle_tracking_microrheology",
        "pressure_relaxation",
        "other_mechanics",
    }
)
_ALLOWED_STAGES = frozenset(
    {"baseline", "loading", "hold", "relaxation", "washout", "derived_parameter"}
)
_REQUIRED_RAW_STAGES = frozenset({"baseline", "loading", "relaxation"})
_PARAMETER_QUANTITIES = frozenset(
    {
        "membrane_tension",
        "bending_modulus",
        "area_expansion_modulus",
        "cortical_elastic_modulus",
        "cortical_viscosity",
        "hydraulic_permeability",
        "poroelastic_diffusivity",
        "cytosol_apparent_viscosity",
    }
)


class PHHMechanicsCalibrationError(ValueError):
    """Raised when a mechanics delivery violates the versioned intake."""


@dataclass(frozen=True)
class PHHMechanicsRecord:
    record_id: str
    donor_id: str
    source_study_id: str
    source_locator: str
    split_role: str
    species: str
    biological_system: str
    tissue_health_state: str
    preparation_context: str
    culture_format: str
    liver_zone: str
    nutritional_state: str
    temperature_c: float
    medium_composition: str
    biological_replicate_id: str
    cell_id: str
    assay_id: str
    trajectory_id: str
    record_kind: str
    assay_type: str
    stage: str
    timepoint_index: int
    time_from_assay_start_s: float
    measured_quantity_id: str
    value: float
    unit: str
    measurement_method: str
    coordinate_frame: str
    membrane_domain: str
    uncertainty_value: float
    uncertainty_type: str
    raw_artifact_path: str
    raw_artifact_sha256: str
    cell_viability_context: str
    manual_primary_source_review_status: str
    stimulus_identity: str | None
    stimulus_value: float | None
    stimulus_unit: str | None
    loading_axis: str | None
    boundary_condition_description: str | None
    paired_mesh_record_id: str | None
    derived_from_trajectory_ids: str | None
    constitutive_model_equation: str | None
    fitting_report_path: str | None
    fitting_report_sha256: str | None
    protocol_report_path: str | None
    protocol_report_sha256: str | None
    censoring_or_missingness: str | None

    @property
    def donor_key(self) -> tuple[str, str]:
        return self.source_study_id, self.donor_id

    @property
    def trajectory_key(self) -> tuple[str, str, str, str]:
        return (
            self.source_study_id,
            self.donor_id,
            self.cell_id,
            self.trajectory_id,
        )


@dataclass(frozen=True)
class PHHMechanicsTrajectoryAssessment:
    trajectory_key: tuple[str, str, str, str]
    raw_timepoint_count: int
    stages: tuple[str, ...]
    strictly_increasing_time: bool
    same_trajectory_context: bool
    paired_mesh_present: bool
    boundary_conditions_present: bool
    structurally_complete: bool
    spatial_fsi_ready: bool
    quantitative_activation_allowed: bool
    automatic_parameter_fitting: bool
    automatic_runtime_coupling: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class PHHMechanicsDataset:
    version: str
    contract_id: str
    delivery_path: str
    artifact_sha256: str
    contract_sha256: str
    records: tuple[PHHMechanicsRecord, ...]


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


def _required_text(row: dict[str, str], field: str, row_number: int) -> str:
    value = row[field].strip()
    if not value or value.lower() == _NULL_TOKEN:
        raise PHHMechanicsCalibrationError(f"row {row_number}: {field} is required")
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
) -> float | None:
    token = row[field].strip()
    if optional and (not token or token.lower() == _NULL_TOKEN):
        return None
    if not _NUMBER_RE.fullmatch(token):
        raise PHHMechanicsCalibrationError(
            f"row {row_number}: {field} must be one finite number"
        )
    value = float(token)
    if not math.isfinite(value):
        raise PHHMechanicsCalibrationError(f"row {row_number}: {field} must be finite")
    return value


def _artifact_path(raw: str, *, label: str) -> Path:
    path = Path(raw)
    resolved = path.resolve() if path.is_absolute() else (REPOSITORY_ROOT / path).resolve()
    if not resolved.is_file():
        raise PHHMechanicsCalibrationError(f"{label} does not exist: {raw}")
    return resolved


def _verify_artifact(raw_path: str, expected_sha256: str, *, label: str) -> str:
    expected = expected_sha256.strip().lower()
    if not _SHA256_RE.fullmatch(expected):
        raise PHHMechanicsCalibrationError(f"{label} SHA-256 is malformed")
    path = _artifact_path(raw_path, label=label)
    if _sha256(path) != expected:
        raise PHHMechanicsCalibrationError(f"{label} SHA-256 mismatch")
    return _display_path(path)


def load_phh_mechanics_calibration_contract(
    path: Path = CONTRACT_PATH,
) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != CONTRACT_SCHEMA_VERSION:
        raise PHHMechanicsCalibrationError("unsupported PHH mechanics contract schema")
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
        raise PHHMechanicsCalibrationError("PHH mechanics contract is malformed")
    required_ids = tuple(
        str(item.get("id", "")) for item in required if isinstance(item, dict)
    )
    conditional_ids = tuple(
        str(item.get("id", "")) for item in conditional if isinstance(item, dict)
    )
    if (
        len(required_ids) != 35
        or len(set(required_ids)) != 35
        or len(conditional_ids) != 13
        or len(set(conditional_ids)) != 13
        or not all(required_ids + conditional_ids)
    ):
        raise PHHMechanicsCalibrationError("PHH mechanics field contract changed")
    if set(payload.get("allowed_split_roles", ())) != _ALLOWED_SPLIT_ROLES:
        raise PHHMechanicsCalibrationError("PHH mechanics split roles changed")
    if set(payload.get("allowed_record_kinds", ())) != _ALLOWED_RECORD_KINDS:
        raise PHHMechanicsCalibrationError("PHH mechanics record kinds changed")
    if set(payload.get("allowed_assay_types", ())) != _ALLOWED_ASSAY_TYPES:
        raise PHHMechanicsCalibrationError("PHH mechanics assay types changed")
    if set(payload.get("allowed_stages", ())) != _ALLOWED_STAGES:
        raise PHHMechanicsCalibrationError("PHH mechanics stages changed")
    quantities = payload.get("measured_quantities")
    if not isinstance(quantities, dict) or set(quantities) != {
        "cell_volume",
        "surface_area",
        "normal_displacement",
        "indentation_depth",
        "applied_force",
        "pressure_difference",
        "aspiration_length",
        "membrane_tension",
        "bending_modulus",
        "area_expansion_modulus",
        "cortical_elastic_modulus",
        "cortical_viscosity",
        "hydraulic_permeability",
        "poroelastic_diffusivity",
        "cytosol_apparent_viscosity",
    }:
        raise PHHMechanicsCalibrationError("PHH mechanics quantity registry changed")
    if payload.get("canonical_null_token") != _NULL_TOKEN:
        raise PHHMechanicsCalibrationError("PHH mechanics null policy changed")
    if (
        gate.get("version") != TRAJECTORY_GATE_VERSION
        or gate.get("minimum_raw_timepoint_count") != 3
        or set(gate.get("required_stages", ())) != _REQUIRED_RAW_STAGES
    ):
        raise PHHMechanicsCalibrationError("PHH mechanics trajectory gate changed")
    required_true = {
        "same_donor_required",
        "same_cell_required",
        "same_assay_required",
        "same_quantity_required",
        "same_coordinate_frame_required",
        "strictly_increasing_time_required",
        "raw_artifact_checksum_required",
        "paired_mesh_required_for_spatial_fsi",
        "boundary_conditions_required_for_spatial_fsi",
        "donor_disjoint_validation_required",
        "independent_heldout_study_required",
        "frozen_constitutive_model_before_heldout_access_required",
    }
    required_false = {
        "automatic_parameter_fitting",
        "automatic_unit_conversion",
        "automatic_proxy_substitution",
        "automatic_runtime_activation",
        "automatic_membrane_feedback",
    }
    if any(gate.get(key) is not True for key in required_true) or any(
        gate.get(key) is not False for key in required_false
    ):
        raise PHHMechanicsCalibrationError("PHH mechanics gate escaped fail-closed policy")
    policy_false = {
        "aggregate_tissue_value_may_initialize_single_cell",
        "cell_line_mechanics_may_initialize_healthy_phh",
        "nonhuman_mechanics_may_initialize_healthy_phh",
        "renderer_deformation_is_measurement",
        "reported_parameter_may_replace_raw_validation_trajectory",
        "mesh_implies_mechanics",
        "one_assay_identifies_all_constitutive_parameters",
        "interpolation_for_heldout_validation",
        "automatic_parameter_activation",
        "automatic_runtime_coupling",
    }
    if policy.get("manual_primary_source_review_required") is not True or any(
        policy.get(key) is not False for key in policy_false
    ):
        raise PHHMechanicsCalibrationError("PHH mechanics policy escaped fail-closed state")
    return payload


def _record(
    row: dict[str, str],
    row_number: int,
    contract: dict[str, Any],
) -> PHHMechanicsRecord:
    split_role = _required_text(row, "split_role", row_number)
    record_kind = _required_text(row, "record_kind", row_number)
    assay_type = _required_text(row, "assay_type", row_number)
    stage = _required_text(row, "stage", row_number)
    if split_role not in _ALLOWED_SPLIT_ROLES:
        raise PHHMechanicsCalibrationError(
            f"row {row_number}: unsupported split_role {split_role!r}"
        )
    if record_kind not in _ALLOWED_RECORD_KINDS:
        raise PHHMechanicsCalibrationError(
            f"row {row_number}: unsupported record_kind {record_kind!r}"
        )
    if assay_type not in _ALLOWED_ASSAY_TYPES:
        raise PHHMechanicsCalibrationError(
            f"row {row_number}: unsupported assay_type {assay_type!r}"
        )
    if stage not in _ALLOWED_STAGES:
        raise PHHMechanicsCalibrationError(
            f"row {row_number}: unsupported stage {stage!r}"
        )
    if _required_text(row, "species", row_number) != "Homo sapiens":
        raise PHHMechanicsCalibrationError(
            f"row {row_number}: non-human mechanics cannot enter the PHH set"
        )
    biological_system = _required_text(row, "biological_system", row_number)
    if "primary_human_hepatocyte" not in biological_system.lower():
        raise PHHMechanicsCalibrationError(
            f"row {row_number}: biological_system is outside primary human hepatocytes"
        )
    health = _required_text(row, "tissue_health_state", row_number).lower()
    if "healthy" not in health and "non_diseased" not in health:
        raise PHHMechanicsCalibrationError(
            f"row {row_number}: healthy/non-diseased donor context is required"
        )
    review = _required_text(row, "manual_primary_source_review_status", row_number)
    if review.lower() != "pass":
        raise PHHMechanicsCalibrationError(
            f"row {row_number}: manual primary-source review must be pass"
        )
    timepoint_token = _required_text(row, "timepoint_index", row_number)
    if not _INTEGER_RE.fullmatch(timepoint_token):
        raise PHHMechanicsCalibrationError(
            f"row {row_number}: timepoint_index must be a non-negative integer"
        )
    temperature = _number(row, "temperature_c", row_number)
    time_s = _number(row, "time_from_assay_start_s", row_number)
    value = _number(row, "value", row_number)
    uncertainty = _number(row, "uncertainty_value", row_number)
    if temperature is None or not 0 < temperature < 100:
        raise PHHMechanicsCalibrationError(
            f"row {row_number}: temperature_c is outside a physical assay range"
        )
    if time_s is None or time_s < 0:
        raise PHHMechanicsCalibrationError(
            f"row {row_number}: time_from_assay_start_s must be non-negative"
        )
    if value is None:
        raise PHHMechanicsCalibrationError(f"row {row_number}: value is required")
    if uncertainty is None or uncertainty < 0:
        raise PHHMechanicsCalibrationError(
            f"row {row_number}: uncertainty_value must be non-negative"
        )
    quantity = _required_text(row, "measured_quantity_id", row_number)
    quantities = contract["measured_quantities"]
    if quantity not in quantities:
        raise PHHMechanicsCalibrationError(
            f"row {row_number}: unsupported measured_quantity_id {quantity!r}"
        )
    unit = _required_text(row, "unit", row_number)
    if unit != quantities[quantity]:
        raise PHHMechanicsCalibrationError(
            f"row {row_number}: {quantity} must use canonical unit {quantities[quantity]!r}"
        )
    stimulus_identity = _optional_text(row, "stimulus_identity")
    stimulus_value = _number(row, "stimulus_value", row_number, optional=True)
    stimulus_unit = _optional_text(row, "stimulus_unit")
    if (stimulus_value is None) != (stimulus_unit is None):
        raise PHHMechanicsCalibrationError(
            f"row {row_number}: stimulus_value and stimulus_unit must be paired"
        )
    if stimulus_value is not None and stimulus_identity is None:
        raise PHHMechanicsCalibrationError(
            f"row {row_number}: stimulus_identity is required with a stimulus value"
        )
    raw_path = _required_text(row, "raw_artifact_path", row_number)
    raw_sha = _required_text(row, "raw_artifact_sha256", row_number).lower()
    raw_path = _verify_artifact(raw_path, raw_sha, label=f"row {row_number} raw artifact")

    paired_mesh = _optional_text(row, "paired_mesh_record_id")
    boundary = _optional_text(row, "boundary_condition_description")
    derived_ids = _optional_text(row, "derived_from_trajectory_ids")
    equation = _optional_text(row, "constitutive_model_equation")
    fitting_path = _optional_text(row, "fitting_report_path")
    fitting_sha = _optional_text(row, "fitting_report_sha256")
    protocol_path = _optional_text(row, "protocol_report_path")
    protocol_sha = _optional_text(row, "protocol_report_sha256")
    if (fitting_path is None) != (fitting_sha is None):
        raise PHHMechanicsCalibrationError(
            f"row {row_number}: fitting report path and checksum must be paired"
        )
    if fitting_path is not None and fitting_sha is not None:
        fitting_path = _verify_artifact(
            fitting_path, fitting_sha, label=f"row {row_number} fitting report"
        )
    if (protocol_path is None) != (protocol_sha is None):
        raise PHHMechanicsCalibrationError(
            f"row {row_number}: protocol report path and checksum must be paired"
        )
    if protocol_path is not None and protocol_sha is not None:
        protocol_path = _verify_artifact(
            protocol_path, protocol_sha, label=f"row {row_number} protocol report"
        )
    if record_kind == "raw_observation":
        if stage == "derived_parameter":
            raise PHHMechanicsCalibrationError(
                f"row {row_number}: raw observations cannot use derived_parameter stage"
            )
        if any((derived_ids, equation, fitting_path, fitting_sha)):
            raise PHHMechanicsCalibrationError(
                f"row {row_number}: raw observations cannot carry fitted-parameter fields"
            )
    else:
        if stage != "derived_parameter" or quantity not in _PARAMETER_QUANTITIES:
            raise PHHMechanicsCalibrationError(
                f"row {row_number}: reported parameters require a constitutive quantity and derived_parameter stage"
            )
        if not all((derived_ids, equation, fitting_path, fitting_sha)):
            raise PHHMechanicsCalibrationError(
                f"row {row_number}: reported parameter provenance is incomplete"
            )

    return PHHMechanicsRecord(
        record_id=_required_text(row, "record_id", row_number),
        donor_id=_required_text(row, "donor_id", row_number),
        source_study_id=_required_text(row, "source_study_id", row_number),
        source_locator=_required_text(row, "source_locator", row_number),
        split_role=split_role,
        species="Homo sapiens",
        biological_system=biological_system,
        tissue_health_state=_required_text(row, "tissue_health_state", row_number),
        preparation_context=_required_text(row, "preparation_context", row_number),
        culture_format=_required_text(row, "culture_format", row_number),
        liver_zone=_required_text(row, "liver_zone", row_number),
        nutritional_state=_required_text(row, "nutritional_state", row_number),
        temperature_c=temperature,
        medium_composition=_required_text(row, "medium_composition", row_number),
        biological_replicate_id=_required_text(
            row, "biological_replicate_id", row_number
        ),
        cell_id=_required_text(row, "cell_id", row_number),
        assay_id=_required_text(row, "assay_id", row_number),
        trajectory_id=_required_text(row, "trajectory_id", row_number),
        record_kind=record_kind,
        assay_type=assay_type,
        stage=stage,
        timepoint_index=int(timepoint_token),
        time_from_assay_start_s=time_s,
        measured_quantity_id=quantity,
        value=value,
        unit=unit,
        measurement_method=_required_text(row, "measurement_method", row_number),
        coordinate_frame=_required_text(row, "coordinate_frame", row_number),
        membrane_domain=_required_text(row, "membrane_domain", row_number),
        uncertainty_value=uncertainty,
        uncertainty_type=_required_text(row, "uncertainty_type", row_number),
        raw_artifact_path=raw_path,
        raw_artifact_sha256=raw_sha,
        cell_viability_context=_required_text(
            row, "cell_viability_context", row_number
        ),
        manual_primary_source_review_status=review,
        stimulus_identity=stimulus_identity,
        stimulus_value=stimulus_value,
        stimulus_unit=stimulus_unit,
        loading_axis=_optional_text(row, "loading_axis"),
        boundary_condition_description=boundary,
        paired_mesh_record_id=paired_mesh,
        derived_from_trajectory_ids=derived_ids,
        constitutive_model_equation=equation,
        fitting_report_path=fitting_path,
        fitting_report_sha256=fitting_sha,
        protocol_report_path=protocol_path,
        protocol_report_sha256=protocol_sha,
        censoring_or_missingness=_optional_text(row, "censoring_or_missingness"),
    )


def load_phh_mechanics_calibration_dataset(
    path: Path = DEFAULT_DELIVERY_PATH,
) -> PHHMechanicsDataset:
    contract = load_phh_mechanics_calibration_contract()
    expected_fields = tuple(
        item["id"]
        for group in ("required_columns", "conditional_columns")
        for item in contract[group]
    )
    if not path.exists():
        raise PHHMechanicsCalibrationError(
            f"PHH mechanics delivery not found: {_display_path(path)}"
        )
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != expected_fields:
            raise PHHMechanicsCalibrationError(
                "PHH mechanics CSV header must exactly match the versioned contract"
            )
        records = tuple(
            _record(row, row_number, contract)
            for row_number, row in enumerate(reader, start=2)
        )
    if not records:
        raise PHHMechanicsCalibrationError("PHH mechanics delivery contains no records")
    record_ids = [record.record_id for record in records]
    if len(set(record_ids)) != len(record_ids):
        raise PHHMechanicsCalibrationError("PHH mechanics record_id values must be unique")

    donor_splits: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    study_splits: defaultdict[str, set[str]] = defaultdict(set)
    raw_timepoints: defaultdict[tuple[str, str, str, str], set[int]] = defaultdict(set)
    for record in records:
        donor_splits[record.donor_key].add(record.split_role)
        study_splits[record.source_study_id].add(record.split_role)
        if record.record_kind == "raw_observation":
            if record.timepoint_index in raw_timepoints[record.trajectory_key]:
                raise PHHMechanicsCalibrationError(
                    f"trajectory {record.trajectory_key!r} repeats timepoint_index "
                    f"{record.timepoint_index}"
                )
            raw_timepoints[record.trajectory_key].add(record.timepoint_index)
    leaking_donors = [key for key, splits in donor_splits.items() if len(splits) > 1]
    if leaking_donors:
        raise PHHMechanicsCalibrationError(
            f"PHH mechanics donor crosses split roles: {leaking_donors!r}"
        )
    leaking_studies = [
        study
        for study, splits in study_splits.items()
        if "independent_heldout" in splits and len(splits) > 1
    ]
    if leaking_studies:
        raise PHHMechanicsCalibrationError(
            f"independent-heldout study crosses development splits: {leaking_studies!r}"
        )
    return PHHMechanicsDataset(
        version=INTAKE_VERSION,
        contract_id=str(contract["contract_id"]),
        delivery_path=_display_path(path),
        artifact_sha256=_sha256(path),
        contract_sha256=_sha256(CONTRACT_PATH),
        records=records,
    )


def assess_phh_mechanics_trajectory(
    records: tuple[PHHMechanicsRecord, ...],
) -> PHHMechanicsTrajectoryAssessment:
    raw = tuple(record for record in records if record.record_kind == "raw_observation")
    if not raw:
        raise PHHMechanicsCalibrationError(
            "cannot assess a mechanics trajectory without raw observations"
        )
    keys = {record.trajectory_key for record in raw}
    if len(keys) != 1:
        raise PHHMechanicsCalibrationError(
            "one mechanics assessment cannot mix trajectory identifiers"
        )
    ordered = sorted(raw, key=lambda record: record.timepoint_index)
    times = [record.time_from_assay_start_s for record in ordered]
    strictly_increasing = all(
        later > earlier for earlier, later in zip(times, times[1:], strict=False)
    )
    contexts = {
        (
            record.donor_key,
            record.biological_replicate_id,
            record.cell_id,
            record.assay_id,
            record.assay_type,
            record.measured_quantity_id,
            record.unit,
            record.coordinate_frame,
            record.membrane_domain,
            record.temperature_c,
            record.medium_composition,
            record.measurement_method,
        )
        for record in ordered
    }
    same_context = len(contexts) == 1
    stages = frozenset(record.stage for record in ordered)
    paired_mesh_present = all(record.paired_mesh_record_id for record in ordered)
    boundary_conditions_present = all(
        record.boundary_condition_description for record in ordered
    )
    blockers: list[str] = []
    if len(ordered) < 3:
        blockers.append("fewer than three raw mechanics timepoints")
    if not _REQUIRED_RAW_STAGES <= stages:
        blockers.append("baseline, loading and relaxation stages are incomplete")
    if not strictly_increasing:
        blockers.append("mechanics trajectory time is not strictly increasing")
    if not same_context:
        blockers.append("cell, assay, quantity, frame or acquisition context changes")
    structurally_complete = not blockers
    spatial_fsi_ready = (
        structurally_complete and paired_mesh_present and boundary_conditions_present
    )
    if not paired_mesh_present:
        blockers.append("same-cell PHH mesh record is absent")
    if not boundary_conditions_present:
        blockers.append("spatial boundary-condition description is absent")
    blockers.extend(
        (
            "frozen constitutive-law fit has not passed independent review",
            "donor- and study-disjoint held-out mechanics validation is absent",
            "runtime membrane feedback remains disabled",
        )
    )
    return PHHMechanicsTrajectoryAssessment(
        trajectory_key=next(iter(keys)),
        raw_timepoint_count=len(ordered),
        stages=tuple(sorted(stages)),
        strictly_increasing_time=strictly_increasing,
        same_trajectory_context=same_context,
        paired_mesh_present=paired_mesh_present,
        boundary_conditions_present=boundary_conditions_present,
        structurally_complete=structurally_complete,
        spatial_fsi_ready=spatial_fsi_ready,
        quantitative_activation_allowed=False,
        automatic_parameter_fitting=False,
        automatic_runtime_coupling=False,
        blockers=tuple(blockers),
    )


def phh_mechanics_calibration_intake_snapshot(
    path: Path = DEFAULT_DELIVERY_PATH,
) -> dict[str, object]:
    contract = load_phh_mechanics_calibration_contract()
    expected_header_count = len(contract["required_columns"]) + len(
        contract["conditional_columns"]
    )
    if not path.exists():
        return {
            "version": INTAKE_VERSION,
            "contract_id": contract["contract_id"],
            "status": "awaiting_donor_resolved_phh_mechanics_delivery",
            "delivery_path": _display_path(path),
            "contract_sha256": _sha256(CONTRACT_PATH),
            "expected_header_count": expected_header_count,
            "target_quantity_count": len(contract["measured_quantities"]),
            "record_count": 0,
            "donor_count": 0,
            "raw_trajectory_count": 0,
            "reported_parameter_record_count": 0,
            "structurally_complete_trajectory_count": 0,
            "spatial_fsi_ready_trajectory_count": 0,
            "independent_heldout_trajectory_count": 0,
            "quantitatively_authorized_parameter_count": 0,
            "mechanics_coupling_allowed": False,
            "automatic_parameter_fitting": False,
            "automatic_unit_conversion": False,
            "automatic_runtime_coupling": False,
            "blockers": (
                "versioned donor-resolved mechanics delivery is absent",
                "same-cell meshes and spatial boundary conditions are absent",
                "frozen constitutive-law fit and independent held-out validation are absent",
            ),
        }
    dataset = load_phh_mechanics_calibration_dataset(path)
    raw_groups: defaultdict[
        tuple[str, str, str, str], list[PHHMechanicsRecord]
    ] = defaultdict(list)
    for record in dataset.records:
        if record.record_kind == "raw_observation":
            raw_groups[record.trajectory_key].append(record)
    assessments = tuple(
        assess_phh_mechanics_trajectory(tuple(records))
        for records in raw_groups.values()
    )
    heldout_keys = {
        record.trajectory_key
        for record in dataset.records
        if record.record_kind == "raw_observation"
        and record.split_role == "independent_heldout"
    }
    return {
        "version": INTAKE_VERSION,
        "contract_id": dataset.contract_id,
        "status": "mechanics_delivery_structurally_audited_not_authoritative",
        "delivery_path": dataset.delivery_path,
        "artifact_sha256": dataset.artifact_sha256,
        "contract_sha256": dataset.contract_sha256,
        "expected_header_count": expected_header_count,
        "target_quantity_count": len(contract["measured_quantities"]),
        "record_count": len(dataset.records),
        "donor_count": len({record.donor_key for record in dataset.records}),
        "raw_trajectory_count": len(assessments),
        "reported_parameter_record_count": sum(
            record.record_kind == "reported_parameter" for record in dataset.records
        ),
        "record_count_by_split": dict(
            sorted(Counter(record.split_role for record in dataset.records).items())
        ),
        "structurally_complete_trajectory_count": sum(
            assessment.structurally_complete for assessment in assessments
        ),
        "spatial_fsi_ready_trajectory_count": sum(
            assessment.spatial_fsi_ready for assessment in assessments
        ),
        "independent_heldout_trajectory_count": len(heldout_keys),
        "quantitatively_authorized_parameter_count": 0,
        "mechanics_coupling_allowed": False,
        "automatic_parameter_fitting": False,
        "automatic_unit_conversion": False,
        "automatic_runtime_coupling": False,
        "trajectory_assessments": tuple(to_plain(assessment) for assessment in assessments),
        "blockers": (
            "frozen constitutive-law fit has not passed independent review",
            "donor- and study-disjoint held-out evaluation has not authorized a law",
            "runtime membrane feedback remains disabled",
        ),
    }


def validate_phh_mechanics_calibration_intake_snapshot(
    payload: dict[str, object],
) -> None:
    if payload.get("version") != INTAKE_VERSION:
        raise ValueError("unexpected PHH mechanics intake version")
    if payload.get("expected_header_count") != 48:
        raise ValueError("PHH mechanics intake header count changed")
    if payload.get("target_quantity_count") != 15:
        raise ValueError("PHH mechanics quantity registry changed")
    if any(
        payload.get(key) is not False
        for key in (
            "mechanics_coupling_allowed",
            "automatic_parameter_fitting",
            "automatic_unit_conversion",
            "automatic_runtime_coupling",
        )
    ):
        raise ValueError("PHH mechanics intake escaped fail-closed state")
    if int(payload.get("quantitatively_authorized_parameter_count", -1)) != 0:
        raise ValueError("PHH mechanics parameters activated without scientific review")
