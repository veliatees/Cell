"""PHH d8-taurocholate biliary-excretion observation operator.

BEI is a paired-condition assay output.  It is not a direct BSEP turnover
measurement and cannot separate uptake, intracellular handling, canalicular
geometry, or export kinetics.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from math import isfinite
from pathlib import Path

from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain


DATE_VERIFIED = "2026-07-14"
VERSION = "phh_biliary_excretion_v1"
SCHEMA_VERSION = "cell.phh-biliary-excretion.v1"
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "phh_baseline"
    / "curated"
    / "peng2025_phh_biliary_excretion.v1.json"
)
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


PHH_BILIARY_EXCRETION_SOURCES: dict[str, SourceReference] = {
    "peng2025_phh_quality_attributes": SourceReference(
        id="peng2025_phh_quality_attributes",
        title="The validation of quality attributes in Primary Human Hepatocytes Standard",
        url="https://doi.org/10.1186/s13619-025-00258-6",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Table S7 reports d8-taurocholate BEI for five commercial PHH batches after five "
            "days of collagen-I/Matrigel sandwich culture."
        ),
    ),
    "peng2022_phh_requirements_standard": SourceReference(
        id="peng2022_phh_requirements_standard",
        title="Requirments for primary human hepatocyte",
        url="https://doi.org/10.1111/cpr.13147",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Published CSCB standard source for the d8-TCA BEI >=30 percent PHH product criterion.",
    ),
}


@dataclass(frozen=True)
class BeiSourceArtifact:
    source_id: str
    supplement_filename: str
    supplement_md5: str
    supplement_sha256: str
    source_tables: tuple[str, ...]


@dataclass(frozen=True)
class BeiAssayContract:
    species: str
    biological_system: str
    culture_format: str
    seeded_cells_per_well: int
    culture_medium: str
    matrigel_percent: float
    culture_duration_days: int
    temperature_c: float
    co2_percent: float
    preincubation_duration_min: float
    probe: str
    probe_concentration_uM: float
    probe_incubation_duration_min: float
    paired_conditions: tuple[str, ...]
    instrument: str
    measured_quantity: str
    reported_unit: str


@dataclass(frozen=True)
class BeiMeasurementContract:
    required_inputs: tuple[str, ...]
    input_unit_constraint: str
    denominator_constraint: str
    operator_formula: str
    output_quantity: str
    output_unit: str


@dataclass(frozen=True)
class BeiBatchObservation:
    batch_id: str
    bei_percent: float


@dataclass(frozen=True)
class BeiProductQualityCriterion:
    authority: str
    source_id: str
    threshold_percent: float
    comparison: str
    role: str
    may_be_used_as_model_pass_threshold: bool


@dataclass(frozen=True)
class BeiQuantityAudit:
    id: str
    identified_from_current_assay: bool
    mechanism_specific: bool
    may_fit_kinetic_parameter: bool


@dataclass(frozen=True)
class BeiRequiredMeasurement:
    id: str
    requirements: tuple[str, ...]
    purpose: str


@dataclass(frozen=True)
class PhhBiliaryExcretionState:
    version: str
    status: str
    date_verified: str
    source_artifact: BeiSourceArtifact
    assay_contract: BeiAssayContract
    measurement_contract: BeiMeasurementContract
    batch_records: tuple[BeiBatchObservation, ...]
    product_quality_criterion: BeiProductQualityCriterion
    quantity_audit: tuple[BeiQuantityAudit, ...]
    required_measurements: tuple[BeiRequiredMeasurement, ...]
    individual_batch_table_loaded: bool
    measurement_operator_ready: bool
    raw_paired_condition_values_loaded: bool
    transporter_specific_rate_fit_ready: bool
    canalicular_geometry_coupling_ready: bool
    automatic_state_coupling: bool
    model_pass_threshold_defined: bool
    predictive_ready: bool
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


@dataclass(frozen=True)
class BeiPairedConditionInput:
    prediction_id: str
    model_id: str
    model_artifact_sha256: str
    measurement_contract_version: str
    species: str
    biological_system: str
    culture_format: str
    culture_duration_days: int
    probe: str
    probe_concentration_uM: float
    probe_incubation_duration_min: float
    input_unit: str
    a_ca: float
    a_ca_free: float


@dataclass(frozen=True)
class BeiPairedInputAudit:
    context_match: bool
    input_unit_present: bool
    values_finite_nonnegative: bool
    denominator_positive: bool
    artifact_provenance_present: bool
    exact_input_match: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class BeiMeasurementProjection:
    status: str
    input_audit: BeiPairedInputAudit
    bei_percent: float
    published_batch_span_classification: str
    fitted_parameter_count: int
    pass_fail_assigned: bool
    may_drive_cell_state: bool

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain one JSON object")
    return payload


def build_phh_biliary_excretion(data_path: Path = DATA_PATH) -> PhhBiliaryExcretionState:
    payload = _load_json(data_path)
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported PHH biliary-excretion schema")
    artifact_raw = payload["source_artifact"]
    assay_raw = payload["assay_contract"]
    measurement_raw = payload["measurement_contract"]
    criterion_raw = payload["product_quality_criterion"]
    gates = payload["gates"]
    if not all(isinstance(item, dict) for item in (artifact_raw, assay_raw, measurement_raw, criterion_raw, gates)):
        raise ValueError("PHH biliary-excretion object payload is malformed")
    batches_raw = payload.get("batch_records")
    quantities_raw = payload.get("quantity_audit")
    required_raw = payload.get("required_measurements")
    if not all(isinstance(item, list) for item in (batches_raw, quantities_raw, required_raw)):
        raise ValueError("PHH biliary-excretion list payload is malformed")

    state = PhhBiliaryExcretionState(
        version=VERSION,
        status=str(payload["status"]),
        date_verified=str(payload["date_verified"]),
        source_artifact=BeiSourceArtifact(
            source_id=str(artifact_raw["source_id"]),
            supplement_filename=str(artifact_raw["supplement_filename"]),
            supplement_md5=str(artifact_raw["supplement_md5"]),
            supplement_sha256=str(artifact_raw["supplement_sha256"]),
            source_tables=tuple(str(item) for item in artifact_raw["source_tables"]),  # type: ignore[index]
        ),
        assay_contract=BeiAssayContract(
            species=str(assay_raw["species"]),
            biological_system=str(assay_raw["biological_system"]),
            culture_format=str(assay_raw["culture_format"]),
            seeded_cells_per_well=int(assay_raw["seeded_cells_per_well"]),
            culture_medium=str(assay_raw["culture_medium"]),
            matrigel_percent=float(assay_raw["matrigel_percent"]),
            culture_duration_days=int(assay_raw["culture_duration_days"]),
            temperature_c=float(assay_raw["temperature_c"]),
            co2_percent=float(assay_raw["co2_percent"]),
            preincubation_duration_min=float(assay_raw["preincubation_duration_min"]),
            probe=str(assay_raw["probe"]),
            probe_concentration_uM=float(assay_raw["probe_concentration_uM"]),
            probe_incubation_duration_min=float(assay_raw["probe_incubation_duration_min"]),
            paired_conditions=tuple(str(item) for item in assay_raw["paired_conditions"]),  # type: ignore[index]
            instrument=str(assay_raw["instrument"]),
            measured_quantity=str(assay_raw["measured_quantity"]),
            reported_unit=str(assay_raw["reported_unit"]),
        ),
        measurement_contract=BeiMeasurementContract(
            required_inputs=tuple(str(item) for item in measurement_raw["required_inputs"]),  # type: ignore[index]
            input_unit_constraint=str(measurement_raw["input_unit_constraint"]),
            denominator_constraint=str(measurement_raw["denominator_constraint"]),
            operator_formula=str(measurement_raw["operator_formula"]),
            output_quantity=str(measurement_raw["output_quantity"]),
            output_unit=str(measurement_raw["output_unit"]),
        ),
        batch_records=tuple(
            BeiBatchObservation(batch_id=str(item["batch_id"]), bei_percent=float(item["bei_percent"]))
            for item in batches_raw
            if isinstance(item, dict)
        ),
        product_quality_criterion=BeiProductQualityCriterion(
            authority=str(criterion_raw["authority"]),
            source_id=str(criterion_raw["source_id"]),
            threshold_percent=float(criterion_raw["threshold_percent"]),
            comparison=str(criterion_raw["comparison"]),
            role=str(criterion_raw["role"]),
            may_be_used_as_model_pass_threshold=bool(criterion_raw["may_be_used_as_model_pass_threshold"]),
        ),
        quantity_audit=tuple(
            BeiQuantityAudit(
                id=str(item["id"]),
                identified_from_current_assay=bool(item["identified_from_current_assay"]),
                mechanism_specific=bool(item["mechanism_specific"]),
                may_fit_kinetic_parameter=bool(item["may_fit_kinetic_parameter"]),
            )
            for item in quantities_raw
            if isinstance(item, dict)
        ),
        required_measurements=tuple(
            BeiRequiredMeasurement(
                id=str(item["id"]),
                requirements=tuple(str(value) for value in item["requirements"]),  # type: ignore[index]
                purpose=str(item["purpose"]),
            )
            for item in required_raw
            if isinstance(item, dict)
        ),
        individual_batch_table_loaded=bool(gates["individual_batch_table_loaded"]),
        measurement_operator_ready=bool(gates["measurement_operator_ready"]),
        raw_paired_condition_values_loaded=bool(gates["raw_paired_condition_values_loaded"]),
        transporter_specific_rate_fit_ready=bool(gates["transporter_specific_rate_fit_ready"]),
        canalicular_geometry_coupling_ready=bool(gates["canalicular_geometry_coupling_ready"]),
        automatic_state_coupling=bool(gates["automatic_state_coupling"]),
        model_pass_threshold_defined=bool(gates["model_pass_threshold_defined"]),
        predictive_ready=bool(gates["predictive_ready"]),
        source_ids=tuple(str(item) for item in payload["source_ids"]),  # type: ignore[index]
        limitations=tuple(str(item) for item in payload["limitations"]),  # type: ignore[index]
    )
    validate_phh_biliary_excretion(state)
    return state


def validate_phh_biliary_excretion(state: PhhBiliaryExcretionState) -> None:
    assay = state.assay_contract
    artifact = state.source_artifact
    contract = state.measurement_contract
    criterion = state.product_quality_criterion
    if state.version != VERSION or state.date_verified != DATE_VERIFIED:
        raise ValueError("PHH biliary-excretion version or verification date changed")
    if (
        artifact.source_id != "peng2025_phh_quality_attributes"
        or artifact.supplement_filename != "13619_2025_258_MOESM1_ESM.docx"
        or artifact.supplement_md5 != "cf6103b084c236f3fedf2f30e548559e"
        or artifact.supplement_sha256 != "deeb835fe82d7e0e883447268354b9abb8f3ca4950639be3b68b802d3c6183bf"
        or artifact.source_tables != ("Table S6", "Table S7")
    ):
        raise ValueError("PHH BEI supplement provenance changed")
    if (
        assay.species != "Homo sapiens"
        or assay.biological_system != "cryopreserved_commercial_primary_human_hepatocytes"
        or assay.culture_format != "collagen_I_matrigel_sandwich_24_well"
        or assay.seeded_cells_per_well != 250_000
        or assay.matrigel_percent != 2.0
        or assay.culture_duration_days != 5
        or assay.temperature_c != 37.0
        or assay.co2_percent != 5.0
        or assay.preincubation_duration_min != 15.0
        or assay.probe != "d8_taurocholate"
        or assay.probe_concentration_uM != 5.0
        or assay.probe_incubation_duration_min != 15.0
        or assay.paired_conditions != ("calcium_containing_HBSS", "calcium_free_HBSS")
        or assay.reported_unit != "percent"
    ):
        raise ValueError("PHH BEI assay contract changed")
    if (
        contract.required_inputs != ("A_Ca", "A_CaFree")
        or contract.input_unit_constraint != "same_nonnegative_concentration_unit"
        or contract.denominator_constraint != "A_Ca_must_be_positive"
        or contract.operator_formula != "BEI_percent=(A_Ca-A_CaFree)/A_Ca*100"
        or contract.output_quantity != "biliary_excretion_index"
        or contract.output_unit != assay.reported_unit
    ):
        raise ValueError("PHH BEI measurement operator changed")
    expected_records = (
        ("PHH393", 27.2),
        ("PHH396", 27.5),
        ("PHH416", 25.7),
        ("PHH005", 62.0),
        ("PHH910", 59.0),
    )
    if tuple((record.batch_id, record.bei_percent) for record in state.batch_records) != expected_records:
        raise ValueError("PHH BEI batch table changed")
    if any(not isfinite(record.bei_percent) for record in state.batch_records):
        raise ValueError("PHH BEI values must be finite")
    if (
        criterion.authority != "T_CSCB_0008_2021_group_standard"
        or criterion.source_id != "peng2022_phh_requirements_standard"
        or criterion.threshold_percent != 30.0
        or criterion.comparison != "greater_than_or_equal"
        or criterion.may_be_used_as_model_pass_threshold
    ):
        raise ValueError("PHH BEI product criterion was promoted or changed")
    expected_quantity_ids = {
        "paired_condition_BEI",
        "basolateral_d8_TCA_uptake_rate",
        "BSEP_canalicular_export_rate",
        "intracellular_d8_TCA_binding_or_loss_rate",
        "canalicular_network_volume_and_sealing",
    }
    if {item.id for item in state.quantity_audit} != expected_quantity_ids:
        raise ValueError("PHH BEI identifiability audit is incomplete")
    identified = [item for item in state.quantity_audit if item.identified_from_current_assay]
    mechanisms = [item for item in state.quantity_audit if item.mechanism_specific]
    if (
        len(identified) != 1
        or identified[0].id != "paired_condition_BEI"
        or len(mechanisms) != 4
        or any(item.identified_from_current_assay or item.may_fit_kinetic_parameter for item in mechanisms)
    ):
        raise ValueError("PHH BEI endpoint was used to identify a hidden mechanism")
    if {item.id for item in state.required_measurements} != {
        "paired_raw_d8_TCA_records",
        "transporter_resolved_flux",
        "canalicular_geometry_and_barrier",
    }:
        raise ValueError("PHH BEI required-measurement set is incomplete")
    if set(state.source_ids) != {"peng2025_phh_quality_attributes", "peng2022_phh_requirements_standard"} or not set(state.source_ids) <= set(PHH_BILIARY_EXCRETION_SOURCES):
        raise ValueError("PHH BEI source registry changed")
    if (
        not state.individual_batch_table_loaded
        or not state.measurement_operator_ready
        or state.raw_paired_condition_values_loaded
        or state.transporter_specific_rate_fit_ready
        or state.canalicular_geometry_coupling_ready
        or state.automatic_state_coupling
        or state.model_pass_threshold_defined
        or state.predictive_ready
    ):
        raise ValueError("PHH BEI readiness gates exceeded the evidence")
    if len(state.limitations) < 5:
        raise ValueError("PHH BEI limitations are incomplete")


def calculate_bei_percent(a_ca: float, a_ca_free: float) -> float:
    if not all(isfinite(value) and value >= 0.0 for value in (a_ca, a_ca_free)):
        raise ValueError("paired d8-TCA values must be finite and non-negative")
    if a_ca <= 0.0:
        raise ValueError("A_Ca must be positive")
    return (a_ca - a_ca_free) / a_ca * 100.0


def audit_bei_paired_input(
    state: PhhBiliaryExcretionState,
    paired_input: BeiPairedConditionInput,
) -> BeiPairedInputAudit:
    validate_phh_biliary_excretion(state)
    assay = state.assay_contract
    context_match = (
        paired_input.measurement_contract_version == state.version
        and paired_input.species == assay.species
        and paired_input.biological_system == assay.biological_system
        and paired_input.culture_format == assay.culture_format
        and paired_input.culture_duration_days == assay.culture_duration_days
        and paired_input.probe == assay.probe
        and paired_input.probe_concentration_uM == assay.probe_concentration_uM
        and paired_input.probe_incubation_duration_min == assay.probe_incubation_duration_min
    )
    input_unit_present = bool(paired_input.input_unit.strip())
    values_finite_nonnegative = all(
        isfinite(value) and value >= 0.0
        for value in (paired_input.a_ca, paired_input.a_ca_free)
    )
    denominator_positive = isfinite(paired_input.a_ca) and paired_input.a_ca > 0.0
    artifact_provenance_present = bool(paired_input.prediction_id and paired_input.model_id) and bool(
        SHA256_PATTERN.fullmatch(paired_input.model_artifact_sha256)
    )
    checks = {
        "measurement contract or biological context differs": context_match,
        "the shared paired-condition concentration unit is missing": input_unit_present,
        "one or more paired-condition values is non-finite or negative": values_finite_nonnegative,
        "A_Ca is not positive": denominator_positive,
        "prediction/model identifier or SHA-256 provenance is missing": artifact_provenance_present,
    }
    blockers = tuple(message for message, passed in checks.items() if not passed)
    return BeiPairedInputAudit(
        context_match=context_match,
        input_unit_present=input_unit_present,
        values_finite_nonnegative=values_finite_nonnegative,
        denominator_positive=denominator_positive,
        artifact_provenance_present=artifact_provenance_present,
        exact_input_match=not blockers,
        blockers=blockers,
    )


def project_paired_d8_tca_to_bei(
    state: PhhBiliaryExcretionState,
    paired_input: BeiPairedConditionInput,
) -> BeiMeasurementProjection:
    audit = audit_bei_paired_input(state, paired_input)
    if not audit.exact_input_match:
        raise ValueError("paired d8-TCA input does not match the assay: " + "; ".join(audit.blockers))
    bei = calculate_bei_percent(paired_input.a_ca, paired_input.a_ca_free)
    observed_values = [record.bei_percent for record in state.batch_records]
    low, high = min(observed_values), max(observed_values)
    if bei < low:
        classification = "below_published_batch_span"
    elif bei > high:
        classification = "above_published_batch_span"
    else:
        classification = "within_published_batch_span"
    return BeiMeasurementProjection(
        status="same_format_diagnostic_no_pass_threshold",
        input_audit=audit,
        bei_percent=bei,
        published_batch_span_classification=classification,
        fitted_parameter_count=0,
        pass_fail_assigned=False,
        may_drive_cell_state=False,
    )


def phh_biliary_excretion_snapshot() -> dict[str, object]:
    state = build_phh_biliary_excretion()
    values = [record.bei_percent for record in state.batch_records]
    mechanisms = [item for item in state.quantity_audit if item.mechanism_specific]
    payload = state.to_dict()
    payload["summary"] = {
        "batch_count": len(state.batch_records),
        "published_numeric_endpoint_count": len(state.batch_records),
        "bei_low_percent": min(values),
        "bei_high_percent": max(values),
        "source_product_criterion_percent": state.product_quality_criterion.threshold_percent,
        "batch_count_at_or_above_source_criterion": sum(
            value >= state.product_quality_criterion.threshold_percent for value in values
        ),
        "mechanism_specific_quantity_count": len(mechanisms),
        "mechanism_specific_quantity_identified_count": sum(
            item.identified_from_current_assay for item in mechanisms
        ),
        "raw_paired_condition_record_count": 0,
        "exact_model_prediction_count": 0,
        "pass_fail_count": 0,
    }
    return payload
