from __future__ import annotations

from cell_engine.quantitative.metabolic_constraint_shell import (
    metabolic_constraint_shell_snapshot,
    validate_metabolic_constraint_shell,
)


def test_constraint_shell_stays_non_executable_until_artifact_and_context_are_pinned() -> None:
    snapshot = metabolic_constraint_shell_snapshot()
    validate_metabolic_constraint_shell(snapshot)
    assert snapshot["candidate_reconstruction"]["model_version"] is None
    assert snapshot["candidate_reconstruction"]["artifact_sha256"] is None
    assert snapshot["optimization_problem"]["objective"] is None
    assert snapshot["optimization_problem"]["boundary_fluxes"] is None
    assert not any(snapshot["gates"].values())
