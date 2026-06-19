from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Brian2Adapter:
    available: bool
    error: str = ""
    module_name: str = "brian2"

    @classmethod
    def detect(cls) -> "Brian2Adapter":
        try:
            __import__("brian2")
        except Exception as exc:  # pragma: no cover - depends on local install
            return cls(available=False, error=str(exc))
        return cls(available=True)

