from __future__ import annotations

from dataclasses import dataclass, replace

from cell_engine.core.cell_definition import CellDefinition
from cell_engine.core.engine import step_cell
from cell_engine.core.random import EngineRng
from cell_engine.core.serialization import to_plain
from cell_engine.core.state import CellState


@dataclass(frozen=True)
class Scenario:
    id: str
    description: str
    interventions: dict[str, float]


@dataclass(frozen=True)
class TrajectoryFrame:
    step: int
    elapsed_s: float
    status: str
    pools: dict[str, float]
    stress: dict[str, float]


@dataclass(frozen=True)
class ScenarioResult:
    scenario: Scenario
    frames: tuple[TrajectoryFrame, ...]
    final_status: str

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


BASELINE_SCENARIO = Scenario(id="baseline", description="Fed baseline hepatocyte", interventions={})
DETOX_LOAD_SCENARIO = Scenario(id="detox_load", description="High xenobiotic load", interventions={"xenobiotic": 0.9})
ENERGY_STARVATION_SCENARIO = Scenario(id="energy_starvation", description="Low ATP stress", interventions={"ATP": 0.12, "ADP": 0.78, "AMP": 0.10})


def run_scenario(
    definition: CellDefinition,
    initial_state: CellState,
    scenario: Scenario,
    *,
    dt_s: float,
    steps: int,
    seed: int,
) -> ScenarioResult:
    state = apply_interventions(initial_state, scenario.interventions)
    rng = EngineRng(seed)
    frames = [_frame(0, state)]
    for step in range(1, steps + 1):
        state = step_cell(definition, state, dt_s, rng=rng)
        frames.append(_frame(step, state))
    return ScenarioResult(scenario=scenario, frames=tuple(frames), final_status=state.status)


def apply_interventions(state: CellState, interventions: dict[str, float]) -> CellState:
    pools = dict(state.pools)
    for pool_id, value in interventions.items():
        if pool_id in pools:
            pools[pool_id] = replace(pools[pool_id], value=max(0.0, value))
    return replace(state, pools=pools)


def _frame(step: int, state: CellState) -> TrajectoryFrame:
    tracked_pools = {
        id: state.pools[id].value
        for id in ("ATP", "ADP", "AMP", "ROS", "xenobiotic", "detoxified_xenobiotic", "GSH", "urea", "bile_acids")
        if id in state.pools
    }
    return TrajectoryFrame(
        step=step,
        elapsed_s=state.elapsed_s,
        status=state.status,
        pools=tracked_pools,
        stress=dict(state.stress),
    )

