"""Donor abundance, localization, kinetics and response evidence for PHH proteins.

Every evidence layer keeps its original biological system and denominator.
Total copies never become surface copies, active molecules or a whole-cell rate.
Assay parameters may only be compared with model output that reproduces the
same protein, substrate, kinetic form, experimental system and units.
"""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Any

from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain
from cell_engine.quantitative.human_liver_open_atlas import surface_protein_observation
from cell_engine.quantitative.phh_glucose_validation import load_healthy_phh_glucose_validation
from cell_engine.quantitative.phh_proteome_atlas import canonical_gene_reference


DATE_VERIFIED = "2026-07-22"
VERSION = "phh_protein_functional_evidence_v2"
SCHEMA_VERSION = "cell.phh-protein-functional-evidence.v2"
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "phh_baseline"
    / "curated"
    / "phh_protein_functional_evidence.v2.json"
)


PHH_PROTEIN_FUNCTIONAL_EVIDENCE_SOURCES: dict[str, SourceReference] = {
    "human_hepatocyte_proteome_2016": SourceReference(
        id="human_hepatocyte_proteome_2016",
        title="In-depth quantitative analysis and comparison of the human hepatocyte and hepatoma cell line HepG2 proteomes",
        url="https://doi.org/10.1016/j.jprot.2016.01.016",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Seven-donor total protein-group abundance per nucleus.",
    ),
    "mallanna2016_phh_surfaceome": SourceReference(
        id="mallanna2016_phh_surfaceome",
        title="Mapping the Cell-Surface N-Glycoproteome of Human Hepatocytes Reveals Markers for Selecting a Homogeneous Population of iPSC-Derived Hepatocytes",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC5032032/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Primary-human-hepatocyte surface identity; no density, domain or orientation.",
    ),
    "human_bsep_taurocholate_2002": SourceReference(
        id="human_bsep_taurocholate_2002",
        title="The human bile salt export pump: characterization of substrate specificity and identification of inhibitors",
        url="https://pubmed.ncbi.nlm.nih.gov/12404239/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Recombinant human BSEP taurocholate Km and Vmax.",
    ),
    "human_bsep_taurocholate_2013": SourceReference(
        id="human_bsep_taurocholate_2013",
        title="Early identification of clinically relevant drug interactions with the human bile salt export pump",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC3858191/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Independent recombinant human BSEP taurocholate Km and Vmax with SD.",
    ),
    "human_mrp2_bilirubin_glucuronides_1999": SourceReference(
        id="human_mrp2_bilirubin_glucuronides_1999",
        title="Transport of monoglucuronosyl and bisglucuronosyl bilirubin by recombinant human and rat multidrug resistance protein 2",
        url="https://pubmed.ncbi.nlm.nih.gov/10421658/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Human MRP2 Km values and measured rates at 0.5 uM substrate; the rates are not Vmax.",
    ),
    "human_ntcp_uptake_2003": SourceReference(
        id="human_ntcp_uptake_2003",
        title="Function of uptake transporters for taurocholate and estradiol 17beta-D-glucuronide in cryopreserved human hepatocytes",
        url="https://doi.org/10.2133/dmpk.18.33",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Whole-hepatocyte taurocholate uptake Km range and cryopreservation variability.",
    ),
    "bi2006_human_schh_taurocholate_transport": SourceReference(
        id="bi2006_human_schh_taurocholate_transport",
        title="Use of cryopreserved human hepatocytes in sandwich culture to measure hepatobiliary transport",
        url="https://pubmed.ncbi.nlm.nih.gov/16782767/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Five-lot sandwich-cultured human-hepatocyte taurocholate apparent "
            "uptake, intrinsic biliary clearance and BEI ranges. These are coupled "
            "system outputs, not individual transporter rates."
        ),
    ),
    "kemas2021_phh_glucose": SourceReference(
        id="kemas2021_phh_glucose",
        title="Primary human hepatocytes in 3D spheroid culture display insulin-sensitive glucose metabolism",
        url="https://doi.org/10.1016/j.abb.2021.108854",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Defined insulin exposure with pAKT and gene-expression response observations.",
    ),
    "noe2002_human_bsep_bile_salts": SourceReference(
        id="noe2002_human_bsep_bile_salts",
        title="Functional expression of the canalicular bile salt export pump of human liver",
        url="https://doi.org/10.1053/gast.2002.36587",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Recombinant human BSEP affinity observations for four bile salts.",
    ),
    "gilibili2017_human_mrp2_probe_substrates": SourceReference(
        id="gilibili2017_human_mrp2_probe_substrates",
        title="Coproporphyrin-I: A Fluorescent, Endogenous Optimal Probe Substrate for ABCC2 (MRP2) Suitable for Vesicle-Based MRP2 Inhibition Assay",
        url="https://pubmed.ncbi.nlm.nih.gov/28325716/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Recombinant human MRP2 E17G and coproporphyrin-I transport curves.",
    ),
    "arbuckle1996_human_glut2_oocyte": SourceReference(
        id="arbuckle1996_human_glut2_oocyte",
        title="Structure-Function Analysis of Liver-Type (GLUT2) and Brain-Type (GLUT3) Glucose Transporters",
        url="https://doi.org/10.1021/bi962210n",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Human GLUT2 2-deoxyglucose affinity measured in Xenopus oocytes.",
    ),
}


