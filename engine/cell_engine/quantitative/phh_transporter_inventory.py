"""Denominator-audited BSEP and MRP2 abundance inventory.

Seven-donor total abundance comes directly from the PHH proteome atlas and is
reported per nucleus. Surface localization, active fraction, density and flux
remain explicitly absent. An independent MRP2 membrane-fraction observation is
retained in its original denominator and is never fused with the PHH cohort.
"""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass
from math import isclose, isfinite
from pathlib import Path

from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain
from cell_engine.quantitative.phh_proteome_atlas import (
    canonical_gene_reference,
    detected_donor_copy_summary,
)


DATE_VERIFIED = "2026-07-16"
VERSION = "phh_transporter_inventory_v2"
SCHEMA_VERSION = "cell.phh-transporter-inventory.v2"
AVOGADRO = 6.02214076e23
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "phh_baseline"
    / "curated"
    / "human_hepatocyte_transporter_inventory.v2.json"
)


PHH_TRANSPORTER_INVENTORY_SOURCES: dict[str, SourceReference] = {
    "human_hepatocyte_proteome_2016": SourceReference(
        id="human_hepatocyte_proteome_2016",
        title=(
            "In-depth quantitative analysis and comparison of the human "
            "hepatocyte and hepatoma cell line HepG2 proteomes"
        ),
        url="https://doi.org/10.1016/j.jprot.2016.01.016",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Seven-donor protein-group concentrations and copies per nucleus.",
    ),
    "human_mrp2_abundance_2012": SourceReference(
        id="human_mrp2_abundance_2012",
        title=(
            "Interindividual variability in hepatic expression of the multidrug "
            "resistance-associated protein 2 (MRP2/ABCC2)"
        ),
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC3336801/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Independent human-liver membrane-fraction abundance; denominator "
            "must remain separate from total PHH protein per nucleus."
        ),
    ),
}


@dataclass(frozen=True)
class TransporterSourceArtifact:
    source_id: str
    title: str
    url: str
    source_role: str


@dataclass(frozen=True)
class DonorTotalAbundance:
    donor_id: str
    concentration_pmol_per_mg_total_protein: float
    copies_per_nucleus: float


@dataclass(frozen=True)
class DonorAbundanceSummary:
    detected_donor_count: int
    mean_copies_per_nucleus: float
    median_copies_per_nucleus: float
    minimum_copies_per_nucleus: float
    maximum_copies_per_nucleus: float
    mean_concentration_pmol_per_mg_total_protein: float
    median_concentration_pmol_per_mg_total_protein: float
    minimum_concentration_pmol_per_mg_total_protein: float
    maximum_concentration_pmol_per_mg_total_protein: float
    aggregation: str = "positive_source_donor_values_no_imputation"
    copy_number_denominator: str = "per_nucleus"


@dataclass(frozen=True)
class RoundedHeadlineArithmeticCrossCheck:
    abundance_pmol_per_mg_total_protein: float
    total_protein_pg_per_reference_nucleus: float
    avogadro_per_mol: float
    formula: str
    derived_copies_per_reference_nucleus: float
    display_precision_copies_per_reference_nucleus: int
    evidence_role: str


@dataclass(frozen=True)
class IndependentMembraneFractionAbundance:
    value: float
    sd: float
    unit: str
    biological_system: str
    denominator: str
    source_id: str


@dataclass(frozen=True)
class TransporterInventoryRecord:
    id: str
    gene: str
    protein: str
    uniprot_accession: str
    physiological_location: str
    direct_total_abundance: tuple[DonorTotalAbundance, ...]
    direct_total_summary: DonorAbundanceSummary
    rounded_headline_arithmetic_cross_check: RoundedHeadlineArithmeticCrossCheck | None
    independent_membrane_fraction_abundance: IndependentMembraneFractionAbundance | None
    canalicular_surface_copies_per_hepatocyte: None = None
    transport_active_copies_per_hepatocyte: None = None
    surface_density_copies_per_um2: None = None


@dataclass(frozen=True)
class TransporterRequiredMeasurement:
    id: str
    requirements: tuple[str, ...]
    purpose: str


