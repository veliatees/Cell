from __future__ import annotations

import pytest

from cell_engine.quantitative.human_gem_gpr import (
    GeneRuleError,
    evaluate_gene_rule,
    parse_gene_rule,
    referenced_gene_products,
)


def test_gpr_evaluator_preserves_and_or_semantics() -> None:
    parsed = parse_gene_rule("(g1 and (g2 or g3))")

    assert referenced_gene_products(parsed) == ("g1", "g2", "g3")
    assert evaluate_gene_rule("(g1 and (g2 or g3))", {"g1", "g2"}) is True
    assert evaluate_gene_rule("(g1 and (g2 or g3))", {"g1", "g3"}) is True
    assert evaluate_gene_rule("(g1 and (g2 or g3))", {"g2", "g3"}) is False


@pytest.mark.parametrize(
    "rule",
    (
        "not g1",
        "g1 == g2",
        "g1()",
        "True",
        "g1 + g2",
        "__import__('os')",
    ),
)
def test_gpr_evaluator_rejects_non_boolean_syntax(rule: str) -> None:
    with pytest.raises(GeneRuleError, match="unsupported"):
        parse_gene_rule(rule)
