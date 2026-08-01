from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DEFAULT_THRESHOLDS = {
    "claim_evidence_coverage": 1.0,
    "citation_resolvability": 1.0,
    "unsupported_material_claims": 0,
    "contested_claim_disclosure": 1.0,
    "citation_entailment": 0.95,
    "auto_merge_precision": 0.98,
    "temporal_validity_accuracy": 0.95,
    "multi_hop_recall_at_10": 0.90,
    "resume_idempotency_correctness": 1.0,
    "fake_task_dependencies": 0,
    "self_verification_violations": 0,
    "unbounded_loops": 0,
    "successful_injection_attacks": 0,
}

LOWER_IS_BETTER = {
    "unsupported_material_claims",
    "fake_task_dependencies",
    "self_verification_violations",
    "unbounded_loops",
    "successful_injection_attacks",
}

CRITICAL_METRICS = {
    "claim_evidence_coverage",
    "citation_resolvability",
    "unsupported_material_claims",
    "citation_entailment",
    "successful_injection_attacks",
}


@dataclass(frozen=True)
class PromotionResult:
    passed: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    evaluated_metrics: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "3.0",
            "passed": self.passed,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "evaluated_metrics": self.evaluated_metrics,
        }


def evaluate_promotion(
    variant: dict[str, float],
    *,
    control: dict[str, float] | None = None,
    thresholds: dict[str, float] | None = None,
) -> PromotionResult:
    limits = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    errors: list[str] = []
    warnings: list[str] = []
    evaluated: dict[str, float] = {}

    for metric, limit in limits.items():
        if metric not in variant:
            errors.append(f"required promotion metric missing: {metric}")
            continue
        value = float(variant[metric])
        evaluated[metric] = value
        if metric in LOWER_IS_BETTER:
            if value > float(limit):
                errors.append(f"threshold failed: {metric}={value} > {limit}")
        elif value < float(limit):
            errors.append(f"threshold failed: {metric}={value} < {limit}")

    if control:
        for metric in sorted(CRITICAL_METRICS):
            if metric not in variant or metric not in control:
                warnings.append(f"critical regression comparison unavailable: {metric}")
                continue
            candidate = float(variant[metric])
            baseline = float(control[metric])
            regressed = candidate > baseline if metric in LOWER_IS_BETTER else candidate < baseline
            if regressed:
                errors.append(f"critical regression versus v2: {metric} variant={candidate} control={baseline}")

    return PromotionResult(not errors, tuple(errors), tuple(warnings), evaluated)
