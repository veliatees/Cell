from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from cell_engine.core.cell_definition import CellDefinition
from cell_engine.core.random import EngineRng
from cell_engine.quantitative.geometry import build_hepatocyte_geometry, molecules_from_concentration_mM
from cell_engine.stochastic.cell_cycle import (
    RAT_HEPATOCYTE_PHX_REFERENCE_TIMING_PROFILE,
    CellCycleParams,
    CellCycleState,
    apply_timing_profile,
    cell_cycle_timing_profile_snapshot,
)
from cell_engine.stochastic.cell_cycle import cytokinesis_failure_risk
from cell_engine.stochastic.cell_cycle import divide as cycle_divide
from cell_engine.stochastic.cell_cycle import evaluate_cell_cycle_control
from cell_engine.stochastic.cell_cycle import fail_cytokinesis
from cell_engine.stochastic.cell_cycle import step as cycle_step
from cell_engine.stochastic.cell_model import CYTOSOL
from cell_engine.stochastic.central_dogma import HEPATOCYTE_ENZYME_GENE, build_central_dogma_network
from cell_engine.stochastic.glycolysis import build_glycolysis_network
from cell_engine.stochastic.integrators import simulate_hybrid
from cell_engine.stochastic.reactions import ReactionNetwork, compose_networks, mass_action
from cell_engine.stochastic.redox import build_redox_network
from cell_engine.stochastic.urea_cycle import build_urea_cycle_network

# The whole cell grows on glucose; division needs a size checkpoint reached only
# while fed, but nutrition alone is not a license to divide. Adult hepatocytes are
# normally quiescent and need mitogen/regeneration signals to re-enter cycle.
# Hepatocyte cytokinesis failure is context-dependent; 0.20 is a starting,
# source-tagged modelling assumption to make binucleation possible by default in
# population runs. Validation/calibration should replace it per species/context.
HEPATOCYTE_CYTOKINESIS_FAILURE_PROBABILITY = 0.20
WHOLE_CELL_CYCLE = CellCycleParams(
    nutrient_species="glucose",
    regeneration_signal_active=False,
    cytokinesis_failure_probability=HEPATOCYTE_CYTOKINESIS_FAILURE_PROBABILITY,
)
PROLIFERATING_HEPATOCYTE_CYCLE = CellCycleParams(
    nutrient_species="glucose",
    regeneration_signal_active=True,
    cytokinesis_failure_probability=HEPATOCYTE_CYTOKINESIS_FAILURE_PROBABILITY,
)
REAL_TIME_PROLIFERATING_HEPATOCYTE_CYCLE = apply_timing_profile(
    PROLIFERATING_HEPATOCYTE_CYCLE,
    RAT_HEPATOCYTE_PHX_REFERENCE_TIMING_PROFILE,
)

# Gene expression is the low-copy subsystem run by exact SSA; metabolism (even its
# scarce intermediates) runs on CLE. This subsystem partition is what the field
# uses for whole-cell models and keeps the run tractable.
DISCRETE_SPECIES = {"gene", "mRNA"}


@dataclass(frozen=True)
class WholeCell:
    """One hepatocyte as a single coupled system.

    A unified reaction network (glycolysis + urea cycle + redox + gene
    expression) sharing pools by name, plus a cell-cycle state. Metabolites are
    high-copy (CLE) and genes/mRNA are low-copy (SSA) in the *same* network — the
    hybrid integrator runs both. The cell cycle reads the network's real glucose
    pool, and division partitions the network's real molecule counts.
    """

    network: ReactionNetwork
    counts: dict[str, float]
    cycle: CellCycleState
    t_s: float = 0.0

    def concentration_mM(self, species: str):
        from cell_engine.quantitative.geometry import concentration_mM_from_molecules
        return concentration_mM_from_molecules(max(self.counts.get(species, 0.0), 0.0), self.network.volume_l)

    def energy_charge(self) -> float:
        atp = self.counts.get("ATP", 0.0)
        adp = self.counts.get("ADP", 0.0)
        amp = self.counts.get("AMP", 0.0)
        total = atp + adp + amp
        return (atp + 0.5 * adp) / total if total > 0 else 0.0


DivisionOutcome = Literal["none", "abscission_success", "cytokinesis_failure"]


@dataclass(frozen=True)
class WholeCellDivisionEvent:
    """A real division event in the engine state.

    Browser visuals are allowed to show daughter cells only when an event contains
    two daughter cell states. Cytokinesis failure returns one
    binucleated/polyploid state instead.
    """

    parent_index: int
    outcome: DivisionOutcome
    parent: WholeCell
    resulting_cells: tuple[WholeCell, ...]
    t_s: float

    @property
    def daughters(self) -> tuple[WholeCell, ...]:
        """Return daughter cells only for true abscission success."""
        return self.resulting_cells if self.outcome == "abscission_success" else ()


