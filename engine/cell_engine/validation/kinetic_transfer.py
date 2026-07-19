"""Fail-closed transfer audit from a published model into the active network.

Published kinetic constants are not portable merely because two reactions have
similar names. Transfer requires matching stoichiometry, compartments, symbolic
rate law, units/scale, biological context and validation. This module makes each
gate explicit for every reaction in the integrated hepatocyte fuel network.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Literal

from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain
from cell_engine.io.sbml import (
    SbmlReactionFingerprint,
    SbmlReactionParticipant,
    inspect_sbml_document,
    inspect_sbml_reaction_fingerprints,
)
from cell_engine.quantitative.published_glucose_model import (
    EXECUTABLE_MODEL_PATH,
    EXECUTABLE_MODEL_SHA256,
)
from cell_engine.stochastic.integrated_cell import build_integrated_hepatocyte_network
from cell_engine.stochastic.reactions import Reaction, ReactionNetwork
from cell_engine.stochastic.signaling import HormoneState
from cell_engine.validation.reaction_authority import audit_reaction_authority


DATE_VERIFIED = "2026-07-19"
VERSION = "published_reaction_kinetic_transfer_audit_v1"
SCHEMA_VERSION = "koenig2012.reaction-transfer.v1"

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
TRANSFER_MANIFEST_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "published_models"
    / "koenig2012_reaction_transfer_manifest.json"
)

TransferRelationship = Literal[
    "single_reaction_candidate",
    "multi_reaction_lump",
    "outside_source_scope",
    "current_source_backed_outside_source_scope",
]

KINETIC_TRANSFER_SOURCES: dict[str, SourceReference] = {
    "koenig2012_text_s2_kinetic_parameters": SourceReference(
        id="koenig2012_text_s2_kinetic_parameters",
        title="Koenig et al. 2012 Text S2: kinetic equations and parameters",
        url="https://doi.org/10.1371/journal.pcbi.1002577.s013",
        source_type="primary_supplement",
        date_verified=DATE_VERIFIED,
        notes=(
            "Official supporting text containing kinetic equations, literature parameter "
            "references and fitted model Vmax values. Values are model-context parameters, "
            "not direct single-PHH rate constants."
        ),
    ),
}


@dataclass(frozen=True)
class CandidateReactionAudit:
    model_reaction_id: str
    name: str | None
    compartment_id: str | None
    reversible: bool
    exact_stoichiometry: bool
    matching_orientation: Literal["forward", "reverse"] | None
    kinetic_math_sha256: str | None
    kinetic_parameter_ids: tuple[str, ...]
    kinetic_species_ids: tuple[str, ...]
    boundary_species_ids: tuple[str, ...]


@dataclass(frozen=True)
class ReactionKineticTransferAudit:
    active_reaction_id: str
    current_authority: str
    current_rate_law_family: str
    relationship: TransferRelationship
    candidate_reaction_ids: tuple[str, ...]
    candidates: tuple[CandidateReactionAudit, ...]
    species_aliases: dict[str, str]
    exact_stoichiometry_match: bool
    source_compartment_matches_runtime_volume: bool
    exact_symbolic_rate_law_match: bool
    per_cell_unit_bridge_ready: bool
    biological_context_match: bool
    heldout_validation_confirmed: bool
    parameter_activation_allowed: bool
    status: str
    blockers: tuple[str, ...]
    note: str


@dataclass(frozen=True)
class KineticTransferAudit:
    version: str
    status: str
    source_model: dict[str, object]
    target_network: dict[str, object]
    policy: dict[str, object]
    source_model_reaction_count: int
    source_model_kinetic_law_count: int
    active_reaction_count: int
    mapped_candidate_count: int
    outside_source_scope_count: int
    exact_stoichiometry_match_count: int
    exact_symbolic_rate_law_match_count: int
    per_cell_unit_bridge_ready_count: int
    biological_context_match_count: int
    activated_transfer_count: int
    relationship_counts: dict[str, int]
    mapped_active_reaction_ids: tuple[str, ...]
    exact_stoichiometry_reaction_ids: tuple[str, ...]
    activated_reaction_ids: tuple[str, ...]
    reactions: tuple[ReactionKineticTransferAudit, ...]
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


class KineticTransferError(RuntimeError):
    """Raised when an unqualified published parameter transfer is requested."""


def _load_manifest(path: Path = TRANSFER_MANIFEST_PATH) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("kinetic-transfer manifest schema is not supported")
    return data


def _stoichiometry(
    items: tuple[SbmlReactionParticipant, ...],
) -> dict[str, float]:
    side: dict[str, float] = {}
    for item in items:
        side[item.species_id] = side.get(item.species_id, 0.0) + float(item.stoichiometry)
    return side


def _aliased_stoichiometry(
    side: dict[str, int],
    aliases: dict[str, str],
) -> dict[str, float]:
    aliased: dict[str, float] = {}
    for species, stoich in side.items():
        target = aliases.get(species, species)
        aliased[target] = aliased.get(target, 0.0) + float(stoich)
    return aliased


def _matching_orientation(
    reaction: Reaction,
    candidate: SbmlReactionFingerprint,
    aliases: dict[str, str],
) -> Literal["forward", "reverse"] | None:
    active_reactants = _aliased_stoichiometry(reaction.reactants, aliases)
    active_products = _aliased_stoichiometry(reaction.products, aliases)
    source_reactants = _stoichiometry(candidate.reactants)
    source_products = _stoichiometry(candidate.products)
    if active_reactants == source_reactants and active_products == source_products:
        return "forward"
    if (
        candidate.reversible
        and active_reactants == source_products
        and active_products == source_reactants
    ):
        return "reverse"
    return None


def _candidate_audit(
    reaction: Reaction,
    candidate: SbmlReactionFingerprint,
    aliases: dict[str, str],
) -> CandidateReactionAudit:
    orientation = _matching_orientation(reaction, candidate, aliases)
    return CandidateReactionAudit(
        model_reaction_id=candidate.reaction_id,
        name=candidate.name,
        compartment_id=candidate.compartment_id,
        reversible=candidate.reversible,
        exact_stoichiometry=orientation is not None,
        matching_orientation=orientation,
        kinetic_math_sha256=candidate.kinetic_math_sha256,
        kinetic_parameter_ids=candidate.kinetic_parameter_ids,
        kinetic_species_ids=candidate.kinetic_species_ids,
        boundary_species_ids=candidate.boundary_species_ids,
    )


def _status(
    relationship: TransferRelationship,
    exact_stoichiometry: bool,
) -> str:
    if relationship == "current_source_backed_outside_source_scope":
        return "not_applicable_current_parameterization_retained"
    if relationship == "outside_source_scope":
        return "blocked_outside_source_scope"
    if relationship == "multi_reaction_lump":
        return "blocked_lumped_reaction"
    if not exact_stoichiometry:
        return "blocked_stoichiometry_mismatch"
    return "blocked_after_topology_match"


def _blockers(
    *,
    relationship: TransferRelationship,
    candidates: tuple[CandidateReactionAudit, ...],
    compartment_match: bool,
) -> tuple[str, ...]:
    if relationship == "current_source_backed_outside_source_scope":
        return ("published-model transfer is not applicable to this separately sourced channel",)
    if relationship == "outside_source_scope":
        return ("no reaction candidate exists in the published glucose-model scope",)
    blockers: list[str] = []
    if relationship == "multi_reaction_lump":
        blockers.append("one active event collapses multiple published reactions and intermediate pools")
    elif not any(candidate.exact_stoichiometry for candidate in candidates):
        blockers.append("reactants/products and stoichiometric coefficients are not identical")
    if not compartment_match:
        blockers.append("source compartment semantics do not match the active shared-cytosol runtime")
    blockers.extend(
        (
            "the active callable has no symbolic equation fingerprint matching the published MathML",
            "published per-kilogram flux scale has no validated per-hepatocyte unit bridge",
            "published mean-liver model context is not a matched healthy-PHH experiment",
            "independent held-out validation of the transferred reaction is absent",
        )
    )
    return tuple(blockers)


def build_kinetic_transfer_audit(
    network: ReactionNetwork | None = None,
) -> KineticTransferAudit:
    manifest = _load_manifest()
    source_model = manifest.get("source_model")
    target_network = manifest.get("target_network")
    policy = manifest.get("policy")
    raw_mappings = manifest.get("mappings")
    if not isinstance(source_model, dict) or not isinstance(target_network, dict):
        raise ValueError("kinetic-transfer manifest is missing model metadata")
    if not isinstance(policy, dict) or not isinstance(raw_mappings, list):
        raise ValueError("kinetic-transfer manifest is missing policy or mappings")
    if source_model.get("sha256") != EXECUTABLE_MODEL_SHA256:
        raise ValueError("kinetic-transfer manifest source checksum is stale")

    source_document = inspect_sbml_document(EXECUTABLE_MODEL_PATH)
    if source_document.sha256 != EXECUTABLE_MODEL_SHA256:
        raise ValueError("vendored executable glucose-model checksum mismatch")
    source_fingerprints = {
        item.reaction_id: item
        for item in inspect_sbml_reaction_fingerprints(EXECUTABLE_MODEL_PATH)
    }
    active_network = network or build_integrated_hepatocyte_network(HormoneState())
    active_reactions = {reaction.id: reaction for reaction in active_network.reactions}
    mapping_by_id: dict[str, dict[str, object]] = {}
    for raw in raw_mappings:
        if not isinstance(raw, dict) or not isinstance(raw.get("active_reaction_id"), str):
            raise ValueError("kinetic-transfer mapping is malformed")
        active_reaction_id = raw["active_reaction_id"]
        if active_reaction_id in mapping_by_id:
            raise ValueError(f"duplicate kinetic-transfer mapping for {active_reaction_id}")
        mapping_by_id[active_reaction_id] = raw
    if set(mapping_by_id) != set(active_reactions):
        missing = sorted(set(active_reactions) - set(mapping_by_id))
        unexpected = sorted(set(mapping_by_id) - set(active_reactions))
        raise ValueError(
            f"kinetic-transfer mapping must cover the active network exactly; "
            f"missing={missing}, unexpected={unexpected}"
        )

    records: list[ReactionKineticTransferAudit] = []
    for reaction in active_network.reactions:
        raw = mapping_by_id[reaction.id]
        relationship = raw.get("relationship")
        if relationship not in (
            "single_reaction_candidate",
            "multi_reaction_lump",
            "outside_source_scope",
            "current_source_backed_outside_source_scope",
        ):
            raise ValueError(f"unsupported kinetic-transfer relationship for {reaction.id}")
        candidate_ids_raw = raw.get("candidate_reaction_ids")
        aliases_raw = raw.get("species_aliases")
        note = raw.get("note")
        if not isinstance(candidate_ids_raw, list) or not all(
            isinstance(item, str) for item in candidate_ids_raw
        ):
            raise ValueError(f"candidate ids are malformed for {reaction.id}")
        if not isinstance(aliases_raw, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in aliases_raw.items()
        ):
            raise ValueError(f"species aliases are malformed for {reaction.id}")
        if not isinstance(note, str) or not note.strip():
            raise ValueError(f"kinetic-transfer note is missing for {reaction.id}")
        candidate_ids = tuple(candidate_ids_raw)
        aliases = dict(aliases_raw)
        if relationship in ("single_reaction_candidate", "multi_reaction_lump") and not candidate_ids:
            raise ValueError(f"candidate relationship has no candidate for {reaction.id}")
        if relationship in (
            "outside_source_scope",
            "current_source_backed_outside_source_scope",
        ) and candidate_ids:
            raise ValueError(f"outside-scope relationship has candidates for {reaction.id}")
        unknown_candidates = tuple(
            candidate_id for candidate_id in candidate_ids if candidate_id not in source_fingerprints
        )
        if unknown_candidates:
            raise ValueError(
                f"unknown published candidate(s) for {reaction.id}: {unknown_candidates}"
            )
        current_species = set(reaction.reactants) | set(reaction.products)
        if not set(aliases).issubset(current_species):
            raise ValueError(f"species aliases reference nonparticipants for {reaction.id}")
        if candidate_ids and not set(aliases.values()).issubset(source_document.species_ids):
            raise ValueError(f"species aliases reference unknown source species for {reaction.id}")
        candidate_records = tuple(
            _candidate_audit(reaction, source_fingerprints[candidate_id], aliases)
            for candidate_id in candidate_ids
        )
        exact_stoichiometry = (
            relationship == "single_reaction_candidate"
            and any(candidate.exact_stoichiometry for candidate in candidate_records)
        )
        compartment_match = bool(candidate_records) and all(
            candidate.compartment_id == "cyto" for candidate in candidate_records
        )
        authority = audit_reaction_authority(reaction)
        blockers = _blockers(
            relationship=relationship,
            candidates=candidate_records,
            compartment_match=compartment_match,
        )
        records.append(
            ReactionKineticTransferAudit(
                active_reaction_id=reaction.id,
                current_authority=authority.authority,
                current_rate_law_family=reaction.rate_law_family,
                relationship=relationship,
                candidate_reaction_ids=candidate_ids,
                candidates=candidate_records,
                species_aliases=aliases,
                exact_stoichiometry_match=exact_stoichiometry,
                source_compartment_matches_runtime_volume=compartment_match,
                exact_symbolic_rate_law_match=False,
                per_cell_unit_bridge_ready=False,
                biological_context_match=False,
                heldout_validation_confirmed=False,
                parameter_activation_allowed=False,
                status=_status(relationship, exact_stoichiometry),
                blockers=blockers,
                note=note,
            )
        )

    relationships = (
        "single_reaction_candidate",
        "multi_reaction_lump",
        "outside_source_scope",
        "current_source_backed_outside_source_scope",
    )
    relationship_counts = {
        relationship: sum(record.relationship == relationship for record in records)
        for relationship in relationships
    }
    mapped = tuple(record for record in records if record.candidate_reaction_ids)
    exact = tuple(record for record in records if record.exact_stoichiometry_match)
    activated = tuple(record for record in records if record.parameter_activation_allowed)
    source_ids_raw = source_model.get("source_ids")
    if not isinstance(source_ids_raw, list) or not all(
        isinstance(source_id, str) for source_id in source_ids_raw
    ):
        raise ValueError("kinetic-transfer source ids are malformed")
    return KineticTransferAudit(
        version=VERSION,
        status="blocked_no_equation_level_transfer",
        source_model=dict(source_model),
        target_network=dict(target_network),
        policy=dict(policy),
        source_model_reaction_count=len(source_document.reaction_ids),
        source_model_kinetic_law_count=len(source_document.reactions_with_kinetic_law),
        active_reaction_count=len(records),
        mapped_candidate_count=len(mapped),
        outside_source_scope_count=sum(
            record.relationship in (
                "outside_source_scope",
                "current_source_backed_outside_source_scope",
            )
            for record in records
        ),
        exact_stoichiometry_match_count=len(exact),
        exact_symbolic_rate_law_match_count=sum(
            record.exact_symbolic_rate_law_match for record in records
        ),
        per_cell_unit_bridge_ready_count=sum(
            record.per_cell_unit_bridge_ready for record in records
        ),
        biological_context_match_count=sum(
            record.biological_context_match for record in records
        ),
        activated_transfer_count=len(activated),
        relationship_counts=relationship_counts,
        mapped_active_reaction_ids=tuple(record.active_reaction_id for record in mapped),
        exact_stoichiometry_reaction_ids=tuple(
            record.active_reaction_id for record in exact
        ),
        activated_reaction_ids=tuple(
            record.active_reaction_id for record in activated
        ),
        reactions=tuple(records),
        source_ids=tuple(source_ids_raw),
        limitations=(
            "The published model is a mean human-liver glucose model, not a donor-, zone- or single-cell-resolved PHH experiment.",
            "Published Vmax values are fitted model quantities on a per-kilogram scale and are not direct per-cell measurements.",
            "Three active channels share exact stoichiometry with a published reversible reaction after aliases, but none shares the full symbolic rate law, unit scale and context.",
            "No published parameter is activated in the integrated network by this audit.",
        ),
    )


def validate_kinetic_transfer_audit(audit: KineticTransferAudit) -> None:
    if audit.source_model_reaction_count != 36 or audit.source_model_kinetic_law_count != 36:
        raise ValueError("published source model must retain 36 equation-bearing reactions")
    if audit.active_reaction_count != 36 or len(audit.reactions) != 36:
        raise ValueError("kinetic-transfer audit must cover all 36 active reactions")
    if len({record.active_reaction_id for record in audit.reactions}) != 36:
        raise ValueError("kinetic-transfer audit contains duplicate active reactions")
    if audit.mapped_candidate_count != 12:
        raise ValueError("kinetic-transfer candidate coverage changed without manifest review")
    if audit.exact_stoichiometry_match_count != 3:
        raise ValueError("kinetic-transfer exact-stoichiometry count changed without review")
    if set(audit.exact_stoichiometry_reaction_ids) != {
        "glucose_export",
        "phosphoglucose_isomerase_reverse",
        "hepatic_glucose_output",
    }:
        raise ValueError("unexpected exact-stoichiometry transfer candidates")
    if (
        audit.exact_symbolic_rate_law_match_count
        or audit.per_cell_unit_bridge_ready_count
        or audit.biological_context_match_count
        or audit.activated_transfer_count
        or audit.activated_reaction_ids
    ):
        raise ValueError("an unqualified published kinetic parameter transfer was activated")
    if any(record.parameter_activation_allowed for record in audit.reactions):
        raise ValueError("reaction-level transfer gate disagrees with the audit summary")


def assert_kinetic_transfer_allowed(
    reaction_id: str,
    audit: KineticTransferAudit | None = None,
) -> ReactionKineticTransferAudit:
    checked = audit or build_kinetic_transfer_audit()
    validate_kinetic_transfer_audit(checked)
    record = next(
        (item for item in checked.reactions if item.active_reaction_id == reaction_id),
        None,
    )
    if record is None:
        raise KeyError(reaction_id)
    if not record.parameter_activation_allowed:
        raise KineticTransferError(
            f"{reaction_id}: " + "; ".join(record.blockers)
        )
    return record


def kinetic_transfer_snapshot() -> dict[str, object]:
    audit = build_kinetic_transfer_audit()
    validate_kinetic_transfer_audit(audit)
    return audit.to_dict()
