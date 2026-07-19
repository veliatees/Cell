"""Source-exact structural contract for hepatocyte glucose homeostasis.

This module deliberately separates three claims that older exploratory networks
mixed together:

1. a published reaction graph can establish topology and stoichiometry;
2. a canonical pool registry can establish which names represent one physical
   pool; and
3. numerical execution requires independently qualified kinetic parameters.

The official Koenig 2012 SBML supplement is used only for its exact 52-species,
36-reaction structure. It contains no kinetic laws. The current active network
is audited for incompatible pool splitting and lumping, but is not silently
rewritten or promoted by this contract.
"""

from __future__ import annotations

from dataclasses import dataclass

from cell_engine.core.serialization import to_plain
from cell_engine.io.sbml import (
    inspect_sbml_document,
    inspect_sbml_reaction_fingerprints,
    inspect_sbml_species_fingerprints,
)
from cell_engine.quantitative.published_glucose_model import (
    OFFICIAL_MODEL_PATH,
    OFFICIAL_MODEL_SHA256,
)
from cell_engine.stochastic.integrated_cell import build_integrated_hepatocyte_network
from cell_engine.stochastic.signaling import HormoneState


VERSION = "exact_glucose_homeostasis_subnetwork_v1"


@dataclass(frozen=True)
class StoichiometricTerm:
    species_id: str
    stoichiometry: float
    compartment_id: str


@dataclass(frozen=True)
class SourceExactReaction:
    reaction_id: str
    name: str | None
    reversible: bool
    reactants: tuple[StoichiometricTerm, ...]
    products: tuple[StoichiometricTerm, ...]
    modifier_species_ids: tuple[str, ...]
    kinetic_law_present: bool
    topology_source_id: str


@dataclass(frozen=True)
class CanonicalPoolMapping:
    canonical_pool_id: str
    compartment_id: str
    source_species_ids: tuple[str, ...]
    exploratory_runtime_species_ids: tuple[str, ...]
    mapping_status: str


@dataclass(frozen=True)
class RuntimeStructuralConflict:
    id: str
    detected: bool
    affected_species_ids: tuple[str, ...]
    affected_reaction_ids: tuple[str, ...]
    consequence: str


@dataclass(frozen=True)
class ExactGlucoseHomeostasisContract:
    version: str
    status: str
    source_model_id: str
    source_model_sha256: str
    source_compartment_ids: tuple[str, ...]
    source_species_count: int
    source_reaction_count: int
    source_kinetic_law_count: int
    source_species: tuple[dict[str, object], ...]
    source_reactions: tuple[SourceExactReaction, ...]
    canonical_pools: tuple[CanonicalPoolMapping, ...]
    runtime_conflicts: tuple[RuntimeStructuralConflict, ...]
    exact_source_topology_ready: bool
    canonical_pool_contract_ready: bool
    active_runtime_replacement_ready: bool
    numerical_execution_enabled: bool
    parameter_activation_allowed: bool
    predictive_ready: bool
    source_ids: tuple[str, ...]
    blockers: tuple[str, ...]
    policy: str

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def _term(participant: object) -> StoichiometricTerm:
    return StoichiometricTerm(
        species_id=str(getattr(participant, "species_id")),
        stoichiometry=float(getattr(participant, "stoichiometry")),
        compartment_id=str(getattr(participant, "compartment_id")),
    )


def _canonical_pools() -> tuple[CanonicalPoolMapping, ...]:
    return (
        CanonicalPoolMapping(
            "glucose_extracellular",
            "blood_or_assay_medium",
            ("glc_blood",),
            ("glucose_blood",),
            "one_to_one_name_bridge",
        ),
        CanonicalPoolMapping(
            "glucose_cytosol",
            "cytosol",
            ("glc",),
            ("glucose", "glucose_cyto"),
            "blocked_exploratory_runtime_splits_one_physical_pool",
        ),
        CanonicalPoolMapping(
            "glucose_6_phosphate_cytosol",
            "cytosol",
            ("glc6p",),
            ("glucose_6_phosphate",),
            "one_to_one_name_bridge",
        ),
        CanonicalPoolMapping(
            "glycogen_glucosyl_residue_cytosol",
            "cytosol",
            ("glyglc",),
            ("glycogen",),
            "one_to_one_name_bridge",
        ),
        CanonicalPoolMapping(
            "lactate_extracellular",
            "blood_or_assay_medium",
            ("lac_blood",),
            (),
            "missing_exploratory_runtime_boundary_pool",
        ),
        CanonicalPoolMapping(
            "lactate_cytosol",
            "cytosol",
            ("lac",),
            ("lactate",),
            "one_to_one_name_bridge",
        ),
        CanonicalPoolMapping(
            "pyruvate_cytosol",
            "cytosol",
            ("pyr",),
            ("pyruvate",),
            "one_to_one_name_bridge",
        ),
        CanonicalPoolMapping(
            "pyruvate_mitochondrial",
            "mitochondrion",
            ("pyr_mito",),
            ("pyruvate",),
            "blocked_exploratory_runtime_collapses_compartments",
        ),
        CanonicalPoolMapping(
            "ATP_cytosol",
            "cytosol",
            ("atp",),
            ("ATP",),
            "one_to_one_name_bridge",
        ),
        CanonicalPoolMapping(
            "ATP_mitochondrial",
            "mitochondrion",
            ("atp_mito",),
            ("ATP",),
            "blocked_exploratory_runtime_collapses_compartments",
        ),
        CanonicalPoolMapping(
            "NADH_cytosol",
            "cytosol",
            ("nadh",),
            ("NADH",),
            "one_to_one_name_bridge",
        ),
        CanonicalPoolMapping(
            "NADH_mitochondrial",
            "mitochondrion",
            ("nadh_mito",),
            ("NADH",),
            "blocked_exploratory_runtime_collapses_compartments",
        ),
    )


