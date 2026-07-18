from __future__ import annotations

from dataclasses import dataclass
from math import pi

from cell_engine.core.cell_definition import CellDefinition
from cell_engine.core.provenance import SourceReference
from cell_engine.quantitative.human_hepatocyte_3d_morphometry import (
    HUMAN_HEPATOCYTE_3D_MORPHOMETRY_SOURCES,
    HUMAN_NC_3D_HEPATOCYTE_MEDIAN_VOLUME_UM3,
    HUMAN_NC_3D_HEPATOCYTE_VOLUME_MAD_UM3,
    HUMAN_NC_3D_LIPID_DROPLET_VOLUME_FRACTION,
    HUMAN_NC_3D_LIPID_DROPLET_VOLUME_MAD_PERCENTAGE_POINTS,
    HUMAN_NC_3D_RECONSTRUCTION_COUNT,
)

# Physical constants
AVOGADRO = 6.02214076e23  # 1 / mol (exact, SI 2019 redefinition)
LITERS_PER_PICOLITER = 1.0e-12
LITERS_PER_CUBIC_MICROMETER = 1.0e-15

# Olander et al. measured isolated primary human hepatocytes from 54
# cryopreserved batches: median diameter 18.4 um and 88% in 12-26 um. The
# equivalent-sphere volume/area below are mathematical consequences of that
# measured diameter, not independent morphometric observations and not an
# in-situ liver-plate shape claim. DOI: 10.1002/jcp.30273.
ISOLATED_PHH_MEDIAN_DIAMETER_UM = 18.4
ISOLATED_PHH_OBSERVED_INTERVAL_UM = (12.0, 26.0)
ISOLATED_PHH_INTERVAL_FRACTION = 0.88
ISOLATED_PHH_CRYOPRESERVED_BATCH_COUNT = 54

# Duarte et al. measured normal human liver biopsy material from five selected
# hospital cases using stereology. The reported mean hepatocyte volume applies
# to the intermediate lobular zone in situ. The publication abstract reports
# ``2850 +/- 99.9 um3`` without identifying the +/- statistic, so it is retained
# exactly as an as-reported uncertainty rather than relabelled SD or SEM.
IN_SITU_MIDLOBULAR_PHH_MEAN_VOLUME_UM3 = 2850.0
IN_SITU_MIDLOBULAR_PHH_REPORTED_PLUS_MINUS_UM3 = 99.9
IN_SITU_MIDLOBULAR_PHH_CASE_COUNT = 5

PHH_GEOMETRY_SOURCES: dict[str, SourceReference] = {
    **HUMAN_HEPATOCYTE_3D_MORPHOMETRY_SOURCES,
    "duarte1989_human_hepatocyte_volume": SourceReference(
        id="duarte1989_human_hepatocyte_volume",
        title="Baseline volume data of human liver parenchymal cell",
        url="https://pubmed.ncbi.nlm.nih.gov/2752360/",
        source_type="primary_paper",
        date_verified="2026-07-17",
        notes=(
            "Stereological normal-human-liver biopsy estimate for the intermediate "
            "lobular zone: mean hepatocyte volume 2850 +/- 99.9 um3 across five "
            "selected cases; the abstract does not identify the +/- statistic."
        ),
    ),
    "olander2021_human_hepatocyte_size": SourceReference(
        id="olander2021_human_hepatocyte_size",
        title="Hepatocyte size fractionation allows dissection of human liver zonation",
        url="https://doi.org/10.1002/jcp.30273",
        source_type="primary_paper",
        date_verified="2026-07-17",
        notes=(
            "Median diameter 18.4 um across 54 isolated cryopreserved PHH batches; "
            "88% of measured cells were 12-26 um."
        ),
    ),
    "fabyan2026_human_liver_3d": SourceReference(
        id="fabyan2026_human_liver_3d",
        title="3D reconstruction of human liver tissue at cellular resolution",
        url="https://doi.org/10.1126/sciadv.adz2299",
        source_type="primary_paper",
        date_verified="2026-07-17",
        notes=(
            "Healthy-human tissue-scale architecture and lobule geometry; not a "
            "donor-general single-hepatocyte boundary or organelle mesh."
        ),
    ),
}

