from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

MANIFEST_NAME = "MANIFEST.json"
IGNORED_PARTS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache"}
IGNORED_NAMES = {MANIFEST_NAME, "benchmark-report.json"}


@dataclass(frozen=True)
class SealResult:
    passed: bool
    errors: tuple[str, ...]
    files_checked: int

    def to_dict(self) -> dict[str, object]:
        return {"schema_version": "3.0", "passed": self.passed, "errors": list(self.errors), "files_checked": self.files_checked}


def _eligible(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    return path.is_file() and path.name not in IGNORED_NAMES and path.suffix != ".pyc" and not (set(relative.parts) & IGNORED_PARTS)


def release_files(root: str | Path) -> list[Path]:
    base = Path(root).resolve()
    return sorted((path for path in base.rglob("*") if _eligible(path, base)), key=lambda path: path.relative_to(base).as_posix())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_manifest(root: str | Path) -> dict[str, object]:
    base = Path(root).resolve()
    return {
        "schema_version": "3.0",
        "algorithm": "sha256",
        "files": [
            {"path": path.relative_to(base).as_posix(), "sha256": sha256(path), "size": path.stat().st_size}
            for path in release_files(base)
        ],
    }


def write_manifest(root: str | Path) -> Path:
    base = Path(root).resolve()
    path = base / MANIFEST_NAME
    path.write_text(json.dumps(build_manifest(base), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def verify_manifest(root: str | Path, *, required: bool = True) -> SealResult:
    base = Path(root).resolve()
    path = base / MANIFEST_NAME
    if not path.exists():
        return SealResult(not required, ("release manifest missing",) if required else (), 0)
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return SealResult(False, (f"release manifest unreadable: {exc}",), 0)
    if manifest.get("schema_version") != "3.0" or manifest.get("algorithm") != "sha256":
        return SealResult(False, ("release manifest schema or algorithm invalid",), 0)
    entries = manifest.get("files")
    if not isinstance(entries, list):
        return SealResult(False, ("release manifest files must be a list",), 0)
    errors: list[str] = []
    declared: dict[str, dict[str, object]] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            errors.append("release manifest contains invalid entry")
            continue
        relative = entry["path"]
        if relative in declared:
            errors.append(f"duplicate manifest member: {relative}")
            continue
        declared[relative] = entry
    actual = {item.relative_to(base).as_posix(): item for item in release_files(base)}
    for relative in sorted(set(actual) - set(declared)):
        errors.append(f"unsealed release file: {relative}")
    for relative in sorted(set(declared) - set(actual)):
        errors.append(f"manifest member missing: {relative}")
    for relative in sorted(set(actual) & set(declared)):
        entry = declared[relative]
        path_item = actual[relative]
        if entry.get("sha256") != sha256(path_item):
            errors.append(f"manifest hash mismatch: {relative}")
        if int(entry.get("size", -1)) != path_item.stat().st_size:
            errors.append(f"manifest size mismatch: {relative}")
    return SealResult(not errors, tuple(errors), len(actual))
