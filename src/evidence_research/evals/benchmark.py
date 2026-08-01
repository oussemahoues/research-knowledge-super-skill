from __future__ import annotations

import json
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..acquisition import SourceEpisodeStore, scan_untrusted_content
from ..graph import FusionEngine, TemporalGraph
from ..ontology.registry import check_evolution
from ..retrieval.graph_search import shortest_path
from ..retrieval.query import classify_query
from ..runtime import DurableExecutor, EventStore, TaskResult
from ..taskgraph import WorkProfile, compile_task_graph, select_architecture, validate_compiled_graph
from ..verification import EvidenceChainVerifier
from .promotion import PromotionResult, evaluate_promotion

EXPECTED_CATEGORY_COUNTS = {
    "normal": 30,
    "multi_hop": 20,
    "temporal": 15,
    "conflicting": 10,
    "entity_resolution": 10,
    "ontology_drift": 5,
    "adversarial": 10,
}


@dataclass(frozen=True)
class BenchmarkCaseResult:
    case_id: str
    category: str
    passed: bool
    expected: Any
    actual: Any
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "category": self.category,
            "passed": self.passed,
            "expected": self.expected,
            "actual": self.actual,
            "details": self.details,
        }


@dataclass(frozen=True)
class BenchmarkReport:
    corpus_id: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    category_counts: dict[str, int]
    category_accuracy: dict[str, float]
    metrics: dict[str, float]
    promotion: PromotionResult
    cases: tuple[BenchmarkCaseResult, ...]

    @property
    def passed(self) -> bool:
        return self.failed_cases == 0 and self.promotion.passed

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "3.0",
            "corpus_id": self.corpus_id,
            "passed": self.passed,
            "total_cases": self.total_cases,
            "passed_cases": self.passed_cases,
            "failed_cases": self.failed_cases,
            "category_counts": self.category_counts,
            "category_accuracy": self.category_accuracy,
            "metrics": self.metrics,
            "promotion": self.promotion.to_dict(),
            "cases": [case.to_dict() for case in self.cases],
        }


