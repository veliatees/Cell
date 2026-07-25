"""Context-matched PHH injury observations without a generalized fate law."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from math import isfinite
from pathlib import Path
from typing import Any

from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain
from cell_engine.core.injury_authority import injury_runtime_authority_snapshot
from cell_engine.quantitative.phh_injury_trajectory import (
    load_phh_injury_trajectory_contract,
    phh_injury_trajectory_intake_snapshot,
)


DATE_VERIFIED = "2026-07-22"
VERSION = "phh_injury_validation_v1"
SCHEMA_VERSION = "cell.phh-injury-validation.v1"
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "phh_baseline"
    / "curated"
    / "phh_injury_validation.v1.json"
)
OBSERVATION_OPERATOR_VERSION = "exact_phh_injury_observation_operator_v1"

PHH_INJURY_VALIDATION_SOURCES: dict[str, SourceReference] = {
    "xie2014_apap_phh": SourceReference(
        id="xie2014_apap_phh",
        title="Mechanisms of acetaminophen-induced cell death in primary human hepatocytes",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC4171351/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Freshly isolated PHH APAP time course and delayed NAC rescue protocol.",
    ),
    "woolbright2015_bile_acid_phh": SourceReference(
        id="woolbright2015_bile_acid_phh",
        title="Bile acid-induced necrosis in primary human hepatocytes and in patients with obstructive cholestasis",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC4361327/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Primary-human-hepatocyte comparison of serum and local biliary bile-acid exposures.",
    ),
}


@dataclass(frozen=True)
class PhhInjuryProtocol:
    id: str
    species: str
    biological_system: str
    challenge: str
    challenge_low: float
    challenge_high: float | None
    challenge_unit: str
    maximum_exposure_h: float
    temperature_c: float
    source_id: str
    source_locator: str
    may_initialize_healthy_baseline: bool
    may_define_general_fate_law: bool
    may_drive_cell_state: bool


@dataclass(frozen=True)
class PhhInjuryObservation:
    id: str
    protocol_id: str
    endpoint: str
    assay: str
    condition: str
    time_low_h: float
    time_high_h: float
    result: str
    death_mode: str | None
    donor_count_low: int
    donor_count_high: int
    source_id: str
    source_locator: str
    may_validate_matching_protocol: bool
    may_generalize: bool
    may_drive_cell_state: bool


@dataclass(frozen=True)
class PhhInjuryValidationState:
    version: str
    status: str
    date_verified: str
    policy: str
    protocols: tuple[PhhInjuryProtocol, ...]
    observations: tuple[PhhInjuryObservation, ...]
    integration_gates: dict[str, bool]
    source_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


@dataclass(frozen=True)
class PhhInjuryProtocolQuery:
    species: str
    biological_system: str
    challenge: str
    challenge_low: float
    challenge_high: float | None
    challenge_unit: str
    maximum_exposure_h: float
    temperature_c: float


@dataclass(frozen=True)
class PhhInjuryObservationMatch:
    status: str
    exact_protocol_match: bool
    protocol_id: str | None
    at_time_h: float | None
    endpoint: str | None
    condition: str | None
    mismatch_dimensions: tuple[str, ...]
    observations: tuple[PhhInjuryObservation, ...]
    unit_conversion_performed: bool
    interpolation_performed: bool
    state_mutation_allowed: bool
    unknown_is_negative_result: bool
    reason: str

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("PHH injury evidence must be one JSON object")
    return payload


def _protocol(raw: object) -> PhhInjuryProtocol:
    if not isinstance(raw, dict):
        raise ValueError("PHH injury protocol is malformed")
    return PhhInjuryProtocol(
        id=str(raw["id"]),
        species=str(raw["species"]),
        biological_system=str(raw["biological_system"]),
        challenge=str(raw["challenge"]),
        challenge_low=float(raw["challenge_low"]),
        challenge_high=(
            None if raw.get("challenge_high") is None else float(raw["challenge_high"])
        ),
        challenge_unit=str(raw["challenge_unit"]),
        maximum_exposure_h=float(raw["maximum_exposure_h"]),
        temperature_c=float(raw["temperature_c"]),
        source_id=str(raw["source_id"]),
        source_locator=str(raw["source_locator"]),
        may_initialize_healthy_baseline=bool(raw["may_initialize_healthy_baseline"]),
        may_define_general_fate_law=bool(raw["may_define_general_fate_law"]),
        may_drive_cell_state=bool(raw["may_drive_cell_state"]),
    )


def _observation(raw: object) -> PhhInjuryObservation:
    if not isinstance(raw, dict):
        raise ValueError("PHH injury observation is malformed")
    return PhhInjuryObservation(
        id=str(raw["id"]),
        protocol_id=str(raw["protocol_id"]),
        endpoint=str(raw["endpoint"]),
        assay=str(raw["assay"]),
        condition=str(raw["condition"]),
        time_low_h=float(raw["time_low_h"]),
        time_high_h=float(raw["time_high_h"]),
        result=str(raw["result"]),
        death_mode=None if raw.get("death_mode") is None else str(raw["death_mode"]),
        donor_count_low=int(raw["donor_count_low"]),
        donor_count_high=int(raw["donor_count_high"]),
        source_id=str(raw["source_id"]),
        source_locator=str(raw["source_locator"]),
        may_validate_matching_protocol=bool(raw["may_validate_matching_protocol"]),
        may_generalize=bool(raw["may_generalize"]),
        may_drive_cell_state=bool(raw["may_drive_cell_state"]),
    )


def build_phh_injury_validation(
    data_path: Path = DATA_PATH,
) -> PhhInjuryValidationState:
    payload = _load_json(data_path)
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported PHH injury-validation schema")
    protocols_raw = payload.get("protocols")
    observations_raw = payload.get("observations")
    gates = payload.get("integration_gates")
    sources = payload.get("source_artifacts")
    if not isinstance(protocols_raw, list) or not isinstance(observations_raw, list):
        raise ValueError("PHH injury evidence arrays are malformed")
    if not isinstance(gates, dict) or not isinstance(sources, list):
        raise ValueError("PHH injury evidence metadata is malformed")
    state = PhhInjuryValidationState(
        version=str(payload["version"]),
        status=str(payload["status"]),
        date_verified=str(payload["date_verified"]),
        policy=str(payload["policy"]),
        protocols=tuple(_protocol(item) for item in protocols_raw),
        observations=tuple(_observation(item) for item in observations_raw),
        integration_gates={str(key): bool(value) for key, value in gates.items()},
        source_ids=tuple(str(item["source_id"]) for item in sources if isinstance(item, dict)),
    )
    validate_phh_injury_validation(state)
    return state


_PROTOCOL_MATCH_DIMENSIONS = (
    "species",
    "biological_system",
    "challenge",
    "challenge_low",
    "challenge_high",
    "challenge_unit",
    "maximum_exposure_h",
    "temperature_c",
)


def protocol_query_from_protocol(
    protocol: PhhInjuryProtocol,
) -> PhhInjuryProtocolQuery:
    return PhhInjuryProtocolQuery(
        species=protocol.species,
        biological_system=protocol.biological_system,
        challenge=protocol.challenge,
        challenge_low=protocol.challenge_low,
        challenge_high=protocol.challenge_high,
        challenge_unit=protocol.challenge_unit,
        maximum_exposure_h=protocol.maximum_exposure_h,
        temperature_c=protocol.temperature_c,
    )


def _validate_protocol_query(query: PhhInjuryProtocolQuery) -> None:
    if not query.species or not query.biological_system or not query.challenge:
        raise ValueError("PHH injury protocol query labels must be non-empty")
    if not query.challenge_unit:
        raise ValueError("PHH injury protocol query unit must be non-empty")
    values = (
        query.challenge_low,
        query.maximum_exposure_h,
        query.temperature_c,
    )
    if any(not isfinite(value) for value in values):
        raise ValueError("PHH injury protocol query values must be finite")
    if query.challenge_low < 0.0 or query.maximum_exposure_h < 0.0:
        raise ValueError("PHH injury protocol query dose and duration must be non-negative")
    if query.challenge_high is not None and (
        not isfinite(query.challenge_high)
        or query.challenge_high < query.challenge_low
    ):
        raise ValueError("PHH injury protocol query has invalid challenge bounds")


def _protocol_mismatches(
    query: PhhInjuryProtocolQuery,
    protocol: PhhInjuryProtocol,
) -> tuple[str, ...]:
    return tuple(
        dimension
        for dimension in _PROTOCOL_MATCH_DIMENSIONS
        if getattr(query, dimension) != getattr(protocol, dimension)
    )


def evaluate_phh_injury_observations(
    query: PhhInjuryProtocolQuery,
    *,
    at_time_h: float | None = None,
    endpoint: str | None = None,
    condition: str | None = None,
    state: PhhInjuryValidationState | None = None,
) -> PhhInjuryObservationMatch:
    """Return only source observations from one exactly matching PHH protocol."""

    _validate_protocol_query(query)
    if at_time_h is not None and (not isfinite(at_time_h) or at_time_h < 0.0):
        raise ValueError("PHH injury observation time must be finite and non-negative")
    if endpoint is not None and not endpoint:
        raise ValueError("PHH injury endpoint filter must be non-empty")
    if condition is not None and not condition:
        raise ValueError("PHH injury condition filter must be non-empty")

    evidence = state or build_phh_injury_validation()
    comparisons = tuple(
        (protocol, _protocol_mismatches(query, protocol))
        for protocol in evidence.protocols
    )
    exact = tuple(protocol for protocol, mismatches in comparisons if not mismatches)
    if not exact:
        nearest_protocol, nearest_mismatches = min(
            comparisons,
            key=lambda item: (len(item[1]), item[0].id),
        )
        return PhhInjuryObservationMatch(
            status="context_mismatch",
            exact_protocol_match=False,
            protocol_id=None,
            at_time_h=at_time_h,
            endpoint=endpoint,
            condition=condition,
            mismatch_dimensions=nearest_mismatches,
            observations=(),
            unit_conversion_performed=False,
            interpolation_performed=False,
            state_mutation_allowed=False,
            unknown_is_negative_result=False,
            reason=(
                "No curated protocol matches every required dimension. The nearest "
                f"protocol is {nearest_protocol.id}, but approximate matching is prohibited."
            ),
        )
    if len(exact) != 1:
        raise ValueError("PHH injury evidence contains duplicate exact protocols")
    protocol = exact[0]
    if at_time_h is not None and at_time_h > protocol.maximum_exposure_h:
        return PhhInjuryObservationMatch(
            status="outside_protocol_window",
            exact_protocol_match=True,
            protocol_id=protocol.id,
            at_time_h=at_time_h,
            endpoint=endpoint,
            condition=condition,
            mismatch_dimensions=(),
            observations=(),
            unit_conversion_performed=False,
            interpolation_performed=False,
            state_mutation_allowed=False,
            unknown_is_negative_result=False,
            reason="The requested time is beyond the curated protocol exposure window.",
        )

    candidates = tuple(
        observation
        for observation in evidence.observations
        if observation.protocol_id == protocol.id
    )
    if endpoint is not None:
        candidates = tuple(
            observation for observation in candidates if observation.endpoint == endpoint
        )
        if not candidates:
            return PhhInjuryObservationMatch(
                status="unobserved_endpoint",
                exact_protocol_match=True,
                protocol_id=protocol.id,
                at_time_h=at_time_h,
                endpoint=endpoint,
                condition=condition,
                mismatch_dimensions=("endpoint",),
                observations=(),
                unit_conversion_performed=False,
                interpolation_performed=False,
                state_mutation_allowed=False,
                unknown_is_negative_result=False,
                reason=(
                    "The exact protocol is curated, but this endpoint was not observed. "
                    "Missing evidence does not mean no biological effect."
                ),
            )
    if condition is not None:
        candidates = tuple(
            observation
            for observation in candidates
            if observation.condition == condition
        )
        if not candidates:
            return PhhInjuryObservationMatch(
                status="unobserved_condition",
                exact_protocol_match=True,
                protocol_id=protocol.id,
                at_time_h=at_time_h,
                endpoint=endpoint,
                condition=condition,
                mismatch_dimensions=("condition",),
                observations=(),
                unit_conversion_performed=False,
                interpolation_performed=False,
                state_mutation_allowed=False,
                unknown_is_negative_result=False,
                reason=(
                    "The exact protocol is curated, but this intervention or condition "
                    "was not observed in the retained evidence."
                ),
            )
    if at_time_h is not None:
        candidates = tuple(
            observation
            for observation in candidates
            if observation.time_low_h <= at_time_h <= observation.time_high_h
        )
        if not candidates:
            return PhhInjuryObservationMatch(
                status="unobserved_time_window",
                exact_protocol_match=True,
                protocol_id=protocol.id,
                at_time_h=at_time_h,
                endpoint=endpoint,
                condition=condition,
                mismatch_dimensions=("time_window",),
                observations=(),
                unit_conversion_performed=False,
                interpolation_performed=False,
                state_mutation_allowed=False,
                unknown_is_negative_result=False,
                reason=(
                    "The time lies inside the protocol but outside every retained "
                    "matching observation window; interpolation is prohibited."
                ),
            )

    return PhhInjuryObservationMatch(
        status="matching_protocol_observations_available",
        exact_protocol_match=True,
        protocol_id=protocol.id,
        at_time_h=at_time_h,
        endpoint=endpoint,
        condition=condition,
        mismatch_dimensions=(),
        observations=candidates,
        unit_conversion_performed=False,
        interpolation_performed=False,
        state_mutation_allowed=False,
        unknown_is_negative_result=False,
        reason=(
            "These source observations may evaluate the exact matching protocol only. "
            "They do not define a fate law or mutate simulated cell state."
        ),
    )


def _observation_operator_snapshot(
    state: PhhInjuryValidationState,
) -> dict[str, object]:
    replay_results = tuple(
        evaluate_phh_injury_observations(
            protocol_query_from_protocol(protocol),
            state=state,
        )
        for protocol in state.protocols
    )
    reference = protocol_query_from_protocol(state.protocols[0])
    negative_queries = (
        replace(reference, species="software_mismatch_probe"),
        replace(reference, biological_system="software_mismatch_probe"),
        replace(reference, challenge="software_mismatch_probe"),
        replace(
            reference,
            challenge_low=reference.challenge_low + 1.0,
            challenge_high=(
                None
                if reference.challenge_high is None
                else reference.challenge_high + 1.0
            ),
        ),
        replace(reference, challenge_unit="software_mismatch_probe"),
        replace(reference, maximum_exposure_h=reference.maximum_exposure_h + 1.0),
        replace(reference, temperature_c=reference.temperature_c + 1.0),
    )
    negative_results = tuple(
        evaluate_phh_injury_observations(query, state=state)
        for query in negative_queries
    )
    replay_pass_count = sum(
        result.exact_protocol_match
        and result.status == "matching_protocol_observations_available"
        for result in replay_results
    )
    rejection_count = sum(
        not result.exact_protocol_match and result.status == "context_mismatch"
        for result in negative_results
    )
    if replay_pass_count != len(state.protocols):
        raise ValueError("PHH injury exact-protocol replay self-check failed")
    if rejection_count != len(negative_queries):
        raise ValueError("PHH injury near-miss rejection self-check failed")
    return {
        "version": OBSERVATION_OPERATOR_VERSION,
        "status": "exact_context_read_only_operator_ready",
        "match_dimensions": list(_PROTOCOL_MATCH_DIMENSIONS),
        "supported_result_statuses": [
            "matching_protocol_observations_available",
            "context_mismatch",
            "outside_protocol_window",
            "unobserved_endpoint",
            "unobserved_condition",
            "unobserved_time_window",
        ],
        "exact_protocol_replay_count": len(replay_results),
        "exact_protocol_replay_pass_count": replay_pass_count,
        "near_miss_probe_count": len(negative_results),
        "near_miss_rejection_count": rejection_count,
        "unit_conversion_enabled": False,
        "dose_interpolation_enabled": False,
        "time_interpolation_enabled": False,
        "generalization_enabled": False,
        "state_mutation_enabled": False,
        "unknown_is_negative_result": False,
        "policy": (
            "All protocol dimensions must match exactly. Empty results represent "
            "unobserved context, endpoint or time, never an inferred absence of effect."
        ),
    }


def validate_phh_injury_validation(state: PhhInjuryValidationState) -> None:
    load_phh_injury_trajectory_contract()
    if state.version != VERSION or state.date_verified != DATE_VERIFIED:
        raise ValueError("PHH injury-validation version changed")
    if set(state.source_ids) != set(PHH_INJURY_VALIDATION_SOURCES) or len(
        state.source_ids
    ) != len(set(state.source_ids)):
        raise ValueError("PHH injury source registry changed")
    protocols = {item.id: item for item in state.protocols}
    expected_protocols = {
        "apap_10mM_fresh_phh_48h",
        "gcdc_serum_context_phh_24h",
        "gcdc_biliary_context_phh_24h",
        "reconstituted_patient_bile_acid_milieu_phh_24h",
    }
    if len(protocols) != 4 or set(protocols) != expected_protocols:
        raise ValueError("PHH injury protocol panel changed")
    for protocol in state.protocols:
        values = (protocol.challenge_low, protocol.maximum_exposure_h, protocol.temperature_c)
        if any(not isfinite(value) or value < 0.0 for value in values):
            raise ValueError("Invalid PHH injury protocol quantity")
        if protocol.challenge_high is not None and (
            not isfinite(protocol.challenge_high)
            or protocol.challenge_high < protocol.challenge_low
        ):
            raise ValueError("Invalid PHH injury challenge bounds")
        if protocol.species != "Homo sapiens" or protocol.source_id not in state.source_ids:
            raise ValueError("PHH injury protocol lost human primary-source context")
        if (
            protocol.may_initialize_healthy_baseline
            or protocol.may_define_general_fate_law
            or protocol.may_drive_cell_state
        ):
            raise ValueError("Perturbation protocol escaped into healthy runtime")
    apap = protocols["apap_10mM_fresh_phh_48h"]
    serum = protocols["gcdc_serum_context_phh_24h"]
    biliary = protocols["gcdc_biliary_context_phh_24h"]
    if (apap.challenge_low, apap.challenge_unit) != (10.0, "mM"):
        raise ValueError("APAP protocol concentration changed")
    if (serum.challenge_low, serum.challenge_unit) != (
        22.0,
        "uM_mean_patient_serum_context",
    ):
        raise ValueError("GCDC serum context changed")
    if (biliary.challenge_low, biliary.challenge_unit) != (
        1000.0,
        "uM_lower_bound",
    ):
        raise ValueError("GCDC biliary context changed")

    observations = {item.id: item for item in state.observations}
    expected_observations = {
        "apap_necrosis_onset_24h",
        "apap_gsh_depletion_first_3h",
        "apap_mitochondrial_potential_loss_after_12h",
        "apap_nac_6h_almost_complete_protection",
        "apap_nac_15h_partial_protection",
        "gcdc_serum_context_no_death_24h",
        "gcdc_biliary_context_necrosis",
        "serum_bile_acid_mixture_no_toxicity",
        "biliary_bile_acid_mixture_toxicity",
    }
    if len(observations) != 9 or set(observations) != expected_observations:
        raise ValueError("PHH injury observation panel changed")
    for observation in state.observations:
        if observation.protocol_id not in protocols or observation.source_id not in state.source_ids:
            raise ValueError("PHH injury observation lost protocol provenance")
        if (
            not isfinite(observation.time_low_h)
            or not isfinite(observation.time_high_h)
            or observation.time_low_h < 0.0
            or observation.time_high_h < observation.time_low_h
            or observation.donor_count_low <= 0
            or observation.donor_count_high < observation.donor_count_low
        ):
            raise ValueError("Invalid PHH injury observation window")
        if (
            not observation.may_validate_matching_protocol
            or observation.may_generalize
            or observation.may_drive_cell_state
        ):
            raise ValueError("PHH injury observation exceeded matching-protocol use")
    if observations["gcdc_serum_context_no_death_24h"].death_mode is not None:
        raise ValueError("No-death serum context was assigned a death mode")
    if any(
        observations[key].death_mode != "necrosis"
        for key in (
            "apap_necrosis_onset_24h",
            "gcdc_biliary_context_necrosis",
            "biliary_bile_acid_mixture_toxicity",
        )
    ):
        raise ValueError("Human PHH necrosis observations changed")

    required_true = {"matching_protocol_observations_ready"}
    required_false = {
        "healthy_baseline_initialization_ready",
        "general_fate_law_ready",
        "senescence_commitment_ready",
        "donor_disjoint_validation_ready",
        "automatic_runtime_coupling",
        "predictive_ready",
    }
    if set(state.integration_gates) != required_true | required_false:
        raise ValueError("PHH injury integration gates changed")
    if any(state.integration_gates[key] is not True for key in required_true) or any(
        state.integration_gates[key] is not False for key in required_false
    ):
        raise ValueError("PHH injury integration gate state changed")


def phh_injury_validation_snapshot() -> dict[str, object]:
    state = build_phh_injury_validation()
    observation_operator = _observation_operator_snapshot(state)
    runtime_authority = injury_runtime_authority_snapshot()
    trajectory_contract = load_phh_injury_trajectory_contract()
    trajectory_intake = phh_injury_trajectory_intake_snapshot()
    trajectory_delivery = trajectory_intake["current_delivery"]
    trajectory_contract["current_delivery"] = trajectory_delivery
    payload = state.to_dict()
    payload["observation_operator"] = observation_operator
    payload["runtime_authority"] = runtime_authority
    payload["validation_data_contract"] = trajectory_contract
    payload["trajectory_intake"] = trajectory_intake
    payload["summary"] = {
        "primary_source_count": len(state.source_ids),
        "human_phh_protocol_count": len(state.protocols),
        "matching_protocol_observation_count": len(state.observations),
        "apap_observation_count": sum(item.id.startswith("apap_") for item in state.observations),
        "bile_acid_observation_count": sum(
            not item.id.startswith("apap_") for item in state.observations
        ),
        "necrosis_mode_observation_count": sum(
            item.death_mode == "necrosis" for item in state.observations
        ),
        "healthy_baseline_parameter_count": 0,
        "general_fate_law_count": 0,
        "senescence_commitment_observation_count": 0,
        "donor_disjoint_validation_count": 0,
        "runtime_coupled_observation_count": 0,
        "exact_protocol_operator_count": 1,
        "exact_protocol_replay_pass_count": observation_operator[
            "exact_protocol_replay_pass_count"
        ],
        "near_miss_rejection_count": observation_operator[
            "near_miss_rejection_count"
        ],
        "audited_legacy_injury_surface_count": runtime_authority["summary"][
            "audited_legacy_surface_count"
        ],
        "legacy_quantitative_authority_surface_count": runtime_authority["summary"][
            "quantitative_authority_surface_count"
        ],
        "required_donor_trajectory_field_count": len(
            trajectory_contract["required_columns"]
        ),
        "conditional_donor_trajectory_field_count": len(
            trajectory_contract["conditional_columns"]
        ),
        "trajectory_intake_validator_count": 1,
        "donor_split_leakage_guard_count": int(
            trajectory_intake["split_leakage_guard_enabled"]
        ),
        "independent_heldout_study_guard_count": int(
            trajectory_intake["independent_heldout_study_guard_enabled"]
        ),
        "exact_assay_projection_operator_count": int(
            trajectory_intake["measurement_operator"]["structure_ready"]
        ),
        "frozen_evaluation_contract_count": int(
            trajectory_intake["frozen_evaluation"]["contract_ready"]
        ),
        "complete_donor_trajectory_record_count": trajectory_delivery[
            "donor_resolved_raw_record_count"
        ],
        "numeric_measurement_projection_count": trajectory_delivery[
            "numeric_measurement_projection_count"
        ],
        "independent_heldout_result_count": trajectory_delivery[
            "independent_heldout_result_count"
        ],
    }
    return payload
