from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .selector import ArchitectureDecision


@dataclass(frozen=True)
class CompiledGraph:
    architecture: str
    merge_owner: str
    tasks: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "3.0",
            "architecture": self.architecture,
            "merge_owner": self.merge_owner,
            "tasks": [dict(task) for task in self.tasks],
        }


def _task(
    task_id: str,
    objective: str,
    owner: str,
    consumes: list[str],
    produces: list[str],
    dependencies: list[str],
    *,
    task_type: str,
    max_attempts: int = 2,
) -> dict[str, Any]:
    return {
        "id": task_id,
        "objective": objective,
        "owner": owner,
        "task_type": task_type,
        "consumes": consumes,
        "produces": produces,
        "dependencies": dependencies,
        "done_when": "all declared outputs exist and validate",
        "max_attempts": max_attempts,
        "failure_policy": "block",
    }


def compile_task_graph(
    decision: ArchitectureDecision,
    questions: list[dict[str, Any]],
    *,
    merge_owner: str = "research-supervisor",
) -> CompiledGraph:
    if not questions and decision.architecture not in {"audit-only", "retrieval-only"}:
        raise ValueError("at least one question is required")

    tasks: list[dict[str, Any]] = []
    architecture = decision.architecture

    if architecture == "audit-only":
        tasks.append(_task("audit", "Audit the existing run", "independent-auditor", ["run-artifacts"], ["audit.json"], [], task_type="audit"))
        graph = CompiledGraph(architecture, merge_owner, tuple(tasks))
        _raise_if_invalid(graph)
        return graph

    if architecture == "retrieval-only":
        tasks.extend(
            [
                _task("retrieve", "Retrieve an evidence chain from the existing graph", "retrieval-planner", ["query", "evidence-graph"], ["retrieval-context.json"], [], task_type="retrieval"),
                _task("verify", "Verify the retrieved evidence chain", "claim-verifier", ["retrieval-context.json"], ["verified-context.json"], ["retrieve"], task_type="verification"),
                _task("synthesize", "Render the answer from verified graph material", merge_owner, ["verified-context.json"], ["report.md"], ["verify"], task_type="merge"),
            ]
        )
        graph = CompiledGraph(architecture, merge_owner, tuple(tasks))
        _raise_if_invalid(graph)
        return graph

    tasks.extend(
        [
            _task("scope", "Normalize the research contract", "research-supervisor", ["brief"], ["scope.json"], [], task_type="scope"),
            _task("ontology", "Compile and validate the task ontology", "ontology-architect", ["scope.json"], ["ontology.yaml"], ["scope"], task_type="ontology"),
            _task("plan", "Compile the execution graph and source policy", "research-supervisor", ["scope.json", "ontology.yaml"], ["plan.json"], ["scope", "ontology"], task_type="plan"),
        ]
    )

    if architecture == "single":
        tasks.extend(
            [
                _task("research", "Acquire and extract all evidence in one context", "research-worker", ["plan.json", "ontology.yaml"], ["evidence-batch.jsonl"], ["plan"], task_type="research"),
                _task("verify", "Indepently adjudicate all claims", "claim-verifier", ["evidence-batch.jsonl"], ["verified-claims.jsonl"], ["research"], task_type="verification"),
                _task("synthesize", "Render the report from verified claims", merge_owner, ["verified-claims.jsonl"], ["report.md"], ["verify"], task_type="merge"),
                _task("audit", "Audit completion and evidence coverage", "independent-auditor", ["report.md", "verified-claims.jsonl"], ["audit.json"], ["synthesize", "verify"], task_type="audit"),
            ]
        )
    elif architecture == "diamond":
        verifier_ids: list[str] = []
        verified_outputs: list[str] = []
        for index, question in enumerate(questions, 1):
            qid = str(question.get("id") or f"q{index}")
            research_id = f"research-{qid}"
            verifier_id = f"verify-{qid}"
            finding = f"findings/{qid}.jsonl"
            verified = f"verified/{qid}.jsonl"
            tasks.append(_task(research_id, f"Acquire and extract evidence for {qid}", f"evidence-worker-{index}", ["plan.json", "ontology.yaml"], [finding], ["plan"], task_type="research"))
            tasks.append(_task(verifier_id, f"Independently verify evidence for {qid}", f"claim-verifier-{index}", [finding], [verified], [research_id], task_type="verification"))
            verifier_ids.append(verifier_id)
            verified_outputs.append(verified)
        tasks.extend(
            [
                _task("merge", "Merge verified branches without smoothing contradictions", merge_owner, verified_outputs, ["verified-claims.jsonl"], verifier_ids, task_type="merge"),
                _task("synthesize", "Render the report from the merged verified graph", "synthesis-editor", ["verified-claims.jsonl"], ["report.md"], ["merge"], task_type="synthesis"),
                _task("audit", "Audit completion and evidence coverage", "independent-auditor", ["report.md", "verified-claims.jsonl"], ["audit.json"], ["synthesize", "merge"], task_type="audit"),
            ]
        )
    elif architecture == "hierarchical":
        by_domain: dict[str, list[dict[str, Any]]] = {}
        for index, question in enumerate(questions, 1):
            domain = str(question.get("domain") or "general")
            enriched = dict(question)
            enriched.setdefault("id", f"q{index}")
            by_domain.setdefault(domain, []).append(enriched)
        domain_merge_ids: list[str] = []
        domain_outputs: list[str] = []
        for domain_index, (domain, domain_questions) in enumerate(sorted(by_domain.items()), 1):
            verifier_ids: list[str] = []
            verified_outputs: list[str] = []
            for q_index, question in enumerate(domain_questions, 1):
                qid = str(question["id"])
                research_id = f"research-{qid}"
                verifier_id = f"verify-{qid}"
                finding = f"findings/{qid}.jsonl"
                verified = f"verified/{qid}.jsonl"
                tasks.append(_task(research_id, f"Research {qid} in domain {domain}", f"{domain}-worker-{q_index}", ["plan.json", "ontology.yaml"], [finding], ["plan"], task_type="research"))
                tasks.append(_task(verifier_id, f"Verify {qid} in domain {domain}", f"{domain}-verifier-{q_index}", [finding], [verified], [research_id], task_type="verification"))
                verifier_ids.append(verifier_id)
                verified_outputs.append(verified)
            domain_merge = f"merge-domain-{domain_index}"
            domain_output = f"domains/{domain}.jsonl"
            tasks.append(_task(domain_merge, f"Merge verified findings for domain {domain}", f"domain-lead-{domain_index}", verified_outputs, [domain_output], verifier_ids, task_type="domain-merge"))
            domain_merge_ids.append(domain_merge)
            domain_outputs.append(domain_output)
        tasks.extend(
            [
                _task("merge", "Merge all domain graphs", merge_owner, domain_outputs, ["verified-claims.jsonl"], domain_merge_ids, task_type="merge"),
                _task("synthesize", "Render the report from the merged verified graph", "synthesis-editor", ["verified-claims.jsonl"], ["report.md"], ["merge"], task_type="synthesis"),
                _task("audit", "Audit completion and evidence coverage", "independent-auditor", ["report.md", "verified-claims.jsonl"], ["audit.json"], ["synthesize", "merge"], task_type="audit"),
            ]
        )
    else:
        raise ValueError(f"unsupported architecture: {architecture}")

    graph = CompiledGraph(architecture, merge_owner, tuple(tasks))
    _raise_if_invalid(graph)
    return graph