# Canonical proxy coordinates shared by the cell definition and collision
# world. This is an engine-renderer convention, not measured PHH morphometry.
HEPATOCYTE_CANONICAL_CANALICULAR_DIRECTION = (1.0, 0.0, 0.0)
HEPATOCYTE_CANONICAL_SINUSOIDAL_DIRECTION = (-1.0, 0.0, 0.0)
HEPATOCYTE_CANONICAL_POLARITY_AXIS = HEPATOCYTE_CANONICAL_CANALICULAR_DIRECTION


def sphere_volume_um3_from_diameter(diameter_um: float) -> float:
    """Exact Euclidean sphere volume for a diameter in micrometres."""
    if diameter_um <= 0:
        raise ValueError("diameter_um must be positive")
    return (pi / 6.0) * diameter_um**3


def sphere_surface_area_um2_from_diameter(diameter_um: float) -> float:
    """Exact Euclidean sphere area for a diameter in micrometres."""
    if diameter_um <= 0:
        raise ValueError("diameter_um must be positive")
    return pi * diameter_um**2


def sphere_diameter_um_from_volume(volume_um3: float) -> float:
    """Exact equivalent-sphere diameter for a volume in cubic micrometres."""
    if volume_um3 <= 0:
        raise ValueError("volume_um3 must be positive")
    return (6.0 * volume_um3 / pi) ** (1.0 / 3.0)


ISOLATED_PHH_EQUIVALENT_SPHERE_VOLUME_UM3 = sphere_volume_um3_from_diameter(
    ISOLATED_PHH_MEDIAN_DIAMETER_UM
)
ISOLATED_PHH_EQUIVALENT_SPHERE_SURFACE_AREA_UM2 = sphere_surface_area_um2_from_diameter(
    ISOLATED_PHH_MEDIAN_DIAMETER_UM
)
HEPATOCYTE_REFERENCE_VOLUME_UM3 = HUMAN_NC_3D_HEPATOCYTE_MEDIAN_VOLUME_UM3
HEPATOCYTE_REFERENCE_EQUIVALENT_SPHERE_DIAMETER_UM = sphere_diameter_um_from_volume(
    HEPATOCYTE_REFERENCE_VOLUME_UM3
)
HEPATOCYTE_REFERENCE_EQUIVALENT_SPHERE_SURFACE_AREA_UM2 = sphere_surface_area_um2_from_diameter(
    HEPATOCYTE_REFERENCE_EQUIVALENT_SPHERE_DIAMETER_UM
)
HEPATOCYTE_CELL_VOLUME_L = (
    HEPATOCYTE_REFERENCE_VOLUME_UM3 * LITERS_PER_CUBIC_MICROMETER
)


