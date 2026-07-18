"""Checksummed healthy-human 3D hepatocyte morphometry.

The source exposes aggregate normal-control measurements, not individual-cell
meshes. This module therefore permits reference-volume and aggregate lipid-
fraction initialization while keeping shape, domain-area and contact-ground-
truth gates closed.
"""

from __future__ import annotations

import json
from functools import lru_cache
from math import isfinite, pi
from pathlib import Path

from cell_engine.core.provenance import SourceReference


DATE_VERIFIED = "2026-07-17"
SCHEMA_VERSION = "cell.human-hepatocyte-3d-morphometry.v1"
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "phh_baseline"
    / "curated"
    / "human_hepatocyte_3d_morphometry.v1.json"
)

HUMAN_NC_3D_HEPATOCYTE_MEDIAN_VOLUME_UM3 = 5657.07116
HUMAN_NC_3D_HEPATOCYTE_VOLUME_MAD_UM3 = 744.875484
HUMAN_NC_3D_RECONSTRUCTION_COUNT = 5
HUMAN_NC_3D_LIPID_DROPLET_VOLUME_PERCENT = 0.507807
HUMAN_NC_3D_LIPID_DROPLET_VOLUME_FRACTION = 0.00507807
HUMAN_NC_3D_LIPID_DROPLET_VOLUME_MAD_PERCENTAGE_POINTS = 0.403178

HUMAN_HEPATOCYTE_3D_MORPHOMETRY_SOURCES: dict[str, SourceReference] = {
    "segovia_miranda2019_human_liver_3d_morphometry": SourceReference(
        id="segovia_miranda2019_human_liver_3d_morphometry",
        title=(
            "Three-dimensional spatially resolved geometrical and functional "
            "models of human liver tissue reveal new aspects of NAFLD progression"
        ),
        url="https://doi.org/10.1038/s41591-019-0660-7",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Normal-control human liver was reconstructed at 0.3 um isotropic "
            "voxel size. Supplementary Table 3 reports cell-volume and lipid-"
            "droplet-volume summaries across five NC reconstructions."
        ),
    )
}


def _require_dict(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"3D hepatocyte morphometry {label} must be an object")
    return value


def _require_list(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"3D hepatocyte morphometry {label} must be a list")
    return value


def _equivalent_sphere_diameter_um(volume_um3: float) -> float:
    return (6.0 * volume_um3 / pi) ** (1.0 / 3.0)


