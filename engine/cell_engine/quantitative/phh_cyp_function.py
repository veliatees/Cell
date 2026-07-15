"""Batch-resolved PHH CYP450 observation panel with fail-closed coupling.

The Peng et al. supplement reports assay-level substrate-clearance and
metabolite-formation outputs.  It does not expose the raw concentration time
courses needed to identify transport, CYP turnover, or product-loss kinetics.
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
VERSION = "phh_cyp_function_v1"
SCHEMA_VERSION = "cell.phh-cyp-function.v1"
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "phh_baseline"
    / "curated"
    / "peng2025_phh_cyp_function.v1.json"
)
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


PHH_CYP_FUNCTION_SOURCES: dict[str, SourceReference] = {
    "peng2025_phh_quality_attributes": SourceReference(
        id="peng2025_phh_quality_attributes",
        title="The validation of quality attributes in Primary Human Hepatocytes Standard",
        url="https://doi.org/10.1186/s13619-025-00258-6",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Tables S4-S6 report batch-resolved CYP substrate-clearance and metabolite-formation "
            "rates for six commercial PHH batches. Tables S4-S5 report n=3 but do not label "
            "the within-batch replicate class."
        ),
    ),
    "peng2022_phh_requirements_standard": SourceReference(
        id="peng2022_phh_requirements_standard",
        title="Requirments for primary human hepatocyte",
        url="https://doi.org/10.1111/cpr.13147",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Published CSCB standard. It states a >=100 uL/(h x 10^6 cells) intrinsic-clearance "
            "criterion for representative drug metabolism, explicitly giving CYP3A4/testosterone as the example."
        ),
    ),
}


BATCH_IDS = ("PHH330", "PHH409", "PHH416", "PHH211", "PHH025", "PHH789")
ENZYME_CONTRACTS = {
    "CYP1A2": ("phenacetin", "4-acetamidophenol"),
    "CYP2B6": ("bupropion", "4-hydroxybupropion"),
    "CYP2C9": ("diclofenac", "4'-hydroxydiclofenac"),
    "CYP2C19": ("mephenytoin", "4-hydroxymephenytoin"),
    "CYP2D6": ("dextromethorphan", "dextrorphan"),
    "CYP3A4": ("testosterone", "6beta-hydroxytestosterone"),
}


@dataclass(frozen=True)
class CypSourceArtifact:
    source_id: str
    supplement_filename: str
    supplement_locator: str
    supplement_md5: str
    supplement_sha256: str
    source_tables: tuple[str, ...]


@dataclass(frozen=True)
class CypAssayContract:
    species: str
    biological_system: str
    culture_format: str
    seeded_cells_per_well: int
    incubation_medium: str
    temperature_c: float
    co2_percent: float
    instrument: str
    replicates_per_batch: int
    replicate_type: str
    substrate_concentration_uM: float
    scr_unit: str
    mfr_unit: str
    normalization_denominator: str
    raw_timepoint_matrix_published: bool
    lower_limits_of_quantification_published: bool


@dataclass(frozen=True)
class CypFormulaContract:
    scr_formula_as_printed: str
    mfr_formula_as_printed: str
    regression_definition: str
    v_over_m_definition_as_printed: str
    formula_audit: str


@dataclass(frozen=True)
class CypProductQualityCriterion:
    authority: str
    source_id: str
    standard_scope: str
    explicit_example_enzyme: str
    explicit_example_substrate: str
    threshold: float
    unit: str
    role: str
    may_be_used_as_model_pass_threshold: bool


@dataclass(frozen=True)
class CypBatchObservation:
    batch_id: str
    scr_mean: float
    scr_sd: float | None
    mfr_mean: float
    mfr_sd: float | None
    scr_status: str
    mfr_status: str


@dataclass(frozen=True)
class CypEnzymePanel:
    enzyme: str
    substrate: str
    metabolite: str
    records: tuple[CypBatchObservation, ...]


@dataclass(frozen=True)
class CypReportedAssociation:
    id: str
    finding: str
    numeric_r_published_in_machine_readable_table: bool
    model_consequence: str


@dataclass(frozen=True)
class CypRequiredMeasurement:
    id: str
    requirements: tuple[str, ...]
    purpose: str


@dataclass(frozen=True)
class PhhCypFunctionState:
    version: str
    status: str
    date_verified: str
    source_artifact: CypSourceArtifact
    assay_contract: CypAssayContract
    reported_formula_contract: CypFormulaContract
    product_quality_criterion: CypProductQualityCriterion
    enzymes: tuple[CypEnzymePanel, ...]
    reported_associations: tuple[CypReportedAssociation, ...]
    required_measurements: tuple[CypRequiredMeasurement, ...]
    individual_batch_tables_loaded: bool
    same_format_comparison_ready: bool
    raw_timecourse_reconstruction_ready: bool
    kinetic_parameter_fit_ready: bool
    donor_causal_model_ready: bool
    automatic_state_coupling: bool
    model_pass_threshold_defined: bool
    predictive_ready: bool
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


@dataclass(frozen=True)
class CypModelBatchPrediction:
    enzyme: str
    batch_id: str
    scr: float
    mfr: float


@dataclass(frozen=True)
class CypModelPredictionSet:
    prediction_id: str
    model_id: str
    model_artifact_sha256: str
    measurement_contract_version: str
    species: str
    biological_system: str
    culture_format: str
    substrate_concentration_uM: float
    normalization_denominator: str
    scr_unit: str
    mfr_unit: str
    records: tuple[CypModelBatchPrediction, ...]


@dataclass(frozen=True)
class CypModelInputAudit:
    context_match: bool
    unit_and_denominator_match: bool
    exact_record_matrix: bool
    values_finite_nonnegative: bool
    artifact_provenance_present: bool
    exact_input_match: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class CypObservationResidual:
    enzyme: str
    batch_id: str
    metric: str
    observed_mean: float
    observed_sd: float | None
    predicted_value: float
    observed_status: str
    numeric_residual: float | None
    standardized_residual: float | None


@dataclass(frozen=True)
class CypSameFormatComparison:
    status: str
    input_audit: CypModelInputAudit
    residuals: tuple[CypObservationResidual, ...]
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


def _optional_float(value: object) -> float | None:
    return None if value is None else float(value)


def _measurement_status(mean: float) -> str:
    return "source_reported_undetectable" if mean == 0.0 else "quantified"


def build_phh_cyp_function(data_path: Path = DATA_PATH) -> PhhCypFunctionState:
    payload = _load_json(data_path)
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported PHH CYP-function schema")
    artifact_raw = payload["source_artifact"]
    assay_raw = payload["assay_contract"]
    formula_raw = payload["reported_formula_contract"]
    criterion_raw = payload["product_quality_criterion"]
    gates = payload["gates"]
    if not all(isinstance(item, dict) for item in (artifact_raw, assay_raw, formula_raw, criterion_raw, gates)):
        raise ValueError("PHH CYP-function object payload is malformed")
    enzymes_raw = payload.get("enzymes")
    associations_raw = payload.get("reported_associations")
    required_raw = payload.get("required_measurements")
    if not all(isinstance(item, list) for item in (enzymes_raw, associations_raw, required_raw)):
        raise ValueError("PHH CYP-function list payload is malformed")

    enzymes: list[CypEnzymePanel] = []
    for enzyme_raw in enzymes_raw:
        if not isinstance(enzyme_raw, dict) or not isinstance(enzyme_raw.get("records"), list):
            raise ValueError("PHH CYP enzyme panel is malformed")
        records = []
        for record_raw in enzyme_raw["records"]:
            if not isinstance(record_raw, dict):
                raise ValueError("PHH CYP record is malformed")
            scr_mean = float(record_raw["scr_mean"])
            mfr_mean = float(record_raw["mfr_mean"])
            records.append(
                CypBatchObservation(
                    batch_id=str(record_raw["batch_id"]),
                    scr_mean=scr_mean,
                    scr_sd=_optional_float(record_raw["scr_sd"]),
                    mfr_mean=mfr_mean,
                    mfr_sd=_optional_float(record_raw["mfr_sd"]),
                    scr_status=_measurement_status(scr_mean),
                    mfr_status=_measurement_status(mfr_mean),
                )
            )
        enzymes.append(
            CypEnzymePanel(
                enzyme=str(enzyme_raw["enzyme"]),
                substrate=str(enzyme_raw["substrate"]),
                metabolite=str(enzyme_raw["metabolite"]),
                records=tuple(records),
            )
        )

    state = PhhCypFunctionState(
        version=VERSION,
        status=str(payload["status"]),
        date_verified=str(payload["date_verified"]),
        source_artifact=CypSourceArtifact(
            source_id=str(artifact_raw["source_id"]),
            supplement_filename=str(artifact_raw["supplement_filename"]),
            supplement_locator=str(artifact_raw["supplement_locator"]),
            supplement_md5=str(artifact_raw["supplement_md5"]),
            supplement_sha256=str(artifact_raw["supplement_sha256"]),
            source_tables=tuple(str(item) for item in artifact_raw["source_tables"]),  # type: ignore[index]
        ),
        assay_contract=CypAssayContract(
            species=str(assay_raw["species"]),
            biological_system=str(assay_raw["biological_system"]),
            culture_format=str(assay_raw["culture_format"]),
            seeded_cells_per_well=int(assay_raw["seeded_cells_per_well"]),
            incubation_medium=str(assay_raw["incubation_medium"]),
            temperature_c=float(assay_raw["temperature_c"]),
            co2_percent=float(assay_raw["co2_percent"]),
            instrument=str(assay_raw["instrument"]),
            replicates_per_batch=int(assay_raw["replicates_per_batch"]),
            replicate_type=str(assay_raw["replicate_type"]),
            substrate_concentration_uM=float(assay_raw["substrate_concentration_uM"]),
            scr_unit=str(assay_raw["scr_unit"]),
            mfr_unit=str(assay_raw["mfr_unit"]),
            normalization_denominator=str(assay_raw["normalization_denominator"]),
            raw_timepoint_matrix_published=bool(assay_raw["raw_timepoint_matrix_published"]),
            lower_limits_of_quantification_published=bool(assay_raw["lower_limits_of_quantification_published"]),
        ),
        reported_formula_contract=CypFormulaContract(
            scr_formula_as_printed=str(formula_raw["scr_formula_as_printed"]),
            mfr_formula_as_printed=str(formula_raw["mfr_formula_as_printed"]),
            regression_definition=str(formula_raw["regression_definition"]),
            v_over_m_definition_as_printed=str(formula_raw["v_over_m_definition_as_printed"]),
            formula_audit=str(formula_raw["formula_audit"]),
        ),
        product_quality_criterion=CypProductQualityCriterion(
            authority=str(criterion_raw["authority"]),
            source_id=str(criterion_raw["source_id"]),
            standard_scope=str(criterion_raw["standard_scope"]),
            explicit_example_enzyme=str(criterion_raw["explicit_example_enzyme"]),
            explicit_example_substrate=str(criterion_raw["explicit_example_substrate"]),
            threshold=float(criterion_raw["threshold"]),
            unit=str(criterion_raw["unit"]),
            role=str(criterion_raw["role"]),
            may_be_used_as_model_pass_threshold=bool(criterion_raw["may_be_used_as_model_pass_threshold"]),
        ),
        enzymes=tuple(enzymes),
        reported_associations=tuple(
            CypReportedAssociation(
                id=str(item["id"]),
                finding=str(item["finding"]),
                numeric_r_published_in_machine_readable_table=bool(
                    item["numeric_r_published_in_machine_readable_table"]
                ),
                model_consequence=str(item["model_consequence"]),
            )
            for item in associations_raw
            if isinstance(item, dict)
        ),
        required_measurements=tuple(
            CypRequiredMeasurement(
                id=str(item["id"]),
                requirements=tuple(str(value) for value in item["requirements"]),  # type: ignore[index]
                purpose=str(item["purpose"]),
            )
            for item in required_raw
            if isinstance(item, dict)
        ),
        individual_batch_tables_loaded=bool(gates["individual_batch_tables_loaded"]),
        same_format_comparison_ready=bool(gates["same_format_comparison_ready"]),
        raw_timecourse_reconstruction_ready=bool(gates["raw_timecourse_reconstruction_ready"]),
        kinetic_parameter_fit_ready=bool(gates["kinetic_parameter_fit_ready"]),
        donor_causal_model_ready=bool(gates["donor_causal_model_ready"]),
        automatic_state_coupling=bool(gates["automatic_state_coupling"]),
        model_pass_threshold_defined=bool(gates["model_pass_threshold_defined"]),
        predictive_ready=bool(gates["predictive_ready"]),
        source_ids=tuple(str(item) for item in payload["source_ids"]),  # type: ignore[index]
        limitations=tuple(str(item) for item in payload["limitations"]),  # type: ignore[index]
    )
    validate_phh_cyp_function(state)
    return state


def validate_phh_cyp_function(state: PhhCypFunctionState) -> None:
    assay = state.assay_contract
    artifact = state.source_artifact
    criterion = state.product_quality_criterion
    if state.version != VERSION or state.date_verified != DATE_VERIFIED:
        raise ValueError("PHH CYP-function version or verification date changed")
    if (
        artifact.source_id != "peng2025_phh_quality_attributes"
        or artifact.supplement_filename != "13619_2025_258_MOESM1_ESM.docx"
        or artifact.supplement_md5 != "cf6103b084c236f3fedf2f30e548559e"
        or artifact.supplement_sha256 != "deeb835fe82d7e0e883447268354b9abb8f3ca4950639be3b68b802d3c6183bf"
        or artifact.source_tables != ("Table S4", "Table S5", "Table S6")
    ):
        raise ValueError("PHH CYP supplement provenance changed")
    if (
        assay.species != "Homo sapiens"
        or assay.biological_system != "cryopreserved_commercial_primary_human_hepatocytes"
        or assay.culture_format != "collagen_I_coated_12_well_2d_culture"
        or assay.seeded_cells_per_well != 1_000_000
        or assay.temperature_c != 37.0
        or assay.co2_percent != 5.0
        or assay.instrument != "Shimadzu LCMS-8030"
        or assay.replicates_per_batch != 3
        or assay.replicate_type != "not_specified_in_source_table"
        or assay.substrate_concentration_uM != 1.0
        or assay.scr_unit != "uL_per_h_per_1e6_cells"
        or assay.mfr_unit != "pmol_per_h_per_1e6_cells"
        or assay.normalization_denominator != "reported_hepatocyte_number"
        or assay.raw_timepoint_matrix_published
        or assay.lower_limits_of_quantification_published
    ):
        raise ValueError("PHH CYP assay contract changed")
    if (
        criterion.authority != "T_CSCB_0008_2021_group_standard"
        or criterion.source_id != "peng2022_phh_requirements_standard"
        or criterion.standard_scope != "representative_drug_metabolism_ability"
        or criterion.explicit_example_enzyme != "CYP3A4"
        or criterion.explicit_example_substrate != "testosterone"
        or criterion.threshold != 100.0
        or criterion.unit != assay.scr_unit
        or criterion.may_be_used_as_model_pass_threshold
    ):
        raise ValueError("PHH CYP product criterion was promoted or changed")
    if {panel.enzyme for panel in state.enzymes} != set(ENZYME_CONTRACTS):
        raise ValueError("PHH CYP enzyme panel is incomplete")
    if len(state.enzymes) != 6:
        raise ValueError("PHH CYP panel must contain six enzymes")
    for panel in state.enzymes:
        if (panel.substrate, panel.metabolite) != ENZYME_CONTRACTS[panel.enzyme]:
            raise ValueError(f"PHH CYP substrate/metabolite pair changed for {panel.enzyme}")
        if tuple(record.batch_id for record in panel.records) != BATCH_IDS:
            raise ValueError(f"PHH CYP batch matrix changed for {panel.enzyme}")
        for record in panel.records:
            values = (record.scr_mean, record.mfr_mean)
            if not all(isfinite(value) and value >= 0.0 for value in values):
                raise ValueError("PHH CYP means must be finite and non-negative")
            for mean, sd, status in (
                (record.scr_mean, record.scr_sd, record.scr_status),
                (record.mfr_mean, record.mfr_sd, record.mfr_status),
            ):
                expected_status = _measurement_status(mean)
                if status != expected_status:
                    raise ValueError("PHH CYP censoring semantics changed")
                if mean == 0.0 and sd is not None:
                    raise ValueError("source-reported undetectable CYP record gained an SD")
                if mean > 0.0 and (sd is None or not isfinite(sd) or sd < 0.0):
                    raise ValueError("quantified PHH CYP record lacks a valid SD")

    by_key = {
        (panel.enzyme, record.batch_id): record
        for panel in state.enzymes
        for record in panel.records
    }
    anchors = {
        ("CYP1A2", "PHH416"): (0.0, None, 33.9, 5.6),
        ("CYP2B6", "PHH789"): (476.8, 48.2, 485.2, 19.3),
        ("CYP2C9", "PHH789"): (246.7, 10.4, 744.7, 50.4),
        ("CYP2C19", "PHH789"): (255.1, 64.6, 211.7, 16.4),
        ("CYP2D6", "PHH789"): (902.9, 125.6, 330.0, 2.8),
        ("CYP3A4", "PHH330"): (970.6, 134.4, 2008.6, 147.9),
        ("CYP3A4", "PHH789"): (1981.0, 314.7, 985.8, 21.3),
    }
    for key, expected in anchors.items():
        record = by_key[key]
        if (record.scr_mean, record.scr_sd, record.mfr_mean, record.mfr_sd) != expected:
            raise ValueError(f"PHH CYP source anchor changed for {key}")
    if sum(record.scr_mean == 0.0 for record in by_key.values()) != 4:
        raise ValueError("PHH CYP SCR censoring count changed")
    if sum(record.mfr_mean == 0.0 for record in by_key.values()) != 6:
        raise ValueError("PHH CYP MFR censoring count changed")
    if {item.id for item in state.reported_associations} != {
        "cyp1a2_and_cyp3a4_activity_vs_matched_mrna",
        "purity_and_albumin_vs_cyp_activity",
    }:
        raise ValueError("PHH CYP association audit is incomplete")
    if {item.id for item in state.required_measurements} != {
        "raw_substrate_product_timecourses",
        "matched_donor_genotype_protein_activity",
        "matched_perturbation_timecourse",
    }:
        raise ValueError("PHH CYP required-measurement set is incomplete")
    if set(state.source_ids) != {"peng2025_phh_quality_attributes", "peng2022_phh_requirements_standard"} or not set(state.source_ids) <= set(PHH_CYP_FUNCTION_SOURCES):
        raise ValueError("PHH CYP source registry changed")
    if (
        not state.individual_batch_tables_loaded
        or not state.same_format_comparison_ready
        or state.raw_timecourse_reconstruction_ready
        or state.kinetic_parameter_fit_ready
        or state.donor_causal_model_ready
        or state.automatic_state_coupling
        or state.model_pass_threshold_defined
        or state.predictive_ready
    ):
        raise ValueError("PHH CYP readiness gates exceeded the evidence")
    if len(state.limitations) < 6:
        raise ValueError("PHH CYP limitations are incomplete")


def audit_cyp_model_prediction(
    state: PhhCypFunctionState,
    prediction: CypModelPredictionSet,
) -> CypModelInputAudit:
    validate_phh_cyp_function(state)
    assay = state.assay_contract
    context_match = (
        prediction.measurement_contract_version == state.version
        and prediction.species == assay.species
        and prediction.biological_system == assay.biological_system
        and prediction.culture_format == assay.culture_format
        and prediction.substrate_concentration_uM == assay.substrate_concentration_uM
    )
    unit_and_denominator_match = (
        prediction.normalization_denominator == assay.normalization_denominator
        and prediction.scr_unit == assay.scr_unit
        and prediction.mfr_unit == assay.mfr_unit
    )
    expected_keys = {(enzyme, batch) for enzyme in ENZYME_CONTRACTS for batch in BATCH_IDS}
    actual_keys = {(record.enzyme, record.batch_id) for record in prediction.records}
    exact_record_matrix = len(prediction.records) == len(actual_keys) and actual_keys == expected_keys
    values_finite_nonnegative = all(
        isfinite(record.scr)
        and isfinite(record.mfr)
        and record.scr >= 0.0
        and record.mfr >= 0.0
        for record in prediction.records
    )
    artifact_provenance_present = bool(prediction.prediction_id and prediction.model_id) and bool(
        SHA256_PATTERN.fullmatch(prediction.model_artifact_sha256)
    )
    checks = {
        "measurement contract or biological context differs": context_match,
        "unit or cell-number denominator differs": unit_and_denominator_match,
        "the exact six-enzyme by six-batch prediction matrix is incomplete or duplicated": exact_record_matrix,
        "one or more predictions is non-finite or negative": values_finite_nonnegative,
        "prediction/model identifier or SHA-256 provenance is missing": artifact_provenance_present,
    }
    blockers = tuple(message for message, passed in checks.items() if not passed)
    return CypModelInputAudit(
        context_match=context_match,
        unit_and_denominator_match=unit_and_denominator_match,
        exact_record_matrix=exact_record_matrix,
        values_finite_nonnegative=values_finite_nonnegative,
        artifact_provenance_present=artifact_provenance_present,
        exact_input_match=not blockers,
        blockers=blockers,
    )


def compare_cyp_model_to_observations(
    state: PhhCypFunctionState,
    prediction: CypModelPredictionSet,
) -> CypSameFormatComparison:
    audit = audit_cyp_model_prediction(state, prediction)
    if not audit.exact_input_match:
        raise ValueError("CYP prediction does not match the assay: " + "; ".join(audit.blockers))
    observed = {
        (panel.enzyme, record.batch_id): record
        for panel in state.enzymes
        for record in panel.records
    }
    residuals: list[CypObservationResidual] = []
    for predicted in prediction.records:
        record = observed[(predicted.enzyme, predicted.batch_id)]
        for metric, observed_mean, observed_sd, predicted_value, status in (
            ("SCR", record.scr_mean, record.scr_sd, predicted.scr, record.scr_status),
            ("MFR", record.mfr_mean, record.mfr_sd, predicted.mfr, record.mfr_status),
        ):
            numeric_residual = predicted_value - observed_mean if status == "quantified" else None
            standardized = (
                numeric_residual / observed_sd
                if numeric_residual is not None and observed_sd is not None and observed_sd > 0.0
                else None
            )
            residuals.append(
                CypObservationResidual(
                    enzyme=predicted.enzyme,
                    batch_id=predicted.batch_id,
                    metric=metric,
                    observed_mean=observed_mean,
                    observed_sd=observed_sd,
                    predicted_value=predicted_value,
                    observed_status=status,
                    numeric_residual=numeric_residual,
                    standardized_residual=standardized,
                )
            )
    return CypSameFormatComparison(
        status="same_format_diagnostic_no_pass_threshold",
        input_audit=audit,
        residuals=tuple(residuals),
        fitted_parameter_count=0,
        pass_fail_assigned=False,
        may_drive_cell_state=False,
    )


def phh_cyp_function_snapshot() -> dict[str, object]:
    state = build_phh_cyp_function()
    records = [record for panel in state.enzymes for record in panel.records]
    payload = state.to_dict()
    payload["summary"] = {
        "enzyme_count": len(state.enzymes),
        "batch_count": len(BATCH_IDS),
        "assay_mean_record_count": len(records) * 2,
        "quantified_mean_record_count": sum(
            status == "quantified"
            for record in records
            for status in (record.scr_status, record.mfr_status)
        ),
        "source_reported_undetectable_record_count": sum(
            status == "source_reported_undetectable"
            for record in records
            for status in (record.scr_status, record.mfr_status)
        ),
        "replicates_per_batch": state.assay_contract.replicates_per_batch,
        "replicate_type": state.assay_contract.replicate_type,
        "cyp3a4_scr_low": min(record.scr_mean for record in state.enzymes[-1].records),
        "cyp3a4_scr_high": max(record.scr_mean for record in state.enzymes[-1].records),
        "exact_model_prediction_count": 0,
        "fitted_parameter_count": 0,
        "pass_fail_count": 0,
    }
    return payload
