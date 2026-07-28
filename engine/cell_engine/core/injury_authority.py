"""Scientific authority guard for legacy injury and fate runtimes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from cell_engine.core.serialization import to_plain


VERSION = "injury_runtime_authority_v1"

InjuryRuntimePurpose = Literal[
    "exploratory_execution",
    "quantitative_validation",
    "predictive_execution",
    "authoritative_cell_state_coupling",
]


@dataclass(frozen=True)
class LegacyInjurySurface:
    id: str
    code_surfaces: tuple[str, ...]
    current_role: str
    numerical_parameter_authority: str
    phh_context_match: bool
    quantitative_validation_allowed: bool
    predictive_execution_allowed: bool
    authoritative_cell_state_coupling_allowed: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class InjuryRuntimeAuthority:
    version: str
    status: str
    surfaces: tuple[LegacyInjurySurface, ...]
    explicit_purpose_required: bool
    exploratory_execution_allowed: bool
    quantitative_validation_allowed: bool
    predictive_execution_allowed: bool
    authoritative_cell_state_coupling_allowed: bool
    policy: str

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


class InjuryRuntimeAuthorityError(RuntimeError):
    """Raised when a legacy injury runtime is requested for an unsupported use."""


_LEGACY_SURFACES = (
    LegacyInjurySurface(
        id="legacy_apoptosis_necrosis_switch",
        code_surfaces=(
            "engine/cell_engine/stochastic/apoptosis.py:death_drive",
            "engine/cell_engine/stochastic/apoptosis.py:step_death",
            "engine/cell_engine/stochastic/apoptosis.py:run_death",
        ),
        current_role="exploratory_qualitative_fate_fixture",
        numerical_parameter_authority="unresolved_legacy_defaults",
        phh_context_match=False,
        quantitative_validation_allowed=False,
        predictive_execution_allowed=False,
        authoritative_cell_state_coupling_allowed=False,
        blockers=(
            "Default stress weights, tolerance, decay and commitment thresholds are not calibrated to a matched PHH protocol.",
            "The ATP-dependent apoptosis-versus-necrosis literature supports mechanism direction, not the executable threshold values.",
            "No donor-disjoint PHH fate trajectory validates the executable decision law.",
        ),
    ),
    LegacyInjurySurface(
        id="legacy_detox_to_fate_projection",
        code_surfaces=(
            "engine/cell_engine/stochastic/apoptosis.py:signals_from_detox",
            "engine/cell_engine/stochastic/detox.py",
        ),
        current_role="exploratory_cross_module_adapter",
        numerical_parameter_authority="unresolved_legacy_scaling",
        phh_context_match=False,
        quantitative_validation_allowed=False,
        predictive_execution_allowed=False,
        authoritative_cell_state_coupling_allowed=False,
        blockers=(
            "ROS and adduct saturation scales are not measurements in the APAP PHH protocol.",
            "The adapter does not preserve measured concentration, compartment or assay units.",
            "No matched measurement operator maps its internal counts to PHH GSH, membrane-potential or necrosis endpoints.",
        ),
    ),
    LegacyInjurySurface(
        id="legacy_tissue_injury_population",
        code_surfaces=(
            "engine/cell_engine/stochastic/tissue_injury.py:expose_tissue_to_toxin",
        ),
        current_role="exploratory_population_fixture",
        numerical_parameter_authority="unresolved_legacy_defaults",
        phh_context_match=False,
        quantitative_validation_allowed=False,
        predictive_execution_allowed=False,
        authoritative_cell_state_coupling_allowed=False,
        blockers=(
            "Per-cell dose, GSH heterogeneity, exposure duration and clearance settings are not expressed in the curated PHH assay space.",
            "The synthetic cells are not donor-resolved and do not implement a predeclared donor-disjoint split.",
            "A monotonic software response is not an experimental dose-response validation.",
        ),
    ),
)


def build_injury_runtime_authority() -> InjuryRuntimeAuthority:
    authority = InjuryRuntimeAuthority(
        version=VERSION,
        status="legacy_injury_runtime_exploratory_only",
        surfaces=_LEGACY_SURFACES,
        explicit_purpose_required=True,
        exploratory_execution_allowed=True,
        quantitative_validation_allowed=False,
        predictive_execution_allowed=False,
        authoritative_cell_state_coupling_allowed=False,
        policy=(
            "Legacy injury fixtures may exercise software behavior and qualitative topology. "
            "They may not validate, predict or authoritatively change a PHH state until their "
            "parameters, measurement operators and donor-disjoint validation are supplied."
        ),
    )
    validate_injury_runtime_authority(authority)
    return authority


def validate_injury_runtime_authority(authority: InjuryRuntimeAuthority) -> None:
    expected_ids = {
        "legacy_apoptosis_necrosis_switch",
        "legacy_detox_to_fate_projection",
        "legacy_tissue_injury_population",
    }
    if authority.version != VERSION or authority.status != "legacy_injury_runtime_exploratory_only":
        raise ValueError("Legacy injury authority identity changed")
    if {surface.id for surface in authority.surfaces} != expected_ids:
        raise ValueError("Legacy injury authority surface panel changed")
    if not authority.explicit_purpose_required:
        raise ValueError("Legacy injury runtime purpose became implicit")
    if not authority.exploratory_execution_allowed:
        raise ValueError("Legacy injury exploratory fixture was disabled")
    if (
        authority.quantitative_validation_allowed
        or authority.predictive_execution_allowed
        or authority.authoritative_cell_state_coupling_allowed
    ):
        raise ValueError("Legacy injury runtime escaped its scientific authority gate")
    for surface in authority.surfaces:
        if (
            surface.phh_context_match
            or surface.quantitative_validation_allowed
            or surface.predictive_execution_allowed
            or surface.authoritative_cell_state_coupling_allowed
            or not surface.blockers
        ):
            raise ValueError("Legacy injury surface exceeded exploratory authority")


def assert_injury_runtime_authority(
    purpose: InjuryRuntimePurpose,
) -> InjuryRuntimeAuthority:
    authority = build_injury_runtime_authority()
    if purpose == "exploratory_execution":
        return authority
    allowed = {
        "quantitative_validation": authority.quantitative_validation_allowed,
        "predictive_execution": authority.predictive_execution_allowed,
        "authoritative_cell_state_coupling": authority.authoritative_cell_state_coupling_allowed,
    }
    if purpose not in allowed:
        raise ValueError(f"Unsupported injury runtime purpose: {purpose}")
    if not allowed[purpose]:
        blockers = tuple(
            dict.fromkeys(
                blocker
                for surface in authority.surfaces
                for blocker in surface.blockers
            )
        )
        raise InjuryRuntimeAuthorityError(
            f"{purpose} is blocked for the legacy injury runtime: " + "; ".join(blockers)
        )
    return authority


def injury_runtime_authority_snapshot() -> dict[str, object]:
    authority = build_injury_runtime_authority()
    payload = authority.to_dict()
    payload["summary"] = {
        "audited_legacy_surface_count": len(authority.surfaces),
        "phh_context_matched_surface_count": sum(
            surface.phh_context_match for surface in authority.surfaces
        ),
        "quantitative_authority_surface_count": sum(
            surface.quantitative_validation_allowed for surface in authority.surfaces
        ),
        "predictive_authority_surface_count": sum(
            surface.predictive_execution_allowed for surface in authority.surfaces
        ),
        "authoritative_state_coupling_surface_count": sum(
            surface.authoritative_cell_state_coupling_allowed
            for surface in authority.surfaces
        ),
    }
    return payload
