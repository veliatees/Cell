"""Human hepatocyte BSEP/MRP2 abundance and denominator bridge.

Only BSEP has a same-cohort total-protein denominator bridge. MRP2 remains in
its measured human-liver membrane-fraction denominator. Neither measurement
identifies canalicular surface copies, active copies, density, or flux.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from math import isclose, isfinite
from pathlib import Path

from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain
from cell_engine.quantitative.geometry import AVOGADRO


DATE_VERIFIED = "2026-07-14"
VERSION = "phh_transporter_inventory_v1"
SCHEMA_VERSION = "cell.phh-transporter-inventory.v1"
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "phh_baseline"
    / "curated"
    / "human_hepatocyte_transporter_inventory.v1.json"
)


PHH_TRANSPORTER_INVENTORY_SOURCES: dict[str, SourceReference] = {
    "human_hepatocyte_proteome_2016": SourceReference(
        id="human_hepatocyte_proteome_2016",
        title=(
            "In-depth quantitative analysis and comparison of the human hepatocyte "
            "and hepatoma cell line HepG2 proteomes"
        ),
        url="https://doi.org/10.1016/j.jprot.2016.01.016",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Same seven-donor PHH cohort supplies BSEP abundance and total protein per cell.",
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
        notes="Targeted LC-MS/MS of liver membrane fractions from 51 human donors.",
    ),
}


@dataclass(frozen=True)
class TransporterSourceArtifact:
    source_id: str
    title: str
    url: str
    source_role: str


@dataclass(frozen=True)
class TransporterAbundance:
    value: float
    sd: float | None
    unit: str
    biological_system: str
    denominator: str
    source_id: str


@dataclass(frozen=True)
class ExactUnitEquivalent:
    value: float
    sd: float | None
    unit: str


@dataclass(frozen=True)
class MatchedDenominatorBridge:
    total_protein_pg_per_cell: float
    total_protein_source_id: str
    avogadro_per_mol: float
    formula: str
    derived_total_copies_per_cell: float
    display_precision_total_copies_per_cell: int
    evidence_role: str


@dataclass(frozen=True)
class TransporterInventoryRecord:
    id: str
    gene: str
    protein: str
    physiological_location: str
    abundance: TransporterAbundance
    exact_unit_equivalent: ExactUnitEquivalent | None
    matched_denominator_bridge: MatchedDenominatorBridge | None
    total_copies_per_hepatocyte: float | None
    canalicular_surface_copies_per_cell: float | None
    transport_active_copies_per_cell: float | None
    surface_density_copies_per_um2: float | None


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
    bsep_total_copy_bridge_ready: bool
    bsep_surface_copy_bridge_ready: bool
    bsep_active_copy_bridge_ready: bool
    mrp2_total_copy_bridge_ready: bool
    mrp2_surface_copy_bridge_ready: bool
    surface_density_ready: bool
    flux_coupling_ready: bool
    individual_protein_rendering_permitted: bool
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


def copies_from_pmol_per_mg_and_pg_per_cell(
    abundance_pmol_per_mg: float,
    total_protein_pg_per_cell: float,
) -> float:
    """Apply the exact mass/unit bridge without inventing a surface fraction."""

    if not all(
        isfinite(value) and value > 0.0
        for value in (abundance_pmol_per_mg, total_protein_pg_per_cell)
    ):
        raise ValueError("abundance and total protein mass must be finite and positive")
    return (
        abundance_pmol_per_mg
        * 1e-12
        * total_protein_pg_per_cell
        * 1e-9
        * AVOGADRO
    )


def _optional_float(value: object) -> float | None:
    return None if value is None else float(value)


def _parse_abundance(raw: object) -> TransporterAbundance:
    if not isinstance(raw, dict):
        raise ValueError("transporter abundance is malformed")
    return TransporterAbundance(
        value=float(raw["value"]),
        sd=_optional_float(raw["sd"]),
        unit=str(raw["unit"]),
        biological_system=str(raw["biological_system"]),
        denominator=str(raw["denominator"]),
        source_id=str(raw["source_id"]),
    )


def _parse_unit_equivalent(raw: object) -> ExactUnitEquivalent | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("exact unit equivalent is malformed")
    return ExactUnitEquivalent(
        value=float(raw["value"]),
        sd=_optional_float(raw["sd"]),
        unit=str(raw["unit"]),
    )


def _parse_bridge(raw: object) -> MatchedDenominatorBridge | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("matched denominator bridge is malformed")
    return MatchedDenominatorBridge(
        total_protein_pg_per_cell=float(raw["total_protein_pg_per_cell"]),
        total_protein_source_id=str(raw["total_protein_source_id"]),
        avogadro_per_mol=float(raw["avogadro_per_mol"]),
        formula=str(raw["formula"]),
        derived_total_copies_per_cell=float(raw["derived_total_copies_per_cell"]),
        display_precision_total_copies_per_cell=int(
            raw["display_precision_total_copies_per_cell"]
        ),
        evidence_role=str(raw["evidence_role"]),
    )


def build_phh_transporter_inventory(
    data_path: Path = DATA_PATH,
) -> PhhTransporterInventoryState:
    payload = _load_json(data_path)
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported PHH transporter-inventory schema")
    artifacts_raw = payload["source_artifacts"]
    transporters_raw = payload["transporters"]
    required_raw = payload["required_measurements"]
    gates = payload["gates"]
    if not all(isinstance(item, list) for item in (artifacts_raw, transporters_raw, required_raw)) or not isinstance(gates, dict):
        raise ValueError("PHH transporter-inventory payload is malformed")

    transporters: list[TransporterInventoryRecord] = []
    for item in transporters_raw:
        if not isinstance(item, dict):
            raise ValueError("transporter inventory record is malformed")
        bridge = _parse_bridge(item.get("matched_denominator_bridge"))
        transporters.append(
            TransporterInventoryRecord(
                id=str(item["id"]),
                gene=str(item["gene"]),
                protein=str(item["protein"]),
                physiological_location=str(item["physiological_location"]),
                abundance=_parse_abundance(item["abundance"]),
                exact_unit_equivalent=_parse_unit_equivalent(item.get("exact_unit_equivalent")),
                matched_denominator_bridge=bridge,
                total_copies_per_hepatocyte=(
                    bridge.derived_total_copies_per_cell
                    if bridge is not None
                    else _optional_float(item.get("total_copies_per_hepatocyte"))
                ),
                canalicular_surface_copies_per_cell=_optional_float(
                    item.get("canalicular_surface_copies_per_cell")
                ),
                transport_active_copies_per_cell=_optional_float(
                    item.get("transport_active_copies_per_cell")
                ),
                surface_density_copies_per_um2=_optional_float(
                    item.get("surface_density_copies_per_um2")
                ),
            )
        )

    state = PhhTransporterInventoryState(
        version=VERSION,
        status=str(payload["status"]),
        date_verified=str(payload["date_verified"]),
        source_artifacts=tuple(
            TransporterSourceArtifact(
                source_id=str(item["source_id"]),
                title=str(item["title"]),
                url=str(item["url"]),
                source_role=str(item["source_role"]),
            )
            for item in artifacts_raw
            if isinstance(item, dict)
        ),
        transporters=tuple(transporters),
        required_measurements=tuple(
            TransporterRequiredMeasurement(
                id=str(item["id"]),
                requirements=tuple(str(value) for value in item["requirements"]),
                purpose=str(item["purpose"]),
            )
            for item in required_raw
            if isinstance(item, dict)
        ),
        bsep_total_copy_bridge_ready=bool(gates["bsep_total_copy_bridge_ready"]),
        bsep_surface_copy_bridge_ready=bool(gates["bsep_surface_copy_bridge_ready"]),
        bsep_active_copy_bridge_ready=bool(gates["bsep_active_copy_bridge_ready"]),
        mrp2_total_copy_bridge_ready=bool(gates["mrp2_total_copy_bridge_ready"]),
        mrp2_surface_copy_bridge_ready=bool(gates["mrp2_surface_copy_bridge_ready"]),
        surface_density_ready=bool(gates["surface_density_ready"]),
        flux_coupling_ready=bool(gates["flux_coupling_ready"]),
        individual_protein_rendering_permitted=bool(
            gates["individual_protein_rendering_permitted"]
        ),
        automatic_state_coupling=bool(gates["automatic_state_coupling"]),
        predictive_ready=bool(gates["predictive_ready"]),
        source_ids=tuple(str(item) for item in payload["source_ids"]),
        limitations=tuple(str(item) for item in payload["limitations"]),
    )
    validate_phh_transporter_inventory(state)
    return state


def validate_phh_transporter_inventory(state: PhhTransporterInventoryState) -> None:
    if state.version != VERSION or state.date_verified != DATE_VERIFIED:
        raise ValueError("PHH transporter-inventory version or verification date changed")
    by_id = {item.id: item for item in state.transporters}
    if set(by_id) != {"ABCB11_BSEP", "ABCC2_MRP2"}:
        raise ValueError("PHH transporter inventory changed")
    bsep = by_id["ABCB11_BSEP"]
    mrp2 = by_id["ABCC2_MRP2"]
    bridge = bsep.matched_denominator_bridge
    if (
        bsep.abundance.value != 1.4
        or bsep.abundance.sd is not None
        or bsep.abundance.unit != "pmol_per_mg_total_protein"
        or bsep.abundance.denominator != "total_cellular_protein"
        or bridge is None
        or bridge.total_protein_pg_per_cell != 600.0
        or bridge.avogadro_per_mol != AVOGADRO
        or bridge.display_precision_total_copies_per_cell != 510_000
    ):
        raise ValueError("BSEP same-cohort abundance bridge changed")
    expected_bsep_copies = copies_from_pmol_per_mg_and_pg_per_cell(1.4, 600.0)
    if not isclose(
        bridge.derived_total_copies_per_cell,
        expected_bsep_copies,
        rel_tol=0.0,
        abs_tol=1e-9,
    ) or not isclose(
        bsep.total_copies_per_hepatocyte or 0.0,
        expected_bsep_copies,
        rel_tol=0.0,
        abs_tol=1e-9,
    ):
        raise ValueError("BSEP copy derivation changed")
    equivalent = mrp2.exact_unit_equivalent
    if (
        mrp2.abundance.value != 1.54
        or mrp2.abundance.sd != 0.64
        or mrp2.abundance.unit != "fmol_per_ug_liver_membrane_protein"
        or mrp2.abundance.denominator != "isolated_liver_membrane_fraction_protein"
        or equivalent is None
        or equivalent.value != 1.54
        or equivalent.sd != 0.64
        or equivalent.unit != "pmol_per_mg_liver_membrane_protein"
        or mrp2.matched_denominator_bridge is not None
        or mrp2.total_copies_per_hepatocyte is not None
    ):
        raise ValueError("MRP2 tissue-membrane denominator was changed or bridged")
    for item in state.transporters:
        if any(
            value is not None
            for value in (
                item.canalicular_surface_copies_per_cell,
                item.transport_active_copies_per_cell,
                item.surface_density_copies_per_um2,
            )
        ):
            raise ValueError("unmeasured transporter surface or active inventory was populated")
    if {item.id for item in state.required_measurements} != {
        "canalicular_surface_localized_transporter_copies",
        "active_transporter_fraction",
        "canalicular_area",
    }:
        raise ValueError("transporter required-measurement set is incomplete")
    if set(state.source_ids) != {
        "human_hepatocyte_proteome_2016",
        "human_mrp2_abundance_2012",
    } or not set(state.source_ids) <= set(PHH_TRANSPORTER_INVENTORY_SOURCES):
        raise ValueError("PHH transporter source registry changed")
    if (
        not state.bsep_total_copy_bridge_ready
        or state.bsep_surface_copy_bridge_ready
        or state.bsep_active_copy_bridge_ready
        or state.mrp2_total_copy_bridge_ready
        or state.mrp2_surface_copy_bridge_ready
        or state.surface_density_ready
        or state.flux_coupling_ready
        or state.individual_protein_rendering_permitted
        or state.automatic_state_coupling
        or state.predictive_ready
    ):
        raise ValueError("PHH transporter readiness gates exceeded the evidence")
    if len(state.limitations) < 6:
        raise ValueError("PHH transporter limitations are incomplete")


def phh_transporter_inventory_snapshot() -> dict[str, object]:
    state = build_phh_transporter_inventory()
    by_id = {item.id: item for item in state.transporters}
    bsep = by_id["ABCB11_BSEP"]
    mrp2 = by_id["ABCC2_MRP2"]
    payload = state.to_dict()
    payload["summary"] = {
        "transporter_count": len(state.transporters),
        "same_cohort_total_copy_bridge_count": sum(
            item.matched_denominator_bridge is not None for item in state.transporters
        ),
        "bsep_total_copies_per_cell": bsep.total_copies_per_hepatocyte,
        "bsep_display_precision_copies_per_cell": (
            bsep.matched_denominator_bridge.display_precision_total_copies_per_cell
            if bsep.matched_denominator_bridge is not None
            else None
        ),
        "mrp2_mean_fmol_per_ug_liver_membrane_protein": mrp2.abundance.value,
        "mrp2_sd_fmol_per_ug_liver_membrane_protein": mrp2.abundance.sd,
        "surface_localized_copy_count_record_count": 0,
        "active_copy_count_record_count": 0,
        "surface_density_record_count": 0,
        "flux_parameter_count": 0,
    }
    return payload
