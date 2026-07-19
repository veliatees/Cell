"""Fail-closed calibration and validation gate for hepatocyte energy/redox.

The structural contract separates cytosolic, mitochondrial, ER and peroxisomal
pools. The executable legacy fixtures do not. This gate audits every numerical
reaction in those fixtures, preserves aggregate human observations in their
original assay space and prevents calibration or state coupling until the
missing compartment-resolved evidence is supplied.
"""

from __future__ import annotations

from dataclasses import dataclass

from cell_engine.core.serialization import to_plain
from cell_engine.quantitative.compartmental_energy_redox import (
    AggregateEnergyRedoxObservation,
    build_compartmental_energy_redox_contract,
)
from cell_engine.stochastic.bioenergetics import build_phh_atp_turnover_network
from cell_engine.stochastic.integrated_cell import INTEGRATED_VOLUME_L
from cell_engine.stochastic.oxphos import build_oxphos_network
from cell_engine.stochastic.redox import build_redox_network
from cell_engine.validation.reaction_authority import audit_reaction_network


VERSION = "energy_redox_calibration_validation_gate_v1"


@dataclass(frozen=True)
class EnergyRedoxReactionEligibility:
    network_id: str
    reaction_id: str
    current_authority: str
    parameter_provenance_documented: bool
    compartment_context_match: bool
    aggregate_observation_identifies_rate: bool
    fit_allowed: bool
    quantitative_validation_allowed: bool
    predictive_execution_allowed: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class EnergyRedoxObservationUseAudit:
    observation_id: str
    target: str
    source_id: str
    original_unit: str
    permitted_role: str
    aggregate_reference_allowed: bool
    same_assay_comparison_allowed: bool
    compartment_initialization_allowed: bool
    kinetic_parameter_fit_allowed: bool
    independent_heldout_eligible: bool
    reason: str


@dataclass(frozen=True)
class EnergyRedoxValidationRequirement:
    id: str
    satisfied: bool
    requirement: str
    current_evidence: str


@dataclass(frozen=True)
class EnergyRedoxCalibrationValidationGate:
    version: str
    status: str
    reaction_fit_eligibility: tuple[EnergyRedoxReactionEligibility, ...]
    observation_use_audit: tuple[EnergyRedoxObservationUseAudit, ...]
    validation_requirements: tuple[EnergyRedoxValidationRequirement, ...]
    structural_topology_ready: bool
    aggregate_reference_ready: bool
    compartment_state_initialization_ready: bool
    same_assay_descriptive_comparison_ready: bool
    reaction_parameter_calibration_ready: bool
    donor_disjoint_split_ready: bool
    independent_heldout_validation_ready: bool
    uncertainty_qualified_pass_fail_ready: bool
    predictive_parameter_activation_allowed: bool
    automatic_state_coupling: bool
    predictive_ready: bool
    source_ids: tuple[str, ...]
    policy: str

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


class EnergyRedoxCalibrationError(RuntimeError):
    """Raised when an unqualified energy/redox fit or activation is requested."""


def _reaction_eligibility() -> tuple[EnergyRedoxReactionEligibility, ...]:
    networks = (
        (
            "legacy_atp_turnover_fixture",
            build_phh_atp_turnover_network(INTEGRATED_VOLUME_L),
        ),
        ("legacy_redox_fixture", build_redox_network(INTEGRATED_VOLUME_L)),
        ("legacy_oxphos_fixture", build_oxphos_network()),
    )
    result: list[EnergyRedoxReactionEligibility] = []
    for network_id, network in networks:
        audit = audit_reaction_network(
            network,
            network_id=network_id,
            context_match_confirmed=False,
            context_description=(
                "Legacy software fixture with shared pools and no matched "
                "compartment-resolved healthy-PHH protocol."
            ),
        )
        for reaction in audit.reactions:
            result.append(
                EnergyRedoxReactionEligibility(
                    network_id=network_id,
                    reaction_id=reaction.reaction_id,
                    current_authority=reaction.authority,
                    parameter_provenance_documented=reaction.parameter_provenance_complete,
                    compartment_context_match=False,
                    aggregate_observation_identifies_rate=False,
                    fit_allowed=False,
                    quantitative_validation_allowed=False,
                    predictive_execution_allowed=False,
                    blockers=tuple(
                        dict.fromkeys(
                            (
                                *reaction.blockers,
                                "The runtime collapses one or more distinct organelle pools.",
                                "Available aggregate observations do not identify this reaction rate.",
                                "No matched healthy-PHH compartment trajectory and held-out result exist.",
                            )
                        )
                    ),
                )
            )
    return tuple(result)


