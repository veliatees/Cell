from __future__ import annotations

import pytest

from cell_engine.quantitative.constraint_numerics import (
    ConstraintNumericsError,
    StoichiometricProblem,
    constraint_numerics_snapshot,
    diagnose_infeasibility,
    solve_fba,
    solve_fva,
    validate_constraint_numerics_snapshot,
    validate_stoichiometric_problem,
)


def _linear_chain() -> StoichiometricProblem:
    return StoichiometricProblem(
        metabolite_ids=("A", "B"),
        reaction_ids=("uptake", "convert", "export"),
        stoichiometry=((1.0, -1.0, 0.0), (0.0, 1.0, -1.0)),
        lower_bounds=(0.0, 0.0, 0.0),
        upper_bounds=(10.0, 10.0, 100.0),
        objective_coefficients=(0.0, 0.0, 1.0),
        right_hand_side=(0.0, 0.0),
    )


def test_fba_solves_mass_balanced_linear_chain() -> None:
    result = solve_fba(_linear_chain())
    assert result.success is True
    assert result.status == "optimal"
    assert result.objective_value == pytest.approx(10.0)
    assert result.fluxes == pytest.approx((10.0, 10.0, 10.0))
    assert result.max_mass_balance_residual is not None
    assert result.max_mass_balance_residual <= 1e-9
    assert result.max_bound_violation == pytest.approx(0.0)


def test_fva_detects_alternate_optimal_routes() -> None:
    problem = StoichiometricProblem(
        metabolite_ids=("A", "B"),
        reaction_ids=("uptake", "route_1", "route_2", "export"),
        stoichiometry=((1.0, -1.0, -1.0, 0.0), (0.0, 1.0, 1.0, -1.0)),
        lower_bounds=(0.0, 0.0, 0.0, 0.0),
        upper_bounds=(10.0, 10.0, 10.0, 10.0),
        objective_coefficients=(0.0, 0.0, 0.0, 1.0),
        right_hand_side=(0.0, 0.0),
    )
    result = solve_fva(problem)
    by_id = {item.reaction_id: item for item in result.ranges}
    assert result.optimum_objective == pytest.approx(10.0)
    assert result.alternate_optimum_reaction_count == 2
    assert by_id["route_1"].minimum == pytest.approx(0.0, abs=2e-8)
    assert by_id["route_1"].maximum == pytest.approx(10.0)
    assert by_id["route_2"].minimum == pytest.approx(0.0, abs=2e-8)
    assert by_id["route_2"].maximum == pytest.approx(10.0)


def test_infeasibility_is_reported_and_elastic_slack_is_localized() -> None:
    problem = StoichiometricProblem(
        metabolite_ids=("A",),
        reaction_ids=("fixed_zero",),
        stoichiometry=((1.0,),),
        lower_bounds=(0.0,),
        upper_bounds=(0.0,),
        objective_coefficients=(1.0,),
        right_hand_side=(1.0,),
    )
    result = solve_fba(problem)
    diagnosis = diagnose_infeasibility(problem)
    assert result.status == "infeasible"
    assert result.fluxes is None
    assert diagnosis.original_status == "infeasible"
    assert diagnosis.minimum_total_mass_balance_slack == pytest.approx(1.0)
    assert diagnosis.metabolite_slacks[0][0] == "A"
    assert diagnosis.metabolite_slacks[0][1] == pytest.approx(1.0)


@pytest.mark.parametrize(
    "problem",
    (
        StoichiometricProblem(
            metabolite_ids=("A",),
            reaction_ids=("r", "r"),
            stoichiometry=((1.0, -1.0),),
            lower_bounds=(0.0, 0.0),
            upper_bounds=(1.0, 1.0),
            objective_coefficients=(1.0, 0.0),
            right_hand_side=(0.0,),
        ),
        StoichiometricProblem(
            metabolite_ids=("A",),
            reaction_ids=("r",),
            stoichiometry=((1.0, 2.0),),
            lower_bounds=(0.0,),
            upper_bounds=(1.0,),
            objective_coefficients=(1.0,),
            right_hand_side=(0.0,),
        ),
        StoichiometricProblem(
            metabolite_ids=("A",),
            reaction_ids=("r",),
            stoichiometry=((1.0,),),
            lower_bounds=(2.0,),
            upper_bounds=(1.0,),
            objective_coefficients=(1.0,),
            right_hand_side=(0.0,),
        ),
    ),
)
def test_problem_validation_rejects_malformed_models(
    problem: StoichiometricProblem,
) -> None:
    with pytest.raises(ConstraintNumericsError):
        validate_stoichiometric_problem(problem)


def test_fva_rejects_invalid_objective_fraction() -> None:
    with pytest.raises(ConstraintNumericsError, match="fraction_of_optimum"):
        solve_fva(_linear_chain(), fraction_of_optimum=0)


def test_snapshot_runs_all_analytic_fixtures_without_biological_authority() -> None:
    snapshot = constraint_numerics_snapshot()
    validate_constraint_numerics_snapshot(snapshot)
    assert snapshot["analytic_fixture_pass_count"] == 5
    assert snapshot["alternate_optimum_audit_count"] == 1
    assert snapshot["elastic_infeasibility_diagnosis_count"] == 1
    assert snapshot["biological_flux_authority"] is False