@dataclass(frozen=True)
class WholeCellPopulation:
    """One or more real hepatocyte states.

    This is the bridge from a single-cell lineage model to honest division
    visuals. A visual split must be driven by ``cells`` increasing from one to
    two, not by drawing decorative daughter shells.
    """

    cells: tuple[WholeCell, ...]
    events: tuple[WholeCellDivisionEvent, ...] = ()


def _tracked_counts_summary(cell: WholeCell) -> dict[str, float]:
    wanted = ("ATP", "ADP", "AMP", "glucose", "glucose_blood", "gene", "mRNA", "protein")
    return {species: cell.counts[species] for species in wanted if species in cell.counts}


def _organelles_snapshot(cycle: CellCycleState) -> dict[str, object]:
    organelles = cycle.organelles
    return {
        "mitochondria": organelles.mitochondria,
        "mitochondrial_fragments": organelles.mitochondrial_fragments,
        "lysosomes": organelles.lysosomes,
        "peroxisomes": organelles.peroxisomes,
        "ribosomes": organelles.ribosomes,
        "golgi_stacks": organelles.golgi_stacks,
        "golgi_fragments": organelles.golgi_fragments,
        "centrosomes": organelles.centrosomes,
        "er_mass": organelles.er_mass,
        "membrane_area": organelles.membrane_area,
    }


def _cytokinesis_snapshot(cycle: CellCycleState) -> dict[str, object]:
    cytokinesis = cycle.cytokinesis
    return {
        "stage": cytokinesis.stage,
        "spindle_axis": cytokinesis.spindle_axis,
        "division_plane_normal": cytokinesis.division_plane_normal,
        "cleavage_origin_um": cytokinesis.cleavage_origin_um,
        "ring_activity": cytokinesis.ring_activity,
        "furrow_depth": cytokinesis.furrow_depth,
        "bridge_present": cytokinesis.bridge_present,
        "midbody_present": cytokinesis.midbody_present,
        "abscission_readiness": cytokinesis.abscission_readiness,
        "chromosome_alignment": cytokinesis.chromosome_alignment,
        "nuclear_envelope_breakdown": cytokinesis.nuclear_envelope_breakdown,
        "nuclear_envelope_reform": cytokinesis.nuclear_envelope_reform,
        "membrane_supply": cytokinesis.membrane_supply,
        "bridge_tension": cytokinesis.bridge_tension,
        "mitochondrial_fragmentation": cytokinesis.mitochondrial_fragmentation,
        "golgi_fragmentation": cytokinesis.golgi_fragmentation,
        "failure_reason": cytokinesis.failure_reason,
    }


def _checkpoint_snapshot(cycle: CellCycleState, params: CellCycleParams) -> dict[str, object]:
    control = evaluate_cell_cycle_control(cycle, params)
    return {
        "g1_s_committed": control.g1_s_committed,
        "g2_m_committed": control.g2_m_committed,
        "metaphase_anaphase_permitted": control.metaphase_anaphase_permitted,
        "blocked_by": control.blocked_by,
        "supported_by": control.supported_by,
        "uncalibrated": control.uncalibrated,
        "nodes": tuple(
            {
                "node": node.node,
                "signal": node.signal,
                "active": node.active,
                "derived": node.derived,
                "source_id": node.source_id,
            }
            for node in control.nodes
        ),
        "sources": control.sources,
    }


def whole_cell_snapshot(
    cell: WholeCell,
    cell_id: str,
    *,
    parent_id: str | None = None,
    params: CellCycleParams = WHOLE_CELL_CYCLE,
) -> dict[str, object]:
    cycle = cell.cycle
    return {
        "id": cell_id,
        "parent_id": parent_id,
        "t_s": cell.t_s,
        "phase": cycle.phase,
        "phase_time_s": cycle.phase_time_s,
        "generation": cycle.generation,
        "biomass": cycle.biomass,
        "ready_to_divide": cycle.ready_to_divide,
        "nuclei": cycle.ploidy.nuclei,
        "ploidy_sets": cycle.ploidy.chromosome_sets_per_nucleus,
        "energy_charge": cell.energy_charge(),
        "counts": _tracked_counts_summary(cell),
        "organelles": _organelles_snapshot(cycle),
        "cytokinesis": _cytokinesis_snapshot(cycle),
        "checkpoint_control": _checkpoint_snapshot(cycle, params),
    }


