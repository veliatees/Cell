"""Fail-closed dependency graph for the four hepatocyte metabolic workstreams.

The project already contains useful reaction topologies, assay operators and a
generic Human-GEM solver stack.  Those surfaces are not interchangeable with a
quantitative single-PHH model.  This module computes the exact authority state
of each workstream from the existing scientific gates and prevents a partially
implemented cycle, or a name-only cross-cycle connection, from driving the
authoritative cell state.

The graph carries no kinetic parameter and activates no runtime behavior.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Mapping, Sequence

from cell_engine.quantitative.compartmental_energy_redox import (
    compartmental_energy_redox_snapshot,
)
from cell_engine.quantitative.human_sch_bile_acids import (
    human_sch_bile_acids_snapshot,
)
from cell_engine.quantitative.metabolic_constraint_shell import (
    metabolic_constraint_shell_snapshot,
)
from cell_engine.quantitative.phh_biliary_excretion import (
    phh_biliary_excretion_snapshot,
)
from cell_engine.quantitative.phh_cyp_function import phh_cyp_function_snapshot
from cell_engine.quantitative.phh_injury_validation import (
    phh_injury_validation_snapshot,
)
from cell_engine.quantitative.phh_transporter_inventory import (
    phh_transporter_inventory_snapshot,
)
from cell_engine.stochastic.detox import DETOX_VOLUME_L, build_detox_network
from cell_engine.stochastic.urea_cycle import build_urea_cycle_network
from cell_engine.validation.glucose_calibration import (
    glucose_calibration_validation_snapshot,
)
from cell_engine.validation.evidence_readiness import phh_evidence_readiness_snapshot
from cell_engine.validation.kinetic_transfer import kinetic_transfer_snapshot


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "validation"
    / "hepatocyte_metabolic_cycle_program.v1.json"
)
VERSION = "hepatocyte_metabolic_cycle_program_v1"
SCHEMA_VERSION = "cell.hepatocyte-metabolic-cycle-program.v1"
PROGRAM_ID = "hepatocyte_metabolic_cycle_program_v1"
DATE_VERIFIED = "2026-08-17"

STAGES = ("quantitative_execution", "prediction", "runtime_coupling")
CYCLE_IDS = (
    "glucose_glycogen_control",
    "cyp_apap_redox_injury",
    "polarized_transport_bile_flux",
    "urea_ammonia_human_gem",
)
EDGE_IDS = (
    "glut2_glucose_exchange",
    "glucose_redox_apap",
    "apap_biliary_export",
    "glucose_urea_energy_carbon",
    "urea_system_boundary",
)
EDGE_OPERATOR_IDS = (
    "shared_state_identity",
    "compartment_mapping",
    "unit_and_scale_operator",
    "time_alignment_operator",
    "donor_context_match",
    "transfer_or_conservation_law",
    "uncertainty_propagation",
)

_MANIFEST_FIELDS = frozenset(
    {
        "schema_version",
        "program_id",
        "date_verified",
        "scientific_authority",
        "automatic_parameter_activation",
        "automatic_state_coupling",
        "cycle_order",
        "cycles",
        "shared_edges",
        "policy",
    }
)
_CYCLE_FIELDS = frozenset(
    {"id", "label", "scope", "target_components", "surface_ids", "gate_ids"}
)
_EDGE_FIELDS = frozenset(
    {
        "id",
        "endpoint_cycle_ids",
        "direction",
        "shared_state_ids",
        "required_operator_ids",
    }
)
_GATE_ASSESSMENT_FIELDS = frozenset(
    {
        "id",
        "stage",
        "satisfied",
        "evidence_surface",
        "requirement",
        "observed",
        "blocker",
    }
)
_EDGE_OPERATOR_FIELDS = frozenset(
    {"id", "satisfied", "requirement", "evidence_surface", "blocker"}
)
_CYCLE_SNAPSHOT_FIELDS = frozenset(
    {
        "id",
        "label",
        "scope",
        "target_components",
        "surface_ids",
        "gates",
        "quantitative_execution_ready",
        "predictive_ready",
        "runtime_coupling_ready",
        "cross_cycle_runtime_ready",
        "blockers",
        "incident_edge_ids",
    }
)
_EDGE_SNAPSHOT_FIELDS = frozenset(
    {
        "id",
        "endpoint_cycle_ids",
        "direction",
        "shared_state_ids",
        "operators",
        "coupling_ready",
        "automatic_state_coupling",
        "blockers",
    }
)
_PROGRAM_SNAPSHOT_FIELDS = frozenset(
    {
        "version",
        "status",
        "date_verified",
        "manifest",
        "scientific_authority",
        "automatic_parameter_activation",
        "automatic_state_coupling",
        "cycles",
        "shared_edges",
        "summary",
        "policy",
    }
)
_MANIFEST_IDENTITY_FIELDS = frozenset(
    {"path", "sha256", "schema_version", "program_id"}
)
_POLICY = {
    "all_quantitative_gates_required": True,
    "prediction_requires_quantitative_execution": True,
    "runtime_coupling_requires_prediction": True,
    "cross_cycle_runtime_requires_all_incident_edges": True,
    "edge_requires_all_declared_operators": True,
    "missing_evidence_fails_closed": True,
    "shared_name_is_not_a_coupling_law": True,
    "automatic_parameter_activation": False,
    "automatic_state_coupling": False,
}
_GATE_IDS_BY_CYCLE = {
    "glucose_glycogen_control": {
        "quantitative_execution": (
            "glucose_topology_audited",
            "glucose_transfer_equations_exact",
            "glucose_single_cell_scale_ready",
            "glucose_fit_identifiability_ready",
            "glucose_independent_evidence_review_ready",
        ),
        "prediction": ("glucose_independent_validation_ready",),
        "runtime_coupling": (
            "glucose_authoritative_state_coupling_ready",
        ),
    },
    "cyp_apap_redox_injury": {
        "quantitative_execution": (
            "apap_competing_pathway_topology_ready",
            "cyp_function_observation_surface_ready",
            "apap_compartmental_redox_topology_ready",
            "apap_donor_trajectory_ready",
            "apap_kinetics_calibrated",
            "apap_mpt_injury_law_ready",
            "apap_independent_evidence_review_ready",
        ),
        "prediction": ("apap_independent_validation_ready",),
        "runtime_coupling": ("apap_authoritative_state_coupling_ready",),
    },
    "polarized_transport_bile_flux": {
        "quantitative_execution": (
            "polarized_target_inventory_ready",
            "transporter_total_abundance_observed",
            "transporter_surface_density_ready",
            "transporter_active_copy_ready",
            "canalicular_geometry_coupling_ready",
            "transporter_flux_fit_ready",
            "bile_driving_gradient_ready",
            "transporter_energy_coupling_ready",
            "transport_independent_evidence_review_ready",
        ),
        "prediction": ("transport_independent_validation_ready",),
        "runtime_coupling": (
            "transport_authoritative_state_coupling_ready",
        ),
    },
    "urea_ammonia_human_gem": {
        "quantitative_execution": (
            "urea_cycle_topology_ready",
            "urea_cycle_kinetics_ready",
            "human_gem_artifact_and_solver_ready",
            "healthy_phh_context_model_ready",
            "measured_exchange_bounds_ready",
            "measured_phh_objective_ready",
            "human_gem_single_cell_scale_ready",
            "dynamic_fba_update_law_ready",
            "human_gem_independent_evidence_review_ready",
        ),
        "prediction": ("human_gem_independent_flux_validation_ready",),
        "runtime_coupling": (
            "urea_dfba_authoritative_state_coupling_ready",
        ),
    },
}


class MetabolicCycleProgramError(RuntimeError):
    """Raised when a blocked metabolic cycle or edge is requested."""


@dataclass(frozen=True)
class GateAssessment:
    id: str
    stage: str
    satisfied: bool
    evidence_surface: str
    requirement: str
    observed: Mapping[str, object]
    blocker: str | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _nonempty_strings(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or not value:
        raise ValueError(f"{field} must be a non-empty list")
    items = tuple(value)
    if any(not isinstance(item, str) or not item.strip() for item in items):
        raise ValueError(f"{field} entries must be non-empty strings")
    if len(items) != len(set(items)):
        raise ValueError(f"{field} entries must be unique")
    return items


def validate_metabolic_cycle_manifest(payload: object) -> None:
    if not isinstance(payload, Mapping) or frozenset(payload) != _MANIFEST_FIELDS:
        raise ValueError("metabolic cycle manifest fields changed")
    if (
        payload.get("schema_version") != SCHEMA_VERSION
        or payload.get("program_id") != PROGRAM_ID
    ):
        raise ValueError("unsupported metabolic cycle manifest identity")
    try:
        date.fromisoformat(str(payload.get("date_verified")))
    except ValueError as exc:
        raise ValueError("metabolic cycle date_verified is invalid") from exc
    if (
        payload.get("date_verified") != DATE_VERIFIED
        or payload.get("scientific_authority") is not False
        or payload.get("automatic_parameter_activation") is not False
        or payload.get("automatic_state_coupling") is not False
        or payload.get("policy") != _POLICY
    ):
        raise ValueError("metabolic cycle manifest escaped fail-closed policy")

    cycle_order = _nonempty_strings(payload.get("cycle_order"), "cycle_order")
    if cycle_order != CYCLE_IDS:
        raise ValueError("metabolic cycle order changed")
    raw_cycles = payload.get("cycles")
    if not isinstance(raw_cycles, list) or len(raw_cycles) != len(CYCLE_IDS):
        raise ValueError("metabolic cycle manifest requires exactly four cycles")
    seen_gate_ids: set[str] = set()
    for expected_id, raw in zip(CYCLE_IDS, raw_cycles, strict=True):
        if not isinstance(raw, Mapping) or frozenset(raw) != _CYCLE_FIELDS:
            raise ValueError("metabolic cycle record fields changed")
        if raw.get("id") != expected_id:
            raise ValueError("metabolic cycle records are out of order")
        for field in ("label", "scope"):
            if not isinstance(raw.get(field), str) or not str(raw[field]).strip():
                raise ValueError(f"{expected_id}: {field} is required")
        _nonempty_strings(raw.get("target_components"), f"{expected_id}.target_components")
        _nonempty_strings(raw.get("surface_ids"), f"{expected_id}.surface_ids")
        gate_ids = raw.get("gate_ids")
        if not isinstance(gate_ids, Mapping) or set(gate_ids) != set(STAGES):
            raise ValueError(f"{expected_id}: gate stages changed")
        expected_stages = _GATE_IDS_BY_CYCLE[expected_id]
        for stage in STAGES:
            ids = _nonempty_strings(gate_ids.get(stage), f"{expected_id}.{stage}")
            if ids != expected_stages[stage]:
                raise ValueError(f"{expected_id}: {stage} gate identities changed")
            if seen_gate_ids.intersection(ids):
                raise ValueError("metabolic gate identities must be globally unique")
            seen_gate_ids.update(ids)

    raw_edges = payload.get("shared_edges")
    if not isinstance(raw_edges, list) or len(raw_edges) != len(EDGE_IDS):
        raise ValueError("metabolic cycle manifest requires exactly five shared edges")
    adjacency = {cycle_id: set() for cycle_id in CYCLE_IDS}
    for expected_id, raw in zip(EDGE_IDS, raw_edges, strict=True):
        if not isinstance(raw, Mapping) or frozenset(raw) != _EDGE_FIELDS:
            raise ValueError("metabolic shared-edge fields changed")
        if raw.get("id") != expected_id:
            raise ValueError("metabolic shared edges are out of order")
        endpoints = _nonempty_strings(
            raw.get("endpoint_cycle_ids"), f"{expected_id}.endpoint_cycle_ids"
        )
        if len(endpoints) != 2 or any(item not in CYCLE_IDS for item in endpoints):
            raise ValueError(f"{expected_id}: exactly two known endpoints are required")
        if raw.get("direction") != "bidirectional_state_constraint":
            raise ValueError(f"{expected_id}: unsupported edge direction")
        _nonempty_strings(raw.get("shared_state_ids"), f"{expected_id}.shared_state_ids")
        operators = _nonempty_strings(
            raw.get("required_operator_ids"),
            f"{expected_id}.required_operator_ids",
        )
        if operators != EDGE_OPERATOR_IDS:
            raise ValueError(f"{expected_id}: coupling operator contract changed")
        adjacency[endpoints[0]].add(endpoints[1])
        adjacency[endpoints[1]].add(endpoints[0])

    visited = {CYCLE_IDS[0]}
    pending = [CYCLE_IDS[0]]
    while pending:
        current = pending.pop()
        for neighbour in adjacency[current] - visited:
            visited.add(neighbour)
            pending.append(neighbour)
    if visited != set(CYCLE_IDS):
        raise ValueError("metabolic cycle dependency graph must be connected")


def load_metabolic_cycle_manifest(path: Path = MANIFEST_PATH) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    validate_metabolic_cycle_manifest(payload)
    return payload


def _assessment(
    gate_id: str,
    stage: str,
    satisfied: bool,
    evidence_surface: str,
    requirement: str,
    observed: Mapping[str, object],
    blocker: str,
) -> GateAssessment:
    return GateAssessment(
        id=gate_id,
        stage=stage,
        satisfied=bool(satisfied),
        evidence_surface=evidence_surface,
        requirement=requirement,
        observed=dict(observed),
        blocker=None if satisfied else blocker,
    )


def _gate_stage(manifest_cycle: Mapping[str, object], gate_id: str) -> str:
    gate_ids = manifest_cycle["gate_ids"]
    if not isinstance(gate_ids, Mapping):
        raise ValueError("metabolic cycle gate map is malformed")
    for stage in STAGES:
        if gate_id in gate_ids[stage]:
            return stage
    raise ValueError(f"unregistered metabolic gate: {gate_id}")


def _build_gate_assessments(
    manifest_cycles: Sequence[Mapping[str, object]],
) -> dict[str, GateAssessment]:
    by_cycle = {str(item["id"]): item for item in manifest_cycles}
    transfer = kinetic_transfer_snapshot()
    glucose = glucose_calibration_validation_snapshot()
    cyp = phh_cyp_function_snapshot()
    redox = compartmental_energy_redox_snapshot()
    injury = phh_injury_validation_snapshot()
    transporters = phh_transporter_inventory_snapshot()
    transporter_ids = {item["id"] for item in transporters["transporters"]}
    target_transporter_ids = {
        "ABCB11_BSEP",
        "ABCC2_MRP2",
        "SLC10A1_NTCP",
        "SLC2A2_GLUT2",
        "SLCO1B1_OATP1B1",
        "SLCO1B3_OATP1B3",
    }
    biliary = phh_biliary_excretion_snapshot()
    bile_acids = human_sch_bile_acids_snapshot()
    human_gem = metabolic_constraint_shell_snapshot()
    human_gem_loader = human_gem["candidate_reconstruction"][
        "sparse_fbc_loader_audit"
    ]
    human_gem_numerics = human_gem["generic_constraint_numerics"]
    human_gem_bundle = human_gem["phh_execution_bundle_intake"]
    evidence_readiness = phh_evidence_readiness_snapshot()
    evidence_by_id = {item["id"]: item for item in evidence_readiness["entries"]}

    detox_network = build_detox_network(DETOX_VOLUME_L)
    detox_reactions = {reaction.id for reaction in detox_network.reactions}
    detox_species = set(detox_network.species)
    detox_topology_ready = {
        "safe_conjugation",
        "cyp_oxidation",
        "gsh_conjugation",
        "protein_binding",
    } <= detox_reactions and {
        "paracetamol",
        "NAPQI",
        "GSH",
        "protein_adduct",
        "ROS",
    } <= detox_species

    urea_network = build_urea_cycle_network(1.0e-12)
    urea_reactions = {reaction.id for reaction in urea_network.reactions}
    urea_topology_ready = urea_reactions == {"cps1", "otc", "ass1", "asl", "arg1"}
    urea_placeholder_reactions = tuple(
        reaction.id
        for reaction in urea_network.reactions
        if "placeholder" in reaction.notes.lower()
        or "lumped" in reaction.notes.lower()
    )

    def make(
        cycle_id: str,
        gate_id: str,
        satisfied: bool,
        surface: str,
        requirement: str,
        observed: Mapping[str, object],
        blocker: str,
    ) -> GateAssessment:
        return _assessment(
            gate_id,
            _gate_stage(by_cycle[cycle_id], gate_id),
            satisfied,
            surface,
            requirement,
            observed,
            blocker,
        )

    def review_observation(*entry_ids: str) -> dict[str, object]:
        return {
            entry_id: {
                "delivery_present": evidence_by_id[entry_id]["delivery_present"],
                "delivery_review_status": evidence_by_id[entry_id][
                    "delivery_review_status"
                ],
                "independent_review_approved": evidence_by_id[entry_id][
                    "independent_review_approved"
                ],
            }
            for entry_id in entry_ids
        }

    def reviews_approved(*entry_ids: str) -> bool:
        return all(
            evidence_by_id[entry_id]["contract_identity_verified"]
            and evidence_by_id[entry_id]["independent_review_approved"]
            for entry_id in entry_ids
        )

    gates = (
        make(
            "glucose_glycogen_control",
            "glucose_topology_audited",
            transfer["source_model_reaction_count"] == 36
            and transfer["source_model_kinetic_law_count"] == 36
            and transfer["active_reaction_count"] == 36
            and transfer["mapped_candidate_count"] == 12,
            "kinetic_transfer",
            "The source and active glucose networks must be enumerated before transfer.",
            {
                "source_reaction_count": transfer["source_model_reaction_count"],
                "active_reaction_count": transfer["active_reaction_count"],
                "mapped_candidate_count": transfer["mapped_candidate_count"],
            },
            "The source/target topology audit is incomplete.",
        ),
        make(
            "glucose_glycogen_control",
            "glucose_transfer_equations_exact",
            transfer["exact_stoichiometry_match_count"]
            == transfer["mapped_candidate_count"]
            and transfer["exact_symbolic_rate_law_match_count"]
            == transfer["mapped_candidate_count"],
            "kinetic_transfer",
            "Every candidate transfer requires exact stoichiometry and symbolic rate law.",
            {
                "candidate_count": transfer["mapped_candidate_count"],
                "exact_stoichiometry_count": transfer[
                    "exact_stoichiometry_match_count"
                ],
                "exact_symbolic_rate_law_count": transfer[
                    "exact_symbolic_rate_law_match_count"
                ],
            },
            "Only part of the stoichiometry matches and no symbolic kinetic law matches exactly.",
        ),
        make(
            "glucose_glycogen_control",
            "glucose_single_cell_scale_ready",
            transfer["per_cell_unit_bridge_ready_count"]
            == transfer["mapped_candidate_count"],
            "kinetic_transfer",
            "Organ/tissue flux denominators require an explicit single-PHH scale operator.",
            {
                "required_bridge_count": transfer["mapped_candidate_count"],
                "ready_bridge_count": transfer["per_cell_unit_bridge_ready_count"],
            },
            "No candidate reaction has an accepted organ-to-single-cell unit bridge.",
        ),
        make(
            "glucose_glycogen_control",
            "glucose_fit_identifiability_ready",
            bool(glucose["kinetic_parameter_calibration_ready"])
            and glucose["summary"]["fit_eligible_reaction_count"]
            == glucose["summary"]["audited_reaction_count"],
            "glucose_calibration_validation",
            "Reaction-specific observability and identifiable PHH calibration data are required.",
            {
                "audited_reaction_count": glucose["summary"][
                    "audited_reaction_count"
                ],
                "fit_eligible_reaction_count": glucose["summary"][
                    "fit_eligible_reaction_count"
                ],
                "kinetic_parameter_calibration_ready": glucose[
                    "kinetic_parameter_calibration_ready"
                ],
            },
            "Net glucose observations do not identify the individual reaction parameters.",
        ),
        make(
            "glucose_glycogen_control",
            "glucose_independent_evidence_review_ready",
            reviews_approved("legacy_scale_bridge_bundle", "reaction_evidence"),
            "phh_evidence_readiness",
            "Scale-bridge and reaction-evidence deliveries require exact-hash independent review.",
            review_observation("legacy_scale_bridge_bundle", "reaction_evidence"),
            "Glucose scale and reaction evidence have no independently approved delivery.",
        ),
        make(
            "glucose_glycogen_control",
            "glucose_independent_validation_ready",
            bool(glucose["independent_heldout_validation_ready"])
            and bool(glucose["uncertainty_qualified_pass_fail_ready"])
            and bool(glucose["predictive_ready"]),
            "glucose_calibration_validation",
            "Prediction requires donor-disjoint held-out validation and a frozen uncertainty-qualified threshold.",
            {
                "independent_heldout_result_count": glucose["summary"][
                    "independent_heldout_result_count"
                ],
                "pass_fail_count": glucose["summary"]["pass_fail_count"],
                "predictive_ready": glucose["predictive_ready"],
            },
            "No independent held-out glucose result or predictive pass/fail decision exists.",
        ),
        make(
            "glucose_glycogen_control",
            "glucose_authoritative_state_coupling_ready",
            bool(glucose["automatic_state_coupling"])
            and bool(glucose["predictive_parameter_activation_allowed"]),
            "glucose_calibration_validation",
            "Only independently validated parameters may mutate authoritative cell state.",
            {
                "parameter_activation_allowed": glucose[
                    "predictive_parameter_activation_allowed"
                ],
                "automatic_state_coupling": glucose["automatic_state_coupling"],
            },
            "Glucose parameter activation and authoritative state coupling remain disabled.",
        ),
        make(
            "cyp_apap_redox_injury",
            "apap_competing_pathway_topology_ready",
            detox_topology_ready,
            "legacy_detox_fixture",
            "The exploratory network must represent competing safe, NAPQI, GSH and adduct routes.",
            {
                "reaction_ids": tuple(sorted(detox_reactions)),
                "required_species_present": detox_topology_ready,
                "quantitative_authority": False,
            },
            "The APAP competing-pathway topology is incomplete.",
        ),
        make(
            "cyp_apap_redox_injury",
            "cyp_function_observation_surface_ready",
            cyp["summary"]["enzyme_count"] == 6
            and cyp["summary"]["quantified_mean_record_count"] > 0
            and bool(cyp["same_format_comparison_ready"]),
            "phh_cyp_function",
            "CYP assay endpoints must be retained in their exact reported format.",
            {
                "enzyme_count": cyp["summary"]["enzyme_count"],
                "quantified_mean_record_count": cyp["summary"][
                    "quantified_mean_record_count"
                ],
                "same_format_comparison_ready": cyp[
                    "same_format_comparison_ready"
                ],
            },
            "The CYP function observation surface is incomplete.",
        ),
        make(
            "cyp_apap_redox_injury",
            "apap_compartmental_redox_topology_ready",
            bool(redox["compartment_topology_ready"])
            and redox["summary"]["explicit_pool_count"] == 38,
            "compartmental_energy_redox",
            "APAP injury must address compartment-specific ATP, NADPH, GSH and ROS pools.",
            {
                "compartment_count": redox["summary"]["compartment_count"],
                "explicit_pool_count": redox["summary"]["explicit_pool_count"],
                "numerical_execution_enabled": redox["numerical_execution_enabled"],
            },
            "The compartmental energy/redox topology is incomplete.",
        ),
        make(
            "cyp_apap_redox_injury",
            "apap_donor_trajectory_ready",
            injury["summary"]["complete_donor_trajectory_record_count"] > 0
            and injury["summary"]["numeric_measurement_projection_count"] > 0,
            "phh_injury_validation",
            "Matched donor-resolved APAP exposure, GSH, energy, injury and recovery trajectories are required.",
            {
                "complete_donor_trajectory_record_count": injury["summary"][
                    "complete_donor_trajectory_record_count"
                ],
                "numeric_measurement_projection_count": injury["summary"][
                    "numeric_measurement_projection_count"
                ],
            },
            "No complete donor-resolved APAP trajectory has passed intake and review.",
        ),
        make(
            "cyp_apap_redox_injury",
            "apap_kinetics_calibrated",
            bool(cyp["kinetic_parameter_fit_ready"])
            and bool(redox["numerical_execution_enabled"])
            and bool(redox["parameter_activation_allowed"]),
            "phh_cyp_function + compartmental_energy_redox",
            "CYP formation, conjugation and redox rates require identifiable PHH kinetics.",
            {
                "cyp_kinetic_parameter_fit_ready": cyp[
                    "kinetic_parameter_fit_ready"
                ],
                "redox_executable_process_count": redox["summary"][
                    "executable_process_count"
                ],
                "redox_parameter_activation_allowed": redox[
                    "parameter_activation_allowed"
                ],
            },
            "CYP-to-NAPQI and compartmental GSH/NADPH kinetics are not calibrated.",
        ),
        make(
            "cyp_apap_redox_injury",
            "apap_mpt_injury_law_ready",
            bool(injury["integration_gates"]["general_fate_law_ready"]),
            "phh_injury_validation",
            "A measured law must connect mitochondrial/redox failure to MPT and injury outputs.",
            {
                "general_fate_law_ready": injury["integration_gates"][
                    "general_fate_law_ready"
                ],
                "general_fate_law_count": injury["summary"][
                    "general_fate_law_count"
                ],
            },
            "No validated PHH MPT/injury transition law is registered.",
        ),
        make(
            "cyp_apap_redox_injury",
            "apap_independent_evidence_review_ready",
            reviews_approved("energy_redox_trajectory", "phh_injury_trajectory"),
            "phh_evidence_readiness",
            "Energy/redox and APAP injury trajectories require exact-hash independent review.",
            review_observation("energy_redox_trajectory", "phh_injury_trajectory"),
            "APAP/redox trajectory evidence has no independently approved delivery.",
        ),
        make(
            "cyp_apap_redox_injury",
            "apap_independent_validation_ready",
            injury["summary"]["independent_heldout_result_count"] > 0
            and bool(injury["integration_gates"]["donor_disjoint_validation_ready"])
            and bool(injury["integration_gates"]["predictive_ready"]),
            "phh_injury_validation",
            "Prediction requires donor/study-disjoint APAP validation.",
            {
                "independent_heldout_result_count": injury["summary"][
                    "independent_heldout_result_count"
                ],
                "predictive_ready": injury["integration_gates"][
                    "predictive_ready"
                ],
            },
            "No independent APAP injury prediction has passed a frozen evaluation.",
        ),
        make(
            "cyp_apap_redox_injury",
            "apap_authoritative_state_coupling_ready",
            bool(injury["integration_gates"]["automatic_runtime_coupling"])
            and bool(
                injury["runtime_authority"][
                    "authoritative_cell_state_coupling_allowed"
                ]
            ),
            "phh_injury_validation.runtime_authority",
            "The validated APAP cascade must explicitly permit authoritative state mutation.",
            {
                "automatic_runtime_coupling": injury["integration_gates"][
                    "automatic_runtime_coupling"
                ],
                "authoritative_cell_state_coupling_allowed": injury[
                    "runtime_authority"
                ]["authoritative_cell_state_coupling_allowed"],
            },
            "The legacy injury fixture has zero authoritative state-coupling permission.",
        ),
        make(
            "polarized_transport_bile_flux",
            "polarized_target_inventory_ready",
            transporter_ids == target_transporter_ids,
            "phh_transporter_inventory",
            "BSEP, MRP2, NTCP, GLUT2, OATP1B1 and OATP1B3 require quantitative inventory records.",
            {
                "target_transporter_count": 6,
                "quantitative_inventory_count": transporters["summary"][
                    "transporter_count"
                ],
                "quantitative_inventory_ids": tuple(sorted(transporter_ids)),
            },
            "Only BSEP and MRP2 have quantitative inventory records; four target transporters are absent.",
        ),
        make(
            "polarized_transport_bile_flux",
            "transporter_total_abundance_observed",
            bool(transporters["bsep_total_per_nucleus_observation_ready"])
            and bool(transporters["mrp2_total_per_nucleus_observation_ready"]),
            "phh_transporter_inventory",
            "At least the existing BSEP/MRP2 total-abundance observations must remain available.",
            {
                "direct_total_per_nucleus_observation_count": transporters[
                    "summary"
                ]["direct_total_per_nucleus_observation_count"],
                "bsep_ready": transporters[
                    "bsep_total_per_nucleus_observation_ready"
                ],
                "mrp2_ready": transporters[
                    "mrp2_total_per_nucleus_observation_ready"
                ],
            },
            "BSEP/MRP2 total-abundance observations are incomplete.",
        ),
        make(
            "polarized_transport_bile_flux",
            "transporter_surface_density_ready",
            bool(transporters["surface_density_ready"])
            and transporters["summary"]["surface_density_record_count"] >= 6,
            "phh_transporter_inventory",
            "Each target requires domain-localized copies divided by measured local membrane area.",
            {
                "target_transporter_count": 6,
                "surface_density_record_count": transporters["summary"][
                    "surface_density_record_count"
                ],
                "surface_density_ready": transporters["surface_density_ready"],
            },
            "No target transporter has a validated local surface-density record.",
        ),
        make(
            "polarized_transport_bile_flux",
            "transporter_active_copy_ready",
            bool(transporters["active_copy_observation_ready"])
            and transporters["summary"]["active_copy_count_record_count"] >= 6,
            "phh_transporter_inventory",
            "Flux capacity requires active surface copies rather than whole-cell totals.",
            {
                "active_copy_count_record_count": transporters["summary"][
                    "active_copy_count_record_count"
                ],
                "active_copy_observation_ready": transporters[
                    "active_copy_observation_ready"
                ],
            },
            "Total abundance has not been converted into active surface copy number.",
        ),
        make(
            "polarized_transport_bile_flux",
            "canalicular_geometry_coupling_ready",
            bool(biliary["canalicular_geometry_coupling_ready"]),
            "phh_biliary_excretion",
            "Bile flux requires donor-matched canalicular area/volume and transporter localization.",
            {
                "measurement_operator_ready": biliary[
                    "measurement_operator_ready"
                ],
                "canalicular_geometry_coupling_ready": biliary[
                    "canalicular_geometry_coupling_ready"
                ],
            },
            "The biliary assay operator is present, but no canalicular geometry coupling exists.",
        ),
        make(
            "polarized_transport_bile_flux",
            "transporter_flux_fit_ready",
            bool(biliary["transporter_specific_rate_fit_ready"])
            and bool(transporters["flux_coupling_ready"]),
            "phh_biliary_excretion + phh_transporter_inventory",
            "Transporter-specific rates must be identifiable from matched perturbation data.",
            {
                "transporter_specific_rate_fit_ready": biliary[
                    "transporter_specific_rate_fit_ready"
                ],
                "flux_parameter_count": transporters["summary"][
                    "flux_parameter_count"
                ],
            },
            "Aggregate BEI endpoints do not identify transporter-specific flux parameters.",
        ),
        make(
            "polarized_transport_bile_flux",
            "bile_driving_gradient_ready",
            bool(bile_acids["true_canalicular_concentration_ready"])
            and bool(bile_acids["healthy_in_vivo_initialization_ready"]),
            "human_sch_bile_acids",
            "Transport requires true compartment concentrations and healthy-PHH boundary initialization.",
            {
                "true_canalicular_concentration_ready": bile_acids[
                    "true_canalicular_concentration_ready"
                ],
                "healthy_in_vivo_initialization_ready": bile_acids[
                    "healthy_in_vivo_initialization_ready"
                ],
            },
            "Reported aggregate SCH concentrations do not define a true canalicular driving gradient.",
        ),
        make(
            "polarized_transport_bile_flux",
            "transporter_energy_coupling_ready",
            bool(redox["compartment_initialization_ready"])
            and bool(redox["numerical_execution_enabled"])
            and bool(transporters["flux_coupling_ready"]),
            "compartmental_energy_redox + phh_transporter_inventory",
            "ATP-dependent transport requires a validated local ATP/ADP state and consumption law.",
            {
                "energy_compartment_initialization_ready": redox[
                    "compartment_initialization_ready"
                ],
                "energy_numerical_execution_enabled": redox[
                    "numerical_execution_enabled"
                ],
                "transport_flux_coupling_ready": transporters[
                    "flux_coupling_ready"
                ],
            },
            "No quantitative ATP-to-transporter flux coupling is authorized.",
        ),
        make(
            "polarized_transport_bile_flux",
            "transport_independent_evidence_review_ready",
            reviews_approved("active_protein_localization"),
            "phh_evidence_readiness",
            "Localized active-transporter evidence requires exact-hash independent review.",
            review_observation("active_protein_localization"),
            "Active localized transporter evidence has no independently approved delivery.",
        ),
        make(
            "polarized_transport_bile_flux",
            "transport_independent_validation_ready",
            bool(biliary["predictive_ready"])
            and bool(bile_acids["predictive_ready"])
            and biliary["summary"]["pass_fail_count"] > 0,
            "phh_biliary_excretion + human_sch_bile_acids",
            "Prediction requires held-out vectorial flux trajectories and frozen acceptance criteria.",
            {
                "biliary_pass_fail_count": biliary["summary"]["pass_fail_count"],
                "biliary_predictive_ready": biliary["predictive_ready"],
                "bile_acid_predictive_ready": bile_acids["predictive_ready"],
            },
            "No held-out polarized transport prediction has passed validation.",
        ),
        make(
            "polarized_transport_bile_flux",
            "transport_authoritative_state_coupling_ready",
            bool(transporters["automatic_state_coupling"])
            and bool(biliary["automatic_state_coupling"])
            and bool(bile_acids["automatic_state_coupling"]),
            "polarized transport authority surfaces",
            "Every contributing transport surface must authorize cell-state coupling.",
            {
                "inventory_coupling": transporters["automatic_state_coupling"],
                "biliary_coupling": biliary["automatic_state_coupling"],
                "bile_acid_coupling": bile_acids["automatic_state_coupling"],
            },
            "All polarized transport authority surfaces keep automatic state coupling disabled.",
        ),
        make(
            "urea_ammonia_human_gem",
            "urea_cycle_topology_ready",
            urea_topology_ready,
            "legacy_urea_cycle_fixture",
            "The five-enzyme urea-cycle topology and ornithine closure must be explicit.",
            {
                "reaction_ids": tuple(sorted(urea_reactions)),
                "reaction_count": len(urea_reactions),
                "quantitative_authority": False,
            },
            "The five-enzyme urea-cycle topology is incomplete.",
        ),
        make(
            "urea_ammonia_human_gem",
            "urea_cycle_kinetics_ready",
            not urea_placeholder_reactions,
            "legacy_urea_cycle_fixture",
            "All urea-cycle kinetic constants require PHH provenance, units and validation.",
            {
                "reaction_count": len(urea_reactions),
                "placeholder_or_lumped_reaction_ids": urea_placeholder_reactions,
            },
            "The urea-cycle fixture contains placeholder or lumped kinetics.",
        ),
        make(
            "urea_ammonia_human_gem",
            "human_gem_artifact_and_solver_ready",
            bool(human_gem_loader["artifact_identity_verified_before_parse"])
            and bool(human_gem_loader["generic_human_reconstruction_loaded"])
            and human_gem_numerics["analytic_fixture_pass_count"] == 5,
            "metabolic_constraint_shell",
            "The pinned Human-GEM identity, sparse loader and generic solver fixtures must pass.",
            {
                "artifact_identity_verified": human_gem_loader[
                    "artifact_identity_verified_before_parse"
                ],
                "generic_reconstruction_loaded": human_gem_loader[
                    "generic_human_reconstruction_loaded"
                ],
                "generic_solver_fixture_pass_count": human_gem_numerics[
                    "analytic_fixture_pass_count"
                ],
                "biological_flux_authority": human_gem_numerics[
                    "biological_flux_authority"
                ],
            },
            "The pinned Human-GEM artifact or generic numerical kernel is unavailable.",
        ),
        make(
            "urea_ammonia_human_gem",
            "healthy_phh_context_model_ready",
            bool(human_gem_loader["healthy_phh_context_extracted"])
            and human_gem_bundle["structurally_complete_bundle_count"] > 0,
            "metabolic_constraint_shell",
            "A donor/cohort-, nutrition- and zonation-qualified PHH context model is required.",
            {
                "healthy_phh_context_extracted": human_gem_loader[
                    "healthy_phh_context_extracted"
                ],
                "structurally_complete_bundle_count": human_gem_bundle[
                    "structurally_complete_bundle_count"
                ],
            },
            "The generic human reconstruction has not become an accepted healthy-PHH context model.",
        ),
        make(
            "urea_ammonia_human_gem",
            "measured_exchange_bounds_ready",
            human_gem_bundle["measured_exchange_bound_count"] > 0
            and human_gem["optimization_problem"]["boundary_fluxes"] is not None,
            "metabolic_constraint_shell",
            "Measured PHH exchange bounds must define the open-system boundary.",
            {
                "measured_exchange_bound_count": human_gem_bundle[
                    "measured_exchange_bound_count"
                ],
                "boundary_fluxes_loaded": human_gem["optimization_problem"][
                    "boundary_fluxes"
                ]
                is not None,
            },
            "No measured PHH exchange-bound set is loaded.",
        ),
        make(
            "urea_ammonia_human_gem",
            "measured_phh_objective_ready",
            human_gem["optimization_problem"]["objective"] is not None
            and bool(
                human_gem["optimization_problem"][
                    "objective_is_biological_measurement"
                ]
            ),
            "metabolic_constraint_shell",
            "The optimization objective must be justified by a matched PHH measurement.",
            {
                "objective_loaded": human_gem["optimization_problem"]["objective"]
                is not None,
                "objective_is_biological_measurement": human_gem[
                    "optimization_problem"
                ]["objective_is_biological_measurement"],
            },
            "The generic biomass objective is not an accepted healthy-PHH objective.",
        ),
        make(
            "urea_ammonia_human_gem",
            "human_gem_single_cell_scale_ready",
            human_gem_bundle["structurally_complete_bundle_count"] > 0
            and human_gem_bundle["verified_artifact_count"]
            == human_gem_bundle["required_artifact_count"],
            "phh_metabolic_execution_bundle",
            "Tissue/exchange fluxes require an explicit denominator-preserving single-cell scale operator.",
            {
                "structurally_complete_bundle_count": human_gem_bundle[
                    "structurally_complete_bundle_count"
                ],
                "verified_artifact_count": human_gem_bundle[
                    "verified_artifact_count"
                ],
                "required_artifact_count": human_gem_bundle[
                    "required_artifact_count"
                ],
            },
            "No reviewed Human-GEM-to-single-PHH scale operator is delivered.",
        ),
        make(
            "urea_ammonia_human_gem",
            "dynamic_fba_update_law_ready",
            False,
            "metabolic_cycle_program",
            "A registered mass-conserving law must update extracellular state, bounds and intracellular pools over time.",
            {
                "registered_dynamic_fba_update_law_count": 0,
                "static_fba_execution_allowed": human_gem["gates"][
                    "fba_execution_allowed"
                ],
            },
            "No quantitative dynamic-FBA state/boundary update law is registered.",
        ),
        make(
            "urea_ammonia_human_gem",
            "human_gem_independent_evidence_review_ready",
            reviews_approved("metabolic_execution_bundle"),
            "phh_evidence_readiness",
            "The complete PHH metabolic execution bundle requires exact-hash independent review.",
            review_observation("metabolic_execution_bundle"),
            "The PHH metabolic execution bundle has no independently approved delivery.",
        ),
        make(
            "urea_ammonia_human_gem",
            "human_gem_independent_flux_validation_ready",
            human_gem_bundle["independent_validation_record_count"] > 0
            and bool(human_gem["gates"]["may_drive_scientific_validation"]),
            "phh_metabolic_execution_bundle",
            "Prediction requires donor/study-disjoint exchange and isotope-flux validation.",
            {
                "independent_validation_record_count": human_gem_bundle[
                    "independent_validation_record_count"
                ],
                "may_drive_scientific_validation": human_gem["gates"][
                    "may_drive_scientific_validation"
                ],
            },
            "No independent PHH flux validation record is loaded.",
        ),
        make(
            "urea_ammonia_human_gem",
            "urea_dfba_authoritative_state_coupling_ready",
            bool(human_gem_bundle["runtime_flux_coupling_allowed"])
            and bool(human_gem["gates"]["may_initialize_dynamic_reaction_rates"]),
            "metabolic_constraint_shell",
            "Validated dFBA fluxes must explicitly authorize dynamic cell-state coupling.",
            {
                "runtime_flux_coupling_allowed": human_gem_bundle[
                    "runtime_flux_coupling_allowed"
                ],
                "may_initialize_dynamic_reaction_rates": human_gem["gates"][
                    "may_initialize_dynamic_reaction_rates"
                ],
            },
            "Human-GEM fluxes cannot initialize or mutate the authoritative dynamic state.",
        ),
    )
    by_id = {item.id: item for item in gates}
    expected_ids = {
        gate_id
        for stages in _GATE_IDS_BY_CYCLE.values()
        for ids in stages.values()
        for gate_id in ids
    }
    if set(by_id) != expected_ids or len(by_id) != len(gates):
        raise ValueError("metabolic cycle gate implementation and manifest disagree")
    return by_id


def _edge_operator_assessments(edge: Mapping[str, object]) -> tuple[dict[str, object], ...]:
    edge_id = str(edge["id"])
    shared_states = tuple(edge["shared_state_ids"])
    requirements = {
        "shared_state_identity": (
            bool(shared_states),
            "Shared state identities are declared, but declaration alone carries no quantitative authority.",
        ),
        "compartment_mapping": (
            False,
            "No reviewed endpoint-to-endpoint compartment mapping is registered.",
        ),
        "unit_and_scale_operator": (
            False,
            "No reviewed unit and biological-scale conversion operator is registered.",
        ),
        "time_alignment_operator": (
            False,
            "No common event/time-step alignment and interpolation contract is registered.",
        ),
        "donor_context_match": (
            False,
            "No donor-, nutrition-, zonation- and assay-matched cross-cycle context is registered.",
        ),
        "transfer_or_conservation_law": (
            False,
            "No source-backed transfer, conservation or work law joins the endpoints.",
        ),
        "uncertainty_propagation": (
            False,
            "No uncertainty propagation operator joins the endpoint state estimates.",
        ),
    }
    return tuple(
        {
            "id": operator_id,
            "satisfied": requirements[operator_id][0],
            "requirement": requirements[operator_id][1],
            "evidence_surface": (
                "metabolic_cycle_program.manifest"
                if operator_id == "shared_state_identity"
                else None
            ),
            "blocker": None
            if requirements[operator_id][0]
            else f"{edge_id}: {requirements[operator_id][1]}",
        }
        for operator_id in edge["required_operator_ids"]
    )


def hepatocyte_metabolic_cycle_program_snapshot() -> dict[str, object]:
    manifest = load_metabolic_cycle_manifest()
    manifest_cycles = tuple(manifest["cycles"])
    gate_assessments = _build_gate_assessments(manifest_cycles)

    cycles: list[dict[str, object]] = []
    for raw in manifest_cycles:
        gates = tuple(
            gate_assessments[gate_id].to_dict()
            for stage in STAGES
            for gate_id in raw["gate_ids"][stage]
        )
        by_stage = {
            stage: tuple(item for item in gates if item["stage"] == stage)
            for stage in STAGES
        }
        quantitative_ready = all(
            item["satisfied"] for item in by_stage["quantitative_execution"]
        )
        predictive_ready = quantitative_ready and all(
            item["satisfied"] for item in by_stage["prediction"]
        )
        runtime_ready = predictive_ready and all(
            item["satisfied"] for item in by_stage["runtime_coupling"]
        )
        cycles.append(
            {
                "id": raw["id"],
                "label": raw["label"],
                "scope": raw["scope"],
                "target_components": tuple(raw["target_components"]),
                "surface_ids": tuple(raw["surface_ids"]),
                "gates": gates,
                "quantitative_execution_ready": quantitative_ready,
                "predictive_ready": predictive_ready,
                "runtime_coupling_ready": runtime_ready,
                "cross_cycle_runtime_ready": False,
                "blockers": tuple(
                    item["blocker"] for item in gates if not item["satisfied"]
                ),
            }
        )

    edges: list[dict[str, object]] = []
    for raw in manifest["shared_edges"]:
        operators = _edge_operator_assessments(raw)
        coupling_ready = all(item["satisfied"] for item in operators)
        edges.append(
            {
                "id": raw["id"],
                "endpoint_cycle_ids": tuple(raw["endpoint_cycle_ids"]),
                "direction": raw["direction"],
                "shared_state_ids": tuple(raw["shared_state_ids"]),
                "operators": operators,
                "coupling_ready": coupling_ready,
                "automatic_state_coupling": False,
                "blockers": tuple(
                    item["blocker"] for item in operators if not item["satisfied"]
                ),
            }
        )

    for cycle in cycles:
        incident = tuple(
            edge
            for edge in edges
            if cycle["id"] in edge["endpoint_cycle_ids"]
        )
        cycle["cross_cycle_runtime_ready"] = bool(
            cycle["runtime_coupling_ready"]
            and incident
            and all(edge["coupling_ready"] for edge in incident)
        )
        cycle["incident_edge_ids"] = tuple(edge["id"] for edge in incident)

    all_gates = tuple(gate for cycle in cycles for gate in cycle["gates"])
    all_operators = tuple(operator for edge in edges for operator in edge["operators"])
    payload = {
        "version": VERSION,
        "status": "four_cycle_dependency_surface_ready_quantitative_execution_blocked",
        "date_verified": DATE_VERIFIED,
        "manifest": {
            "path": str(MANIFEST_PATH.relative_to(REPOSITORY_ROOT)),
            "sha256": _sha256(MANIFEST_PATH),
            "schema_version": manifest["schema_version"],
            "program_id": manifest["program_id"],
        },
        "scientific_authority": False,
        "automatic_parameter_activation": False,
        "automatic_state_coupling": False,
        "cycles": tuple(cycles),
        "shared_edges": tuple(edges),
        "summary": {
            "cycle_count": len(cycles),
            "cycle_with_structural_surface_count": sum(
                any(gate["satisfied"] for gate in cycle["gates"])
                for cycle in cycles
            ),
            "gate_count": len(all_gates),
            "satisfied_gate_count": sum(gate["satisfied"] for gate in all_gates),
            "quantitative_execution_ready_cycle_count": sum(
                cycle["quantitative_execution_ready"] for cycle in cycles
            ),
            "predictive_ready_cycle_count": sum(
                cycle["predictive_ready"] for cycle in cycles
            ),
            "runtime_coupling_ready_cycle_count": sum(
                cycle["runtime_coupling_ready"] for cycle in cycles
            ),
            "cross_cycle_runtime_ready_cycle_count": sum(
                cycle["cross_cycle_runtime_ready"] for cycle in cycles
            ),
            "shared_edge_count": len(edges),
            "edge_operator_count": len(all_operators),
            "satisfied_edge_operator_count": sum(
                operator["satisfied"] for operator in all_operators
            ),
            "coupled_edge_count": sum(edge["coupling_ready"] for edge in edges),
            "automatic_parameter_activation_count": 0,
            "automatic_state_coupling_count": 0,
        },
        "policy": manifest["policy"],
    }
    validate_hepatocyte_metabolic_cycle_program(payload)
    return payload


def validate_hepatocyte_metabolic_cycle_program(payload: Mapping[str, object]) -> None:
    if frozenset(payload) != _PROGRAM_SNAPSHOT_FIELDS:
        raise ValueError("metabolic cycle program fields changed")
    if payload.get("version") != VERSION:
        raise ValueError("unexpected metabolic cycle program version")
    if (
        payload.get("status")
        != "four_cycle_dependency_surface_ready_quantitative_execution_blocked"
        or payload.get("date_verified") != DATE_VERIFIED
        or payload.get("scientific_authority") is not False
        or payload.get("automatic_parameter_activation") is not False
        or payload.get("automatic_state_coupling") is not False
        or payload.get("policy") != _POLICY
    ):
        raise ValueError("metabolic cycle program escaped fail-closed policy")
    manifest = load_metabolic_cycle_manifest()
    manifest_identity = payload.get("manifest")
    if (
        not isinstance(manifest_identity, Mapping)
        or frozenset(manifest_identity) != _MANIFEST_IDENTITY_FIELDS
        or manifest_identity.get("path")
        != str(MANIFEST_PATH.relative_to(REPOSITORY_ROOT))
        or manifest_identity.get("sha256") != _sha256(MANIFEST_PATH)
        or manifest_identity.get("schema_version") != SCHEMA_VERSION
        or manifest_identity.get("program_id") != PROGRAM_ID
        or payload.get("date_verified") != manifest["date_verified"]
    ):
        raise ValueError("metabolic cycle program manifest identity changed")

    expected_gate_assessments = _build_gate_assessments(tuple(manifest["cycles"]))

    cycles = payload.get("cycles")
    edges = payload.get("shared_edges")
    summary = payload.get("summary")
    if (
        not isinstance(cycles, (list, tuple))
        or not isinstance(edges, (list, tuple))
        or not isinstance(summary, Mapping)
    ):
        raise ValueError("metabolic cycle program is malformed")
    if tuple(item.get("id") for item in cycles if isinstance(item, Mapping)) != CYCLE_IDS:
        raise ValueError("metabolic cycle program cycle identities changed")
    if tuple(item.get("id") for item in edges if isinstance(item, Mapping)) != EDGE_IDS:
        raise ValueError("metabolic cycle program edge identities changed")

    manifest_by_cycle = {item["id"]: item for item in manifest["cycles"]}
    gate_count = 0
    satisfied_gate_count = 0
    for cycle in cycles:
        if not isinstance(cycle, Mapping):
            raise ValueError("metabolic cycle record is malformed")
        cycle_id = str(cycle["id"])
        manifest_cycle = manifest_by_cycle[cycle_id]
        if frozenset(cycle) != _CYCLE_SNAPSHOT_FIELDS or (
            cycle.get("label") != manifest_cycle["label"]
            or cycle.get("scope") != manifest_cycle["scope"]
            or tuple(cycle.get("target_components", ()))
            != tuple(manifest_cycle["target_components"])
            or tuple(cycle.get("surface_ids", ()))
            != tuple(manifest_cycle["surface_ids"])
        ):
            raise ValueError(f"{cycle_id}: snapshot contract changed")
        gates = cycle.get("gates")
        if not isinstance(gates, (list, tuple)):
            raise ValueError(f"{cycle_id}: gate assessments are missing")
        expected_gate_contract = tuple(
            (gate_id, stage)
            for stage in STAGES
            for gate_id in manifest_cycle["gate_ids"][stage]
        )
        if tuple(
            (gate.get("id"), gate.get("stage"))
            for gate in gates
            if isinstance(gate, Mapping)
        ) != expected_gate_contract:
            raise ValueError(f"{cycle_id}: gate assessments changed")
        for gate in gates:
            if (
                not isinstance(gate, Mapping)
                or frozenset(gate) != _GATE_ASSESSMENT_FIELDS
            ):
                raise ValueError(f"{cycle_id}: malformed gate assessment")
            satisfied = gate.get("satisfied")
            if not isinstance(satisfied, bool):
                raise ValueError(f"{cycle_id}: gate state must be boolean")
            if (
                not isinstance(gate.get("observed"), Mapping)
                or not isinstance(gate.get("requirement"), str)
                or not gate.get("requirement")
                or not isinstance(gate.get("evidence_surface"), str)
                or not gate.get("evidence_surface")
                or (satisfied and gate.get("blocker") is not None)
                or (
                    not satisfied
                    and (
                        not isinstance(gate.get("blocker"), str)
                        or not gate.get("blocker")
                    )
                )
            ):
                raise ValueError(f"{cycle_id}: invalid gate assessment semantics")
            expected_gate = expected_gate_assessments[str(gate["id"])].to_dict()
            if _canonical_json(gate) != _canonical_json(expected_gate):
                raise ValueError(
                    f"{cycle_id}: gate assessment diverges from current evidence"
                )
        quantitative = all(
            gate["satisfied"]
            for gate in gates
            if gate["stage"] == "quantitative_execution"
        )
        predictive = quantitative and all(
            gate["satisfied"] for gate in gates if gate["stage"] == "prediction"
        )
        runtime = predictive and all(
            gate["satisfied"]
            for gate in gates
            if gate["stage"] == "runtime_coupling"
        )
        if (
            cycle.get("quantitative_execution_ready") is not quantitative
            or cycle.get("predictive_ready") is not predictive
            or cycle.get("runtime_coupling_ready") is not runtime
            or tuple(cycle.get("blockers", ()))
            != tuple(gate["blocker"] for gate in gates if not gate["satisfied"])
        ):
            raise ValueError(f"{cycle_id}: readiness is inconsistent with its gates")
        gate_count += len(gates)
        satisfied_gate_count += sum(bool(gate["satisfied"]) for gate in gates)

    coupled_edge_count = 0
    satisfied_operator_count = 0
    operator_count = 0
    edge_by_id: dict[str, Mapping[str, object]] = {}
    for edge, manifest_edge in zip(edges, manifest["shared_edges"], strict=True):
        if not isinstance(edge, Mapping):
            raise ValueError("metabolic edge record is malformed")
        edge_id = str(edge["id"])
        if (
            frozenset(edge) != _EDGE_SNAPSHOT_FIELDS
            or edge.get("direction") != manifest_edge["direction"]
        ):
            raise ValueError(f"{edge_id}: edge snapshot contract changed")
        edge_by_id[edge_id] = edge
        operators = edge.get("operators")
        if not isinstance(operators, (list, tuple)) or tuple(
            operator.get("id")
            for operator in operators
            if isinstance(operator, Mapping)
        ) != tuple(manifest_edge["required_operator_ids"]):
            raise ValueError(f"{edge_id}: coupling operators changed")
        if tuple(edge.get("endpoint_cycle_ids", ())) != tuple(
            manifest_edge["endpoint_cycle_ids"]
        ) or tuple(edge.get("shared_state_ids", ())) != tuple(
            manifest_edge["shared_state_ids"]
        ):
            raise ValueError(f"{edge_id}: edge contract changed")
        expected_operators = _edge_operator_assessments(manifest_edge)
        if _canonical_json(operators) != _canonical_json(expected_operators):
            raise ValueError(
                f"{edge_id}: coupling operators diverge from current evidence"
            )
        for operator in operators:
            if (
                not isinstance(operator, Mapping)
                or frozenset(operator) != _EDGE_OPERATOR_FIELDS
                or not isinstance(operator.get("satisfied"), bool)
                or not isinstance(operator.get("requirement"), str)
                or not operator.get("requirement")
            ):
                raise ValueError(f"{edge_id}: malformed coupling operator")
            if operator["satisfied"] and operator.get("blocker") is not None:
                raise ValueError(f"{edge_id}: satisfied operator carries a blocker")
            if not operator["satisfied"] and not operator.get("blocker"):
                raise ValueError(f"{edge_id}: blocked operator lacks a blocker")
        ready = all(operator["satisfied"] for operator in operators)
        if (
            edge.get("coupling_ready") is not ready
            or edge.get("automatic_state_coupling") is not False
            or tuple(edge.get("blockers", ()))
            != tuple(
                operator["blocker"]
                for operator in operators
                if not operator["satisfied"]
            )
        ):
            raise ValueError(f"{edge_id}: coupling readiness escaped its operators")
        operator_count += len(operators)
        satisfied_operator_count += sum(
            bool(operator["satisfied"]) for operator in operators
        )
        coupled_edge_count += int(ready)

    for cycle in cycles:
        incident_ids = tuple(cycle.get("incident_edge_ids", ()))
        expected_incident = tuple(
            edge["id"]
            for edge in edges
            if cycle["id"] in edge["endpoint_cycle_ids"]
        )
        if incident_ids != expected_incident:
            raise ValueError(f"{cycle['id']}: incident edge inventory changed")
        cross_ready = bool(
            cycle["runtime_coupling_ready"]
            and incident_ids
            and all(edge_by_id[edge_id]["coupling_ready"] for edge_id in incident_ids)
        )
        if cycle.get("cross_cycle_runtime_ready") is not cross_ready:
            raise ValueError(f"{cycle['id']}: cross-cycle readiness is inconsistent")

    expected_summary = {
        "cycle_count": len(cycles),
        "cycle_with_structural_surface_count": sum(
            any(gate["satisfied"] for gate in cycle["gates"]) for cycle in cycles
        ),
        "gate_count": gate_count,
        "satisfied_gate_count": satisfied_gate_count,
        "quantitative_execution_ready_cycle_count": sum(
            bool(cycle["quantitative_execution_ready"]) for cycle in cycles
        ),
        "predictive_ready_cycle_count": sum(
            bool(cycle["predictive_ready"]) for cycle in cycles
        ),
        "runtime_coupling_ready_cycle_count": sum(
            bool(cycle["runtime_coupling_ready"]) for cycle in cycles
        ),
        "cross_cycle_runtime_ready_cycle_count": sum(
            bool(cycle["cross_cycle_runtime_ready"]) for cycle in cycles
        ),
        "shared_edge_count": len(edges),
        "edge_operator_count": operator_count,
        "satisfied_edge_operator_count": satisfied_operator_count,
        "coupled_edge_count": coupled_edge_count,
        "automatic_parameter_activation_count": 0,
        "automatic_state_coupling_count": 0,
    }
    if dict(summary) != expected_summary:
        raise ValueError("metabolic cycle program summary is stale")
    if (
        summary["cycle_count"] != 4
        or summary["cycle_with_structural_surface_count"] != 4
        or summary["quantitative_execution_ready_cycle_count"] != 0
        or summary["predictive_ready_cycle_count"] != 0
        or summary["runtime_coupling_ready_cycle_count"] != 0
        or summary["cross_cycle_runtime_ready_cycle_count"] != 0
        or summary["shared_edge_count"] != 5
        or summary["coupled_edge_count"] != 0
    ):
        raise ValueError("metabolic cycle program current authority boundary changed")


def assert_metabolic_cycle_execution_allowed(
    cycle_id: str,
    *,
    stage: str = "quantitative_execution",
    program: Mapping[str, object] | None = None,
) -> Mapping[str, object]:
    if stage not in STAGES:
        raise ValueError(f"unsupported metabolic execution stage: {stage}")
    checked = program or hepatocyte_metabolic_cycle_program_snapshot()
    validate_hepatocyte_metabolic_cycle_program(checked)
    cycle = next(
        (item for item in checked["cycles"] if item["id"] == cycle_id),
        None,
    )
    if cycle is None:
        raise KeyError(cycle_id)
    readiness_field = {
        "quantitative_execution": "quantitative_execution_ready",
        "prediction": "predictive_ready",
        "runtime_coupling": "cross_cycle_runtime_ready",
    }[stage]
    if not cycle[readiness_field]:
        stage_index = STAGES.index(stage)
        blockers = [
            gate["blocker"]
            for gate in cycle["gates"]
            if STAGES.index(gate["stage"]) <= stage_index and not gate["satisfied"]
        ]
        if stage == "runtime_coupling":
            incident = set(cycle["incident_edge_ids"])
            blockers.extend(
                blocker
                for edge in checked["shared_edges"]
                if edge["id"] in incident
                for blocker in edge["blockers"]
            )
        raise MetabolicCycleProgramError(
            f"{cycle_id}:{stage} blocked: " + "; ".join(blockers)
        )
    return cycle


def assert_metabolic_edge_coupling_allowed(
    edge_id: str,
    *,
    program: Mapping[str, object] | None = None,
) -> Mapping[str, object]:
    checked = program or hepatocyte_metabolic_cycle_program_snapshot()
    validate_hepatocyte_metabolic_cycle_program(checked)
    edge = next(
        (item for item in checked["shared_edges"] if item["id"] == edge_id),
        None,
    )
    if edge is None:
        raise KeyError(edge_id)
    if not edge["coupling_ready"]:
        raise MetabolicCycleProgramError(
            f"{edge_id}:coupling blocked: " + "; ".join(edge["blockers"])
        )
    return edge


__all__ = [
    "CYCLE_IDS",
    "EDGE_IDS",
    "MANIFEST_PATH",
    "MetabolicCycleProgramError",
    "assert_metabolic_cycle_execution_allowed",
    "assert_metabolic_edge_coupling_allowed",
    "hepatocyte_metabolic_cycle_program_snapshot",
    "load_metabolic_cycle_manifest",
    "validate_hepatocyte_metabolic_cycle_program",
    "validate_metabolic_cycle_manifest",
]
