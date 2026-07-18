from __future__ import annotations

from dataclasses import dataclass, field, replace

from cell_engine.core.cell_definition import CellDefinition
from cell_engine.core.engine import step_cell
from cell_engine.core.random import EngineRng
from cell_engine.core.serialization import to_plain
from cell_engine.core.state import CellState
from cell_engine.core.expression import apply_functional_perturbation


@dataclass(frozen=True)
class Scenario:
    id: str
    description: str
    interventions: dict[str, float]
    controls: dict[str, float | str] = field(default_factory=dict)


@dataclass(frozen=True)
class TrajectoryFrame:
    step: int
    elapsed_s: float
    status: str
    pools: dict[str, float]
    stress: dict[str, float]
    response: dict[str, object] | None = None


@dataclass(frozen=True)
class ScenarioResult:
    scenario: Scenario
    frames: tuple[TrajectoryFrame, ...]
    final_status: str

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


BASELINE_SCENARIO = Scenario(
    id="baseline",
    description="Healthy reference hepatocyte",
    interventions={},
    controls={"experiment_id": "baseline", "intervention_type": "healthy_reference"},
)
DETOX_LOAD_SCENARIO = Scenario(id="detox_load", description="High xenobiotic load", interventions={"xenobiotic": 0.9})
ENERGY_STARVATION_SCENARIO = Scenario(id="energy_starvation", description="Low ATP stress", interventions={"ATP": 0.12, "ADP": 0.78, "AMP": 0.10})
BSEP_LOSS_SCENARIO = Scenario(
    id="bsep_loss",
    description="Exact BSEP/ABCB11 loss-of-function experiment",
    interventions={},
    controls={"experiment_id": "bsep_loss", "intervention_type": "genetic_abcb11_loss", "bsep_surface_activity": 0.0},
)
MRP2_LOSS_SCENARIO = Scenario(
    id="mrp2_loss",
    description="Exact MRP2/ABCC2 loss-of-function experiment",
    interventions={},
    controls={"experiment_id": "mrp2_loss", "intervention_type": "genetic_abcc2_loss", "mrp2_surface_activity": 0.0},
)
CANALICULAR_EXPORT_LOSS_SCENARIO = Scenario(
    id="canalicular_export_loss",
    description="Exact combined BSEP and MRP2 loss-of-function experiment",
    interventions={},
    controls={
        "experiment_id": "canalicular_export_loss",
        "intervention_type": "combined_genetic_abcb11_abcc2_loss",
        "bsep_surface_activity": 0.0,
        "mrp2_surface_activity": 0.0,
    },
)

CURATED_EXPERIMENTS = {
    scenario.id: scenario
    for scenario in (
        BASELINE_SCENARIO,
        BSEP_LOSS_SCENARIO,
        MRP2_LOSS_SCENARIO,
        CANALICULAR_EXPORT_LOSS_SCENARIO,
    )
}


def run_scenario(
    definition: CellDefinition,
    initial_state: CellState,
    scenario: Scenario,
    *,
    dt_s: float,
    steps: int,
    seed: int,
) -> ScenarioResult:
    state = apply_scenario(initial_state, scenario)
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


def apply_scenario(state: CellState, scenario: Scenario) -> CellState:
    """Apply pools and explicit experimental controls without silent defaults."""
    intervened = apply_interventions(state, scenario.interventions)
    controls = {**intervened.model_controls, **scenario.controls}
    controls.setdefault("experiment_id", scenario.id)
    expression = intervened.gene_expression
    if expression is not None:
        for control_id, gene_symbol in (
            ("bsep_surface_activity", "ABCB11"),
            ("mrp2_surface_activity", "ABCC2"),
        ):
            if control_id not in scenario.controls:
                continue
            expression = apply_functional_perturbation(
                expression,
                gene_symbol=gene_symbol,
                activity_scale=float(scenario.controls[control_id]),
                event_id=f"experiment-{scenario.id}-{gene_symbol}",
                t_s=intervened.elapsed_s,
                source_id=f"experiment:{scenario.id}",
                evidence=scenario.description,
            )
    return replace(intervened, model_controls=controls, gene_expression=expression)


def _frame(step: int, state: CellState) -> TrajectoryFrame:
    tracked_pools = {
        id: state.pools[id].value
        for id in (
            "ATP",
            "ADP",
            "AMP",
            "ROS",
            "xenobiotic",
            "detoxified_xenobiotic",
            "GSH",
            "urea",
            "bile_acids",
            "canalicular_bile_acids",
            "bilirubin_conjugates",
            "canalicular_bilirubin_conjugates",
        )
        if id in state.pools
    }
    return TrajectoryFrame(
        step=step,
        elapsed_s=state.elapsed_s,
        status=state.status,
        pools=tracked_pools,
        stress=dict(state.stress),
        response=state.cellular_response.to_dict() if state.cellular_response else None,
    )
