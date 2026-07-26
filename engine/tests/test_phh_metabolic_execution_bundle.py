from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from cell_engine.quantitative.constraint_numerics import (
    DUAL_FEASIBILITY_TOLERANCE,
    OBJECTIVE_ABSOLUTE_TOLERANCE,
    PINNED_SCIPY_VERSION,
    PRIMAL_FEASIBILITY_TOLERANCE,
    SOLVER_METHOD,
)
from cell_engine.quantitative.phh_metabolic_execution_bundle import (
    HUMAN_GEM_RELEASE_COMMIT,
    HUMAN_GEM_SHA256,
    PHHMetabolicExecutionBundleError,
    load_phh_metabolic_execution_bundle,
    load_phh_metabolic_execution_bundle_contract,
    phh_metabolic_execution_bundle_intake_snapshot,
    validate_phh_metabolic_execution_bundle_intake_snapshot,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _reference(path: Path) -> dict[str, str]:
    return {"path": str(path), "sha256": _sha256(path)}


def _write_csv(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


def _bundle_fixture(tmp_path: Path) -> tuple[Path, dict[str, object], dict[str, Path]]:
    contract = load_phh_metabolic_execution_bundle_contract()
    context_model = tmp_path / "context-model.xml"
    context_model.write_text("<model id=\"synthetic-test-only\"/>\n", encoding="utf-8")
    model_sha = _sha256(context_model)

    solver = tmp_path / "solver.json"
    _write_json(
        solver,
        {
            "schema_version": "cell.constraint-solver-manifest.v1",
            "backend": "scipy.optimize.linprog",
            "backend_version": PINNED_SCIPY_VERSION,
            "method": SOLVER_METHOD,
            "primal_feasibility_tolerance": PRIMAL_FEASIBILITY_TOLERANCE,
            "dual_feasibility_tolerance": DUAL_FEASIBILITY_TOLERANCE,
            "objective_absolute_tolerance": OBJECTIVE_ABSOLUTE_TOLERANCE,
        },
    )
    solver_sha = _sha256(solver)

    extraction = tmp_path / "extraction.json"
    _write_json(
        extraction,
        {
            "schema_version": "cell.phh-context-extraction-report.v1",
            "algorithm_name": "declared_test_extractor",
            "algorithm_version": "1.0.0",
            "algorithm_code_sha256": "1" * 64,
            "input_artifact_sha256s": ["2" * 64],
            "generated_context_model_sha256": model_sha,
            "included_reaction_count": 3,
            "excluded_reaction_count": 1,
            "deterministic_reproduction_pass": True,
            "reaction_identity_audit_pass": True,
            "structural_exception_resolution_complete": True,
            "automatic_imputation_used": False,
        },
    )

    scale = tmp_path / "scale.json"
    _write_json(
        scale,
        {
            "schema_version": "cell.phh-flux-scale-operator.v1",
            "operator_id": "frozen-scale-operator",
            "source_units": ["pmol/1e6_cells/min"],
            "target_model_unit": "mmol/gDW/h",
            "equation": "source value divided by measured matched dry mass",
            "denominator_definition": "matched measured dry mass; no default cell mass",
            "uncertainty_propagation": "source interval and dry-mass interval retained",
            "same_context_validation_pass": True,
            "automatic_unit_conversion": False,
        },
    )

    exchange = tmp_path / "exchange.csv"
    _write_csv(
        exchange,
        contract["exchange_bounds_header"],
        [
            {
                "reaction_id": "EX_glc",
                "source_study_id": "study-dev",
                "donor_or_cohort_id": "donor-dev",
                "split_role": "calibration",
                "raw_lower": "1",
                "raw_upper": "2",
                "raw_unit": "pmol/1e6_cells/min",
                "model_lower": "0.1",
                "model_upper": "0.2",
                "model_unit": "mmol/gDW/h",
                "measurement_operator_id": "operator-dev",
                "assay": "direct exchange assay",
                "uncertainty_description": "source interval",
                "manual_primary_source_review_status": "pass",
            }
        ],
    )

    objective = tmp_path / "objective.json"
    _write_json(
        objective,
        {
            "schema_version": "cell.phh-fba-objective.v1",
            "objective_id": "measured-export-objective",
            "reaction_coefficients": {"R_export": 1.0},
            "model_flux_unit": "mmol/gDW/h",
            "measurement_source_ids": ["study-dev"],
            "measurement_operator_id": "operator-dev",
            "directly_measured_in_matched_phh_context": True,
            "automatic_objective_selection": False,
        },
    )

    fba = tmp_path / "fba.json"
    _write_json(
        fba,
        {
            "schema_version": "cell.phh-fba-result.v1",
            "context_model_sha256": model_sha,
            "solver_manifest_sha256": solver_sha,
            "status": "optimal",
            "objective_value": 1.0,
            "max_mass_balance_residual": 0.0,
            "max_bound_violation": 0.0,
        },
    )
    fva = tmp_path / "fva.json"
    _write_json(
        fva,
        {
            "schema_version": "cell.phh-fva-result.v1",
            "context_model_sha256": model_sha,
            "solver_manifest_sha256": solver_sha,
            "fraction_of_optimum": 1.0,
            "reaction_range_count": 3,
            "all_ranges_finite": True,
        },
    )
    infeasibility = tmp_path / "infeasibility.json"
    _write_json(
        infeasibility,
        {
            "schema_version": "cell.phh-infeasibility-report.v1",
            "context_model_sha256": model_sha,
            "status": "feasible_no_relaxation_required",
            "minimum_total_mass_balance_slack": 0.0,
            "bound_relaxation_used": False,
            "reaction_or_metabolite_deletion_used": False,
        },
    )
    validation = tmp_path / "validation.csv"
    _write_csv(
        validation,
        contract["independent_validation_header"],
        [
            {
                "reaction_id": "EX_glc",
                "source_study_id": "study-heldout",
                "donor_or_cohort_id": "donor-heldout",
                "split_role": "independent_heldout",
                "observed_value": "1.5",
                "observed_unit": "mmol/gDW/h",
                "predicted_value": "1.4",
                "predicted_unit": "mmol/gDW/h",
                "uncertainty_value": "0.2",
                "uncertainty_type": "source interval",
                "measurement_operator_id": "operator-heldout",
                "assay": "independent direct exchange assay",
                "manual_primary_source_review_status": "pass",
            }
        ],
    )

    artifacts = {
        "context_model": context_model,
        "context_extraction_report": extraction,
        "exchange_bounds": exchange,
        "objective_specification": objective,
        "scale_conversion_report": scale,
        "solver_manifest": solver,
        "fba_result": fba,
        "fva_result": fva,
        "infeasibility_report": infeasibility,
        "independent_validation": validation,
    }
    payload: dict[str, object] = {
        "schema_version": "cell.phh-metabolic-execution-bundle.v1",
        "bundle_id": "synthetic-structural-test-bundle",
        "candidate_reconstruction": {
            "model_family": "Human-GEM",
            "model_version": "2.0.0",
            "release_commit": HUMAN_GEM_RELEASE_COMMIT,
            "artifact_sha256": HUMAN_GEM_SHA256,
        },
        "context": {
            "species": "Homo sapiens",
            "biological_system": "primary_human_hepatocyte_freshly_isolated",
            "tissue_health_state": "healthy_non_diseased",
            "donor_or_cohort_id": "cohort-dev",
            "preparation_context": "freshly_isolated",
            "culture_format": "source-defined short-term PHH",
            "nutritional_state": "matched source context",
            "liver_zone": "measured_or_unresolved",
            "oxygen_context": "measured source oxygen context",
            "temperature_c": 37.0,
            "sampling_timepoint": "source-defined endpoint",
        },
        "splits": {
            "development_donor_ids": ["donor-dev"],
            "development_study_ids": ["study-dev"],
            "heldout_donor_ids": ["donor-heldout"],
            "heldout_study_ids": ["study-heldout"],
        },
        "artifacts": {key: _reference(value) for key, value in artifacts.items()},
        "frozen_before_heldout_access": True,
        "manual_primary_source_review_status": "pass",
        "permissions": {
            "automatic_fba_execution": False,
            "automatic_runtime_flux_coupling": False,
            "automatic_dynamic_rate_initialization": False,
        },
    }
    bundle = tmp_path / "bundle.json"
    _write_json(bundle, payload)
    return bundle, payload, artifacts


def test_contract_and_empty_snapshot_are_fail_closed(tmp_path: Path) -> None:
    contract = load_phh_metabolic_execution_bundle_contract()
    assert contract["contract_id"] == "phh_metabolic_execution_bundle_contract_v1"
    assert len(contract["required_artifacts"]) == 10

    snapshot = phh_metabolic_execution_bundle_intake_snapshot(
        tmp_path / "missing.json"
    )
    validate_phh_metabolic_execution_bundle_intake_snapshot(snapshot)
    assert snapshot["delivered_bundle_count"] == 0
    assert snapshot["generic_solver_fixture_pass_count"] == 5
    assert snapshot["fba_execution_allowed"] is False


def test_complete_bundle_is_structurally_verified_but_not_executed(
    tmp_path: Path,
) -> None:
    bundle_path, _, _ = _bundle_fixture(tmp_path)
    bundle = load_phh_metabolic_execution_bundle(bundle_path)
    snapshot = phh_metabolic_execution_bundle_intake_snapshot(bundle_path)
    validate_phh_metabolic_execution_bundle_intake_snapshot(snapshot)

    assert bundle.structurally_complete is True
    assert bundle.exchange_bound_count == 1
    assert bundle.independent_validation_record_count == 1
    assert bundle.fba_execution_allowed is False
    assert bundle.runtime_flux_coupling_allowed is False
    assert snapshot["structurally_complete_bundle_count"] == 1
    assert snapshot["verified_artifact_count"] == 10
    assert snapshot["runtime_flux_coupling_allowed"] is False


def test_artifact_checksum_mismatch_is_rejected(tmp_path: Path) -> None:
    bundle_path, payload, _ = _bundle_fixture(tmp_path)
    payload["artifacts"]["context_model"]["sha256"] = "0" * 64  # type: ignore[index]
    _write_json(bundle_path, payload)
    with pytest.raises(PHHMetabolicExecutionBundleError, match="SHA-256 mismatch"):
        load_phh_metabolic_execution_bundle(bundle_path)


def test_development_and_heldout_identifiers_must_be_disjoint(
    tmp_path: Path,
) -> None:
    bundle_path, payload, _ = _bundle_fixture(tmp_path)
    payload["splits"]["heldout_donor_ids"] = ["donor-dev"]  # type: ignore[index]
    _write_json(bundle_path, payload)
    with pytest.raises(PHHMetabolicExecutionBundleError, match="donors overlap"):
        load_phh_metabolic_execution_bundle(bundle_path)


def test_unmeasured_objective_is_rejected(tmp_path: Path) -> None:
    bundle_path, payload, artifacts = _bundle_fixture(tmp_path)
    objective_path = artifacts["objective_specification"]
    objective = json.loads(objective_path.read_text(encoding="utf-8"))
    objective["directly_measured_in_matched_phh_context"] = False
    _write_json(objective_path, objective)
    payload["artifacts"]["objective_specification"] = _reference(objective_path)  # type: ignore[index]
    _write_json(bundle_path, payload)
    with pytest.raises(
        PHHMetabolicExecutionBundleError,
        match="objective specification does not pass",
    ):
        load_phh_metabolic_execution_bundle(bundle_path)


def test_validation_record_must_use_independent_heldout_split(
    tmp_path: Path,
) -> None:
    bundle_path, payload, artifacts = _bundle_fixture(tmp_path)
    contract = load_phh_metabolic_execution_bundle_contract()
    validation_path = artifacts["independent_validation"]
    _write_csv(
        validation_path,
        contract["independent_validation_header"],
        [
            {
                "reaction_id": "EX_glc",
                "source_study_id": "study-heldout",
                "donor_or_cohort_id": "donor-heldout",
                "split_role": "internal_validation",
                "observed_value": "1.5",
                "observed_unit": "mmol/gDW/h",
                "predicted_value": "1.4",
                "predicted_unit": "mmol/gDW/h",
                "uncertainty_value": "0.2",
                "uncertainty_type": "source interval",
                "measurement_operator_id": "operator-heldout",
                "assay": "independent direct exchange assay",
                "manual_primary_source_review_status": "pass",
            }
        ],
    )
    payload["artifacts"]["independent_validation"] = _reference(validation_path)  # type: ignore[index]
    _write_json(bundle_path, payload)
    with pytest.raises(
        PHHMetabolicExecutionBundleError,
        match="not donor/study-disjoint heldout",
    ):
        load_phh_metabolic_execution_bundle(bundle_path)