def hepatocyte_geometry_reference_snapshot() -> dict[str, object]:
    """Return the measured geometry hierarchy and explicit 3D readiness gates."""

    return {
        "version": "human_hepatocyte_geometry_reference_v2",
        "status": "healthy_human_aggregate_3d_volume_active_individual_mesh_blocked",
        "canonical_reference": {
            "biological_context": "normal_control_human_liver_tissue_3d_reconstruction",
            "summary_statistic": "source_reported_median",
            "cell_volume_um3": HEPATOCYTE_REFERENCE_VOLUME_UM3,
            "cell_volume_mad_um3": HUMAN_NC_3D_HEPATOCYTE_VOLUME_MAD_UM3,
            "reconstruction_count": HUMAN_NC_3D_RECONSTRUCTION_COUNT,
            "voxel_size_um": (0.3, 0.3, 0.3),
            "equivalent_sphere_diameter_um": HEPATOCYTE_REFERENCE_EQUIVALENT_SPHERE_DIAMETER_UM,
            "equivalent_sphere_surface_area_um2": HEPATOCYTE_REFERENCE_EQUIVALENT_SPHERE_SURFACE_AREA_UM2,
            "diameter_and_area_are_derived_not_measured": True,
            "source_id": "segovia_miranda2019_human_liver_3d_morphometry",
        },
        "aggregate_lipid_droplet_reference": {
            "fraction_of_cell_volume": HUMAN_NC_3D_LIPID_DROPLET_VOLUME_FRACTION,
            "median_percent": HUMAN_NC_3D_LIPID_DROPLET_VOLUME_FRACTION * 100.0,
            "mad_percentage_points": HUMAN_NC_3D_LIPID_DROPLET_VOLUME_MAD_PERCENTAGE_POINTS,
            "reconstruction_count": HUMAN_NC_3D_RECONSTRUCTION_COUNT,
            "may_define_count_or_size_distribution": False,
            "may_define_dynamic_nutritional_response": False,
            "source_id": "segovia_miranda2019_human_liver_3d_morphometry",
        },
        "historical_in_situ_stereology_cross_check": {
            "biological_context": "normal_human_intermediate_lobular_zone_in_situ",
            "mean_cell_volume_um3": IN_SITU_MIDLOBULAR_PHH_MEAN_VOLUME_UM3,
            "reported_plus_minus_um3": IN_SITU_MIDLOBULAR_PHH_REPORTED_PLUS_MINUS_UM3,
            "reported_uncertainty_semantics": "as_reported_statistic_not_identified_in_abstract",
            "case_count": IN_SITU_MIDLOBULAR_PHH_CASE_COUNT,
            "active_reference_to_historical_ratio": (
                HEPATOCYTE_REFERENCE_VOLUME_UM3
                / IN_SITU_MIDLOBULAR_PHH_MEAN_VOLUME_UM3
            ),
            "resolution_policy": "not_averaged_direct_3d_NC_median_is_active",
            "source_id": "duarte1989_human_hepatocyte_volume",
        },
        "isolated_phh_cross_check": {
            "median_diameter_um": ISOLATED_PHH_MEDIAN_DIAMETER_UM,
            "observed_interval_um": ISOLATED_PHH_OBSERVED_INTERVAL_UM,
            "interval_fraction": ISOLATED_PHH_INTERVAL_FRACTION,
            "cryopreserved_batch_count": ISOLATED_PHH_CRYOPRESERVED_BATCH_COUNT,
            "equivalent_sphere_volume_um3": ISOLATED_PHH_EQUIVALENT_SPHERE_VOLUME_UM3,
            "role": "independent_isolated_cell_context_not_canonical_in_situ_volume",
            "source_id": "olander2021_human_hepatocyte_size",
        },
        "three_dimensional_evidence": {
            "human_tissue_architecture_available": True,
            "aggregate_normal_control_cell_volume_available": True,
            "aggregate_normal_control_lipid_fraction_available": True,
            "donor_resolved_single_hepatocyte_boundary_mesh_available": False,
            "healthy_population_cell_shape_distribution_available": False,
            "quantitative_membrane_domain_surface_area_available": False,
            "organelle_resolved_human_volume_em_parameterization_available": False,
            "matched_human_contact_interface_mesh_available": False,
            "three_d_required_for": (
                "cell_boundary_and_contact_patch_geometry",
                "sinusoidal_canalicular_domain_topology",
                "organelle_exclusion_and_contact_distances",
                "transport_path_lengths_and_local_surface_area",
            ),
            "three_d_not_required_for": (
                "protein_total_abundance",
                "isolated_assay_km_or_vmax",
                "whole_culture_uptake_or_biliary_excretion_index",
            ),
            "source_ids": (
                "segovia_miranda2019_human_liver_3d_morphometry",
                "fabyan2026_human_liver_3d",
            ),
        },
        "integration_gates": {
            "may_initialize_cell_volume": True,
            "may_initialize_equivalent_scale": True,
            "may_initialize_aggregate_lipid_droplet_fraction": True,
            "may_replace_canonical_surface_with_measured_mesh": False,
            "may_parameterize_organelle_shapes_from_human_3d": False,
            "may_validate_contact_patch_against_human_ground_truth": False,
        },
        "source_ids": tuple(PHH_GEOMETRY_SOURCES),
        "limitations": (
            "The active volume is an aggregate normal-control median across five 3D reconstructions, not a raw individual-cell distribution.",
            "The 1989 stereology mean is retained as a conflicting historical cross-check and is not averaged with the direct 3D measurement.",
            "Equivalent-sphere diameter and surface area preserve volume but do not claim a spherical in-situ hepatocyte.",
            "The measured lipid-droplet fraction does not identify droplet count, size distribution or nutritional dynamics.",
            "The runtime polyhedron remains a volume-equivalent contact proxy until measured single-cell 3D boundaries are available.",
        ),
    }