@dataclass(frozen=True)
class NumericEvidence:
    kind: str
    value: float | None
    low: float | None
    high: float | None
    sd: float | None
    unit: str


@dataclass(frozen=True)
class VelocityEvidence:
    kind: str
    value: float
    sd: float | None
    unit: str
    substrate_concentration_uM: float | None


@dataclass(frozen=True)
class RelativeActivityContext:
    reference: str
    low: float
    high: float
    unit: str


@dataclass(frozen=True)
class ProteinKineticObservation:
    id: str
    gene: str
    protein_id: str
    interaction_type: str
    substrate: str
    kinetic_model: str
    biological_system: str
    km: NumericEvidence
    hill_coefficient: NumericEvidence | None
    velocity: VelocityEvidence | None
    relative_activity_context: RelativeActivityContext | None
    source_id: str
    source_locator: str
    may_evaluate_assay_curve: bool
    may_scale_whole_cell_flux: bool


@dataclass(frozen=True)
class WholeCellTransportMetricRange:
    id: str
    low: float
    high: float
    unit: str


@dataclass(frozen=True)
class WholeCellTransportValidation:
    id: str
    species: str
    biological_system: str
    culture_format: str
    culture_medium: str
    seeded_cells_per_well: int
    medium_volume_uL_per_well: float
    lot_count: int
    substrate: str
    coupled_components: tuple[str, ...]
    metric_ranges: tuple[WholeCellTransportMetricRange, ...]
    range_semantics: str
    individual_lot_values_loaded: bool
    uncertainty_statistics_loaded: bool
    exact_probe_protocol_loaded: bool
    may_identify_individual_transporter_rate: bool
    may_initialize_healthy_in_vivo_cell: bool
    may_drive_cell_state: bool
    source_id: str
    source_locator: str


@dataclass(frozen=True)
class DonorAbundanceProfile:
    gene: str
    protein_group_id: str
    copy_number_denominator: str
    donor_copies_per_nucleus: dict[str, float]
    detected_donor_count: int
    missing_donor_count: int
    mean_copies_per_nucleus: float
    median_copies_per_nucleus: float
    minimum_copies_per_nucleus: float
    maximum_copies_per_nucleus: float
    sample_sd_copies_per_nucleus: float
    sample_cv: float
    maximum_to_minimum_fold: float
    interpretation: str


@dataclass(frozen=True)
class FunctionalResponseEvidence:
    id: str
    protein_id: str
    response: str
    direction: str
    reported_fold_change: float
    duration_min: float
    ligand_challenge_pM: float
    uncertainty_value: float | None
    may_fit_quantitative_kinetics: bool
    source_id: str
    source_locator: str


@dataclass(frozen=True)
class ProteinFunctionalRecord:
    id: str
    gene: str
    protein_id: str
    uniprot_accession: str
    functional_role: str
    physiological_compartment: str | None
    physiological_domain: str | None
    domain_source_id: str | None
    abundance: DonorAbundanceProfile
    surface_capture_observed: bool
    surface_capture_source_id: str | None
    surface_localized_copies_per_hepatocyte: None
    active_fraction: None
    active_copies_per_hepatocyte: None
    kinetic_observations: tuple[ProteinKineticObservation, ...]
    functional_responses: tuple[FunctionalResponseEvidence, ...]
    receptor_binding_kinetics_ready: bool
    whole_cell_rate_ready: bool


@dataclass(frozen=True)
class ProteinFunctionalEvidenceState:
    version: str
    status: str
    date_verified: str
    policy: str
    proteins: tuple[ProteinFunctionalRecord, ...]
    kinetic_observations: tuple[ProteinKineticObservation, ...]
    whole_cell_transport_validations: tuple[WholeCellTransportValidation, ...]
    functional_responses: tuple[FunctionalResponseEvidence, ...]
    integration_gates: dict[str, bool]
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


@dataclass(frozen=True)
class AssayKineticPrediction:
    prediction_id: str
    model_id: str
    observation_id: str
    protein_id: str
    substrate: str
    biological_system: str
    kinetic_model: str
    km_value: float
    km_unit: str
    velocity_kind: str | None
    velocity_value: float | None
    velocity_unit: str | None
    substrate_concentration_uM: float | None
    hill_coefficient_value: float | None = None
    hill_coefficient_unit: str | None = None


