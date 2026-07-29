from __future__ import annotations

from copy import deepcopy

import pytest

from cell_engine.validation.scientific_snapshot_export_policy import (
    CACHE_SURFACE_IDS,
    scientific_snapshot_export_policy_snapshot,
    validate_scientific_snapshot_export_policy,
)


def test_snapshot_export_policy_is_engineering_only_and_fail_closed() -> None:
    policy = scientific_snapshot_export_policy_snapshot()
    surfaces = policy["cache_surfaces"]

    assert policy["scientific_authority"] is False
    assert policy["biological_parameter_activation"] is False
    assert tuple(item["id"] for item in surfaces) == CACHE_SURFACE_IDS
    assert policy["scientific_output_equivalence"]["required"] is True
    assert policy["scientific_output_equivalence"]["excluded_volatile_paths"] == [
        "metadata.created_at_utc"
    ]


def test_custom_scientific_inputs_must_bypass_default_caches() -> None:
    policy = scientific_snapshot_export_policy_snapshot()
    by_id = {item["id"]: item for item in policy["cache_surfaces"]}

    assert by_id["phh_proteome_gene_accession_indexes"][
        "custom_arguments_bypass_cache"
    ] is True
    assert by_id["kinetic_transfer_audit"]["custom_arguments_bypass_cache"] is True
    assert by_id["reaction_evidence_atlas"]["custom_arguments_bypass_cache"] is True


def test_policy_rejects_biological_authority_promotion() -> None:
    policy = deepcopy(scientific_snapshot_export_policy_snapshot())
    policy["biological_parameter_activation"] = True

    with pytest.raises(ValueError, match="cannot carry biological authority"):
        validate_scientific_snapshot_export_policy(policy)