def validate_hepatocyte_geometry_reference(payload: dict[str, object]) -> None:
    """Fail closed if measured and derived geometry layers are conflated."""

    if payload.get("version") != "human_hepatocyte_geometry_reference_v2":
        raise ValueError("unexpected human hepatocyte geometry reference version")
    canonical = payload.get("canonical_reference")
    lipid = payload.get("aggregate_lipid_droplet_reference")
    historical = payload.get("historical_in_situ_stereology_cross_check")
    isolated = payload.get("isolated_phh_cross_check")
    evidence_3d = payload.get("three_dimensional_evidence")
    gates = payload.get("integration_gates")
    if not all(
        isinstance(item, dict)
        for item in (canonical, lipid, historical, isolated, evidence_3d, gates)
    ):
        raise ValueError("human hepatocyte geometry reference is malformed")
    if (
        canonical["cell_volume_um3"] != HUMAN_NC_3D_HEPATOCYTE_MEDIAN_VOLUME_UM3
        or canonical["cell_volume_mad_um3"] != HUMAN_NC_3D_HEPATOCYTE_VOLUME_MAD_UM3
        or canonical["reconstruction_count"] != 5
        or canonical["voxel_size_um"] != (0.3, 0.3, 0.3)
        or canonical["diameter_and_area_are_derived_not_measured"] is not True
        or lipid["fraction_of_cell_volume"] != HUMAN_NC_3D_LIPID_DROPLET_VOLUME_FRACTION
        or lipid["may_define_count_or_size_distribution"] is not False
        or historical["mean_cell_volume_um3"] != 2850.0
        or historical["resolution_policy"] != "not_averaged_direct_3d_NC_median_is_active"
        or isolated["median_diameter_um"] != 18.4
        or isolated["role"] != "independent_isolated_cell_context_not_canonical_in_situ_volume"
    ):
        raise ValueError("human hepatocyte geometry measurements changed")
    if abs(
        sphere_volume_um3_from_diameter(float(canonical["equivalent_sphere_diameter_um"]))
        - float(canonical["cell_volume_um3"])
    ) > 1.0e-9:
        raise ValueError("equivalent hepatocyte scale no longer preserves measured volume")
    if (
        evidence_3d["human_tissue_architecture_available"] is not True
        or evidence_3d["aggregate_normal_control_cell_volume_available"] is not True
        or evidence_3d["donor_resolved_single_hepatocyte_boundary_mesh_available"] is not False
        or evidence_3d["quantitative_membrane_domain_surface_area_available"] is not False
        or evidence_3d["organelle_resolved_human_volume_em_parameterization_available"] is not False
        or gates["may_initialize_cell_volume"] is not True
        or gates["may_initialize_aggregate_lipid_droplet_fraction"] is not True
        or gates["may_replace_canonical_surface_with_measured_mesh"] is not False
        or gates["may_parameterize_organelle_shapes_from_human_3d"] is not False
    ):
        raise ValueError("human 3D evidence gates exceeded available measurements")
    if set(payload.get("source_ids", ())) != set(PHH_GEOMETRY_SOURCES):
        raise ValueError("human hepatocyte geometry source registry changed")


def relative_radius_from_biomass(biomass: float) -> float:
    """Equivalent-sphere radius relative to a unit-biomass reference cell.

    The cell-cycle biomass proxy is explicitly treated as relative volume/mass.
    For similar shapes, radius therefore scales as ``V^(1/3)``. This is pure
    geometry rather than a fitted biological parameter.
    """
    if biomass < 0:
        raise ValueError("biomass must be non-negative")
    return biomass ** (1.0 / 3.0)


def relative_membrane_area_from_biomass(biomass: float) -> float:
    """Equivalent-sphere membrane area relative to a unit-biomass cell.

    For similar shapes, area scales as ``V^(2/3)``. A value of ``1`` is the
    reference cell surface area; units cancel, so this also works for the
    cycle's normalized membrane-area inventory.
    """
    radius = relative_radius_from_biomass(biomass)
    return radius * radius


