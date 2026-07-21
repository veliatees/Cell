from __future__ import annotations

from dataclasses import dataclass, replace

from cell_engine.core.history import CellHistoryState, ExperienceEvent, LifecycleState, initial_cell_history, record_or_extend_event
from cell_engine.core.provenance import SourceReference
from cell_engine.core.state import CellState

DATE_VERIFIED = "2026-07-10"

CELLULAR_MEMORY_SOURCES: dict[str, SourceReference] = {
    "human_hepatocyte_renewal": SourceReference(
        id="human_hepatocyte_renewal",
        title="Diploid hepatocytes drive physiological liver renewal in adult humans",
        url="https://doi.org/10.1016/j.cels.2022.05.001",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Retrospective carbon-14 birth dating; population renewal is not a fixed single-cell lifespan.",
    ),
    "hepatocyte_regeneration_cycle": SourceReference(
        id="hepatocyte_regeneration_cycle",
        title="Cellular and Molecular Basis of Liver Regeneration",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC7108750/",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes="Mature hepatocytes are quiescent and can re-enter the cell cycle after priming and mitogenic signaling.",
    ),
    "human_hepatocyte_somatic_mutations": SourceReference(
        id="human_hepatocyte_somatic_mutations",
        title="Single-cell analysis of somatic mutations in human hepatocytes",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC6994209/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Somatic sequence variants are stable physical records; the model does not infer an individual variant without data.",
    ),
    "hcv_epigenetic_scar": SourceReference(
        id="hcv_epigenetic_scar",
        title="HCV-induced epigenetic changes persist after sustained virologic response",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC8756817/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="A defined exposure-specific persistent liver epigenetic scar; not a generic stress-memory rate.",
    ),
    "alberts_cell_memory_substrates": SourceReference(
        id="alberts_cell_memory_substrates",
        title="Molecular Biology of the Cell",
        url="https://www.ncbi.nlm.nih.gov/books/NBK21054/",
        source_type="textbook",
        date_verified="2026-07-21",
        notes=(
            "General molecular and organelle-state topology. It does not authorize a "
            "hepatocyte-specific memory write, decay, inheritance or response law."
        ),
    ),
}


@dataclass(frozen=True)
class MemorySubstrateContract:
    id: str
    physical_carrier: str
    compartments: tuple[str, ...]
    candidate_write_processes: tuple[str, ...]
    required_persistence_tests: tuple[str, ...]
    future_response_readouts: tuple[str, ...]
    division_handling: str
    source_ids: tuple[str, ...]
    quantitative_coupling_allowed: bool = False


