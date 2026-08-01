from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

DEFAULT_REQUIRED = ("read-local",)
DEFAULT_RESEARCH_ANY_OF = ("web-search", "connected-files", "scholarly-search", "notebooklm")


@dataclass(frozen=True)
class CapabilityCheck:
    passed: bool
    strict: bool
    discovery_available: bool
    available: tuple[str, ...]
    missing_required: tuple[str, ...]
    research_any_of: tuple[str, ...]
    research_capability_satisfied: bool
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "3.0",
            "passed": self.passed,
            "strict": self.strict,
            "discovery_available": self.discovery_available,
            "available": list(self.available),
            "missing_required": list(self.missing_required),
            "research_any_of": list(self.research_any_of),
            "research_capability_satisfied": self.research_capability_satisfied,
            "warnings": list(self.warnings),
        }


def evaluate_capabilities(
    available: Iterable[str] | None,
    *,
    required: Iterable[str] = DEFAULT_REQUIRED,
    research_any_of: Iterable[str] = DEFAULT_RESEARCH_ANY_OF,
    strict: bool = False,
) -> CapabilityCheck:
    required_set = {item.strip().lower() for item in required if item.strip()}
    research_set = {item.strip().lower() for item in research_any_of if item.strip()}
    discovery_available = available is not None
    available_set = {item.strip().lower() for item in (available or ()) if item.strip()}
    warnings: list[str] = []

    if not discovery_available:
        warnings.append("host capability discovery unavailable")
        return CapabilityCheck(
            passed=not strict,
            strict=strict,
            discovery_available=False,
            available=(),
            missing_required=tuple(sorted(required_set)) if strict else (),
            research_any_of=tuple(sorted(research_set)),
            research_capability_satisfied=False,
            warnings=tuple(warnings),
        )

    missing_required = tuple(sorted(required_set - available_set))
    research_satisfied = not research_set or bool(research_set & available_set)
    if missing_required:
        warnings.append("required host capabilities are missing")
    if not research_satisfied:
        warnings.append("no supported research acquisition capability is available")
    return CapabilityCheck(
        passed=not missing_required and research_satisfied,
        strict=strict,
        discovery_available=True,
        available=tuple(sorted(available_set)),
        missing_required=missing_required,
        research_any_of=tuple(sorted(research_set)),
        research_capability_satisfied=research_satisfied,
        warnings=tuple(warnings),
    )


def parse_capabilities(value: str | None) -> tuple[str, ...] | None:
    if value is None:
        return None
    return tuple(sorted({item.strip().lower() for item in value.split(",") if item.strip()}))
