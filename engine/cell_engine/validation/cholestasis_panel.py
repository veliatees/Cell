from __future__ import annotations

import csv
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CHOLESTASIS_DATA_ROOT = REPOSITORY_ROOT / "data" / "cholestasis"
RAW_PANEL_ROOT = CHOLESTASIS_DATA_ROOT / "raw"
CURATED_PANEL_ROOT = CHOLESTASIS_DATA_ROOT / "curated"
MASTER_CSV_PATH = RAW_PANEL_ROOT / "cholestasis_master_panel.csv"
MASTER_JSON_PATH = RAW_PANEL_ROOT / "cholestasis_master_panel.json"
CURATED_ANCHORS_PATH = CURATED_PANEL_ROOT / "calibration_anchors.json"

PANEL_COLUMNS = (
    "track",
    "condition_class",
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
    "pmid",
    "doi",
    "figure_table",
    "notes",
)
ORGANISM_BUCKETS = ("HepaRG", "human", "mouse", "other", "rat")
MISSING_TOKENS = frozenset(("", "NR", "NOT_REPORTED"))

_STRICT_NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)"
_STRICT_VALUE_RE = re.compile(
    rf"^\s*(?P<approx>[~≈])?(?P<low>{_STRICT_NUMBER})"
    rf"(?:\s*[-–]\s*(?P<high>{_STRICT_NUMBER}))?\s*$"
)


class EvidencePanelError(ValueError):
    pass


@dataclass(frozen=True)
class CholestasisObservation:
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
class CholestasisPanelAudit:
    total_records: int
    track_counts: Mapping[str, int]
    organism_bucket_counts: Mapping[str, int]
    condition_class_counts: Mapping[str, int]
    strict_numeric_value_records: int
    reported_time_records: int
    reported_error_records: int
    reported_sample_size_records: int
    unique_primary_sources: int
    exact_duplicate_records: int


@dataclass(frozen=True)
class CholestasisCalibrationAnchor:
    id: str
    raw_rows: tuple[int, ...]
    pmid: str
    doi: str
    url: str
    organism: str
    model: str
    intervention_type: str
    endpoint: str
    time_h: float | None
    value_low: float | None
    value_high: float | None
    qualifier: str
    unit: str
    error_type: str | None
    error: float | None
    sample_size: int | None
    model_use: str
    applicability: str
    limitations: str


def is_missing(value: str) -> bool:
    return value.strip() in MISSING_TOKENS


def parse_strict_numeric_value(value: str) -> StrictNumericValue | None:
    """Parse only standalone scalars/ranges; never infer numbers from prose."""
    if is_missing(value):
        return None
    match = _STRICT_VALUE_RE.fullmatch(value)
    if match is None:
        return None
    low = float(match.group("low"))
    high_token = match.group("high")
    high = float(high_token) if high_token is not None else low
    if high < low:
        raise EvidencePanelError(f"Numeric range is descending: {value!r}")
    approximate = match.group("approx") is not None
    ranged = high_token is not None
    qualifier: Literal["exact", "approximate", "range", "approximate_range"]
    if approximate and ranged:
        qualifier = "approximate_range"
    elif approximate:
        qualifier = "approximate"
    elif ranged:
        qualifier = "range"
    else:
        qualifier = "exact"
    return StrictNumericValue(low=low, high=high, qualifier=qualifier)


def load_master_panel(path: Path = MASTER_CSV_PATH) -> tuple[CholestasisObservation, ...]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != PANEL_COLUMNS:
            raise EvidencePanelError("Unexpected cholestasis panel columns")
        observations: list[CholestasisObservation] = []
        for row_number, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise EvidencePanelError(f"Malformed CSV record at row {row_number}")
            observations.append(
                CholestasisObservation(
                    row_number=row_number,
                    values={column: str(row[column]) for column in PANEL_COLUMNS},
                )
            )
    return tuple(observations)


