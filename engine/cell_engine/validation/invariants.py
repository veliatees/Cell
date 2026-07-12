from __future__ import annotations

import math

from cell_engine.core.cell_definition import CellDefinition
from cell_engine.core.state import CellState, TERMINAL_CARGO_STATES


class ValidationError(ValueError):
    pass


REQUIRED_HEPATOCYTE_COMPARTMENTS = {
    "cytosol",
    "nucleus",
    "rough_er",
    "smooth_er",
    "golgi",
    "mitochondria_pool",
    "lysosome_pool",
    "peroxisome_pool",
    "plasma_membrane",
    "sinusoidal_face",
    "canalicular_face",
}

REQUIRED_HEPATOCYTE_POOLS = {
    "ATP",
    "ADP",
    "AMP",
    "NADH",
    "NAD+",
    "NADPH",
    "GSH",
    "GSSG",
    "glucose",
    "glycogen",
    "lactate",
    "pyruvate",
    "fatty_acids",
    "acetyl_CoA",
    "ammonia",
    "urea",
    "bile_acids",
    "canalicular_bile_acids",
    "bilirubin_conjugates",
    "canalicular_bilirubin_conjugates",
    "amino_acids",
    "oxygen",
    "cytosolic_protein",
    "ROS",
    "Ca2+",
    "folded_cargo",
    "misfolded_protein",
    "ubiquitinated_cargo",
    "endocytosed_cargo",
    "autophagy_cargo",
    "very_long_chain_fatty_acids",
    "damaged_organelle_mass",
}

REQUIRED_HEPATOCYTE_PROCESSES = {
    "transcription",
    "translation",
    "protein_folding",
    "vesicle_trafficking",
    "membrane_transport",
    "glycolysis",
    "glycogen_storage_breakdown",
    "urea_cycle",
    "CYP_detox",
    "bile_export",
    "albumin_secretion",
    "autophagy",
    "apoptosis",
    "senescence",
}


def validate_definition(definition: CellDefinition) -> None:
    _assert_unique("compartment", [compartment.id for compartment in definition.compartments])
    _assert_unique("pool", [pool.id for pool in definition.pools])
    _assert_unique("organelle", [organelle.id for organelle in definition.organelles])

    source_ids = set(definition.sources)
    compartment_ids = definition.compartment_ids

    for compartment in definition.compartments:
        if compartment.parent_id is not None and compartment.parent_id not in compartment_ids:
            raise ValidationError(f"Compartment {compartment.id} has unknown parent {compartment.parent_id}")
        if compartment.volume_fraction is not None and not 0 < compartment.volume_fraction <= 1:
            raise ValidationError(f"Compartment {compartment.id} has invalid volume_fraction")

    for pool in definition.pools:
        if pool.compartment_id not in compartment_ids:
            raise ValidationError(f"Pool {pool.id} points to unknown compartment {pool.compartment_id}")
        if pool.source_id not in source_ids:
            raise ValidationError(f"Pool {pool.id} points to unknown source {pool.source_id}")
        if not pool.unit:
            raise ValidationError(f"Pool {pool.id} must declare a unit")
        if pool.initial_value < 0:
            raise ValidationError(f"Pool {pool.id} has negative initial value")

    for organelle in definition.organelles:
        if organelle.compartment_id not in compartment_ids:
            raise ValidationError(f"Organelle {organelle.id} points to unknown compartment {organelle.compartment_id}")
        if not organelle.model_layers:
            raise ValidationError(f"Organelle {organelle.id} must declare model layers")
        if not organelle.functions:
            raise ValidationError(f"Organelle {organelle.id} must declare functions")
        if not organelle.failure_modes:
            raise ValidationError(f"Organelle {organelle.id} must declare failure modes")
        if not organelle.stochastic_events:
            raise ValidationError(f"Organelle {organelle.id} must declare stochastic events")
        missing_sources = set(organelle.source_ids) - source_ids
        if missing_sources:
            raise ValidationError(f"Organelle {organelle.id} has unknown sources: {sorted(missing_sources)}")

    for parameter in definition.parameters.values():
        if parameter.source_id not in source_ids:
            raise ValidationError(f"Parameter {parameter.name} points to unknown source {parameter.source_id}")
        if not 0 <= parameter.confidence <= 1:
            raise ValidationError(f"Parameter {parameter.name} confidence must be in 0..1")

    missing_compartments = REQUIRED_HEPATOCYTE_COMPARTMENTS - compartment_ids
    if missing_compartments:
        raise ValidationError(f"Missing hepatocyte compartments: {sorted(missing_compartments)}")

    missing_pools = REQUIRED_HEPATOCYTE_POOLS - definition.pool_ids
    if missing_pools:
        raise ValidationError(f"Missing hepatocyte pools: {sorted(missing_pools)}")

    missing_processes = REQUIRED_HEPATOCYTE_PROCESSES - set(definition.processes)
    if missing_processes:
        raise ValidationError(f"Missing hepatocyte processes: {sorted(missing_processes)}")

    if definition.stochastic_policy.hazard_model != "state_conditioned":
        raise ValidationError("Stochastic policy must use state_conditioned hazard_model")


