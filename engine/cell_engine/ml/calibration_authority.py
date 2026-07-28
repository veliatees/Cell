"""Scientific-use boundary for legacy relative-pool fixture scoring."""

from __future__ import annotations

from typing import Literal


VERSION = "legacy_calibration_authority_v1"

LegacyCalibrationPurpose = Literal[
    "software_fixture_evaluation",
    "exploratory_candidate_ranking",
    "biological_parameter_calibration",
    "quantitative_validation",
    "predictive_model_selection",
]


class LegacyCalibrationAuthorityError(RuntimeError):
    """Raised when schematic fixture scoring is requested for scientific use."""


_BUILT_IN_TARGET_CONTRACTS = (
    {
        "id": "baseline_atp",
        "path": "pools.ATP",
        "unit": "relative_pool_0_1",
        "evidence_authority": "schematic_project_fixture",
        "biological_parameter_authority": False,
    },
    {
        "id": "baseline_ros",
        "path": "pools.ROS",
        "unit": "relative_pool_0_1",
        "evidence_authority": "schematic_project_fixture",
        "biological_parameter_authority": False,
    },
    {
        "id": "baseline_energy_stress",
        "path": "stress.energy",
        "unit": "dimensionless",
        "evidence_authority": "schematic_project_fixture",
        "biological_parameter_authority": False,
    },
)


def assert_legacy_calibration_authority(
    purpose: LegacyCalibrationPurpose,
) -> None:
    allowed = {
        "software_fixture_evaluation": True,
        "exploratory_candidate_ranking": True,
        "biological_parameter_calibration": False,
        "quantitative_validation": False,
        "predictive_model_selection": False,
    }
    if purpose not in allowed:
        raise ValueError(f"Unsupported legacy calibration purpose: {purpose}")
    if not allowed[purpose]:
        raise LegacyCalibrationAuthorityError(
            f"{purpose} is blocked for legacy relative-pool fixture scoring: "
            "the built-in targets are project placeholders, the whole-cell dynamics "
            "are not calibrated to matched PHH measurements, and no donor-disjoint "
            "held-out validation authorizes parameter fitting or model selection"
        )


def legacy_calibration_authority_snapshot() -> dict[str, object]:
    payload: dict[str, object] = {
        "version": VERSION,
        "status": "software_fixture_only",
        "explicit_purpose_required": True,
        "allowed_purposes": (
            "software_fixture_evaluation",
            "exploratory_candidate_ranking",
        ),
        "blocked_purposes": (
            "biological_parameter_calibration",
            "quantitative_validation",
            "predictive_model_selection",
        ),
        "built_in_targets": _BUILT_IN_TARGET_CONTRACTS,
        "gates": {
            "biological_parameter_calibration_allowed": False,
            "quantitative_validation_allowed": False,
            "predictive_model_selection_allowed": False,
            "automatic_cell_rule_mutation_allowed": False,
        },
        "summary": {
            "audited_workflow_count": 3,
            "built_in_target_count": len(_BUILT_IN_TARGET_CONTRACTS),
            "placeholder_target_count": len(_BUILT_IN_TARGET_CONTRACTS),
            "source_backed_target_count": 0,
            "biologically_authorized_target_count": 0,
            "scientific_authority_purpose_count": 0,
        },
        "policy": (
            "Residuals and fixture-fit scores may test deterministic software behavior "
            "or rank exploratory candidates only. They are not parameter estimates, "
            "biological validation results or predictive model-selection evidence."
        ),
    }
    validate_legacy_calibration_authority_snapshot(payload)
    return payload


def validate_legacy_calibration_authority_snapshot(
    payload: dict[str, object],
) -> None:
    if (
        payload.get("version") != VERSION
        or payload.get("status") != "software_fixture_only"
        or payload.get("explicit_purpose_required") is not True
    ):
        raise ValueError("legacy calibration authority identity changed")
    summary = payload.get("summary")
    gates = payload.get("gates")
    targets = payload.get("built_in_targets")
    if (
        not isinstance(summary, dict)
        or not isinstance(gates, dict)
        or not isinstance(targets, tuple)
    ):
        raise ValueError("legacy calibration authority snapshot is malformed")
    expected_target_ids = (
        "baseline_atp",
        "baseline_ros",
        "baseline_energy_stress",
    )
    if (
        len(targets) != len(expected_target_ids)
        or any(not isinstance(target, dict) for target in targets)
        or tuple(target["id"] for target in targets) != expected_target_ids
    ):
        raise ValueError("legacy calibration fixture-target identity changed")
    if (
        summary.get("audited_workflow_count") != 3
        or summary.get("built_in_target_count") != 3
        or summary.get("placeholder_target_count") != 3
        or summary.get("source_backed_target_count") != 0
        or summary.get("biologically_authorized_target_count") != 0
        or summary.get("scientific_authority_purpose_count") != 0
    ):
        raise ValueError("legacy calibration target authority changed")
    if any(bool(value) for value in gates.values()):
        raise ValueError("legacy calibration escaped its scientific-use firewall")
    if any(
        target.get("evidence_authority") != "schematic_project_fixture"
        or bool(target.get("biological_parameter_authority"))
        for target in targets
    ):
        raise ValueError("legacy calibration target gained biological authority")
