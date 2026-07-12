"""Fail-closed release checks for the authoritative Healthy PHH baseline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from cell_engine.quantitative.phh_profiles import PHH_NUTRITIONAL_PROFILES
from cell_engine.quantitative.phh_state import build_quantitative_phh_state, validate_quantitative_phh_state
from cell_engine.quantitative.zonation import build_human_hepatocyte_zonation, validate_human_hepatocyte_zonation
from cell_engine.quantitative.homeostasis_v3 import build_human_nutritional_homeostasis_v3, validate_human_nutritional_homeostasis_v3
from cell_engine.stochastic.bioenergetics import build_phh_atp_turnover_network
from cell_engine.stochastic.integrated_cell import INTEGRATED_VOLUME_L
from cell_engine.stochastic.sinusoid import (
    build_sinusoid_boundary_network,
    build_sinusoid_coupled_homeostasis,
    validate_sinusoid_coupled_homeostasis,
)
from cell_engine.validation.phh_baseline import load_phh_baseline
from cell_engine.validation.model_audit import MODEL_SURFACE_AUDIT
from cell_engine.validation.hepatic_flux import load_hepatic_flux_evidence


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
        "authoritative_scope": "Healthy PHH metabolic pools, nutrition-state glycogen, apparent ATP turnover, human zonation reference context, postabsorptive blood-glucose perfusion boundary, and healthy-human mixed-meal organ trajectory only. Blood-to-cell, per-cell and zone-specific flux remain blocked.",
    }