def whole_cell_division_event_snapshot(
    event: WholeCellDivisionEvent,
    event_index: int,
    *,
    params: CellCycleParams = WHOLE_CELL_CYCLE,
) -> dict[str, object]:
    parent_id = f"event-{event_index}-parent-{event.parent_index}"
    resulting = tuple(
        whole_cell_snapshot(cell, f"event-{event_index}-cell-{i}", parent_id=parent_id, params=params)
        for i, cell in enumerate(event.resulting_cells)
    )
    return {
        "id": f"division-{event_index}",
        "parent_index": event.parent_index,
        "parent_id": parent_id,
        "outcome": event.outcome,
        "t_s": event.t_s,
        "failure_risk": cytokinesis_failure_risk(params),
        "resulting_cell_count": len(event.resulting_cells),
        "daughter_count": len(event.daughters),
        "parent": whole_cell_snapshot(event.parent, parent_id, params=params),
        "resulting_cells": resulting,
    }


def whole_cell_population_snapshot(
    population: WholeCellPopulation,
    *,
    params: CellCycleParams = WHOLE_CELL_CYCLE,
) -> dict[str, object]:
    events = tuple(
        whole_cell_division_event_snapshot(event, i, params=params)
        for i, event in enumerate(population.events)
    )
    return {
        "engine": "whole_cell_population",
        "cell_count": len(population.cells),
        "event_count": len(population.events),
        "cytokinesis_failure_risk": cytokinesis_failure_risk(params),
        "timing_profile": cell_cycle_timing_profile_snapshot(params.timing_profile),
        "cells": tuple(whole_cell_snapshot(cell, f"cell-{i}", params=params) for i, cell in enumerate(population.cells)),
        "events": events,
        "latest_event": events[-1] if events else None,
    }


def build_whole_cell_network(volume_l: float) -> ReactionNetwork:
    """Compose the subsystems into one network, plus energy/glucose homeostasis.

    Glucose is not pumped in one-way and unlimited. Instead it crosses the
    membrane through **GLUT2, which is bidirectional and gradient-driven**: when
    blood glucose is high the cell takes it up; when cell glucose is high (e.g.
    fasting glycogenolysis/gluconeogenesis) the liver releases it back to blood.
    Equal forward/back rates make the cell glucose track the blood pool, so supply
    is bounded by what's actually in the sinusoid (``glucose_blood``), not infinite.
    """
    homeostasis = ReactionNetwork(
        species=("ATP", "ADP", "glucose", "glucose_blood"),
        reactions=(
            mass_action("atp_regeneration", {"ADP": 1}, {"ATP": 1}, 0.6,
                        notes="LUMPED OXPHOS regenerating ATP against the combined draw."),
            mass_action("atp_maintenance", {"ATP": 1}, {"ADP": 1}, 0.1,
                        notes="LUMPED baseline ATP consumption."),
            mass_action("glut2_uptake", {"glucose_blood": 1}, {"glucose": 1}, 0.4,
                        notes="GLUT2 facilitated uptake (down-gradient from blood)."),
            mass_action("glut2_release", {"glucose": 1}, {"glucose_blood": 1}, 0.4,
                        notes="GLUT2 is bidirectional: glucose flows back to blood when cell glucose is high (fasting output)."),
        ),
        volume_l=volume_l,
    )
    return compose_networks(
        build_glycolysis_network(volume_l),
        build_urea_cycle_network(volume_l),
        build_redox_network(volume_l),
        build_central_dogma_network(HEPATOCYTE_ENZYME_GENE, volume_l=volume_l),
        homeostasis,
        volume_l=volume_l,
    )


def seed_whole_cell(definition: CellDefinition, *, fed: bool = True) -> WholeCell:
    """Seed every subsystem from the M030 grounded concentrations.

    ``fed=False`` starts with no glucose in the cell *or* the blood — a starved
    cell that cannot grow past the G1 size checkpoint, so it should not divide.
    When fed, ``glucose_blood`` is a buffered sinusoidal reservoir the cell
    exchanges with through GLUT2 (bidirectional), not an infinite one-way feed.
    """
    geometry = build_hepatocyte_geometry(definition)
    volume = geometry.volume_of(CYTOSOL)
    network = build_whole_cell_network(volume)

    def n(mM: float) -> float:
        return molecules_from_concentration_mM(mM, volume)

    counts = {s: 0.0 for s in network.species}
    counts.update(
        glucose=n(7.0) if fed else 0.0,
        glucose_blood=n(7.0) * 8 if fed else 0.0,  # buffered blood reservoir (~7 mM, bounded)
        ATP=n(3.5), ADP=n(1.2), AMP=n(0.3),
        NAD_plus=n(0.5), NADH=n(0.1),
        ammonia=n(0.05), ornithine=n(0.3), aspartate=n(1.0),
        GSH=n(7.0), GSSG=n(0.07), NADPH=n(0.2), NADP_plus=n(0.02), ROS=n(0.002),
        gene=float(HEPATOCYTE_ENZYME_GENE.gene_copies),
    )
    cycle = CellCycleState(counts=counts)
    return WholeCell(network=network, counts=counts, cycle=cycle, t_s=0.0)