def _observation_use(
    observations: tuple[AggregateEnergyRedoxObservation, ...],
) -> tuple[EnergyRedoxObservationUseAudit, ...]:
    result: list[EnergyRedoxObservationUseAudit] = []
    for observation in observations:
        is_exchange = observation.id == "human_liver_apparent_atp_synthesis"
        result.append(
            EnergyRedoxObservationUseAudit(
                observation_id=observation.id,
                target=observation.target,
                source_id=observation.source_id,
                original_unit=observation.unit,
                permitted_role=observation.permitted_use,
                aggregate_reference_allowed=True,
                same_assay_comparison_allowed=is_exchange,
                compartment_initialization_allowed=False,
                kinetic_parameter_fit_allowed=False,
                independent_heldout_eligible=False,
                reason=(
                    "The observation can test an exact same-assay Pi-to-ATP exchange output, "
                    "but it cannot identify mitochondrial ATP synthesis, ATP demand or a rate constant."
                    if is_exchange
                    else "The whole-liver or original-denominator observation cannot be allocated among organelles or treated as a kinetic trajectory."
                ),
            )
        )
    return tuple(result)


def _requirements() -> tuple[EnergyRedoxValidationRequirement, ...]:
    return (
        EnergyRedoxValidationRequirement(
            "matched_human_phh_context",
            False,
            "Healthy primary-human-hepatocyte measurements must match donor state, culture format, oxygen, substrate and hormone context.",
            "Current evidence mixes whole liver, isolated protein, mammalian cell lines and PHH total proteomics.",
        ),
        EnergyRedoxValidationRequirement(
            "compartment_volumes",
            False,
            "Cytosol, mitochondrial matrix/intermembrane space, ER lumen and peroxisomal volumes must be measured or source-qualified.",
            "No matched healthy-PHH organelle-volume set is curated.",
        ),
        EnergyRedoxValidationRequirement(
            "compartment_initial_states",
            False,
            "ATP/ADP/Pi, NAD(H), NADP(H), GSH/GSSG, oxygen and ROS initial states must retain compartment and uncertainty.",
            "Available adenylate, NAD+ and glutathione observations are aggregate and cannot be partitioned.",
        ),
        EnergyRedoxValidationRequirement(
            "matched_ocr_atp_linked_respiration",
            False,
            "OCR, ATP-linked respiration, proton leak and viability must share an exact PHH denominator and time axis.",
            "A PHH OCR method is identified, but no exact denominator-matched numeric dataset is curated.",
        ),
        EnergyRedoxValidationRequirement(
            "compartment_redox_trajectories",
            False,
            "Compartment-targeted sensors or isotope tracing must resolve NADPH and glutathione pathway dynamics.",
            "Current sources establish compartment topology, not healthy-PHH trajectories.",
        ),
        EnergyRedoxValidationRequirement(
            "localized_active_protein_abundance",
            False,
            "Transporter/enzyme abundance must be localized and corrected for active fraction and assembled complex.",
            "Seven-donor PHH proteomics supplies total protein groups per reference nucleus only.",
        ),
        EnergyRedoxValidationRequirement(
            "mechanism_identifying_perturbations",
            False,
            "Perturbations must distinguish ETC, ATP synthase, ANT, VDAC, phosphate transport and antioxidant routes.",
            "The aggregate observations cannot identify route-specific parameters.",
        ),
        EnergyRedoxValidationRequirement(
            "donor_disjoint_partition",
            False,
            "Calibration and held-out validation must use disjoint human donors declared before fitting.",
            "No donor-resolved energy/redox trajectory set is loaded.",
        ),
        EnergyRedoxValidationRequirement(
            "uncertainty_and_heldout_result",
            False,
            "A frozen model, measurement operator, covariance-aware acceptance rule and independent held-out result are required.",
            "No qualified energy/redox prediction artifact or held-out result exists.",
        ),
    )


def build_energy_redox_calibration_validation_gate() -> EnergyRedoxCalibrationValidationGate:
    contract = build_compartmental_energy_redox_contract()
    state = EnergyRedoxCalibrationValidationGate(
        version=VERSION,
        status="structural_reference_ready_numerical_calibration_and_prediction_blocked",
        reaction_fit_eligibility=_reaction_eligibility(),
        observation_use_audit=_observation_use(contract.aggregate_observations),
        validation_requirements=_requirements(),
        structural_topology_ready=True,
        aggregate_reference_ready=True,
        compartment_state_initialization_ready=False,
        same_assay_descriptive_comparison_ready=False,
        reaction_parameter_calibration_ready=False,
        donor_disjoint_split_ready=False,
        independent_heldout_validation_ready=False,
        uncertainty_qualified_pass_fail_ready=False,
        predictive_parameter_activation_allowed=False,
        automatic_state_coupling=False,
        predictive_ready=False,
        source_ids=contract.source_ids,
        policy=(
            "Structural topology and denominator-preserved aggregate observations may be audited. "
            "No legacy fixture value may be fitted, validated, coupled to cell state or presented "
            "as predictive until every compartment, identifiability and held-out requirement passes."
        ),
    )
    validate_energy_redox_calibration_validation_gate(state)
    return state


