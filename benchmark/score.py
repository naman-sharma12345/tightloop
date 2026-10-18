#!/usr/bin/env python3
"""benchmark/score.py - turn results/<run-id>/lines.tsv into published tables.

Rules (see MEASURE.md):
- token headline: raw median of per-task ratios (arm tokens_total / no-skill
  tokens_total on the same task), no rounding up
- quality headline: raw ratio of defect counts (no-skill / arm)
- holdout tasks are reported in separate tables, always (split pinned in
  benchmark/tasks/holdout-split.json)
- runs with NO_USAGE / PATCH_FAIL are excluded and counted, never estimated
"""
import json
import statistics
import sys
from pathlib import Path


def load_lines(path: Path):
    rows = []
    lines = path.read_text().splitlines()
    header = lines[0].split("\t")
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) != len(header):
            continue
        rows.append(dict(zip(header, parts)))
    return rows


def num(x):
    try:
        return int(x)
    except (TypeError, ValueError):
        try:
            return float(x)
        except (TypeError, ValueError):
            return None


def table(rows, label):
    by_task = {}
    for r in rows:
        by_task.setdefault(r["task"], {})[r["arm"]] = r
    print(f"--- {label} ({len(by_task)} tasks) ---")
    for task, arms in sorted(by_task.items()):
        cells = []
        for arm in ("no-skill", "ponytail", "tightloop"):
            r = arms.get(arm)
            if not r:
                cells.append(f"{arm}=--")
                continue
            ti, to = num(r["tokens_in"]), num(r["tokens_out"])
            tot = (ti or 0) + (to or 0) if r["status"] == "OK" else r["status"]
            cells.append(f"{arm}: tokens={tot} wall={r['wall_s']}s tests={r['tests_passed']}/{r['tests_total']}")
        print(f"{task}: " + " | ".join(cells))
    for arm in ("ponytail", "tightloop"):
        ratios = []
        for task, arms in sorted(by_task.items()):
            a, b = arms.get(arm), arms.get("no-skill")
            if not a or not b or a["status"] != "OK" or b["status"] != "OK":
                continue
            ta = (num(a["tokens_in"]) or 0) + (num(a["tokens_out"]) or 0)
            tb = (num(b["tokens_in"]) or 0) + (num(b["tokens_out"]) or 0)
            if tb > 0:
                ratios.append(ta / tb)
        if ratios:
            print(f"{arm} token ratio vs no-skill: raw median {statistics.median(ratios)!r} over {len(ratios)} tasks")
        else:
            print(f"{arm} token ratio vs no-skill: no complete pairs")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: score.py benchmark/results/<run-id>", file=sys.stderr)
        return 2
    results_dir = Path(sys.argv[1])
    lines_path = results_dir / "lines.tsv"
    if not lines_path.is_file():
        print(f"no lines.tsv at {results_dir}", file=sys.stderr)
        return 1
    rows = load_lines(lines_path)
    bad = [r for r in rows if r["status"] != "OK"]
    print(f"lines: {len(rows)}; excluded (status != OK): {len(bad)}")
    if not rows:
        print("no runs yet - results pending")
        return 0
    split_path = Path(__file__).parent / "tasks" / "holdout-split.json"
    holdout = set()
    if split_path.is_file():
        holdout = set(json.loads(split_path.read_text()).get("holdout_task_ids", []))
    tune = [r for r in rows if r["task"] not in holdout]
    hold = [r for r in rows if r["task"] in holdout]
    table(tune, "tuning set")
    if hold:
        table(hold, "HOLDOUT - reported separately, never mixed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
