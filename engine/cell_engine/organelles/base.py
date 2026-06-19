from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, replace

from cell_engine.core.cell_definition import OrganelleDefinition
from cell_engine.core.random import EngineRng
from cell_engine.core.state import CellEvent, CellState, OrganelleState
from cell_engine.stochastic.hazard import HazardResult, clamp, state_conditioned_hazard


@dataclass(frozen=True)
class OrganelleStepResult:
    organelle_id: str
    next_state: OrganelleState
    hazard: HazardResult
    events: tuple[CellEvent, ...] = ()


class OrganelleModule(ABC):
    def __init__(self, definition: OrganelleDefinition) -> None:
        self.definition = definition

    @property
    def id(self) -> str:
        return self.definition.id

    def inputs(self) -> tuple[str, ...]:
        return self.definition.inputs

    def outputs(self) -> tuple[str, ...]:
        return self.definition.outputs

    def events(self) -> tuple[str, ...]:
        return self.definition.stochastic_events

    def provenance(self) -> tuple[str, ...]:
        return self.definition.source_ids

    def health(self, state: CellState) -> float:
        return state.organelles[self.id].health

    @abstractmethod
    def step(self, dt_s: float, state: CellState, rng: EngineRng) -> OrganelleStepResult:
        raise NotImplementedError


class BasicOrganelleModule(OrganelleModule):
    """Executable M016 stub shared by all organelles.

    The class intentionally updates only organelle-local state: age, activity,
    risk, damage and health. Pool fluxes come in the metabolism/cargo milestones.
    """

    def step(self, dt_s: float, state: CellState, rng: EngineRng) -> OrganelleStepResult:
        current = state.organelles[self.id]
        hazard = state_conditioned_hazard(self.id, current, state, dt_s=dt_s)
        input_availability = self._input_availability(state)
        stress_penalty = 1.0 - 0.35 * hazard.stress_load
        activity = clamp(current.capacity * current.health * input_availability * stress_penalty, 0.0, 1.25)

        event_damage = 0.0
        events: list[CellEvent] = []
        if rng.random() < hazard.event_probability:
            event_damage = 0.025 + 0.035 * hazard.stress_load
            events.append(
                CellEvent(
                    id=f"{self.id}_hazard_{int(state.elapsed_s + dt_s)}",
                    t_s=state.elapsed_s + dt_s,
                    severity="warn" if hazard.stress_load < 0.75 else "crit",
                    text=f"{self.definition.label} hazard event biased by {hazard.dominant_axis}.",
                )
            )

        passive_damage = hazard.probability_per_hour * dt_s / 3600.0 * 0.05
        repair = 0.012 * current.health * dt_s / 3600.0
        next_damage = clamp(current.damage + passive_damage + event_damage - repair, 0.0, 1.0)
        next_health = clamp(1.0 - next_damage, 0.0, 1.0)

        return OrganelleStepResult(
            organelle_id=self.id,
            hazard=hazard,
            next_state=replace(
                current,
                activity=activity,
                age_h=current.age_h + dt_s / 3600.0,
                damage=next_damage,
                health=next_health,
                risk_per_hour=hazard.probability_per_hour,
                active_processes=self.definition.functions[:3],
            ),
            events=tuple(events),
        )

    def _input_availability(self, state: CellState) -> float:
        values: list[float] = []
        for input_id in self.definition.inputs:
            if input_id == "ATP":
                values.append(clamp(state.organelles[self.id].local_atp, 0.0, 1.0))
                continue
            pool = state.pools.get(input_id)
            if pool is not None:
                values.append(clamp(pool.value, 0.0, 1.0))
        if not values:
            return 0.78
        return clamp(0.25 + 0.75 * min(values), 0.0, 1.0)
