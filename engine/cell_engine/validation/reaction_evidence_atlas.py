"""Reaction Evidence Atlas for the active integrated hepatocyte network.

This inventory separates reaction topology from every quantity needed to turn a
reaction into a context-matched kinetic claim.  Missing quantities are explicit
``None`` values, and fluid/crowding coupling is disabled reaction by reaction.
"""

from __future__ import annotations

from dataclasses import dataclass

from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain
from cell_engine.stochastic.integrated_cell import build_integrated_hepatocyte_network
from cell_engine.stochastic.reactions import ReactionNetwork
from cell_engine.stochastic.signaling import HormoneState
from cell_engine.validation.kinetic_transfer import (
    KineticTransferAudit,
    build_kinetic_transfer_audit,
    validate_kinetic_transfer_audit,
)
from cell_engine.validation.reaction_authority import audit_reaction_authority


DATE_VERIFIED = "2026-07-21"
VERSION = "reaction_evidence_atlas_v1"

REACTION_EVIDENCE_SOURCES: dict[str, SourceReference] = {
    "sabio_rk_kinetics_database": SourceReference(
        id="sabio_rk_kinetics_database",
        title="SABIO-RK: an updated resource for manually curated biochemical reaction kinetics",
        url="https://doi.org/10.1093/nar/gkx1065",
        source_type="database",
        date_verified=DATE_VERIFIED,
        notes=(
            "Candidate source for rate laws and assay-qualified kinetic constants. "
            "Database presence does not establish healthy-PHH context transferability."
        ),
    ),
    "brenda_enzyme_database": SourceReference(
        id="brenda_enzyme_database",
        title="BRENDA enzyme information system",
        url="https://www.brenda-enzymes.org/",
        source_type="database",
        date_verified=DATE_VERIFIED,
        notes=(
            "Candidate source for organism-, tissue- and condition-indexed enzyme data. "
            "Purified-enzyme values remain assay-context observations."
        ),
    ),
    "hepatokin1_human_liver_model": SourceReference(
        id="hepatokin1_human_liver_model",
        title="Hepatocyte-specific model of glucose metabolism integrating proteomics",
        url="https://doi.org/10.1038/s41467-018-04720-9",
        source_type="primary_model",
        date_verified=DATE_VERIFIED,
        notes=(
            "Candidate published kinetic-model lineage. Model equations and fitted values "
            "must pass exact identity, units, compartment, context and validation gates."
        ),
    ),
    "davidi2016_in_vivo_catalytic_rates": SourceReference(
        id="davidi2016_in_vivo_catalytic_rates",
        title="Global characterization of in vivo enzyme catalytic rates and their correspondence to in vitro kcat measurements",
        url="https://doi.org/10.1073/pnas.1514240113",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Shows that in-vivo apparent catalytic rates and in-vitro kcat are distinct "
            "quantities; not a source of human-hepatocyte reaction parameters."
        ),
    ),
}


@dataclass(frozen=True)
class ReactionEvidenceSlot:
    id: str
    quantity: str
    unit: str
    value: None
    status: str
    required_context: str


@dataclass(frozen=True)
class ReactionTransportCouplingGate:
    diffusion_limitation_demonstrated: bool
    species_apparent_diffusivity_um2_s: None
    characteristic_length_um: None
    damkohler_number: None
    direct_fluid_rate_multiplier: None
    local_concentration_coupling_allowed: bool
    direct_rate_correction_allowed: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class ReactionEvidenceRecord:
    reaction_id: str
    reactants: dict[str, int]
    products: dict[str, int]
    runtime_topology_source_id: str
    runtime_rate_law_family: str
    runtime_parameter_authority: str
    runtime_parameter_count: int
    legacy_runtime_compartment: str
    legacy_runtime_compartment_is_biological_assignment: bool
    published_candidate_relationship: str
    published_candidate_reaction_ids: tuple[str, ...]
    evidence_slots: tuple[ReactionEvidenceSlot, ...]
    transport_coupling: ReactionTransportCouplingGate
    evidence_tier: str
    quantitative_execution_allowed: bool
    predictive_execution_allowed: bool
    blockers: tuple[str, ...]


