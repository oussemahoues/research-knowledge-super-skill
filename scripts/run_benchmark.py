#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evidence_research.evals import run_benchmark


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the fixed Evidence Research v3 benchmark corpus")
    parser.add_argument("--corpus", default=str(ROOT / "evals" / "benchmark-v3.json"))
    parser.add_argument("--control", default=str(ROOT / "evals" / "baseline-v2" / "promotion-metrics.json"))
    parser.add_argument("--output", default="benchmark-report.json")
    args = parser.parse_args()

    control_path = Path(args.control)
    control = json.loads(control_path.read_text(encoding="utf-8")) if control_path.exists() else None
    report = run_benchmark(args.corpus, control_metrics=control)
    output = Path(args.output)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report.passed, "output": str(output), "metrics": report.metrics}, indent=2))
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
