#!/usr/bin/env python3
from __future__ import annotations

import importlib
import os
import sys


def selected_engine() -> str:
    engine = os.environ.get("EVIDENCE_RESEARCH_ENGINE", "v3").strip().lower()
    if engine not in {"v2", "v3"}:
        raise SystemExit("EVIDENCE_RESEARCH_ENGINE must be v2 or v3")
    return engine


def _load(name: str):
    try:
        return importlib.import_module(f"scripts.{name}")
    except ModuleNotFoundError as exc:
        if exc.name != f"scripts.{name}":
            raise
        return importlib.import_module(name)


def cmd_demo(args) -> int:
    """Compatibility entrypoint retained for legacy tests and callers."""
    if selected_engine() == "v2":
        return int(_load("researchctl_v2").cmd_demo(args))
    return int(_load("researchctl_v3_demo").run_demo(args.path))


def main() -> int:
    engine = selected_engine()
    module_name = "researchctl_v3_demo" if engine == "v3" and len(sys.argv) > 1 and sys.argv[1] == "demo" else f"researchctl_{engine}"
    return int(_load(module_name).main())


if __name__ == "__main__":
    raise SystemExit(main())
