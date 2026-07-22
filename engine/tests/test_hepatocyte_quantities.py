from __future__ import annotations

from cell_engine.validation.hepatocyte_quantities import (
    hepatocyte_quantity_harvest_snapshot,
    parse_strict_numeric_value,
    validate_quantity_harvest,
)


def test_quantity_harvest_is_lossless_partitioned_and_fail_closed() -> None:
    audit = validate_quantity_harvest()
    assert audit.total_records == 168
    assert audit.organism_bucket_counts == {
        "HepaRG": 1,
        "human": 74,
        "mouse": 8,
        "other": 36,
        "rat": 49,
    }
    assert audit.reported_value_records == 144
    assert audit.strict_numeric_value_records == 115
    assert audit.exact_duplicate_records == 0
    assert audit.automatic_parameter_activation is False
    assert audit.authoritative_runtime_coupling is False
    assert audit.healthy_phh_runtime_parameter_count == 0


def test_quantity_harvest_keeps_missingness_and_free_text_visible() -> None:
    audit = validate_quantity_harvest()
    assert audit.reported_error_records == 65
    assert audit.reported_sample_size_records == 59
    assert audit.unique_primary_source_pmids == 91
    assert audit.distinct_free_text_usability_labels == 73


def test_known_macaque_human_bucket_error_is_quarantined() -> None:
    audit = validate_quantity_harvest()
    assert audit.bucket_inconsistency_rows == (167,)
    snapshot = hepatocyte_quantity_harvest_snapshot()
    assert snapshot["integration_gates"]["healthy_phh_initialization_ready"] is False


def test_strict_parser_never_extracts_numbers_from_prose() -> None:
    exact = parse_strict_numeric_value("1.3e7")
    assert exact is not None
    assert (exact.low, exact.high, exact.qualifier) == (13_000_000.0, 13_000_000.0, "exact")
    ranged = parse_strict_numeric_value("25-50")
    assert ranged is not None
    assert (ranged.low, ranged.high, ranged.qualifier) == (25.0, 50.0, "range")
    assert parse_strict_numeric_value("29 (24h); 68 (48h)") is None
    assert parse_strict_numeric_value("significant necrosis first at 24 h") is None
    assert parse_strict_numeric_value("NOT_REPORTED") is None


def test_only_reviewed_context_bound_claims_are_promoted() -> None:
    audit = validate_quantity_harvest()
    assert audit.source_review_count == 7
    assert audit.reviewed_raw_record_count == 25
    assert audit.promoted_context_bound_claim_count == 16
    snapshot = hepatocyte_quantity_harvest_snapshot()
    assert snapshot["integration_gates"]["same_assay_kinetic_evidence_ready"] is True
    assert snapshot["integration_gates"]["matching_protocol_injury_observations_ready"] is True
    assert snapshot["integration_gates"]["whole_cell_rate_coupling_ready"] is False
