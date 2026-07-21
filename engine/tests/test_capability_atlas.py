from __future__ import annotations

from cell_engine.validation.capability_atlas import (
    HEPATOCYTE_CAPABILITIES,
    hepatocyte_capability_atlas_snapshot,
    validate_hepatocyte_capability_atlas,
)


def test_capability_atlas_declares_broad_scope_without_activating_templates() -> None:
    validate_hepatocyte_capability_atlas()
    snapshot = hepatocyte_capability_atlas_snapshot()
    summary = snapshot["summary"]
    assert summary["declared_domain_count"] == 12
    assert summary["feature_template_count"] == 38
    assert summary["parameter_slot_count"] == 44
    assert summary["filled_parameter_slot_count"] == 0
    assert summary["quantitatively_activated_template_count"] == 0
    assert summary["biological_accuracy_pct"] is None


def test_every_capability_has_null_parameters_and_validation_observables() -> None:
    assert all(feature.template_status == "template_non_executable" for feature in HEPATOCYTE_CAPABILITIES)
    assert all(not feature.quantitative_activation_allowed for feature in HEPATOCYTE_CAPABILITIES)
    assert all(feature.validation_observables for feature in HEPATOCYTE_CAPABILITIES)
    assert all(
        slot.value is None
        for feature in HEPATOCYTE_CAPABILITIES
        for slot in feature.parameter_slots
    )


def test_declared_scope_includes_fluid_history_and_future_interaction() -> None:
    ids = {feature.id for feature in HEPATOCYTE_CAPABILITIES}
    assert {
        "cytosol_transport_and_rheology",
        "cellular_history_and_memory",
        "host_pathogen_interaction",
        "cell_contact_and_junctions",
        "genome_architecture",
    }.issubset(ids)
