#!/usr/bin/env python3
from __future__ import annotations

import importlib
import os


def selected_engine() -> str:
    engine = os.environ.get("EVIDENCE_RESEARCH_ENGINE", "v3").strip().lower()
    if engine not in {"v2", "v3"}:
        raise SystemExit("EVIDENCE_RESEARCH_ENGINE must be v2 or v3")
    return engine


def main() -> int:
    module = importlib.import_module(f"researchctl_{selected_engine()}")
    return int(module.main())


if __name__ == "__main__":
    raise SystemExit(main())