def build_exact_glucose_homeostasis_contract() -> ExactGlucoseHomeostasisContract:
    manifest = inspect_sbml_document(OFFICIAL_MODEL_PATH)
    species = inspect_sbml_species_fingerprints(OFFICIAL_MODEL_PATH)
    fingerprints = inspect_sbml_reaction_fingerprints(OFFICIAL_MODEL_PATH)
    runtime = build_integrated_hepatocyte_network(HormoneState())
    runtime_species = set(runtime.species)
    runtime_reactions = {reaction.id for reaction in runtime.reactions}

    conflicts = (
        RuntimeStructuralConflict(
            id="split_cytosolic_glucose_pool",
            detected={"glucose", "glucose_cyto"} <= runtime_species,
            affected_species_ids=("glucose", "glucose_cyto"),
            affected_reaction_ids=(
                "glycogen_synthesis",
                "glycogen_breakdown",
                "glucose_6_phosphatase",
                "glucose_export",
                "hepatic_glucose_output",
            ),
            consequence=(
                "One cytosolic glucose pool is represented by two disconnected runtime species, "
                "so storage, production and export cannot share an exact mass balance."
            ),
        ),
        RuntimeStructuralConflict(
            id="duplicate_glucose_export_channels",
            detected={"glucose_export", "hepatic_glucose_output"} <= runtime_reactions,
            affected_species_ids=("glucose", "glucose_cyto", "glucose_blood"),
            affected_reaction_ids=("glucose_export", "hepatic_glucose_output"),
            consequence=(
                "Two non-equivalent exploratory reactions export glucose from different internal pools."
            ),
        ),
        RuntimeStructuralConflict(
            id="lumped_lower_gluconeogenesis",
            detected="lower_glycolysis_reverse" in runtime_reactions,
            affected_species_ids=(
                "phosphoenolpyruvate",
                "fructose_1_6_bisphosphate",
                "ATP",
                "ADP",
                "NADH",
                "NAD_plus",
            ),
            affected_reaction_ids=("lower_glycolysis_reverse",),
            consequence=(
                "A multi-step pathway is collapsed into one callable and is not equation-isomorphic "
                "to the source-resolved reaction sequence."
            ),
        ),
        RuntimeStructuralConflict(
            id="cytosol_mitochondrion_compartment_collapse",
            detected=("ATP" in runtime_species and "NADH" in runtime_species),
            affected_species_ids=("ATP", "ADP", "NADH", "NAD_plus", "pyruvate"),
            affected_reaction_ids=tuple(sorted(runtime_reactions)),
            consequence=(
                "The exploratory network uses one numerical volume for reactions that require "
                "separate cytosolic and mitochondrial pools."
            ),
        ),
    )
    detected = tuple(item for item in conflicts if item.detected)
    blockers = tuple(item.consequence for item in detected) + (
        "The official publication supplement establishes structure but contains zero kinetic laws.",
        "No reaction currently has a complete healthy-PHH equation, per-cell unit, context and held-out-validation transfer.",
    )
    reactions = tuple(
        SourceExactReaction(
            reaction_id=item.reaction_id,
            name=item.name,
            reversible=item.reversible,
            reactants=tuple(_term(term) for term in item.reactants),
            products=tuple(_term(term) for term in item.products),
            modifier_species_ids=item.modifier_species_ids,
            kinetic_law_present=item.kinetic_law_present,
            topology_source_id="koenig2012_plos_dataset_s2",
        )
        for item in fingerprints
    )
    state = ExactGlucoseHomeostasisContract(
        version=VERSION,
        status="source_exact_topology_ready_runtime_replacement_blocked",
        source_model_id=manifest.model_id,
        source_model_sha256=manifest.sha256,
        source_compartment_ids=manifest.compartment_ids,
        source_species_count=len(species),
        source_reaction_count=len(reactions),
        source_kinetic_law_count=len(manifest.reactions_with_kinetic_law),
        source_species=tuple(to_plain(item) for item in species),
        source_reactions=reactions,
        canonical_pools=_canonical_pools(),
        runtime_conflicts=conflicts,
        exact_source_topology_ready=True,
        canonical_pool_contract_ready=True,
        active_runtime_replacement_ready=False,
        numerical_execution_enabled=False,
        parameter_activation_allowed=False,
        predictive_ready=False,
        source_ids=(
            "koenig2012_hepatic_glucose_model",
            "koenig2012_plos_dataset_s2",
            "koenig2012_author_executable_reencoding",
            "koenig2012_text_s2_kinetic_parameters",
        ),
        blockers=blockers,
        policy=(
            "Source-exact topology and canonical naming may drive structural tests. Numerical "
            "execution remains disabled until every active reaction has a qualified equation, "
            "unit bridge, matched PHH context and independent validation."
        ),
    )
    validate_exact_glucose_homeostasis_contract(state)
    return state