def load_corpus(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != "3.0":
        raise ValueError("benchmark corpus schema_version must be 3.0")
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise ValueError("benchmark corpus cases must be a list")
    ids = [str(case.get("id", "")) for case in cases]
    if any(not case_id for case_id in ids) or len(ids) != len(set(ids)):
        raise ValueError("benchmark case IDs must be non-empty and unique")
    counts = Counter(str(case.get("category", "")) for case in cases)
    if dict(counts) != EXPECTED_CATEGORY_COUNTS:
        raise ValueError(f"benchmark category counts differ from fixed contract: {dict(counts)}")
    return payload


def run_benchmark(
    corpus_path: str | Path,
    *,
    control_metrics: dict[str, float] | None = None,
) -> BenchmarkReport:
    corpus = load_corpus(corpus_path)
    results: list[BenchmarkCaseResult] = []
    conflict_lexical: list[float] = []
    supported_claims = 0
    resolvable_claims = 0
    contested_correct = 0
    entity_correct = 0
    temporal_correct = 0
    path_correct = 0
    injection_attacks = 0

    with tempfile.TemporaryDirectory(prefix="evidence-research-benchmark-") as tmp:
        root = Path(tmp)
        for case in corpus["cases"]:
            category = case["category"]
            if category == "normal":
                actual = classify_query(case["query"], entity_count=int(case.get("entity_count", 0)))
                expected = case["expected_class"]
                result = BenchmarkCaseResult(case["id"], category, actual == expected, expected, actual, {})
            elif category == "multi_hop":
                path = shortest_path(case["edges"], case["start"], case["end"], max_hops=int(case["max_hops"]))
                actual_hops = None if path is None else (len(path) - 1) // 2
                expected = int(case["expected_hops"])
                passed = actual_hops == expected
                path_correct += int(passed)
                result = BenchmarkCaseResult(case["id"], category, passed, expected, actual_hops, {"path": list(path or ())})
            elif category == "temporal":
                actual = _run_temporal_case(root, case)
                expected = case["expected_to"]
                passed = actual == expected
                temporal_correct += int(passed)
                result = BenchmarkCaseResult(case["id"], category, passed, expected, actual, {})
            elif category == "conflicting":
                verification = _run_conflict_case(root, case)
                actual = verification.status
                expected = case["expected_status"]
                passed = actual == expected
                contested_correct += int(passed)
                conflict_lexical.append(float(verification.lexical_entailment))
                if verification.support_edge_ids:
                    supported_claims += 1
                if verification.source_episode_ids and len(verification.source_episode_ids) == 2:
                    resolvable_claims += 1
                result = BenchmarkCaseResult(
                    case["id"], category, passed, expected, actual,
                    {"lexical_entailment": verification.lexical_entailment, "issues": list(verification.issues)},
                )
            elif category == "entity_resolution":
                actual = _run_entity_case(root, case)
                expected = case["expected_decision"]
                passed = actual == expected
                entity_correct += int(passed)
                result = BenchmarkCaseResult(case["id"], category, passed, expected, actual, {})
            elif category == "ontology_drift":
                actual = check_evolution(case["previous"], case["proposed"]).compatible
                expected = bool(case["expected_compatible"])
                result = BenchmarkCaseResult(case["id"], category, actual == expected, expected, actual, {})
            elif category == "adversarial":
                actual, findings = scan_untrusted_content(case["content"])
                expected = case["expected_risk"]
                passed = actual == expected
                if expected == "quarantine" and actual != "quarantine":
                    injection_attacks += 1
                result = BenchmarkCaseResult(
                    case["id"], category, passed, expected, actual,
                    {"findings": [finding.code for finding in findings]},
                )
            else:
                raise AssertionError(category)
            results.append(result)

        resume_idempotency = _probe_resume_idempotency(root)
        graph_integrity = _probe_task_graph_integrity()

    counts = Counter(result.category for result in results)
    passed_counts = Counter(result.category for result in results if result.passed)
    category_accuracy = {category: passed_counts[category] / count for category, count in sorted(counts.items())}
    conflict_count = counts["conflicting"]
    metrics: dict[str, float] = {
        "claim_evidence_coverage": supported_claims / conflict_count,
        "citation_resolvability": resolvable_claims / conflict_count,
        "unsupported_material_claims": float(conflict_count - supported_claims),
        "contested_claim_disclosure": contested_correct / conflict_count,
        "citation_entailment": sum(conflict_lexical) / len(conflict_lexical),
        "auto_merge_precision": entity_correct / counts["entity_resolution"],
        "temporal_validity_accuracy": temporal_correct / counts["temporal"],
        "multi_hop_recall_at_10": path_correct / counts["multi_hop"],
        "resume_idempotency_correctness": 1.0 if resume_idempotency else 0.0,
        "fake_task_dependencies": float(graph_integrity["fake_task_dependencies"]),
        "self_verification_violations": float(graph_integrity["self_verification_violations"]),
        "unbounded_loops": float(graph_integrity["unbounded_loops"]),
        "successful_injection_attacks": float(injection_attacks),
        "normal_query_accuracy": category_accuracy["normal"],
        "ontology_evolution_accuracy": category_accuracy["ontology_drift"],
    }
    promotion = evaluate_promotion(metrics, control=control_metrics)
    passed_cases = sum(result.passed for result in results)
    return BenchmarkReport(
        corpus_id=str(corpus.get("corpus_id", "unknown")),
        total_cases=len(results),
        passed_cases=passed_cases,
        failed_cases=len(results) - passed_cases,
        category_counts=dict(sorted(counts.items())),
        category_accuracy=category_accuracy,
        metrics=metrics,
        promotion=promotion,
        cases=tuple(results),
    )


def _run_temporal_case(root: Path, case: dict[str, Any]) -> str | None:
    run_id = f"run:{case['id']}"
    store = EventStore(root / f"{case['id']}.db")
    store.create_run(run_id, case["id"])
    graph = TemporalGraph(store)
    subject = graph.put_node(run_id, "Asset", case["from_id"], {"name": case["from_id"]})
    target_ids: dict[str, str] = {}
    for record in case["edges"]:
        target = graph.put_node(run_id, "Status", record["to_id"], {"name": record["to_id"]})
        target_ids[target.node_id] = record["to_id"]
        graph.add_edge(
            run_id, case["edge_type"], subject.node_id, target.node_id,
            valid_from=record["valid_from"], valid_to=record.get("valid_to"),
        )
    active = graph.edges_as_of(run_id, case["as_of"], edge_type=case["edge_type"], from_id=subject.node_id)
    if len(active) != 1:
        return None
    return target_ids.get(active[0].to_id)


def _run_conflict_case(root: Path, case: dict[str, Any]):
    run_id = f"run:{case['id']}"
    case_root = root / case["id"]
    store = EventStore(case_root / "state.db")
    store.create_run(run_id, case["id"])
    episodes = SourceEpisodeStore(store, case_root / "sources")
    support_source = episodes.record(
        run_id, "support-source", "benchmark://support", case["support_text"],
        authority="primary", independence_group="support-family",
    )
    contradiction_source = episodes.record(
        run_id, "contradiction-source", "benchmark://contradiction", case["contradiction_text"],
        authority="primary", independence_group="contradiction-family",
    )
    graph = TemporalGraph(store)
    claim = graph.put_node(run_id, "Claim", case["id"], {"text": case["claim_text"], "material": True})
    support = graph.put_node(run_id, "EvidenceSpan", case["id"] + ":support", {"text": case["support_text"]})
    contradiction = graph.put_node(run_id, "EvidenceSpan", case["id"] + ":contradiction", {"text": case["contradiction_text"]})
    graph.add_edge(
        run_id, "SUPPORTS", support.node_id, claim.node_id,
        valid_from="2026-01-01T00:00:00Z", source_episode_id=support_source.episode_id,
        provenance={"locator": "benchmark support"},
    )
    graph.add_edge(
        run_id, "CONTRADICTS", contradiction.node_id, claim.node_id,
        valid_from="2026-01-01T00:00:00Z", source_episode_id=contradiction_source.episode_id,
        provenance={"locator": "benchmark contradiction"},
    )
    return EvidenceChainVerifier(store).verify_claim(run_id, claim.node_id)


def _run_entity_case(root: Path, case: dict[str, Any]) -> str:
    run_id = f"run:{case['id']}"
    store = EventStore(root / f"{case['id']}.db")
    store.create_run(run_id, case["id"])
    graph = TemporalGraph(store)
    for side in ("left", "right"):
        data = dict(case[side])
        graph.put_node(
            run_id, data["entity_type"], data["node_id"],
            {
                "name": data["name"], "aliases": data.get("aliases", []),
                "identifiers": data.get("identifiers", {}), "attributes": data.get("attributes", {}),
            },
        )
    proposals = FusionEngine(store).proposals(run_id)
    if len(proposals) != 1:
        return "no_unique_proposal"
    return proposals[0].decision


def _probe_resume_idempotency(root: Path) -> bool:
    run_id = "run:idempotency-probe"
    store = EventStore(root / "idempotency.db")
    store.create_run(run_id, "Idempotency probe")
    executor = DurableExecutor(store)
    executor.register_graph(run_id, {"tasks": [{
        "id": "once", "objective": "Execute once", "task_type": "research", "owner": "worker",
        "consumes": [], "produces": ["probe.json"], "dependencies": [],
        "done_when": "artifact exists", "max_attempts": 1, "failure_policy": "block",
    }]})
    artifact = {
        "artifact_id": "artifact:probe", "path": "probe.json",
        "content_hash": "sha256:probe", "media_type": "application/json",
    }
    first = executor.run_task(run_id, "once", "worker-1", lambda: TaskResult([artifact], {"execution": 1}))
    second = executor.run_task(run_id, "once", "worker-2", lambda: TaskResult([], {"execution": 2}))
    return first.artifacts[0]["artifact_id"] == "artifact:probe" and bool(second.metadata.get("replayed"))


def _probe_task_graph_integrity() -> dict[str, int]:
    fake = {"tasks": [
        {"id": "a", "owner": "one", "task_type": "research", "consumes": [], "produces": ["a.json"], "dependencies": []},
        {"id": "b", "owner": "two", "task_type": "merge", "consumes": ["other.json"], "produces": ["b.json"], "dependencies": ["a"]},
    ]}
    self_verify = {"tasks": [
        {"id": "a", "owner": "same", "task_type": "research", "consumes": [], "produces": ["a.json"], "dependencies": []},
        {"id": "v", "owner": "same", "task_type": "verification", "consumes": ["a.json"], "produces": ["v.json"], "dependencies": ["a"]},
    ]}
    fake_errors = validate_compiled_graph(fake)
    verify_errors = validate_compiled_graph(self_verify)
    decision = select_architecture(WorkProfile(question_count=1, independent_branches=1, dependency_depth=1))
    compiled = compile_task_graph(decision, [{"id": "q1", "text": "Probe", "domain": "general"}])
    unbounded = sum(
        1 for task in compiled.tasks
        if int(task.get("max_attempts", 0)) < 1 or int(task.get("max_attempts", 0)) > 3
    )
    return {
        "fake_task_dependencies": 0 if any("fake dependency" in error for error in fake_errors) else 1,
        "self_verification_violations": 0 if any("verifier cannot own" in error for error in verify_errors) else 1,
        "unbounded_loops": unbounded,
    }
