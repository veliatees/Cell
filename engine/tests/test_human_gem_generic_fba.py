from __future__ import annotations

from copy import deepcopy

import pytest

from cell_engine.quantitative.human_gem_fbc_loader import (
    FluxObjectiveRecord,
    HumanGemFbcModel,
    ObjectiveRecord,
    ReactionRecord,
    SparseStoichiometricMatrix,
    SpeciesRecord,
)
from cell_engine.quantitative.human_gem_generic_fba import (
    HumanGemGenericFbaError,
    load_committed_human_gem_generic_fba_audit,
    solve_native_generic_objective,
    validate_human_gem_generic_fba_audit,
)


def _synthetic_model(*, active_objective_id: str | None = "obj") -> HumanGemFbcModel:
    return HumanGemFbcModel(
        model_id="synthetic",
        model_name="analytic linear chain",
        sbml_level=3,
        sbml_version=1,
        fbc_strict=True,
        compartment_ids=("c",),
        species=(
            SpeciesRecord(
                identifier="A_c",
                name="A",
                compartment_id="c",
                boundary_condition=False,
            ),
        ),
        reactions=(
            ReactionRecord(
                identifier="A_in",
                name="A input",
                reversible=False,
                lower_bound_parameter_id="zero",
                upper_bound_parameter_id="ten",
                lower_bound=0.0,
                upper_bound=10.0,
                gene_product_ids=(),
                gene_rule=None,
            ),
            ReactionRecord(
                identifier="A_out",
                name="A output",
                reversible=False,
                lower_bound_parameter_id="zero",
                upper_bound_parameter_id="ten",
                lower_bound=0.0,
                upper_bound=10.0,
                gene_product_ids=(),
                gene_rule=None,
            ),
        ),
        gene_product_ids=(),
        objectives=(
            ObjectiveRecord(
                identifier="obj",
                objective_type="maximize",
                flux_objectives=(
                    FluxObjectiveRecord(
                        reaction_id="A_out",
                        coefficient=1.0,
                    ),
                ),
            ),
        ),
        active_objective_id=active_objective_id,
        stoichiometry=SparseStoichiometricMatrix(
            shape=(1, 2),
            row_indices=(0, 0),
            column_indices=(0, 1),
            values=(1.0, -1.0),
        ),
        parameter_values=(("zero", 0.0), ("ten", 10.0)),
    )


def test_sparse_native_objective_solver_matches_analytic_chain() -> None:
    result = solve_native_generic_objective(_synthetic_model())

    assert result.objective_value == pytest.approx(10.0)
    assert result.fluxes == pytest.approx((10.0, 10.0))
    assert result.active_reaction_count == 2
    assert result.maximum_mass_balance_residual <= 1e-10
    assert result.maximum_bound_violation <= 1e-10
    assert result.optimum_uniqueness_established is False
    assert result.biological_flux_authority is False


def test_sparse_native_objective_solver_rejects_missing_objective() -> None:
    with pytest.raises(HumanGemGenericFbaError, match="no active"):
        solve_native_generic_objective(
            _synthetic_model(active_objective_id=None)
        )


def test_committed_generic_human_gem_fba_audit_is_fail_closed() -> None:
    report = load_committed_human_gem_generic_fba_audit()

    assert report["native_fbc_objective"]["terms"][0]["reaction_id"] == "MAR13082"
    assert report["generic_solve"]["status"] == "optimal"
    assert report["generic_solve"]["objective_value"] > 0
    assert report["scientific_boundary"]["generic_native_objective_optimized"] is True
    assert report["scientific_boundary"]["healthy_phh_context_extracted"] is False
    assert report["scientific_boundary"]["biological_flux_authority"] is False

    escaped = deepcopy(report)
    escaped["scientific_boundary"]["biological_flux_authority"] = True
    with pytest.raises(HumanGemGenericFbaError, match="healthy-PHH"):
        validate_human_gem_generic_fba_audit(escaped)
