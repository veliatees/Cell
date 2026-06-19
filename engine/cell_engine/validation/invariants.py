from __future__ import annotations

import math

from cell_engine.core.cell_definition import CellDefinition
from cell_engine.core.state import CellState


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
    "bilirubin_conjugates",
    "amino_acids",
    "ROS",
    "Ca2+",
    "misfolded_protein",
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
        if any(not _finite(coord) for coord in organelle_state.location_um):
            raise ValidationError(f"Organelle {organelle_id} location must be finite")

    for stress_id, value in state.stress.items():
        if not 0 <= value <= 1:
            raise ValidationError(f"Stress axis {stress_id} must be in 0..1")


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