@dataclass(frozen=True)
class AssayComparisonAudit:
    protein_match: bool
    substrate_match: bool
    biological_system_match: bool
    kinetic_model_match: bool
    km_unit_match: bool
    hill_coefficient_contract_match: bool
    velocity_contract_match: bool
    exact_input_match: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class AssayParameterResidual:
    metric: str
    observed_value: float | None
    observed_low: float | None
    observed_high: float | None
    observed_sd: float | None
    predicted_value: float
    raw_residual: float | None
    standardized_residual: float | None
    within_reported_range: bool | None
    unit: str


@dataclass(frozen=True)
class AssayKineticComparison:
    status: str
    observation_id: str
    input_audit: AssayComparisonAudit
    residuals: tuple[AssayParameterResidual, ...]
    fitted_parameter_count: int
    pass_fail_assigned: bool
    may_drive_cell_state: bool

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("PHH protein-functional evidence must be one JSON object")
    return payload


def _optional_float(value: object) -> float | None:
    return None if value is None else float(value)


def _numeric_evidence(raw: object) -> NumericEvidence:
    if not isinstance(raw, dict):
        raise ValueError("numeric evidence is malformed")
    return NumericEvidence(
        kind=str(raw["kind"]),
        value=_optional_float(raw.get("value")),
        low=_optional_float(raw.get("low")),
        high=_optional_float(raw.get("high")),
        sd=_optional_float(raw.get("sd")),
        unit=str(raw["unit"]),
    )


def _velocity_evidence(raw: object) -> VelocityEvidence | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("velocity evidence is malformed")
    return VelocityEvidence(
        kind=str(raw["kind"]),
        value=float(raw["value"]),
        sd=_optional_float(raw.get("sd")),
        unit=str(raw["unit"]),
        substrate_concentration_uM=_optional_float(raw.get("substrate_concentration_uM")),
    )


def _activity_context(raw: object) -> RelativeActivityContext | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("relative activity context is malformed")
    return RelativeActivityContext(
        reference=str(raw["reference"]),
        low=float(raw["low"]),
        high=float(raw["high"]),
        unit=str(raw["unit"]),
    )


def _kinetic_observation(raw: object) -> ProteinKineticObservation:
    if not isinstance(raw, dict):
        raise ValueError("kinetic observation is malformed")
    return ProteinKineticObservation(
        id=str(raw["id"]),
        gene=str(raw["gene"]),
        protein_id=str(raw["protein_id"]),
        interaction_type=str(raw["interaction_type"]),
        substrate=str(raw["substrate"]),
        kinetic_model=str(raw["kinetic_model"]),
        biological_system=str(raw["biological_system"]),
        km=_numeric_evidence(raw["km"]),
        hill_coefficient=(
            None
            if raw.get("hill_coefficient") is None
            else _numeric_evidence(raw["hill_coefficient"])
        ),
        velocity=_velocity_evidence(raw.get("velocity")),
        relative_activity_context=_activity_context(raw.get("relative_activity_context")),
        source_id=str(raw["source_id"]),
        source_locator=str(raw["source_locator"]),
        may_evaluate_assay_curve=bool(raw["may_evaluate_assay_curve"]),
        may_scale_whole_cell_flux=bool(raw["may_scale_whole_cell_flux"]),
    )


def _whole_cell_transport_validation(raw: object) -> WholeCellTransportValidation:
    if not isinstance(raw, dict) or not isinstance(raw.get("metric_ranges"), list):
        raise ValueError("whole-cell transport validation is malformed")
    return WholeCellTransportValidation(
        id=str(raw["id"]),
        species=str(raw["species"]),
        biological_system=str(raw["biological_system"]),
        culture_format=str(raw["culture_format"]),
        culture_medium=str(raw["culture_medium"]),
        seeded_cells_per_well=int(raw["seeded_cells_per_well"]),
        medium_volume_uL_per_well=float(raw["medium_volume_uL_per_well"]),
        lot_count=int(raw["lot_count"]),
        substrate=str(raw["substrate"]),
        coupled_components=tuple(str(item) for item in raw["coupled_components"]),
        metric_ranges=tuple(
            WholeCellTransportMetricRange(
                id=str(item["id"]),
                low=float(item["low"]),
                high=float(item["high"]),
                unit=str(item["unit"]),
            )
            for item in raw["metric_ranges"]
            if isinstance(item, dict)
        ),
        range_semantics=str(raw["range_semantics"]),
        individual_lot_values_loaded=bool(raw["individual_lot_values_loaded"]),
        uncertainty_statistics_loaded=bool(raw["uncertainty_statistics_loaded"]),
        exact_probe_protocol_loaded=bool(raw["exact_probe_protocol_loaded"]),
        may_identify_individual_transporter_rate=bool(
            raw["may_identify_individual_transporter_rate"]
        ),
        may_initialize_healthy_in_vivo_cell=bool(raw["may_initialize_healthy_in_vivo_cell"]),
        may_drive_cell_state=bool(raw["may_drive_cell_state"]),
        source_id=str(raw["source_id"]),
        source_locator=str(raw["source_locator"]),
    )


