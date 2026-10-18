#!/usr/bin/env python3
"""benchmark/score.py - turn a results directory into published tables.

Rules (see MEASURE.md):
- token headline: raw median of per-task ratios (arm / no-skill)
- quality headline: raw ratio of defect scores (no-skill / arm)
- holdout tasks reported separately, never mixed
- no rounding up, no estimates; runs missing token data are excluded
  and counted
"""
import json
import statistics
import sys
from pathlib import Path


def load_results(results_dir: Path):
    runs = []
    for task_dir in sorted(results_dir.iterdir()):
        if not task_dir.is_dir():
            continue
        for arm_dir in sorted(task_dir.iterdir()):
            entry = {"task": task_dir.name, "arm": arm_dir.name}
            for name in ("tokens", "tests", "review"):
                path = arm_dir / f"{name}.json"
                entry[name] = json.loads(path.read_text()) if path.exists() else None
            runs.append(entry)
    return runs


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: score.py benchmark/results/<run-id>", file=sys.stderr)
        return 2
    results_dir = Path(sys.argv[1])
    if not results_dir.is_dir():
        print(f"no results at {results_dir}", file=sys.stderr)
        return 1
    runs = load_results(results_dir)
    usable = [r for r in runs if r["tokens"] and r["tests"] and r["review"]]
    print(f"runs found: {len(runs)}; usable (tokens+tests+review): {len(usable)}")
    if not usable:
        print("no complete runs yet - results pending")
        return 0
    by_task = {}
    for r in usable:
        by_task.setdefault(r["task"], {})[r["arm"]] = r
    for arm in ("ponytail", "tightloop"):
        ratios = []
        for task, arms in sorted(by_task.items()):
            if "no-skill" in arms and arm in arms:
                ratios.append(arms[arm]["tokens"]["total"] / arms["no-skill"]["tokens"]["total"])
        if ratios:
            print(f"{arm} token ratio vs no-skill: raw median {statistics.median(ratios)!r} over {len(ratios)} tasks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
