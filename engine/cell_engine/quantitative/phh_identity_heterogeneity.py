"""PHH identity, product composition, and heterogeneity observations.

FACS marker-positive fractions and scRNA-seq cell-type fractions are kept as
separate measurement constructs.  Neither is converted into a fractional
internal state of one simulated hepatocyte.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from math import isclose, isfinite
from pathlib import Path

from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain


DATE_VERIFIED = "2026-07-14"
VERSION = "phh_identity_heterogeneity_v1"
SCHEMA_VERSION = "cell.phh-identity-heterogeneity.v1"
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "phh_baseline"
    / "curated"
    / "peng2025_phh_identity_heterogeneity.v1.json"
)


PHH_IDENTITY_HETEROGENEITY_SOURCES: dict[str, SourceReference] = {
    "peng2025_phh_quality_attributes": SourceReference(
        id="peng2025_phh_quality_attributes",
        title="The validation of quality attributes in Primary Human Hepatocytes Standard",
        url="https://doi.org/10.1186/s13619-025-00258-6",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Table S2 and Figure S2B report batch-resolved FACS marker fractions and scRNA-seq "
            "cell-type composition for six commercial PHH batches."
        ),
    ),
    "geo_gse289636": SourceReference(
        id="geo_gse289636",
        title="GEO Series GSE289636: primary human hepatocyte single-cell RNA-seq",
        url="https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE289636",
        source_type="database",
        date_verified=DATE_VERIFIED,
        notes="Primary repository accession registered by the Peng et al. study for six PHH batches.",
    ),
    "peng2022_phh_requirements_standard": SourceReference(
        id="peng2022_phh_requirements_standard",
        title="Requirments for primary human hepatocyte",
        url="https://doi.org/10.1111/cpr.13147",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Published CSCB standard source for ALB and HNF4A >=90 percent PHH product-marker criteria.",
    ),
}


BATCH_IDS = ("PHH330", "PHH409", "PHH416", "PHH211", "PHH025", "PHH789")
CELL_TYPE_IDS = ("hepatocyte", "lymphocyte", "lsec", "cholangiocyte", "stellate_cell")


@dataclass(frozen=True)
class IdentitySourceArtifact:
    source_id: str
    supplement_filename: str
    supplement_md5: str
    supplement_sha256: str
    source_locations: tuple[str, ...]
    geo_accession: str


@dataclass(frozen=True)
class FacsMarkerContract:
    marker: str
    primary_antibody: str
    dilution: str


@dataclass(frozen=True)
class FacsAssayContract:
    input_cells: str
    fixation: str
    permeabilization: str
    instrument: str
    markers: tuple[FacsMarkerContract, ...]
    reported_unit: str


@dataclass(frozen=True)
class FacsBatchObservation:
    batch_id: str
    alb_positive_percent: float
    hnf4a_positive_percent: float


@dataclass(frozen=True)
class ScrnaQualityFilters:
    genes_greater_than: int
    umis_greater_than: int
    mitochondrial_percent_less_than: float


@dataclass(frozen=True)
class ScrnaAssayContract:
    platform: str
    sequencer: str
    read_layout: str
    minimum_reads_per_cell: int
    cells_loaded_per_channel: int
    target_recovery_per_channel: int
    reference_genome: str
    software: str
    quality_filters: ScrnaQualityFilters
    batch_correction: str
    clustering_resolution: float
    cell_type_markers: dict[str, tuple[str, ...]]


@dataclass(frozen=True)
class CellTypeObservation:
    cell_type: str
    count: int
    percent: float


@dataclass(frozen=True)
class ScrnaBatchComposition:
    batch_id: str
    cell_types: tuple[CellTypeObservation, ...]


@dataclass(frozen=True)
class IdentityProductQualityCriterion:
    authority: str
    source_id: str
    markers: tuple[str, ...]
    threshold_percent: float
    role: str
    may_be_used_as_single_cell_state_threshold: bool


@dataclass(frozen=True)
class IdentityReportedAssociation:
    id: str
    correlation_r: float
    p_value: float | None
    sample_size: int
    statistically_significant_as_reported: bool | None


@dataclass(frozen=True)
class HepatocyteSubset:
    id: str
    reported_enrichment: tuple[str, ...]


@dataclass(frozen=True)
class PhhIdentityHeterogeneityState:
    version: str
    status: str
    date_verified: str
    source_artifact: IdentitySourceArtifact
    facs_contract: FacsAssayContract
    facs_records: tuple[FacsBatchObservation, ...]
    scrna_contract: ScrnaAssayContract
    scrna_records: tuple[ScrnaBatchComposition, ...]
    product_quality_criterion: IdentityProductQualityCriterion
    reported_associations: tuple[IdentityReportedAssociation, ...]
    hepatocyte_subsets: tuple[HepatocyteSubset, ...]
    facs_batch_table_loaded: bool
    scrna_composition_table_loaded: bool
    raw_geo_accession_registered: bool
    hepatocyte_subset_count_loaded: bool
    hepatocyte_subset_batch_numeric_matrix_loaded: bool
    single_cell_state_initialization_ready: bool
    generative_training_ready: bool
    automatic_state_coupling: bool
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


def _optional_bool(value: object) -> bool | None:
    return None if value is None else bool(value)


def build_phh_identity_heterogeneity(
    data_path: Path = DATA_PATH,
) -> PhhIdentityHeterogeneityState:
    payload = _load_json(data_path)
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported PHH identity/heterogeneity schema")
    artifact_raw = payload["source_artifact"]
    facs_raw = payload["facs_contract"]
    scrna_raw = payload["scrna_contract"]
    criterion_raw = payload["product_quality_criterion"]
    gates = payload["gates"]
    if not all(isinstance(item, dict) for item in (artifact_raw, facs_raw, scrna_raw, criterion_raw, gates)):
        raise ValueError("PHH identity/heterogeneity object payload is malformed")
    facs_records_raw = payload.get("facs_records")
    scrna_records_raw = payload.get("scrna_records")
    associations_raw = payload.get("reported_associations")
    subsets_raw = payload.get("hepatocyte_subsets")
    if not all(isinstance(item, list) for item in (facs_records_raw, scrna_records_raw, associations_raw, subsets_raw)):
        raise ValueError("PHH identity/heterogeneity list payload is malformed")
    markers_raw = facs_raw.get("markers")
    filters_raw = scrna_raw.get("quality_filters")
    cell_type_markers_raw = scrna_raw.get("cell_type_markers")
    if not isinstance(markers_raw, list) or not isinstance(filters_raw, dict) or not isinstance(cell_type_markers_raw, dict):
        raise ValueError("PHH identity assay contract is malformed")

    scrna_records: list[ScrnaBatchComposition] = []
    for record_raw in scrna_records_raw:
        if not isinstance(record_raw, dict) or not isinstance(record_raw.get("cell_types"), dict):
            raise ValueError("PHH scRNA composition record is malformed")
        cell_types_raw = record_raw["cell_types"]
        scrna_records.append(
            ScrnaBatchComposition(
                batch_id=str(record_raw["batch_id"]),
                cell_types=tuple(
                    CellTypeObservation(
                        cell_type=cell_type,
                        count=int(cell_types_raw[cell_type]["count"]),
                        percent=float(cell_types_raw[cell_type]["percent"]),
                    )
                    for cell_type in CELL_TYPE_IDS
                ),
            )
        )

    state = PhhIdentityHeterogeneityState(
        version=VERSION,
        status=str(payload["status"]),
        date_verified=str(payload["date_verified"]),
        source_artifact=IdentitySourceArtifact(
            source_id=str(artifact_raw["source_id"]),
            supplement_filename=str(artifact_raw["supplement_filename"]),
            supplement_md5=str(artifact_raw["supplement_md5"]),
            supplement_sha256=str(artifact_raw["supplement_sha256"]),
            source_locations=tuple(str(item) for item in artifact_raw["source_locations"]),  # type: ignore[index]
            geo_accession=str(artifact_raw["geo_accession"]),
        ),
        facs_contract=FacsAssayContract(
            input_cells=str(facs_raw["input_cells"]),
            fixation=str(facs_raw["fixation"]),
            permeabilization=str(facs_raw["permeabilization"]),
            instrument=str(facs_raw["instrument"]),
            markers=tuple(
                FacsMarkerContract(
                    marker=str(item["marker"]),
                    primary_antibody=str(item["primary_antibody"]),
                    dilution=str(item["dilution"]),
                )
                for item in markers_raw
                if isinstance(item, dict)
            ),
            reported_unit=str(facs_raw["reported_unit"]),
        ),
        facs_records=tuple(
            FacsBatchObservation(
                batch_id=str(item["batch_id"]),
                alb_positive_percent=float(item["alb_positive_percent"]),
                hnf4a_positive_percent=float(item["hnf4a_positive_percent"]),
            )
            for item in facs_records_raw
            if isinstance(item, dict)
        ),
        scrna_contract=ScrnaAssayContract(
            platform=str(scrna_raw["platform"]),
            sequencer=str(scrna_raw["sequencer"]),
            read_layout=str(scrna_raw["read_layout"]),
            minimum_reads_per_cell=int(scrna_raw["minimum_reads_per_cell"]),
            cells_loaded_per_channel=int(scrna_raw["cells_loaded_per_channel"]),
            target_recovery_per_channel=int(scrna_raw["target_recovery_per_channel"]),
            reference_genome=str(scrna_raw["reference_genome"]),
            software=str(scrna_raw["software"]),
            quality_filters=ScrnaQualityFilters(
                genes_greater_than=int(filters_raw["genes_greater_than"]),
                umis_greater_than=int(filters_raw["umis_greater_than"]),
                mitochondrial_percent_less_than=float(filters_raw["mitochondrial_percent_less_than"]),
            ),
            batch_correction=str(scrna_raw["batch_correction"]),
            clustering_resolution=float(scrna_raw["clustering_resolution"]),
            cell_type_markers={
                str(cell_type): tuple(str(marker) for marker in markers)
                for cell_type, markers in cell_type_markers_raw.items()
                if isinstance(markers, list)
            },
        ),
        scrna_records=tuple(scrna_records),
        product_quality_criterion=IdentityProductQualityCriterion(
            authority=str(criterion_raw["authority"]),
            source_id=str(criterion_raw["source_id"]),
            markers=tuple(str(item) for item in criterion_raw["markers"]),  # type: ignore[index]
            threshold_percent=float(criterion_raw["threshold_percent"]),
            role=str(criterion_raw["role"]),
            may_be_used_as_single_cell_state_threshold=bool(
                criterion_raw["may_be_used_as_single_cell_state_threshold"]
            ),
        ),
        reported_associations=tuple(
            IdentityReportedAssociation(
                id=str(item["id"]),
                correlation_r=float(item["correlation_r"]),
                p_value=_optional_float(item["p_value"]),
                sample_size=int(item["sample_size"]),
                statistically_significant_as_reported=_optional_bool(
                    item["statistically_significant_as_reported"]
                ),
            )
            for item in associations_raw
            if isinstance(item, dict)
        ),
        hepatocyte_subsets=tuple(
            HepatocyteSubset(
                id=str(item["id"]),
                reported_enrichment=tuple(str(value) for value in item["reported_enrichment"]),  # type: ignore[index]
            )
            for item in subsets_raw
            if isinstance(item, dict)
        ),
        facs_batch_table_loaded=bool(gates["facs_batch_table_loaded"]),
        scrna_composition_table_loaded=bool(gates["scrna_composition_table_loaded"]),
        raw_geo_accession_registered=bool(gates["raw_geo_accession_registered"]),
        hepatocyte_subset_count_loaded=bool(gates["hepatocyte_subset_count_loaded"]),
        hepatocyte_subset_batch_numeric_matrix_loaded=bool(
            gates["hepatocyte_subset_batch_numeric_matrix_loaded"]
        ),
        single_cell_state_initialization_ready=bool(gates["single_cell_state_initialization_ready"]),
        generative_training_ready=bool(gates["generative_training_ready"]),
        automatic_state_coupling=bool(gates["automatic_state_coupling"]),
        predictive_ready=bool(gates["predictive_ready"]),
        source_ids=tuple(str(item) for item in payload["source_ids"]),  # type: ignore[index]
        limitations=tuple(str(item) for item in payload["limitations"]),  # type: ignore[index]
    )
    validate_phh_identity_heterogeneity(state)
    return state


def validate_phh_identity_heterogeneity(state: PhhIdentityHeterogeneityState) -> None:
    artifact = state.source_artifact
    facs = state.facs_contract
    scrna = state.scrna_contract
    criterion = state.product_quality_criterion
    if state.version != VERSION or state.date_verified != DATE_VERIFIED:
        raise ValueError("PHH identity version or verification date changed")
    if (
        artifact.source_id != "peng2025_phh_quality_attributes"
        or artifact.supplement_filename != "13619_2025_258_MOESM1_ESM.docx"
        or artifact.supplement_md5 != "cf6103b084c236f3fedf2f30e548559e"
        or artifact.supplement_sha256 != "deeb835fe82d7e0e883447268354b9abb8f3ca4950639be3b68b802d3c6183bf"
        or artifact.source_locations != ("Table S2", "Figure S2B")
        or artifact.geo_accession != "GSE289636"
    ):
        raise ValueError("PHH identity source provenance changed")
    if (
        facs.input_cells != "100000_to_300000_single_PHHs"
        or facs.instrument != "BD FACSCelesta"
        or facs.reported_unit != "percent_marker_positive_cells"
        or tuple((item.marker, item.primary_antibody, item.dilution) for item in facs.markers)
        != (
            ("ALB", "Bethyl A80-129A", "1:200"),
            ("HNF4A", "Cell Signaling Technology 3113S", "1:100"),
        )
    ):
        raise ValueError("PHH FACS assay contract changed")
    expected_facs = (
        ("PHH330", 72.2, 49.4),
        ("PHH409", 94.9, 91.4),
        ("PHH416", 95.4, 90.9),
        ("PHH211", 49.4, 37.7),
        ("PHH025", 98.0, 78.5),
        ("PHH789", 98.9, 70.2),
    )
    if tuple(
        (item.batch_id, item.alb_positive_percent, item.hnf4a_positive_percent)
        for item in state.facs_records
    ) != expected_facs:
        raise ValueError("PHH FACS source table changed")
    if any(
        not isfinite(value) or not 0.0 <= value <= 100.0
        for record in state.facs_records
        for value in (record.alb_positive_percent, record.hnf4a_positive_percent)
    ):
        raise ValueError("PHH FACS percentages are invalid")
    if (
        scrna.platform != "10x_Genomics_Chromium_Single_Cell_3prime_v2"
        or scrna.sequencer != "Illumina_NovaSeq6000"
        or scrna.read_layout != "paired_end_150_bp"
        or scrna.minimum_reads_per_cell != 100_000
        or scrna.cells_loaded_per_channel != 8_700
        or scrna.target_recovery_per_channel != 5_000
        or scrna.reference_genome != "GRCh38"
        or scrna.software != "Seurat_4.2.0"
        or scrna.quality_filters != ScrnaQualityFilters(500, 600, 20.0)
        or scrna.batch_correction != "fastMNN_50_PCs_knn_20"
        or scrna.clustering_resolution != 0.5
        or set(scrna.cell_type_markers) != set(CELL_TYPE_IDS)
    ):
        raise ValueError("PHH scRNA assay contract changed")
    if tuple(record.batch_id for record in state.scrna_records) != BATCH_IDS:
        raise ValueError("PHH scRNA batch matrix changed")
    expected_total_counts = {
        "PHH330": 13_419,
        "PHH409": 3_712,
        "PHH416": 19_558,
        "PHH211": 3_771,
        "PHH025": 7_469,
        "PHH789": 6_205,
    }
    expected_hepatocytes = {
        "PHH330": (12_730, 94.87),
        "PHH409": (3_640, 98.06),
        "PHH416": (19_344, 98.91),
        "PHH211": (3_198, 84.81),
        "PHH025": (5_515, 73.84),
        "PHH789": (4_295, 69.22),
    }
    for record in state.scrna_records:
        if tuple(item.cell_type for item in record.cell_types) != CELL_TYPE_IDS:
            raise ValueError("PHH scRNA cell-type order changed")
        total = sum(item.count for item in record.cell_types)
        if total != expected_total_counts[record.batch_id]:
            raise ValueError(f"PHH scRNA total count changed for {record.batch_id}")
        hepatocyte = record.cell_types[0]
        if (hepatocyte.count, hepatocyte.percent) != expected_hepatocytes[record.batch_id]:
            raise ValueError(f"PHH hepatocyte fraction changed for {record.batch_id}")
        if any(item.count < 0 or not 0.0 <= item.percent <= 100.0 for item in record.cell_types):
            raise ValueError("PHH scRNA count or percentage is invalid")
        if any(
            not isclose(item.count / total * 100.0, item.percent, rel_tol=0.0, abs_tol=0.011)
            for item in record.cell_types
        ):
            raise ValueError("PHH scRNA count and rounded percentage disagree")
        if not 99.99 <= sum(item.percent for item in record.cell_types) <= 100.01:
            raise ValueError("PHH scRNA rounded percentages do not close")
    phh789 = next(record for record in state.scrna_records if record.batch_id == "PHH789")
    phh789_by_type = {item.cell_type: item for item in phh789.cell_types}
    if (
        phh789_by_type["lymphocyte"] != CellTypeObservation("lymphocyte", 1_438, 23.17)
        or phh789_by_type["lsec"] != CellTypeObservation("lsec", 386, 6.22)
    ):
        raise ValueError("PHH789 non-hepatocyte source anchors changed")
    if (
        criterion.authority != "T_CSCB_0008_2021_group_standard"
        or criterion.source_id != "peng2022_phh_requirements_standard"
        or criterion.markers != ("ALB", "HNF4A")
        or criterion.threshold_percent != 90.0
        or criterion.may_be_used_as_single_cell_state_threshold
    ):
        raise ValueError("PHH identity product criterion was promoted or changed")
    associations = {item.id: item for item in state.reported_associations}
    if set(associations) != {
        "facs_alb_vs_hnf4a",
        "scrna_hepatocyte_fraction_vs_facs_alb",
        "scrna_hepatocyte_fraction_vs_facs_hnf4a",
    }:
        raise ValueError("PHH identity association set is incomplete")
    if (
        associations["facs_alb_vs_hnf4a"].correlation_r != 0.89
        or associations["facs_alb_vs_hnf4a"].statistically_significant_as_reported is not None
        or associations["scrna_hepatocyte_fraction_vs_facs_alb"].correlation_r != 0.16
        or associations["scrna_hepatocyte_fraction_vs_facs_alb"].statistically_significant_as_reported
        or associations["scrna_hepatocyte_fraction_vs_facs_hnf4a"].correlation_r != 0.20
        or associations["scrna_hepatocyte_fraction_vs_facs_hnf4a"].statistically_significant_as_reported
    ):
        raise ValueError("PHH identity associations exceeded reported evidence")
    if tuple(item.id for item in state.hepatocyte_subsets) != (
        "cluster_a",
        "cluster_b",
        "cluster_c",
        "cluster_d",
        "cluster_e",
    ):
        raise ValueError("PHH hepatocyte subset count changed")
    if set(state.source_ids) != {"peng2025_phh_quality_attributes", "peng2022_phh_requirements_standard", "geo_gse289636"} or not set(state.source_ids) <= set(PHH_IDENTITY_HETEROGENEITY_SOURCES):
        raise ValueError("PHH identity source registry changed")
    if (
        not state.facs_batch_table_loaded
        or not state.scrna_composition_table_loaded
        or not state.raw_geo_accession_registered
        or not state.hepatocyte_subset_count_loaded
        or state.hepatocyte_subset_batch_numeric_matrix_loaded
        or state.single_cell_state_initialization_ready
        or state.generative_training_ready
        or state.automatic_state_coupling
        or state.predictive_ready
    ):
        raise ValueError("PHH identity readiness gates exceeded the evidence")
    if len(state.limitations) < 6:
        raise ValueError("PHH identity limitations are incomplete")


def phh_identity_heterogeneity_snapshot() -> dict[str, object]:
    state = build_phh_identity_heterogeneity()
    hepatocyte_percentages = [record.cell_types[0].percent for record in state.scrna_records]
    all_cells = [item for record in state.scrna_records for item in record.cell_types]
    criterion = state.product_quality_criterion.threshold_percent
    payload = state.to_dict()
    payload["summary"] = {
        "facs_batch_count": len(state.facs_records),
        "scrna_batch_count": len(state.scrna_records),
        "filtered_single_cell_count": sum(item.count for item in all_cells),
        "cell_type_count": len(CELL_TYPE_IDS),
        "facs_alb_low_percent": min(record.alb_positive_percent for record in state.facs_records),
        "facs_alb_high_percent": max(record.alb_positive_percent for record in state.facs_records),
        "facs_hnf4a_low_percent": min(record.hnf4a_positive_percent for record in state.facs_records),
        "facs_hnf4a_high_percent": max(record.hnf4a_positive_percent for record in state.facs_records),
        "scrna_hepatocyte_low_percent": min(hepatocyte_percentages),
        "scrna_hepatocyte_high_percent": max(hepatocyte_percentages),
        "batches_with_both_facs_markers_at_or_above_source_criterion": sum(
            record.alb_positive_percent >= criterion and record.hnf4a_positive_percent >= criterion
            for record in state.facs_records
        ),
        "batches_with_more_than_10_percent_non_hepatocytes": sum(
            percent < 90.0 for percent in hepatocyte_percentages
        ),
        "hepatocyte_subset_count": len(state.hepatocyte_subsets),
        "numeric_subset_distribution_count": 0,
        "generative_training_dataset_count": 0,
        "single_cell_state_initialization_count": 0,
        "pass_fail_count": 0,
    }
    return payload