def _donor_profile(gene: str) -> DonorAbundanceProfile:
    record = canonical_gene_reference(gene)
    donor_values = {
        str(donor_id): float(observation["copies_per_nucleus"])
        for donor_id, observation in record["donor_values"].items()
        if observation["copies_per_nucleus"] is not None
    }
    values = list(donor_values.values())
    mean = statistics.fmean(values)
    sample_sd = statistics.stdev(values) if len(values) > 1 else 0.0
    return DonorAbundanceProfile(
        gene=gene,
        protein_group_id=str(record["group_id"]),
        copy_number_denominator="per_nucleus",
        donor_copies_per_nucleus=donor_values,
        detected_donor_count=len(values),
        missing_donor_count=7 - len(values),
        mean_copies_per_nucleus=mean,
        median_copies_per_nucleus=statistics.median(values),
        minimum_copies_per_nucleus=min(values),
        maximum_copies_per_nucleus=max(values),
        sample_sd_copies_per_nucleus=sample_sd,
        sample_cv=sample_sd / mean,
        maximum_to_minimum_fold=max(values) / min(values),
        interpretation=(
            "descriptive_seven_surgical_resection_donor_abundance_not_healthy_population_activity"
        ),
    )


def _response_evidence(raw_links: list[object]) -> tuple[FunctionalResponseEvidence, ...]:
    validation = load_healthy_phh_glucose_validation()
    responses = {item.id: item for item in validation.insulin_response_observations}
    output: list[FunctionalResponseEvidence] = []
    for raw in raw_links:
        if not isinstance(raw, dict):
            raise ValueError("functional response link is malformed")
        source = responses.get(str(raw["id"]))
        if source is None:
            raise ValueError("functional response link is not present in its source module")
        output.append(
            FunctionalResponseEvidence(
                id=source.id,
                protein_id=str(raw["protein_id"]),
                response=source.response,
                direction=source.direction,
                reported_fold_change=source.reported_fold_change,
                duration_min=source.duration_min,
                ligand_challenge_pM=source.insulin_challenge_pM,
                uncertainty_value=source.uncertainty_value,
                may_fit_quantitative_kinetics=source.may_fit_quantitative_kinetics,
                source_id=str(raw["source_id"]),
                source_locator=source.source_locator,
            )
        )
    return tuple(output)


def build_phh_protein_functional_evidence(
    data_path: Path = DATA_PATH,
) -> ProteinFunctionalEvidenceState:
    payload = _load_json(data_path)
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported PHH protein-functional evidence schema")
    kinetic_raw = payload.get("kinetic_observations")
    proteins_raw = payload.get("proteins")
    response_raw = payload.get("functional_response_links")
    whole_cell_raw = payload.get("whole_cell_transport_validations")
    gates = payload.get("integration_gates")
    if not all(
        isinstance(item, list)
        for item in (kinetic_raw, proteins_raw, response_raw, whole_cell_raw)
    ):
        raise ValueError("PHH protein-functional evidence arrays are malformed")
    if not isinstance(gates, dict):
        raise ValueError("PHH protein-functional integration gates are malformed")

    kinetics = tuple(_kinetic_observation(item) for item in kinetic_raw)
    whole_cell_validations = tuple(
        _whole_cell_transport_validation(item) for item in whole_cell_raw
    )
    kinetics_by_id = {item.id: item for item in kinetics}
    responses = _response_evidence(response_raw)
    responses_by_id = {item.id: item for item in responses}
    proteins: list[ProteinFunctionalRecord] = []
    for raw in proteins_raw:
        if not isinstance(raw, dict):
            raise ValueError("functional protein record is malformed")
        gene = str(raw["gene"])
        surface = surface_protein_observation(gene)
        expected_surface = bool(raw["surface_capture_expected"])
        if (surface is not None) != expected_surface:
            raise ValueError(f"surface-capture expectation changed for {gene}")
        protein_kinetics = tuple(
            kinetics_by_id[str(record_id)] for record_id in raw["kinetic_observation_ids"]
        )
        protein_responses = tuple(
            responses_by_id[str(record_id)] for record_id in raw["functional_response_ids"]
        )
        proteins.append(
            ProteinFunctionalRecord(
                id=str(raw["id"]),
                gene=gene,
                protein_id=str(raw["protein_id"]),
                uniprot_accession=str(raw["uniprot_accession"]),
                functional_role=str(raw["functional_role"]),
                physiological_compartment=(
                    None if raw.get("physiological_compartment") is None else str(raw["physiological_compartment"])
                ),
                physiological_domain=(
                    None if raw.get("physiological_domain") is None else str(raw["physiological_domain"])
                ),
                domain_source_id=(
                    None if raw.get("domain_source_id") is None else str(raw["domain_source_id"])
                ),
                abundance=_donor_profile(gene),
                surface_capture_observed=surface is not None,
                surface_capture_source_id=("mallanna2016_phh_surfaceome" if surface is not None else None),
                surface_localized_copies_per_hepatocyte=None,
                active_fraction=None,
                active_copies_per_hepatocyte=None,
                kinetic_observations=protein_kinetics,
                functional_responses=protein_responses,
                receptor_binding_kinetics_ready=False,
                whole_cell_rate_ready=False,
            )
        )

    state = ProteinFunctionalEvidenceState(
        version=str(payload["version"]),
        status=str(payload["status"]),
        date_verified=str(payload["date_verified"]),
        policy=str(payload["policy"]),
        proteins=tuple(proteins),
        kinetic_observations=kinetics,
        whole_cell_transport_validations=whole_cell_validations,
        functional_responses=responses,
        integration_gates={str(key): bool(value) for key, value in gates.items()},
        source_ids=tuple(str(item["source_id"]) for item in payload["source_artifacts"]),
        limitations=tuple(str(item) for item in payload["limitations"]),
    )
    validate_phh_protein_functional_evidence(state)
    return state


