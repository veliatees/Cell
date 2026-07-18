"""Human-specific hepatocyte zonation context without invented effect sizes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain
from cell_engine.quantitative.human_liver_open_atlas import (
    HUMAN_LIVER_OPEN_ATLAS_SOURCES,
    SpatialProteinObservation,
    spatial_protein_observations,
)


HepaticZone = Literal["periportal", "midlobular", "pericentral"]
DATE_VERIFIED = "2026-07-15"

ZONATION_SOURCES: dict[str, SourceReference] = {
    "human_liver_spatial_atlas_2026": SourceReference(
        id="human_liver_spatial_atlas_2026",
        title="A spatial atlas of the healthy human liver from live donors",
        url="https://www.nature.com/articles/s41586-026-10377-y",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Human spatial transcriptomics, MERFISH and protein validation; reports species-specific portal-central expression programs.",
    ),
    "human_liver_single_cell_proteomics_2025": SourceReference(
        id="human_liver_single_cell_proteomics_2025",
        title="Single cell spatial proteomics maps human liver zonation patterns and their vulnerability to fibrosis",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC12027366/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Healthy human single-hepatocyte proteomics across 20 portal-central bins; 413 cells from 14 individuals.",
    ),
    "human_liver_cell_atlas_2019": SourceReference(
        id="human_liver_cell_atlas_2019",
        title="A human liver cell atlas reveals heterogeneity and epithelial progenitors",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC6687507/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Human single-cell RNA-seq supports portal-central hepatocyte heterogeneity and canonical zonation markers.",
    ),
    "human_liver_mps_oxygen_zonation_2017": SourceReference(
        id="human_liver_mps_oxygen_zonation_2017",
        title="Control of oxygen tension recapitulates zone-specific functions in human liver microphysiology systems",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC5661766/",
        source_type="primary_paper",
        date_verified="2026-07-14",
        notes="Human liver MPS under controlled approximately 3-13% oxygen; supports directional zone functions, not an in-situ human sinusoidal pO2 value.",
    ),
    "weiss2026_spatial_proteome": HUMAN_LIVER_OPEN_ATLAS_SOURCES[
        "weiss2026_spatial_proteome"
    ],
}


@dataclass(frozen=True)
class ZonationMarker:
    gene: str
    enriched_zone: HepaticZone
    observed_layer: Literal["transcript", "protein", "transcript_and_protein"]
    source_ids: tuple[str, ...]
    notes: str = ""


@dataclass(frozen=True)
class ZoneContext:
    id: HepaticZone
    label: str
    porto_central_position: str
    oxygen_context: Literal["relatively_higher", "intermediate", "relatively_lower"]
    marker_genes: tuple[str, ...]
    functional_biases: tuple[str, ...]
    niche_signals: tuple[str, ...]
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class HumanMpsOxygenContext:
    model_system: str
    controlled_oxygen_low_percent: float
    controlled_oxygen_high_percent: float
    zone1_supported_functions: tuple[str, ...]
    zone3_supported_functions: tuple[str, ...]
    is_human_in_situ_measurement: bool
    may_initialize_sinusoid_pO2: bool
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class HumanHepatocyteZonationState:
    species: str
    selected_zone: HepaticZone
    status: str
    coordinate_status: str
    zone: ZoneContext
    experimental_oxygen_context: HumanMpsOxygenContext
    markers: tuple[ZonationMarker, ...]
    spatial_protein_markers: tuple[SpatialProteinObservation, ...]
    spatial_proteome_measurements_available: bool
    spatial_proteome_may_scale_flux: bool
    quantitative_effect_sizes_available: bool
    oxygen_partial_pressure_available: bool
    dynamic_flux_scaling_enabled: bool
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


_MARKERS: tuple[ZonationMarker, ...] = (
    ZonationMarker("PCK1", "periportal", "transcript", ("human_liver_spatial_atlas_2026",)),
    ZonationMarker("ALDOB", "periportal", "transcript", ("human_liver_spatial_atlas_2026",)),
    ZonationMarker("HAL", "periportal", "transcript_and_protein", ("human_liver_spatial_atlas_2026", "human_liver_cell_atlas_2019")),
    ZonationMarker("ASS1", "periportal", "transcript", ("human_liver_spatial_atlas_2026",)),
    ZonationMarker("ALB", "periportal", "transcript_and_protein", ("human_liver_spatial_atlas_2026", "human_liver_cell_atlas_2019")),
    ZonationMarker("GLS2", "periportal", "transcript", ("human_liver_spatial_atlas_2026",)),
    ZonationMarker("LDHB", "periportal", "transcript", ("human_liver_spatial_atlas_2026",)),
    ZonationMarker("SUCLG2", "periportal", "protein", ("weiss2026_spatial_proteome",)),
    ZonationMarker("HSD17B13", "midlobular", "transcript", ("human_liver_spatial_atlas_2026",)),
    ZonationMarker("C6", "midlobular", "transcript", ("human_liver_spatial_atlas_2026",)),
    ZonationMarker("KLKB1", "midlobular", "transcript", ("human_liver_spatial_atlas_2026",)),
    ZonationMarker("LIPC", "midlobular", "transcript", ("human_liver_spatial_atlas_2026",)),
    ZonationMarker("HGD", "midlobular", "transcript", ("human_liver_spatial_atlas_2026",)),
    ZonationMarker("SDC1", "midlobular", "transcript_and_protein", ("human_liver_spatial_atlas_2026",)),
    ZonationMarker("CYP2E1", "pericentral", "transcript_and_protein", ("human_liver_spatial_atlas_2026", "human_liver_cell_atlas_2019")),
    ZonationMarker("CYP27A1", "pericentral", "transcript", ("human_liver_spatial_atlas_2026",)),
    ZonationMarker("FASN", "pericentral", "transcript", ("human_liver_spatial_atlas_2026",)),
    ZonationMarker("MLXIPL", "pericentral", "transcript", ("human_liver_spatial_atlas_2026",)),
    ZonationMarker("PCK2", "pericentral", "transcript_and_protein", ("human_liver_spatial_atlas_2026",)),
    ZonationMarker("SLC2A2", "pericentral", "transcript_and_protein", ("human_liver_spatial_atlas_2026",)),
    ZonationMarker("GLUL", "pericentral", "transcript", ("human_liver_spatial_atlas_2026", "human_liver_cell_atlas_2019")),
    ZonationMarker("ADH4", "pericentral", "transcript", ("human_liver_spatial_atlas_2026",)),
    ZonationMarker("HNF4A", "pericentral", "transcript", ("human_liver_spatial_atlas_2026",), "Human pattern; do not substitute the mouse periportal pattern."),
    ZonationMarker("ACSL5", "pericentral", "protein", ("weiss2026_spatial_proteome",)),
)


_ZONE_CONTEXTS: dict[HepaticZone, ZoneContext] = {
    "periportal": ZoneContext(
        "periportal", "Zone 1 / periportal", "portal_tract_facing", "relatively_higher",
        tuple(item.gene for item in _MARKERS if item.enriched_zone == "periportal"),
        ("portal-biased gluconeogenic program", "oxidative phosphorylation and ribosomal enrichment", "glutamine breakdown and nitrogen handling"),
        ("periportal Notch ligand/receptor context",),
        ("human_liver_spatial_atlas_2026", "weiss2026_spatial_proteome"),
    ),
    "midlobular": ZoneContext(
        "midlobular", "Zone 2 / midlobular", "intermediate_porto_central", "intermediate",
        tuple(item.gene for item in _MARKERS if item.enriched_zone == "midlobular"),
        ("human-specific midlobular identity program",),
        ("transition between portal and central niche programs",),
        ("human_liver_spatial_atlas_2026",),
    ),
    "pericentral": ZoneContext(
        "pericentral", "Zone 3 / pericentral", "central_vein_facing", "relatively_lower",
        tuple(item.gene for item in _MARKERS if item.enriched_zone == "pericentral"),
        ("xenobiotic metabolism", "bile-acid and lipid biosynthesis", "fatty-acid and peroxisomal programs", "glutamine synthesis"),
        ("pericentral WNT2-RSPO3-LGR5 context",),
        ("human_liver_spatial_atlas_2026", "weiss2026_spatial_proteome"),
    ),
}


def build_human_hepatocyte_zonation(zone: HepaticZone) -> HumanHepatocyteZonationState:
    if zone not in _ZONE_CONTEXTS:
        raise ValueError(f"unsupported human hepatic zone: {zone}")
    context = _ZONE_CONTEXTS[zone]
    oxygen_context = HumanMpsOxygenContext(
        model_system="human_liver_acinus_microphysiology_system",
        controlled_oxygen_low_percent=3.0,
        controlled_oxygen_high_percent=13.0,
        zone1_supported_functions=("oxidative_phosphorylation", "albumin_secretion", "urea_secretion"),
        zone3_supported_functions=("glycolysis", "alpha1_antitrypsin_secretion", "CYP2E1_expression", "acetaminophen_toxicity"),
        is_human_in_situ_measurement=False,
        may_initialize_sinusoid_pO2=False,
        source_ids=("human_liver_mps_oxygen_zonation_2017",),
        limitations=(
            "The 3-13% values are controlled MPS oxygen settings, not direct human sinusoidal measurements.",
            "Flow, device material, cell composition and culture adaptation differ from an intact liver acinus.",
            "The experiment supports functional direction and an assay design target, not a zone-specific reaction-rate multiplier.",
        ),
    )
    state = HumanHepatocyteZonationState(
        species="Homo sapiens",
        selected_zone=zone,
        status="source_backed_reference_context_not_donor_observation",
        coordinate_status="categorical_zone_not_measured_cell_coordinate",
        zone=context,
        experimental_oxygen_context=oxygen_context,
        markers=tuple(item for item in _MARKERS if item.enriched_zone == zone),
        spatial_protein_markers=spatial_protein_observations(zone),
        spatial_proteome_measurements_available=True,
        spatial_proteome_may_scale_flux=False,
        quantitative_effect_sizes_available=False,
        oxygen_partial_pressure_available=False,
        dynamic_flux_scaling_enabled=False,
        source_ids=tuple(dict.fromkeys(
            [source for item in _MARKERS for source in item.source_ids]
            + list(oxygen_context.source_ids)
            + ["weiss2026_spatial_proteome"]
        )),
        limitations=(
            "Marker direction is human-atlas evidence; no donor-specific expression value is inferred.",
            "Relative oxygen context is directional only; no human zonal pO2 value is assigned.",
            "Controlled human-MPS oxygen settings are retained separately and cannot initialize sinusoidal oxygen.",
            "Normalized spatial-proteome gradients identify protein zonation but cannot scale reaction or transport rates.",
            "The source analysis does not define a separate midlobular protein-maximum class.",
            "Zonation does not scale reaction rates until matched human quantitative effects are loaded.",
        ),
    )
    validate_human_hepatocyte_zonation(state)
    return state


def validate_human_hepatocyte_zonation(state: HumanHepatocyteZonationState) -> None:
    if state.species != "Homo sapiens":
        raise ValueError("human zonation state cannot silently use another species")
    if state.dynamic_flux_scaling_enabled or state.quantitative_effect_sizes_available:
        raise ValueError("zonation effect sizes are unavailable and cannot drive flux")
    if not state.spatial_proteome_measurements_available:
        raise ValueError("published human spatial-proteome measurements are missing")
    if state.spatial_proteome_may_scale_flux:
        raise ValueError("normalized spatial-proteome gradients cannot drive flux")
    if state.oxygen_partial_pressure_available:
        raise ValueError("human zonal oxygen partial pressure is not available")
    oxygen = state.experimental_oxygen_context
    if (
        oxygen.controlled_oxygen_low_percent != 3.0
        or oxygen.controlled_oxygen_high_percent != 13.0
        or oxygen.is_human_in_situ_measurement
        or oxygen.may_initialize_sinusoid_pO2
    ):
        raise ValueError("human-MPS oxygen context changed or was promoted to in-situ pO2")
    if not oxygen.source_ids or not set(oxygen.source_ids) <= set(ZONATION_SOURCES):
        raise ValueError("human-MPS oxygen context lacks registered provenance")
    if not state.markers:
        raise ValueError("selected zone has no source-backed markers")
    source_ids = set(ZONATION_SOURCES)
    for marker in state.markers:
        if marker.enriched_zone != state.selected_zone:
            raise ValueError(f"marker {marker.gene} conflicts with selected zone")
        if not marker.source_ids or not set(marker.source_ids) <= source_ids:
            raise ValueError(f"marker {marker.gene} lacks registered human provenance")
    expected_spatial_count = {
        "periportal": 102,
        "midlobular": 0,
        "pericentral": 69,
    }[state.selected_zone]
    if len(state.spatial_protein_markers) != expected_spatial_count:
        raise ValueError("published strong protein-zonation count changed")
    if any(
        marker.enriched_region != state.selected_zone
        or not marker.strong_zonated
        or marker.source_id != "weiss2026_spatial_proteome"
        for marker in state.spatial_protein_markers
    ):
        raise ValueError("spatial protein marker conflicts with selected zone")


def human_hepatocyte_zonation_snapshot(zone: HepaticZone) -> dict[str, object]:
    return build_human_hepatocyte_zonation(zone).to_dict()
