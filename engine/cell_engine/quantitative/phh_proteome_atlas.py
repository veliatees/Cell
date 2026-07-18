"""Donor-resolved absolute protein abundance for primary human hepatocytes.

The source entity is a MaxQuant protein group and the absolute denominator is
one nucleus. APIs preserve both boundaries: they never merge protein groups by
gene and never relabel a per-nucleus value as a per-hepatocyte measurement.
"""

from __future__ import annotations

import json
import statistics
from functools import lru_cache
from math import isclose, isfinite
from pathlib import Path
from typing import Any

from cell_engine.core.provenance import SourceReference


DATE_VERIFIED = "2026-07-16"
VERSION = "phh_absolute_proteome_atlas_v1"
SCHEMA_VERSION = "cell.phh-absolute-proteome-atlas.v1"
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "phh_baseline"
    / "curated"
    / "wisniewski2016_donor_proteome_atlas.v1.json"
)
DONOR_IDS = tuple("ABCDEFG")


PHH_PROTEOME_ATLAS_SOURCES: dict[str, SourceReference] = {
    "human_hepatocyte_proteome_2016": SourceReference(
        id="human_hepatocyte_proteome_2016",
        title=(
            "In-depth quantitative analysis and comparison of the human "
            "hepatocyte and hepatoma cell line HepG2 proteomes"
        ),
        url="https://doi.org/10.1016/j.jprot.2016.01.016",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Official supplementary workbooks provide seven-donor protein-group "
            "concentrations and proteomic-ruler copies per nucleus."
        ),
    ),
    "massive_msv000079562": SourceReference(
        id="massive_msv000079562",
        title="Human hepatocyte and HepG2 proteome mass-spectrometry dataset",
        url=(
            "https://massive.ucsd.edu/ProteoSAFe/dataset.jsp?"
            "task=2ed487a661bf401caae8285acc1cd507"
        ),
        source_type="open_data_repository",
        date_verified=DATE_VERIFIED,
        notes="MassIVE MSV000079562 / ProteomeXchange PXD001874; CC0 dataset.",
    ),
}


CANONICAL_REFERENCE_ACCESSIONS: dict[str, str] = {
    "ABCB1": "P08183",
    "ABCB11": "O95342",
    "ABCC2": "Q92887",
    "ACTB": "P60709",
    "ADH1B": "P00325",
    "ALB": "P02768",
    "ALDH2": "P05091",
    "ALDOB": "P05062",
    "ARG1": "P05089",
    "ATP1A1": "P05023",
    "CAT": "P04040",
    "CDH1": "P12830",
    "CPS1": "P31327",
    "CYP2E1": "P05181",
    "EGFR": "P00533",
    "FABP1": "P07148",
    "FTL": "P02792",
    "GAPDH": "P04406",
    "GCK": "P35557",
    "GJB1": "P08034",
    "GLUL": "P15104",
    "GSTA1": "P08263",
    "IL6ST": "P40189",
    "INSR": "P06213",
    "MET": "P08581",
    "PCK1": "P35558",
    "SLC10A1": "Q14973",
    "SLC2A2": "P11168",
}


def _require_dict(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"PHH proteome {label} must be an object")
    return value


def _require_list(value: object, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"PHH proteome {label} must be an array")
    return value


