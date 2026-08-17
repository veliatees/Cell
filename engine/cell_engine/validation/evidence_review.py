"""Hash-bound, two-person review gate for external evidence deliveries.

Structural CSV/JSON validation can show that a delivery is machine-readable; it
cannot show that a number appears in the cited primary source.  This module
keeps those claims separate.  A delivery receives scientific structural credit
only when an independent review record is bound to the exact delivery,
contract, and review-artifact hashes.

The gate does not authorize a parameter, fit, prediction, or cell-state
coupling.  It records a review decision that later authority gates may inspect.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Mapping


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "evidence_intake"
    / "phh_delivery_review_registry.v1.json"
)
REGISTRY_SCHEMA_VERSION = "cell.phh-delivery-review-registry.v1"
REGISTRY_ID = "phh_delivery_review_registry_v1"
VERSION = "phh_delivery_review_gate_v1"
EMPTY_FILE_SHA256 = hashlib.sha256(b"").hexdigest()

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DECISIONS = frozenset({"approved_for_structural_credit", "rejected"})
_REGISTRY_FIELDS = frozenset(
    {
        "schema_version",
        "registry_id",
        "scientific_authority",
        "automatic_parameter_activation",
        "automatic_state_coupling",
        "reviews",
        "policy",
    }
)
_POLICY = {
    "delivery_hash_bound": True,
    "contract_hash_bound": True,
    "review_artifact_hash_bound": True,
    "curator_reviewer_separation_required": True,
    "primary_source_row_review_required": True,
    "raw_artifact_review_required": True,
    "context_and_units_review_required": True,
    "heldout_independence_review_required": True,
    "automatic_parameter_activation": False,
    "automatic_state_coupling": False,
    "predictive_authority": False,
}
_REVIEW_FIELDS = frozenset(
    {
        "review_id",
        "entry_id",
        "delivery_sha256",
        "contract_sha256",
        "review_artifact_path",
        "review_artifact_sha256",
        "curator_id",
        "reviewer_id",
        "review_date",
        "decision",
        "primary_source_row_review_complete",
        "raw_artifact_hashes_verified",
        "context_and_units_review_complete",
        "heldout_independence_review_complete",
        "independent_reviewer_attested",
        "notes",
    }
)


@dataclass(frozen=True)
class EvidenceDeliveryReviewAssessment:
    version: str
    entry_id: str
    status: str
    delivery_sha256: str | None
    contract_sha256: str
    review_id: str | None
    review_artifact_path: str | None
    approved_for_structural_credit: bool
    quarantined: bool
    automatic_parameter_activation: bool
    automatic_state_coupling: bool
    predictive_authority: bool
    blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def delivery_sha256(path: Path) -> str:
    """Return a stable digest for one file or a directory delivery."""

    if path.is_symlink():
        raise ValueError("evidence delivery cannot be a symlink")
    if path.is_file():
        return _sha256_file(path)
    if not path.is_dir():
        raise ValueError(f"evidence delivery is absent: {path}")
    digest = hashlib.sha256(b"cell.evidence-directory.v1\0")
    files = sorted(item for item in path.rglob("*") if item.is_file())
    for item in files:
        if item.is_symlink():
            raise ValueError("evidence delivery directories cannot contain symlinks")
        relative = item.relative_to(path).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(bytes.fromhex(_sha256_file(item)))
    return digest.hexdigest()


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _digest(value: object, field: str) -> str:
    token = _required_text(value, field)
    if not _SHA256_RE.fullmatch(token):
        raise ValueError(f"{field} must be a lowercase SHA-256 digest")
    if token == EMPTY_FILE_SHA256:
        raise ValueError(f"{field} cannot identify an empty artifact")
    return token


def _review_artifact_path(value: object, repository_root: Path) -> Path:
    token = _required_text(value, "review_artifact_path")
    relative = Path(token)
    required_prefix = Path("data/evidence_intake/reviews")
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("review_artifact_path must stay inside the repository")
    try:
        relative.relative_to(required_prefix)
    except ValueError as exc:
        raise ValueError(
            "review_artifact_path must be under data/evidence_intake/reviews"
        ) from exc
    path = repository_root / relative
    review_root = (repository_root / required_prefix).resolve()
    if path.is_symlink():
        raise ValueError("review artifact cannot be a symlink")
    try:
        path.resolve().relative_to(review_root)
    except ValueError as exc:
        raise ValueError("review artifact resolved outside its review root") from exc
    if not path.is_file():
        raise ValueError(f"review artifact is absent: {token}")
    return path


def validate_evidence_delivery_review_registry(
    payload: object,
    *,
    repository_root: Path = REPOSITORY_ROOT,
) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError("evidence delivery review registry must be an object")
    if frozenset(payload) != _REGISTRY_FIELDS:
        raise ValueError("evidence delivery review registry fields changed")
    if (
        payload.get("schema_version") != REGISTRY_SCHEMA_VERSION
        or payload.get("registry_id") != REGISTRY_ID
    ):
        raise ValueError("unsupported evidence delivery review registry identity")
    if (
        payload.get("scientific_authority") is not False
        or payload.get("automatic_parameter_activation") is not False
        or payload.get("automatic_state_coupling") is not False
        or payload.get("policy") != _POLICY
    ):
        raise ValueError("evidence review registry escaped fail-closed policy")
    reviews = payload.get("reviews")
    if not isinstance(reviews, list):
        raise ValueError("evidence delivery review registry requires a reviews list")

    seen_review_ids: set[str] = set()
    seen_delivery_decisions: set[tuple[str, str]] = set()
    for raw in reviews:
        if not isinstance(raw, Mapping) or frozenset(raw) != _REVIEW_FIELDS:
            raise ValueError("evidence delivery review record fields changed")
        review_id = _required_text(raw["review_id"], "review_id")
        entry_id = _required_text(raw["entry_id"], "entry_id")
        delivery_digest = _digest(raw["delivery_sha256"], "delivery_sha256")
        _digest(raw["contract_sha256"], "contract_sha256")
        review_digest = _digest(
            raw["review_artifact_sha256"], "review_artifact_sha256"
        )
        review_path = _review_artifact_path(
            raw["review_artifact_path"], repository_root
        )
        if _sha256_file(review_path) != review_digest:
            raise ValueError(f"{review_id}: review artifact SHA-256 mismatch")
        curator_id = _required_text(raw["curator_id"], "curator_id")
        reviewer_id = _required_text(raw["reviewer_id"], "reviewer_id")
        review_date = _required_text(raw["review_date"], "review_date")
        if not _DATE_RE.fullmatch(review_date):
            raise ValueError(f"{review_id}: review_date must use YYYY-MM-DD")
        try:
            date.fromisoformat(review_date)
        except ValueError as exc:
            raise ValueError(f"{review_id}: review_date is not a real date") from exc
        decision = _required_text(raw["decision"], "decision")
        if decision not in _DECISIONS:
            raise ValueError(f"{review_id}: unsupported review decision")
        _required_text(raw["notes"], "notes")
        boolean_fields = (
            "primary_source_row_review_complete",
            "raw_artifact_hashes_verified",
            "context_and_units_review_complete",
            "heldout_independence_review_complete",
            "independent_reviewer_attested",
        )
        if any(not isinstance(raw[field], bool) for field in boolean_fields):
            raise ValueError(f"{review_id}: review attestations must be boolean")
        if decision == "approved_for_structural_credit" and (
            curator_id == reviewer_id
            or not all(bool(raw[field]) for field in boolean_fields)
        ):
            raise ValueError(
                f"{review_id}: approval requires independent curator/reviewer "
                "separation and complete attestations"
            )
        if review_id in seen_review_ids:
            raise ValueError(f"duplicate review_id: {review_id}")
        delivery_key = (entry_id, delivery_digest)
        if delivery_key in seen_delivery_decisions:
            raise ValueError(
                f"duplicate review decision for {entry_id}:{delivery_digest}"
            )
        seen_review_ids.add(review_id)
        seen_delivery_decisions.add(delivery_key)


def load_evidence_delivery_review_registry(
    path: Path = REGISTRY_PATH,
    *,
    repository_root: Path = REPOSITORY_ROOT,
) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("evidence delivery review registry must be an object")
    validate_evidence_delivery_review_registry(
        payload, repository_root=repository_root
    )
    return payload


def assess_evidence_delivery_review(
    entry_id: str,
    delivery_path: Path,
    contract_sha256: str,
    *,
    registry_path: Path = REGISTRY_PATH,
    repository_root: Path = REPOSITORY_ROOT,
) -> EvidenceDeliveryReviewAssessment:
    if not _SHA256_RE.fullmatch(contract_sha256):
        raise ValueError("contract_sha256 must be a lowercase SHA-256 digest")
    if not delivery_path.exists():
        return EvidenceDeliveryReviewAssessment(
            version=VERSION,
            entry_id=entry_id,
            status="not_delivered",
            delivery_sha256=None,
            contract_sha256=contract_sha256,
            review_id=None,
            review_artifact_path=None,
            approved_for_structural_credit=False,
            quarantined=False,
            automatic_parameter_activation=False,
            automatic_state_coupling=False,
            predictive_authority=False,
            blockers=("evidence delivery is absent",),
        )

    artifact_digest = delivery_sha256(delivery_path)
    registry = load_evidence_delivery_review_registry(
        registry_path, repository_root=repository_root
    )
    reviews = registry["reviews"]
    if not isinstance(reviews, list):
        raise ValueError("validated evidence review registry lost its reviews list")
    exact = [
        item
        for item in reviews
        if isinstance(item, Mapping)
        and item.get("entry_id") == entry_id
        and item.get("delivery_sha256") == artifact_digest
    ]
    prior = [
        item
        for item in reviews
        if isinstance(item, Mapping) and item.get("entry_id") == entry_id
    ]
    if not exact:
        changed = bool(prior)
        return EvidenceDeliveryReviewAssessment(
            version=VERSION,
            entry_id=entry_id,
            status=(
                "delivery_changed_since_review"
                if changed
                else "manual_primary_source_review_required"
            ),
            delivery_sha256=artifact_digest,
            contract_sha256=contract_sha256,
            review_id=None,
            review_artifact_path=None,
            approved_for_structural_credit=False,
            quarantined=changed,
            automatic_parameter_activation=False,
            automatic_state_coupling=False,
            predictive_authority=False,
            blockers=(
                "delivery hash does not match its prior review decision"
                if changed
                else "no independent hash-bound primary-source review exists",
            ),
        )

    review = exact[0]
    if review.get("contract_sha256") != contract_sha256:
        return EvidenceDeliveryReviewAssessment(
            version=VERSION,
            entry_id=entry_id,
            status="contract_changed_since_review",
            delivery_sha256=artifact_digest,
            contract_sha256=contract_sha256,
            review_id=str(review["review_id"]),
            review_artifact_path=str(review["review_artifact_path"]),
            approved_for_structural_credit=False,
            quarantined=True,
            automatic_parameter_activation=False,
            automatic_state_coupling=False,
            predictive_authority=False,
            blockers=("contract hash no longer matches the review decision",),
        )
    approved = review.get("decision") == "approved_for_structural_credit"
    return EvidenceDeliveryReviewAssessment(
        version=VERSION,
        entry_id=entry_id,
        status=("independently_reviewed" if approved else "review_rejected"),
        delivery_sha256=artifact_digest,
        contract_sha256=contract_sha256,
        review_id=str(review["review_id"]),
        review_artifact_path=str(review["review_artifact_path"]),
        approved_for_structural_credit=approved,
        quarantined=not approved,
        automatic_parameter_activation=False,
        automatic_state_coupling=False,
        predictive_authority=False,
        blockers=(
            ()
            if approved
            else ("independent primary-source review rejected this delivery",)
        ),
    )


__all__ = [
    "EMPTY_FILE_SHA256",
    "EvidenceDeliveryReviewAssessment",
    "REGISTRY_PATH",
    "VERSION",
    "assess_evidence_delivery_review",
    "delivery_sha256",
    "load_evidence_delivery_review_registry",
    "validate_evidence_delivery_review_registry",
]