MEMORY_SUBSTRATE_CONTRACTS: tuple[MemorySubstrateContract, ...] = (
    MemorySubstrateContract(
        "genetic_sequence",
        "somatic DNA sequence variant or structural variant",
        ("nucleus", "mitochondria"),
        ("replication_error", "DNA_damage_and_misrepair"),
        ("direct_single_cell_sequence_measurement", "technical_replicate_or_orthogonal_confirmation"),
        ("allele_specific_expression", "repair_or_fate_response"),
        "chromosome segregation or mitochondrial partition; lineage-specific state must be measured",
        ("human_hepatocyte_somatic_mutations",),
    ),
    MemorySubstrateContract(
        "dna_damage_or_repair_scar",
        "persistent lesion, repair focus, rearrangement or verified repair-product state",
        ("nucleus",),
        ("genotoxic_exposure", "replication_stress", "repair"),
        ("washout_time_course", "lesion_or_repair_product_assay"),
        ("rechallenge_repair_dynamics", "checkpoint_or_fate_response"),
        "unknown until lineage-resolved lesion or repair evidence is available",
        ("human_hepatocyte_somatic_mutations", "alberts_cell_memory_substrates"),
    ),
    MemorySubstrateContract(
        "dna_methylation",
        "locus-resolved DNA methylation state",
        ("nucleus",),
        ("methyltransferase_activity", "demethylation", "replication_coupled_maintenance"),
        ("trigger_washout", "locus_resolved_methylome", "rechallenge_or_longitudinal_sampling"),
        ("locus_accessibility", "gene_expression", "rechallenge_response"),
        "replication-coupled maintenance is possible but must be measured for the locus and context",
        ("hcv_epigenetic_scar",),
    ),
    MemorySubstrateContract(
        "histone_or_chromatin",
        "histone modification, nucleosome occupancy or stable chromatin accessibility state",
        ("nucleus",),
        ("chromatin_writer_eraser_activity", "transcription_factor_recruitment"),
        ("trigger_washout", "ATAC_or_ChIP_time_course", "rechallenge"),
        ("transcriptional_response", "fate_bias"),
        "partition and re-establishment must be measured; inheritance is not assumed",
        ("hcv_epigenetic_scar",),
    ),
    MemorySubstrateContract(
        "transcriptional_or_rna_network",
        "self-sustaining regulator expression, stable RNA or ribonucleoprotein state",
        ("nucleus", "cytosol"),
        ("transcriptional_feedback", "RNA_processing", "RNA_stabilization"),
        ("trigger_washout", "absolute_RNA_time_course", "translation_block_or_rechallenge"),
        ("future_transcription", "protein_output", "signal_response"),
        "molecular partition and dilution; no inheritance rule without measurements",
        ("alberts_cell_memory_substrates",),
    ),
    MemorySubstrateContract(
        "stable_post_translational_or_receptor_state",
        "persistent protein modification, receptor internalization or desensitized signaling complex",
        ("plasma_membrane", "cytosol", "endosome"),
        ("ligand_exposure", "kinase_phosphatase_activity", "endocytosis_and_recycling"),
        ("ligand_washout", "surface_copy_and_PTM_time_course", "rechallenge"),
        ("receptor_occupancy", "second_messenger_response", "transport_activity"),
        "protein/vesicle partition and turnover; no fixed half-life is assumed",
        ("alberts_cell_memory_substrates",),
    ),
    MemorySubstrateContract(
        "protein_or_aggregate",
        "long-lived protein abundance, complex assembly, aggregate or proteostasis state",
        ("cytosol", "er", "proteasome", "lysosome"),
        ("translation", "folding", "aggregation", "degradation"),
        ("pulse_chase_proteomics", "washout", "aggregate_clearance_time_course"),
        ("enzyme_capacity", "stress_response", "future_aggregation"),
        "molecular partition and dilution plus measured turnover",
        ("alberts_cell_memory_substrates",),
    ),
    MemorySubstrateContract(
        "mitochondrial_or_organelle_quality",
        "organelle abundance, age, genome, damage, composition or network state",
        ("mitochondria", "er", "peroxisome", "lysosome", "golgi"),
        ("biogenesis", "fission_fusion", "damage", "selective_autophagy"),
        ("organelle_resolved_longitudinal_imaging", "turnover_assay", "functional_rechallenge"),
        ("bioenergetics", "redox", "calcium", "cargo_processing"),
        "organelle partition plus biogenesis/turnover; distribution must be measured",
        ("alberts_cell_memory_substrates",),
    ),
    MemorySubstrateContract(
        "metabolic_store",
        "persistent glycogen, lipid, cofactor or metabolite-pool state",
        ("cytosol", "lipid_droplet", "organelles"),
        ("feeding_fasting", "synthesis", "consumption", "transport"),
        ("absolute_pool_time_course", "boundary_flux_mass_balance", "washout_or_state_transition"),
        ("future_flux_capacity", "energy_response", "hormone_response"),
        "partition and dilution depend on the measured store and cell-cycle context",
        ("alberts_cell_memory_substrates",),
    ),
    MemorySubstrateContract(
        "membrane_lipid_or_polarity_state",
        "membrane lipid composition, domain organization, junction or cytoskeletal polarity",
        ("plasma_membrane", "cell_cortex", "junctions"),
        ("lipid_remodelling", "trafficking", "contact", "mechanical_load"),
        ("washout", "lipidomics_or_domain_imaging", "contact_rechallenge"),
        ("receptor_transport_localization", "shape_response", "junction_function"),
        "surface and cytoskeletal partition/remodelling must be measured",
        ("alberts_cell_memory_substrates",),
    ),
    MemorySubstrateContract(
        "damage_response_state",
        "persistent checkpoint, stress-program or stable-arrest molecular state",
        ("whole_cell",),
        ("oxidative_proteotoxic_genotoxic_or_cholestatic_stress",),
        ("trigger_washout", "recovery_time_course", "rechallenge", "fate_markers"),
        ("repair_capacity", "senescence_or_death_bias", "stress_response"),
        "partition/inheritance is mechanism-specific and remains unknown by default",
        ("alberts_cell_memory_substrates",),
    ),
    MemorySubstrateContract(
        "external_niche_record",
        "persistent extracellular matrix, junction or neighbour-produced environmental state",
        ("extracellular_space", "cell_surface"),
        ("matrix_remodelling", "cell_cell_contact", "paracrine_secretion"),
        ("environmental_washout_or_replacement", "matched_cell_response"),
        ("adhesion", "polarity", "receptor_signaling", "future_cell_state"),
        "not cell-intrinsic; it follows the spatial world and is not inherited as a molecular cell trace",
        ("alberts_cell_memory_substrates",),
    ),
)