def validate_state(definition: CellDefinition, state: CellState) -> None:
    if state.definition_id != definition.id:
        raise ValidationError(f"State definition_id {state.definition_id} does not match {definition.id}")

    missing_pools = definition.pool_ids - set(state.pools)
    if missing_pools:
        raise ValidationError(f"State is missing pools: {sorted(missing_pools)}")

    missing_organelles = definition.organelle_ids - set(state.organelles)
    if missing_organelles:
        raise ValidationError(f"State is missing organelles: {sorted(missing_organelles)}")

    pool_defs = {pool.id: pool for pool in definition.pools}
    for pool_id, pool_state in state.pools.items():
        if pool_id not in pool_defs:
            raise ValidationError(f"State has unknown pool {pool_id}")
        if not _finite(pool_state.value) or pool_state.value < 0:
            raise ValidationError(f"Pool {pool_id} must be finite and non-negative")
        if pool_state.unit != pool_defs[pool_id].unit:
            raise ValidationError(f"Pool {pool_id} unit mismatch: {pool_state.unit} != {pool_defs[pool_id].unit}")
        if pool_state.compartment_id != pool_defs[pool_id].compartment_id:
            raise ValidationError(f"Pool {pool_id} compartment mismatch")

    for organelle_id, organelle_state in state.organelles.items():
        if organelle_id not in definition.organelle_ids:
            raise ValidationError(f"State has unknown organelle {organelle_id}")
        if not 0 <= organelle_state.health <= 1:
            raise ValidationError(f"Organelle {organelle_id} health must be in 0..1")
        if not 0 <= organelle_state.damage <= 1:
            raise ValidationError(f"Organelle {organelle_id} damage must be in 0..1")
        if organelle_state.capacity < 0:
            raise ValidationError(f"Organelle {organelle_id} capacity must be non-negative")
        if organelle_state.age_h < 0:
            raise ValidationError(f"Organelle {organelle_id} age_h must be non-negative")
        if organelle_state.risk_per_hour < 0:
            raise ValidationError(f"Organelle {organelle_id} risk_per_hour must be non-negative")
        if not 0 <= organelle_state.local_atp <= 1:
            raise ValidationError(f"Organelle {organelle_id} local_atp must be in 0..1")
        if organelle_state.transport_delay_s < 0:
            raise ValidationError(f"Organelle {organelle_id} transport_delay_s must be non-negative")
        if any(not _finite(coord) for coord in organelle_state.location_um):
            raise ValidationError(f"Organelle {organelle_id} location must be finite")

    for stress_id, value in state.stress.items():
        if not 0 <= value <= 1:
            raise ValidationError(f"Stress axis {stress_id} must be in 0..1")

    if state.gene_expression is not None:
        program = state.gene_expression
        if set(program.genes) != {gene.gene_symbol for gene in program.genes.values()}:
            raise ValidationError("Gene-expression map keys must equal gene symbols")
        expected_autosomal_copies = state.genome.total_chromosome_sets if state.genome is not None else None
        for symbol, gene in program.genes.items():
            if not _finite(gene.allele_copies) or gene.allele_copies <= 0:
                raise ValidationError(f"Gene {symbol} allele copies must be finite and positive")
            if expected_autosomal_copies is not None and not math.isclose(gene.allele_copies, expected_autosomal_copies):
                raise ValidationError(f"Gene {symbol} allele copies do not match hepatocyte ploidy")
            for field_name in (
                "functional_dosage_scale",
                "active_allele_count",
                "nuclear_pre_mrna_count",
                "nuclear_mature_mrna_count",
                "cytoplasmic_mrna_count",
                "total_protein_count",
                "functional_protein_scale",
            ):
                value = getattr(gene, field_name)
                if value is not None and (not _finite(value) or value < 0):
                    raise ValidationError(f"Gene {symbol} {field_name} must be finite and non-negative")
            if gene.active_allele_count is not None and gene.active_allele_count > gene.allele_copies:
                raise ValidationError(f"Gene {symbol} active alleles exceed allele copies")
        if set(program.kinetic_profiles) - set(program.genes):
            raise ValidationError("Gene-expression kinetic profile has an unknown gene")
        for symbol, profile in program.kinetic_profiles.items():
            if profile.gene_symbol != symbol:
                raise ValidationError(f"Gene-expression kinetic profile key mismatch for {symbol}")
            rates = (
                profile.promoter_on_rate_per_s,
                profile.promoter_off_rate_per_s,
                profile.transcription_rate_per_active_allele_per_s,
                profile.splicing_rate_per_s,
                profile.nuclear_export_rate_per_s,
                profile.cytoplasmic_mrna_decay_rate_per_s,
                profile.translation_rate_per_mrna_per_s,
                profile.protein_decay_rate_per_s,
            )
            if any(not _finite(rate) or rate <= 0 for rate in rates):
                raise ValidationError(f"Gene {symbol} has invalid kinetic rates")
            if not profile.source_ids or not profile.biological_system or not profile.assay or not profile.evidence:
                raise ValidationError(f"Gene {symbol} kinetic profile lacks calibration provenance")
        edge_ids: set[str] = set()
        for edge in program.regulatory_edges:
            if edge.id in edge_ids:
                raise ValidationError(f"Duplicate expression regulatory edge: {edge.id}")
            edge_ids.add(edge.id)
            if edge.target_gene not in program.genes:
                raise ValidationError(f"Regulatory edge {edge.id} has an unknown target gene")
            if not edge.source_ids or edge.quantification_status != "qualitative_direction_only":
                raise ValidationError(f"Regulatory edge {edge.id} has an invalid evidence boundary")
        event_ids: set[str] = set()
        for event in program.events:
            if event.id in event_ids:
                raise ValidationError(f"Duplicate expression event id: {event.id}")
            event_ids.add(event.id)
            if event.gene_symbol not in program.genes:
                raise ValidationError(f"Expression event {event.id} has unknown gene")
            if event.t_s < 0 or not _finite(event.t_s):
                raise ValidationError(f"Expression event {event.id} has invalid time")
            if not event.changed_fields or not event.source_id or not event.evidence:
                raise ValidationError(f"Expression event {event.id} lacks state change or evidence")

    if state.genomic_architecture is not None:
        architecture = state.genomic_architecture
        genome_symbols = {locus.symbol for locus in state.genome.functional_loci} if state.genome is not None else set()
        if set(architecture.epigenetic_loci) != genome_symbols:
            raise ValidationError("Epigenetic locus registry must match the simulation-facing genome loci")
        module_ids: set[str] = set()
        for module in architecture.gene_modules:
            if module.id in module_ids:
                raise ValidationError(f"Duplicate gene module: {module.id}")
            module_ids.add(module.id)
            if not set(module.member_genes) <= genome_symbols:
                raise ValidationError(f"Gene module {module.id} references an unknown locus")
            if not set(module.explicit_expression_genes) <= set(module.member_genes):
                raise ValidationError(f"Gene module {module.id} has an invalid explicit-expression subset")
        for symbol, locus in architecture.epigenetic_loci.items():
            if locus.dna_methylation_fraction is not None and not 0 <= locus.dna_methylation_fraction <= 1:
                raise ValidationError(f"Epigenetic locus {symbol} has invalid DNA methylation")
            if any(not _finite(value) or not 0 <= value <= 1 for value in locus.histone_marks.values()):
                raise ValidationError(f"Epigenetic locus {symbol} has invalid histone-mark values")
        if len(architecture.milestones) != 6 or tuple(item.milestone for item in architecture.milestones) != tuple(range(1, 7)):
            raise ValidationError("Genomic architecture must expose the ordered six-milestone contract")
        dataset_ids = [dataset.id for dataset in architecture.omics_datasets]
        if len(dataset_ids) != len(set(dataset_ids)):
            raise ValidationError("Genomic architecture has duplicate omics datasets")
        link_ids = [link.id for link in architecture.variant_functional_links]
        if len(link_ids) != len(set(link_ids)):
            raise ValidationError("Genomic architecture has duplicate variant-functional links")

    known_locations = definition.compartment_ids | definition.organelle_ids | {
        "er_quality_control",
        "proteasome",
        "lysosome_endosome",
        "plasma_membrane",
    }
    for packet in state.cargo_packets:
        if packet.origin_compartment not in known_locations:
            raise ValidationError(f"Cargo {packet.id} has unknown origin {packet.origin_compartment}")
        if packet.target_compartment not in known_locations:
            raise ValidationError(f"Cargo {packet.id} has unknown target {packet.target_compartment}")
        if packet.current_location not in known_locations:
            raise ValidationError(f"Cargo {packet.id} has unknown current_location {packet.current_location}")
        if not packet.route_plan:
            raise ValidationError(f"Cargo {packet.id} route_plan cannot be empty")
        if packet.current_location not in set(packet.route_plan) | known_locations:
            raise ValidationError(f"Cargo {packet.id} location must be route-compatible")
        if not 0 <= packet.route_index < len(packet.route_plan):
            raise ValidationError(f"Cargo {packet.id} has invalid route_index")
        if not 0 <= packet.quality_score <= 1:
            raise ValidationError(f"Cargo {packet.id} quality_score must be in 0..1")
        if packet.age_s < 0:
            raise ValidationError(f"Cargo {packet.id} age_s must be non-negative")
        if packet.energy_cost_atp < 0:
            raise ValidationError(f"Cargo {packet.id} energy_cost_atp must be non-negative")
        if packet.state != "in_transit" and packet.state not in TERMINAL_CARGO_STATES:
            raise ValidationError(f"Cargo {packet.id} has invalid state {packet.state}")

    for flux in state.metabolic_fluxes:
        if not flux.id:
            raise ValidationError("Metabolic flux id cannot be empty")
        if flux.value < 0 or not _finite(flux.value):
            raise ValidationError(f"Metabolic flux {flux.id} must be finite and non-negative")
        if not flux.unit:
            raise ValidationError(f"Metabolic flux {flux.id} must declare a unit")

    for result in state.pathway_results:
        if not result.id or not result.model_id:
            raise ValidationError("Pathway result id and model_id cannot be empty")
        if not result.engine:
            raise ValidationError(f"Pathway result {result.id} must declare engine")
        if not result.unit:
            raise ValidationError(f"Pathway result {result.id} must declare unit")
        if not result.provenance:
            raise ValidationError(f"Pathway result {result.id} must declare provenance")
        if any((not _finite(value) or value < 0) for value in result.species.values()):
            raise ValidationError(f"Pathway result {result.id} species values must be finite and non-negative")

    for result in state.signaling_results:
        if not result.id or not result.model_id:
            raise ValidationError("Signaling result id and model_id cannot be empty")
        if not result.engine:
            raise ValidationError(f"Signaling result {result.id} must declare engine")
        if not result.provenance:
            raise ValidationError(f"Signaling result {result.id} must declare provenance")
        if any((not _finite(value) or value < 0) for value in result.markers.values()):
            raise ValidationError(f"Signaling result {result.id} markers must be finite and non-negative")
        if any((not _finite(value) or value < 0) for value in result.actions.values()):
            raise ValidationError(f"Signaling result {result.id} actions must be finite and non-negative")

    if state.membrane_state is not None:
        membrane = state.membrane_state
        if not membrane.engine:
            raise ValidationError("Membrane state must declare engine")
        if not membrane.provenance:
            raise ValidationError("Membrane state must declare provenance")
        if not _finite(membrane.membrane_potential_mv):
            raise ValidationError("Membrane potential must be finite")
        if not 0 <= membrane.cytosolic_ca <= 1.5:
            raise ValidationError("Membrane cytosolic_ca must be in 0..1.5")
        if not 0 <= membrane.er_ca <= 1.5:
            raise ValidationError("Membrane er_ca must be in 0..1.5")
        if not 0 <= membrane.pump_activity <= 1:
            raise ValidationError("Membrane pump_activity must be in 0..1")
        if not 0 <= membrane.channel_open_probability <= 1:
            raise ValidationError("Membrane channel_open_probability must be in 0..1")


def _assert_unique(label: str, ids: list[str]) -> None:
    seen: set[str] = set()
    duplicated: set[str] = set()
    for id in ids:
        if id in seen:
            duplicated.add(id)
        seen.add(id)
    if duplicated:
        raise ValidationError(f"Duplicate {label} ids: {sorted(duplicated)}")


def _finite(value: float) -> bool:
    return math.isfinite(value)
