from __future__ import annotations

from cell_engine.processes.cellular_memory import (
    MEMORY_SUBSTRATE_CONTRACTS,
    cellular_memory_contract_snapshot,
)


def test_memory_contract_separates_event_log_from_physical_memory() -> None:
    snapshot = cellular_memory_contract_snapshot()
    assert snapshot["event_log_is_memory"] is False
    assert snapshot["automatic_memory_consolidation"] is False
    assert snapshot["automatic_future_response_coupling"] is False
    assert snapshot["active_memory_trace_count"] == 0


def test_memory_contract_requires_persistence_and_rechallenge_evidence() -> None:
    assert len(MEMORY_SUBSTRATE_CONTRACTS) == 12
    assert all(item.required_persistence_tests for item in MEMORY_SUBSTRATE_CONTRACTS)
    assert all(item.future_response_readouts for item in MEMORY_SUBSTRATE_CONTRACTS)
    assert all(not item.quantitative_coupling_allowed for item in MEMORY_SUBSTRATE_CONTRACTS)
