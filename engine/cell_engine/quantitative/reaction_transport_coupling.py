"""Reaction-specific PHH transport-limitation evidence and coupling gate.

The conservative scalar solver is not attached to biology merely because a
diffusivity exists. Each reaction needs matched species mobility, geometry,
reaction timescale, a transport perturbation, a dimensionally explicit
coupling law and donor/study-disjoint held-out validation. This intake never
applies a global fluid multiplier or activates a local rate correction.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Collection


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "evidence_intake"
    / "phh_reaction_transport_coupling_contract.v1.json"
)
DEFAULT_OBSERVATION_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "evidence_intake"
    / "incoming"
    / "phh_reaction_transport_coupling"
    / "latest"
    / "phh_reaction_transport_observations.csv"
)
CONTRACT_SCHEMA_VERSION = "cell.phh-reaction-transport-coupling-contract.v1"
INTAKE_VERSION = "phh_reaction_transport_coupling_intake_v1"
COUPLING_GATE_VERSION = "phh_reaction_transport_coupling_gate_v1"
TRANSPORT_SCALE_DEFINITION = "L^2/(D*tau_reaction)"

_NULL_TOKEN = "null"
_ALLOWED_SPLIT_ROLES = frozenset(
    {"calibration", "internal_validation", "independent_heldout"}
)
_DYNAMIC_STAGE_IDS = frozenset(
    {
        "reaction_timescale_trajectory",
        "transport_perturbation_demonstration",
        "independent_heldout_validation",
    }
)
_TARGET_REACTION_IDS = (
    "glycogen_synthesis", "glycogen_breakdown", "glucose_export",
    "glutaminase", "alanine_transaminase", "aspartate_transaminase",
    "glutamate_dehydrogenase", "lactate_dehydrogenase",
    "pyruvate_carboxylase", "pepck", "lower_glycolysis_reverse",
    "fructose_1_6_bisphosphatase", "phosphoglucose_isomerase_reverse",
    "glucose_6_phosphatase", "hepatic_glucose_output", "glycerol_kinase",
    "glycerol_3_phosphate_dehydrogenase", "triose_phosphate_condensation",
    "beta_oxidation", "thiolase", "hmgcs2", "hmgcl", "bdh1_forward",
    "bdh1_reverse", "acetoacetate_decarboxylation",
    "acetyl_coa_carboxylase", "fatty_acid_synthase",
    "malonyl_coa_decarboxylase", "cpt1_beta_oxidation", "cps1", "otc",
    "ass1", "asl", "arg1", "atp_regeneration", "atp_maintenance",
)
_REQUIRED_STAGE_IDS = (
    "exact_reaction_identity",
    "participant_compartment_fields",
    "species_mobility_link",
    "characteristic_length_geometry",
    "reaction_timescale_trajectory",
    "transport_perturbation_demonstration",
    "dimensional_coupling_law",
    "independent_heldout_validation",
)


class ReactionTransportCouplingError(ValueError):
    """Raised when reaction-transport evidence violates the contract."""


@dataclass(frozen=True)
class ReactionTransportRecord:
    record_id: str
    target_reaction_id: str
    stage_id: str
    series_id: str
    observation_index: int
    donor_id: str
    split_role: str
    source_study_id: str
    source_locator: str
    species: str
    biological_system: str
    culture_format: str
    tissue_health_state: str
    liver_zone: str
    biological_replicate_id: str
    reaction_equation: str
    reaction_equation_sha256: str
    participant_species_ids: str
    compartment: str
    localization_method: str
    mobility_evidence_record_ids: tuple[str, ...]
    geometry_evidence_record_ids: tuple[str, ...]
    independent_axis_name: str
    independent_value: float
    independent_unit: str
    observed_quantity: str
    observed_value: float
    observed_unit: str
    uncertainty_value: float
    uncertainty_type: str
    raw_artifact_path: str
    raw_artifact_sha256: str
    model_or_operator_version: str
    frozen_before_heldout_access: bool
    manual_primary_source_review_status: str
    apparent_diffusivity_value: float | None
    apparent_diffusivity_unit: str | None
    characteristic_length_value: float | None
    characteristic_length_unit: str | None
    reaction_timescale_value: float | None
    reaction_timescale_unit: str | None
    transport_scale_ratio_value: float | None
    transport_scale_ratio_definition: str | None
    coupling_equation: str | None
    coupling_equation_sha256: str | None
    transport_limitation_criterion: str | None
    transport_limitation_result: str | None
    perturbation_identity: str | None
    perturbation_value: float | None
    perturbation_unit: str | None
    censoring_or_missingness: str | None

    @property
    def donor_key(self) -> tuple[str, str]:
        return self.source_study_id, self.donor_id

    @property
    def series_key(self) -> tuple[str, str, str, str]:
        return (
            self.source_study_id,
            self.donor_id,
            self.target_reaction_id,
            self.series_id,
        )


@dataclass(frozen=True)
class ReactionTransportAssessment:
    target_reaction_id: str
    covered_stage_ids: tuple[str, ...]
    missing_stage_ids: tuple[str, ...]
    record_count: int
    ordered_dynamic_series_count: int
    calibration_context_consistent: bool
    mobility_links_resolved: bool
    geometry_links_resolved: bool
    dimensionally_consistent_scale_ratio: bool
    transport_limitation_demonstrated: bool
    donor_disjoint_heldout: bool
    study_disjoint_heldout: bool
    structurally_complete: bool
    local_concentration_coupling_allowed: bool
    direct_rate_correction_allowed: bool
    runtime_activation_allowed: bool
    blockers: tuple[str, ...]


def _sha256_bytes(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


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


def _resolve_artifact(raw: str, expected_sha256: str, *, label: str) -> Path:
    path = Path(raw)
    resolved = path.resolve() if path.is_absolute() else (REPOSITORY_ROOT / path).resolve()
    if not resolved.is_file():
        raise ReactionTransportCouplingError(f"{label} does not exist: {raw}")
    expected = expected_sha256.lower()
    if len(expected) != 64 or any(character not in "0123456789abcdef" for character in expected):
        raise ReactionTransportCouplingError(f"{label} SHA-256 is malformed")
    if _sha256(resolved) != expected:
        raise ReactionTransportCouplingError(f"{label} SHA-256 mismatch")
    return resolved


def transport_scale_ratio(
    characteristic_length_um: float,
    apparent_diffusivity_um2_s: float,
    reaction_timescale_s: float,
) -> float:
    """Return the declared dimensionless scale L^2/(D*tau_reaction)."""

    values = (
        characteristic_length_um,
        apparent_diffusivity_um2_s,
        reaction_timescale_s,
    )
    if not all(math.isfinite(value) and value > 0 for value in values):
        raise ReactionTransportCouplingError(
            "transport scale inputs must be finite and positive"
        )
    return characteristic_length_um**2 / (
        apparent_diffusivity_um2_s * reaction_timescale_s
    )


def _reaction_ids_from_atlas() -> tuple[str, ...]:
    from cell_engine.validation.reaction_evidence_atlas import (
        build_reaction_evidence_atlas,
    )

    return tuple(
        reaction["reaction_id"]
        for reaction in build_reaction_evidence_atlas()["reactions"]
    )


def load_reaction_transport_coupling_contract(
    path: Path = CONTRACT_PATH,
) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != CONTRACT_SCHEMA_VERSION:
        raise ReactionTransportCouplingError("unsupported reaction-transport contract schema")
    required = payload.get("required_columns")
    conditional = payload.get("conditional_columns")
    gate = payload.get("coupling_gate")
    policy = payload.get("policy")
    required_ids = tuple(
        str(item.get("id", "")) for item in required or () if isinstance(item, dict)
    )
    conditional_ids = tuple(
        str(item.get("id", "")) for item in conditional or () if isinstance(item, dict)
    )
    if (
        len(required_ids) != 35
        or len(set(required_ids)) != 35
        or len(conditional_ids) != 16
        or len(set(conditional_ids)) != 16
        or not all(required_ids + conditional_ids)
    ):
        raise ReactionTransportCouplingError("reaction-transport field contract changed")
    if tuple(payload.get("target_reaction_ids", ())) != _TARGET_REACTION_IDS:
        raise ReactionTransportCouplingError("reaction-transport targets changed")
    if _reaction_ids_from_atlas() != _TARGET_REACTION_IDS:
        raise ReactionTransportCouplingError("reaction-transport targets no longer match the atlas")
    if tuple(payload.get("required_stage_ids", ())) != _REQUIRED_STAGE_IDS:
        raise ReactionTransportCouplingError("reaction-transport stages changed")
    if set(payload.get("allowed_split_roles", ())) != _ALLOWED_SPLIT_ROLES:
        raise ReactionTransportCouplingError("reaction-transport split roles changed")
    if (
        payload.get("canonical_null_token") != _NULL_TOKEN
        or payload.get("transport_scale_definition") != TRANSPORT_SCALE_DEFINITION
    ):
        raise ReactionTransportCouplingError("reaction-transport scale/null policy changed")
    if (
        not isinstance(gate, dict)
        or gate.get("version") != COUPLING_GATE_VERSION
        or gate.get("minimum_ordered_points_per_dynamic_series") != 3
    ):
        raise ReactionTransportCouplingError("reaction-transport gate changed")
    required_true = {
        "same_donor_required_for_calibration_chain",
        "same_reaction_equation_required",
        "same_compartment_required",
        "matched_species_mobility_records_required",
        "measured_characteristic_length_required",
        "matched_reaction_timescale_required",
        "transport_perturbation_demonstration_required",
        "dimensionally_consistent_scale_ratio_required",
        "complete_coupling_equation_fingerprint_required",
        "healthy_human_context_required",
        "donor_disjoint_validation_required",
        "independent_heldout_study_required",
        "frozen_model_before_heldout_access_required",
    }
    required_false = {
        "automatic_global_fluid_multiplier",
        "automatic_damkohler_threshold",
        "automatic_parameter_fitting",
        "automatic_local_concentration_coupling",
        "automatic_direct_rate_correction",
        "automatic_runtime_activation",
    }
    if any(gate.get(key) is not True for key in required_true) or any(
        gate.get(key) is not False for key in required_false
    ):
        raise ReactionTransportCouplingError("reaction-transport gate escaped fail-closed state")
    if not isinstance(policy, dict) or policy.get("manual_primary_source_review_required") is not True:
        raise ReactionTransportCouplingError("reaction-transport review policy changed")
    if any(
        policy.get(key) is not False
        for key in (
            "mobility_record_without_matching_reaction_context_is_sufficient",
            "bulk_tissue_flux_defines_local_reaction_timescale",
            "equivalent_sphere_radius_defines_every_transport_length",
            "dimensionless_scale_ratio_alone_proves_transport_limitation",
            "global_viscosity_multiplier_is_allowed",
            "cross_species_transfer_allowed",
            "cell_line_transfer_to_healthy_phh_allowed",
            "missing_transport_effect_means_no_effect",
            "automatic_parameter_activation",
        )
    ):
        raise ReactionTransportCouplingError("reaction-transport policy escaped fail-closed state")
    return payload


def _required_text(row: dict[str, str], field: str, row_number: int) -> str:
    value = row[field].strip()
    if not value or value.lower() == _NULL_TOKEN:
        raise ReactionTransportCouplingError(f"row {row_number}: {field} is required")
    return value


def _optional_text(row: dict[str, str], field: str) -> str | None:
    value = row[field].strip()
    return None if not value or value.lower() == _NULL_TOKEN else value


def _required_float(
    row: dict[str, str],
    field: str,
    row_number: int,
    *,
    nonnegative: bool = False,
) -> float:
    raw = _required_text(row, field, row_number)
    try:
        value = float(raw)
    except ValueError as error:
        raise ReactionTransportCouplingError(f"row {row_number}: {field} must be numeric") from error
    if not math.isfinite(value) or (nonnegative and value < 0):
        raise ReactionTransportCouplingError(f"row {row_number}: {field} is outside its domain")
    return value


def _optional_float(row: dict[str, str], field: str, row_number: int) -> float | None:
    raw = _optional_text(row, field)
    if raw is None:
        return None
    try:
        value = float(raw)
    except ValueError as error:
        raise ReactionTransportCouplingError(f"row {row_number}: {field} must be numeric") from error
    if not math.isfinite(value):
        raise ReactionTransportCouplingError(f"row {row_number}: {field} must be finite")
    return value


def _identifier_tuple(raw: str) -> tuple[str, ...]:
    values = tuple(value.strip() for value in raw.split(";") if value.strip())
    if not values or any(value.lower() == _NULL_TOKEN for value in values):
        raise ReactionTransportCouplingError("evidence identifiers must be semicolon-delimited non-null IDs")
    return values


def _record_from_row(row: dict[str, str], row_number: int) -> ReactionTransportRecord:
    raw_index = _required_text(row, "observation_index", row_number)
    if not raw_index.isdigit():
        raise ReactionTransportCouplingError(
            f"row {row_number}: observation_index must be non-negative"
        )
    raw_frozen = _required_text(row, "frozen_before_heldout_access", row_number).lower()
    if raw_frozen not in {"true", "false"}:
        raise ReactionTransportCouplingError(
            f"row {row_number}: frozen_before_heldout_access must be true or false"
        )
    text_fields = (
        "record_id", "target_reaction_id", "stage_id", "series_id", "donor_id",
        "split_role", "source_study_id", "source_locator", "species",
        "biological_system", "culture_format", "tissue_health_state", "liver_zone",
        "biological_replicate_id", "reaction_equation", "reaction_equation_sha256",
        "participant_species_ids", "compartment", "localization_method",
        "independent_axis_name", "independent_unit", "observed_quantity",
        "observed_unit", "uncertainty_type", "raw_artifact_path",
        "raw_artifact_sha256", "model_or_operator_version",
        "manual_primary_source_review_status",
    )
    values: dict[str, Any] = {
        field: _required_text(row, field, row_number) for field in text_fields
    }
    values.update(
        {
            "observation_index": int(raw_index),
            "mobility_evidence_record_ids": _identifier_tuple(
                _required_text(row, "mobility_evidence_record_ids", row_number)
            ),
            "geometry_evidence_record_ids": _identifier_tuple(
                _required_text(row, "geometry_evidence_record_ids", row_number)
            ),
            "independent_value": _required_float(row, "independent_value", row_number),
            "observed_value": _required_float(row, "observed_value", row_number),
            "uncertainty_value": _required_float(
                row, "uncertainty_value", row_number, nonnegative=True
            ),
            "frozen_before_heldout_access": raw_frozen == "true",
        }
    )
    optional_text_fields = (
        "apparent_diffusivity_unit", "characteristic_length_unit",
        "reaction_timescale_unit", "transport_scale_ratio_definition",
        "coupling_equation", "coupling_equation_sha256",
        "transport_limitation_criterion", "transport_limitation_result",
        "perturbation_identity", "perturbation_unit", "censoring_or_missingness",
    )
    values.update({field: _optional_text(row, field) for field in optional_text_fields})
    optional_float_fields = (
        "apparent_diffusivity_value", "characteristic_length_value",
        "reaction_timescale_value", "transport_scale_ratio_value",
        "perturbation_value",
    )
    values.update(
        {field: _optional_float(row, field, row_number) for field in optional_float_fields}
    )
    if values["target_reaction_id"] not in _TARGET_REACTION_IDS:
        raise ReactionTransportCouplingError(f"row {row_number}: unsupported target_reaction_id")
    if values["stage_id"] not in _REQUIRED_STAGE_IDS:
        raise ReactionTransportCouplingError(f"row {row_number}: unsupported stage_id")
    if values["split_role"] not in _ALLOWED_SPLIT_ROLES:
        raise ReactionTransportCouplingError(f"row {row_number}: unsupported split_role")
    if values["species"] != "Homo sapiens":
        raise ReactionTransportCouplingError(f"row {row_number}: species must be Homo sapiens")
    if _sha256_bytes(values["reaction_equation"]) != values["reaction_equation_sha256"]:
        raise ReactionTransportCouplingError(f"row {row_number}: reaction equation SHA-256 mismatch")
    if values["coupling_equation"] is not None:
        if (
            values["coupling_equation_sha256"] is None
            or _sha256_bytes(values["coupling_equation"])
            != values["coupling_equation_sha256"]
        ):
            raise ReactionTransportCouplingError(f"row {row_number}: coupling equation SHA-256 mismatch")
    elif values["coupling_equation_sha256"] is not None:
        raise ReactionTransportCouplingError(
            f"row {row_number}: coupling equation and fingerprint must be paired"
        )
    for value_field, unit_field in (
        ("apparent_diffusivity_value", "apparent_diffusivity_unit"),
        ("characteristic_length_value", "characteristic_length_unit"),
        ("reaction_timescale_value", "reaction_timescale_unit"),
        ("perturbation_value", "perturbation_unit"),
    ):
        if (values[value_field] is None) != (values[unit_field] is None):
            raise ReactionTransportCouplingError(
                f"row {row_number}: {value_field} and {unit_field} must be paired"
            )
    ratio_paired = (
        values["transport_scale_ratio_value"] is None
    ) == (
        values["transport_scale_ratio_definition"] is None
    )
    if not ratio_paired:
        raise ReactionTransportCouplingError(
            f"row {row_number}: transport ratio and definition must be paired"
        )
    if values["split_role"] == "independent_heldout" and not values["frozen_before_heldout_access"]:
        raise ReactionTransportCouplingError(
            f"row {row_number}: held-out operator was not frozen before access"
        )
    _resolve_artifact(
        values["raw_artifact_path"],
        values["raw_artifact_sha256"],
        label=f"reaction-transport raw artifact row {row_number}",
    )
    return ReactionTransportRecord(**values)


def load_reaction_transport_observations(
    path: Path = DEFAULT_OBSERVATION_PATH,
) -> tuple[ReactionTransportRecord, ...]:
    contract = load_reaction_transport_coupling_contract()
    if not path.exists():
        return ()
    expected_header = tuple(
        item["id"]
        for group in ("required_columns", "conditional_columns")
        for item in contract[group]
    )
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != expected_header:
            raise ReactionTransportCouplingError("reaction-transport header changed")
        records = tuple(
            _record_from_row(row, row_number)
            for row_number, row in enumerate(reader, start=2)
        )
    record_ids = [record.record_id for record in records]
    if len(record_ids) != len(set(record_ids)):
        raise ReactionTransportCouplingError("reaction-transport record_id values must be unique")
    donor_splits: dict[tuple[str, str], set[str]] = defaultdict(set)
    series: dict[tuple[str, str, str, str], list[ReactionTransportRecord]] = defaultdict(list)
    for record in records:
        donor_splits[record.donor_key].add(record.split_role)
        series[record.series_key].append(record)
    if any(len(splits) > 1 for splits in donor_splits.values()):
        raise ReactionTransportCouplingError("reaction-transport donor leaks across splits")
    for key, series_records in series.items():
        contexts = {
            (
                record.stage_id, record.reaction_equation_sha256,
                record.compartment, record.independent_axis_name,
                record.independent_unit, record.observed_quantity,
                record.observed_unit,
            )
            for record in series_records
        }
        if len(contexts) != 1:
            raise ReactionTransportCouplingError(f"reaction-transport series context changed in {key}")
        ordered = sorted(series_records, key=lambda record: record.observation_index)
        if [record.observation_index for record in ordered] != list(range(len(ordered))):
            raise ReactionTransportCouplingError(f"reaction-transport indices are not contiguous in {key}")
        if ordered[0].stage_id in _DYNAMIC_STAGE_IDS:
            if len(ordered) < 3:
                raise ReactionTransportCouplingError(
                    f"dynamic reaction-transport series {key} needs at least three points"
                )
            if any(
                later.independent_value <= earlier.independent_value
                for earlier, later in zip(ordered, ordered[1:])
            ):
                raise ReactionTransportCouplingError(
                    f"dynamic reaction-transport series {key} axis must increase strictly"
                )
    return records


def _assess_reaction(
    target_reaction_id: str,
    records: tuple[ReactionTransportRecord, ...],
    *,
    available_mobility_record_ids: Collection[str],
    available_geometry_record_ids: Collection[str],
) -> ReactionTransportAssessment:
    reaction_records = tuple(
        record for record in records if record.target_reaction_id == target_reaction_id
    )
    covered = tuple(
        stage_id
        for stage_id in _REQUIRED_STAGE_IDS
        if any(record.stage_id == stage_id for record in reaction_records)
    )
    missing = tuple(stage_id for stage_id in _REQUIRED_STAGE_IDS if stage_id not in covered)
    calibration = tuple(
        record for record in reaction_records if record.split_role != "independent_heldout"
    )
    heldout = tuple(
        record for record in reaction_records if record.split_role == "independent_heldout"
    )
    calibration_contexts = {
        (
            record.donor_key,
            record.reaction_equation_sha256,
            record.compartment,
        )
        for record in calibration
    }
    calibration_consistent = bool(calibration) and len(calibration_contexts) == 1
    calibration_donors = {record.donor_key for record in calibration}
    heldout_donors = {record.donor_key for record in heldout}
    calibration_studies = {record.source_study_id for record in calibration}
    heldout_studies = {record.source_study_id for record in heldout}
    donor_disjoint = bool(calibration_donors and heldout_donors) and calibration_donors.isdisjoint(
        heldout_donors
    )
    study_disjoint = bool(calibration_studies and heldout_studies) and calibration_studies.isdisjoint(
        heldout_studies
    )
    mobility_links = {
        identifier
        for record in reaction_records
        for identifier in record.mobility_evidence_record_ids
    }
    geometry_links = {
        identifier
        for record in reaction_records
        for identifier in record.geometry_evidence_record_ids
    }
    mobility_resolved = bool(mobility_links) and mobility_links.issubset(
        set(available_mobility_record_ids)
    )
    geometry_resolved = bool(geometry_links) and geometry_links.issubset(
        set(available_geometry_record_ids)
    )
    ratio_records = tuple(
        record
        for record in reaction_records
        if record.stage_id == "dimensional_coupling_law"
    )
    ratio_consistent = False
    if ratio_records:
        ratio_consistent = all(
            record.apparent_diffusivity_value is not None
            and record.apparent_diffusivity_unit == "um2/s"
            and record.characteristic_length_value is not None
            and record.characteristic_length_unit == "um"
            and record.reaction_timescale_value is not None
            and record.reaction_timescale_unit == "s"
            and record.transport_scale_ratio_value is not None
            and record.transport_scale_ratio_definition == TRANSPORT_SCALE_DEFINITION
            and record.coupling_equation is not None
            and math.isclose(
                record.transport_scale_ratio_value,
                transport_scale_ratio(
                    record.characteristic_length_value,
                    record.apparent_diffusivity_value,
                    record.reaction_timescale_value,
                ),
                rel_tol=1e-9,
                abs_tol=1e-12,
            )
            for record in ratio_records
        )
    limitation_demonstrated = any(
        record.stage_id == "transport_perturbation_demonstration"
        and record.transport_limitation_criterion is not None
        and record.transport_limitation_result == "pass"
        and record.perturbation_identity is not None
        for record in reaction_records
    )
    blockers: list[str] = []
    if missing:
        blockers.append("one or more required reaction-transport stages are missing")
    if not calibration_consistent:
        blockers.append("calibration stages do not share donor, equation and compartment")
    if not mobility_resolved:
        blockers.append("linked species-mobility records are absent or unresolved")
    if not geometry_resolved:
        blockers.append("linked measured geometry records are absent or unresolved")
    if not ratio_consistent:
        blockers.append("dimensionally consistent L^2/(D*tau_reaction) record is absent")
    if not limitation_demonstrated:
        blockers.append("pre-registered transport perturbation did not demonstrate limitation")
    if not donor_disjoint:
        blockers.append("donor-disjoint held-out validation is absent")
    if not study_disjoint:
        blockers.append("study-disjoint held-out validation is absent")
    if any(
        record.manual_primary_source_review_status != "pass"
        for record in reaction_records
    ):
        blockers.append("manual primary-source review is incomplete")
    if any(
        "healthy" not in record.tissue_health_state.lower()
        and "non-diseased" not in record.tissue_health_state.lower()
        for record in reaction_records
    ):
        blockers.append("healthy/non-diseased PHH context is not explicit")
    structurally_complete = bool(reaction_records) and not blockers
    return ReactionTransportAssessment(
        target_reaction_id=target_reaction_id,
        covered_stage_ids=covered,
        missing_stage_ids=missing,
        record_count=len(reaction_records),
        ordered_dynamic_series_count=len(
            {
                record.series_key
                for record in reaction_records
                if record.stage_id in _DYNAMIC_STAGE_IDS
            }
        ),
        calibration_context_consistent=calibration_consistent,
        mobility_links_resolved=mobility_resolved,
        geometry_links_resolved=geometry_resolved,
        dimensionally_consistent_scale_ratio=ratio_consistent,
        transport_limitation_demonstrated=limitation_demonstrated,
        donor_disjoint_heldout=donor_disjoint,
        study_disjoint_heldout=study_disjoint,
        structurally_complete=structurally_complete,
        local_concentration_coupling_allowed=False,
        direct_rate_correction_allowed=False,
        runtime_activation_allowed=False,
        blockers=tuple(blockers)
        + ("explicit frozen-model promotion is required before runtime coupling",),
    )


def _default_available_record_ids() -> tuple[set[str], set[str]]:
    from cell_engine.quantitative.intracellular_mobility import (
        intracellular_mobility_intake_snapshot,
    )
    from cell_engine.quantitative.phh_3d_mesh_boundary import (
        phh_3d_mesh_boundary_intake_snapshot,
    )

    mobility = intracellular_mobility_intake_snapshot()
    geometry = phh_3d_mesh_boundary_intake_snapshot()
    return (
        {str(record["record_id"]) for record in mobility["records"]},
        {str(record["record_id"]) for record in geometry["records"]},
    )


def reaction_transport_coupling_intake_snapshot(
    observation_path: Path = DEFAULT_OBSERVATION_PATH,
    *,
    available_mobility_record_ids: Collection[str] | None = None,
    available_geometry_record_ids: Collection[str] | None = None,
) -> dict[str, object]:
    contract = load_reaction_transport_coupling_contract()
    records = load_reaction_transport_observations(observation_path)
    if available_mobility_record_ids is None or available_geometry_record_ids is None:
        default_mobility, default_geometry = _default_available_record_ids()
        if available_mobility_record_ids is None:
            available_mobility_record_ids = default_mobility
        if available_geometry_record_ids is None:
            available_geometry_record_ids = default_geometry
    assessments = tuple(
        _assess_reaction(
            target_reaction_id,
            records,
            available_mobility_record_ids=available_mobility_record_ids,
            available_geometry_record_ids=available_geometry_record_ids,
        )
        for target_reaction_id in _TARGET_REACTION_IDS
    )
    return {
        "version": INTAKE_VERSION,
        "status": "contract_ready_no_reaction_transport_coupling_authorized",
        "contract_id": contract["contract_id"],
        "contract_path": _display_path(CONTRACT_PATH),
        "contract_sha256": _sha256(CONTRACT_PATH),
        "delivery_path": _display_path(observation_path),
        "delivery_sha256": _sha256(observation_path) if observation_path.exists() else None,
        "transport_scale_definition": TRANSPORT_SCALE_DEFINITION,
        "expected_headers": [
            item["id"]
            for group in ("required_columns", "conditional_columns")
            for item in contract[group]
        ],
        "target_reaction_ids": list(_TARGET_REACTION_IDS),
        "required_stage_ids": list(_REQUIRED_STAGE_IDS),
        "records": [asdict(record) for record in records],
        "assessments": [asdict(assessment) for assessment in assessments],
        "summary": {
            "required_field_count": len(contract["required_columns"]),
            "conditional_field_count": len(contract["conditional_columns"]),
            "target_reaction_count": len(_TARGET_REACTION_IDS),
            "required_stage_count_per_reaction": len(_REQUIRED_STAGE_IDS),
            "required_stage_slot_count": len(_TARGET_REACTION_IDS) * len(_REQUIRED_STAGE_IDS),
            "record_count": len(records),
            "covered_stage_slot_count": sum(
                len(assessment.covered_stage_ids) for assessment in assessments
            ),
            "mobility_resolved_reaction_count": sum(
                assessment.mobility_links_resolved for assessment in assessments
            ),
            "geometry_resolved_reaction_count": sum(
                assessment.geometry_links_resolved for assessment in assessments
            ),
            "dimensionally_consistent_reaction_count": sum(
                assessment.dimensionally_consistent_scale_ratio
                for assessment in assessments
            ),
            "transport_limitation_demonstrated_reaction_count": sum(
                assessment.transport_limitation_demonstrated
                for assessment in assessments
            ),
            "structurally_complete_reaction_count": sum(
                assessment.structurally_complete for assessment in assessments
            ),
            "local_concentration_coupled_reaction_count": 0,
            "direct_rate_corrected_reaction_count": 0,
            "runtime_activated_reaction_count": 0,
            "global_fluid_multiplier_count": 0,
        },
        "gates": {
            "matched_species_mobility_required": True,
            "measured_characteristic_length_required": True,
            "matched_reaction_timescale_required": True,
            "transport_perturbation_required": True,
            "dimensionally_consistent_coupling_law_required": True,
            "automatic_global_fluid_multiplier": False,
            "automatic_local_concentration_coupling": False,
            "automatic_direct_rate_correction": False,
            "automatic_runtime_activation": False,
        },
        "limitations": [
            "No reaction has matched healthy-PHH mobility, geometry, timescale and transport-perturbation evidence.",
            "The dimensionless L^2/(D*tau_reaction) scale is an audit quantity, not an automatic threshold.",
            "A species diffusivity alone cannot establish that a reaction is transport-limited.",
            "Equivalent-sphere cell radius and bulk-tissue flux cannot silently define local transport length or reaction time.",
            "No local concentration coupling, direct rate correction or global fluid multiplier is active.",
        ],
    }


__all__ = [
    "CONTRACT_PATH",
    "DEFAULT_OBSERVATION_PATH",
    "ReactionTransportAssessment",
    "ReactionTransportCouplingError",
    "ReactionTransportRecord",
    "load_reaction_transport_coupling_contract",
    "load_reaction_transport_observations",
    "reaction_transport_coupling_intake_snapshot",
    "transport_scale_ratio",
]