def validate_compiled_graph(graph: CompiledGraph | dict[str, Any]) -> list[str]:
    data = graph.to_dict() if isinstance(graph, CompiledGraph) else graph
    tasks = data.get("tasks", [])
    errors: list[str] = []
    by_id: dict[str, dict[str, Any]] = {}
    producers: dict[str, str] = {}

    for task in tasks:
        task_id = task.get("id")
        if not task_id or task_id in by_id:
            errors.append(f"duplicate or missing task id: {task_id}")
            continue
        by_id[task_id] = task
        for artifact in task.get("produces", []):
            previous = producers.get(artifact)
            if previous and previous != task.get("owner"):
                errors.append(f"artifact {artifact} has multiple writer owners: {previous}, {task.get('owner')}")
            producers[artifact] = task.get("owner", "")

    for task_id, task in by_id.items():
        consumes = set(task.get("consumes", []))
        for dependency in task.get("dependencies", []):
            parent = by_id.get(dependency)
            if parent is None:
                errors.append(f"{task_id}: missing dependency {dependency}")
                continue
            flowing = set(parent.get("produces", [])) & consumes
            if not flowing:
                errors.append(f"fake dependency: {dependency} -> {task_id}")
        if task.get("task_type") == "verification" and len(task.get("dependencies", [])) == 1:
            parent = by_id.get(task["dependencies"][0])
            if parent and parent.get("owner") == task.get("owner"):
                errors.append(f"{task_id}: verifier cannot own the work it verifies")
        if len(task.get("dependencies", [])) > 1:
            missing_inputs: list[str] = []
            for dependency in task["dependencies"]:
                parent = by_id.get(dependency)
                if parent and not (set(parent.get("produces", [])) & consumes):
                    missing_inputs.append(dependency)
            if missing_inputs:
                errors.append(f"{task_id}: fan-in does not consume outputs from {sorted(missing_inputs)}")

    indegree = {task_id: 0 for task_id in by_id}
    outgoing = {task_id: [] for task_id in by_id}
    for task_id, task in by_id.items():
        for dependency in task.get("dependencies", []):
            if dependency in by_id:
                indegree[task_id] += 1
                outgoing[dependency].append(task_id)
    frontier = [task_id for task_id, degree in indegree.items() if degree == 0]
    visited = 0
    while frontier:
        current = frontier.pop()
        visited += 1
        for child in outgoing[current]:
            indegree[child] -= 1
            if indegree[child] == 0:
                frontier.append(child)
    if visited != len(by_id):
        errors.append("compiled task graph contains a cycle")
    return errors


def _raise_if_invalid(graph: CompiledGraph) -> None:
    errors = validate_compiled_graph(graph)
    if errors:
        raise ValueError("; ".join(errors))
