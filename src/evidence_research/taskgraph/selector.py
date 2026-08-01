from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Architecture = Literal["single", "diamond", "hierarchical", "audit-only", "retrieval-only"]
Consequence = Literal["low", "medium", "high", "critical"]


@dataclass(frozen=True)
class WorkProfile:
    question_count: int
    independent_branches: int
    dependency_depth: int
    domain_count: int = 1
    shared_context_ratio: float = 0.0
    source_overlap_ratio: float = 0.0
    sequential_dependency_ratio: float = 0.0
    verification_burden: float = 0.5
    consequence: Consequence = "medium"
    existing_graph: bool = False
    needs_new_evidence: bool = True
    audit_requested: bool = False

    def validate(self) -> None:
        if self.question_count < 0 or self.independent_branches < 0 or self.dependency_depth < 0:
            raise ValueError("counts and dependency depth must be non-negative")
        if self.domain_count < 1:
            raise ValueError("domain_count must be at least 1")
        for name in (
            "shared_context_ratio",
            "source_overlap_ratio",
            "sequential_dependency_ratio",
            "verification_burden",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")


@dataclass(frozen=True)
class ArchitectureDecision:
    architecture: Architecture
    reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    max_parallel: int
    verifier_separation: bool
    human_gate_required: bool
    delegation_depth: int

    def to_dict(self) -> dict[str, object]:
        return {
            "architecture": self.architecture,
            "reasons": list(self.reasons),
            "warnings": list(self.warnings),
            "max_parallel": self.max_parallel,
            "verifier_separation": self.verifier_separation,
            "human_gate_required": self.human_gate_required,
            "delegation_depth": self.delegation_depth,
        }


def select_architecture(profile: WorkProfile, *, max_agents: int = 8) -> ArchitectureDecision:
    profile.validate()
    if max_agents < 1:
        raise ValueError("max_agents must be at least 1")
    reasons: list[str] = []
    warnings: list[str] = []
    human_gate = profile.consequence in {"high", "critical"}
    if profile.audit_requested:
        return ArchitectureDecision("audit-only", ("The request is limited to auditing existing artifacts.",), (), 1, True, human_gate, 1)
    if profile.existing_graph and not profile.needs_new_evidence:
        return ArchitectureDecision("retrieval-only", ("An existing graph can answer the request without new evidence acquisition.",), (), 1, True, human_gate, 1)
    tightly_coupled = profile.independent_branches < 2 or profile.shared_context_ratio >= 0.70 or profile.sequential_dependency_ratio >= 0.65
    if tightly_coupled or max_agents < 3:
        if profile.independent_branches < 2:
            reasons.append("Fewer than two independent branches exist.")
        if profile.shared_context_ratio >= 0.70:
            reasons.append("Most work requires the same shared context.")
        if profile.sequential_dependency_ratio >= 0.65:
            reasons.append("The workflow is predominantly sequential.")
        if max_agents < 3:
            warnings.append("Agent budget cannot reserve separate worker, verifier, and merge roles.")
        return ArchitectureDecision("single", tuple(reasons or ["Single-context execution minimizes coordination overhead."]), tuple(warnings), 1, profile.verification_burden >= 0.50, human_gate, 1)
    hierarchical_candidate = profile.independent_branches >= 6 and profile.domain_count >= 3 and profile.dependency_depth >= 2 and max_agents >= 5
    if hierarchical_candidate:
        reasons.extend(["The task has at least six independent branches.", "The branches span at least three domains.", "Layered fan-in is needed to contain merge complexity."])
        if profile.source_overlap_ratio > 0.65:
            warnings.append("High source overlap may duplicate acquisition; deduplicate source episodes globally.")
        return ArchitectureDecision("hierarchical", tuple(reasons), tuple(warnings), min(profile.independent_branches, max(2, max_agents - 2), 8), True, human_gate, 2)
    reasons.append("Two or more independent artifact branches can execute concurrently.")
    reasons.append("A single fan-in verifier and merge owner are sufficient.")
    if profile.source_overlap_ratio > 0.75:
        warnings.append("High source overlap reduces expected parallel benefit.")
    return ArchitectureDecision("diamond", tuple(reasons), tuple(warnings), min(profile.independent_branches, max(2, max_agents - 2), 6), True, human_gate, 1)
