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


def main() -> int:
    engine = selected_engine()
    module_name = "researchctl_v3_demo" if engine == "v3" and len(sys.argv) > 1 and sys.argv[1] == "demo" else f"researchctl_{engine}"
    module = importlib.import_module(module_name)
    return int(module.main())


if __name__ == "__main__":
    raise SystemExit(main())
