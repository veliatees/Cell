"""Evidence-gated per-instance organelle state scaffold.

Individual organelles can differ in function and can enter selective quality-
control pathways. That biological structure is worth representing, but the
repository has no matched, longitudinal healthy-adult PHH measurements that
identify an individual organelle's vitality, age, recovery constant, stress
sensitivity, clearance threshold, or turnover time.

This module therefore records stable per-body identities and typed future data
slots while leaving every unsupported quantitative field ``None``. It grants no
runtime, reaction, transport, geometry, or clearance authority. Cross-system
primary studies support the existence of heterogeneity and selective turnover;
they do not parameterize a healthy human hepatocyte.
"""

from __future__ import annotations

from dataclasses import dataclass

from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain
from cell_engine.quantitative.organelle_placement import (
    PLACEMENT_SOURCES,
    build_organelle_placement,
)

DATE_VERIFIED = "2026-08-01"
VERSION = "organelle_instance_vitality_v2"


VITALITY_SOURCES: dict[str, SourceReference] = dict(PLACEMENT_SOURCES)
VITALITY_SOURCES.update(
    {
        "collins2002_mitochondrial_heterogeneity": SourceReference(
            id="collins2002_mitochondrial_heterogeneity",
            title="Mitochondria are morphologically and functionally heterogeneous within cells",
            url="https://pmc.ncbi.nlm.nih.gov/articles/PMC125942/",
            source_type="primary_paper",
            date_verified=DATE_VERIFIED,
            notes=(
                "Includes live imaging of individual mitochondria in primary rat "
                "hepatocytes. Supports within-cell mitochondrial heterogeneity, "
                "not healthy-adult PHH vitality values or turnover kinetics."
            ),
        ),
        "mcwilliams2016_mito_qc": SourceReference(
            id="mcwilliams2016_mito_qc",
            title="mito-QC illuminates mitophagy and mitochondrial architecture in vivo",
            url="https://pubmed.ncbi.nlm.nih.gov/27458135/",
            source_type="primary_paper",
            date_verified=DATE_VERIFIED,
            notes=(
                "Mouse reporter study supporting organelle-selective mitophagy in "
                "vivo. It does not provide a healthy-human hepatocyte per-organelle "
                "clearance threshold or recovery law."
            ),
        ),
        "dutta2021_liver_pexophagy": SourceReference(
            id="dutta2021_liver_pexophagy",
            title=(
                "Catalase deficiency induces reactive oxygen species mediated "
                "pexophagy and cell death in the liver during prolonged fasting"
            ),
            url="https://pubmed.ncbi.nlm.nih.gov/33496364/",
            source_type="primary_paper",
            date_verified=DATE_VERIFIED,
            notes=(
                "Catalase-knockout mouse liver under prolonged fasting. Supports "
                "stress-responsive pexophagy as a pathway, not baseline PHH rates."
            ),
        ),
    }
)


@dataclass(frozen=True)
class OrganelleVitalityModel:
    """Typed slots for a future context-matched per-organelle model."""

    organelle_id: str
    baseline_vitality: float | None
    initial_vitality_spread: float | None
    mean_turnover_age_h: float | None
    recovery_time_constant_h: float | None
    stress_sensitivity: float | None
    clearance_vitality_threshold: float | None
    turns_over: bool | None
    quantitative_runtime_enabled: bool


_MODEL_IDS = (
    "mitochondria",
    "nucleus",
    "lysosomes",
    "peroxisomes",
    "rough_er",
    "smooth_er",
    "golgi",
    "ribosomes",
    "centrosome",
)
_MODELS: tuple[OrganelleVitalityModel, ...] = tuple(
    OrganelleVitalityModel(
        organelle_id=organelle_id,
        baseline_vitality=None,
        initial_vitality_spread=None,
        mean_turnover_age_h=None,
        recovery_time_constant_h=None,
        stress_sensitivity=None,
        clearance_vitality_threshold=None,
        turns_over=None,
        quantitative_runtime_enabled=False,
    )
    for organelle_id in _MODEL_IDS
)

# These are the organelle types represented by discrete solid bodies in the
# placement contract. Network organelles retain model slots but no fake bodies.
_DISCRETE_BODY_TYPES = frozenset(
    ("nucleus", "mitochondria", "lysosomes", "peroxisomes")
)


@dataclass(frozen=True)
class OrganelleInstanceVitality:
    """Stable organelle identity with deliberately unresolved measurements."""

    organelle_id: str
    index: int
    vitality: float | None
    health: float | None
    age_h: float | None
    decline_susceptibility: float | None


@dataclass(frozen=True)
class OrganelleInstanceVitalityField:
    version: str
    is_reaction_transport_authority: bool
    quantitative_runtime_enabled: bool
    runtime_geometry_coupling_enabled: bool
    models: tuple[OrganelleVitalityModel, ...]
    instances: tuple[OrganelleInstanceVitality, ...]
    instance_count_by_organelle: dict[str, int]
    quantitative_model_parameter_count: int
    quantified_instance_count: int
    honesty_status: str
    grounded: tuple[str, ...]
    not_grounded: tuple[str, ...]
    blockers: tuple[str, ...]
    source_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def build_organelle_instance_vitality(
    *, seed: int = 0
) -> OrganelleInstanceVitalityField:
    """Return identity-complete, quantitatively empty per-organelle slots.

    ``seed`` remains API-compatible with the placement exporter. It cannot
    manufacture biological values and therefore has no effect on this contract.
    """

    _ = seed
    placement = build_organelle_placement(seed=0)
    instances: list[OrganelleInstanceVitality] = []
    counts: dict[str, int] = {}
    for body in placement.bodies:
        if body.organelle_id not in _DISCRETE_BODY_TYPES:
            continue
        instances.append(
            OrganelleInstanceVitality(
                organelle_id=body.organelle_id,
                index=body.index,
                vitality=None,
                health=None,
                age_h=None,
                decline_susceptibility=None,
            )
        )
        counts[body.organelle_id] = counts.get(body.organelle_id, 0) + 1

    return OrganelleInstanceVitalityField(
        version=VERSION,
        is_reaction_transport_authority=False,
        quantitative_runtime_enabled=False,
        runtime_geometry_coupling_enabled=False,
        models=_MODELS,
        instances=tuple(instances),
        instance_count_by_organelle=counts,
        quantitative_model_parameter_count=0,
        quantified_instance_count=0,
        honesty_status="identity_scaffold_only_all_quantitative_fields_null",
        grounded=(
            "discrete organelle identities and counts from organelle_placement",
            "within-cell mitochondrial functional heterogeneity exists in primary rat hepatocytes",
            "mitophagy and pexophagy exist in mammalian in-vivo liver contexts",
        ),
        not_grounded=(
            "healthy-adult PHH per-organelle vitality and health",
            "healthy-adult PHH organelle age and turnover-time distributions",
            "healthy-adult PHH recovery constants and stress sensitivities",
            "healthy-adult PHH clearance thresholds and size-response laws",
        ),
        blockers=(
            "no matched longitudinal healthy-adult PHH single-organelle trajectories",
            "no donor-resolved calibration and donor/study-disjoint validation",
            "cross-species pathway evidence cannot authorize PHH numerical values",
        ),
        source_ids=tuple(VITALITY_SOURCES),
    )


def organelle_instance_vitality_snapshot(*, seed: int = 0) -> dict[str, object]:
    return build_organelle_instance_vitality(seed=seed).to_dict()
