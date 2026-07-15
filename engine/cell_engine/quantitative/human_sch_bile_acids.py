"""Endogenous bile-acid compartments in human sandwich-cultured hepatocytes.

The source table is retained as a day-7, four-donor in-vitro endpoint. Its
paired-buffer BEI values are aggregates of experiment-level ratios and are not
reconstructed from group-mean concentrations. No value initializes the healthy
in-vivo cell or identifies transporter-specific kinetics.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from math import isclose, isfinite
from pathlib import Path

from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain


DATE_VERIFIED = "2026-07-14"
VERSION = "human_sch_bile_acids_v1"
SCHEMA_VERSION = "cell.human-sch-bile-acid-compartments.v1"
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "phh_baseline"
    / "curated"
    / "marion2013_human_sch_bile_acids.v1.json"
)


HUMAN_SCH_BILE_ACID_SOURCES: dict[str, SourceReference] = {
    "marion2013_human_sch_bile_acids": SourceReference(
        id="marion2013_human_sch_bile_acids",
        title="Endogenous Bile Acid Disposition in Rat and Human Sandwich-Cultured Hepatocytes",
        url="https://doi.org/10.1016/j.taap.2012.02.002",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Table 4 reports endogenous bile acids and experiment-level BEI aggregates "
            "from four human sandwich-cultured hepatocyte donors."
        ),
    )
}


ANALYTES = ("TCA", "GCA", "TCDCA", "GCDCA", "Total")
CONDITION_IDS = ("vehicle_control", "troglitazone_10_uM")


@dataclass(frozen=True)
class SchSourceArtifact:
    source_id: str
    title: str
    doi: str
    pmcid: str
    pmid: str
    url: str
    source_location: str


@dataclass(frozen=True)
class SchDonor:
    id: str
    age_years: int
    sex: str
    race_as_reported: str
    smoking_status: str


@dataclass(frozen=True)
class SchAssayContract:
    species: str
    biological_system: str
    plate_format: str
    overlay: str
    overlay_concentration_mg_per_mL: float
    treatment_day: int
    sampling_day: int
    treatment_duration_h: float
    medium_volume_mL_per_well: float
    representative_protein_mg_per_well: float
    estimated_intracellular_volume_uL_per_well: float
    instrument: str
    donor_experiment_count: int
    uncertainty_type: str
    cell_and_bile_replication: str
    medium_replication: str
    below_quantification_policy_in_source: str
    below_quantification_proxy_is_biological_zero: bool


@dataclass(frozen=True)
class SchMeasurementContract:
    concentration_unit: str
    bei_unit: str
    cells_plus_bile_definition: str
    cells_definition: str
    medium_definition: str
    bei_formula_for_matched_raw_experiment: str
    published_bei_aggregation: str
    may_reconstruct_published_bei_from_group_mean_concentrations: bool
    cells_plus_bile_and_cells_normalization: str
    difference_is_true_canalicular_concentration: bool


@dataclass(frozen=True)
class SchBileAcidRecord:
    analyte: str
    cells_plus_bile_mean_uM: float
    cells_plus_bile_sd_uM: float
    cells_mean_uM: float
    cells_sd_uM: float
    medium_mean_uM: float
    medium_sd_uM: float
    bei_mean_percent: float | None
    bei_sd_percent: float | None


@dataclass(frozen=True)
class SchCondition:
    id: str
    treatment: str
    records: tuple[SchBileAcidRecord, ...]


@dataclass(frozen=True)
class SchRequiredMeasurement:
    id: str
    requirements: tuple[str, ...]
    purpose: str


@dataclass(frozen=True)
class HumanSchBileAcidState:
    version: str
    status: str
    date_verified: str
    source_artifact: SchSourceArtifact
    donors: tuple[SchDonor, ...]
    assay_contract: SchAssayContract
    measurement_contract: SchMeasurementContract
    conditions: tuple[SchCondition, ...]
    source_consistency_notes: tuple[str, ...]
    required_measurements: tuple[SchRequiredMeasurement, ...]
    table4_numeric_records_loaded: bool
    aggregate_measurement_contract_ready: bool
    raw_donor_records_loaded: bool
    analyte_LLOQ_loaded: bool
    true_canalicular_concentration_ready: bool
    kinetic_parameter_fit_ready: bool
    healthy_in_vivo_initialization_ready: bool
    automatic_state_coupling: bool
    model_pass_threshold_defined: bool
    predictive_ready: bool
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain one JSON object")
    return payload


def _optional_float(value: object) -> float | None:
    return None if value is None else float(value)


def calculate_matched_raw_bei_percent(
    accumulation_standard_buffer: float,
    accumulation_calcium_free_buffer: float,
) -> float:
    """Calculate BEI only for a matched raw experiment-level pair."""

    if not all(
        isfinite(value) and value >= 0.0
        for value in (accumulation_standard_buffer, accumulation_calcium_free_buffer)
    ):
        raise ValueError("matched accumulation values must be finite and non-negative")
    if accumulation_standard_buffer <= 0.0:
        raise ValueError("standard-buffer accumulation must be positive")
    return (
        (accumulation_standard_buffer - accumulation_calcium_free_buffer)
        / accumulation_standard_buffer
        * 100.0
    )


def build_human_sch_bile_acids(data_path: Path = DATA_PATH) -> HumanSchBileAcidState:
    payload = _load_json(data_path)
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported human SCH bile-acid schema")
    artifact_raw = payload["source_artifact"]
    assay_raw = payload["assay_contract"]
    measurement_raw = payload["measurement_contract"]
    donors_raw = payload["donors"]
    conditions_raw = payload["conditions"]
    required_raw = payload["required_measurements"]
    gates = payload["gates"]
    if not all(
        isinstance(item, dict)
        for item in (artifact_raw, assay_raw, measurement_raw, gates)
    ) or not all(
        isinstance(item, list) for item in (donors_raw, conditions_raw, required_raw)
    ):
        raise ValueError("human SCH bile-acid payload is malformed")

    conditions: list[SchCondition] = []
    for condition_raw in conditions_raw:
        if not isinstance(condition_raw, dict) or not isinstance(
            condition_raw.get("records"), list
        ):
            raise ValueError("human SCH condition is malformed")
        conditions.append(
            SchCondition(
                id=str(condition_raw["id"]),
                treatment=str(condition_raw["treatment"]),
                records=tuple(
                    SchBileAcidRecord(
                        analyte=str(item["analyte"]),
                        cells_plus_bile_mean_uM=float(item["cells_plus_bile_mean_uM"]),
                        cells_plus_bile_sd_uM=float(item["cells_plus_bile_sd_uM"]),
                        cells_mean_uM=float(item["cells_mean_uM"]),
                        cells_sd_uM=float(item["cells_sd_uM"]),
                        medium_mean_uM=float(item["medium_mean_uM"]),
                        medium_sd_uM=float(item["medium_sd_uM"]),
                        bei_mean_percent=_optional_float(item["bei_mean_percent"]),
                        bei_sd_percent=_optional_float(item["bei_sd_percent"]),
                    )
                    for item in condition_raw["records"]
                    if isinstance(item, dict)
                ),
            )
        )

    state = HumanSchBileAcidState(
        version=VERSION,
        status=str(payload["status"]),
        date_verified=str(payload["date_verified"]),
        source_artifact=SchSourceArtifact(
            source_id=str(artifact_raw["source_id"]),
            title=str(artifact_raw["title"]),
            doi=str(artifact_raw["doi"]),
            pmcid=str(artifact_raw["pmcid"]),
            pmid=str(artifact_raw["pmid"]),
            url=str(artifact_raw["url"]),
            source_location=str(artifact_raw["source_location"]),
        ),
        donors=tuple(
            SchDonor(
                id=str(item["id"]),
                age_years=int(item["age_years"]),
                sex=str(item["sex"]),
                race_as_reported=str(item["race_as_reported"]),
                smoking_status=str(item["smoking_status"]),
            )
            for item in donors_raw
            if isinstance(item, dict)
        ),
        assay_contract=SchAssayContract(
            species=str(assay_raw["species"]),
            biological_system=str(assay_raw["biological_system"]),
            plate_format=str(assay_raw["plate_format"]),
            overlay=str(assay_raw["overlay"]),
            overlay_concentration_mg_per_mL=float(
                assay_raw["overlay_concentration_mg_per_mL"]
            ),
            treatment_day=int(assay_raw["treatment_day"]),
            sampling_day=int(assay_raw["sampling_day"]),
            treatment_duration_h=float(assay_raw["treatment_duration_h"]),
            medium_volume_mL_per_well=float(assay_raw["medium_volume_mL_per_well"]),
            representative_protein_mg_per_well=float(
                assay_raw["representative_protein_mg_per_well"]
            ),
            estimated_intracellular_volume_uL_per_well=float(
                assay_raw["estimated_intracellular_volume_uL_per_well"]
            ),
            instrument=str(assay_raw["instrument"]),
            donor_experiment_count=int(assay_raw["donor_experiment_count"]),
            uncertainty_type=str(assay_raw["uncertainty_type"]),
            cell_and_bile_replication=str(assay_raw["cell_and_bile_replication"]),
            medium_replication=str(assay_raw["medium_replication"]),
            below_quantification_policy_in_source=str(
                assay_raw["below_quantification_policy_in_source"]
            ),
            below_quantification_proxy_is_biological_zero=bool(
                assay_raw["below_quantification_proxy_is_biological_zero"]
            ),
        ),
        measurement_contract=SchMeasurementContract(
            concentration_unit=str(measurement_raw["concentration_unit"]),
            bei_unit=str(measurement_raw["bei_unit"]),
            cells_plus_bile_definition=str(measurement_raw["cells_plus_bile_definition"]),
            cells_definition=str(measurement_raw["cells_definition"]),
            medium_definition=str(measurement_raw["medium_definition"]),
            bei_formula_for_matched_raw_experiment=str(
                measurement_raw["bei_formula_for_matched_raw_experiment"]
            ),
            published_bei_aggregation=str(measurement_raw["published_bei_aggregation"]),
            may_reconstruct_published_bei_from_group_mean_concentrations=bool(
                measurement_raw[
                    "may_reconstruct_published_bei_from_group_mean_concentrations"
                ]
            ),
            cells_plus_bile_and_cells_normalization=str(
                measurement_raw["cells_plus_bile_and_cells_normalization"]
            ),
            difference_is_true_canalicular_concentration=bool(
                measurement_raw["difference_is_true_canalicular_concentration"]
            ),
        ),
        conditions=tuple(conditions),
        source_consistency_notes=tuple(
            str(item) for item in payload["source_consistency_notes"]
        ),
        required_measurements=tuple(
            SchRequiredMeasurement(
                id=str(item["id"]),
                requirements=tuple(str(value) for value in item["requirements"]),
                purpose=str(item["purpose"]),
            )
            for item in required_raw
            if isinstance(item, dict)
        ),
        table4_numeric_records_loaded=bool(gates["table4_numeric_records_loaded"]),
        aggregate_measurement_contract_ready=bool(
            gates["aggregate_measurement_contract_ready"]
        ),
        raw_donor_records_loaded=bool(gates["raw_donor_records_loaded"]),
        analyte_LLOQ_loaded=bool(gates["analyte_LLOQ_loaded"]),
        true_canalicular_concentration_ready=bool(
            gates["true_canalicular_concentration_ready"]
        ),
        kinetic_parameter_fit_ready=bool(gates["kinetic_parameter_fit_ready"]),
        healthy_in_vivo_initialization_ready=bool(
            gates["healthy_in_vivo_initialization_ready"]
        ),
        automatic_state_coupling=bool(gates["automatic_state_coupling"]),
        model_pass_threshold_defined=bool(gates["model_pass_threshold_defined"]),
        predictive_ready=bool(gates["predictive_ready"]),
        source_ids=tuple(str(item) for item in payload["source_ids"]),
        limitations=tuple(str(item) for item in payload["limitations"]),
    )
    validate_human_sch_bile_acids(state)
    return state


def validate_human_sch_bile_acids(state: HumanSchBileAcidState) -> None:
    artifact = state.source_artifact
    assay = state.assay_contract
    contract = state.measurement_contract
    if state.version != VERSION or state.date_verified != DATE_VERIFIED:
        raise ValueError("human SCH bile-acid version or verification date changed")
    if (
        artifact.source_id != "marion2013_human_sch_bile_acids"
        or artifact.doi != "10.1016/j.taap.2012.02.002"
        or artifact.pmcid != "PMC3679176"
        or artifact.pmid != "22342602"
        or artifact.source_location != "Table 4"
    ):
        raise ValueError("human SCH source provenance changed")
    if (
        assay.species != "Homo sapiens"
        or assay.biological_system != "primary_human_sandwich_cultured_hepatocytes"
        or assay.overlay_concentration_mg_per_mL != 0.25
        or assay.treatment_day != 6
        or assay.sampling_day != 7
        or assay.treatment_duration_h != 24.0
        or assay.medium_volume_mL_per_well != 1.5
        or assay.representative_protein_mg_per_well != 0.9
        or assay.estimated_intracellular_volume_uL_per_well != 6.79
        or assay.donor_experiment_count != 4
        or assay.below_quantification_policy_in_source != "assigned_proxy_zero"
        or assay.below_quantification_proxy_is_biological_zero
    ):
        raise ValueError("human SCH assay contract changed")
    expected_donors = {
        ("HU0803", 42, "male"),
        ("HU1067", 61, "male"),
        ("HU1184", 73, "female"),
        ("HU1191", 19, "male"),
    }
    if {(item.id, item.age_years, item.sex) for item in state.donors} != expected_donors:
        raise ValueError("human SCH donor table changed")
    if (
        contract.concentration_unit != "uM"
        or contract.bei_unit != "percent"
        or contract.may_reconstruct_published_bei_from_group_mean_concentrations
        or contract.difference_is_true_canalicular_concentration
        or contract.published_bei_aggregation
        != "mean_and_SD_of_experiment_level_BEI_values"
    ):
        raise ValueError("human SCH measurement semantics changed")
    by_condition = {item.id: item for item in state.conditions}
    if tuple(by_condition) != CONDITION_IDS:
        raise ValueError("human SCH condition table changed")
    expected = {
        "vehicle_control": {
            "TCA": (0.703, 0.408, 0.391, 0.189, 0.010, 0.010, 41.7, 16.2),
            "GCA": (136.0, 112.0, 78.7, 64.1, 8.70, 12.7, 40.4, 11.9),
            "TCDCA": (0.876, 0.249, 0.666, 0.151, 0.002, 0.003, 21.8, 14.3),
            "GCDCA": (142.0, 130.0, 104.0, 91.0, 0.891, 1.23, 24.2, 8.81),
            "Total": (281.0, 85.7, 183.0, 55.6, 9.61, 6.36, None, None),
        },
        "troglitazone_10_uM": {
            "TCA": (0.334, 0.179, 0.187, 0.141, 0.008, 0.008, 45.6, 39.7),
            "GCA": (59.0, 46.0, 32.4, 26.9, 6.59, 8.29, 38.5, 26.0),
            "TCDCA": (0.469, 0.030, 0.432, 0.061, 0.003, 0.002, 9.45, 12.3),
            "GCDCA": (73.8, 70.1, 63.4, 62.4, 0.706, 0.784, 17.4, 18.2),
            "Total": (134.0, 41.9, 96.5, 34.0, 7.31, 4.17, None, None),
        },
    }
    for condition_id, condition in by_condition.items():
        if tuple(record.analyte for record in condition.records) != ANALYTES:
            raise ValueError("human SCH analyte order or set changed")
        for record in condition.records:
            observed = (
                record.cells_plus_bile_mean_uM,
                record.cells_plus_bile_sd_uM,
                record.cells_mean_uM,
                record.cells_sd_uM,
                record.medium_mean_uM,
                record.medium_sd_uM,
                record.bei_mean_percent,
                record.bei_sd_percent,
            )
            if observed != expected[condition_id][record.analyte]:
                raise ValueError("human SCH Table 4 numeric record changed")
            numeric = [value for value in observed if value is not None]
            if any(not isfinite(value) or value < 0.0 for value in numeric):
                raise ValueError("human SCH records must be finite and non-negative")
            if record.analyte == "Total" and (
                record.bei_mean_percent is not None or record.bei_sd_percent is not None
            ):
                raise ValueError("source does not report a total-bile-acid BEI")
    control_tca = by_condition["vehicle_control"].records[0]
    group_mean_ratio = calculate_matched_raw_bei_percent(
        control_tca.cells_plus_bile_mean_uM,
        control_tca.cells_mean_uM,
    )
    if isclose(group_mean_ratio, control_tca.bei_mean_percent or 0.0, abs_tol=1e-6):
        raise ValueError("published aggregate BEI was incorrectly reconstructed from group means")
    if {item.id for item in state.required_measurements} != {
        "raw_donor_level_records_and_LLOQ",
        "true_canalicular_volume_and_content",
        "matched_time_course_and_fluxes",
        "healthy_in_vivo_or_freshly_isolated_reference",
    }:
        raise ValueError("human SCH required-measurement set is incomplete")
    notes = " ".join(state.source_consistency_notes)
    if "183 +/- 55.6" not in notes or "183 +/- 111" not in notes:
        raise ValueError("human SCH source inconsistency is not documented")
    if set(state.source_ids) != {"marion2013_human_sch_bile_acids"} or not set(
        state.source_ids
    ) <= set(HUMAN_SCH_BILE_ACID_SOURCES):
        raise ValueError("human SCH source registry changed")
    if (
        not state.table4_numeric_records_loaded
        or not state.aggregate_measurement_contract_ready
        or state.raw_donor_records_loaded
        or state.analyte_LLOQ_loaded
        or state.true_canalicular_concentration_ready
        or state.kinetic_parameter_fit_ready
        or state.healthy_in_vivo_initialization_ready
        or state.automatic_state_coupling
        or state.model_pass_threshold_defined
        or state.predictive_ready
    ):
        raise ValueError("human SCH readiness gates exceeded the evidence")
    if len(state.limitations) < 7:
        raise ValueError("human SCH limitations are incomplete")


def human_sch_bile_acids_snapshot() -> dict[str, object]:
    state = build_human_sch_bile_acids()
    by_condition = {item.id: item for item in state.conditions}
    control_total = next(
        item for item in by_condition["vehicle_control"].records if item.analyte == "Total"
    )
    payload = state.to_dict()
    payload["summary"] = {
        "donor_count": len(state.donors),
        "condition_count": len(state.conditions),
        "named_analyte_count": len(ANALYTES) - 1,
        "table_record_count": sum(len(item.records) for item in state.conditions),
        "published_mean_endpoint_count": sum(
            3 + (record.bei_mean_percent is not None)
            for condition in state.conditions
            for record in condition.records
        ),
        "vehicle_total_cells_plus_bile_mean_uM": control_total.cells_plus_bile_mean_uM,
        "vehicle_total_cells_mean_uM": control_total.cells_mean_uM,
        "vehicle_total_medium_mean_uM": control_total.medium_mean_uM,
        "raw_donor_record_count": 0,
        "analyte_LLOQ_record_count": 0,
        "exact_model_prediction_count": 0,
        "fitted_parameter_count": 0,
        "pass_fail_count": 0,
    }
    return payload