@dataclass(frozen=True)
class PhhTransporterInventoryState:
    version: str
    status: str
    date_verified: str
    source_artifacts: tuple[TransporterSourceArtifact, ...]
    transporters: tuple[TransporterInventoryRecord, ...]
    required_measurements: tuple[TransporterRequiredMeasurement, ...]
    bsep_total_per_nucleus_observation_ready: bool
    mrp2_total_per_nucleus_observation_ready: bool
    bsep_surface_copy_observation_ready: bool
    mrp2_surface_copy_observation_ready: bool
    active_copy_observation_ready: bool
    surface_density_ready: bool
    flux_coupling_ready: bool
    individual_protein_rendering_permitted: bool
    automatic_state_coupling: bool
    predictive_ready: bool
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def copies_from_pmol_per_mg_and_pg_per_reference_nucleus(
    abundance_pmol_per_mg: float,
    total_protein_pg_per_reference_nucleus: float,
) -> float:
    """Apply the exact unit bridge without relabeling the denominator as a cell."""

    if not all(
        isfinite(value) and value > 0.0
        for value in (
            abundance_pmol_per_mg,
            total_protein_pg_per_reference_nucleus,
        )
    ):
        raise ValueError("abundance and total protein mass must be finite and positive")
    return (
        abundance_pmol_per_mg
        * 1e-12
        * total_protein_pg_per_reference_nucleus
        * 1e-9
        * AVOGADRO
    )


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain one JSON object")
    return payload


def _direct_abundance(gene: str) -> tuple[tuple[DonorTotalAbundance, ...], DonorAbundanceSummary]:
    record = canonical_gene_reference(gene)
    observations: list[DonorTotalAbundance] = []
    for donor_id, raw in record["donor_values"].items():
        concentration = raw["concentration_pmol_per_mg_total_protein"]
        copies = raw["copies_per_nucleus"]
        if concentration is None or copies is None:
            continue
        observations.append(
            DonorTotalAbundance(
                donor_id=str(donor_id),
                concentration_pmol_per_mg_total_protein=float(concentration),
                copies_per_nucleus=float(copies),
            )
        )
    copy_summary = detected_donor_copy_summary(record)
    concentrations = [item.concentration_pmol_per_mg_total_protein for item in observations]
    return tuple(observations), DonorAbundanceSummary(
        detected_donor_count=int(copy_summary["detected_donor_count"]),
        mean_copies_per_nucleus=float(copy_summary["mean_copies_per_nucleus"]),
        median_copies_per_nucleus=float(copy_summary["median_copies_per_nucleus"]),
        minimum_copies_per_nucleus=float(copy_summary["minimum_copies_per_nucleus"]),
        maximum_copies_per_nucleus=float(copy_summary["maximum_copies_per_nucleus"]),
        mean_concentration_pmol_per_mg_total_protein=statistics.fmean(concentrations),
        median_concentration_pmol_per_mg_total_protein=statistics.median(concentrations),
        minimum_concentration_pmol_per_mg_total_protein=min(concentrations),
        maximum_concentration_pmol_per_mg_total_protein=max(concentrations),
    )


def _cross_check(raw: object) -> RoundedHeadlineArithmeticCrossCheck | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("transporter arithmetic cross-check is malformed")
    return RoundedHeadlineArithmeticCrossCheck(
        abundance_pmol_per_mg_total_protein=float(
            raw["abundance_pmol_per_mg_total_protein"]
        ),
        total_protein_pg_per_reference_nucleus=float(
            raw["total_protein_pg_per_reference_nucleus"]
        ),
        avogadro_per_mol=float(raw["avogadro_per_mol"]),
        formula=str(raw["formula"]),
        derived_copies_per_reference_nucleus=float(
            raw["derived_copies_per_reference_nucleus"]
        ),
        display_precision_copies_per_reference_nucleus=int(
            raw["display_precision_copies_per_reference_nucleus"]
        ),
        evidence_role=str(raw["evidence_role"]),
    )


def _membrane_fraction(raw: object) -> IndependentMembraneFractionAbundance | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("independent membrane-fraction abundance is malformed")
    return IndependentMembraneFractionAbundance(
        value=float(raw["value"]),
        sd=float(raw["sd"]),
        unit=str(raw["unit"]),
        biological_system=str(raw["biological_system"]),
        denominator=str(raw["denominator"]),
        source_id=str(raw["source_id"]),
    )


