"""Reaction-level scientific authority and fail-closed execution gates.

A pathway citation can support topology without supporting the numerical rate
used by the runtime.  This module therefore audits reaction parameterization,
network context compatibility, and held-out validation as separate gates.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Literal

from cell_engine.stochastic.reactions import Reaction, ReactionNetwork


ReactionAuthority = Literal[
    "source_backed",
    "fitted",
    "placeholder",
    "unparameterized",
    "invalid",
]
ReactionAuthorityPurpose = Literal[
    "exploratory_execution",
    "quantitative_validation",
    "predictive_execution",
]


@dataclass(frozen=True)
class ReactionAuthorityRecord:
    reaction_id: str
    authority: ReactionAuthority
    topology_source_id: str
    parameter_count: int
    parameter_names: tuple[str, ...]
    assumption_levels: tuple[str, ...]
    parameter_source_ids: tuple[str, ...]
    parameter_provenance_complete: bool
    eligible_for_context_matched_quantitative_use: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class ReactionNetworkAuthorityAudit:
    network_id: str
    status: str
    runtime_role: Literal["exploratory", "quantitative", "predictive"]
    reaction_count: int
    authority_counts: dict[str, int]
    parameter_provenance_documented_count: int
    source_backed_parameterization_count: int
    parameter_provenance_coverage_fraction: float
    source_backed_fraction: float
    context_match_confirmed: bool
    context_description: str
    heldout_validation_confirmed: bool
    scientific_validation_ready: bool
    predictive_execution_ready: bool
    exploratory_execution_allowed: bool
    validation_blockers: tuple[str, ...]
    predictive_blockers: tuple[str, ...]
    blocked_reaction_ids: tuple[str, ...]
    reactions: tuple[ReactionAuthorityRecord, ...]
    policy: str


class ReactionAuthorityError(RuntimeError):
    """Raised when a caller requests a use that the authority audit forbids."""


_VALID_LEVELS = frozenset(("measured", "literature_derived", "fitted", "placeholder"))


def _invalid_parameter_fields(reaction: Reaction) -> tuple[str, ...]:
    invalid: list[str] = []
    for index, parameter in enumerate(reaction.parameter_provenance):
        prefix = f"parameter[{index}]"
        if not parameter.name.strip():
            invalid.append(f"{prefix} name is empty")
        if not parameter.unit.strip():
            invalid.append(f"{prefix} unit is empty")
        if not parameter.source_id.strip():
            invalid.append(f"{prefix} source_id is empty")
        if parameter.assumption_level not in _VALID_LEVELS:
            invalid.append(f"{prefix} assumption level is unsupported")
        if not isfinite(parameter.confidence) or not 0.0 <= parameter.confidence <= 1.0:
            invalid.append(f"{prefix} confidence must be finite and within [0, 1]")
        value = parameter.value
        if isinstance(value, (int, float)) and not isfinite(float(value)):
            invalid.append(f"{prefix} numeric value is not finite")
        if isinstance(value, str) and not value.strip():
            invalid.append(f"{prefix} string value is empty")
    return tuple(invalid)


def audit_reaction_authority(reaction: Reaction) -> ReactionAuthorityRecord:
    blockers: list[str] = []
    if not reaction.id.strip():
        blockers.append("reaction id is empty")
    if not reaction.source_id.strip():
        blockers.append("topology source_id is empty")

    invalid_parameters = _invalid_parameter_fields(reaction)
    blockers.extend(invalid_parameters)
    parameters = reaction.parameter_provenance
    levels = tuple(dict.fromkeys(parameter.assumption_level for parameter in parameters))

    if blockers:
        authority: ReactionAuthority = "invalid"
    elif not parameters:
        authority = "unparameterized"
        blockers.append("no numerical parameter provenance is registered")
    elif "placeholder" in levels:
        authority = "placeholder"
        blockers.append("at least one numerical parameter is a placeholder")
    elif "fitted" in levels:
        authority = "fitted"
        blockers.append("fitted parameters require a separate held-out validation context")
    elif all(level in ("measured", "literature_derived") for level in levels):
        authority = "source_backed"
    else:
        authority = "invalid"
        blockers.append("parameter authority could not be classified")

    return ReactionAuthorityRecord(
        reaction_id=reaction.id,
        authority=authority,
        topology_source_id=reaction.source_id,
        parameter_count=len(parameters),
        parameter_names=tuple(parameter.name for parameter in parameters),
        assumption_levels=levels,
        parameter_source_ids=tuple(
            dict.fromkeys(parameter.source_id for parameter in parameters if parameter.source_id)
        ),
        parameter_provenance_complete=authority in ("source_backed", "fitted", "placeholder"),
        eligible_for_context_matched_quantitative_use=authority == "source_backed",
        blockers=tuple(blockers),
    )


def audit_reaction_network(
    network: ReactionNetwork,
    *,
    network_id: str,
    context_match_confirmed: bool,
    context_description: str,
    heldout_validation_confirmed: bool = False,
) -> ReactionNetworkAuthorityAudit:
    if not network_id.strip():
        raise ValueError("network_id must be non-empty")
    if not context_description.strip():
        raise ValueError("context_description must be non-empty")
    if not network.reactions:
        raise ValueError("reaction authority requires at least one reaction")

    reaction_ids = tuple(reaction.id for reaction in network.reactions)
    if len(set(reaction_ids)) != len(reaction_ids):
        raise ValueError("reaction authority cannot audit duplicate reaction ids")

    records = tuple(audit_reaction_authority(reaction) for reaction in network.reactions)
    authority_counts = {
        authority: sum(record.authority == authority for record in records)
        for authority in (
            "source_backed",
            "fitted",
            "placeholder",
            "unparameterized",
            "invalid",
        )
    }
    reaction_count = len(records)
    documented_count = sum(record.parameter_count > 0 for record in records)
    source_backed_count = authority_counts["source_backed"]
    blocked_records = tuple(record for record in records if record.authority != "source_backed")

    validation_blockers: list[str] = []
    if blocked_records:
        validation_blockers.append(
            f"{len(blocked_records)} of {reaction_count} reactions lack source-backed numerical parameterization"
        )
    if not context_match_confirmed:
        validation_blockers.append("network biological and experimental context match is not confirmed")

    scientific_validation_ready = not validation_blockers
    predictive_blockers = list(validation_blockers)
    if not heldout_validation_confirmed:
        predictive_blockers.append("independent held-out validation is not confirmed")
    predictive_execution_ready = not predictive_blockers

    if predictive_execution_ready:
        status = "predictive_ready"
        runtime_role: Literal["exploratory", "quantitative", "predictive"] = "predictive"
    elif scientific_validation_ready:
        status = "context_matched_quantitative_ready"
        runtime_role = "quantitative"
    else:
        status = "mixed_authority_exploratory"
        runtime_role = "exploratory"

    return ReactionNetworkAuthorityAudit(
        network_id=network_id,
        status=status,
        runtime_role=runtime_role,
        reaction_count=reaction_count,
        authority_counts=authority_counts,
        parameter_provenance_documented_count=documented_count,
        source_backed_parameterization_count=source_backed_count,
        parameter_provenance_coverage_fraction=documented_count / reaction_count,
        source_backed_fraction=source_backed_count / reaction_count,
        context_match_confirmed=context_match_confirmed,
        context_description=context_description,
        heldout_validation_confirmed=heldout_validation_confirmed,
        scientific_validation_ready=scientific_validation_ready,
        predictive_execution_ready=predictive_execution_ready,
        exploratory_execution_allowed=True,
        validation_blockers=tuple(validation_blockers),
        predictive_blockers=tuple(dict.fromkeys(predictive_blockers)),
        blocked_reaction_ids=tuple(record.reaction_id for record in blocked_records),
        reactions=records,
        policy=(
            "A pathway or topology citation does not authorize its numerical rate. "
            "Quantitative validation requires source-backed parameter provenance for every "
            "reaction plus a confirmed biological/experimental context match. Predictive "
            "execution additionally requires independent held-out validation."
        ),
    )


def assert_reaction_network_authority(
    network: ReactionNetwork,
    *,
    network_id: str,
    purpose: ReactionAuthorityPurpose,
    context_match_confirmed: bool,
    context_description: str,
    heldout_validation_confirmed: bool = False,
) -> ReactionNetworkAuthorityAudit:
    audit = audit_reaction_network(
        network,
        network_id=network_id,
        context_match_confirmed=context_match_confirmed,
        context_description=context_description,
        heldout_validation_confirmed=heldout_validation_confirmed,
    )
    if purpose == "exploratory_execution":
        return audit
    if purpose == "quantitative_validation" and not audit.scientific_validation_ready:
        raise ReactionAuthorityError("; ".join(audit.validation_blockers))
    if purpose == "predictive_execution" and not audit.predictive_execution_ready:
        raise ReactionAuthorityError("; ".join(audit.predictive_blockers))
    return audit