def audit_panel(observations: tuple[CholestasisObservation, ...]) -> CholestasisPanelAudit:
    rows = [observation.values for observation in observations]
    fingerprints = [tuple(row[column] for column in PANEL_COLUMNS) for row in rows]
    source_keys = {
        (row["pmid"], row["doi"])
        for row in rows
        if not is_missing(row["pmid"]) or not is_missing(row["doi"])
    }
    return CholestasisPanelAudit(
        total_records=len(rows),
        track_counts=dict(sorted(Counter(row["track"] for row in rows).items())),
        organism_bucket_counts=dict(sorted(Counter(row["organism_bucket"] for row in rows).items())),
        condition_class_counts=dict(sorted(Counter(row["condition_class"] for row in rows).items())),
        strict_numeric_value_records=sum(parse_strict_numeric_value(row["value"]) is not None for row in rows),
        reported_time_records=sum(not is_missing(row["time_h"]) for row in rows),
        reported_error_records=sum(not is_missing(row["error"]) for row in rows),
        reported_sample_size_records=sum(not is_missing(row["n"]) for row in rows),
        unique_primary_sources=len(source_keys),
        exact_duplicate_records=len(fingerprints) - len(set(fingerprints)),
    )


def validate_panel_bundle() -> CholestasisPanelAudit:
    observations = load_master_panel()
    csv_rows = [dict(observation.values) for observation in observations]
    json_rows = json.loads(MASTER_JSON_PATH.read_text(encoding="utf-8"))
    if csv_rows != json_rows:
        raise EvidencePanelError("Master CSV and JSON are not identical")

    for bucket in ORGANISM_BUCKETS:
        path = RAW_PANEL_ROOT / f"cholestasis_panel_{bucket}.csv"
        subset = load_master_panel(path)
        subset_rows = [dict(observation.values) for observation in subset]
        expected = [row for row in csv_rows if row["organism_bucket"] == bucket]
        if subset_rows != expected:
            raise EvidencePanelError(f"{bucket} panel is not an exact master-panel partition")

    audit = audit_panel(observations)
    if audit.exact_duplicate_records:
        raise EvidencePanelError("Master panel contains exact duplicate records")
    return audit


def load_calibration_anchors(
    path: Path = CURATED_ANCHORS_PATH,
) -> tuple[CholestasisCalibrationAnchor, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise EvidencePanelError("Unsupported cholestasis anchor schema")
    anchors: list[CholestasisCalibrationAnchor] = []
    for item in payload.get("anchors", ()):
        value = item.get("value") or {}
        error = item.get("error") or {}
        anchors.append(
            CholestasisCalibrationAnchor(
                id=str(item["id"]),
                raw_rows=tuple(int(row) for row in item["raw_rows"]),
                pmid=str(item["source"]["pmid"]),
                doi=str(item["source"]["doi"]),
                url=str(item["source"]["url"]),
                organism=str(item["organism"]),
                model=str(item["model"]),
                intervention_type=str(item["intervention_type"]),
                endpoint=str(item["endpoint"]),
                time_h=float(item["time_h"]) if item.get("time_h") is not None else None,
                value_low=float(value["low"]) if value.get("low") is not None else None,
                value_high=float(value["high"]) if value.get("high") is not None else None,
                qualifier=str(value.get("qualifier", "qualitative")),
                unit=str(value.get("unit", "qualitative")),
                error_type=str(error["type"]) if error.get("type") is not None else None,
                error=float(error["value"]) if error.get("value") is not None else None,
                sample_size=int(item["sample_size"]) if item.get("sample_size") is not None else None,
                model_use=str(item["model_use"]),
                applicability=str(item["applicability"]),
                limitations=str(item["limitations"]),
            )
        )
    ids = [anchor.id for anchor in anchors]
    if len(ids) != len(set(ids)):
        raise EvidencePanelError("Curated cholestasis anchors contain duplicate IDs")
    return tuple(anchors)
