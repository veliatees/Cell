from __future__ import annotations

from cell_engine.quantitative.metabolic_constraint_shell import (
    metabolic_constraint_shell_snapshot,
    validate_metabolic_constraint_shell,
)


def test_constraint_shell_pins_artifact_but_stays_non_executable_without_phh_context() -> None:
    snapshot = metabolic_constraint_shell_snapshot()
    validate_metabolic_constraint_shell(snapshot)
    assert snapshot["version"] == "metabolic_constraint_shell_v4"
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
    assert reconstruction["mass_charge_balance_audited_in_project"] is True
    audit = reconstruction["structural_audit"]
    assert audit["one_sided_reaction_count"] == 1660
    assert audit["two_sided_reaction_count"] == 11271
    assert audit["elementally_assessable_reaction_count"] == 9849
    assert audit["elementally_balanced_reaction_count"] == 9832
    assert audit["elementally_imbalanced_reaction_count"] == 17
    assert audit["jointly_unassessable_reaction_count"] == 1422
    assert snapshot["optimization_problem"]["objective"] is None
    assert snapshot["optimization_problem"]["boundary_fluxes"] is None
    numerics = snapshot["generic_constraint_numerics"]
    assert numerics["backend"] == "scipy.optimize.linprog"
    assert numerics["backend_version"] == "1.17.1"
    assert numerics["analytic_fixture_pass_count"] == 5
    assert numerics["human_gem_loaded"] is False
    assert numerics["biological_flux_authority"] is False
    bundle = snapshot["phh_execution_bundle_intake"]
    assert bundle["required_artifact_count"] == 10
    assert bundle["delivered_bundle_count"] == 0
    assert bundle["structurally_complete_bundle_count"] == 0
    assert bundle["runtime_flux_coupling_allowed"] is False
    assert not any(snapshot["gates"].values())


def test_exact_release_pin_removed_only_the_artifact_identity_blocker() -> None:
    snapshot = metabolic_constraint_shell_snapshot()
    blockers = snapshot["blockers"]
    assert not any("release and checksum are not pinned" in item for item in blockers)
    assert any("healthy-PHH context extraction" in item for item in blockers)
    assert any("independent flux validation" in item for item in blockers)
    assert not any("have not been audited" in item for item in blockers)
    assert any("structural audit exceptions" in item for item in blockers)