@lru_cache(maxsize=1)
def load_phh_proteome_atlas(data_path: Path = DATA_PATH) -> dict[str, Any]:
    payload = json.loads(data_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported PHH absolute-proteome atlas schema")
    validate_phh_proteome_atlas(payload)
    return payload


def validate_phh_proteome_atlas(payload: dict[str, Any]) -> None:
    if payload.get("version") != VERSION or payload.get("date_verified") != DATE_VERIFIED:
        raise ValueError("PHH proteome atlas version or verification date changed")

    artifacts = _require_list(payload.get("source_artifacts"), "source_artifacts")
    expected_hashes = {
        "supplemental_table_1": (
            10_366,
            "9bbc90323a184d8224388b927d720343e6222b5f58b4eba8355a64e4b918f17a",
        ),
        "supplemental_table_2": (
            15_457_204,
            "f84b9c2a4af4cac3ba6394907e50786485c789ab5ed6421de76bf0d52ebb46d0",
        ),
    }
    artifact_map = {
        str(_require_dict(item, "source artifact").get("id")): item
        for item in artifacts
    }
    if set(artifact_map) != set(expected_hashes):
        raise ValueError("PHH proteome source artifact registry changed")
    for source_id, (size, digest) in expected_hashes.items():
        artifact = _require_dict(artifact_map[source_id], "source artifact")
        if artifact.get("size_bytes") != size or artifact.get("sha256") != digest:
            raise ValueError("PHH proteome source checksum changed")

    cohort = _require_dict(payload.get("cohort"), "cohort")
    donors = _require_list(cohort.get("donors"), "donors")
    if (
        cohort.get("donor_count") != 7
        or tuple(str(item.get("id")) for item in donors if isinstance(item, dict))
        != DONOR_IDS
        or cohort.get("not_healthy_volunteers") is not True
    ):
        raise ValueError("PHH proteome donor cohort changed")
    for donor in donors:
        raw = _require_dict(donor, "donor")
        mass = _require_dict(raw.get("total_protein_measurement"), "donor protein mass")
        if (
            not isfinite(float(mass.get("mean_pg_per_nucleus", 0.0)))
            or float(mass.get("mean_pg_per_nucleus", 0.0)) <= 0.0
            or int(raw.get("quantified_target_group_count", 0)) <= 0
            or float(raw.get("sum_of_quantified_target_group_copies_per_nucleus", 0.0))
            <= 0.0
        ):
            raise ValueError("PHH proteome donor summary is invalid")

    contract = _require_dict(payload.get("measurement_contract"), "measurement_contract")
    if (
        contract.get("protein_entity") != "maxquant_protein_group"
        or contract.get("copy_number_denominator") != "per_nucleus"
        or contract.get("source_zero_or_blank_policy")
        != "nonquantified_null_no_imputation"
        or contract.get("distinct_groups_may_not_be_collapsed_by_gene") is not True
    ):
        raise ValueError("PHH proteome measurement contract changed")

    audit = _require_dict(payload.get("source_audit"), "source_audit")
    expected_audit = {
        "source_rows": 9_565,
        "target_rows": 9_386,
        "contaminant_only_rows": 179,
        "quantified_target_rows": 8_689,
        "target_rows_without_positive_phh_value": 697,
        "article_reported_whole_cell_lysate_protein_count": 8_705,
        "article_reported_combined_dataset_protein_count": 9_400,
    }
    if any(int(audit.get(key, -1)) != value for key, value in expected_audit.items()):
        raise ValueError("PHH proteome source-row audit changed")

    records = _require_list(payload.get("protein_groups"), "protein_groups")
    if len(records) != 8_689:
        raise ValueError("PHH quantified protein-group count changed")
    group_ids: set[str] = set()
    observed_coverage = {str(value): 0 for value in range(1, 8)}
    for item in records:
        record = _require_dict(item, "protein group")
        group_id = str(record.get("group_id"))
        if not group_id or group_id in group_ids:
            raise ValueError("PHH proteome group identifiers are not unique")
        group_ids.add(group_id)
        donor_values = _require_dict(record.get("donor_values"), "donor_values")
        if tuple(donor_values) != DONOR_IDS:
            raise ValueError("PHH proteome donor columns changed")
        detected = 0
        for donor_id in DONOR_IDS:
            observation = _require_dict(donor_values[donor_id], "donor observation")
            concentration = observation.get("concentration_pmol_per_mg_total_protein")
            copies = observation.get("copies_per_nucleus")
            if (concentration is None) != (copies is None):
                raise ValueError("PHH concentration/copy missingness diverged")
            if copies is None:
                continue
            if (
                not isfinite(float(copies))
                or float(copies) <= 0.0
                or not isfinite(float(concentration))
                or float(concentration) <= 0.0
            ):
                raise ValueError("PHH proteome contains zero or invalid abundance")
            detected += 1
        if detected != int(record.get("detected_donor_count", 0)):
            raise ValueError("PHH proteome detected-donor count changed")
        observed_coverage[str(detected)] += 1
    if observed_coverage != audit.get("detected_donor_coverage_histogram"):
        raise ValueError("PHH proteome donor-coverage histogram changed")

    gates = _require_dict(payload.get("integration_gates"), "integration_gates")
    if (
        gates.get("static_donor_abundance_query_ready") is not True
        or gates.get("reference_nucleus_population_initialization_ready") is not True
        or any(
            gates.get(key) is not False
            for key in (
                "donor_specific_cell_initialization_ready",
                "binucleate_cell_scaling_ready",
                "surface_localized_copy_number_ready",
                "transport_active_copy_number_ready",
                "protein_turnover_dynamics_ready",
                "automatic_flux_coupling",
                "literal_molecule_rendering_permitted",
                "predictive_ready",
            )
        )
    ):
        raise ValueError("PHH proteome integration gates exceeded the evidence")

    bsep = protein_group_for_accession("O95342", payload=payload)
    mrp2 = protein_group_for_accession("Q92887", payload=payload)
    if not isclose(
        detected_donor_copy_summary(bsep)["median_copies_per_nucleus"],
        419_353.48438855633,
        rel_tol=0.0,
        abs_tol=1e-6,
    ) or not isclose(
        detected_donor_copy_summary(mrp2)["median_copies_per_nucleus"],
        129_918.86133753612,
        rel_tol=0.0,
        abs_tol=1e-6,
    ):
        raise ValueError("canonical BSEP or MRP2 abundance changed")


def protein_groups_for_gene(
    gene: str,
    *,
    payload: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], ...]:
    atlas = payload or load_phh_proteome_atlas()
    records = _require_list(atlas.get("protein_groups"), "protein_groups")
    return tuple(
        record
        for record in records
        if isinstance(record, dict) and gene in record.get("gene_names", [])
    )