def seed_whole_cell_population(definition: CellDefinition, *, fed: bool = True) -> WholeCellPopulation:
    """Seed a population with one real hepatocyte."""
    return WholeCellPopulation(cells=(seed_whole_cell(definition, fed=fed),))


def step_whole_cell(
    cell: WholeCell, dt_s: float, rng: EngineRng, *, params: CellCycleParams = WHOLE_CELL_CYCLE
) -> WholeCell:
    """Advance the unified reactions, then the cell cycle; divide if ready.

    Division partitions the real network counts (genome exact, metabolites/mRNA
    binomial), so the two daughters inherit a stochastic split of the actual cell
    contents.
    """
    point = simulate_hybrid(cell.network, cell.counts, dt_s, dt_s, rng, discrete_species=DISCRETE_SPECIES)
    counts = point.counts

    cyc = replace(cell.cycle, counts=counts)
    cyc = cycle_step(cyc, dt_s, params)
    counts = cyc.counts
    if cyc.ready_to_divide:
        daughter_a, _ = cycle_divide(cyc, params, rng)
        cyc = daughter_a
        counts = daughter_a.counts

    return WholeCell(network=cell.network, counts=counts, cycle=cyc, t_s=cell.t_s + dt_s)


def step_whole_cell_population(
    population: WholeCellPopulation,
    dt_s: float,
    rng: EngineRng,
    *,
    params: CellCycleParams = WHOLE_CELL_CYCLE,
) -> WholeCellPopulation:
    """Advance every cell and keep all real daughters.

    Unlike :func:`step_whole_cell`, this does not silently follow daughter A and
    discard daughter B. When abscission succeeds, the returned population contains
    both daughter cells and records a ``WholeCellDivisionEvent``.
    """
    next_cells: list[WholeCell] = []
    events: list[WholeCellDivisionEvent] = []

    for parent_index, cell in enumerate(population.cells):
        point = simulate_hybrid(cell.network, cell.counts, dt_s, dt_s, rng, discrete_species=DISCRETE_SPECIES)
        counts = point.counts
        cyc = replace(cell.cycle, counts=counts)
        cyc = cycle_step(cyc, dt_s, params)
        counts = cyc.counts
        next_t = cell.t_s + dt_s
        if cyc.ready_to_divide:
            if rng.random() < cytokinesis_failure_risk(params):
                failed_cycle = fail_cytokinesis(cyc, params)
                failed_cell = WholeCell(network=cell.network, counts=failed_cycle.counts, cycle=failed_cycle, t_s=next_t)
                resulting_cells = (failed_cell,)
                outcome: DivisionOutcome = "cytokinesis_failure"
            else:
                daughter_a_cycle, daughter_b_cycle = cycle_divide(cyc, params, rng)
                daughter_a = WholeCell(network=cell.network, counts=daughter_a_cycle.counts, cycle=daughter_a_cycle, t_s=next_t)
                daughter_b = WholeCell(network=cell.network, counts=daughter_b_cycle.counts, cycle=daughter_b_cycle, t_s=next_t)
                resulting_cells = (daughter_a, daughter_b)
                outcome = "abscission_success"
            next_cells.extend(resulting_cells)
            events.append(
                WholeCellDivisionEvent(
                    parent_index=parent_index,
                    outcome=outcome,
                    parent=WholeCell(network=cell.network, counts=counts, cycle=cyc, t_s=next_t),
                    resulting_cells=resulting_cells,
                    t_s=next_t,
                )
            )
        else:
            next_cells.append(WholeCell(network=cell.network, counts=counts, cycle=cyc, t_s=next_t))

    return WholeCellPopulation(cells=tuple(next_cells), events=tuple(events))


def run_whole_cell(
    cell: WholeCell, t_end_s: float, dt_s: float, rng: EngineRng,
    *, params: CellCycleParams = WHOLE_CELL_CYCLE
) -> tuple[WholeCell, int]:
    """Run the whole cell; return (final cell, number of divisions)."""
    divisions = 0
    steps = int(round(t_end_s / dt_s))
    for _ in range(steps):
        prev_gen = cell.cycle.generation
        cell = step_whole_cell(cell, dt_s, rng, params=params)
        if cell.cycle.generation > prev_gen:
            divisions += 1
    return cell, divisions


def run_whole_cell_population(
    population: WholeCellPopulation,
    t_end_s: float,
    dt_s: float,
    rng: EngineRng,
    *,
    params: CellCycleParams = WHOLE_CELL_CYCLE,
) -> WholeCellPopulation:
    """Run a real population, preserving all daughters created by division."""
    steps = int(round(t_end_s / dt_s))
    events: list[WholeCellDivisionEvent] = []
    for _ in range(steps):
        population = step_whole_cell_population(population, dt_s, rng, params=params)
        events.extend(population.events)
    return WholeCellPopulation(cells=population.cells, events=tuple(events))
