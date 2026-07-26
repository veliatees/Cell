"""Fail-closed intake for route-resolved active-cargo trajectories in PHH.

The contract accepts raw donor-resolved 3D time-position observations and
observed trafficking events. It never promotes a reported mean speed, a cell
line, a non-human preparation, or renderer motion into healthy-PHH motor
kinetics. Structural completeness prepares a future frozen route evaluation;
it does not fit or activate a transport law.
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
    / "phh_active_cargo_trajectory_contract.v1.json"
)
DEFAULT_TRAJECTORY_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "evidence_intake"
    / "incoming"
    / "phh_active_cargo"
    / "latest"
    / "phh_active_cargo_trajectories.csv"
)
CONTRACT_SCHEMA_VERSION = "cell.phh-active-cargo-trajectory-contract.v1"
INTAKE_VERSION = "phh_active_cargo_trajectory_intake_v1"
ROUTE_GATE_VERSION = "phh_active_cargo_route_gate_v1"

_NULL_TOKEN = "null"
_NUMBER_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
_INTEGER_RE = re.compile(r"^\d+$")
_ALLOWED_SPLIT_ROLES = frozenset(
    {"calibration", "internal_validation", "independent_heldout"}
)
_ALLOWED_EVENT_LABELS = frozenset(
    {
        "departure",
        "in_transit",
        "pause",
        "reversal",
        "arrival",
        "fusion",
        "fission",
        "lost_from_track",
    }
)
_ALLOWED_TRACK_SYSTEMS = frozenset(
    {"microtubule", "actin", "mixed_or_unresolved"}
)
_REQUIRED_EVENTS = frozenset({"departure", "in_transit"})
_TERMINAL_EVENTS = frozenset({"arrival", "fusion", "fission"})


class ActiveCargoTrajectoryError(ValueError):
    """Raised when active-cargo evidence violates the intake contract."""


@dataclass(frozen=True)
class ActiveCargoTrajectoryRecord:
    record_id: str
    donor_id: str
    split_role: str
    source_study_id: str
    source_locator: str
    species: str
    biological_system: str
    culture_format: str
    trajectory_id: str
    biological_replicate_id: str
    cargo_identity: str
    cargo_labeling_method: str
    origin_compartment: str
    destination_compartment: str
    cytoskeletal_track: str
    motor_identity: str
    frame_index: int
    time_from_trajectory_start_s: float
    position_x_um: float
    position_y_um: float
    position_z_um: float
    position_reference_frame: str
    localization_uncertainty_um: float
    trajectory_sampling_interval_s: float
    event_label: str
    assay: str
    cell_viability_context: str
    track_polarity: str | None
    atp_value: float | None
    atp_unit: str | None
    atp_assay: str | None
    motor_occupancy_value: float | None
    motor_occupancy_unit: str | None
    perturbation_identity: str | None
    perturbation_value: float | None
    perturbation_unit: str | None
    fusion_or_fission_partner_id: str | None
    uncertainty_type: str | None
    censoring_flag: str | None

    @property
    def donor_key(self) -> tuple[str, str]:
        return self.source_study_id, self.donor_id

    @property
    def route_key(self) -> tuple[str, str, str]:
        return self.source_study_id, self.donor_id, self.trajectory_id


@dataclass(frozen=True)
class ActiveCargoRouteAssessment:
    route_key: tuple[str, str, str]
    raw_position_count: int
    event_labels: tuple[str, ...]
    strictly_increasing_time: bool
    same_route_context: bool
    structurally_complete: bool
    quantitative_activation_allowed: bool
    automatic_velocity_inference: bool
    automatic_motor_parameter_fitting: bool
    automatic_route_activation: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class ActiveCargoTrajectoryDataset:
    version: str
    contract_id: str
    delivery_path: str
    artifact_sha256: str
    contract_sha256: str
    records: tuple[ActiveCargoTrajectoryRecord, ...]


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


def load_active_cargo_trajectory_contract(
    path: Path = CONTRACT_PATH,
) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ActiveCargoTrajectoryError("active-cargo contract must be one object")
    if payload.get("schema_version") != CONTRACT_SCHEMA_VERSION:
        raise ActiveCargoTrajectoryError("unsupported active-cargo contract schema")
    required = payload.get("required_columns")
    conditional = payload.get("conditional_columns")
    gate = payload.get("route_gate")
    policy = payload.get("policy")
    if not all(
        (
            isinstance(required, list),
            isinstance(conditional, list),
            isinstance(gate, dict),
            isinstance(policy, dict),
        )
    ):
        raise ActiveCargoTrajectoryError("active-cargo contract is malformed")
    required_ids = tuple(
        str(item.get("id", "")) for item in required if isinstance(item, dict)
    )
    conditional_ids = tuple(
        str(item.get("id", "")) for item in conditional if isinstance(item, dict)
    )
    if (
        len(required_ids) != 27
        or len(set(required_ids)) != 27
        or not all(required_ids)
        or len(conditional_ids) != 12
        or len(set(conditional_ids)) != 12
        or not all(conditional_ids)
    ):
        raise ActiveCargoTrajectoryError("active-cargo field contract changed")
    if set(payload.get("allowed_split_roles", ())) != _ALLOWED_SPLIT_ROLES:
        raise ActiveCargoTrajectoryError("active-cargo split roles changed")
    if set(payload.get("allowed_event_labels", ())) != _ALLOWED_EVENT_LABELS:
        raise ActiveCargoTrajectoryError("active-cargo event labels changed")
    if set(payload.get("allowed_track_systems", ())) != _ALLOWED_TRACK_SYSTEMS:
        raise ActiveCargoTrajectoryError("active-cargo track systems changed")
    if payload.get("canonical_null_token") != _NULL_TOKEN:
        raise ActiveCargoTrajectoryError("active-cargo null policy changed")
    if (
        gate.get("version") != ROUTE_GATE_VERSION
        or gate.get("minimum_raw_position_count") != 3
        or set(gate.get("required_event_labels", ())) != _REQUIRED_EVENTS
        or set(gate.get("required_terminal_event_any_of", ())) != _TERMINAL_EVENTS
    ):
        raise ActiveCargoTrajectoryError("active-cargo route gate changed")
    required_true = {
        "same_donor_required",
        "same_trajectory_required",
        "same_cargo_label_required",
        "same_coordinate_frame_required",
        "strictly_increasing_time_required",
        "donor_disjoint_validation_required",
        "independent_heldout_study_required",
        "frozen_route_model_before_heldout_access_required",
    }
    required_false = {
        "automatic_velocity_inference",
        "automatic_motor_parameter_fitting",
        "automatic_route_activation",
        "automatic_cell_state_coupling",
    }
    if any(gate.get(key) is not True for key in required_true) or any(
        gate.get(key) is not False for key in required_false
    ):
        raise ActiveCargoTrajectoryError("active-cargo route gate escaped fail-closed policy")
    policy_false = {
        "two_dimensional_tracks_may_enter_three_dimensional_intake",
        "reported_mean_speed_may_replace_raw_positions",
        "cross_species_rate_transfer_allowed",
        "cell_line_rate_transfer_to_healthy_phh_allowed",
        "interpolation_for_validation",
        "missing_event_means_no_event",
        "visual_route_geometry_is_measurement",
        "automatic_parameter_activation",
        "automatic_cell_state_coupling",
    }
    if policy.get("manual_primary_source_review_required") is not True or any(
        policy.get(key) is not False for key in policy_false
    ):
        raise ActiveCargoTrajectoryError("active-cargo policy escaped fail-closed state")
    return payload


def _required_text(row: dict[str, str], field: str, row_number: int) -> str:
    value = row[field].strip()
    if not value or value.lower() == _NULL_TOKEN:
        raise ActiveCargoTrajectoryError(f"row {row_number}: {field} is required")
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
        raise ActiveCargoTrajectoryError(
            f"row {row_number}: {field} must be one finite number"
        )
    value = float(token)
    if not math.isfinite(value):
        raise ActiveCargoTrajectoryError(f"row {row_number}: {field} must be finite")
    return value


def _nonnegative_number(
    row: dict[str, str],
    field: str,
    row_number: int,
    *,
    optional: bool = False,
) -> float | None:
    value = _number(row, field, row_number, optional=optional)
    if value is not None and value < 0:
        raise ActiveCargoTrajectoryError(
            f"row {row_number}: {field} must be non-negative"
        )
    return value


def _paired_value_and_unit(
    row: dict[str, str],
    value_field: str,
    unit_field: str,
    row_number: int,
) -> tuple[float | None, str | None]:
    value = _number(row, value_field, row_number, optional=True)
    unit = _optional_text(row, unit_field)
    if (value is None) != (unit is None):
        raise ActiveCargoTrajectoryError(
            f"row {row_number}: {value_field} and {unit_field} must be supplied together"
        )
    return value, unit


def _record(row: dict[str, str], row_number: int) -> ActiveCargoTrajectoryRecord:
    split_role = _required_text(row, "split_role", row_number)
    if split_role not in _ALLOWED_SPLIT_ROLES:
        raise ActiveCargoTrajectoryError(
            f"row {row_number}: unsupported split_role {split_role!r}"
        )
    if _required_text(row, "species", row_number) != "Homo sapiens":
        raise ActiveCargoTrajectoryError(
            f"row {row_number}: non-human record cannot enter the PHH cargo set"
        )
    biological_system = _required_text(row, "biological_system", row_number)
    if "primary_human_hepatocyte" not in biological_system.lower():
        raise ActiveCargoTrajectoryError(
            f"row {row_number}: biological_system is outside primary human hepatocytes"
        )
    track = _required_text(row, "cytoskeletal_track", row_number)
    if track not in _ALLOWED_TRACK_SYSTEMS:
        raise ActiveCargoTrajectoryError(
            f"row {row_number}: unsupported cytoskeletal_track {track!r}"
        )
    event = _required_text(row, "event_label", row_number)
    if event not in _ALLOWED_EVENT_LABELS:
        raise ActiveCargoTrajectoryError(
            f"row {row_number}: unsupported event_label {event!r}"
        )
    frame_token = _required_text(row, "frame_index", row_number)
    if not _INTEGER_RE.fullmatch(frame_token):
        raise ActiveCargoTrajectoryError(
            f"row {row_number}: frame_index must be a non-negative integer"
        )
    sampling_interval = _nonnegative_number(
        row, "trajectory_sampling_interval_s", row_number
    )
    if sampling_interval is None or sampling_interval <= 0:
        raise ActiveCargoTrajectoryError(
            f"row {row_number}: trajectory_sampling_interval_s must be positive"
        )
    atp_value, atp_unit = _paired_value_and_unit(
        row, "atp_value", "atp_unit", row_number
    )
    atp_assay = _optional_text(row, "atp_assay")
    if (atp_value is None) != (atp_assay is None):
        raise ActiveCargoTrajectoryError(
            f"row {row_number}: atp_value, atp_unit and atp_assay must be supplied together"
        )
    occupancy_value, occupancy_unit = _paired_value_and_unit(
        row, "motor_occupancy_value", "motor_occupancy_unit", row_number
    )
    perturbation_value, perturbation_unit = _paired_value_and_unit(
        row, "perturbation_value", "perturbation_unit", row_number
    )
    perturbation_identity = _optional_text(row, "perturbation_identity")
    if perturbation_value is not None and perturbation_identity is None:
        raise ActiveCargoTrajectoryError(
            f"row {row_number}: quantitative perturbation requires perturbation_identity"
        )
    partner_id = _optional_text(row, "fusion_or_fission_partner_id")
    if event in {"fusion", "fission"} and partner_id is None:
        raise ActiveCargoTrajectoryError(
            f"row {row_number}: fusion/fission requires a tracked partner id"
        )
    return ActiveCargoTrajectoryRecord(
        record_id=_required_text(row, "record_id", row_number),
        donor_id=_required_text(row, "donor_id", row_number),
        split_role=split_role,
        source_study_id=_required_text(row, "source_study_id", row_number),
        source_locator=_required_text(row, "source_locator", row_number),
        species="Homo sapiens",
        biological_system=biological_system,
        culture_format=_required_text(row, "culture_format", row_number),
        trajectory_id=_required_text(row, "trajectory_id", row_number),
        biological_replicate_id=_required_text(
            row, "biological_replicate_id", row_number
        ),
        cargo_identity=_required_text(row, "cargo_identity", row_number),
        cargo_labeling_method=_required_text(
            row, "cargo_labeling_method", row_number
        ),
        origin_compartment=_required_text(row, "origin_compartment", row_number),
        destination_compartment=_required_text(
            row, "destination_compartment", row_number
        ),
        cytoskeletal_track=track,
        motor_identity=_required_text(row, "motor_identity", row_number),
        frame_index=int(frame_token),
        time_from_trajectory_start_s=float(
            _nonnegative_number(
                row, "time_from_trajectory_start_s", row_number
            )
        ),
        position_x_um=float(_number(row, "position_x_um", row_number)),
        position_y_um=float(_number(row, "position_y_um", row_number)),
        position_z_um=float(_number(row, "position_z_um", row_number)),
        position_reference_frame=_required_text(
            row, "position_reference_frame", row_number
        ),
        localization_uncertainty_um=float(
            _nonnegative_number(row, "localization_uncertainty_um", row_number)
        ),
        trajectory_sampling_interval_s=float(sampling_interval),
        event_label=event,
        assay=_required_text(row, "assay", row_number),
        cell_viability_context=_required_text(
            row, "cell_viability_context", row_number
        ),
        track_polarity=_optional_text(row, "track_polarity"),
        atp_value=atp_value,
        atp_unit=atp_unit,
        atp_assay=atp_assay,
        motor_occupancy_value=occupancy_value,
        motor_occupancy_unit=occupancy_unit,
        perturbation_identity=perturbation_identity,
        perturbation_value=perturbation_value,
        perturbation_unit=perturbation_unit,
        fusion_or_fission_partner_id=partner_id,
        uncertainty_type=_optional_text(row, "uncertainty_type"),
        censoring_flag=_optional_text(row, "censoring_flag"),
    )


def load_active_cargo_trajectory_dataset(
    path: Path = DEFAULT_TRAJECTORY_PATH,
) -> ActiveCargoTrajectoryDataset:
    contract = load_active_cargo_trajectory_contract()
    expected_fields = tuple(
        item["id"]
        for group in ("required_columns", "conditional_columns")
        for item in contract[group]
    )
    if not path.exists():
        raise ActiveCargoTrajectoryError(f"active-cargo delivery not found: {_display_path(path)}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != expected_fields:
            raise ActiveCargoTrajectoryError(
                "active-cargo CSV header must exactly match the versioned contract"
            )
        records = tuple(_record(row, index) for index, row in enumerate(reader, start=2))
    if not records:
        raise ActiveCargoTrajectoryError("active-cargo delivery contains no records")
    record_ids = [record.record_id for record in records]
    if len(set(record_ids)) != len(record_ids):
        raise ActiveCargoTrajectoryError("active-cargo record_id values must be unique")

    donor_splits: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    study_splits: defaultdict[str, set[str]] = defaultdict(set)
    route_frames: defaultdict[tuple[str, str, str], set[int]] = defaultdict(set)
    for record in records:
        donor_splits[record.donor_key].add(record.split_role)
        study_splits[record.source_study_id].add(record.split_role)
        if record.frame_index in route_frames[record.route_key]:
            raise ActiveCargoTrajectoryError(
                f"route {record.route_key!r} repeats frame_index {record.frame_index}"
            )
        route_frames[record.route_key].add(record.frame_index)
    leaking_donors = [key for key, splits in donor_splits.items() if len(splits) > 1]
    if leaking_donors:
        raise ActiveCargoTrajectoryError(
            f"active-cargo donor crosses split roles: {leaking_donors!r}"
        )
    leaking_studies = [
        study
        for study, splits in study_splits.items()
        if "independent_heldout" in splits and len(splits) > 1
    ]
    if leaking_studies:
        raise ActiveCargoTrajectoryError(
            f"independent-heldout study crosses development splits: {leaking_studies!r}"
        )
    return ActiveCargoTrajectoryDataset(
        version=INTAKE_VERSION,
        contract_id=str(contract["contract_id"]),
        delivery_path=_display_path(path),
        artifact_sha256=_sha256(path),
        contract_sha256=_sha256(CONTRACT_PATH),
        records=records,
    )


def assess_active_cargo_route(
    records: tuple[ActiveCargoTrajectoryRecord, ...],
) -> ActiveCargoRouteAssessment:
    if not records:
        raise ActiveCargoTrajectoryError("cannot assess an empty active-cargo route")
    keys = {record.route_key for record in records}
    if len(keys) != 1:
        raise ActiveCargoTrajectoryError("one route assessment cannot mix trajectory ids")
    ordered = sorted(records, key=lambda record: record.frame_index)
    times = [record.time_from_trajectory_start_s for record in ordered]
    strictly_increasing_time = all(
        later > earlier for earlier, later in zip(times, times[1:], strict=False)
    )
    contexts = {
        (
            record.donor_key,
            record.biological_replicate_id,
            record.cargo_identity,
            record.cargo_labeling_method,
            record.origin_compartment,
            record.destination_compartment,
            record.cytoskeletal_track,
            record.motor_identity,
            record.position_reference_frame,
            record.assay,
            record.trajectory_sampling_interval_s,
        )
        for record in ordered
    }
    same_route_context = len(contexts) == 1
    events = frozenset(record.event_label for record in ordered)
    blockers: list[str] = []
    if len(ordered) < 3:
        blockers.append("fewer than three raw 3D positions")
    if not _REQUIRED_EVENTS <= events:
        blockers.append("departure and in-transit observations are incomplete")
    if not events.intersection(_TERMINAL_EVENTS):
        blockers.append("arrival, fusion or fission terminal observation is absent")
    if not strictly_increasing_time:
        blockers.append("trajectory time is not strictly increasing")
    if not same_route_context:
        blockers.append("cargo label, route, coordinate frame or assay changes within trajectory")
    structurally_complete = not blockers
    blockers.extend(
        (
            "manual primary-source trajectory review is incomplete",
            "frozen route model artifact is absent",
            "donor- and study-disjoint route-level held-out evaluation is absent",
        )
    )
    return ActiveCargoRouteAssessment(
        route_key=next(iter(keys)),
        raw_position_count=len(ordered),
        event_labels=tuple(sorted(events)),
        strictly_increasing_time=strictly_increasing_time,
        same_route_context=same_route_context,
        structurally_complete=structurally_complete,
        quantitative_activation_allowed=False,
        automatic_velocity_inference=False,
        automatic_motor_parameter_fitting=False,
        automatic_route_activation=False,
        blockers=tuple(blockers),
    )


def active_cargo_trajectory_intake_snapshot(
    path: Path = DEFAULT_TRAJECTORY_PATH,
) -> dict[str, object]:
    contract = load_active_cargo_trajectory_contract()
    expected_header_count = len(contract["required_columns"]) + len(
        contract["conditional_columns"]
    )
    if not path.exists():
        return {
            "version": INTAKE_VERSION,
            "contract_id": contract["contract_id"],
            "status": "awaiting_donor_resolved_3d_phh_active_cargo_trajectories",
            "delivery_path": _display_path(path),
            "contract_sha256": _sha256(CONTRACT_PATH),
            "expected_header_count": expected_header_count,
            "record_count": 0,
            "donor_count": 0,
            "route_count": 0,
            "structurally_complete_route_count": 0,
            "quantitatively_authorized_route_count": 0,
            "automatic_velocity_inference": False,
            "automatic_motor_parameter_fitting": False,
            "automatic_route_activation": False,
            "automatic_cell_state_coupling": False,
            "blockers": (
                "versioned donor-resolved raw 3D trajectory delivery is absent",
                "manual primary-source review is incomplete",
                "frozen route model and independent held-out evaluation are absent",
            ),
        }
    dataset = load_active_cargo_trajectory_dataset(path)
    grouped: defaultdict[
        tuple[str, str, str], list[ActiveCargoTrajectoryRecord]
    ] = defaultdict(list)
    for record in dataset.records:
        grouped[record.route_key].append(record)
    assessments = tuple(
        assess_active_cargo_route(tuple(records)) for records in grouped.values()
    )
    return {
        "version": INTAKE_VERSION,
        "contract_id": dataset.contract_id,
        "status": "trajectory_delivery_structurally_audited_not_authoritative",
        "delivery_path": dataset.delivery_path,
        "artifact_sha256": dataset.artifact_sha256,
        "contract_sha256": dataset.contract_sha256,
        "expected_header_count": expected_header_count,
        "record_count": len(dataset.records),
        "donor_count": len({record.donor_key for record in dataset.records}),
        "route_count": len(assessments),
        "record_count_by_split": dict(
            sorted(Counter(record.split_role for record in dataset.records).items())
        ),
        "structurally_complete_route_count": sum(
            assessment.structurally_complete for assessment in assessments
        ),
        "quantitatively_authorized_route_count": 0,
        "automatic_velocity_inference": False,
        "automatic_motor_parameter_fitting": False,
        "automatic_route_activation": False,
        "automatic_cell_state_coupling": False,
        "route_assessments": tuple(to_plain(assessment) for assessment in assessments),
        "blockers": (
            "manual primary-source trajectory review is incomplete",
            "frozen route model artifact is absent",
            "donor- and study-disjoint route-level held-out evaluation is absent",
        ),
    }
