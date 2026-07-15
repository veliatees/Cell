"""Absolute protein-mass reference for an average primary human hepatocyte.

The source reports a static seven-donor proteomic reference. Compartment
percentages are protein-mass fractions only; they are never interpreted as
organelle volumes, membrane areas, or dynamic proteostasis parameters.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from math import isclose, isfinite
from pathlib import Path

from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain


DATE_VERIFIED = "2026-07-14"
VERSION = "phh_proteome_budget_v1"
SCHEMA_VERSION = "cell.phh-proteome-budget.v1"
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "phh_baseline"
    / "curated"
    / "wisniewski2016_hepatocyte_proteome_budget.v1.json"
)


PHH_PROTEOME_BUDGET_SOURCES: dict[str, SourceReference] = {
    "human_hepatocyte_proteome_2016": SourceReference(
        id="human_hepatocyte_proteome_2016",
        title=(
            "In-depth quantitative analysis and comparison of the human hepatocyte "
            "and hepatoma cell line HepG2 proteomes"
        ),
        url="https://doi.org/10.1016/j.jprot.2016.01.016",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Quantitative LC-MS/MS of purified hepatocytes from seven human donors "
            "using Total Protein Approach and Proteomic Ruler."
        ),
    )
}


@dataclass(frozen=True)
class ProteomeSourceArtifact:
    source_id: str
    doi: str
    repository_url: str
    pdf_filename: str
    repository_md5: str
    source_locations: tuple[str, ...]


@dataclass(frozen=True)
class ProteomeCohort:
    species: str
    biological_system: str
    donor_count: int
    assay: str


@dataclass(frozen=True)
class ProteomeAnchor:
    value: float
    uncertainty: float | None
    evidence_role: str


@dataclass(frozen=True)
class ProteomeWholeCellAnchors:
    total_protein_pg_per_cell: ProteomeAnchor
    total_protein_molecules_per_cell: ProteomeAnchor
    estimated_cell_volume_um3: ProteomeAnchor


@dataclass(frozen=True)
class CompartmentProteinMassFraction:
    id: str
    fraction_of_total_cellular_protein: float
    evidence_role: str


@dataclass(frozen=True)
class CompartmentProteinMassBudget:
    id: str
    fraction_of_total_cellular_protein: float
    derived_protein_mass_pg_per_cell: float
    evidence_role: str


@dataclass(frozen=True)
class ProteomeRequiredMeasurement:
    id: str
    requirements: tuple[str, ...]
    purpose: str


@dataclass(frozen=True)
class PhhProteomeBudgetState:
    version: str
    status: str
    date_verified: str
    source_artifact: ProteomeSourceArtifact
    cohort: ProteomeCohort
    whole_cell_anchors: ProteomeWholeCellAnchors
    compartment_protein_mass_fractions: tuple[CompartmentProteinMassFraction, ...]
    derived_compartment_mass_budget: tuple[CompartmentProteinMassBudget, ...]
    required_measurements: tuple[ProteomeRequiredMeasurement, ...]
    whole_cell_protein_reference_ready: bool
    arithmetic_compartment_mass_budget_ready: bool
    donor_specific_initialization_ready: bool
    dynamic_proteostasis_ready: bool
    macromolecular_crowding_ready: bool
    geometry_coupling_ready: bool
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


def _anchor(raw: object) -> ProteomeAnchor:
    if not isinstance(raw, dict):
        raise ValueError("proteome anchor is malformed")
    uncertainty = raw["uncertainty"]
    return ProteomeAnchor(
        value=float(raw["value"]),
        uncertainty=None if uncertainty is None else float(uncertainty),
        evidence_role=str(raw["evidence_role"]),
    )


def derive_compartment_protein_mass_budget(
    total_protein_pg_per_cell: float,
    fractions: tuple[CompartmentProteinMassFraction, ...],
) -> tuple[CompartmentProteinMassBudget, ...]:
    if not isfinite(total_protein_pg_per_cell) or total_protein_pg_per_cell <= 0.0:
        raise ValueError("total protein mass must be finite and positive")
    if any(
        not isfinite(item.fraction_of_total_cellular_protein)
        or not 0.0 <= item.fraction_of_total_cellular_protein <= 1.0
        for item in fractions
    ):
        raise ValueError("protein-mass fractions must be finite and between zero and one")
    return tuple(
        CompartmentProteinMassBudget(
            id=item.id,
            fraction_of_total_cellular_protein=item.fraction_of_total_cellular_protein,
            derived_protein_mass_pg_per_cell=(
                total_protein_pg_per_cell * item.fraction_of_total_cellular_protein
            ),
            evidence_role="arithmetic_from_source_reported_average_and_mass_fraction",
        )
        for item in fractions
    )


def build_phh_proteome_budget(data_path: Path = DATA_PATH) -> PhhProteomeBudgetState:
    payload = _load_json(data_path)
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported PHH proteome-budget schema")
    artifact_raw = payload["source_artifact"]
    cohort_raw = payload["cohort"]
    anchors_raw = payload["whole_cell_anchors"]
    fractions_raw = payload["compartment_protein_mass_fractions"]
    required_raw = payload["required_measurements"]
    gates = payload["gates"]
    if not all(
        isinstance(item, dict)
        for item in (artifact_raw, cohort_raw, anchors_raw, gates)
    ) or not isinstance(fractions_raw, list) or not isinstance(required_raw, list):
        raise ValueError("PHH proteome-budget payload is malformed")

    anchors = ProteomeWholeCellAnchors(
        total_protein_pg_per_cell=_anchor(anchors_raw["total_protein_pg_per_cell"]),
        total_protein_molecules_per_cell=_anchor(
            anchors_raw["total_protein_molecules_per_cell"]
        ),
        estimated_cell_volume_um3=_anchor(anchors_raw["estimated_cell_volume_um3"]),
    )
    fractions = tuple(
        CompartmentProteinMassFraction(
            id=str(item["id"]),
            fraction_of_total_cellular_protein=float(
                item["fraction_of_total_cellular_protein"]
            ),
            evidence_role=str(item["evidence_role"]),
        )
        for item in fractions_raw
        if isinstance(item, dict)
    )
    state = PhhProteomeBudgetState(
        version=VERSION,
        status=str(payload["status"]),
        date_verified=str(payload["date_verified"]),
        source_artifact=ProteomeSourceArtifact(
            source_id=str(artifact_raw["source_id"]),
            doi=str(artifact_raw["doi"]),
            repository_url=str(artifact_raw["repository_url"]),
            pdf_filename=str(artifact_raw["pdf_filename"]),
            repository_md5=str(artifact_raw["repository_md5"]),
            source_locations=tuple(str(item) for item in artifact_raw["source_locations"]),
        ),
        cohort=ProteomeCohort(
            species=str(cohort_raw["species"]),
            biological_system=str(cohort_raw["biological_system"]),
            donor_count=int(cohort_raw["donor_count"]),
            assay=str(cohort_raw["assay"]),
        ),
        whole_cell_anchors=anchors,
        compartment_protein_mass_fractions=fractions,
        derived_compartment_mass_budget=derive_compartment_protein_mass_budget(
            anchors.total_protein_pg_per_cell.value, fractions
        ),
        required_measurements=tuple(
            ProteomeRequiredMeasurement(
                id=str(item["id"]),
                requirements=tuple(str(value) for value in item["requirements"]),
                purpose=str(item["purpose"]),
            )
            for item in required_raw
            if isinstance(item, dict)
        ),
        whole_cell_protein_reference_ready=bool(gates["whole_cell_protein_reference_ready"]),
        arithmetic_compartment_mass_budget_ready=bool(
            gates["arithmetic_compartment_mass_budget_ready"]
        ),
        donor_specific_initialization_ready=bool(gates["donor_specific_initialization_ready"]),
        dynamic_proteostasis_ready=bool(gates["dynamic_proteostasis_ready"]),
        macromolecular_crowding_ready=bool(gates["macromolecular_crowding_ready"]),
        geometry_coupling_ready=bool(gates["geometry_coupling_ready"]),
        automatic_state_coupling=bool(gates["automatic_state_coupling"]),
        predictive_ready=bool(gates["predictive_ready"]),
        source_ids=tuple(str(item) for item in payload["source_ids"]),
        limitations=tuple(str(item) for item in payload["limitations"]),
    )
    validate_phh_proteome_budget(state)
    return state


def validate_phh_proteome_budget(state: PhhProteomeBudgetState) -> None:
    artifact = state.source_artifact
    anchors = state.whole_cell_anchors
    if state.version != VERSION or state.date_verified != DATE_VERIFIED:
        raise ValueError("PHH proteome-budget version or verification date changed")
    if (
        artifact.source_id != "human_hepatocyte_proteome_2016"
        or artifact.doi != "10.1016/j.jprot.2016.01.016"
        or artifact.pdf_filename != "1-s2.0-S1874391916300197-main.pdf"
        or artifact.repository_md5 != "5cd1a046891b8bc4b3819e443da006ec"
    ):
        raise ValueError("PHH proteome source provenance changed")
    if (
        state.cohort.species != "Homo sapiens"
        or state.cohort.donor_count != 7
        or anchors.total_protein_pg_per_cell.value != 600.0
        or anchors.total_protein_molecules_per_cell.value != 8_700_000_000.0
        or anchors.estimated_cell_volume_um3.value != 3_000.0
        or any(
            anchor.uncertainty is not None
            for anchor in (
                anchors.total_protein_pg_per_cell,
                anchors.total_protein_molecules_per_cell,
                anchors.estimated_cell_volume_um3,
            )
        )
    ):
        raise ValueError("PHH whole-cell proteome anchors changed")
    if "assumed_200_g_per_L" not in anchors.estimated_cell_volume_um3.evidence_role:
        raise ValueError("source-derived cell volume was promoted to a direct measurement")
    expected_fractions = {
        "mitochondria": 0.25,
        "endoplasmic_reticulum_and_golgi": 0.12,
        "nucleus": 0.10,
        "integral_plasma_membrane_proteins": 0.012,
    }
    if {item.id: item.fraction_of_total_cellular_protein for item in state.compartment_protein_mass_fractions} != expected_fractions:
        raise ValueError("PHH compartment protein-mass fractions changed")
    expected_masses = {key: 600.0 * value for key, value in expected_fractions.items()}
    if any(
        not isclose(
            item.derived_protein_mass_pg_per_cell,
            expected_masses[item.id],
            rel_tol=0.0,
            abs_tol=1e-12,
        )
        for item in state.derived_compartment_mass_budget
    ):
        raise ValueError("PHH compartment protein-mass arithmetic changed")
    if {item.id for item in state.required_measurements} != {
        "matched_single_cell_total_protein",
        "dynamic_protein_turnover",
        "geometry_resolved_compartment_measurements",
    }:
        raise ValueError("PHH proteome required-measurement set is incomplete")
    if set(state.source_ids) != {"human_hepatocyte_proteome_2016"} or not set(
        state.source_ids
    ) <= set(PHH_PROTEOME_BUDGET_SOURCES):
        raise ValueError("PHH proteome source registry changed")
    if (
        not state.whole_cell_protein_reference_ready
        or not state.arithmetic_compartment_mass_budget_ready
        or state.donor_specific_initialization_ready
        or state.dynamic_proteostasis_ready
        or state.macromolecular_crowding_ready
        or state.geometry_coupling_ready
        or state.automatic_state_coupling
        or state.predictive_ready
    ):
        raise ValueError("PHH proteome readiness gates exceeded the evidence")
    if len(state.limitations) < 6:
        raise ValueError("PHH proteome limitations are incomplete")


def phh_proteome_budget_snapshot() -> dict[str, object]:
    state = build_phh_proteome_budget()
    payload = state.to_dict()
    payload["summary"] = {
        "donor_count": state.cohort.donor_count,
        "total_protein_pg_per_cell": state.whole_cell_anchors.total_protein_pg_per_cell.value,
        "total_protein_molecules_per_cell": state.whole_cell_anchors.total_protein_molecules_per_cell.value,
        "estimated_cell_volume_um3": state.whole_cell_anchors.estimated_cell_volume_um3.value,
        "compartment_fraction_count": len(state.compartment_protein_mass_fractions),
        "mitochondrial_protein_mass_pg_per_cell": next(
            item.derived_protein_mass_pg_per_cell
            for item in state.derived_compartment_mass_budget
            if item.id == "mitochondria"
        ),
        "integral_plasma_membrane_protein_mass_pg_per_cell": next(
            item.derived_protein_mass_pg_per_cell
            for item in state.derived_compartment_mass_budget
            if item.id == "integral_plasma_membrane_proteins"
        ),
        "dynamic_parameter_count": 0,
        "geometry_parameter_count": 0,
    }
    return payload
