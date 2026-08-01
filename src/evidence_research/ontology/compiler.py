from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OntologyValidation:
    passed: bool
    errors: list[str]
    paths: dict[str, list[str]]


def validate_ontology(ontology: dict[str, Any]) -> OntologyValidation:
    errors: list[str] = []
    entities = ontology.get('entities', {})
    relations = ontology.get('relations', {})
    questions = ontology.get('competency_questions', [])
    if not entities:
        errors.append('ontology requires entity types')
    graph: dict[str, list[tuple[str, str]]] = {name: [] for name in entities}
    for name, spec in relations.items():
        domain, range_ = spec.get('domain'), spec.get('range')
        if domain not in entities or range_ not in entities:
            errors.append(f'{name}: invalid domain/range {domain}->{range_}')
            continue
        graph[domain].append((name, range_))
    paths: dict[str, list[str]] = {}
    for question in questions:
        qid = question.get('id')
        start = question.get('start_type')
        end = question.get('end_type')
        if not qid or start not in entities or end not in entities:
            errors.append(f'competency question {qid or "<missing>"}: invalid start/end type')
            continue
        path = _find_path(graph, start, end, max_hops=int(question.get('max_hops', 4)))
        if path is None:
            errors.append(f'{qid}: no legal ontology path from {start} to {end}')
        else:
            paths[qid] = path
    return OntologyValidation(not errors, errors, paths)


def _find_path(graph: dict[str, list[tuple[str, str]]], start: str, end: str, max_hops: int) -> list[str] | None:
    frontier: list[tuple[str, list[str]]] = [(start, [])]
    visited = {(start, 0)}
    while frontier:
        node, path = frontier.pop(0)
        if node == end:
            return path
        if len(path) >= max_hops:
            continue
        for relation, nxt in graph.get(node, []):
            state = (nxt, len(path) + 1)
            if state in visited:
                continue
            visited.add(state)
            frontier.append((nxt, path + [relation]))
    return None


def compile_minimal_ontology(contract: dict[str, Any], proposed: dict[str, Any]) -> dict[str, Any]:
    ontology = {
        'schema_version': '3.0',
        'version': 1,
        'run_target': contract['target'],
        'competency_questions': proposed.get('competency_questions', contract.get('competency_questions', [])),
        'entities': proposed.get('entities', {}),
        'relations': proposed.get('relations', {}),
        'events': proposed.get('events', {}),
        'canonicalization': proposed.get('canonicalization', {}),
        'candidate_relations': [],
    }
    result = validate_ontology(ontology)
    if not result.passed:
        raise ValueError('; '.join(result.errors))
    ontology['validated_paths'] = result.paths
    return ontology
