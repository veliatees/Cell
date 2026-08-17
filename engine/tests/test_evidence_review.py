from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from cell_engine.validation.evidence_review import (
    EMPTY_FILE_SHA256,
    assess_evidence_delivery_review,
    delivery_sha256,
    load_evidence_delivery_review_registry,
    validate_evidence_delivery_review_registry,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _review_record(
    delivery: Path,
    artifact: Path,
    contract_sha256: str,
    **updates: object,
) -> dict[str, object]:
    record: dict[str, object] = {
        "review_id": "software-review-1",
        "entry_id": "reaction_evidence",
        "delivery_sha256": _sha256(delivery),
        "contract_sha256": contract_sha256,
        "review_artifact_path": "data/evidence_intake/reviews/software-review.json",
        "review_artifact_sha256": _sha256(artifact),
        "curator_id": "software-curator",
        "reviewer_id": "software-independent-reviewer",
        "review_date": "2026-08-17",
        "decision": "approved_for_structural_credit",
        "primary_source_row_review_complete": True,
        "raw_artifact_hashes_verified": True,
        "context_and_units_review_complete": True,
        "heldout_independence_review_complete": True,
        "independent_reviewer_attested": True,
        "notes": "Software fixture only.",
    }
    record.update(updates)
    return record


def _registry(review: dict[str, object] | None = None) -> dict[str, object]:
    payload = deepcopy(load_evidence_delivery_review_registry())
    payload["reviews"] = [] if review is None else [review]
    return payload


def _write_registry(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_delivery_without_independent_review_receives_no_structural_credit(
    tmp_path: Path,
) -> None:
    delivery = tmp_path / "delivery.csv"
    delivery.write_text("record_id,value\nsoftware,1\n", encoding="utf-8")
    registry_path = tmp_path / "review-registry.json"
    _write_registry(registry_path, _registry())

    assessment = assess_evidence_delivery_review(
        "reaction_evidence",
        delivery,
        "a" * 64,
        registry_path=registry_path,
    )

    assert assessment.status == "manual_primary_source_review_required"
    assert assessment.approved_for_structural_credit is False
    assert assessment.quarantined is False
    assert assessment.automatic_parameter_activation is False


def test_exact_hash_bound_independent_review_can_grant_structural_credit(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repository"
    review_dir = root / "data/evidence_intake/reviews"
    review_dir.mkdir(parents=True)
    artifact = review_dir / "software-review.json"
    artifact.write_text('{"review":"software fixture"}\n', encoding="utf-8")
    delivery = tmp_path / "delivery.csv"
    delivery.write_text("record_id,value\nsoftware,1\n", encoding="utf-8")
    contract_digest = "b" * 64
    registry_path = tmp_path / "review-registry.json"
    _write_registry(
        registry_path,
        _registry(_review_record(delivery, artifact, contract_digest)),
    )

    assessment = assess_evidence_delivery_review(
        "reaction_evidence",
        delivery,
        contract_digest,
        registry_path=registry_path,
        repository_root=root,
    )

    assert assessment.status == "independently_reviewed"
    assert assessment.approved_for_structural_credit is True
    assert assessment.quarantined is False
    assert assessment.predictive_authority is False


def test_delivery_change_after_review_is_quarantined(tmp_path: Path) -> None:
    root = tmp_path / "repository"
    review_dir = root / "data/evidence_intake/reviews"
    review_dir.mkdir(parents=True)
    artifact = review_dir / "software-review.json"
    artifact.write_text('{"review":"software fixture"}\n', encoding="utf-8")
    delivery = tmp_path / "delivery.csv"
    delivery.write_text("record_id,value\nsoftware,1\n", encoding="utf-8")
    contract_digest = "c" * 64
    review = _review_record(delivery, artifact, contract_digest)
    registry_path = tmp_path / "review-registry.json"
    _write_registry(registry_path, _registry(review))
    delivery.write_text("record_id,value\nsoftware,2\n", encoding="utf-8")

    assessment = assess_evidence_delivery_review(
        "reaction_evidence",
        delivery,
        contract_digest,
        registry_path=registry_path,
        repository_root=root,
    )

    assert assessment.status == "delivery_changed_since_review"
    assert assessment.quarantined is True
    assert assessment.approved_for_structural_credit is False


def test_registry_rejects_self_review_and_empty_artifact_digests(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repository"
    review_dir = root / "data/evidence_intake/reviews"
    review_dir.mkdir(parents=True)
    artifact = review_dir / "software-review.json"
    artifact.write_text('{"review":"software fixture"}\n', encoding="utf-8")
    delivery = tmp_path / "delivery.csv"
    delivery.write_text("record_id,value\nsoftware,1\n", encoding="utf-8")
    record = _review_record(delivery, artifact, "d" * 64)
    record["reviewer_id"] = record["curator_id"]
    with pytest.raises(ValueError, match="curator/reviewer"):
        validate_evidence_delivery_review_registry(
            _registry(record), repository_root=root
        )

    record = _review_record(delivery, artifact, "d" * 64)
    record["delivery_sha256"] = EMPTY_FILE_SHA256
    with pytest.raises(ValueError, match="empty artifact"):
        validate_evidence_delivery_review_registry(
            _registry(record), repository_root=root
        )


def test_delivery_and_review_artifact_symlinks_are_rejected(tmp_path: Path) -> None:
    target = tmp_path / "delivery-target.csv"
    target.write_text("record_id,value\nsoftware,1\n", encoding="utf-8")
    delivery_link = tmp_path / "delivery.csv"
    delivery_link.symlink_to(target)
    with pytest.raises(ValueError, match="symlink"):
        delivery_sha256(delivery_link)

    root = tmp_path / "repository"
    review_dir = root / "data/evidence_intake/reviews"
    review_dir.mkdir(parents=True)
    outside = tmp_path / "outside-review.json"
    outside.write_text('{"review":"software fixture"}\n', encoding="utf-8")
    review_link = review_dir / "software-review.json"
    review_link.symlink_to(outside)
    record = _review_record(target, outside, "e" * 64)
    with pytest.raises(ValueError, match="symlink"):
        validate_evidence_delivery_review_registry(
            _registry(record), repository_root=root
        )
