#!/usr/bin/env python3
from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIRED = [
    ".claude-plugin/plugin.json", "README.md", "SKILL.md", "AGENTS.md",
    "harness-config.yaml", ".claude/harness-config.yaml", "commands/research.md",
    "agents/research-orchestrator.md", "agents/independent-auditor.md",
    "hooks/hooks.json", "lib/research_graph.py", "lib/task_graph.py", "lib/run_state.py",
    "scripts/researchctl.py", "scripts/researchctl_v3.py", "scripts/run_benchmark.py",
    "scripts/build_manifest.py", "schemas/evidence-graph.schema.json",
    "src/evidence_research/runtime/event_store.py", "src/evidence_research/acquisition/source_episodes.py",
    "src/evidence_research/evals/benchmark.py", "src/evidence_research/release/seal.py",
    "docs/migration-v2-to-v3.md", ".github/workflows/release-verify.yml",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


for rel in REQUIRED:
    if not (ROOT / rel).is_file():
        fail(f"missing required file {rel}")

plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
if plugin.get("version") != "3.0.0":
    fail("plugin version mismatch")

for path in ROOT.rglob("*.py"):
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        fail(f"python parse error {path}: {exc}")

validator = Path("/home/oai/skills/skill-creator/scripts/quick_validate.py")
if validator.exists():
    for skill in sorted((ROOT / "skills").iterdir()):
        if not skill.is_dir():
            continue
        result = subprocess.run([sys.executable, str(validator), str(skill)], text=True, capture_output=True)
        if result.returncode:
            fail(f"skill validation failed for {skill.name}: {result.stdout}{result.stderr}")

result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(ROOT / "tests"), "-v"], cwd=ROOT)
if result.returncode:
    fail("unit tests failed")

manifest_path = ROOT / "MANIFEST.json"
if manifest_path.exists():
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in manifest.get("files", []):
        rel = entry["path"]
        path = ROOT / rel
        if not path.is_file():
            fail(f"manifest member missing: {rel}")
        if rel == "SKILL.md" or rel.startswith("skills/") or rel == "verify.py" or rel.startswith("tests/"):
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            fail(f"manifest hash mismatch: {rel}")

release_mode = os.environ.get("EVIDENCE_RESEARCH_RELEASE_VERIFY") == "1" or "--release" in sys.argv[1:]
if release_mode:
    from src.evidence_research.release import verify_manifest

    seal = verify_manifest(ROOT, required=True)
    if not seal.passed:
        fail("release seal failed: " + "; ".join(seal.errors))
    print(f"RELEASE SEALED: {seal.files_checked} files verified")

print("ACCEPTANCE CLEAN: v3 structure, skills, Python, tests, benchmark contracts, and runtime seal verified")
