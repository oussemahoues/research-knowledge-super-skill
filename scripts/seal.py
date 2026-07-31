#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE = {"MANIFEST.json", "evidence-research-plugin.zip"}
entries = []
for path in sorted(p for p in ROOT.rglob("*") if p.is_file()):
    rel = path.relative_to(ROOT).as_posix()
    if rel in EXCLUDE or "__pycache__" in rel:
        continue
    data = path.read_bytes()
    entries.append({"path": rel, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
manifest = {"schema": "evidence-research-manifest-v1", "version": "2.0.0", "files": entries}
(ROOT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"sealed {len(entries)} files")
