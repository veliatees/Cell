from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata, util

from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain


BRIAN2_PINNED_VERSION = "2.10.1"
DATE_VERIFIED = "2026-07-14"

BRIAN2_SOURCES: dict[str, SourceReference] = {
    "brian2_2_10_1": SourceReference(
        id="brian2_2_10_1",
        title="Brian2 2.10.1",
        url="https://pypi.org/project/Brian2/2.10.1/",
        source_type="tool_doc",
        date_verified=DATE_VERIFIED,
        notes="Audited optional backend version; Brian2 supplies equation/event execution, not biological equations or parameter values.",
    ),
    "brian2_custom_events": SourceReference(
        id="brian2_custom_events",
        title="Brian2 2.10.1: custom events",
        url="https://brian2.readthedocs.io/en/2.10.1/examples/advanced.custom_events.html",
        source_type="tool_doc",
        date_verified=DATE_VERIFIED,
        notes="Documents event-triggered interactions suitable for an optional communication backend.",
    ),
}


@dataclass(frozen=True)
class Brian2CommunicationModelSpec:
    id: str
    equation_source_ids: tuple[str, ...]
    parameter_source_ids: tuple[str, ...]
    state_units_complete: bool
    parameters_complete: bool
    contact_geometry_coupled: bool


@dataclass(frozen=True)
class Brian2ExecutionGate:
    backend_available: bool
    package_version: str | None
    version_matches_project_pin: bool
    model_attached: bool
    execution_ready: bool
    blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


@dataclass(frozen=True)
class Brian2Adapter:
    available: bool
    error: str = ""
    module_name: str = "brian2"
    package_version: str | None = None
    supported_role: str = "optional equation/event backend; never the biological authority"

    @classmethod
    def detect(cls) -> "Brian2Adapter":
        if util.find_spec("brian2") is None:
            return cls(available=False, error="module_not_installed")
        try:
            package_version = metadata.version("Brian2")
        except metadata.PackageNotFoundError:
            package_version = None
        except Exception as exc:  # pragma: no cover - local metadata failure
            return cls(available=False, error=str(exc))
        return cls(available=True, package_version=package_version)

    def assess_communication_model(
        self,
        spec: Brian2CommunicationModelSpec | None = None,
    ) -> Brian2ExecutionGate:
        blockers: list[str] = []
        if not self.available:
            blockers.append("Brian2 backend is not installed")
        version_matches = self.package_version == BRIAN2_PINNED_VERSION
        if self.available and not version_matches:
            blockers.append(
                f"Brian2 version must match the audited project pin {BRIAN2_PINNED_VERSION}"
            )
        if spec is None:
            blockers.append("no calibrated intercellular communication model is attached")
        else:
            if not spec.equation_source_ids:
                blockers.append("communication equations lack source provenance")
            if not spec.parameter_source_ids or not spec.parameters_complete:
                blockers.append("communication parameters are incomplete or lack provenance")
            if not spec.state_units_complete:
                blockers.append("communication state units are incomplete")
            if not spec.contact_geometry_coupled:
                blockers.append("contact-dependent equations are not coupled to contact geometry")
        return Brian2ExecutionGate(
            backend_available=self.available,
            package_version=self.package_version,
            version_matches_project_pin=version_matches,
            model_attached=spec is not None,
            execution_ready=not blockers,
            blockers=tuple(blockers),
        )


def brian2_communication_snapshot() -> dict[str, object]:
    adapter = Brian2Adapter.detect()
    gate = adapter.assess_communication_model()
    return {
        "adapter": adapter,
        "gate": gate,
        "pinned_version": BRIAN2_PINNED_VERSION,
        "role": adapter.supported_role,
        "automatic_state_coupling": False,
        "source_ids": tuple(BRIAN2_SOURCES),
    }
