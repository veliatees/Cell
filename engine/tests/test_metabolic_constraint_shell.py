from __future__ import annotations

from cell_engine.quantitative.metabolic_constraint_shell import (
    metabolic_constraint_shell_snapshot,
    validate_metabolic_constraint_shell,
)


def test_constraint_shell_pins_artifact_but_stays_non_executable_without_phh_context() -> None:
    snapshot = metabolic_constraint_shell_snapshot()
    validate_metabolic_constraint_shell(snapshot)
    reconstruction = snapshot["candidate_reconstruction"]
    assert reconstruction["model_version"] == "2.0.0"
    assert reconstruction["release_tag"] == "v2.0.0"
    assert reconstruction["release_commit"] == "635f533152dc5f7290ce04d12700eaa882273c3e"
    assert reconstruction["artifact_sha256"] == "cc5a4383c6116b0c91f4db089cc640f29aec7e840249b573b74d3792c9ca4a7a"
    assert reconstruction["artifact_size_bytes"] == 43115559
    assert reconstruction["structural_counts_verified_from_sbml"] == {
        "compartments": 9,
        "metabolites": 8461,
        "reactions": 12931,
        "genes": 2848,
    }
    assert reconstruction["sbml_path"] is None
    assert reconstruction["model_loaded_by_runtime"] is False
    assert snapshot["optimization_problem"]["objective"] is None
    assert snapshot["optimization_problem"]["boundary_fluxes"] is None
    assert not any(snapshot["gates"].values())


def test_exact_release_pin_removed_only_the_artifact_identity_blocker() -> None:
    snapshot = metabolic_constraint_shell_snapshot()
    blockers = snapshot["blockers"]
    assert not any("release and checksum are not pinned" in item for item in blockers)
    assert any("healthy-PHH context extraction" in item for item in blockers)
    assert any("independent flux validation" in item for item in blockers)