def validate_energy_redox_calibration_validation_gate(
    state: EnergyRedoxCalibrationValidationGate,
) -> None:
    if state.version != VERSION:
        raise ValueError("energy/redox calibration gate version changed")
    if len(state.reaction_fit_eligibility) != 9:
        raise ValueError("energy/redox gate must audit all nine legacy fixture reactions")
    reaction_keys = {
        (item.network_id, item.reaction_id) for item in state.reaction_fit_eligibility
    }
    if len(reaction_keys) != 9:
        raise ValueError("energy/redox reaction audit contains duplicate reactions")
    if any(
        item.current_authority != "placeholder"
        or not item.parameter_provenance_documented
        or item.compartment_context_match
        or item.aggregate_observation_identifies_rate
        or item.fit_allowed
        or item.quantitative_validation_allowed
        or item.predictive_execution_allowed
        for item in state.reaction_fit_eligibility
    ):
        raise ValueError("a legacy energy/redox fixture exceeded placeholder authority")
    if len(state.observation_use_audit) != 7:
        raise ValueError("energy/redox observation-use audit is incomplete")
    if sum(item.same_assay_comparison_allowed for item in state.observation_use_audit) != 1:
        raise ValueError("only the apparent exchange observation has a same-assay comparison role")
    if any(
        not item.aggregate_reference_allowed
        or item.compartment_initialization_allowed
        or item.kinetic_parameter_fit_allowed
        or item.independent_heldout_eligible
        for item in state.observation_use_audit
    ):
        raise ValueError("aggregate energy/redox evidence was promoted beyond its assay")
    expected_requirements = {
        "matched_human_phh_context",
        "compartment_volumes",
        "compartment_initial_states",
        "matched_ocr_atp_linked_respiration",
        "compartment_redox_trajectories",
        "localized_active_protein_abundance",
        "mechanism_identifying_perturbations",
        "donor_disjoint_partition",
        "uncertainty_and_heldout_result",
    }
    if {item.id for item in state.validation_requirements} != expected_requirements:
        raise ValueError("energy/redox validation requirement registry changed")
    if any(item.satisfied for item in state.validation_requirements):
        raise ValueError("an unmet energy/redox requirement was marked satisfied")
    if (
        not state.structural_topology_ready
        or not state.aggregate_reference_ready
        or state.compartment_state_initialization_ready
        or state.same_assay_descriptive_comparison_ready
        or state.reaction_parameter_calibration_ready
        or state.donor_disjoint_split_ready
        or state.independent_heldout_validation_ready
        or state.uncertainty_qualified_pass_fail_ready
        or state.predictive_parameter_activation_allowed
        or state.automatic_state_coupling
        or state.predictive_ready
    ):
        raise ValueError("energy/redox calibration gate exceeded current evidence")


def assert_energy_redox_reaction_fit_allowed(
    reaction_id: str,
    gate: EnergyRedoxCalibrationValidationGate | None = None,
) -> EnergyRedoxReactionEligibility:
    checked = gate or build_energy_redox_calibration_validation_gate()
    matches = tuple(
        item for item in checked.reaction_fit_eligibility
        if item.reaction_id == reaction_id
    )
    if not matches:
        raise KeyError(reaction_id)
    if len(matches) > 1:
        raise EnergyRedoxCalibrationError(
            f"{reaction_id} is ambiguous across legacy fixture networks"
        )
    record = matches[0]
    if not record.fit_allowed:
        raise EnergyRedoxCalibrationError(
            f"{reaction_id}: " + "; ".join(record.blockers)
        )
    return record


def assert_energy_redox_predictive_activation(
    gate: EnergyRedoxCalibrationValidationGate | None = None,
) -> EnergyRedoxCalibrationValidationGate:
    checked = gate or build_energy_redox_calibration_validation_gate()
    if not checked.predictive_parameter_activation_allowed:
        missing = tuple(
            item.requirement for item in checked.validation_requirements
            if not item.satisfied
        )
        raise EnergyRedoxCalibrationError(
            "predictive energy/redox activation blocked: " + "; ".join(missing)
        )
    return checked


def energy_redox_calibration_validation_snapshot() -> dict[str, object]:
    state = build_energy_redox_calibration_validation_gate()
    payload = state.to_dict()
    payload["summary"] = {
        "audited_legacy_reaction_count": len(state.reaction_fit_eligibility),
        "placeholder_reaction_count": sum(
            item.current_authority == "placeholder"
            for item in state.reaction_fit_eligibility
        ),
        "fit_eligible_reaction_count": sum(
            item.fit_allowed for item in state.reaction_fit_eligibility
        ),
        "aggregate_observation_count": len(state.observation_use_audit),
        "same_assay_observation_count": sum(
            item.same_assay_comparison_allowed
            for item in state.observation_use_audit
        ),
        "satisfied_validation_requirement_count": sum(
            item.satisfied for item in state.validation_requirements
        ),
        "independent_heldout_result_count": 0,
        "activated_parameter_count": 0,
    }
    return payload