def cellular_memory_contract_snapshot() -> dict[str, object]:
    ids = tuple(item.id for item in MEMORY_SUBSTRATE_CONTRACTS)
    if len(set(ids)) != len(ids):
        raise ValueError("cellular-memory substrate contract ids must be unique")
    if any(item.quantitative_coupling_allowed for item in MEMORY_SUBSTRATE_CONTRACTS):
        raise ValueError("cellular-memory templates may not activate quantitative coupling")
    return {
        "version": "cellular_memory_substrate_contract_v1",
        "status": "physical_substrates_declared_quantitative_readout_blocked",
        "event_log_is_memory": False,
        "causal_rule": (
            "An experience becomes cell memory only when it writes a directly assayed "
            "physical substrate that persists after trigger removal and measurably changes "
            "a later response. Event duration alone never creates a memory trace."
        ),
        "substrates": MEMORY_SUBSTRATE_CONTRACTS,
        "active_memory_trace_count": 0,
        "automatic_memory_consolidation": False,
        "automatic_future_response_coupling": False,
        "source_ids": tuple(CELLULAR_MEMORY_SOURCES),
        "summary": {
            "substrate_contract_count": len(MEMORY_SUBSTRATE_CONTRACTS),
            "quantitatively_coupled_substrate_count": 0,
            "required_persistence_test_count": sum(
                len(item.required_persistence_tests) for item in MEMORY_SUBSTRATE_CONTRACTS
            ),
        },
    }


def apply_cellular_memory(state: CellState, *, dt_s: float) -> CellState:
    """Advance life history while refusing to invent memory consolidation.

    Exposure history is updated from explicit experiment controls. No persistent
    trace is created from stress-time alone because the current engine lacks a
    matched washout/rechallenge or locus-resolved persistence calibration.
    """
    if dt_s <= 0:
        raise ValueError("dt_s must be positive")
    history = state.history or initial_cell_history()
    lifecycle_name = "dying" if state.status == "dying" else "quiescent_G0"
    previous_lifecycle = history.lifecycle
    lifecycle = LifecycleState(
        state=lifecycle_name,
        entered_state_time_s=(
            previous_lifecycle.entered_state_time_s
            if previous_lifecycle.state == lifecycle_name
            else state.elapsed_s
        ),
        cell_age_s=max(0.0, state.elapsed_s - history.birth_time_s),
        terminal_status="terminal_process_active" if lifecycle_name == "dying" else "alive",
        evidence_status=(
            "derived_from_engine_terminal_status"
            if lifecycle_name == "dying"
            else "source_backed_state_identity"
        ),
        source_ids=previous_lifecycle.source_ids,
        notes=(
            "The integrated state engine has no active regeneration context, so the mature "
            "cell remains G0. Stress evidence alone does not establish senescence."
        ),
    )
    history = replace(history, lifecycle=lifecycle)

    experiment_id = str(state.model_controls.get("experiment_id", "baseline"))
    if experiment_id != "baseline":
        measurements = {
            key: float(value)
            for key, value in state.model_controls.items()
            if key.endswith("surface_activity") and isinstance(value, (int, float))
        }
        event_id = f"experiment-{experiment_id}"
        existing = next((event for event in history.event_log if event.id == event_id), None)
        start = existing.start_time_s if existing else max(0.0, state.elapsed_s - dt_s)
        source_ids = state.cellular_response.source_ids if state.cellular_response else ()
        event = ExperienceEvent(
            id=event_id,
            event_type=experiment_id,
            start_time_s=start,
            last_observed_time_s=state.elapsed_s,
            duration_s=max(0.0, state.elapsed_s - start),
            status="ongoing",
            compartment="plasma_membrane_and_cell",
            measurements=measurements,
            measurement_unit="relative_to_reference_condition",
            source_ids=source_ids,
            notes=(
                "Recorded exposure/intervention. No persistent memory trace is consolidated "
                "without washout, persistence, rechallenge, or inheritance evidence."
            ),
        )
        history = record_or_extend_event(history, event)

    return replace(state, history=history)