def build_phh_transporter_inventory(
    data_path: Path = DATA_PATH,
) -> PhhTransporterInventoryState:
    payload = _load_json(data_path)
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported PHH transporter-inventory schema")
    raw_artifacts = payload.get("source_artifacts")
    raw_transporters = payload.get("transporters")
    raw_required = payload.get("required_measurements")
    gates = payload.get("gates")
    if not all(isinstance(value, list) for value in (raw_artifacts, raw_transporters, raw_required)) or not isinstance(gates, dict):
        raise ValueError("PHH transporter-inventory payload is malformed")

    transporters: list[TransporterInventoryRecord] = []
    for raw in raw_transporters:
        if not isinstance(raw, dict):
            raise ValueError("transporter record is malformed")
        observations, summary = _direct_abundance(str(raw["gene"]))
        transporters.append(
            TransporterInventoryRecord(
                id=str(raw["id"]),
                gene=str(raw["gene"]),
                protein=str(raw["protein"]),
                uniprot_accession=str(raw["uniprot_accession"]),
                physiological_location=str(raw["physiological_location"]),
                direct_total_abundance=observations,
                direct_total_summary=summary,
                rounded_headline_arithmetic_cross_check=_cross_check(
                    raw.get("rounded_headline_arithmetic_cross_check")
                ),
                independent_membrane_fraction_abundance=_membrane_fraction(
                    raw.get("independent_membrane_fraction_abundance")
                ),
            )
        )

    state = PhhTransporterInventoryState(
        version=str(payload["version"]),
        status=str(payload["status"]),
        date_verified=str(payload["date_verified"]),
        source_artifacts=tuple(
            TransporterSourceArtifact(
                source_id=str(raw["source_id"]),
                title=str(raw["title"]),
                url=str(raw["url"]),
                source_role=str(raw["source_role"]),
            )
            for raw in raw_artifacts
            if isinstance(raw, dict)
        ),
        transporters=tuple(transporters),
        required_measurements=tuple(
            TransporterRequiredMeasurement(
                id=str(raw["id"]),
                requirements=tuple(str(value) for value in raw["requirements"]),
                purpose=str(raw["purpose"]),
            )
            for raw in raw_required
            if isinstance(raw, dict)
        ),
        bsep_total_per_nucleus_observation_ready=bool(
            gates["bsep_total_per_nucleus_observation_ready"]
        ),
        mrp2_total_per_nucleus_observation_ready=bool(
            gates["mrp2_total_per_nucleus_observation_ready"]
        ),
        bsep_surface_copy_observation_ready=bool(
            gates["bsep_surface_copy_observation_ready"]
        ),
        mrp2_surface_copy_observation_ready=bool(
            gates["mrp2_surface_copy_observation_ready"]
        ),
        active_copy_observation_ready=bool(gates["active_copy_observation_ready"]),
        surface_density_ready=bool(gates["surface_density_ready"]),
        flux_coupling_ready=bool(gates["flux_coupling_ready"]),
        individual_protein_rendering_permitted=bool(
            gates["individual_protein_rendering_permitted"]
        ),
        automatic_state_coupling=bool(gates["automatic_state_coupling"]),
        predictive_ready=bool(gates["predictive_ready"]),
        source_ids=tuple(str(value) for value in payload["source_ids"]),
        limitations=tuple(str(value) for value in payload["limitations"]),
    )
    validate_phh_transporter_inventory(state)
    return state