def validate_phh_protein_functional_evidence(state: ProteinFunctionalEvidenceState) -> None:
    if state.version != VERSION or state.date_verified != DATE_VERIFIED:
        raise ValueError("PHH protein-functional evidence version changed")
    if (
        len(state.source_ids) != len(PHH_PROTEIN_FUNCTIONAL_EVIDENCE_SOURCES)
        or len(set(state.source_ids)) != len(state.source_ids)
        or set(state.source_ids) != set(PHH_PROTEIN_FUNCTIONAL_EVIDENCE_SOURCES)
    ):
        raise ValueError("PHH protein-functional source registry changed")
    expected_genes = {"ABCB11", "ABCC2", "SLC10A1", "INSR", "MET", "EGFR", "SLC2A2", "GCK"}
    if len(state.proteins) != 8 or {item.gene for item in state.proteins} != expected_genes:
        raise ValueError("PHH functional protein panel changed")
    if any(item.abundance.detected_donor_count != 7 for item in state.proteins):
        raise ValueError("functional protein donor abundance is incomplete")
    if any(
        item.surface_localized_copies_per_hepatocyte is not None
        or item.active_fraction is not None
        or item.active_copies_per_hepatocyte is not None
        or item.whole_cell_rate_ready
        for item in state.proteins
    ):
        raise ValueError("unmeasured protein activity was promoted")
    expected_domains = {
        "ABCB11": "canalicular_apical",
        "ABCC2": "canalicular_apical",
        "SLC10A1": "sinusoidal_basolateral",
        "INSR": None,
        "MET": None,
        "EGFR": None,
        "SLC2A2": None,
        "GCK": None,
    }
    if {item.gene: item.physiological_domain for item in state.proteins} != expected_domains:
        raise ValueError("PHH protein physiological-domain evidence changed")

    kinetics = {item.id: item for item in state.kinetic_observations}
    expected_kinetics = {
        "bsep_taurocholate_2002",
        "bsep_taurocholate_2013",
        "bsep_taurocholate_noe2002",
        "bsep_glycocholate_noe2002",
        "bsep_taurochenodeoxycholate_noe2002",
        "bsep_tauroursodeoxycholate_noe2002",
        "mrp2_monoglucuronosyl_bilirubin_1999",
        "mrp2_bisglucuronosyl_bilirubin_1999",
        "mrp2_estradiol_17_glucuronide_2017",
        "mrp2_coproporphyrin_I_2017",
        "ntcp_dominated_taurocholate_uptake_2003",
        "glut2_2_deoxyglucose_oocyte_1996",
    }
    if len(state.kinetic_observations) != 12 or set(kinetics) != expected_kinetics:
        raise ValueError("PHH protein kinetic panel changed")
    linked_kinetic_ids = [
        observation.id
        for protein in state.proteins
        for observation in protein.kinetic_observations
    ]
    if len(linked_kinetic_ids) != len(set(linked_kinetic_ids)) or set(
        linked_kinetic_ids
    ) != expected_kinetics:
        raise ValueError("PHH protein kinetic links are incomplete or duplicated")
    if any(
        observation.gene != protein.gene
        or observation.protein_id != protein.protein_id
        for protein in state.proteins
        for observation in protein.kinetic_observations
    ):
        raise ValueError("PHH kinetic observation was linked to the wrong protein")
    for observation in state.kinetic_observations:
        if observation.source_id not in state.source_ids or observation.may_scale_whole_cell_flux:
            raise ValueError("assay kinetics exceeded their source context")
        if observation.km.unit not in {"uM", "mM"}:
            raise ValueError("kinetic affinity unit changed")
        values = [value for value in (observation.km.value, observation.km.low, observation.km.high) if value is not None]
        if not values or any(not isfinite(value) or value <= 0.0 for value in values):
            raise ValueError("invalid kinetic affinity evidence")
        velocity = observation.velocity
        if velocity is not None and (
            not isfinite(velocity.value)
            or velocity.value <= 0.0
            or velocity.unit != "pmol_per_mg_assay_protein_per_min"
            or (velocity.sd is not None and (not isfinite(velocity.sd) or velocity.sd <= 0.0))
            or (
                velocity.substrate_concentration_uM is not None
                and (
                    not isfinite(velocity.substrate_concentration_uM)
                    or velocity.substrate_concentration_uM <= 0.0
                )
            )
        ):
            raise ValueError("invalid assay velocity evidence")
        hill = observation.hill_coefficient
        if hill is not None and (
            hill.kind != "point"
            or hill.unit != "dimensionless"
            or hill.value is None
            or not isfinite(hill.value)
            or hill.value <= 0.0
            or hill.low is not None
            or hill.high is not None
            or (hill.sd is not None and (not isfinite(hill.sd) or hill.sd <= 0.0))
        ):
            raise ValueError("invalid Hill-coefficient evidence")

    bsep_2002 = kinetics["bsep_taurocholate_2002"]
    bsep_2013 = kinetics["bsep_taurocholate_2013"]
    if (
        bsep_2002.velocity is None
        or bsep_2013.velocity is None
        or bsep_2002.velocity.kind != "vmax"
        or bsep_2013.velocity.kind != "vmax"
        or bsep_2002.km.value != 4.25
        or bsep_2013.km.value != 17.8
    ):
        raise ValueError("independent BSEP assay records were merged or altered")
    for observation_id, rate in (
        ("mrp2_monoglucuronosyl_bilirubin_1999", 183.0),
        ("mrp2_bisglucuronosyl_bilirubin_1999", 104.0),
    ):
        velocity = kinetics[observation_id].velocity
        if (
            velocity is None
            or velocity.kind != "rate_at_substrate_concentration"
            or velocity.value != rate
            or velocity.substrate_concentration_uM != 0.5
            or kinetics[observation_id].may_evaluate_assay_curve
        ):
            raise ValueError("MRP2 measured rate was mislabeled as Vmax")

    noe_bsep = {
        "bsep_taurocholate_noe2002": ("taurocholate", 7.9, 2.1),
        "bsep_glycocholate_noe2002": ("glycocholate", 11.1, 3.3),
        "bsep_taurochenodeoxycholate_noe2002": (
            "taurochenodeoxycholate",
            4.8,
            1.7,
        ),
        "bsep_tauroursodeoxycholate_noe2002": (
            "tauroursodeoxycholate",
            11.9,
            1.8,
        ),
    }
    if any(
        kinetics[observation_id].substrate != substrate
        or kinetics[observation_id].km.value != value
        or kinetics[observation_id].km.sd != sd
        or kinetics[observation_id].velocity is not None
        or kinetics[observation_id].may_evaluate_assay_curve
        for observation_id, (substrate, value, sd) in noe_bsep.items()
    ):
        raise ValueError("Noe 2002 BSEP affinity observations changed")

    mrp2_e17g = kinetics["mrp2_estradiol_17_glucuronide_2017"]
    mrp2_cpi = kinetics["mrp2_coproporphyrin_I_2017"]
    if (
        mrp2_e17g.kinetic_model != "hill_cooperative"
        or mrp2_e17g.km.kind != "apparent_S50"
        or (mrp2_e17g.km.value, mrp2_e17g.km.sd) != (170.0, 17.0)
        or mrp2_e17g.hill_coefficient is None
        or (
            mrp2_e17g.hill_coefficient.value,
            mrp2_e17g.hill_coefficient.sd,
        )
        != (2.05, 0.1)
        or mrp2_e17g.velocity is None
        or (mrp2_e17g.velocity.value, mrp2_e17g.velocity.sd) != (1447.0, 137.0)
        or not mrp2_e17g.may_evaluate_assay_curve
        or mrp2_cpi.km.value != 7.7
        or mrp2_cpi.km.sd != 0.7
        or mrp2_cpi.hill_coefficient is not None
        or mrp2_cpi.velocity is None
        or (mrp2_cpi.velocity.value, mrp2_cpi.velocity.sd) != (48.0, 11.0)
        or not mrp2_cpi.may_evaluate_assay_curve
    ):
        raise ValueError("Gilibili 2017 MRP2 kinetic observations changed")

    glut2 = kinetics["glut2_2_deoxyglucose_oocyte_1996"]
    if (
        glut2.km.unit != "mM"
        or (glut2.km.value, glut2.km.sd) != (11.2, 1.1)
        or glut2.velocity is not None
        or glut2.hill_coefficient is not None
        or glut2.may_evaluate_assay_curve
    ):
        raise ValueError("Arbuckle 1996 GLUT2 affinity observation changed")
    if any(
        observation.km.unit == "mM" and observation.id != glut2.id
        for observation in state.kinetic_observations
    ):
        raise ValueError("Only the source-reported GLUT2 affinity may use mM")
    if any(
        observation.hill_coefficient is not None and observation.id != mrp2_e17g.id
        for observation in state.kinetic_observations
    ):
        raise ValueError("Unexpected Hill coefficient was introduced")

    if len(state.whole_cell_transport_validations) != 1:
        raise ValueError("whole-cell transport validation panel changed")
    whole_cell = state.whole_cell_transport_validations[0]
    metric_ranges = {item.id: item for item in whole_cell.metric_ranges}
    expected_metrics = {
        "apparent_uptake": (11.0, 17.0, "pmol_per_min_per_mg_cell_protein"),
        "apparent_intrinsic_biliary_clearance": (
            5.8,
            10.0,
            "uL_per_min_per_mg_cell_protein",
        ),
        "biliary_excretion_index": (41.0, 63.0, "percent"),
    }
    if (
        whole_cell.id != "bi2006_schh_taurocholate_coupled_transport"
        or whole_cell.species != "Homo sapiens"
        or whole_cell.biological_system != "cryopreserved_primary_human_hepatocytes"
        or whole_cell.seeded_cells_per_well != 350_000
        or whole_cell.medium_volume_uL_per_well != 500.0
        or whole_cell.lot_count != 5
        or whole_cell.substrate != "taurocholate"
        or set(metric_ranges) != set(expected_metrics)
        or any(
            (metric_ranges[key].low, metric_ranges[key].high, metric_ranges[key].unit)
            != expected
            for key, expected in expected_metrics.items()
        )
    ):
        raise ValueError("Bi 2006 coupled taurocholate validation changed")
    if (
        whole_cell.source_id not in state.source_ids
        or whole_cell.individual_lot_values_loaded
        or whole_cell.uncertainty_statistics_loaded
        or whole_cell.exact_probe_protocol_loaded
        or whole_cell.may_identify_individual_transporter_rate
        or whole_cell.may_initialize_healthy_in_vivo_cell
        or whole_cell.may_drive_cell_state
        or any(
            not isfinite(metric.low)
            or not isfinite(metric.high)
            or metric.low < 0.0
            or metric.high <= metric.low
            for metric in whole_cell.metric_ranges
        )
    ):
        raise ValueError("whole-cell transport evidence exceeded its source context")

    response_ids = {item.id for item in state.functional_responses}
    if len(state.functional_responses) != 3 or response_ids != {
        "kemas_insulin_pakt_ser473_7min",
        "kemas_insulin_pck1_6h",
        "kemas_insulin_g6pc_6h",
    } or any(item.may_fit_quantitative_kinetics for item in state.functional_responses):
        raise ValueError("INSR response evidence exceeded its timepoint observations")

    required_true = {
        "donor_resolved_total_abundance_ready",
        "surface_identity_observation_ready",
        "physiological_domain_identity_ready",
        "assay_kinetic_observation_ready",
        "same_assay_parameter_comparison_ready",
        "whole_cell_transport_validation_observation_ready",
    }
    required_false = {
        "quantitative_surface_localization_ready",
        "active_fraction_ready",
        "exact_whole_cell_transport_comparison_ready",
        "receptor_binding_kinetics_ready",
        "donor_activity_distribution_ready",
        "whole_cell_flux_coupling_ready",
        "automatic_state_coupling",
        "predictive_ready",
    }
    if set(state.integration_gates) != required_true | required_false:
        raise ValueError("PHH protein-functional integration gate registry changed")
    if any(state.integration_gates.get(key) is not True for key in required_true) or any(
        state.integration_gates.get(key) is not False for key in required_false
    ):
        raise ValueError("PHH protein-functional integration gates changed")


