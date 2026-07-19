"""Compartment-resolved structural contract for hepatocyte energy and redox.

The legacy runtime uses single ATP, NAD(H), NADP(H), glutathione and ROS pools.
That is useful for software demonstrations but cannot represent a hepatocyte:
cytosol, mitochondrial matrix, ER lumen and peroxisomes maintain distinct pools
connected by specific transporters and shuttles.

This module establishes the compartment and process graph without inventing
organelle concentrations, volumes or rates. Whole-liver measurements remain in
their original assay space, and donor-resolved PHH proteomics supports protein
presence only. Nothing in this contract is numerically executable.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain
from cell_engine.quantitative.phh_proteome_atlas import (
    DONOR_IDS,
    load_phh_proteome_atlas,
    protein_groups_for_gene,
)
from cell_engine.stochastic.bioenergetics import build_phh_atp_turnover_network
from cell_engine.stochastic.integrated_cell import INTEGRATED_VOLUME_L, build_integrated_hepatocyte_network
from cell_engine.stochastic.oxphos import build_oxphos_network
from cell_engine.stochastic.redox import build_redox_network
from cell_engine.stochastic.signaling import HormoneState


DATE_VERIFIED = "2026-07-20"
VERSION = "compartment_resolved_energy_redox_contract_v1"
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PHH_BASELINE_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "phh_baseline"
    / "curated"
    / "quantitative_anchors.json"
)


ENERGY_REDOX_SOURCES: dict[str, SourceReference] = {
    "cimadamore2023_slc25a4_exchange": SourceReference(
        id="cimadamore2023_slc25a4_exchange",
        title="Human mitochondrial ADP/ATP carrier SLC25A4 operates with a ping-pong kinetic mechanism",
        url="https://doi.org/10.15252/embr.202357127",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Purified human SLC25A4 establishes equimolar ADP/ATP exchange topology. "
            "Its assay kinetics are not transferred to a hepatocyte."
        ),
    ),
    "wang2021_slc25a39_mitochondrial_gsh": SourceReference(
        id="wang2021_slc25a39_mitochondrial_gsh",
        title="SLC25A39 is necessary for mitochondrial glutathione import in mammalian cells",
        url="https://doi.org/10.1038/s41586-021-04025-w",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Organelle metabolomics and transport experiments identify SLC25A39 as "
            "required for mitochondrial GSH import. The experiments are not PHH rate measurements."
        ),
    ),
    "yong2019_slc35b1_er_atp": SourceReference(
        id="yong2019_slc35b1_er_atp",
        title="Mitochondria supply ATP to the ER through a mechanism antagonized by cytosolic Ca2+",
        url="https://doi.org/10.7554/eLife.49682",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Cell-line experiments support SLC35B1/AXER-mediated ER ATP import. "
            "The result establishes mammalian topology, not a PHH transport rate."
        ),
    ),
    "lewis2014_compartmental_nadph": SourceReference(
        id="lewis2014_compartmental_nadph",
        title="Tracing compartmentalized NADPH metabolism in the cytosol and mitochondria of mammalian cells",
        url="https://doi.org/10.1016/j.molcel.2014.05.008",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Isotope tracing resolves distinct cytosolic and mitochondrial NADPH pathways. "
            "Cancer-cell-line fluxes are not transferred to PHH."
        ),
    ),
    "hwang1992_er_glutathione": SourceReference(
        id="hwang1992_er_glutathione",
        title="Oxidized redox state of glutathione in the endoplasmic reticulum",
        url="https://pubmed.ncbi.nlm.nih.gov/1523409/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Directly supports a secretory-pathway glutathione pool distinct from cytosol.",
    ),
    "kappenberg2022_phh_oxygen_consumption": SourceReference(
        id="kappenberg2022_phh_oxygen_consumption",
        title="Continuous non-invasive monitoring of oxygen consumption in primary human hepatocytes",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC8822303/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Supports oxygen-consumption time courses as a PHH observability surface. "
            "No value is activated here because an exact denominator-matched dataset has not been curated."
        ),
    ),
    "choudhary2014_vdac_transport": SourceReference(
        id="choudhary2014_vdac_transport",
        title="ATP transport through VDAC and the VDAC-tubulin complex probed by equilibrium and nonequilibrium MD simulations",
        url="https://doi.org/10.1021/bi4011495",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Supports VDAC as the principal outer-mitochondrial-membrane pathway "
            "for ATP/ADP and other respiratory substrates. Simulation-derived "
            "transport energetics are not transferred to PHH."
        ),
    ),
    "mayr2007_slc25a3_phosphate": SourceReference(
        id="mayr2007_slc25a3_phosphate",
        title="Mitochondrial phosphate-carrier deficiency: a novel disorder of oxidative phosphorylation",
        url="https://doi.org/10.1086/511788",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Human genetic evidence supports SLC25A3-mediated inorganic-phosphate "
            "delivery into the mitochondrial matrix. Patient phenotypes and rates "
            "are not transferred to healthy PHH."
        ),
    ),
}


@dataclass(frozen=True)
class EnergyRedoxCompartment:
    id: str
    label: str
    measured_volume_l: float | None
    volume_initialization_allowed: bool
    boundary: str


@dataclass(frozen=True)
class EnergyRedoxPool:
    id: str
    molecule: str
    compartment_id: str
    quantity_kind: str
    initial_value: float | None
    initial_unit: str | None
    initialization_allowed: bool
    source_ids: tuple[str, ...]
    limitation: str


@dataclass(frozen=True)
class EnergyRedoxProcess:
    id: str
    process_kind: str
    reactant_pool_ids: tuple[str, ...]
    product_pool_ids: tuple[str, ...]
    mediator_gene_symbols: tuple[str, ...]
    topology_source_ids: tuple[str, ...]
    exact_stoichiometry_claimed: bool
    numerical_rate: float | None
    numerical_rate_unit: str | None
    numerical_execution_allowed: bool
    evidence_context: str
    limitation: str


@dataclass(frozen=True)
class DonorProteinGroupObservation:
    group_id: str
    protein_ids: tuple[str, ...]
    detected_donor_count: int
    donor_copies_per_nucleus: tuple[tuple[str, float | None], ...]


@dataclass(frozen=True)
class EnergyRedoxGeneEvidence:
    gene_symbol: str
    source_status: str
    protein_groups: tuple[DonorProteinGroupObservation, ...]
    allowed_use: str
    prohibited_inference: str


@dataclass(frozen=True)
class AggregateEnergyRedoxObservation:
    id: str
    target: str
    value: float | None
    low: float | None
    high: float | None
    uncertainty_type: str | None
    uncertainty_value: float | None
    unit: str
    biological_system: str
    assay: str
    source_id: str
    permitted_use: str
    compartment_allocation_allowed: bool
    kinetic_parameter_fit_allowed: bool
    limitation: str


@dataclass(frozen=True)
class EnergyRedoxRuntimeConflict:
    id: str
    detected: bool
    affected_pool_or_reaction_ids: tuple[str, ...]
    consequence: str


@dataclass(frozen=True)
class CompartmentalEnergyRedoxContract:
    version: str
    status: str
    compartments: tuple[EnergyRedoxCompartment, ...]
    pools: tuple[EnergyRedoxPool, ...]
    processes: tuple[EnergyRedoxProcess, ...]
    human_phh_proteome_evidence: tuple[EnergyRedoxGeneEvidence, ...]
    aggregate_observations: tuple[AggregateEnergyRedoxObservation, ...]
    runtime_conflicts: tuple[EnergyRedoxRuntimeConflict, ...]
    compartment_topology_ready: bool
    whole_tissue_observation_registry_ready: bool
    human_phh_proteome_presence_bridge_ready: bool
    compartment_initialization_ready: bool
    numerical_execution_enabled: bool
    parameter_activation_allowed: bool
    automatic_state_coupling: bool
    predictive_ready: bool
    source_ids: tuple[str, ...]
    blockers: tuple[str, ...]
    policy: str

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def _compartments() -> tuple[EnergyRedoxCompartment, ...]:
    return (
        EnergyRedoxCompartment("sinusoidal_extracellular", "Sinusoidal extracellular space", None, False, "plasma_membrane_outside"),
        EnergyRedoxCompartment("cytosol", "Cytosol", None, False, "plasma_membrane_inside"),
        EnergyRedoxCompartment("mitochondrial_intermembrane_space", "Mitochondrial intermembrane space", None, False, "between_mitochondrial_membranes"),
        EnergyRedoxCompartment("mitochondrial_matrix", "Mitochondrial matrix", None, False, "inside_inner_mitochondrial_membrane"),
        EnergyRedoxCompartment("er_lumen", "Endoplasmic-reticulum lumen", None, False, "inside_er_membrane"),
        EnergyRedoxCompartment("peroxisomal_matrix", "Peroxisomal matrix", None, False, "inside_peroxisomal_membrane"),
    )


def _pool(
    pool_id: str,
    molecule: str,
    compartment_id: str,
    source_ids: tuple[str, ...],
    limitation: str,
    *,
    quantity_kind: str = "chemical_pool",
) -> EnergyRedoxPool:
    return EnergyRedoxPool(
        id=pool_id,
        molecule=molecule,
        compartment_id=compartment_id,
        quantity_kind=quantity_kind,
        initial_value=None,
        initial_unit=None,
        initialization_allowed=False,
        source_ids=source_ids,
        limitation=limitation,
    )


def _pools() -> tuple[EnergyRedoxPool, ...]:
    aggregate_only = "Available measurements are aggregate; no compartment value is inferred."
    redox_split = "A distinct physical pool is required, but no matched healthy-PHH initial value is available."
    return (
        _pool("oxygen_sinusoidal_extracellular", "O2", "sinusoidal_extracellular", ("kappenberg2022_phh_oxygen_consumption",), "No in-situ single-sinusoid concentration is curated."),
        _pool("oxygen_cytosol", "O2", "cytosol", ("kappenberg2022_phh_oxygen_consumption",), redox_split),
        _pool("atp_cytosol", "ATP", "cytosol", ("human_liver_adenylates_1992",), aggregate_only),
        _pool("adp_cytosol", "ADP", "cytosol", ("human_liver_adenylates_1992",), aggregate_only),
        _pool("amp_cytosol", "AMP", "cytosol", ("human_liver_adenylates_1992",), aggregate_only),
        _pool("phosphate_cytosol", "Pi", "cytosol", ("human_liver_atp_synthesis_2008",), "The MRS exchange assay does not provide a compartment-resolved initial Pi pool."),
        _pool("nad_plus_cytosol", "NAD+", "cytosol", ("human_liver_adenylates_1992",), aggregate_only),
        _pool("nadh_cytosol", "NADH", "cytosol", ("lewis2014_compartmental_nadph",), redox_split),
        _pool("nadp_plus_cytosol", "NADP+", "cytosol", ("lewis2014_compartmental_nadph",), redox_split),
        _pool("nadph_cytosol", "NADPH", "cytosol", ("lewis2014_compartmental_nadph",), redox_split),
        _pool("gsh_cytosol", "GSH", "cytosol", ("human_liver_glutathione_1980", "wang2021_slc25a39_mitochondrial_gsh"), aggregate_only),
        _pool("gssg_cytosol", "GSSG", "cytosol", ("human_liver_glutathione_1980",), aggregate_only),
        _pool("hydrogen_peroxide_cytosol", "H2O2", "cytosol", ("glutathione_redox",), redox_split),
        _pool("atp_mitochondrial_intermembrane_space", "ATP", "mitochondrial_intermembrane_space", ("cimadamore2023_slc25a4_exchange", "choudhary2014_vdac_transport"), redox_split),
        _pool("adp_mitochondrial_intermembrane_space", "ADP", "mitochondrial_intermembrane_space", ("cimadamore2023_slc25a4_exchange", "choudhary2014_vdac_transport"), redox_split),
        _pool("phosphate_mitochondrial_intermembrane_space", "Pi", "mitochondrial_intermembrane_space", ("choudhary2014_vdac_transport", "mayr2007_slc25a3_phosphate"), redox_split),
        _pool("oxygen_mitochondrial_matrix", "O2", "mitochondrial_matrix", ("kappenberg2022_phh_oxygen_consumption",), redox_split),
        _pool("atp_mitochondrial_matrix", "ATP", "mitochondrial_matrix", ("cimadamore2023_slc25a4_exchange",), aggregate_only),
        _pool("adp_mitochondrial_matrix", "ADP", "mitochondrial_matrix", ("cimadamore2023_slc25a4_exchange",), aggregate_only),
        _pool("phosphate_mitochondrial_matrix", "Pi", "mitochondrial_matrix", ("human_liver_atp_synthesis_2008",), aggregate_only),
        _pool("nad_plus_mitochondrial_matrix", "NAD+", "mitochondrial_matrix", ("human_liver_adenylates_1992", "lewis2014_compartmental_nadph"), aggregate_only),
        _pool("nadh_mitochondrial_matrix", "NADH", "mitochondrial_matrix", ("lewis2014_compartmental_nadph",), redox_split),
        _pool("nadp_plus_mitochondrial_matrix", "NADP+", "mitochondrial_matrix", ("lewis2014_compartmental_nadph",), redox_split),
        _pool("nadph_mitochondrial_matrix", "NADPH", "mitochondrial_matrix", ("lewis2014_compartmental_nadph",), redox_split),
        _pool("gsh_mitochondrial_matrix", "GSH", "mitochondrial_matrix", ("wang2021_slc25a39_mitochondrial_gsh",), redox_split),
        _pool("gssg_mitochondrial_matrix", "GSSG", "mitochondrial_matrix", ("wang2021_slc25a39_mitochondrial_gsh",), redox_split),
        _pool("superoxide_mitochondrial_matrix", "O2.-", "mitochondrial_matrix", ("human_hepatocyte_proteome_2016",), redox_split),
        _pool("hydrogen_peroxide_mitochondrial_matrix", "H2O2", "mitochondrial_matrix", ("human_hepatocyte_proteome_2016",), redox_split),
        _pool("water_mitochondrial_matrix", "H2O", "mitochondrial_matrix", ("oxphos_po_ratio",), redox_split),
        _pool("mitochondrial_proton_motive_force", "proton_motive_force", "mitochondrial_intermembrane_space", ("oxphos_po_ratio",), "No membrane-potential or delta-pH initial condition is inferred.", quantity_kind="electrochemical_state"),
        _pool("atp_er_lumen", "ATP", "er_lumen", ("yong2019_slc35b1_er_atp",), redox_split),
        _pool("adp_er_lumen", "ADP", "er_lumen", ("yong2019_slc35b1_er_atp",), redox_split),
        _pool("gsh_er_lumen", "GSH", "er_lumen", ("hwang1992_er_glutathione",), redox_split),
        _pool("gssg_er_lumen", "GSSG", "er_lumen", ("hwang1992_er_glutathione",), redox_split),
        _pool("hydrogen_peroxide_er_lumen", "H2O2", "er_lumen", ("hwang1992_er_glutathione",), redox_split),
        _pool("oxygen_peroxisomal_matrix", "O2", "peroxisomal_matrix", ("human_hepatocyte_proteome_2016",), redox_split),
        _pool("hydrogen_peroxide_peroxisomal_matrix", "H2O2", "peroxisomal_matrix", ("human_hepatocyte_proteome_2016",), redox_split),
        _pool("water_peroxisomal_matrix", "H2O", "peroxisomal_matrix", ("human_hepatocyte_proteome_2016",), redox_split),
    )


def _processes() -> tuple[EnergyRedoxProcess, ...]:
    no_rate = dict(
        exact_stoichiometry_claimed=False,
        numerical_rate=None,
        numerical_rate_unit=None,
        numerical_execution_allowed=False,
    )
    return (
        EnergyRedoxProcess(
            "respiratory_chain_proton_pumping",
            "coupled_electron_transport_system",
            ("nadh_mitochondrial_matrix", "oxygen_mitochondrial_matrix"),
            ("nad_plus_mitochondrial_matrix", "water_mitochondrial_matrix", "mitochondrial_proton_motive_force"),
            ("NDUFS1", "UQCRC1", "COX4I1"),
            ("oxphos_po_ratio", "human_hepatocyte_proteome_2016"),
            evidence_context="Canonical mammalian inner-membrane topology plus total PHH protein-group evidence.",
            limitation="Complex stoichiometry, proton leak, assembly, oxygen flux and membrane potential are not activated.",
            **no_rate,
        ),
        EnergyRedoxProcess(
            "atp_synthase_coupling",
            "proton_motive_atp_synthesis_system",
            ("adp_mitochondrial_matrix", "phosphate_mitochondrial_matrix", "mitochondrial_proton_motive_force"),
            ("atp_mitochondrial_matrix",),
            ("ATP5A1", "ATP5B"),
            ("oxphos_po_ratio", "human_hepatocyte_proteome_2016"),
            evidence_context="Canonical mammalian ATP-synthase topology plus total PHH protein-group evidence.",
            limitation="P/O ratio, proton stoichiometry, ATP-synthase activity and reverse operation are not activated.",
            **no_rate,
        ),
        EnergyRedoxProcess(
            "outer_mitochondrial_membrane_metabolite_permeation",
            "bidirectional_outer_membrane_channel",
            ("atp_cytosol", "adp_cytosol", "phosphate_cytosol"),
            ("atp_mitochondrial_intermembrane_space", "adp_mitochondrial_intermembrane_space", "phosphate_mitochondrial_intermembrane_space"),
            ("VDAC1", "VDAC2", "VDAC3"),
            ("choudhary2014_vdac_transport", "human_hepatocyte_proteome_2016"),
            evidence_context="Outer-membrane VDAC topology plus donor-resolved total PHH protein-group evidence.",
            limitation="Direction is bidirectional; open probability, isoform contribution and PHH permeability are unavailable.",
            **no_rate,
        ),
        EnergyRedoxProcess(
            "mitochondrial_adp_atp_exchange",
            "equimolar_antiport",
            ("atp_mitochondrial_matrix", "adp_mitochondrial_intermembrane_space"),
            ("atp_mitochondrial_intermembrane_space", "adp_mitochondrial_matrix"),
            ("SLC25A4", "SLC25A5", "SLC25A6"),
            ("cimadamore2023_slc25a4_exchange", "human_hepatocyte_proteome_2016"),
            evidence_context="Purified human carrier topology; all three listed isoforms quantified in seven-donor PHH proteomics.",
            limitation="Isoform-specific PHH membrane abundance, activity and exchange kinetics are not identified.",
            **no_rate,
        ),
        EnergyRedoxProcess(
            "mitochondrial_phosphate_import",
            "inner_membrane_phosphate_transport",
            ("phosphate_mitochondrial_intermembrane_space",),
            ("phosphate_mitochondrial_matrix",),
            ("SLC25A3",),
            ("mayr2007_slc25a3_phosphate", "human_hepatocyte_proteome_2016"),
            evidence_context="Human genetic transport evidence plus total PHH protein-group abundance.",
            limitation="Transport mode, driving force, active fraction and healthy-PHH phosphate flux are not identified.",
            **no_rate,
        ),
        EnergyRedoxProcess(
            "er_atp_adp_exchange",
            "organelle_nucleotide_exchange",
            ("atp_cytosol", "adp_er_lumen"),
            ("atp_er_lumen", "adp_cytosol"),
            ("SLC35B1",),
            ("yong2019_slc35b1_er_atp",),
            evidence_context="CHO, INS1 and HeLa experiments; mammalian topology only.",
            limitation="SLC35B1 was not quantified in the seven-donor PHH atlas; non-detection is not absence.",
            **no_rate,
        ),
        EnergyRedoxProcess(
            "mitochondrial_gsh_import",
            "organelle_transport",
            ("gsh_cytosol",),
            ("gsh_mitochondrial_matrix",),
            ("SLC25A39",),
            ("wang2021_slc25a39_mitochondrial_gsh",),
            evidence_context="Mammalian-cell organelle transport experiments; topology only.",
            limitation="No PHH SLC25A39 abundance, active fraction or GSH import rate is available.",
            **no_rate,
        ),
        EnergyRedoxProcess(
            "malate_aspartate_reducing_equivalent_shuttle",
            "reducing_equivalent_shuttle_not_nadh_transport",
            ("nadh_cytosol", "nad_plus_mitochondrial_matrix"),
            ("nad_plus_cytosol", "nadh_mitochondrial_matrix"),
            ("MDH1", "MDH2", "GOT1", "GOT2"),
            ("lewis2014_compartmental_nadph", "human_hepatocyte_proteome_2016"),
            evidence_context="Structural shorthand for redox-equivalent transfer between distinct NAD(H) pools.",
            limitation="The listed pool relation is not the shuttle's full metabolite stoichiometry and has no PHH flux.",
            **no_rate,
        ),
        EnergyRedoxProcess(
            "cytosolic_pentose_phosphate_nadph_generation",
            "compartment_specific_redox_generation",
            ("nadp_plus_cytosol",),
            ("nadph_cytosol",),
            ("G6PD", "PGD"),
            ("lewis2014_compartmental_nadph", "human_hepatocyte_proteome_2016"),
            evidence_context="Compartment-resolved mammalian isotope tracing plus total PHH protein abundance.",
            limitation="Substrate pools, enzyme activity and donor-matched PHH NADPH flux are unavailable.",
            **no_rate,
        ),
        EnergyRedoxProcess(
            "mitochondrial_nadph_regeneration",
            "compartment_specific_redox_generation",
            ("nadp_plus_mitochondrial_matrix", "nadh_mitochondrial_matrix"),
            ("nadph_mitochondrial_matrix", "nad_plus_mitochondrial_matrix"),
            ("IDH2", "NNT"),
            ("lewis2014_compartmental_nadph", "human_hepatocyte_proteome_2016"),
            evidence_context="Distinct mitochondrial NADPH network plus total PHH protein abundance.",
            limitation="IDH2 and NNT are separate mechanisms; the shorthand is not a single reaction or fitted rate law.",
            **no_rate,
        ),
        EnergyRedoxProcess(
            "cytosolic_glutathione_peroxide_buffering",
            "antioxidant_reaction_system",
            ("gsh_cytosol", "hydrogen_peroxide_cytosol", "nadph_cytosol"),
            ("gssg_cytosol", "nadp_plus_cytosol"),
            ("GPX1", "GSR"),
            ("glutathione_redox", "human_hepatocyte_proteome_2016"),
            evidence_context="Canonical glutathione-cycle topology plus total PHH protein abundance.",
            limitation="Peroxide production, compartment-specific enzyme activity and PHH turnover are unmeasured.",
            **no_rate,
        ),
        EnergyRedoxProcess(
            "mitochondrial_superoxide_and_peroxide_buffering",
            "antioxidant_reaction_system",
            ("superoxide_mitochondrial_matrix", "gsh_mitochondrial_matrix", "nadph_mitochondrial_matrix"),
            ("hydrogen_peroxide_mitochondrial_matrix", "gssg_mitochondrial_matrix", "nadp_plus_mitochondrial_matrix"),
            ("SOD2", "GPX4", "PRDX3", "GSR"),
            ("wang2021_slc25a39_mitochondrial_gsh", "human_hepatocyte_proteome_2016"),
            evidence_context="Mitochondrial glutathione dependency plus total PHH protein abundance.",
            limitation="Multiple reactions are represented as a non-executable system; ROS leak and scavenging rates are unknown.",
            **no_rate,
        ),
        EnergyRedoxProcess(
            "er_oxidative_folding_redox_system",
            "secretory_pathway_redox_system",
            ("gsh_er_lumen",),
            ("gssg_er_lumen", "hydrogen_peroxide_er_lumen"),
            ("PRDX4", "ERO1A", "ERO1B"),
            ("hwang1992_er_glutathione", "human_hepatocyte_proteome_2016"),
            evidence_context="Secretory-pathway redox compartment plus total PHH protein-group evidence where detected.",
            limitation="Protein-folding load, ER redox potential and PHH reaction rates are unavailable.",
            **no_rate,
        ),
        EnergyRedoxProcess(
            "peroxisomal_catalase_buffering",
            "peroxide_dismutation",
            ("hydrogen_peroxide_peroxisomal_matrix",),
            ("oxygen_peroxisomal_matrix", "water_peroxisomal_matrix"),
            ("CAT",),
            ("human_hepatocyte_proteome_2016",),
            evidence_context="CAT is quantified in all seven PHH donor proteomes; catalytic topology is canonical.",
            limitation="Total copies per nucleus do not identify peroxisomal active concentration or H2O2 turnover.",
            **no_rate,
        ),
    )


def _proteome_evidence(processes: tuple[EnergyRedoxProcess, ...]) -> tuple[EnergyRedoxGeneEvidence, ...]:
    atlas = load_phh_proteome_atlas()
    genes = sorted({gene for process in processes for gene in process.mediator_gene_symbols})
    evidence: list[EnergyRedoxGeneEvidence] = []
    for gene in genes:
        groups = protein_groups_for_gene(gene, payload=atlas)
        observations = tuple(
            DonorProteinGroupObservation(
                group_id=str(record["group_id"]),
                protein_ids=tuple(str(item) for item in record["protein_ids"]),
                detected_donor_count=int(record["detected_donor_count"]),
                donor_copies_per_nucleus=tuple(
                    (
                        donor_id,
                        float(record["donor_values"][donor_id]["copies_per_nucleus"])
                        if record["donor_values"][donor_id]["copies_per_nucleus"] is not None
                        else None,
                    )
                    for donor_id in DONOR_IDS
                ),
            )
            for record in groups
        )
        evidence.append(
            EnergyRedoxGeneEvidence(
                gene_symbol=gene,
                source_status=(
                    "quantified_as_one_or_more_distinct_protein_groups"
                    if observations
                    else "not_quantified_in_this_source_not_evidence_of_absence"
                ),
                protein_groups=observations,
                allowed_use="static_total_protein_group_abundance_per_reference_nucleus",
                prohibited_inference=(
                    "No compartment-localized concentration, active fraction, complex assembly, "
                    "turnover, flux or rate scaling may be inferred."
                ),
            )
        )
    return tuple(evidence)


def _aggregate_observations() -> tuple[AggregateEnergyRedoxObservation, ...]:
    payload = json.loads(PHH_BASELINE_PATH.read_text(encoding="utf-8"))
    wanted = (
        "human_liver_atp_control",
        "human_liver_adp_control",
        "human_liver_amp_control",
        "human_liver_energy_charge_control",
        "human_liver_nad_plus_control",
        "human_liver_total_glutathione",
        "human_liver_apparent_atp_synthesis",
    )
    anchors = {item["id"]: item for item in payload["anchors"]}
    result: list[AggregateEnergyRedoxObservation] = []
    for observation_id in wanted:
        anchor = anchors[observation_id]
        measurement = anchor["measurement"]
        if observation_id == "human_liver_total_glutathione":
            permitted_use = "original_protein_denominator_aggregate_reference_only"
        elif observation_id == "human_liver_apparent_atp_synthesis":
            permitted_use = "same_assay_apparent_pi_to_atp_exchange_observation_only"
        else:
            permitted_use = "whole_liver_aggregate_reference_only"
        result.append(
            AggregateEnergyRedoxObservation(
                id=str(anchor["id"]),
                target=str(anchor["target"]),
                value=float(measurement["value"]) if measurement["value"] is not None else None,
                low=float(measurement["low"]) if measurement["low"] is not None else None,
                high=float(measurement["high"]) if measurement["high"] is not None else None,
                uncertainty_type=(
                    str(measurement["uncertainty_type"])
                    if measurement["uncertainty_type"] is not None
                    else None
                ),
                uncertainty_value=(
                    float(measurement["uncertainty_value"])
                    if measurement["uncertainty_value"] is not None
                    else None
                ),
                unit=str(measurement["unit"]),
                biological_system=str(anchor["biological_system"]),
                assay=str(anchor["assay"]),
                source_id=str(anchor["source_id"]),
                permitted_use=permitted_use,
                compartment_allocation_allowed=False,
                kinetic_parameter_fit_allowed=False,
                limitation=str(anchor["limitations"]),
            )
        )
    return tuple(result)


def _runtime_conflicts() -> tuple[EnergyRedoxRuntimeConflict, ...]:
    integrated = build_integrated_hepatocyte_network(HormoneState())
    atp = build_phh_atp_turnover_network(INTEGRATED_VOLUME_L)
    redox = build_redox_network(INTEGRATED_VOLUME_L)
    oxphos = build_oxphos_network()
    integrated_species = set(integrated.species)
    atp_reactions = {item.id: item for item in atp.reactions}
    return (
        EnergyRedoxRuntimeConflict(
            "adenylate_compartment_collapse",
            {"ATP", "ADP", "AMP"} <= integrated_species,
            ("ATP", "ADP", "AMP"),
            "Cytosolic, mitochondrial and ER adenylates share one runtime pool and one volume.",
        ),
        EnergyRedoxRuntimeConflict(
            "nad_redox_compartment_collapse",
            {"NAD_plus", "NADH"} <= integrated_species,
            ("NAD_plus", "NADH"),
            "Cytosolic and mitochondrial NAD(H) are merged, bypassing redox shuttles.",
        ),
        EnergyRedoxRuntimeConflict(
            "apparent_exchange_miscast_as_turnover",
            {"atp_regeneration", "atp_maintenance"} <= set(atp_reactions),
            ("human_liver_apparent_atp_synthesis", "atp_regeneration", "atp_maintenance"),
            "A whole-liver Pi-to-ATP exchange observation is mapped to two unmeasured first-order reactions.",
        ),
        EnergyRedoxRuntimeConflict(
            "redox_placeholder_kinetics",
            all(
                any(parameter.assumption_level == "placeholder" for parameter in reaction.parameter_provenance)
                for reaction in redox.reactions
            ),
            tuple(reaction.id for reaction in redox.reactions),
            "All executable glutathione/ROS rates are software-fixture placeholders.",
        ),
        EnergyRedoxRuntimeConflict(
            "oxphos_placeholder_kinetics",
            all(
                any(parameter.assumption_level == "placeholder" for parameter in reaction.parameter_provenance)
                for reaction in oxphos.reactions
            ),
            tuple(reaction.id for reaction in oxphos.reactions),
            "All executable TCA/OXPHOS Vmax and Km values are software-fixture placeholders.",
        ),
        EnergyRedoxRuntimeConflict(
            "er_and_peroxisome_redox_omitted",
            not any("er_lumen" in species or "peroxisomal" in species for species in integrated_species),
            ("er_lumen", "peroxisomal_matrix"),
            "The integrated fuel runtime has no explicit ER-lumen or peroxisomal energy/redox state.",
        ),
    )


def build_compartmental_energy_redox_contract() -> CompartmentalEnergyRedoxContract:
    compartments = _compartments()
    pools = _pools()
    processes = _processes()
    conflicts = _runtime_conflicts()
    state = CompartmentalEnergyRedoxContract(
        version=VERSION,
        status="structural_and_human_proteome_reference_ready_numerical_state_blocked",
        compartments=compartments,
        pools=pools,
        processes=processes,
        human_phh_proteome_evidence=_proteome_evidence(processes),
        aggregate_observations=_aggregate_observations(),
        runtime_conflicts=conflicts,
        compartment_topology_ready=True,
        whole_tissue_observation_registry_ready=True,
        human_phh_proteome_presence_bridge_ready=True,
        compartment_initialization_ready=False,
        numerical_execution_enabled=False,
        parameter_activation_allowed=False,
        automatic_state_coupling=False,
        predictive_ready=False,
        source_ids=(
            "human_liver_adenylates_1992",
            "human_liver_atp_synthesis_2008",
            "human_liver_glutathione_1980",
            "human_hepatocyte_proteome_2016",
            *ENERGY_REDOX_SOURCES,
        ),
        blockers=(
            "No matched healthy-PHH compartment volumes are curated.",
            "No donor-matched cytosol/matrix/ER/peroxisome ATP, NAD(H), NADP(H), GSH/GSSG and ROS initial state exists.",
            "Whole-liver Pi-to-ATP exchange does not identify mitochondrial ATP synthesis or cellular ATP demand.",
            "Total protein copies per nucleus do not identify localization, active fraction or assembled complexes.",
            "No exact PHH oxygen-consumption and ATP-linked-respiration trajectory is loaded with a matched denominator.",
            "No compartment-resolved isotope or redox-sensor trajectory identifies shuttle and antioxidant fluxes.",
            "No donor-disjoint held-out validation set exists for energy/redox dynamics.",
        ),
        policy=(
            "Compartments, physical pool identity and source-supported process topology may drive structural tests. "
            "All compartment values and rates remain null until a matched human-PHH measurement, unit bridge, "
            "uncertainty model and held-out validation qualify them."
        ),
    )
    validate_compartmental_energy_redox_contract(state)
    return state


def validate_compartmental_energy_redox_contract(state: CompartmentalEnergyRedoxContract) -> None:
    if state.version != VERSION:
        raise ValueError("energy/redox contract version changed")
    compartment_ids = {item.id for item in state.compartments}
    expected_compartments = {
        "sinusoidal_extracellular",
        "cytosol",
        "mitochondrial_intermembrane_space",
        "mitochondrial_matrix",
        "er_lumen",
        "peroxisomal_matrix",
    }
    if compartment_ids != expected_compartments:
        raise ValueError("energy/redox compartment registry changed")
    if any(item.measured_volume_l is not None or item.volume_initialization_allowed for item in state.compartments):
        raise ValueError("unmeasured organelle volume was activated")
    pool_ids = [item.id for item in state.pools]
    if len(pool_ids) != len(set(pool_ids)) or any(item.compartment_id not in compartment_ids for item in state.pools):
        raise ValueError("energy/redox pool registry is duplicated or references an unknown compartment")
    required_pools = {
        "atp_cytosol",
        "atp_mitochondrial_intermembrane_space",
        "atp_mitochondrial_matrix",
        "atp_er_lumen",
        "nadh_cytosol",
        "nadh_mitochondrial_matrix",
        "nadph_cytosol",
        "nadph_mitochondrial_matrix",
        "gsh_cytosol",
        "gsh_mitochondrial_matrix",
        "gsh_er_lumen",
        "hydrogen_peroxide_peroxisomal_matrix",
        "mitochondrial_proton_motive_force",
    }
    if not required_pools <= set(pool_ids):
        raise ValueError("required compartment-resolved energy/redox pools are missing")
    if any(
        item.initial_value is not None
        or item.initial_unit is not None
        or item.initialization_allowed
        for item in state.pools
    ):
        raise ValueError("an unmeasured compartment pool was initialized")
    process_ids = [item.id for item in state.processes]
    if len(process_ids) != len(set(process_ids)) or len(process_ids) != 14:
        raise ValueError("energy/redox process registry changed")
    known_pools = set(pool_ids)
    if any(
        not set(item.reactant_pool_ids + item.product_pool_ids) <= known_pools
        or item.numerical_rate is not None
        or item.numerical_rate_unit is not None
        or item.numerical_execution_allowed
        for item in state.processes
    ):
        raise ValueError("energy/redox process exceeded structural authority")
    gene_ids = [item.gene_symbol for item in state.human_phh_proteome_evidence]
    expected_genes = sorted({gene for process in state.processes for gene in process.mediator_gene_symbols})
    if gene_ids != expected_genes:
        raise ValueError("energy/redox PHH proteome bridge is incomplete")
    for evidence in state.human_phh_proteome_evidence:
        for group in evidence.protein_groups:
            if tuple(donor_id for donor_id, _ in group.donor_copies_per_nucleus) != DONOR_IDS:
                raise ValueError("energy/redox PHH proteome donor columns changed")
    if len(state.aggregate_observations) != 7 or any(
        item.compartment_allocation_allowed or item.kinetic_parameter_fit_allowed
        for item in state.aggregate_observations
    ):
        raise ValueError("aggregate energy/redox evidence was promoted beyond its assay")
    expected_conflicts = {
        "adenylate_compartment_collapse",
        "nad_redox_compartment_collapse",
        "apparent_exchange_miscast_as_turnover",
        "redox_placeholder_kinetics",
        "oxphos_placeholder_kinetics",
        "er_and_peroxisome_redox_omitted",
    }
    if {item.id for item in state.runtime_conflicts if item.detected} != expected_conflicts:
        raise ValueError("legacy energy/redox runtime conflicts changed without review")
    if (
        not state.compartment_topology_ready
        or not state.whole_tissue_observation_registry_ready
        or not state.human_phh_proteome_presence_bridge_ready
        or state.compartment_initialization_ready
        or state.numerical_execution_enabled
        or state.parameter_activation_allowed
        or state.automatic_state_coupling
        or state.predictive_ready
    ):
        raise ValueError("energy/redox contract exceeded current evidence")


def compartmental_energy_redox_snapshot() -> dict[str, object]:
    state = build_compartmental_energy_redox_contract()
    payload = state.to_dict()
    payload["summary"] = {
        "compartment_count": len(state.compartments),
        "explicit_pool_count": len(state.pools),
        "structural_process_count": len(state.processes),
        "phh_proteome_gene_count": len(state.human_phh_proteome_evidence),
        "phh_quantified_gene_count": sum(bool(item.protein_groups) for item in state.human_phh_proteome_evidence),
        "aggregate_observation_count": len(state.aggregate_observations),
        "detected_runtime_conflict_count": sum(item.detected for item in state.runtime_conflicts),
        "initialized_compartment_pool_count": sum(item.initialization_allowed for item in state.pools),
        "executable_process_count": sum(item.numerical_execution_allowed for item in state.processes),
        "activated_parameter_count": int(state.parameter_activation_allowed),
    }
    return payload
