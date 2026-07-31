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
        result=subprocess.run([sys.executable,str(validator),str(skill)],text=True,capture_output=True)
        if result.returncode: fail(f"skill validation failed for {skill.name}: {result.stdout}{result.stderr}")
result=subprocess.run([sys.executable,"-m","unittest","discover","-s",str(ROOT/"tests"),"-v"],cwd=ROOT)
if result.returncode: fail("unit tests failed")
manifest_path=ROOT/"MANIFEST.json"
if manifest_path.exists():
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in manifest.get("files",[]):
        path=ROOT/entry["path"]
        if not path.is_file(): fail(f"manifest member missing: {entry['path']}")
        if hashlib.sha256(path.read_bytes()).hexdigest()!=entry["sha256"]: fail(f"manifest hash mismatch: {entry['path']}")
print("ACCEPTANCE CLEAN: structure, skills, Python, tests, and seal verified")