@lru_cache(maxsize=1)
def load_human_hepatocyte_3d_morphometry(
    data_path: Path = DATA_PATH,
) -> dict[str, object]:
    payload = json.loads(data_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported human-hepatocyte 3D morphometry schema")
    validate_human_hepatocyte_3d_morphometry(payload)
    return payload


def validate_human_hepatocyte_3d_morphometry(payload: dict[str, object]) -> None:
    artifact = _require_dict(payload.get("source_artifact"), "source_artifact")
    if (
        artifact.get("source_id") not in HUMAN_HEPATOCYTE_3D_MORPHOMETRY_SOURCES
        or artifact.get("downloaded_bytes") != 104382
        or artifact.get("md5") != "7dcf837c391ae5433cbeb507d6baf534"
        or artifact.get("sha256")
        != "ab282a593c9b66fd95f764271625f73cd3c5ab33746c8f757c6c60fa2b8ffc3f"
    ):
        raise ValueError("3D hepatocyte source artifact identity changed")

    study = _require_dict(payload.get("study_context"), "study_context")
    voxel = _require_list(study.get("voxel_size_um"), "voxel_size_um")
    groups = _require_dict(study.get("all_group_counts"), "all_group_counts")
    if (
        study.get("species") != "Homo sapiens"
        or study.get("normal_control_reconstruction_count") != 5
        or study.get("all_group_reconstruction_count") != 16
        or study.get("all_group_analyzed_cell_count") != 11278
        or groups != {"NC": 5, "HO": 3, "STEA": 4, "eNASH": 4}
        or voxel != [0.3, 0.3, 0.3]
    ):
        raise ValueError("3D hepatocyte study context changed")

    volume = _require_dict(
        payload.get("normal_control_cell_volume_um3"),
        "normal_control_cell_volume_um3",
    )
    regional_volume = _require_list(volume.get("regional_medians"), "regional_medians")
    regional_volume_mads = _require_list(volume.get("regional_mads"), "regional_mads")
    regional_volume_n = _require_list(
        volume.get("regional_n_reconstructions"), "regional_n_reconstructions"
    )
    if (
        volume.get("overall") != HUMAN_NC_3D_HEPATOCYTE_MEDIAN_VOLUME_UM3
        or volume.get("overall_mad") != HUMAN_NC_3D_HEPATOCYTE_VOLUME_MAD_UM3
        or volume.get("n_reconstructions") != HUMAN_NC_3D_RECONSTRUCTION_COUNT
        or len(regional_volume) != 10
        or len(regional_volume_mads) != 10
        or regional_volume_n != [5] * 10
        or not all(isfinite(float(value)) and float(value) > 0 for value in regional_volume)
        or not all(isfinite(float(value)) and float(value) >= 0 for value in regional_volume_mads)
        or volume.get("diameter_and_area_are_derived_not_measured") is not True
        or volume.get("may_define_single_cell_shape_distribution") is not False
    ):
        raise ValueError("normal-control 3D cell-volume measurements changed")
    derived_diameter = _equivalent_sphere_diameter_um(
        HUMAN_NC_3D_HEPATOCYTE_MEDIAN_VOLUME_UM3
    )
    if (
        abs(float(volume["derived_equivalent_sphere_diameter_um"]) - derived_diameter)
        > 1.0e-12
        or abs(
            float(volume["derived_equivalent_sphere_surface_area_um2"])
            - pi * derived_diameter**2
        )
        > 1.0e-9
    ):
        raise ValueError("3D hepatocyte equivalent geometry is inconsistent")

    lipid = _require_dict(
        payload.get("normal_control_lipid_droplet_volume_percent"),
        "normal_control_lipid_droplet_volume_percent",
    )
    regional_lipid = _require_list(lipid.get("regional_medians"), "regional_medians")
    regional_lipid_mads = _require_list(
        lipid.get("regional_mads_percentage_points"),
        "regional_mads_percentage_points",
    )
    if (
        lipid.get("overall") != HUMAN_NC_3D_LIPID_DROPLET_VOLUME_PERCENT
        or lipid.get("overall_mad_percentage_points")
        != HUMAN_NC_3D_LIPID_DROPLET_VOLUME_MAD_PERCENTAGE_POINTS
        or lipid.get("fraction_of_cell_volume")
        != HUMAN_NC_3D_LIPID_DROPLET_VOLUME_FRACTION
        or lipid.get("n_reconstructions") != 5
        or len(regional_lipid) != 10
        or len(regional_lipid_mads) != 10
        or lipid.get("may_define_droplet_count_or_size_distribution") is not False
        or lipid.get("may_define_dynamic_nutritional_response") is not False
    ):
        raise ValueError("normal-control 3D lipid-droplet measurements changed")

    pooled = _require_dict(
        payload.get("pooled_all_group_cell_volume_classes_um3"),
        "pooled_all_group_cell_volume_classes_um3",
    )
    if (
        pooled.get("small_upper_exclusive") != 5800.0
        or pooled.get("medium_lower_inclusive") != 5800.0
        or pooled.get("medium_upper_inclusive") != 11000.0
        or pooled.get("large_lower_exclusive") != 11000.0
        or pooled.get("may_initialize_healthy_population_mixture") is not False
    ):
        raise ValueError("pooled disease-study cell-volume classes changed")

    conflict = _require_dict(
        payload.get("historical_stereology_conflict"),
        "historical_stereology_conflict",
    )
    if (
        conflict.get("historical_mean_volume_um3") != 2850.0
        or conflict.get("new_to_historical_ratio") != 1.9849372491228072
        or not str(conflict.get("resolution_policy", "")).startswith("do_not_average")
    ):
        raise ValueError("historical 3D/stereology conflict policy changed")

    gates = _require_dict(payload.get("integration_gates"), "integration_gates")
    if (
        gates.get("aggregate_3d_normal_control_volume_available") is not True
        or gates.get("aggregate_3d_normal_control_lipid_fraction_available") is not True
        or gates.get("may_initialize_reference_volume") is not True
        or gates.get("may_initialize_aggregate_lipid_fraction") is not True
        or gates.get("individual_cell_boundary_mesh_available") is not False
        or gates.get("healthy_population_shape_distribution_available") is not False
        or gates.get("quantitative_apical_basal_lateral_surface_area_available")
        is not False
        or gates.get("may_replace_runtime_polyhedron_with_measured_mesh") is not False
        or gates.get("may_calibrate_contact_patch_ground_truth") is not False
    ):
        raise ValueError("3D hepatocyte evidence gates exceed available measurements")


def human_hepatocyte_3d_morphometry_snapshot() -> dict[str, object]:
    payload = load_human_hepatocyte_3d_morphometry()
    return {
        "version": payload["version"],
        "status": payload["status"],
        "date_verified": payload["date_verified"],
        "policy": payload["policy"],
        "source_artifact": payload["source_artifact"],
        "study_context": payload["study_context"],
        "normal_control_cell_volume_um3": payload[
            "normal_control_cell_volume_um3"
        ],
        "normal_control_lipid_droplet_volume_percent": payload[
            "normal_control_lipid_droplet_volume_percent"
        ],
        "pooled_all_group_cell_volume_classes_um3": payload[
            "pooled_all_group_cell_volume_classes_um3"
        ],
        "historical_stereology_conflict": payload[
            "historical_stereology_conflict"
        ],
        "integration_gates": payload["integration_gates"],
        "source_ids": list(HUMAN_HEPATOCYTE_3D_MORPHOMETRY_SOURCES),
        "limitations": payload["limitations"],
    }


__all__ = [
    "DATA_PATH",
    "HUMAN_HEPATOCYTE_3D_MORPHOMETRY_SOURCES",
    "HUMAN_NC_3D_HEPATOCYTE_MEDIAN_VOLUME_UM3",
    "HUMAN_NC_3D_HEPATOCYTE_VOLUME_MAD_UM3",
    "HUMAN_NC_3D_LIPID_DROPLET_VOLUME_FRACTION",
    "HUMAN_NC_3D_LIPID_DROPLET_VOLUME_MAD_PERCENTAGE_POINTS",
    "HUMAN_NC_3D_LIPID_DROPLET_VOLUME_PERCENT",
    "HUMAN_NC_3D_RECONSTRUCTION_COUNT",
    "human_hepatocyte_3d_morphometry_snapshot",
    "load_human_hepatocyte_3d_morphometry",
    "validate_human_hepatocyte_3d_morphometry",
]