def kinetic_observation_by_id(
    observation_id: str,
    *,
    state: ProteinFunctionalEvidenceState | None = None,
) -> ProteinKineticObservation:
    evidence = state or build_phh_protein_functional_evidence()
    matches = [item for item in evidence.kinetic_observations if item.id == observation_id]
    if len(matches) != 1:
        raise ValueError(f"unknown protein kinetic observation: {observation_id}")
    return matches[0]


def _metric_residual(
    observed: NumericEvidence,
    predicted: float,
    *,
    metric: str,
) -> AssayParameterResidual:
    if observed.value is not None:
        residual = predicted - observed.value
        standardized = residual / observed.sd if observed.sd not in (None, 0.0) else None
        within = None
    else:
        if observed.low is None or observed.high is None:
            raise ValueError("range evidence requires both lower and upper bounds")
        residual = None
        standardized = None
        within = observed.low <= predicted <= observed.high
    return AssayParameterResidual(
        metric=metric,
        observed_value=observed.value,
        observed_low=observed.low,
        observed_high=observed.high,
        observed_sd=observed.sd,
        predicted_value=predicted,
        raw_residual=residual,
        standardized_residual=standardized,
        within_reported_range=within,
        unit=observed.unit,
    )


def compare_same_assay_kinetics(
    prediction: AssayKineticPrediction,
    *,
    state: ProteinFunctionalEvidenceState | None = None,
) -> AssayKineticComparison:
    evidence = state or build_phh_protein_functional_evidence()
    observed = kinetic_observation_by_id(prediction.observation_id, state=evidence)
    velocity = observed.velocity
    hill = observed.hill_coefficient
    checks = {
        "protein match": prediction.protein_id == observed.protein_id,
        "substrate match": prediction.substrate == observed.substrate,
        "biological system match": prediction.biological_system == observed.biological_system,
        "kinetic model match": prediction.kinetic_model == observed.kinetic_model,
        "Km unit match": prediction.km_unit == observed.km.unit,
        "Hill coefficient contract match": (
            (
                hill is None
                and prediction.hill_coefficient_value is None
                and prediction.hill_coefficient_unit is None
            )
            or (
                hill is not None
                and prediction.hill_coefficient_value is not None
                and prediction.hill_coefficient_unit == hill.unit
            )
        ),
        "velocity contract match": (
            (velocity is None and prediction.velocity_kind is None and prediction.velocity_value is None)
            or (
                velocity is not None
                and prediction.velocity_kind == velocity.kind
                and prediction.velocity_unit == velocity.unit
                and prediction.velocity_value is not None
                and prediction.substrate_concentration_uM == velocity.substrate_concentration_uM
            )
        ),
    }
    blockers = tuple(label for label, passed in checks.items() if not passed)
    exact = not blockers
    audit = AssayComparisonAudit(
        protein_match=checks["protein match"],
        substrate_match=checks["substrate match"],
        biological_system_match=checks["biological system match"],
        kinetic_model_match=checks["kinetic model match"],
        km_unit_match=checks["Km unit match"],
        hill_coefficient_contract_match=checks["Hill coefficient contract match"],
        velocity_contract_match=checks["velocity contract match"],
        exact_input_match=exact,
        blockers=blockers,
    )
    residuals: list[AssayParameterResidual] = []
    if exact:
        residuals.append(_metric_residual(observed.km, prediction.km_value, metric="km"))
        if hill is not None and prediction.hill_coefficient_value is not None:
            residuals.append(
                _metric_residual(
                    hill,
                    prediction.hill_coefficient_value,
                    metric="hill_coefficient",
                )
            )
        if velocity is not None and prediction.velocity_value is not None:
            raw = prediction.velocity_value - velocity.value
            residuals.append(
                AssayParameterResidual(
                    metric=velocity.kind,
                    observed_value=velocity.value,
                    observed_low=None,
                    observed_high=None,
                    observed_sd=velocity.sd,
                    predicted_value=prediction.velocity_value,
                    raw_residual=raw,
                    standardized_residual=(raw / velocity.sd if velocity.sd not in (None, 0.0) else None),
                    within_reported_range=None,
                    unit=velocity.unit,
                )
            )
    return AssayKineticComparison(
        status="same_assay_residuals_ready" if exact else "blocked_context_mismatch",
        observation_id=observed.id,
        input_audit=audit,
        residuals=tuple(residuals),
        fitted_parameter_count=0,
        pass_fail_assigned=False,
        may_drive_cell_state=False,
    )