_SLOT_SPECS: tuple[tuple[str, str, str, str], ...] = (
    ("biochemical_identity", "exact enzyme/reaction identity including isoform and direction", "identifier", "same biochemical event"),
    ("biological_compartment", "subcellular compartment and membrane side", "identifier", "healthy human hepatocyte"),
    ("symbolic_rate_law", "complete symbolic rate equation", "equation", "same substrates, products, effectors and direction"),
    ("km", "substrate-specific Michaelis or half-saturation constants", "M", "same isoform and assay conditions"),
    ("kcat", "enzyme turnover number", "1/s", "same isoform, temperature, pH and cofactors"),
    ("ki_or_allostery", "inhibition and allosteric constants", "context_specific", "same inhibitor/effector and assay conditions"),
    ("vmax", "maximum reaction capacity", "mol/(cell s)", "same healthy-PHH context and active enzyme state"),
    ("active_enzyme_abundance", "active localized enzyme abundance", "molecules/cell", "matched donor, compartment, PTM and complex state"),
    ("assay_temperature", "assay temperature", "degC", "reported by the kinetic source"),
    ("assay_ph", "assay pH", "pH", "reported by the kinetic source"),
    ("intracellular_flux", "reaction-resolved intracellular flux", "mol/(cell s)", "matched human hepatocyte isotope/flux experiment"),
    ("heldout_validation", "independent same-format held-out result", "validation_result", "donor-disjoint frozen-model evaluation"),
)


def _empty_slots() -> tuple[ReactionEvidenceSlot, ...]:
    return tuple(
        ReactionEvidenceSlot(
            id=id,
            quantity=quantity,
            unit=unit,
            value=None,
            status="missing_not_zero",
            required_context=context,
        )
        for id, quantity, unit, context in _SLOT_SPECS
    )


def _transport_gate() -> ReactionTransportCouplingGate:
    return ReactionTransportCouplingGate(
        diffusion_limitation_demonstrated=False,
        species_apparent_diffusivity_um2_s=None,
        characteristic_length_um=None,
        damkohler_number=None,
        direct_fluid_rate_multiplier=None,
        local_concentration_coupling_allowed=False,
        direct_rate_correction_allowed=False,
        blockers=(
            "reaction-specific diffusion limitation has not been demonstrated in healthy PHH",
            "reactant apparent diffusivity and hydrodynamic scale are not identified for the matched state",
            "no resolved concentration/velocity field is coupled to the active reaction network",
            "a global viscosity or crowding multiplier is scientifically prohibited",
        ),
    )


