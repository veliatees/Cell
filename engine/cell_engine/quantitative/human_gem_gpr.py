"""Strict Boolean evaluation for SBML/FBC gene-product-reaction rules."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import AbstractSet, Literal

from cell_engine.quantitative.human_gem_fbc_loader import HumanGemFbcModel


VERSION = "human_gem_gpr_evaluator_v1"


class GeneRuleError(ValueError):
    """Raised when an FBC gene rule escapes the supported Boolean grammar."""


@dataclass(frozen=True)
class GeneReference:
    identifier: str


@dataclass(frozen=True)
class GeneBoolean:
    operator: Literal["and", "or"]
    children: tuple["GeneRuleNode", ...]


GeneRuleNode = GeneReference | GeneBoolean


def _convert_node(node: ast.AST) -> GeneRuleNode:
    if isinstance(node, ast.Name):
        if not node.id:
            raise GeneRuleError("gene-product identifier cannot be empty")
        return GeneReference(node.id)
    if isinstance(node, ast.BoolOp) and isinstance(node.op, (ast.And, ast.Or)):
        if len(node.values) < 2:
            raise GeneRuleError("Boolean gene rule requires at least two operands")
        return GeneBoolean(
            operator="and" if isinstance(node.op, ast.And) else "or",
            children=tuple(_convert_node(child) for child in node.values),
        )
    raise GeneRuleError(
        f"unsupported gene-rule syntax: {type(node).__name__}"
    )


def parse_gene_rule(rule: str) -> GeneRuleNode:
    """Parse only identifiers, parentheses and Boolean ``and``/``or``."""

    if not isinstance(rule, str) or not rule.strip():
        raise GeneRuleError("gene rule must be a nonempty string")
    try:
        expression = ast.parse(rule, mode="eval")
    except SyntaxError as exc:
        raise GeneRuleError("gene rule is not valid Boolean syntax") from exc
    return _convert_node(expression.body)


def referenced_gene_products(rule: GeneRuleNode) -> tuple[str, ...]:
    if isinstance(rule, GeneReference):
        return (rule.identifier,)
    return tuple(
        dict.fromkeys(
            identifier
            for child in rule.children
            for identifier in referenced_gene_products(child)
        )
    )


def evaluate_parsed_gene_rule(
    rule: GeneRuleNode,
    available_gene_product_ids: AbstractSet[str],
) -> bool:
    if isinstance(rule, GeneReference):
        return rule.identifier in available_gene_product_ids
    values = (
        evaluate_parsed_gene_rule(child, available_gene_product_ids)
        for child in rule.children
    )
    return all(values) if rule.operator == "and" else any(values)


def evaluate_gene_rule(
    rule: str,
    available_gene_product_ids: AbstractSet[str],
) -> bool:
    return evaluate_parsed_gene_rule(
        parse_gene_rule(rule),
        available_gene_product_ids,
    )


def gene_product_label_map(model: HumanGemFbcModel) -> dict[str, str]:
    """Return an exact label-to-FBC-ID map, rejecting ambiguous labels."""

    if len(model.gene_product_labels) != len(model.gene_product_ids):
        raise GeneRuleError("gene-product labels are incomplete")
    labels: dict[str, str] = {}
    for identifier, label in model.gene_product_labels:
        if identifier not in model.gene_product_ids:
            raise GeneRuleError(
                f"label references unknown gene product {identifier!r}"
            )
        previous = labels.get(label)
        if previous is not None and previous != identifier:
            raise GeneRuleError(f"ambiguous gene-product label {label!r}")
        labels[label] = identifier
    if len(labels) != len(model.gene_product_ids):
        raise GeneRuleError("gene-product labels are not one-to-one")
    return labels


def validate_model_gene_rules(model: HumanGemFbcModel) -> dict[str, int]:
    known = set(model.gene_product_ids)
    associated = 0
    references = 0
    for reaction in model.reactions:
        if reaction.gene_rule is None:
            if reaction.gene_product_ids:
                raise GeneRuleError(
                    f"reaction {reaction.identifier!r} has genes but no rule"
                )
            continue
        parsed = parse_gene_rule(reaction.gene_rule)
        observed = referenced_gene_products(parsed)
        if observed != reaction.gene_product_ids:
            raise GeneRuleError(
                f"reaction {reaction.identifier!r} gene-rule identity changed"
            )
        unknown = set(observed) - known
        if unknown:
            raise GeneRuleError(
                f"reaction {reaction.identifier!r} references unknown genes"
            )
        associated += 1
        references += len(observed)
    gene_product_label_map(model)
    return {
        "gene_rule_count": associated,
        "gene_reference_count": references,
        "gene_product_label_count": len(model.gene_product_labels),
    }