def protein_group_for_accession(
    accession: str,
    *,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    atlas = payload or load_phh_proteome_atlas()
    records = _require_list(atlas.get("protein_groups"), "protein_groups")
    matches = [
        record
        for record in records
        if isinstance(record, dict) and accession in record.get("protein_ids", [])
    ]
    if len(matches) != 1:
        raise ValueError(
            f"expected one PHH protein group for accession {accession}, found {len(matches)}"
        )
    return matches[0]


def canonical_gene_reference(
    gene: str,
    *,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        accession = CANONICAL_REFERENCE_ACCESSIONS[gene]
    except KeyError as exc:
        raise ValueError(f"no curated canonical PHH reference for gene {gene}") from exc
    record = protein_group_for_accession(accession, payload=payload)
    if gene not in record["gene_names"]:
        raise ValueError(f"canonical accession {accession} is not assigned to {gene}")
    return record


def detected_donor_copy_summary(record: dict[str, Any]) -> dict[str, float | int]:
    donor_values = _require_dict(record.get("donor_values"), "donor_values")
    copies = [
        float(observation["copies_per_nucleus"])
        for observation in donor_values.values()
        if isinstance(observation, dict) and observation.get("copies_per_nucleus") is not None
    ]
    if not copies:
        raise ValueError("protein group has no quantified PHH donor")
    return {
        "detected_donor_count": len(copies),
        "mean_copies_per_nucleus": statistics.fmean(copies),
        "median_copies_per_nucleus": statistics.median(copies),
        "minimum_copies_per_nucleus": min(copies),
        "maximum_copies_per_nucleus": max(copies),
    }


def donor_reference_nucleus_inventory(donor_id: str) -> dict[str, float]:
    if donor_id not in DONOR_IDS:
        raise ValueError(f"unsupported PHH proteome donor: {donor_id}")
    records = _require_list(load_phh_proteome_atlas()["protein_groups"], "protein_groups")
    inventory: dict[str, float] = {}
    for record in records:
        raw = _require_dict(record, "protein group")
        observation = _require_dict(raw["donor_values"][donor_id], "donor observation")
        copies = observation["copies_per_nucleus"]
        if copies is not None:
            inventory[f"protein_group:{raw['group_id']}"] = float(copies)
    return inventory


def _snapshot_record(record: dict[str, Any]) -> dict[str, Any]:
    summary = detected_donor_copy_summary(record)
    return {
        "group_id": record["group_id"],
        "gene_names": list(record["gene_names"]),
        "protein_names": list(record["protein_names"]),
        "protein_ids": list(record["protein_ids"]),
        "detected_donor_count": record["detected_donor_count"],
        **summary,
        "donor_copies_per_nucleus": {
            donor_id: record["donor_values"][donor_id]["copies_per_nucleus"]
            for donor_id in DONOR_IDS
        },
    }


def phh_proteome_atlas_snapshot() -> dict[str, Any]:
    atlas = load_phh_proteome_atlas()
    records = _require_list(atlas["protein_groups"], "protein_groups")
    selected = [
        {"gene": gene, **_snapshot_record(canonical_gene_reference(gene, payload=atlas))}
        for gene in CANONICAL_REFERENCE_ACCESSIONS
    ]
    ranked = sorted(
        (_snapshot_record(_require_dict(record, "protein group")) for record in records),
        key=lambda record: float(record["median_copies_per_nucleus"]),
        reverse=True,
    )
    donors = _require_list(_require_dict(atlas["cohort"], "cohort")["donors"], "donors")
    donor_masses = [
        float(donor["total_protein_measurement"]["mean_pg_per_nucleus"])
        for donor in donors
    ]
    donor_copy_sums = [
        float(donor["sum_of_quantified_target_group_copies_per_nucleus"])
        for donor in donors
    ]
    return {
        "version": atlas["version"],
        "status": atlas["status"],
        "date_verified": atlas["date_verified"],
        "source": atlas["source"],
        "source_artifacts": atlas["source_artifacts"],
        "cohort": atlas["cohort"],
        "measurement_contract": atlas["measurement_contract"],
        "source_audit": atlas["source_audit"],
        "cohort_arithmetic_audit": atlas["cohort_arithmetic_audit"],
        "selected_canonical_gene_panel": selected,
        "top_protein_groups_by_detected_donor_median": ranked[:20],
        "integration_gates": atlas["integration_gates"],
        "limitations": atlas["limitations"],
        "source_ids": tuple(PHH_PROTEOME_ATLAS_SOURCES),
        "summary": {
            "donor_count": 7,
            "source_protein_group_row_count": 9_565,
            "quantified_target_protein_group_count": 8_689,
            "quantified_in_all_seven_donors_count": int(
                atlas["source_audit"]["detected_donor_coverage_histogram"]["7"]
            ),
            "canonical_gene_panel_count": len(selected),
            "donor_mean_total_protein_pg_per_nucleus": statistics.fmean(donor_masses),
            "donor_minimum_total_protein_pg_per_nucleus": min(donor_masses),
            "donor_maximum_total_protein_pg_per_nucleus": max(donor_masses),
            "donor_mean_quantified_group_copy_sum_per_nucleus": statistics.fmean(
                donor_copy_sums
            ),
            "donor_minimum_quantified_group_copy_sum_per_nucleus": min(donor_copy_sums),
            "donor_maximum_quantified_group_copy_sum_per_nucleus": max(donor_copy_sums),
            "imputed_value_count": 0,
            "surface_localized_copy_count_record_count": 0,
            "active_copy_count_record_count": 0,
            "turnover_parameter_count": 0,
            "flux_parameter_count": 0,
        },
    }