def phh_protein_functional_evidence_snapshot() -> dict[str, object]:
    state = build_phh_protein_functional_evidence()
    payload = state.to_dict()
    highest_cv = max(state.proteins, key=lambda item: item.abundance.sample_cv)
    payload["summary"] = {
        "protein_count": len(state.proteins),
        "donor_abundance_profile_count": len(state.proteins),
        "all_seven_donor_abundance_profile_count": sum(
            item.abundance.detected_donor_count == 7 for item in state.proteins
        ),
        "surface_identity_observation_count": sum(item.surface_capture_observed for item in state.proteins),
        "physiological_domain_identity_count": sum(item.physiological_domain is not None for item in state.proteins),
        "quantitative_surface_localization_count": 0,
        "active_fraction_observation_count": 0,
        "assay_kinetic_observation_count": len(state.kinetic_observations),
        "assay_curve_evaluable_count": sum(item.may_evaluate_assay_curve for item in state.kinetic_observations),
        "hill_coefficient_observation_count": sum(
            item.hill_coefficient is not None for item in state.kinetic_observations
        ),
        "receptor_binding_kinetic_observation_count": 0,
        "functional_response_observation_count": len(state.functional_responses),
        "whole_cell_transport_validation_observation_count": len(
            state.whole_cell_transport_validations
        ),
        "whole_cell_transport_metric_range_count": sum(
            len(item.metric_ranges) for item in state.whole_cell_transport_validations
        ),
        "whole_cell_transport_lot_count": sum(
            item.lot_count for item in state.whole_cell_transport_validations
        ),
        "exact_whole_cell_transport_prediction_count": 0,
        "same_assay_model_prediction_count": 0,
        "donor_activity_distribution_count": 0,
        "whole_cell_rate_ready_count": sum(item.whole_cell_rate_ready for item in state.proteins),
        "highest_selected_abundance_cv_gene": highest_cv.gene,
        "highest_selected_abundance_cv": highest_cv.abundance.sample_cv,
    }
    return payload