def build_reaction_evidence_atlas(
    network: ReactionNetwork | None = None,
    kinetic_transfer: KineticTransferAudit | None = None,
) -> dict[str, object]:
    active_network = network or build_integrated_hepatocyte_network(HormoneState())
    transfer = kinetic_transfer or build_kinetic_transfer_audit(active_network)
    validate_kinetic_transfer_audit(transfer)
    transfer_by_id = {item.active_reaction_id: item for item in transfer.reactions}

    records: list[ReactionEvidenceRecord] = []
    for reaction in active_network.reactions:
        authority = audit_reaction_authority(reaction)
        candidate = transfer_by_id[reaction.id]
        blockers = tuple(
            dict.fromkeys(
                (
                    *authority.blockers,
                    *candidate.blockers,
                    "reaction evidence slots are incomplete",
                    "matched healthy-PHH held-out validation is absent",
                )
            )
        )
        records.append(
            ReactionEvidenceRecord(
                reaction_id=reaction.id,
                reactants=dict(reaction.reactants),
                products=dict(reaction.products),
                runtime_topology_source_id=reaction.source_id,
                runtime_rate_law_family=reaction.rate_law_family,
                runtime_parameter_authority=authority.authority,
                runtime_parameter_count=authority.parameter_count,
                legacy_runtime_compartment="single_shared_cytosol_volume",
                legacy_runtime_compartment_is_biological_assignment=False,
                published_candidate_relationship=candidate.relationship,
                published_candidate_reaction_ids=candidate.candidate_reaction_ids,
                evidence_slots=_empty_slots(),
                transport_coupling=_transport_gate(),
                evidence_tier="E_missing_context_matched_kinetic_parameterization",
                quantitative_execution_allowed=False,
                predictive_execution_allowed=False,
                blockers=blockers,
            )
        )

    payload: dict[str, object] = {
        "version": VERSION,
        "status": "all_active_reactions_inventoried_quantitative_execution_blocked",
        "network_id": "integrated_hepatocyte_fuel_network_v1",
        "policy": (
            "Topology, enzyme abundance, in-vitro kinetics, intracellular state, flux and "
            "held-out validation are independent evidence layers. A reaction becomes "
            "quantitative only when every required layer matches the modeled biological and "
            "experimental context. Missing values remain null, never zero or an estimate."
        ),
        "evidence_tiers": {
            "A": "same-protocol donor-resolved healthy primary human hepatocyte evidence",
            "B": "human liver or purified human enzyme plus matched PHH abundance/state bridge",
            "C": "human cell line, non-human or unmatched experimental context",
            "D": "fitted, balanced or machine-learned exploratory parameter",
            "E": "missing or unidentifiable",
        },
        "candidate_search_sources": tuple(REACTION_EVIDENCE_SOURCES),
        "reactions": to_plain(tuple(records)),
        "source_ids": tuple(REACTION_EVIDENCE_SOURCES),
        "summary": {
            "active_reaction_count": len(records),
            "evidence_slot_count": sum(len(record.evidence_slots) for record in records),
            "filled_evidence_slot_count": 0,
            "source_backed_quantitative_reaction_count": 0,
            "transport_coupled_reaction_count": 0,
            "direct_fluid_rate_multiplier_count": 0,
            "quantitative_execution_allowed_count": 0,
            "predictive_execution_allowed_count": 0,
            "published_candidate_mapping_count": sum(
                bool(record.published_candidate_reaction_ids) for record in records
            ),
        },
        "limitations": (
            "The active network still executes only as an exploratory legacy surface.",
            "A single shared-cytosol runtime volume is not a biological compartment assignment for mitochondrial, ER or membrane reactions.",
            "The atlas does not infer enzyme isoforms or compartments from reaction names.",
        ),
    }
    validate_reaction_evidence_atlas(payload, active_network)
    return payload


def validate_reaction_evidence_atlas(
    payload: dict[str, object],
    network: ReactionNetwork | None = None,
) -> None:
    active_network = network or build_integrated_hepatocyte_network(HormoneState())
    if payload.get("version") != VERSION:
        raise ValueError("unsupported reaction evidence atlas version")
    records = payload.get("reactions")
    if not isinstance(records, list) or len(records) != len(active_network.reactions):
        raise ValueError("reaction evidence atlas must cover the active network exactly")
    expected_ids = {reaction.id for reaction in active_network.reactions}
    actual_ids = {record.get("reaction_id") for record in records if isinstance(record, dict)}
    if actual_ids != expected_ids or len(actual_ids) != len(records):
        raise ValueError("reaction evidence atlas ids do not match the active network")
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("reaction evidence record is malformed")
        slots = record.get("evidence_slots")
        transport = record.get("transport_coupling")
        if not isinstance(slots, list) or len(slots) != len(_SLOT_SPECS):
            raise ValueError(f"{record.get('reaction_id')} evidence slots are incomplete")
        if any(slot.get("value") is not None for slot in slots if isinstance(slot, dict)):
            raise ValueError(f"{record.get('reaction_id')} acquired an unaudited evidence value")
        if not isinstance(transport, dict):
            raise ValueError(f"{record.get('reaction_id')} transport gate is missing")
        if (
            transport.get("direct_fluid_rate_multiplier") is not None
            or transport.get("local_concentration_coupling_allowed") is not False
            or transport.get("direct_rate_correction_allowed") is not False
            or record.get("quantitative_execution_allowed") is not False
            or record.get("predictive_execution_allowed") is not False
        ):
            raise ValueError(f"{record.get('reaction_id')} bypassed a quantitative gate")
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        raise ValueError("reaction evidence summary is missing")
    if (
        summary.get("active_reaction_count") != 36
        or summary.get("filled_evidence_slot_count") != 0
        or summary.get("transport_coupled_reaction_count") != 0
        or summary.get("direct_fluid_rate_multiplier_count") != 0
        or summary.get("quantitative_execution_allowed_count") != 0
        or summary.get("predictive_execution_allowed_count") != 0
    ):
        raise ValueError("reaction evidence summary exceeded current authority")