def daughter_membrane_area_requirement(biomass: float) -> float:
    """Total area required by two equal-volume daughters after cytokinesis.

    Two daughters have the same total volume as their mother but a larger total
    surface area. The difference is a geometric requirement for membrane
    insertion during cytokinesis, not a fitted strain or decorative effect.
    """
    if biomass < 0:
        raise ValueError("biomass must be non-negative")
    return 2.0 * relative_membrane_area_from_biomass(biomass / 2.0)


def equivalent_sphere_radius_um(volume_l: float) -> float:
    """Radius of a sphere with the supplied volume, returned in micrometres."""
    if volume_l <= 0:
        raise ValueError("volume_l must be positive")
    volume_um3 = volume_l / LITERS_PER_CUBIC_MICROMETER
    return (3.0 * volume_um3 / (4.0 * pi)) ** (1.0 / 3.0)


def equivalent_sphere_surface_area_um2(volume_l: float) -> float:
    """Surface area of the equivalent sphere for a volume in litres."""
    radius_um = equivalent_sphere_radius_um(volume_l)
    return 4.0 * pi * radius_um * radius_um


@dataclass(frozen=True)
class HepatocyteGeometry:
    """Absolute volumes derived from a CellDefinition's compartment fractions.

    The CellDefinition stores ``volume_fraction`` as a fraction of the whole
    cell. We multiply by an absolute cell volume to get per-compartment volumes
    in liters, which is what concentration <-> count conversion requires.
    """

    cell_volume_l: float
    compartment_volume_l: dict[str, float]

    def volume_of(self, compartment_id: str) -> float:
        """Volume (L) of a compartment, falling back to the whole-cell volume.

        Compartments without a declared volume fraction (membranes, external
        sinks) have no soluble volume; callers asking for a concentration there
        get the whole-cell volume as a deliberate coarse fallback.
        """
        return self.compartment_volume_l.get(compartment_id, self.cell_volume_l)

    @property
    def equivalent_sphere_radius_um(self) -> float:
        """Coarse radius for whole-cell geometric sanity checks only."""
        return equivalent_sphere_radius_um(self.cell_volume_l)

    @property
    def equivalent_sphere_surface_area_um2(self) -> float:
        """Coarse surface area for whole-cell membrane sanity checks only."""
        return equivalent_sphere_surface_area_um2(self.cell_volume_l)


def build_hepatocyte_geometry(
    definition: CellDefinition,
    *,
    cell_volume_l: float = HEPATOCYTE_CELL_VOLUME_L,
) -> HepatocyteGeometry:
    """Compute absolute compartment volumes from definition fractions."""
    if cell_volume_l <= 0:
        raise ValueError("cell_volume_l must be positive")

    volumes: dict[str, float] = {}
    for compartment in definition.compartments:
        if compartment.volume_fraction is None:
            continue
        if compartment.volume_fraction < 0:
            raise ValueError(f"negative volume_fraction for {compartment.id}")
        volumes[compartment.id] = compartment.volume_fraction * cell_volume_l

    return HepatocyteGeometry(cell_volume_l=cell_volume_l, compartment_volume_l=volumes)


def molecules_from_concentration_mM(concentration_mM: float, volume_l: float) -> float:
    """Convert a millimolar concentration in a given volume to a molecule count.

    count = C[mol/L] * V[L] * N_A,  with C[mol/L] = concentration_mM * 1e-3.
    """
    if concentration_mM < 0:
        raise ValueError("concentration must be non-negative")
    if volume_l <= 0:
        raise ValueError("volume_l must be positive")
    return concentration_mM * 1.0e-3 * volume_l * AVOGADRO


def concentration_mM_from_molecules(count: float, volume_l: float) -> float:
    """Inverse of :func:`molecules_from_concentration_mM` (returns mM)."""
    if count < 0:
        raise ValueError("count must be non-negative")
    if volume_l <= 0:
        raise ValueError("volume_l must be positive")
    return count / (volume_l * AVOGADRO) / 1.0e-3
