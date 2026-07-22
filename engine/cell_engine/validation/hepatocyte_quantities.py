"""Lossless audit and fail-closed curation gate for the quantity harvest."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping

from cell_engine.core.serialization import to_plain


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = REPOSITORY_ROOT / "data" / "hepatocyte_quantities"
RAW_ROOT = DATA_ROOT / "raw"
CURATED_ROOT = DATA_ROOT / "curated"
MASTER_CSV_PATH = RAW_ROOT / "hepatocyte_quantities_master.csv"
MASTER_JSON_PATH = RAW_ROOT / "hepatocyte_quantities_master.json"
RAW_MANIFEST_PATH = RAW_ROOT / "manifest.v1.json"
SOURCE_REVIEW_PATH = CURATED_ROOT / "source_review.v1.json"

VERSION = "hepatocyte_quantity_harvest_audit_v1"
MANIFEST_SCHEMA_VERSION = "cell.hepatocyte-quantity-harvest-manifest.v1"
REVIEW_SCHEMA_VERSION = "cell.hepatocyte-quantity-source-review.v1"

QUANTITY_COLUMNS = (
    "track",
    "category",
    "condition",
    "time_h",
    "endpoint",
    "value",
    "unit",
    "mean_or_median",
    "error",
    "n",
    "organism_bucket",
    "organism",
    "model",
    "assay",
    "substrate_condition",
    "temperature",
    "pmid",
    "doi",
    "url",
    "figure_table",
    "usable_for_human_wholecell",
    "notes",
)
ORGANISM_BUCKETS = ("HepaRG", "human", "mouse", "other", "rat")
MISSING_TOKENS = frozenset(("", "NOT_REPORTED"))

_STRICT_NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
_STRICT_VALUE_RE = re.compile(
    rf"^\s*(?P<approx>~|\u2248)?(?P<low>{_STRICT_NUMBER})"
    rf"(?:\s*(?:-|\u2013)\s*(?P<high>{_STRICT_NUMBER}))?\s*$"
)
_DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$", re.IGNORECASE)


class HepatocyteQuantityEvidenceError(ValueError):
    pass


@dataclass(frozen=True)
class QuantityObservation:
    row_number: int
    values: Mapping[str, str]

    def __getitem__(self, column: str) -> str:
        return self.values[column]


@dataclass(frozen=True)
class StrictNumericValue:
    low: float
    high: float
    qualifier: Literal["exact", "approximate", "range", "approximate_range"]


@dataclass(frozen=True)
class HepatocyteQuantityHarvestAudit:
    version: str
    status: str
    total_records: int
    track_counts: Mapping[str, int]
    organism_bucket_counts: Mapping[str, int]
    reported_value_records: int
    strict_numeric_value_records: int
    reported_error_records: int
    reported_sample_size_records: int
    unique_primary_source_pmids: int
    distinct_free_text_usability_labels: int
    exact_duplicate_records: int
    bucket_inconsistency_rows: tuple[int, ...]
    source_review_count: int
    reviewed_raw_record_count: int
    promoted_context_bound_claim_count: int
    automatic_parameter_activation: bool
    authoritative_runtime_coupling: bool
    healthy_phh_runtime_parameter_count: int

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def is_missing(value: str) -> bool:
    return value.strip() in MISSING_TOKENS


def parse_strict_numeric_value(value: str) -> StrictNumericValue | None:
    """Parse only a standalone scalar/range; never mine numbers from prose."""
    if is_missing(value):
        return None
    match = _STRICT_VALUE_RE.fullmatch(value)
    if match is None:
        return None
    low = float(match.group("low"))
    high_token = match.group("high")
    high = float(high_token) if high_token is not None else low
    if high < low:
        raise HepatocyteQuantityEvidenceError(f"Descending numeric range: {value!r}")
    approximate = match.group("approx") is not None
    ranged = high_token is not None
    if approximate and ranged:
        qualifier: Literal["exact", "approximate", "range", "approximate_range"] = (
            "approximate_range"
        )
    elif approximate:
        qualifier = "approximate"
    elif ranged:
        qualifier = "range"
    else:
        qualifier = "exact"
    return StrictNumericValue(low=low, high=high, qualifier=qualifier)


def _load_csv(path: Path) -> tuple[QuantityObservation, ...]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != QUANTITY_COLUMNS:
            raise HepatocyteQuantityEvidenceError(f"Unexpected columns in {path.name}")
        observations: list[QuantityObservation] = []
        for row_number, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise HepatocyteQuantityEvidenceError(
                    f"Malformed CSV record at {path.name}:{row_number}"
                )
            observations.append(
                QuantityObservation(
                    row_number=row_number,
                    values={column: str(row[column]) for column in QUANTITY_COLUMNS},
                )
            )
    return tuple(observations)


def load_quantity_harvest(
    path: Path = MASTER_CSV_PATH,
) -> tuple[QuantityObservation, ...]:
    return _load_csv(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_raw_manifest(root: Path) -> dict[str, object]:
    path = root / "raw" / RAW_MANIFEST_PATH.name
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise HepatocyteQuantityEvidenceError("Unsupported quantity manifest schema")
    files = payload.get("files")
    if not isinstance(files, list) or not files:
        raise HepatocyteQuantityEvidenceError("Quantity manifest has no files")
    names: list[str] = []
    for item in files:
        if not isinstance(item, dict):
            raise HepatocyteQuantityEvidenceError("Malformed quantity manifest entry")
        name = str(item.get("name", ""))
        names.append(name)
        file_path = root / "raw" / name
        if not file_path.is_file() or _sha256(file_path) != item.get("sha256"):
            raise HepatocyteQuantityEvidenceError(
                f"Quantity raw artifact failed checksum validation: {name}"
            )
    if len(names) != len(set(names)):
        raise HepatocyteQuantityEvidenceError("Quantity manifest has duplicate files")
    if payload.get("automatic_parameter_activation") is not False or payload.get(
        "authoritative_runtime_coupling"
    ) is not False:
        raise HepatocyteQuantityEvidenceError("Quantity raw manifest must fail closed")
    return payload


def _validate_source_review(
    root: Path,
    rows_by_number: Mapping[int, QuantityObservation],
) -> tuple[dict[str, object], int, int]:
    payload = json.loads(
        (root / "curated" / SOURCE_REVIEW_PATH.name).read_text(encoding="utf-8")
    )
    if payload.get("schema_version") != REVIEW_SCHEMA_VERSION:
        raise HepatocyteQuantityEvidenceError("Unsupported quantity source-review schema")
    if any(
        payload.get(key) is not False
        for key in (
            "automatic_parameter_activation",
            "healthy_phh_initialization_allowed",
            "whole_cell_rate_coupling_allowed",
        )
    ):
        raise HepatocyteQuantityEvidenceError("Quantity source review exceeded its scope")
    reviews = payload.get("reviews")
    if not isinstance(reviews, list) or not reviews:
        raise HepatocyteQuantityEvidenceError("Quantity source review has no records")
    review_ids: list[str] = []
    reviewed_rows: list[int] = []
    promoted_claim_count = 0
    allowed_targets = {
        "same_assay_protein_kinetic_evidence",
        "matching_protocol_injury_validation",
        "donor_variability_reference_only",
    }
    for review in reviews:
        if not isinstance(review, dict):
            raise HepatocyteQuantityEvidenceError("Malformed source-review record")
        review_ids.append(str(review.get("id", "")))
        raw_rows = review.get("raw_csv_rows")
        expected_pmids = review.get("expected_pmids")
        if not isinstance(raw_rows, list) or not isinstance(expected_pmids, list):
            raise HepatocyteQuantityEvidenceError("Source-review row linkage is malformed")
        if review.get("integration_target") not in allowed_targets:
            raise HepatocyteQuantityEvidenceError("Unknown source-review integration target")
        for raw_row in raw_rows:
            row_number = int(raw_row)
            observation = rows_by_number.get(row_number)
            if observation is None or observation["pmid"] not in expected_pmids:
                raise HepatocyteQuantityEvidenceError(
                    f"Source-review provenance mismatch at raw row {row_number}"
                )
            reviewed_rows.append(row_number)
        promoted = int(review.get("promoted_claim_count", -1))
        if promoted < 0:
            raise HepatocyteQuantityEvidenceError("Invalid promoted-claim count")
        if review.get("integration_target") == "donor_variability_reference_only" and promoted:
            raise HepatocyteQuantityEvidenceError("Donor reference was promoted into a model claim")
        promoted_claim_count += promoted
    if len(review_ids) != len(set(review_ids)) or len(reviewed_rows) != len(set(reviewed_rows)):
        raise HepatocyteQuantityEvidenceError("Duplicate source-review identity or row")
    if 167 in reviewed_rows:
        raise HepatocyteQuantityEvidenceError("Known macaque bucket error entered curation")
    return payload, len(reviewed_rows), promoted_claim_count


def validate_quantity_harvest(
    root: Path = DATA_ROOT,
) -> HepatocyteQuantityHarvestAudit:
    _validate_raw_manifest(root)
    master_csv_path = root / "raw" / MASTER_CSV_PATH.name
    master_json_path = root / "raw" / MASTER_JSON_PATH.name
    observations = _load_csv(master_csv_path)
    csv_rows = [dict(item.values) for item in observations]
    json_rows = json.loads(master_json_path.read_text(encoding="utf-8"))
    if csv_rows != json_rows:
        raise HepatocyteQuantityEvidenceError("Quantity master CSV and JSON differ")

    for bucket in ORGANISM_BUCKETS:
        split_path = root / "raw" / f"hepatocyte_quantities_{bucket}.csv"
        split_rows = [dict(item.values) for item in _load_csv(split_path)]
        expected = [row for row in csv_rows if row["organism_bucket"] == bucket]
        if split_rows != expected:
            raise HepatocyteQuantityEvidenceError(
                f"{bucket} quantity split is not an exact master partition"
            )

    for observation in observations:
        if observation["organism_bucket"] not in ORGANISM_BUCKETS:
            raise HepatocyteQuantityEvidenceError("Unknown organism bucket")
        pmid = observation["pmid"]
        if not is_missing(pmid) and not pmid.isdigit():
            raise HepatocyteQuantityEvidenceError(
                f"Malformed PMID at row {observation.row_number}"
            )
        doi = observation["doi"]
        if not is_missing(doi) and _DOI_RE.fullmatch(doi) is None:
            raise HepatocyteQuantityEvidenceError(
                f"Malformed DOI at row {observation.row_number}"
            )
        if is_missing(observation["url"]) or is_missing(observation["figure_table"]):
            raise HepatocyteQuantityEvidenceError(
                f"Missing source locator at row {observation.row_number}"
            )

    fingerprints = [tuple(row[column] for column in QUANTITY_COLUMNS) for row in csv_rows]
    rows_by_number = {item.row_number: item for item in observations}
    source_review, reviewed_count, promoted_count = _validate_source_review(
        root, rows_by_number
    )
    bucket_inconsistencies = tuple(
        item.row_number
        for item in observations
        if item["organism_bucket"] == "human"
        and item["organism"].strip().lower() != "human"
    )

    audit = HepatocyteQuantityHarvestAudit(
        version=VERSION,
        status="lossless_harvest_curated_claims_context_bound_runtime_activation_blocked",
        total_records=len(observations),
        track_counts=dict(sorted(Counter(item["track"] for item in observations).items())),
        organism_bucket_counts=dict(
            sorted(Counter(item["organism_bucket"] for item in observations).items())
        ),
        reported_value_records=sum(not is_missing(item["value"]) for item in observations),
        strict_numeric_value_records=sum(
            parse_strict_numeric_value(item["value"]) is not None for item in observations
        ),
        reported_error_records=sum(not is_missing(item["error"]) for item in observations),
        reported_sample_size_records=sum(not is_missing(item["n"]) for item in observations),
        unique_primary_source_pmids=len(
            {item["pmid"] for item in observations if not is_missing(item["pmid"])}
        ),
        distinct_free_text_usability_labels=len(
            {item["usable_for_human_wholecell"] for item in observations}
        ),
        exact_duplicate_records=len(fingerprints) - len(set(fingerprints)),
        bucket_inconsistency_rows=bucket_inconsistencies,
        source_review_count=len(source_review["reviews"]),
        reviewed_raw_record_count=reviewed_count,
        promoted_context_bound_claim_count=promoted_count,
        automatic_parameter_activation=False,
        authoritative_runtime_coupling=False,
        healthy_phh_runtime_parameter_count=0,
    )
    expected_counts = {
        "total_records": 168,
        "reported_value_records": 144,
        "strict_numeric_value_records": 115,
        "reported_error_records": 65,
        "reported_sample_size_records": 59,
        "unique_primary_source_pmids": 91,
        "distinct_free_text_usability_labels": 73,
        "source_review_count": 7,
        "reviewed_raw_record_count": 25,
        "promoted_context_bound_claim_count": 16,
    }
    if any(getattr(audit, key) != value for key, value in expected_counts.items()):
        raise HepatocyteQuantityEvidenceError("Quantity harvest audit counts changed")
    if audit.organism_bucket_counts != {
        "HepaRG": 1,
        "human": 74,
        "mouse": 8,
        "other": 36,
        "rat": 49,
    }:
        raise HepatocyteQuantityEvidenceError("Quantity organism partitions changed")
    if audit.exact_duplicate_records or audit.bucket_inconsistency_rows != (167,):
        raise HepatocyteQuantityEvidenceError("Quantity anomaly ledger changed")
    return audit


def hepatocyte_quantity_harvest_snapshot() -> dict[str, object]:
    audit = validate_quantity_harvest()
    review = json.loads(SOURCE_REVIEW_PATH.read_text(encoding="utf-8"))
    return {
        "version": VERSION,
        "status": audit.status,
        "policy": (
            "Raw rows retain their original species, model, assay and denominator. "
            "Only explicitly reviewed claims enter context-matched evidence modules; "
            "none initializes or drives the healthy-PHH runtime."
        ),
        "audit": audit.to_dict(),
        "source_reviews": review["reviews"],
        "integration_gates": {
            "lossless_raw_bundle_ready": True,
            "same_assay_kinetic_evidence_ready": True,
            "matching_protocol_injury_observations_ready": True,
            "automatic_parameter_activation": False,
            "healthy_phh_initialization_ready": False,
            "whole_cell_rate_coupling_ready": False,
            "predictive_ready": False,
        },
        "raw_paths": tuple(
            f"data/hepatocyte_quantities/raw/{name}"
            for name in (
                "METHODS_README_quantities.md",
                "hepatocyte_quantities_master.csv",
                "hepatocyte_quantities_master.json",
                "hepatocyte_quantities_human.csv",
                "hepatocyte_quantities_HepaRG.csv",
                "hepatocyte_quantities_mouse.csv",
                "hepatocyte_quantities_rat.csv",
                "hepatocyte_quantities_other.csv",
                "manifest.v1.json",
            )
        ),
    }
