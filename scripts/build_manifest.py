#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evidence_research.release import verify_manifest, write_manifest


def main() -> int:
    path = write_manifest(ROOT)
    result = verify_manifest(ROOT, required=True)
    print(json.dumps({"manifest": str(path), **result.to_dict()}, indent=2))
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
