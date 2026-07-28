from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Literal

from cell_engine.core.cell_definition import CellDefinition
from cell_engine.core.serialization import to_plain
from cell_engine.core.state import CellState
from cell_engine.ml.calibration_authority import (
    LegacyCalibrationPurpose,
    assert_legacy_calibration_authority,
    legacy_calibration_authority_snapshot,
)
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
    evidence_authority: Literal[
        "schematic_project_fixture",
        "source_backed_observation",
    ] = "schematic_project_fixture"


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
    fixture_fit_score: float
    final_status: str
    execution_purpose: LegacyCalibrationPurpose
    score_authority: Literal["software_fixture_only"]
    biological_parameter_calibration_allowed: Literal[False]
    quantitative_validation_allowed: Literal[False]
    predictive_model_selection_allowed: Literal[False]
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
        evidence_authority="schematic_project_fixture",
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
        evidence_authority="schematic_project_fixture",
    ),
    CalibrationTarget(
        id="baseline_energy_stress",
        path="stress.energy",
        expected=0.0,
        tolerance=0.30,
        weight=1.0,
        unit="dimensionless",
        source_id="project_roadmap_07",
        notes="Project fixture target; not a measured healthy-PHH stress observation.",
        evidence_authority="schematic_project_fixture",
    ),
)


def validate_builtin_calibration_targets() -> None:
    contracts = legacy_calibration_authority_snapshot()["built_in_targets"]
    expected = {
        contract["id"]: contract
        for contract in contracts
        if isinstance(contract, dict)
    }
    actual = {target.id: target for target in BASELINE_HEPATOCYTE_TARGETS}
    if set(actual) != set(expected):
        raise ValueError("legacy calibration built-in target identity changed")
    for target_id, target in actual.items():
        contract = expected[target_id]
        if (
            target.path != contract["path"]
            or target.unit != contract["unit"]
            or target.evidence_authority != contract["evidence_authority"]
        ):
            raise ValueError(
                f"legacy calibration target contract changed: {target_id}"
            )


validate_builtin_calibration_targets()


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
    purpose: LegacyCalibrationPurpose,
) -> CalibrationRun:
    assert_legacy_calibration_authority(purpose)
    calibration_candidate = candidate or CalibrationCandidate(id="default", interventions={})
    merged_scenario = Scenario(
        id=scenario.id,
        description=scenario.description,
        interventions={**scenario.interventions, **calibration_candidate.interventions},
    )
    scenario_result = run_scenario(
        definition,
        initial_state,
        merged_scenario,
        dt_s=dt_s,
        steps=steps,
        seed=seed,
        purpose="exploratory_execution",
    )
    final_frame = scenario_result.frames[-1]
    residuals = tuple(_residual(target, to_plain(final_frame)) for target in targets)
    total_weight = sum(residual.weight for residual in residuals) or 1.0
    normalized_error = sum(residual.weighted_error for residual in residuals) / total_weight
    fixture_fit_score = 1.0 / (1.0 + normalized_error)
    return CalibrationRun(
        candidate_id=calibration_candidate.id,
        scenario_id=scenario.id,
        residuals=residuals,
        normalized_error=normalized_error,
        fixture_fit_score=fixture_fit_score,
        final_status=scenario_result.final_status,
        execution_purpose=purpose,
        score_authority="software_fixture_only",
        biological_parameter_calibration_allowed=False,
        quantitative_validation_allowed=False,
        predictive_model_selection_allowed=False,
        provenance=(
            "legacy_calibration_authority_v1_software_fixture_only_"
            "does_not_mutate_cell_rules"
        ),
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
    purpose: LegacyCalibrationPurpose,
) -> tuple[CalibrationRun, ...]:
    assert_legacy_calibration_authority(purpose)
    if purpose != "exploratory_candidate_ranking":
        raise ValueError(
            "candidate ranking requires purpose='exploratory_candidate_ranking'"
        )
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
            purpose=purpose,
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