def validate_exact_glucose_homeostasis_contract(
    state: ExactGlucoseHomeostasisContract,
) -> None:
    if state.version != VERSION or state.source_model_id != "Koenig2012":
        raise ValueError("exact glucose-homeostasis contract identity changed")
    if state.source_model_sha256 != OFFICIAL_MODEL_SHA256:
        raise ValueError("exact glucose-homeostasis source checksum changed")
    if (
        state.source_species_count != 52
        or state.source_reaction_count != 36
        or state.source_kinetic_law_count != 0
        or state.source_compartment_ids != ("cyto", "blood", "mito", "mm", "pm")
    ):
        raise ValueError("official glucose-model structural inventory changed")
    if len({item.reaction_id for item in state.source_reactions}) != 36:
        raise ValueError("source-exact reaction inventory is duplicated or incomplete")
    if any(item.kinetic_law_present for item in state.source_reactions):
        raise ValueError("official non-kinetic supplement was treated as executable")
    pools = {item.canonical_pool_id: item for item in state.canonical_pools}
    if set(pools) != {
        "glucose_extracellular",
        "glucose_cytosol",
        "glucose_6_phosphate_cytosol",
        "glycogen_glucosyl_residue_cytosol",
        "lactate_extracellular",
        "lactate_cytosol",
        "pyruvate_cytosol",
        "pyruvate_mitochondrial",
        "ATP_cytosol",
        "ATP_mitochondrial",
        "NADH_cytosol",
        "NADH_mitochondrial",
    }:
        raise ValueError("canonical glucose-homeostasis pool registry changed")
    if pools["glucose_cytosol"].exploratory_runtime_species_ids != ("glucose", "glucose_cyto"):
        raise ValueError("split exploratory cytosolic glucose pools were hidden")
    expected_conflicts = {
        "split_cytosolic_glucose_pool",
        "duplicate_glucose_export_channels",
        "lumped_lower_gluconeogenesis",
        "cytosol_mitochondrion_compartment_collapse",
    }
    if {item.id for item in state.runtime_conflicts if item.detected} != expected_conflicts:
        raise ValueError("exploratory runtime structural conflicts changed without review")
    if (
        not state.exact_source_topology_ready
        or not state.canonical_pool_contract_ready
        or state.active_runtime_replacement_ready
        or state.numerical_execution_enabled
        or state.parameter_activation_allowed
        or state.predictive_ready
    ):
        raise ValueError("exact structural contract exceeded its evidence authority")


def exact_glucose_homeostasis_snapshot() -> dict[str, object]:
    state = build_exact_glucose_homeostasis_contract()
    payload = state.to_dict()
    payload["summary"] = {
        "source_compartment_count": len(state.source_compartment_ids),
        "source_species_count": state.source_species_count,
        "source_reaction_count": state.source_reaction_count,
        "source_kinetic_law_count": state.source_kinetic_law_count,
        "canonical_pool_count": len(state.canonical_pools),
        "detected_runtime_conflict_count": sum(item.detected for item in state.runtime_conflicts),
        "activated_parameter_count": int(state.parameter_activation_allowed),
        "executable_reaction_count": 0,
    }
    return payload
