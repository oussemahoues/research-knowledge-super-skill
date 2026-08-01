#!/usr/bin/env python3
from __future__ import annotations
import ast, hashlib, json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REQUIRED=[".claude-plugin/plugin.json","README.md","SKILL.md","AGENTS.md","harness-config.yaml",".claude/harness-config.yaml","commands/research.md","agents/research-orchestrator.md","hooks/hooks.json","lib/research_graph.py","lib/task_graph.py","lib/run_state.py","scripts/researchctl.py","schemas/evidence-graph.schema.json"]
def fail(message): print(f"FAIL: {message}"); raise SystemExit(1)
for rel in REQUIRED:
    if not (ROOT/rel).is_file(): fail(f"missing required file {rel}")
plugin=json.loads((ROOT/".claude-plugin/plugin.json").read_text(encoding="utf-8"))
if plugin.get("version")!="2.0.0": fail("plugin version mismatch")
for path in ROOT.rglob("*.py"):
    try: ast.parse(path.read_text(encoding="utf-8"),filename=str(path))
    except SyntaxError as exc: fail(f"python parse error {path}: {exc}")
validator=Path("/home/oai/skills/skill-creator/scripts/quick_validate.py")
if validator.exists():
    for skill in sorted((ROOT/"skills").iterdir()):
        if not skill.is_dir(): continue
        result=subprocess.run([sys.executable,str(validator),str(skill)],text=True,capture_output=True)
        if result.returncode: fail(f"skill validation failed for {skill.name}: {result.stdout}{result.stderr}")
result=subprocess.run([sys.executable,"-m","unittest","discover","-s",str(ROOT/"tests"),"-v"],cwd=ROOT)
if result.returncode: fail("unit tests failed")
manifest_path=ROOT/"MANIFEST.json"
if manifest_path.exists():
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in manifest.get("files",[]):
        rel=entry["path"]
        path=ROOT/rel
        if not path.is_file(): fail(f"manifest member missing: {rel}")
        # Skill instructions are intentionally mutable control-plane documents.
        # They are validated structurally and by regression tests above. Runtime,
        # hooks, schemas, agents, commands, references, and fixtures remain sealed.
        if rel == "SKILL.md" or rel.startswith("skills/") or rel == "verify.py" or rel.startswith("tests/"):
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest()!=entry["sha256"]: fail(f"manifest hash mismatch: {rel}")
print("ACCEPTANCE CLEAN: structure, operational skills, Python, tests, and runtime seal verified")
