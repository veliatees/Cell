"""Curated open human-liver atlas with explicit cross-assay boundaries.

The atlas is deliberately not a synthetic donor. It exposes measured geometry,
surface-protein identities, spatial protein gradients and interaction hypotheses
through separate APIs so that normalized scores cannot silently become copy
numbers, kinetic rates or three-dimensional geometry.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from math import isfinite, pi
from pathlib import Path
from typing import Literal

from cell_engine.core.provenance import SourceReference
from cell_engine.quantitative.geometry import (
    HEPATOCYTE_REFERENCE_EQUIVALENT_SPHERE_DIAMETER_UM,
    HEPATOCYTE_REFERENCE_VOLUME_UM3,
    ISOLATED_PHH_MEDIAN_DIAMETER_UM,
)


DATE_VERIFIED = "2026-07-15"
SCHEMA_VERSION = "cell.human-liver-open-atlas.v1"
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "phh_baseline"
    / "curated"
    / "human_liver_open_atlas.v1.json"
)

AtlasZone = Literal["periportal", "midlobular", "pericentral"]


HUMAN_LIVER_OPEN_ATLAS_SOURCES: dict[str, SourceReference] = {
    "fabyan2026_liver_3d": SourceReference(
        id="fabyan2026_liver_3d",
        title="3D reconstruction of human liver tissue at cellular resolution",
        url="https://doi.org/10.1126/sciadv.adz2299",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Open human 3D liver-tissue reconstruction; lobule and central-vein "
            "morphometry constrain future tissue geometry, not one hepatocyte."
        ),
    ),
    "watson2025_human_liver_source_data": SourceReference(
        id="watson2025_human_liver_source_data",
        title="Spatial transcriptomics of healthy and fibrotic human liver at single-cell resolution",
        url="https://www.nature.com/articles/s41467-024-55325-4",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Healthy human-liver source data include 2D segmented area and "
            "nucleus-detection categories for 56,055 hepatocytes."
        ),
    ),
    "watson2025_cellphonedb": SourceReference(
        id="watson2025_cellphonedb",
        title="Spatial transcriptomics of healthy and fibrotic human liver at single-cell resolution",
        url="https://www.nature.com/articles/s41467-024-55325-4",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "CellPhoneDB interaction scores nominate hepatocyte communication "
            "hypotheses; they are neither binding probabilities nor kinetic rates."
        ),
    ),
    "mallanna2016_phh_surfaceome": SourceReference(
        id="mallanna2016_phh_surfaceome",
        title=(
            "Mapping the Cell-Surface N-Glycoproteome of Human Hepatocytes "
            "Reveals Markers for Selecting a Homogeneous Population of "
            "iPSC-Derived Hepatocytes"
        ),
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC5032032/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Cell-surface capture identified 300 N-glycoproteins in primary human "
            "hepatocytes; density, domain and orientation were not measured."
        ),
    ),
    "weiss2026_spatial_proteome": SourceReference(
        id="weiss2026_spatial_proteome",
        title=(
            "Single-cell spatial proteomics maps human liver zonation patterns "
            "and their vulnerability to disruption in tissue architecture"
        ),
        url="https://www.nature.com/articles/s42255-026-01459-2",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Healthy-human single-hepatocyte proteomics across 20 portal-central "
            "bins; normalized gradients are not absolute abundance or flux effects."
        ),
    ),
}


@dataclass(frozen=True)
class SpatialProteinObservation:
    protein: str
    binned_expression_percent: tuple[float, ...]
    coefficient: float
    p_value: float
    q_value: float
    enriched_region: Literal["periportal", "pericentral", "flat"]
    zonated: bool
    strong_zonated: bool
    source_id: str = "weiss2026_spatial_proteome"

    def to_dict(self) -> dict[str, object]:
        return {
            "protein": self.protein,
            "binned_expression_percent": list(self.binned_expression_percent),
            "coefficient": self.coefficient,
            "p_value": self.p_value,
            "q_value": self.q_value,
            "enriched_region": self.enriched_region,
            "zonated": self.zonated,
            "strong_zonated": self.strong_zonated,
            "source_id": self.source_id,
        }


def _require_dict(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"human-liver atlas {label} must be an object")
    return value


def _require_list(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"human-liver atlas {label} must be a list")
    return value


@lru_cache(maxsize=1)
def load_human_liver_open_atlas(data_path: Path = DATA_PATH) -> dict[str, object]:
    payload = json.loads(data_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported human-liver open-atlas schema")
    validate_human_liver_open_atlas(payload)
    return payload


def validate_human_liver_open_atlas(payload: dict[str, object]) -> None:
    artifacts = _require_list(payload.get("source_artifacts"), "source_artifacts")
    artifact_ids = {
        str(item.get("id"))
        for item in artifacts
        if isinstance(item, dict)
    }
    if artifact_ids != set(HUMAN_LIVER_OPEN_ATLAS_SOURCES):
        raise ValueError("human-liver atlas source-artifact registry is incomplete")
    for item in artifacts:
        artifact = _require_dict(item, "source artifact")
        if (
            not artifact.get("md5")
            or not artifact.get("sha256")
            or artifact.get("license") != "CC-BY-4.0"
        ):
            raise ValueError("source artifact lacks checksum or open license")

    morphometry = _require_dict(
        payload.get("hepatocyte_morphometry_2d"), "hepatocyte_morphometry_2d"
    )
    if int(morphometry.get("cell_count", 0)) != 56_055:
        raise ValueError("healthy human hepatocyte morphometry count changed")
    if morphometry.get("may_replace_3d_cell_geometry") is not False:
        raise ValueError("2D morphometry cannot replace 3D cell geometry")
    expected_cluster_mapping = {
        "Hep_1": "periportal",
        "Hep_2": "midlobular",
        "Hep_3": "pericentral",
    }
    if morphometry.get("source_reported_cluster_to_zone") != expected_cluster_mapping:
        raise ValueError("source-reported hepatocyte cluster-zone mapping changed")
    area = _require_dict(morphometry.get("segmented_area_um2"), "segmented_area_um2")
    all_area = _require_dict(area.get("all"), "segmented_area_um2.all")
    if not all(
        isfinite(float(all_area[key])) and float(all_area[key]) > 0
        for key in ("p05", "median", "p95")
    ):
        raise ValueError("2D hepatocyte area distribution is invalid")

    surfaceome = _require_dict(
        payload.get("surface_nglycoproteome"), "surface_nglycoproteome"
    )
    proteins = _require_list(surfaceome.get("proteins"), "surface proteins")
    genes = {
        str(item.get("gene"))
        for item in proteins
        if isinstance(item, dict)
    }
    if len(proteins) != 300 or len(genes) != 300:
        raise ValueError("surfaceome must contain 300 unique protein identities")
    for item in proteins:
        protein = _require_dict(item, "surface protein")
        if any(
            protein.get(field) is not None
            for field in ("surface_density_per_um2", "membrane_domain", "orientation")
        ):
            raise ValueError("surfaceome cannot invent density, domain or orientation")

    proteome = _require_dict(payload.get("spatial_proteome"), "spatial_proteome")
    spatial_records = _require_list(proteome.get("records"), "spatial protein records")
    if len(spatial_records) != 1_736:
        raise ValueError("published spatial-proteome row count changed")
    if (
        int(proteome.get("article_reported_protein_count_at_70pct_completeness", 0))
        != 1_741
        or int(proteome.get("supplement_table_record_count", 0)) != 1_736
        or int(proteome.get("article_minus_supplement_record_count", 0)) != 5
    ):
        raise ValueError("article-to-supplement protein-count audit changed")
    strong = [
        item
        for item in spatial_records
        if isinstance(item, dict) and item.get("strong_zonated") is True
    ]
    if len(strong) != 171:
        raise ValueError("published strong-zonated protein count changed")
    if proteome.get("may_scale_metabolic_flux") is not False:
        raise ValueError("normalized protein zonation cannot scale metabolic flux")
    for item in spatial_records:
        record = _require_dict(item, "spatial protein record")
        bins = _require_list(record.get("binned_expression_percent"), "protein bins")
        if len(bins) != 20 or not all(isfinite(float(value)) for value in bins):
            raise ValueError("spatial protein record must retain 20 finite bins")

    hypotheses = _require_dict(
        payload.get("hepatocyte_interaction_hypotheses"),
        "hepatocyte_interaction_hypotheses",
    )
    interaction_records = _require_list(hypotheses.get("records"), "interactions")
    if (
        len(interaction_records) != 209
        or int(hypotheses.get("nonzero_hepatocyte_edge_count", 0)) != 1_806
    ):
        raise ValueError("hepatocyte interaction subset count changed")
    if (
        hypotheses.get("score_is_binding_probability") is not False
        or hypotheses.get("score_is_kinetic_rate") is not False
        or hypotheses.get("may_activate_contact_chain") is not False
    ):
        raise ValueError("interaction hypotheses must remain non-activating")
    if (
        hypotheses.get("source_reported_hepatocyte_cluster_to_zone")
        != expected_cluster_mapping
    ):
        raise ValueError("interaction cluster-zone mapping changed")

    gates = _require_dict(payload.get("integration_gates"), "integration_gates")
    forbidden_true = (
        "may_replace_3d_cell_geometry",
        "surface_density_available",
        "membrane_domain_available",
        "surface_orientation_available",
        "may_scale_flux_from_spatial_proteome",
        "may_activate_interaction_from_score",
        "binding_kinetics_available",
    )
    if any(gates.get(key) is not False for key in forbidden_true):
        raise ValueError("one or more fail-closed atlas gates were promoted")


def surface_protein_observation(gene: str) -> dict[str, object] | None:
    payload = load_human_liver_open_atlas()
    surfaceome = _require_dict(payload["surface_nglycoproteome"], "surfaceome")
    for item in _require_list(surfaceome["proteins"], "surface proteins"):
        if isinstance(item, dict) and item.get("gene") == gene:
            return dict(item)
    return None


def spatial_protein_observations(
    zone: AtlasZone,
    *,
    strong_only: bool = True,
) -> tuple[SpatialProteinObservation, ...]:
    if zone not in ("periportal", "midlobular", "pericentral"):
        raise ValueError(f"unsupported atlas zone: {zone}")
    if zone == "midlobular":
        return ()
    payload = load_human_liver_open_atlas()
    proteome = _require_dict(payload["spatial_proteome"], "spatial_proteome")
    observations: list[SpatialProteinObservation] = []
    for item in _require_list(proteome["records"], "spatial protein records"):
        raw = _require_dict(item, "spatial protein record")
        if raw["enriched_region"] != zone:
            continue
        if strong_only and raw["strong_zonated"] is not True:
            continue
        observations.append(
            SpatialProteinObservation(
                protein=str(raw["protein"]),
                binned_expression_percent=tuple(
                    float(value) for value in _require_list(
                        raw["binned_expression_percent"], "protein bins"
                    )
                ),
                coefficient=float(raw["coefficient"]),
                p_value=float(raw["p_value"]),
                q_value=float(raw["q_value"]),
                enriched_region=zone,
                zonated=bool(raw["zonated"]),
                strong_zonated=bool(raw["strong_zonated"]),
            )
        )
    return tuple(sorted(observations, key=lambda item: abs(item.coefficient), reverse=True))


def ranked_hepatocyte_interaction_hypotheses(
    *,
    hepatocyte_cluster: str | None = None,
    limit: int | None = None,
) -> tuple[dict[str, object], ...]:
    if hepatocyte_cluster not in (None, "Hep_1", "Hep_2", "Hep_3"):
        raise ValueError(f"unsupported hepatocyte cluster: {hepatocyte_cluster}")
    payload = load_human_liver_open_atlas()
    section = _require_dict(
        payload["hepatocyte_interaction_hypotheses"], "interactions"
    )
    ranked: list[dict[str, object]] = []
    for item in _require_list(section["records"], "interaction records"):
        record = _require_dict(item, "interaction record")
        edges = [
            _require_dict(edge, "hepatocyte edge")
            for edge in _require_list(record["hepatocyte_edges"], "hepatocyte edges")
        ]
        matching_edges = [
            edge
            for edge in edges
            if hepatocyte_cluster is None
            or edge["sender"] == hepatocyte_cluster
            or edge["receiver"] == hepatocyte_cluster
        ]
        if not matching_edges:
            continue
        maximum_score = max(
            float(edge["score"])
            for edge in matching_edges
        )
        ranked.append(
            {
                **record,
                "matching_hepatocyte_edges": matching_edges,
                "maximum_source_score": maximum_score,
            }
        )
    ranked.sort(
        key=lambda item: (-float(item["maximum_source_score"]), str(item["id"]))
    )
    return tuple(ranked if limit is None else ranked[:limit])


def human_liver_open_atlas_snapshot(zone: AtlasZone) -> dict[str, object]:
    payload = load_human_liver_open_atlas()
    morphometry = _require_dict(payload["hepatocyte_morphometry_2d"], "morphometry")
    area = _require_dict(morphometry["segmented_area_um2"], "segmented area")
    all_area = _require_dict(area["all"], "all segmented area")
    surfaceome = _require_dict(payload["surface_nglycoproteome"], "surfaceome")
    proteome = _require_dict(payload["spatial_proteome"], "spatial proteome")
    interactions = _require_dict(
        payload["hepatocyte_interaction_hypotheses"], "interactions"
    )
    cluster_to_zone = _require_dict(
        morphometry["source_reported_cluster_to_zone"], "cluster-zone mapping"
    )
    zone_to_cluster = {
        str(mapped_zone): str(cluster)
        for cluster, mapped_zone in cluster_to_zone.items()
    }
    selected_cluster = zone_to_cluster[zone]
    selected_interactions = ranked_hepatocyte_interaction_hypotheses(
        hepatocyte_cluster=selected_cluster
    )
    spatial = spatial_protein_observations(zone)
    canonical_cross_section_um2 = pi * (HEPATOCYTE_REFERENCE_EQUIVALENT_SPHERE_DIAMETER_UM / 2.0) ** 2
    return {
        "version": "human_liver_open_atlas_v1",
        "status": payload["status"],
        "date_verified": payload["date_verified"],
        "selected_zone": zone,
        "source_artifacts": [
            {
                "id": item["id"],
                "title": item["title"],
                "paper_url": item["paper_url"],
                "artifact_url": item["artifact_url"],
                "license": item["license"],
                "md5": item["md5"],
                "sha256": item["sha256"],
            }
            for item in _require_list(payload["source_artifacts"], "source artifacts")
            if isinstance(item, dict)
        ],
        "tissue_architecture": payload["tissue_architecture"],
        "morphometry_2d": {
            "cell_count": morphometry["cell_count"],
            "segmented_area_um2": area,
            "selected_zone_cluster": selected_cluster,
            "selected_zone_segmented_area_um2": _require_dict(
                area["by_cluster"], "cluster area distributions"
            )[selected_cluster],
            "cluster_zone_mapping_status": morphometry["cluster_zone_mapping_status"],
            "detected_nuclei_count": morphometry["detected_nuclei_count"],
            "canonical_geometry_context_check": {
                "active_3d_normal_control_median_volume_um3": HEPATOCYTE_REFERENCE_VOLUME_UM3,
                "volume_equivalent_sphere_diameter_um": HEPATOCYTE_REFERENCE_EQUIVALENT_SPHERE_DIAMETER_UM,
                "isolated_phh_median_diameter_cross_check_um": ISOLATED_PHH_MEDIAN_DIAMETER_UM,
                "equivalent_sphere_great_circle_area_um2": canonical_cross_section_um2,
                "within_in_situ_segmented_area_p05_p95": (
                    float(all_area["p05"])
                    <= canonical_cross_section_um2
                    <= float(all_area["p95"])
                ),
                "comparison_role": "contextual_range_check_only",
                "may_calibrate_3d_geometry": False,
            },
            "may_replace_3d_cell_geometry": False,
        },
        "surfaceome": {
            "observed_protein_count": surfaceome["observed_protein_count"],
            "reported_cd_molecule_count": surfaceome["reported_cd_molecule_count"],
            "reported_transmembrane_count": surfaceome["reported_transmembrane_count"],
            "pathway_relevant_gene_observation": surfaceome[
                "pathway_relevant_gene_observation"
            ],
            "density_available": surfaceome["density_available"],
            "membrane_domain_available": surfaceome["membrane_domain_available"],
            "orientation_available": surfaceome["orientation_available"],
            "full_record_count_in_curated_bundle": len(
                _require_list(surfaceome["proteins"], "surface proteins")
            ),
        },
        "spatial_proteome": {
            "protein_count": proteome["protein_count"],
            "article_reported_protein_count_at_70pct_completeness": proteome[
                "article_reported_protein_count_at_70pct_completeness"
            ],
            "supplement_table_record_count": proteome[
                "supplement_table_record_count"
            ],
            "article_minus_supplement_record_count": proteome[
                "article_minus_supplement_record_count"
            ],
            "strong_zonated_count": proteome["strong_zonated_count"],
            "strong_periportal_count": proteome["strong_periportal_count"],
            "strong_pericentral_count": proteome["strong_pericentral_count"],
            "selected_zone_strong_count": len(spatial),
            "selected_zone_top_proteins": [
                item.to_dict() for item in spatial[:12]
            ],
            "midlobular_specific_class_available": False,
            "may_scale_metabolic_flux": False,
        },
        "interaction_hypotheses": {
            "source_interaction_count": interactions["source_interaction_count"],
            "retained_hepatocyte_interaction_count": interactions[
                "retained_hepatocyte_interaction_count"
            ],
            "nonzero_hepatocyte_edge_count": interactions[
                "nonzero_hepatocyte_edge_count"
            ],
            "selected_zone_cluster": selected_cluster,
            "selected_zone_interaction_count": len(selected_interactions),
            "selected_zone_nonzero_edge_count": sum(
                len(item["matching_hepatocyte_edges"])
                for item in selected_interactions
            ),
            "top_ranked_candidates": list(
                selected_interactions[:12]
            ),
            "score_is_binding_probability": False,
            "score_is_kinetic_rate": False,
            "may_activate_contact_chain": False,
        },
        "integration_gates": payload["integration_gates"],
        "source_ids": list(HUMAN_LIVER_OPEN_ATLAS_SOURCES),
        "limitations": payload["global_limitations"],
    }


__all__ = [
    "AtlasZone",
    "DATA_PATH",
    "HUMAN_LIVER_OPEN_ATLAS_SOURCES",
    "SpatialProteinObservation",
    "human_liver_open_atlas_snapshot",
    "load_human_liver_open_atlas",
    "ranked_hepatocyte_interaction_hypotheses",
    "spatial_protein_observations",
    "surface_protein_observation",
    "validate_human_liver_open_atlas",
]