def validate_phh_transporter_inventory(state: PhhTransporterInventoryState) -> None:
    if state.version != VERSION or state.date_verified != DATE_VERIFIED:
        raise ValueError("PHH transporter inventory version or date changed")
    by_id = {item.id: item for item in state.transporters}
    if set(by_id) != {"ABCB11_BSEP", "ABCC2_MRP2"}:
        raise ValueError("PHH transporter inventory changed")
    bsep = by_id["ABCB11_BSEP"]
    mrp2 = by_id["ABCC2_MRP2"]
    expected_medians = {
        "ABCB11_BSEP": 419_353.48438855633,
        "ABCC2_MRP2": 129_918.86133753612,
    }
    for transporter in state.transporters:
        if (
            len(transporter.direct_total_abundance) != 7
            or transporter.direct_total_summary.detected_donor_count != 7
            or transporter.direct_total_summary.copy_number_denominator != "per_nucleus"
            or not isclose(
                transporter.direct_total_summary.median_copies_per_nucleus,
                expected_medians[transporter.id],
                rel_tol=0.0,
                abs_tol=1e-6,
            )
        ):
            raise ValueError("direct transporter abundance changed")
        if any(
            value is not None
            for value in (
                transporter.canalicular_surface_copies_per_hepatocyte,
                transporter.transport_active_copies_per_hepatocyte,
                transporter.surface_density_copies_per_um2,
            )
        ):
            raise ValueError("unmeasured transporter surface inventory was populated")

    cross_check = bsep.rounded_headline_arithmetic_cross_check
    if cross_check is None:
        raise ValueError("BSEP arithmetic cross-check disappeared")
    expected_cross_check = copies_from_pmol_per_mg_and_pg_per_reference_nucleus(
        1.4, 600.0
    )
    if (
        cross_check.avogadro_per_mol != AVOGADRO
        or cross_check.display_precision_copies_per_reference_nucleus != 510_000
        or not isclose(
            cross_check.derived_copies_per_reference_nucleus,
            expected_cross_check,
            rel_tol=0.0,
            abs_tol=1e-9,
        )
    ):
        raise ValueError("BSEP arithmetic cross-check changed")
    external = mrp2.independent_membrane_fraction_abundance
    if (
        mrp2.rounded_headline_arithmetic_cross_check is not None
        or external is None
        or external.value != 1.54
        or external.sd != 0.64
        or external.denominator != "isolated_liver_membrane_fraction_protein"
    ):
        raise ValueError("MRP2 independent membrane-fraction observation changed")
    if {item.id for item in state.required_measurements} != {
        "canalicular_surface_localized_transporter_copies",
        "active_transporter_fraction",
        "canalicular_area",
    }:
        raise ValueError("transporter required-measurement set is incomplete")
    if set(state.source_ids) != set(PHH_TRANSPORTER_INVENTORY_SOURCES):
        raise ValueError("PHH transporter source registry changed")
    if (
        not state.bsep_total_per_nucleus_observation_ready
        or not state.mrp2_total_per_nucleus_observation_ready
        or state.bsep_surface_copy_observation_ready
        or state.mrp2_surface_copy_observation_ready
        or state.active_copy_observation_ready
        or state.surface_density_ready
        or state.flux_coupling_ready
        or state.individual_protein_rendering_permitted
        or state.automatic_state_coupling
        or state.predictive_ready
    ):
        raise ValueError("PHH transporter readiness gates exceeded the evidence")
    if len(state.limitations) < 7:
        raise ValueError("PHH transporter limitations are incomplete")


def phh_transporter_inventory_snapshot() -> dict[str, object]:
    state = build_phh_transporter_inventory()
    by_id = {item.id: item for item in state.transporters}
    bsep = by_id["ABCB11_BSEP"]
    mrp2 = by_id["ABCC2_MRP2"]
    cross_check = bsep.rounded_headline_arithmetic_cross_check
    external = mrp2.independent_membrane_fraction_abundance
    payload = state.to_dict()
    payload["summary"] = {
        "transporter_count": 2,
        "direct_total_per_nucleus_observation_count": 2,
        "bsep_median_copies_per_nucleus": bsep.direct_total_summary.median_copies_per_nucleus,
        "bsep_minimum_copies_per_nucleus": bsep.direct_total_summary.minimum_copies_per_nucleus,
        "bsep_maximum_copies_per_nucleus": bsep.direct_total_summary.maximum_copies_per_nucleus,
        "mrp2_median_copies_per_nucleus": mrp2.direct_total_summary.median_copies_per_nucleus,
        "mrp2_minimum_copies_per_nucleus": mrp2.direct_total_summary.minimum_copies_per_nucleus,
        "mrp2_maximum_copies_per_nucleus": mrp2.direct_total_summary.maximum_copies_per_nucleus,
        "bsep_rounded_arithmetic_cross_check_copies_per_nucleus": (
            cross_check.derived_copies_per_reference_nucleus if cross_check else None
        ),
        "mrp2_mean_fmol_per_ug_liver_membrane_protein": external.value if external else None,
        "mrp2_sd_fmol_per_ug_liver_membrane_protein": external.sd if external else None,
        "surface_localized_copy_count_record_count": 0,
        "active_copy_count_record_count": 0,
        "surface_density_record_count": 0,
        "flux_parameter_count": 0,
    }
    return payload
