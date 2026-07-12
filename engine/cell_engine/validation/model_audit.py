"""Scientific authority audit for model surfaces exposed by the snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


AuditStatus = Literal["source_backed", "derived", "schematic", "blocked", "disabled"]


@dataclass(frozen=True)
class ModelSurfaceAudit:
    id: str
    status: AuditStatus
    default_snapshot_role: str
    drives_scientific_validation: bool
    action: str
    source_ids: tuple[str, ...]
    limitations: str


MODEL_SURFACE_AUDIT: tuple[ModelSurfaceAudit, ...] = (
    ModelSurfaceAudit("phh_energy_and_glycogen", "source_backed", "authoritative_research_preview", True, "retain", ("human_liver_adenylates_1992", "human_liver_atp_synthesis_2008", "human_liver_glycogen_mixed_meal_2000", "human_liver_glycogen_overnight_1996", "human_liver_glycogen_starvation_1973"), "Whole-liver-equivalent values are not compartment-resolved isolated-PHH measurements."),
    ModelSurfaceAudit("postabsorptive_glucose_boundary", "source_backed", "authoritative_research_preview", True, "retain", ("hmdb_2022", "human_hepatic_transit_1996"), "Systemic plasma target and whole-liver transit time do not resolve portal/arterial mixing or one sinusoid."),
    ModelSurfaceAudit("human_hepatocyte_zonation_context", "source_backed", "source_backed_reference_context", True, "retain categorical marker direction; block numeric flux scaling", ("human_liver_spatial_atlas_2026", "human_liver_single_cell_proteomics_2025", "human_liver_cell_atlas_2019"), "Human atlas marker directions are not donor-specific expression values; zonal pO2 and reaction-rate effect sizes remain unavailable."),
    ModelSurfaceAudit("sinusoid_glucose_homeostasis_v2", "source_backed", "authoritative_research_preview", True, "retain perfusion relaxation; block blood-cell and zonal flux", ("hmdb_2022", "human_hepatic_transit_1996"), "Whole-liver transit and systemic fasting glucose do not identify one sinusoid volume, GLUT2 exchange capacity or zone-specific cellular flux."),
    ModelSurfaceAudit("human_nutritional_homeostasis_v3", "source_backed", "organ_scale_validation_trajectory", True, "retain measured trajectory; prohibit per-cell allocation", ("human_mixed_meal_homeostasis_1996",), "Healthy-human mixed-meal glycogen and hepatic-output observations are whole-liver cohort averages, not single-cell or zone-resolved fluxes."),
    ModelSurfaceAudit("human_hepatic_flux_evidence_bundle", "source_backed", "organ_scale_reference_only", False, "use only for scale-matched validation; never initialize per-cell flux", (), "Thirty-one literature records span organ, splanchnic and whole-body scopes; portal-resolved healthy and single-hepatocyte flux are unavailable."),
    ModelSurfaceAudit("normalized_pool_engine", "schematic", "legacy_relative_state", False, "never use for quantitative validation", ("project_roadmap_07",), "All 48 pools are relative 0-1 placeholders."),
    ModelSurfaceAudit("organelle_functional_cycles", "schematic", "legacy_relative_state", False, "retain only as qualitative renderer driver", ("project_roadmap_07",), "Cycle rates, error fractions, damage and repair coefficients are uncalibrated."),
    ModelSurfaceAudit("organelle_failure_hazards", "disabled", "not_executed_without_calibration", False, "require a source-tagged calibration object", (), "Former per-hour base risks and stress weights were project assumptions."),
    ModelSurfaceAudit("cytokinesis_failure_probability", "disabled", "not_executed_without_calibration", False, "require measured context-specific probability", ("human_hepatocyte_binucleation",), "Binucleated-cell prevalence cannot be used as a per-division failure probability."),
    ModelSurfaceAudit("absolute_transporter_flux", "blocked", "qualitative_activity_only", False, "require active surface copies and matched turnover", ("human_mrp2_abundance_2012", "human_bsep_taurocholate_2013", "human_ntcp_uptake_2003"), "Total or membrane-fraction abundance is not active canalicular surface abundance."),
    ModelSurfaceAudit("glutathione_redox_kinetics", "blocked", "exploratory_network_only", False, "require compartment-resolved human GSH/GSSG/NADPH trajectories", ("human_liver_glutathione_1980", "primary_hepatocyte_isolation_metabolism_2018"), "Legacy GPx, reductase, PPP and ROS influx rates are placeholders; isolation changes these pools."),
    ModelSurfaceAudit("integrated_fuel_pathway_rates", "blocked", "exploratory_network_only", False, "replace pseudo-first-order magnitudes with fitted human fluxes", ("hepatic_glucose_homeostasis",), "Topology and stoichiometry are useful, but several absolute rates are illustrative."),
    ModelSurfaceAudit("cell_fate_thresholds", "blocked", "evidence_labels_only", False, "do not claim calibrated time-to-death", ("atp_death_switch", "human_bile_acid_death_mode"), "Relative stress thresholds are not matched human-hepatocyte commitment kinetics."),
    ModelSurfaceAudit("genome_expression", "derived", "structural_data_gated", False, "run dynamics only for calibrated genes", ("human_hepatocyte_proteome_2016",), "Reference coordinates are real; most donor expression and gene-specific kinetics are unknown."),
)


def scientific_model_audit_snapshot() -> dict[str, object]:
    blocked = tuple(item.id for item in MODEL_SURFACE_AUDIT if item.status in ("blocked", "disabled"))
    authoritative = tuple(item.id for item in MODEL_SURFACE_AUDIT if item.drives_scientific_validation)
    return {
        "status": "mixed_authority_research_preview",
        "authoritative_surfaces": authoritative,
        "blocked_or_disabled_surfaces": blocked,
        "surfaces": MODEL_SURFACE_AUDIT,
        "policy": "Only source-backed surfaces may drive scientific validation. Schematic and blocked surfaces may drive visualization but not quantitative claims.",
    }
