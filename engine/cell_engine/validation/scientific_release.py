"""Fail-closed release checks for the authoritative Healthy PHH baseline."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal

from cell_engine.quantitative.phh_profiles import PHH_NUTRITIONAL_PROFILES
from cell_engine.quantitative.phh_state import build_quantitative_phh_state, validate_quantitative_phh_state
from cell_engine.quantitative.zonation import build_human_hepatocyte_zonation, validate_human_hepatocyte_zonation
from cell_engine.quantitative.homeostasis_v3 import build_human_nutritional_homeostasis_v3, validate_human_nutritional_homeostasis_v3
from cell_engine.quantitative.endocrine import build_human_endocrine_context, validate_human_endocrine_context
from cell_engine.quantitative.published_glucose_model import (
    build_published_hepatic_glucose_context,
    validate_published_hepatic_glucose_context,
)
from cell_engine.quantitative.published_glucose_lineage import (
    load_lineage_reproduction,
    validate_lineage_reproduction,
)
from cell_engine.quantitative.published_glucose_external_validation import (
    build_published_glucose_external_validation,
    validate_published_glucose_external_validation,
)
from cell_engine.quantitative.human_validation_protocol import (
    build_human_mixed_meal_validation_protocol,
    validate_human_mixed_meal_validation_protocol,
)
from cell_engine.quantitative.phh_glucose_validation import (
    load_healthy_phh_glucose_validation,
    validate_healthy_phh_glucose_validation,
)
from cell_engine.quantitative.phh_spheroid_protocol import (
    build_phh_spheroid_validation_protocol,
    validate_phh_spheroid_validation_protocol,
)
from cell_engine.quantitative.phh_glucose_observability import (
    build_phh_glucose_observability,
    validate_phh_glucose_observability,
)
from cell_engine.quantitative.glucose_homeostasis_contract import (
    build_exact_glucose_homeostasis_contract,
    validate_exact_glucose_homeostasis_contract,
)
from cell_engine.quantitative.glucose_open_system import (
    build_glucose_open_system_program,
    validate_glucose_open_system_program,
)
from cell_engine.quantitative.phh_albumin_secretion import (
    build_phh_albumin_secretion,
    validate_phh_albumin_secretion,
)
from cell_engine.quantitative.phh_cyp_function import (
    build_phh_cyp_function,
    validate_phh_cyp_function,
)
from cell_engine.quantitative.phh_biliary_excretion import (
    build_phh_biliary_excretion,
    validate_phh_biliary_excretion,
)
from cell_engine.quantitative.phh_identity_heterogeneity import (
    build_phh_identity_heterogeneity,
    validate_phh_identity_heterogeneity,
)
from cell_engine.quantitative.phh_proteome_budget import (
    build_phh_proteome_budget,
    validate_phh_proteome_budget,
)
from cell_engine.quantitative.phh_transporter_inventory import (
    build_phh_transporter_inventory,
    validate_phh_transporter_inventory,
)
from cell_engine.quantitative.phh_protein_functional_evidence import (
    build_phh_protein_functional_evidence,
    validate_phh_protein_functional_evidence,
)
from cell_engine.quantitative.human_sch_bile_acids import (
    build_human_sch_bile_acids,
    validate_human_sch_bile_acids,
)
from cell_engine.stochastic.bioenergetics import build_phh_atp_turnover_network
from cell_engine.stochastic.integrated_cell import (
    INTEGRATED_VOLUME_L,
    build_integrated_hepatocyte_network,
)
from cell_engine.stochastic.signaling import HormoneState
from cell_engine.stochastic.sinusoid import (
    build_sinusoid_boundary_network,
    build_sinusoid_coupled_homeostasis,
    validate_sinusoid_coupled_homeostasis,
)
from cell_engine.validation.phh_baseline import load_phh_baseline
from cell_engine.validation.model_audit import MODEL_SURFACE_AUDIT
from cell_engine.validation.reaction_authority import audit_reaction_network
from cell_engine.validation.kinetic_transfer import (
    build_kinetic_transfer_audit,
    validate_kinetic_transfer_audit,
)
from cell_engine.validation.hepatic_flux import (
    build_unified_nutritional_context,
    load_hepatic_flux_evidence,
    validate_unified_nutritional_context,
)
from cell_engine.validation.evidence_intake import evidence_intake_snapshot
from cell_engine.io.brian2 import brian2_communication_snapshot
from cell_engine.ml.generative import (
    build_generative_modeling_boundary,
    validate_generative_modeling_boundary,
)
from cell_engine.multicell.communication import (
    build_hepatocyte_communication_system,
    validate_hepatocyte_communication_system,
)
from cell_engine.multicell.spatial_world import (
    build_reference_hepatocyte_pair_world,
    validate_spatial_world,
)


ReleaseTarget = Literal["research_preview", "predictive"]


@dataclass(frozen=True)
class ScientificReleaseGate:
    target: ReleaseTarget
    passed: bool
    checks: tuple[str, ...]
    blockers: tuple[str, ...]


def evaluate_scientific_release(target: ReleaseTarget = "research_preview") -> ScientificReleaseGate:
    registry = load_phh_baseline()
    checks: list[str] = []
    blockers: list[str] = []
    published_model_context = None
    published_model_lineage = None
    published_model_external_validation = None
    phh_glucose_validation = None
    phh_spheroid_protocol = None
    phh_glucose_observability = None
    exact_glucose_contract = None
    glucose_open_system = None
    phh_albumin_secretion = None
    phh_cyp_function = None
    phh_biliary_excretion = None
    phh_identity_heterogeneity = None
    phh_proteome_budget = None
    phh_transporter_inventory = None
    phh_protein_functional_evidence = None
    human_sch_bile_acids = None
    integrated_reaction_authority = None
    kinetic_transfer = None

    if registry.metabolic_pool_initialization_ready:
        checks.append("source-traceable metabolic pool initialization")
    else:
        blockers.append("metabolic pool initialization is not ready")
    if registry.energy_turnover_ready:
        checks.append("human-liver-anchored apparent ATP turnover")
    else:
        blockers.append("energy turnover is not ready")

    source_ids = set(registry.sources)
    for profile in PHH_NUTRITIONAL_PROFILES.values():
        for species, pool in profile.pools.items():
            if not pool.source_ids or not set(pool.source_ids) <= source_ids:
                blockers.append(f"{profile.id}.{species} lacks registered provenance")

    try:
        quantitative_state = build_quantitative_phh_state()
        validate_quantitative_phh_state(quantitative_state)
        for species, pool in quantitative_state.pools.items():
            if not set(pool.source_ids) <= source_ids:
                blockers.append(f"quantitative_state.{species} lacks registered provenance")
        checks.append("unified quantitative PHH state excludes relative schematic units")
    except ValueError as exc:
        blockers.append(f"invalid unified quantitative PHH state: {exc}")

    try:
        for zone in ("periportal", "midlobular", "pericentral"):
            validate_human_hepatocyte_zonation(build_human_hepatocyte_zonation(zone))
        checks.append("human-specific zonation context cannot apply unmeasured flux or oxygen scaling")
    except ValueError as exc:
        blockers.append(f"invalid human zonation context: {exc}")

    try:
        for zone in ("periportal", "midlobular", "pericentral"):
            validate_sinusoid_coupled_homeostasis(build_sinusoid_coupled_homeostasis(zone))
        checks.append("sinusoid v2 enables sourced perfusion while uncalibrated cell and zonal fluxes fail closed")
    except ValueError as exc:
        blockers.append(f"invalid sinusoid-coupled homeostasis state: {exc}")

    try:
        for zone in ("periportal", "midlobular", "pericentral"):
            validate_human_nutritional_homeostasis_v3(build_human_nutritional_homeostasis_v3(zone))
        checks.append("human mixed-meal trajectory is retained at organ scale and cannot invent per-cell flux")
    except ValueError as exc:
        blockers.append(f"invalid nutritional homeostasis V3 state: {exc}")

    flux_evidence = load_hepatic_flux_evidence()
    if flux_evidence.per_cell_applicable_count:
        blockers.append("organ-scale hepatic flux evidence leaked into per-cell calibration")
    else:
        checks.append("31-record hepatic flux bundle remains organ-scale with per-cell conversion disabled")

    try:
        for profile_id in ("fed_peak", "postabsorptive", "prolonged_fasted"):
            validate_unified_nutritional_context(build_unified_nutritional_context(profile_id))
        checks.append("fed, postabsorptive and prolonged-fast contexts share one fail-closed authority contract")
    except ValueError as exc:
        blockers.append(f"invalid unified nutritional context: {exc}")

    try:
        for profile_id in ("fed_peak", "postabsorptive", "prolonged_fasted"):
            validate_human_endocrine_context(build_human_endocrine_context(profile_id))
        checks.append("measured human endocrine observations are retained while portal receptor and rate coupling fail closed")
    except ValueError as exc:
        blockers.append(f"invalid human endocrine context: {exc}")

    try:
        validate_human_mixed_meal_validation_protocol(build_human_mixed_meal_validation_protocol())
        checks.append("human mixed-meal observations form a scale-matched protocol with no interpolation or invented pass threshold")
    except ValueError as exc:
        blockers.append(f"invalid human mixed-meal validation protocol: {exc}")

    try:
        phh_glucose_validation = load_healthy_phh_glucose_validation()
        validate_healthy_phh_glucose_validation(phh_glucose_validation)
        checks.append(
            "16 mean-plus-SD healthy-PHH spheroid glucose windows and three insulin responses retain exact media, time and denominator semantics"
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        blockers.append(f"invalid healthy-PHH spheroid glucose validation: {exc}")

    try:
        phh_spheroid_protocol = build_phh_spheroid_validation_protocol()
        validate_phh_spheroid_validation_protocol(phh_spheroid_protocol)
        checks.append(
            "PHH spheroid protocol derives 12 non-overlapping cumulative mean targets, keeps four overlap audits descriptive, and blocks unidentified concentration reconstruction"
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        blockers.append(f"invalid exact PHH spheroid validation protocol: {exc}")

    try:
        phh_glucose_observability = build_phh_glucose_observability()
        validate_phh_glucose_observability(phh_glucose_observability)
        checks.append(
            "PHH cumulative model outputs map exactly to 16 signed assay windows while nine mechanism-specific fluxes and all kinetic fits remain unidentified"
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        blockers.append(f"invalid PHH glucose observability gate: {exc}")

    try:
        exact_glucose_contract = build_exact_glucose_homeostasis_contract()
        validate_exact_glucose_homeostasis_contract(exact_glucose_contract)
        checks.append(
            "official glucose-model topology is preserved as a non-executable 52-species, five-compartment, 36-reaction contract while split pools, duplicated export, lumping and compartment collapse remain blocked"
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        blockers.append(f"invalid exact glucose-homeostasis structural contract: {exc}")

    try:
        glucose_open_system = build_glucose_open_system_program()
        validate_glucose_open_system_program(glucose_open_system)
        checks.append(
            "physiological sinusoid and finite PHH spheroid boundaries remain non-interchangeable, with an exact signed 12-window input to 16-window assay bridge and no invented volume"
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        blockers.append(f"invalid glucose open-system and exact-assay bridge: {exc}")

    try:
        phh_albumin_secretion = build_phh_albumin_secretion()
        validate_phh_albumin_secretion(phh_albumin_secretion)
        checks.append(
            "six-batch PHH albumin ELISA evidence maps through an exact mature-protein mass operator while five hidden secretory rates remain unidentified"
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        blockers.append(f"invalid PHH albumin-secretion observability gate: {exc}")

    try:
        phh_cyp_function = build_phh_cyp_function()
        validate_phh_cyp_function(phh_cyp_function)
        checks.append(
            "72 batch-resolved PHH CYP SCR/MFR means remain same-format diagnostics while censored records and hidden kinetics fail closed"
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        blockers.append(f"invalid PHH CYP-function observability gate: {exc}")

    try:
        phh_biliary_excretion = build_phh_biliary_excretion()
        validate_phh_biliary_excretion(phh_biliary_excretion)
        checks.append(
            "five batch-resolved d8-TCA BEI outputs retain the paired-condition operator while transporter and canalicular-geometry coupling fail closed"
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        blockers.append(f"invalid PHH biliary-excretion observability gate: {exc}")

    try:
        phh_identity_heterogeneity = build_phh_identity_heterogeneity()
        validate_phh_identity_heterogeneity(phh_identity_heterogeneity)
        checks.append(
            "six-batch FACS and 54,134-cell scRNA composition records remain separate product-level identity observables with one-cell initialization blocked"
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        blockers.append(f"invalid PHH identity/heterogeneity observability gate: {exc}")

    try:
        phh_proteome_budget = build_phh_proteome_budget()
        validate_phh_proteome_budget(phh_proteome_budget)
        checks.append(
            "seven-donor PHH total-protein and compartment protein-mass references are absolute while geometry, crowding and proteostasis dynamics fail closed"
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        blockers.append(f"invalid PHH absolute proteome budget: {exc}")

    try:
        phh_transporter_inventory = build_phh_transporter_inventory()
        validate_phh_transporter_inventory(phh_transporter_inventory)
        checks.append(
            "same-cohort BSEP abundance resolves total copies only while MRP2 denominator, surface copies, active fraction and flux remain blocked"
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        blockers.append(f"invalid PHH transporter inventory: {exc}")

    try:
        phh_protein_functional_evidence = build_phh_protein_functional_evidence()
        validate_phh_protein_functional_evidence(phh_protein_functional_evidence)
        checks.append(
            "eight PHH proteins retain seven-donor total abundance, localization identity, "
            "assay kinetics and response timepoints while active copies and whole-cell rates fail closed"
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        blockers.append(f"invalid PHH protein-functional evidence: {exc}")

    try:
        human_sch_bile_acids = build_human_sch_bile_acids()
        validate_human_sch_bile_acids(human_sch_bile_acids)
        checks.append(
            "four-donor human SCH Table 4 bile-acid compartments retain source aggregation, censoring and culture-context boundaries"
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        blockers.append(f"invalid human SCH bile-acid compartment reference: {exc}")

    evidence_intake = evidence_intake_snapshot()
    if evidence_intake["automatic_parameter_activation"] or evidence_intake["authoritative_coupling_enabled"]:
        blockers.append("external evidence intake attempted to activate an unreviewed model surface")
    elif evidence_intake["status"] == "rejected_invalid_external_evidence_bundle":
        blockers.append("external PHH evidence bundle failed structural validation")
    else:
        checks.append("external PHH evidence intake is fail-closed and requires manual primary-source curation")

    try:
        for profile_id in ("fed_peak", "postabsorptive", "prolonged_fasted"):
            context = build_published_hepatic_glucose_context(profile_id)
            validate_published_hepatic_glucose_context(context)
            if profile_id == "postabsorptive":
                published_model_context = context
        checks.append("published hepatic glucose model is checksum-audited and quarantined as a non-authoritative shadow prediction")
    except (OSError, ValueError) as exc:
        blockers.append(f"invalid published hepatic glucose shadow model: {exc}")

    try:
        published_model_lineage = load_lineage_reproduction()
        validate_lineage_reproduction(published_model_lineage)
        checks.append(
            "legacy author-model lineage reproduces 5 of 5 reported targets under recovered repository conditions while exact publication equivalence remains unresolved"
        )
    except (OSError, ValueError) as exc:
        blockers.append(f"invalid published hepatic glucose lineage audit: {exc}")

    try:
        published_model_external_validation = build_published_glucose_external_validation()
        validate_published_glucose_external_validation(published_model_external_validation)
        checks.append("published glucose shadow has one unit-matched contextual human HGO comparison plus 16 blocked PHH targets with no pass claim")
    except (OSError, ValueError) as exc:
        blockers.append(f"invalid published glucose external-validation matrix: {exc}")

    try:
        spatial_world = build_reference_hepatocyte_pair_world()
        validate_spatial_world(spatial_world)
        communication = build_hepatocyte_communication_system(spatial_world=spatial_world)
        validate_hepatocyte_communication_system(communication)
        checks.append(
            "measured isolated-PHH size drives authoritative contact geometry; kinematic deformation preserves volume under an explicit cross-system 1% area cap while force, PHH rheology, receptor abundance and kinetics remain closed"
        )
    except ValueError as exc:
        blockers.append(f"invalid hepatocyte communication boundary: {exc}")

    brian2 = brian2_communication_snapshot()
    if brian2["automatic_state_coupling"] or brian2["gate"].execution_ready:
        blockers.append("Brian2 communication backend activated without a calibrated model")
    else:
        checks.append("Brian2 remains an optional pinned executor with no implicit biological model")

    try:
        generative = build_generative_modeling_boundary()
        validate_generative_modeling_boundary(generative)
        checks.append(
            "generative modeling boundary enforces donor-disjoint data and quarantines synthetic cells"
        )
    except ValueError as exc:
        blockers.append(f"invalid generative modeling boundary: {exc}")

    network = build_phh_atp_turnover_network(INTEGRATED_VOLUME_L)
    sinusoid = build_sinusoid_boundary_network("postabsorptive", INTEGRATED_VOLUME_L)
    for reaction in network.reactions + sinusoid.reactions:
        if not reaction.parameter_provenance:
            blockers.append(f"{reaction.id} lacks parameter provenance")
        if any(item.assumption_level == "placeholder" for item in reaction.parameter_provenance):
            blockers.append(f"{reaction.id} contains a placeholder parameter")
    if not blockers:
        checks.append("no placeholder in authoritative PHH, ATP-turnover, or glucose-sinusoid surface")
        checks.append("compartment-correct postabsorptive blood glucose boundary")

    integrated_reaction_authority = audit_reaction_network(
        build_integrated_hepatocyte_network(HormoneState()),
        network_id="integrated_hepatocyte_fuel_network_v1",
        context_match_confirmed=False,
        context_description=(
            "Composed exploratory fuel network without a matched healthy-human PHH "
            "multi-pathway flux protocol."
        ),
    )
    if integrated_reaction_authority.scientific_validation_ready:
        blockers.append("exploratory integrated fuel network was promoted to scientific validation")
    else:
        checks.append(
            "reaction-level authority firewall keeps the integrated fuel network "
            f"exploratory ({integrated_reaction_authority.source_backed_parameterization_count}/"
            f"{integrated_reaction_authority.reaction_count} reactions source-backed)"
        )

    try:
        kinetic_transfer = build_kinetic_transfer_audit()
        validate_kinetic_transfer_audit(kinetic_transfer)
        checks.append(
            "published kinetic-transfer gate covers all active reactions and activates "
            f"{kinetic_transfer.activated_transfer_count} unqualified parameters"
        )
    except ValueError as exc:
        blockers.append(f"invalid published kinetic-transfer audit: {exc}")

    invalid_drivers = tuple(
        surface.id
        for surface in MODEL_SURFACE_AUDIT
        if surface.drives_scientific_validation and surface.status not in ("source_backed", "derived")
    )
    if invalid_drivers:
        blockers.extend(f"unsupported surface drives validation: {surface_id}" for surface_id in invalid_drivers)
    else:
        checks.append("schematic and blocked model surfaces excluded from scientific validation")

    if target == "predictive":
        blockers.extend(registry.blocking_measurements)
        blockers.extend((
            "NADH and GSH/GSSG are not compartment resolved",
            "healthy donor trajectory validation is not complete",
        ))
        if evidence_intake["status"] == "awaiting_external_evidence_bundle":
            blockers.append("requested nine-file healthy-human/PHH evidence bundle is not yet delivered")
        elif evidence_intake["status"] == "structurally_valid_manual_review_required":
            blockers.append("external PHH evidence candidates require primary-source review and curated parameter promotion")
        if published_model_context is None:
            blockers.append("published hepatic glucose model validation context is unavailable")
        else:
            if not published_model_context.gate.publication_reproduction_passed:
                validation = published_model_context.runtime_validation
                blockers.append(
                    "published hepatic glucose shadow model reproduces only "
                    f"{validation['benchmark_pass_count']} of {validation['benchmark_total_count']} publication benchmarks"
                )
            if not published_model_context.gate.authoritative_rate_coupling_enabled:
                blockers.append("published hepatic glucose shadow model has no validated per-cell rate coupling")
        if published_model_lineage is None:
            blockers.append("published hepatic glucose lineage audit is unavailable")
        else:
            lineage_gates = published_model_lineage["gates"]
            if not lineage_gates["official_publication_artifact_reproduction_passed"]:
                blockers.append(
                    "exact publication-artifact equivalence remains unresolved despite 5 of 5 legacy author-lineage target reproduction"
                )
            if not lineage_gates["legacy_runtime_vendored"]:
                blockers.append("legacy 2014 author executable is not vendored because no explicit reusable license was found")
        if published_model_external_validation is None:
            blockers.append("published glucose external human-validation matrix is unavailable")
        else:
            if published_model_external_validation.exact_protocol_comparison_count == 0:
                blockers.append("published glucose shadow has no exact-protocol external human comparison")
            if published_model_external_validation.independent_heldout_result_count == 0:
                blockers.append("published glucose shadow has no independently audited held-out PHH validation result")
        if phh_glucose_validation is None:
            blockers.append("healthy-PHH spheroid glucose validation surface is unavailable")
        else:
            if not phh_glucose_validation.same_format_validation_ready:
                blockers.append("healthy-PHH spheroid observations are not ready as same-format validation targets")
            if phh_glucose_validation.exact_published_model_protocol_match is False:
                blockers.append("healthy-PHH spheroid observations have no exact-protocol published-model prediction")
            if phh_glucose_validation.independent_heldout_human_result_count == 0:
                blockers.append("delivered trajectory bundle contains no independent held-out human result")
        if phh_spheroid_protocol is None:
            blockers.append("exact healthy-PHH spheroid validation protocol is unavailable")
        else:
            if not phh_spheroid_protocol.cumulative_mean_trajectory_ready:
                blockers.append("PHH cumulative mean validation targets are unavailable")
            if not phh_spheroid_protocol.exact_protocol_prediction_loaded:
                blockers.append("no model prediction matches the locked 16-window PHH spheroid protocol")
        if phh_glucose_observability is None:
            blockers.append("PHH glucose measurement operator and identifiability audit are unavailable")
        else:
            if not phh_glucose_observability.cumulative_measurement_operator_ready:
                blockers.append("PHH cumulative trajectory cannot be projected into the exact observation space")
            if not phh_glucose_observability.exact_protocol_model_trajectory_loaded:
                blockers.append("no signed cumulative model trajectory is loaded for the PHH measurement operator")
            if not phh_glucose_observability.mechanistic_flux_decomposition_ready:
                blockers.append("PHH net medium glucose measurements do not identify intracellular pathway fluxes")
        if exact_glucose_contract is None:
            blockers.append("source-exact glucose-homeostasis structural contract is unavailable")
        else:
            if not exact_glucose_contract.active_runtime_replacement_ready:
                blockers.append("source-exact glucose topology has not replaced the split and lumped exploratory runtime")
            if not exact_glucose_contract.parameter_activation_allowed:
                blockers.append("source-exact glucose topology has no qualified numerical parameter activation")
        if glucose_open_system is None:
            blockers.append("glucose open-system and exact-assay bridge is unavailable")
        else:
            if not glucose_open_system.physiological_sinusoid.hepatocyte_transport_coupling_ready:
                blockers.append("physiological sinusoid has no calibrated hepatocyte glucose-exchange flux")
            if not glucose_open_system.phh_batch_assay.concentration_trajectory_reconstruction_ready:
                blockers.append("PHH batch assay lacks reported volumes for medium concentration reconstruction")
            if not glucose_open_system.predictive_ready:
                blockers.append("glucose open-system program has no exact-protocol predictive model output")
        if phh_albumin_secretion is None:
            blockers.append("PHH albumin-secretion measurement operator and identifiability audit are unavailable")
        else:
            if not phh_albumin_secretion.measurement_operator_ready:
                blockers.append("PHH albumin output cannot be projected into the 24-hour ELISA observation space")
            if not phh_albumin_secretion.exact_model_trajectory_loaded:
                blockers.append("no exact cumulative albumin model trajectory is loaded for the PHH assay operator")
            if not phh_albumin_secretion.mechanistic_rate_fit_ready:
                blockers.append("PHH albumin endpoint does not identify translation or secretory-path kinetics")
        if phh_cyp_function is None:
            blockers.append("PHH CYP-function observation panel is unavailable")
        else:
            if not phh_cyp_function.same_format_comparison_ready:
                blockers.append("PHH CYP outputs cannot be compared in the exact published assay space")
            if not phh_cyp_function.raw_timecourse_reconstruction_ready:
                blockers.append("PHH CYP source lacks raw substrate/product time courses and LLOQs")
            if not phh_cyp_function.kinetic_parameter_fit_ready:
                blockers.append("PHH CYP endpoint tables do not identify transport or enzyme kinetics")
        if phh_biliary_excretion is None:
            blockers.append("PHH d8-TCA biliary-excretion operator is unavailable")
        else:
            if not phh_biliary_excretion.raw_paired_condition_values_loaded:
                blockers.append("PHH BEI source lacks paired A_Ca and A_CaFree values and uncertainty")
            if not phh_biliary_excretion.transporter_specific_rate_fit_ready:
                blockers.append("PHH BEI does not identify BSEP or uptake kinetics")
            if not phh_biliary_excretion.canalicular_geometry_coupling_ready:
                blockers.append("PHH BEI does not identify canalicular geometry or sealing")
        if phh_identity_heterogeneity is None:
            blockers.append("PHH identity/heterogeneity panel is unavailable")
        else:
            if not phh_identity_heterogeneity.hepatocyte_subset_batch_numeric_matrix_loaded:
                blockers.append("PHH hepatocyte subsets lack a curated donor-by-subset numeric matrix")
            if not phh_identity_heterogeneity.single_cell_state_initialization_ready:
                blockers.append("PHH product composition cannot initialize one simulated hepatocyte")
            if not phh_identity_heterogeneity.generative_training_ready:
                blockers.append("six PHH batches are insufficient for donor-disjoint generative training")
        if phh_proteome_budget is None:
            blockers.append("PHH absolute proteome budget is unavailable")
        else:
            if not phh_proteome_budget.donor_specific_initialization_ready:
                blockers.append("PHH proteome cohort average does not initialize a donor-specific cell")
            if not phh_proteome_budget.dynamic_proteostasis_ready:
                blockers.append("PHH static proteome abundance does not identify synthesis or degradation dynamics")
            if not phh_proteome_budget.geometry_coupling_ready:
                blockers.append("PHH protein-mass fractions do not identify organelle geometry")
        if phh_transporter_inventory is None:
            blockers.append("PHH transporter inventory is unavailable")
        else:
            if not phh_transporter_inventory.bsep_surface_copy_observation_ready:
                blockers.append("BSEP total copies do not identify canalicular surface-localized copies")
            if not phh_transporter_inventory.mrp2_surface_copy_observation_ready:
                blockers.append("MRP2 total copies per nucleus do not identify canalicular surface-localized copies")
            if not phh_transporter_inventory.flux_coupling_ready:
                blockers.append("BSEP and MRP2 abundance do not identify whole-cell transport flux")
        if phh_protein_functional_evidence is None:
            blockers.append("PHH protein-functional evidence is unavailable")
        else:
            if not phh_protein_functional_evidence.integration_gates["active_fraction_ready"]:
                blockers.append("selected PHH proteins lack measured active fractions")
            if not phh_protein_functional_evidence.integration_gates["receptor_binding_kinetics_ready"]:
                blockers.append("INSR, MET and EGFR lack matched PHH receptor-binding kinetics")
            if not phh_protein_functional_evidence.integration_gates["donor_activity_distribution_ready"]:
                blockers.append("seven-donor total abundance does not identify donor activity distributions")
            if not phh_protein_functional_evidence.integration_gates["whole_cell_flux_coupling_ready"]:
                blockers.append("assay kinetics lack active-surface and whole-cell flux calibration")
        if human_sch_bile_acids is None:
            blockers.append("human SCH endogenous bile-acid reference is unavailable")
        else:
            if not human_sch_bile_acids.raw_donor_records_loaded:
                blockers.append("human SCH bile-acid source lacks raw donor-level records")
            if not human_sch_bile_acids.analyte_LLOQ_loaded:
                blockers.append("human SCH bile-acid source lacks analyte-specific LLOQs and censoring flags")
            if not human_sch_bile_acids.true_canalicular_concentration_ready:
                blockers.append("paired-buffer SCH accumulation does not identify true canalicular concentration")
            if not human_sch_bile_acids.healthy_in_vivo_initialization_ready:
                blockers.append("day-7 human SCH bile acids cannot initialize a healthy in-vivo hepatocyte")
        blockers.extend((
            "intercellular communication has no matched healthy-PHH exposure/receptor/response kinetics",
            "no Brian2 communication model has passed equation, unit, parameter and geometry gates",
            "no donor-held-out generative hepatocyte model artifact is available",
        ))
        if integrated_reaction_authority is not None and not integrated_reaction_authority.predictive_execution_ready:
            blockers.extend(
                f"integrated reaction authority: {blocker}"
                for blocker in integrated_reaction_authority.predictive_blockers
            )
        if kinetic_transfer is not None and kinetic_transfer.activated_transfer_count == 0:
            blockers.append(
                "published kinetic transfer: no active reaction passes equation, per-cell unit, context and held-out-validation gates"
            )
        blockers.extend(
            f"model surface not predictive: {surface.id}"
            for surface in MODEL_SURFACE_AUDIT
            if surface.status in ("schematic", "blocked", "disabled")
        )
    return ScientificReleaseGate(target, not blockers, tuple(checks), tuple(dict.fromkeys(blockers)))


def assert_scientific_release(target: ReleaseTarget = "research_preview") -> ScientificReleaseGate:
    gate = evaluate_scientific_release(target)
    if not gate.passed:
        raise RuntimeError(f"Scientific release gate failed ({target}): " + "; ".join(gate.blockers))
    return gate


def scientific_release_snapshot() -> dict[str, object]:
    preview = evaluate_scientific_release("research_preview")
    predictive = evaluate_scientific_release("predictive")
    return {
        "research_preview": preview,
        "predictive": predictive,
        "authoritative_scope": "Healthy PHH metabolic pools, unified fed/postabsorptive/prolonged-fast glycogen contexts, apparent ATP turnover, human zonation reference context with controlled-MPS oxygen evidence, postabsorptive blood-glucose perfusion boundary, measured peripheral endocrine observations, a causal liver-glycogen clamp benchmark, a non-interpolated human mixed-meal protocol, a source-locked PHH 3D-spheroid protocol with 12 independent cumulative-mean targets plus four descriptive overlap audits, a signed cumulative-to-window glucose operator, a six-batch 24-hour PHH albumin ELISA operator, 72 batch-resolved CYP SCR/MFR observations, five d8-TCA BEI observations, separate six-batch FACS/scRNA identity-composition surfaces, a seven-donor absolute proteome-mass reference, one same-cohort total-BSEP copy bridge, denominator-preserved human-liver MRP2 abundance, and four-donor day-7 human-SCH endogenous bile-acid endpoints with explicit identifiability gates. Reaction-level numerical parameter provenance is audited separately from pathway topology; the composed integrated fuel network remains exploratory unless every reaction, model context and held-out validation gate passes. A checksum-locked equation-level transfer audit maps all 36 active reactions against the published hepatic-glucose SBML and activates no fitted parameter without exact stoichiometry, compartment, symbolic law, per-cell units, matched PHH context and validation. Published hepatic glucose execution, model-lineage reproduction and its contextual external HGO comparison are shadow/diagnostic only. Runtime convex-surface geometry, closest points, overlap, membrane-domain labels, polygonal contact patches, enter/stay/exit contact inputs and bounded volume-preserving affine deformation are engine-authoritative. The normal snapshot contains one hepatocyte. Its active equivalent-size scale follows the normal-control human 3D median volume; the regular truncated-octahedron boundary and any diagnostic pair arrangement remain mathematical rather than donor morphometry. The 1% elastic-area cap is an explicit cross-system engineering bound equal to half the lower human-RBC lysis strain, not PHH rheology. Elapsed contact duration is not a causal input. Patch area may be computed from runtime geometry, while force, stiffness, adhesion, junction gating, mechanotransduction and biochemical effects remain blocked. Intercellular topology plus one measured PHH insulin-response chain are source-backed; receptor activation, Brian2 execution and generative-model coupling remain blocked. External evidence intake is manual-review-only. Dynamic proteostasis, macromolecular crowding, proteome-to-geometry mapping, canalicular surface and active transporter copies, transporter flux, raw donor-level bile-acid censoring, true canalicular concentration, healthy in-vivo bile-acid initialization, raw CYP time-course reconstruction, CYP kinetic fitting, transporter-resolved BEI, canalicular geometry coupling, product-composition-to-one-cell initialization, donor-disjoint generative training, albumin translation and secretory-path kinetics, portal receptor, hormone-to-rate, in-situ zonal oxygen, zone-specific flux and predictive external validation remain blocked.",
    }
