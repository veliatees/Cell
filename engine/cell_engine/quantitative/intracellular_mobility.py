"""Species-resolved healthy-PHH mobility and crowding evidence intake.

This module accepts raw, donor-resolved mobility observations while refusing a
global viscosity multiplier. Probe size, molecular form, compartment, binding,
local crowding, perturbation response and donor-heldout validation are separate
evidence stages. Structural completeness never activates diffusivity, crowding
or reaction coupling automatically.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "evidence_intake"
    / "phh_intracellular_mobility_contract.v1.json"
)
DEFAULT_OBSERVATION_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "evidence_intake"
    / "incoming"
    / "phh_intracellular_mobility"
    / "latest"
    / "phh_intracellular_mobility_observations.csv"
)
CONTRACT_SCHEMA_VERSION = "cell.phh-intracellular-mobility-contract.v1"
INTAKE_VERSION = "phh_intracellular_mobility_intake_v1"
MOBILITY_GATE_VERSION = "phh_intracellular_mobility_gate_v1"

_NULL_TOKEN = "null"
_ALLOWED_SPLIT_ROLES = frozenset(
    {"calibration", "internal_validation", "independent_heldout"}
)
_DYNAMIC_STAGE_IDS = frozenset(
    {
        "raw_mobility_trajectory",
        "perturbation_transport_response",
        "independent_heldout_validation",
    }
)
_TARGET_SPECIES_IDS = (
    "ADP", "AMP", "ATP", "CoA", "HMG_CoA", "NADH", "NAD_plus",
    "acetoacetate", "acetoacetyl_CoA", "acetone", "acetyl_CoA",
    "alanine", "alpha_ketoglutarate", "ammonia", "arginine",
    "argininosuccinate", "aspartate", "beta_hydroxybutyrate",
    "carbamoyl_phosphate", "citrulline", "dihydroxyacetone_phosphate",
    "fatty_acids", "fructose_1_6_bisphosphate", "fructose_6_phosphate",
    "fumarate", "glucose", "glucose_6_phosphate", "glucose_blood",
    "glucose_cyto", "glutamate", "glutamine", "glycerol",
    "glycerol_3_phosphate", "glycogen", "lactate", "malonyl_CoA",
    "mito_acetyl_CoA", "ornithine", "oxaloacetate", "palmitate",
    "phosphoenolpyruvate", "pyruvate", "urea",
)
_REQUIRED_STAGE_IDS = (
    "molecular_identity_state",
    "compartment_localization",
    "probe_scale_calibration",
    "raw_mobility_trajectory",
    "apparent_diffusivity_model",
    "local_crowding_abundance_field",
    "binding_free_fraction",
    "perturbation_transport_response",
    "independent_heldout_validation",
)


class IntracellularMobilityError(ValueError):
    """Raised when mobility evidence violates the fail-closed contract."""


@dataclass(frozen=True)
class IntracellularMobilityRecord:
    record_id: str
    target_species_id: str
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
    compartment: str
    subcompartment: str
    molecular_form: str
    label_or_probe_identity: str
    probe_hydrodynamic_radius_value: float
    probe_hydrodynamic_radius_unit: str
    measurement_method: str
    independent_axis_name: str
    independent_value: float
    independent_unit: str
    observed_quantity: str
    observed_value: float
    observed_unit: str
    uncertainty_value: float
    uncertainty_type: str
    assay_temperature_value: float
    assay_temperature_unit: str
    assay_ph: float
    raw_artifact_path: str
    raw_artifact_sha256: str
    manual_primary_source_review_status: str
    apparent_diffusivity_value: float | None
    apparent_diffusivity_unit: str | None
    diffusion_tensor_xx: float | None
    diffusion_tensor_yy: float | None
    diffusion_tensor_zz: float | None
    anomalous_exponent: float | None
    free_fraction_value: float | None
    free_fraction_unit: str | None
    local_crowder_value: float | None
    local_crowder_unit: str | None
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
            self.target_species_id,
            self.series_id,
        )


@dataclass(frozen=True)
class IntracellularMobilityAssessment:
    target_species_id: str
    covered_stage_ids: tuple[str, ...]
    missing_stage_ids: tuple[str, ...]
    record_count: int
    donor_count: int
    study_count: int
    ordered_dynamic_series_count: int
    calibration_context_consistent: bool
    donor_disjoint_heldout: bool
    study_disjoint_heldout: bool
    size_resolved_crowding_chain: bool
    structurally_complete: bool
    apparent_diffusivity_activation_allowed: bool
    crowding_law_activation_allowed: bool
    reaction_coupling_allowed: bool
    blockers: tuple[str, ...]


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
        raise IntracellularMobilityError(f"{label} does not exist: {raw}")
    expected = expected_sha256.lower()
    if len(expected) != 64 or any(character not in "0123456789abcdef" for character in expected):
        raise IntracellularMobilityError(f"{label} SHA-256 is malformed")
    if _sha256(resolved) != expected:
        raise IntracellularMobilityError(f"{label} SHA-256 mismatch")
    return resolved


def _reaction_species_ids() -> tuple[str, ...]:
    from cell_engine.validation.reaction_evidence_atlas import (
        build_reaction_evidence_atlas,
    )

    atlas = build_reaction_evidence_atlas()
    return tuple(
        sorted(
            {
                species_id
                for reaction in atlas["reactions"]
                for side in ("reactants", "products")
                for species_id in reaction[side]
            }
        )
    )


def load_intracellular_mobility_contract(
    path: Path = CONTRACT_PATH,
) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != CONTRACT_SCHEMA_VERSION:
        raise IntracellularMobilityError("unsupported intracellular-mobility contract schema")
    required = payload.get("required_columns")
    conditional = payload.get("conditional_columns")
    gate = payload.get("mobility_gate")
    policy = payload.get("policy")
    required_ids = tuple(
        str(item.get("id", "")) for item in required or () if isinstance(item, dict)
    )
    conditional_ids = tuple(
        str(item.get("id", "")) for item in conditional or () if isinstance(item, dict)
    )
    if (
        len(required_ids) != 36
        or len(set(required_ids)) != 36
        or len(conditional_ids) != 14
        or len(set(conditional_ids)) != 14
        or not all(required_ids + conditional_ids)
    ):
        raise IntracellularMobilityError("mobility field contract changed")
    if tuple(payload.get("target_species_ids", ())) != _TARGET_SPECIES_IDS:
        raise IntracellularMobilityError("mobility target species changed")
    if tuple(sorted(_TARGET_SPECIES_IDS)) != _reaction_species_ids():
        raise IntracellularMobilityError("mobility targets no longer match the reaction atlas")
    if tuple(payload.get("required_stage_ids", ())) != _REQUIRED_STAGE_IDS:
        raise IntracellularMobilityError("mobility evidence stages changed")
    if set(payload.get("allowed_split_roles", ())) != _ALLOWED_SPLIT_ROLES:
        raise IntracellularMobilityError("mobility split roles changed")
    if payload.get("canonical_null_token") != _NULL_TOKEN:
        raise IntracellularMobilityError("mobility null policy changed")
    if (
        not isinstance(gate, dict)
        or gate.get("version") != MOBILITY_GATE_VERSION
        or gate.get("minimum_ordered_points_per_dynamic_series") != 3
        or gate.get("minimum_probe_sizes_for_crowding_law") != 3
    ):
        raise IntracellularMobilityError("mobility gate changed")
    required_true = {
        "same_donor_required_for_calibration_chain",
        "same_compartment_required_for_calibration_chain",
        "same_molecular_form_required_for_calibration_chain",
        "probe_size_and_label_effect_required",
        "raw_units_and_uncertainty_required",
        "healthy_human_context_required",
        "donor_disjoint_validation_required",
        "independent_heldout_study_required",
        "frozen_model_before_heldout_access_required",
    }
    required_false = {
        "automatic_stokes_einstein_conversion",
        "automatic_cell_line_transfer",
        "automatic_cross_species_transfer",
        "automatic_global_viscosity_multiplier",
        "automatic_diffusivity_activation",
        "automatic_crowding_law_activation",
        "automatic_reaction_coupling",
    }
    if any(gate.get(key) is not True for key in required_true) or any(
        gate.get(key) is not False for key in required_false
    ):
        raise IntracellularMobilityError("mobility gate escaped fail-closed state")
    if not isinstance(policy, dict) or policy.get("manual_primary_source_review_required") is not True:
        raise IntracellularMobilityError("mobility review policy changed")
    if any(
        policy.get(key) is not False
        for key in (
            "water_or_gfp_probe_may_stand_in_for_every_species",
            "one_probe_size_defines_crowding_law",
            "reported_mean_without_raw_curve_is_sufficient",
            "bulk_tissue_diffusion_equals_intracellular_phh_diffusion",
            "missing_mobility_means_immobile",
            "visual_crowder_points_are_measurements",
            "automatic_unit_conversion",
            "automatic_parameter_activation",
        )
    ):
        raise IntracellularMobilityError("mobility policy escaped fail-closed state")
    return payload


def _required_text(row: dict[str, str], field: str, row_number: int) -> str:
    value = row[field].strip()
    if not value or value.lower() == _NULL_TOKEN:
        raise IntracellularMobilityError(f"row {row_number}: {field} is required")
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
    positive: bool = False,
) -> float:
    raw = _required_text(row, field, row_number)
    try:
        value = float(raw)
    except ValueError as error:
        raise IntracellularMobilityError(f"row {row_number}: {field} must be numeric") from error
    if not math.isfinite(value):
        raise IntracellularMobilityError(f"row {row_number}: {field} must be finite")
    if positive and value <= 0:
        raise IntracellularMobilityError(f"row {row_number}: {field} must be positive")
    if nonnegative and value < 0:
        raise IntracellularMobilityError(f"row {row_number}: {field} must be non-negative")
    return value


def _optional_float(row: dict[str, str], field: str, row_number: int) -> float | None:
    raw = _optional_text(row, field)
    if raw is None:
        return None
    try:
        value = float(raw)
    except ValueError as error:
        raise IntracellularMobilityError(f"row {row_number}: {field} must be numeric") from error
    if not math.isfinite(value):
        raise IntracellularMobilityError(f"row {row_number}: {field} must be finite")
    return value


def _record_from_row(row: dict[str, str], row_number: int) -> IntracellularMobilityRecord:
    raw_index = _required_text(row, "observation_index", row_number)
    if not raw_index.isdigit():
        raise IntracellularMobilityError(f"row {row_number}: observation_index must be non-negative")
    required_text_fields = (
        "record_id", "target_species_id", "stage_id", "series_id", "donor_id",
        "split_role", "source_study_id", "source_locator", "species",
        "biological_system", "culture_format", "tissue_health_state", "liver_zone",
        "biological_replicate_id", "compartment", "subcompartment",
        "molecular_form", "label_or_probe_identity",
        "probe_hydrodynamic_radius_unit", "measurement_method",
        "independent_axis_name", "independent_unit", "observed_quantity",
        "observed_unit", "uncertainty_type", "assay_temperature_unit",
        "raw_artifact_path", "raw_artifact_sha256",
        "manual_primary_source_review_status",
    )
    values: dict[str, Any] = {
        field: _required_text(row, field, row_number) for field in required_text_fields
    }
    values.update(
        {
            "observation_index": int(raw_index),
            "probe_hydrodynamic_radius_value": _required_float(
                row, "probe_hydrodynamic_radius_value", row_number, positive=True
            ),
            "independent_value": _required_float(row, "independent_value", row_number),
            "observed_value": _required_float(row, "observed_value", row_number),
            "uncertainty_value": _required_float(
                row, "uncertainty_value", row_number, nonnegative=True
            ),
            "assay_temperature_value": _required_float(
                row, "assay_temperature_value", row_number
            ),
            "assay_ph": _required_float(row, "assay_ph", row_number),
        }
    )
    optional_text_fields = (
        "apparent_diffusivity_unit", "free_fraction_unit", "local_crowder_unit",
        "perturbation_identity", "perturbation_unit", "censoring_or_missingness",
    )
    values.update({field: _optional_text(row, field) for field in optional_text_fields})
    optional_float_fields = (
        "apparent_diffusivity_value", "diffusion_tensor_xx", "diffusion_tensor_yy",
        "diffusion_tensor_zz", "anomalous_exponent", "free_fraction_value",
        "local_crowder_value", "perturbation_value",
    )
    values.update(
        {
            field: _optional_float(row, field, row_number)
            for field in optional_float_fields
        }
    )
    if values["target_species_id"] not in _TARGET_SPECIES_IDS:
        raise IntracellularMobilityError(f"row {row_number}: unsupported target_species_id")
    if values["stage_id"] not in _REQUIRED_STAGE_IDS:
        raise IntracellularMobilityError(f"row {row_number}: unsupported stage_id")
    if values["split_role"] not in _ALLOWED_SPLIT_ROLES:
        raise IntracellularMobilityError(f"row {row_number}: unsupported split_role")
    if values["species"] != "Homo sapiens":
        raise IntracellularMobilityError(f"row {row_number}: species must be Homo sapiens")
    if not 0 <= values["assay_ph"] <= 14:
        raise IntracellularMobilityError(f"row {row_number}: assay_ph must be in [0, 14]")
    for value_field, unit_field in (
        ("apparent_diffusivity_value", "apparent_diffusivity_unit"),
        ("free_fraction_value", "free_fraction_unit"),
        ("local_crowder_value", "local_crowder_unit"),
        ("perturbation_value", "perturbation_unit"),
    ):
        if (values[value_field] is None) != (values[unit_field] is None):
            raise IntracellularMobilityError(
                f"row {row_number}: {value_field} and {unit_field} must be paired"
            )
    tensor_values = (
        values["diffusion_tensor_xx"],
        values["diffusion_tensor_yy"],
        values["diffusion_tensor_zz"],
    )
    if any(value is None for value in tensor_values) and any(
        value is not None for value in tensor_values
    ):
        raise IntracellularMobilityError(
            f"row {row_number}: diffusion tensor diagonal must be complete"
        )
    _resolve_artifact(
        values["raw_artifact_path"],
        values["raw_artifact_sha256"],
        label=f"raw mobility artifact row {row_number}",
    )
    return IntracellularMobilityRecord(**values)


def load_intracellular_mobility_observations(
    path: Path = DEFAULT_OBSERVATION_PATH,
) -> tuple[IntracellularMobilityRecord, ...]:
    contract = load_intracellular_mobility_contract()
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
            raise IntracellularMobilityError("intracellular mobility header changed")
        records = tuple(
            _record_from_row(row, row_number)
            for row_number, row in enumerate(reader, start=2)
        )
    record_ids = [record.record_id for record in records]
    if len(record_ids) != len(set(record_ids)):
        raise IntracellularMobilityError("mobility record_id values must be unique")
    donor_splits: dict[tuple[str, str], set[str]] = defaultdict(set)
    series: dict[tuple[str, str, str, str], list[IntracellularMobilityRecord]] = defaultdict(list)
    for record in records:
        donor_splits[record.donor_key].add(record.split_role)
        series[record.series_key].append(record)
    if any(len(splits) > 1 for splits in donor_splits.values()):
        raise IntracellularMobilityError("mobility donor leaks across dataset splits")
    for key, series_records in series.items():
        contexts = {
            (
                record.stage_id, record.compartment, record.subcompartment,
                record.molecular_form, record.label_or_probe_identity,
                record.measurement_method, record.independent_axis_name,
                record.independent_unit, record.observed_quantity,
                record.observed_unit,
            )
            for record in series_records
        }
        if len(contexts) != 1:
            raise IntracellularMobilityError(f"mobility series context changed within {key}")
        ordered = sorted(series_records, key=lambda record: record.observation_index)
        if [record.observation_index for record in ordered] != list(range(len(ordered))):
            raise IntracellularMobilityError(f"mobility series indices are not contiguous in {key}")
        if ordered[0].stage_id in _DYNAMIC_STAGE_IDS:
            if len(ordered) < 3:
                raise IntracellularMobilityError(
                    f"dynamic mobility series {key} needs at least three points"
                )
            if any(
                later.independent_value <= earlier.independent_value
                for earlier, later in zip(ordered, ordered[1:])
            ):
                raise IntracellularMobilityError(
                    f"dynamic mobility series {key} axis must increase strictly"
                )
    return records


def _assess_species(
    target_species_id: str,
    records: tuple[IntracellularMobilityRecord, ...],
) -> IntracellularMobilityAssessment:
    species_records = tuple(
        record for record in records if record.target_species_id == target_species_id
    )
    covered = tuple(
        stage_id
        for stage_id in _REQUIRED_STAGE_IDS
        if any(record.stage_id == stage_id for record in species_records)
    )
    missing = tuple(stage_id for stage_id in _REQUIRED_STAGE_IDS if stage_id not in covered)
    calibration = tuple(
        record for record in species_records if record.split_role != "independent_heldout"
    )
    heldout = tuple(
        record for record in species_records if record.split_role == "independent_heldout"
    )
    calibration_contexts = {
        (
            record.donor_key,
            record.compartment,
            record.subcompartment,
            record.molecular_form,
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
    ordered_dynamic_series = {
        record.series_key
        for record in species_records
        if record.stage_id in _DYNAMIC_STAGE_IDS
    }
    calibration_probe_sizes = {
        (record.probe_hydrodynamic_radius_value, record.probe_hydrodynamic_radius_unit)
        for record in calibration
        if record.stage_id in {
            "probe_scale_calibration",
            "local_crowding_abundance_field",
        }
    }
    size_resolved = (
        len(calibration_probe_sizes) >= 3
        and "local_crowding_abundance_field" in covered
    )
    blockers: list[str] = []
    if missing:
        blockers.append("one or more required mobility/crowding stages are missing")
    if not calibration_consistent:
        blockers.append("calibration stages do not share one donor, compartment and molecular form")
    if not donor_disjoint:
        blockers.append("donor-disjoint held-out validation is absent")
    if not study_disjoint:
        blockers.append("study-disjoint held-out validation is absent")
    if not size_resolved:
        blockers.append("same-context measurements across at least three probe sizes are absent")
    if any(
        record.manual_primary_source_review_status != "pass"
        for record in species_records
    ):
        blockers.append("manual primary-source review is incomplete")
    if any(
        "healthy" not in record.tissue_health_state.lower()
        and "non-diseased" not in record.tissue_health_state.lower()
        for record in species_records
    ):
        blockers.append("healthy/non-diseased PHH context is not explicit")
    structurally_complete = bool(species_records) and not blockers
    return IntracellularMobilityAssessment(
        target_species_id=target_species_id,
        covered_stage_ids=covered,
        missing_stage_ids=missing,
        record_count=len(species_records),
        donor_count=len({record.donor_key for record in species_records}),
        study_count=len({record.source_study_id for record in species_records}),
        ordered_dynamic_series_count=len(ordered_dynamic_series),
        calibration_context_consistent=calibration_consistent,
        donor_disjoint_heldout=donor_disjoint,
        study_disjoint_heldout=study_disjoint,
        size_resolved_crowding_chain=size_resolved,
        structurally_complete=structurally_complete,
        apparent_diffusivity_activation_allowed=False,
        crowding_law_activation_allowed=False,
        reaction_coupling_allowed=False,
        blockers=tuple(blockers)
        + ("explicit frozen-model promotion is required before numerical coupling",),
    )


def intracellular_mobility_intake_snapshot(
    observation_path: Path = DEFAULT_OBSERVATION_PATH,
) -> dict[str, object]:
    contract = load_intracellular_mobility_contract()
    records = load_intracellular_mobility_observations(observation_path)
    assessments = tuple(
        _assess_species(target_species_id, records)
        for target_species_id in _TARGET_SPECIES_IDS
    )
    return {
        "version": INTAKE_VERSION,
        "status": "contract_ready_no_species_mobility_or_crowding_law_authorized",
        "contract_id": contract["contract_id"],
        "contract_path": _display_path(CONTRACT_PATH),
        "contract_sha256": _sha256(CONTRACT_PATH),
        "delivery_path": _display_path(observation_path),
        "delivery_sha256": _sha256(observation_path) if observation_path.exists() else None,
        "expected_headers": [
            item["id"]
            for group in ("required_columns", "conditional_columns")
            for item in contract[group]
        ],
        "target_species_ids": list(_TARGET_SPECIES_IDS),
        "required_stage_ids": list(_REQUIRED_STAGE_IDS),
        "records": [asdict(record) for record in records],
        "assessments": [asdict(assessment) for assessment in assessments],
        "summary": {
            "required_field_count": len(contract["required_columns"]),
            "conditional_field_count": len(contract["conditional_columns"]),
            "target_species_count": len(_TARGET_SPECIES_IDS),
            "required_stage_count_per_species": len(_REQUIRED_STAGE_IDS),
            "required_stage_slot_count": len(_TARGET_SPECIES_IDS) * len(_REQUIRED_STAGE_IDS),
            "record_count": len(records),
            "covered_stage_slot_count": sum(
                len(assessment.covered_stage_ids) for assessment in assessments
            ),
            "structurally_complete_species_count": sum(
                assessment.structurally_complete for assessment in assessments
            ),
            "size_resolved_crowding_chain_count": sum(
                assessment.size_resolved_crowding_chain for assessment in assessments
            ),
            "apparent_diffusivity_authorized_species_count": 0,
            "crowding_law_authorized_species_count": 0,
            "reaction_coupled_species_count": 0,
            "global_viscosity_multiplier_count": 0,
        },
        "gates": {
            "raw_species_resolved_observations_required": True,
            "probe_size_and_molecular_form_required": True,
            "donor_and_study_disjoint_heldout_required": True,
            "automatic_stokes_einstein_conversion": False,
            "automatic_global_viscosity_multiplier": False,
            "automatic_diffusivity_activation": False,
            "automatic_crowding_law_activation": False,
            "automatic_reaction_coupling": False,
        },
        "limitations": [
            "No healthy-PHH species-specific mobility observation has been delivered.",
            "Water, GFP, cell-line and non-human probe measurements cannot stand in for every reaction species.",
            "A single apparent viscosity cannot represent size-, compartment-, binding- and timescale-dependent mobility.",
            "Visual protein/crowder points are not local abundance or obstacle fields.",
            "No diffusivity, crowding law or reaction coupling is activated automatically.",
        ],
    }


__all__ = [
    "CONTRACT_PATH",
    "DEFAULT_OBSERVATION_PATH",
    "IntracellularMobilityAssessment",
    "IntracellularMobilityError",
    "IntracellularMobilityRecord",
    "intracellular_mobility_intake_snapshot",
    "load_intracellular_mobility_contract",
    "load_intracellular_mobility_observations",
]
