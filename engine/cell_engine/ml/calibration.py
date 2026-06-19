from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from cell_engine.core.cell_definition import CellDefinition
from cell_engine.core.serialization import to_plain
from cell_engine.core.state import CellState
from cell_engine.validation.experiments import Scenario, run_scenario


@dataclass(frozen=True)
class CalibrationTarget:
    id: str
    path: str
    expected: float
    tolerance: float
    weight: float = 1.0
    unit: str = ""
    source_id: str = ""
    notes: str = ""


@dataclass(frozen=True)
class CalibrationCandidate:
    id: str
    interventions: dict[str, float] = field(default_factory=dict)
    notes: str = ""


@dataclass(frozen=True)
class CalibrationResidual:
    target_id: str
    path: str
    observed: float
    expected: float
    tolerance: float
    weight: float
    normalized_error: float
    weighted_error: float
    unit: str = ""


@dataclass(frozen=True)
class CalibrationRun:
    candidate_id: str
    scenario_id: str
    residuals: tuple[CalibrationResidual, ...]
    normalized_error: float
    fit_score: float
    final_status: str
    provenance: str

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


BASELINE_HEPATOCYTE_TARGETS = (
    CalibrationTarget(
        id="baseline_atp",
        path="pools.ATP",
        expected=0.72,
        tolerance=0.18,
        weight=1.2,
        unit="relative_pool_0_1",
        source_id="project_roadmap_07",
        notes="Placeholder baseline energy target until curated hepatocyte concentration data is linked.",
    ),
    CalibrationTarget(
        id="baseline_ros",
        path="pools.ROS",
        expected=0.04,
        tolerance=0.16,
        weight=1.0,
        unit="relative_pool_0_1",
        source_id="project_roadmap_07",
        notes="Coarse low-ROS target; intentionally wide while model constants are placeholders.",
    ),
    CalibrationTarget(
        id="baseline_energy_stress",
        path="stress.energy",
        expected=0.0,
        tolerance=0.30,
        weight=1.0,
        unit="dimensionless",
        source_id="project_roadmap_07",
    ),
)


def evaluate_calibration(
    definition: CellDefinition,
    initial_state: CellState,
    scenario: Scenario,
    targets: Iterable[CalibrationTarget],
    *,
    candidate: CalibrationCandidate | None = None,
    dt_s: float,
    steps: int,
    seed: int,
) -> CalibrationRun:
    calibration_candidate = candidate or CalibrationCandidate(id="default", interventions={})
    merged_scenario = Scenario(
        id=scenario.id,
        description=scenario.description,
        interventions={**scenario.interventions, **calibration_candidate.interventions},
    )
    scenario_result = run_scenario(definition, initial_state, merged_scenario, dt_s=dt_s, steps=steps, seed=seed)
    final_frame = scenario_result.frames[-1]
    residuals = tuple(_residual(target, to_plain(final_frame)) for target in targets)
    total_weight = sum(residual.weight for residual in residuals) or 1.0
    normalized_error = sum(residual.weighted_error for residual in residuals) / total_weight
    fit_score = 1.0 / (1.0 + normalized_error)
    return CalibrationRun(
        candidate_id=calibration_candidate.id,
        scenario_id=scenario.id,
        residuals=residuals,
        normalized_error=normalized_error,
        fit_score=fit_score,
        final_status=scenario_result.final_status,
        provenance="calibration_runner_v1_does_not_mutate_cell_rules",
    )


def rank_calibration_candidates(
    definition: CellDefinition,
    initial_state: CellState,
    scenario: Scenario,
    targets: Iterable[CalibrationTarget],
    candidates: Iterable[CalibrationCandidate],
    *,
    dt_s: float,
    steps: int,
    seed: int,
) -> tuple[CalibrationRun, ...]:
    runs = [
        evaluate_calibration(
            definition,
            initial_state,
            scenario,
            targets,
            candidate=candidate,
            dt_s=dt_s,
            steps=steps,
            seed=seed,
        )
        for candidate in candidates
    ]
    return tuple(sorted(runs, key=lambda run: run.normalized_error))


def _residual(target: CalibrationTarget, frame: Mapping[str, object]) -> CalibrationResidual:
    observed = float(_read_path(frame, target.path))
    tolerance = max(target.tolerance, 1e-9)
    normalized_error = abs(observed - target.expected) / tolerance
    weighted_error = normalized_error * target.weight
    return CalibrationResidual(
        target_id=target.id,
        path=target.path,
        observed=observed,
        expected=target.expected,
        tolerance=tolerance,
        weight=target.weight,
        normalized_error=normalized_error,
        weighted_error=weighted_error,
        unit=target.unit,
    )


def _read_path(data: Mapping[str, object], path: str) -> object:
    current: object = data
    for segment in path.split("."):
        if not isinstance(current, Mapping) or segment not in current:
            raise KeyError(f"Calibration path not found: {path}")
        current = current[segment]
    return current
