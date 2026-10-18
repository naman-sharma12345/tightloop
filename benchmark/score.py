#!/usr/bin/env python3
"""benchmark/score.py - turn a results dir into published tables.

Reads results/<run-id>/lines.tsv (run.sh) or, if that is absent,
<dir>/rows.jsonl (runner.py).

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


ARMS = ("no-skill", "ponytail", "tightloop", "tightloop-v3", "tightloop-v4", "tightloop-v4a")


def load_rows_jsonl(path: Path):
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def tok(r, keys):
    """Sum of the named token fields, or None if any is not a number."""
    vals = [r.get("tokens", {}).get(k) for k in keys]
    if any(not isinstance(v, (int, float)) or isinstance(v, bool) for v in vals):
        return None
    return sum(vals)


def table_jsonl(rows, label):
    by_task = {}
    for r in rows:
        by_task.setdefault(r["task"], {}).setdefault(r["arm"], []).append(r)
    print(f"--- {label} ({len(by_task)} tasks) ---")
    for task, arms in sorted(by_task.items()):
        for arm in ARMS:
            for r in arms.get(arm, []):
                t = r.get("tokens", {})
                print(f"{task} {arm} run{r.get('run')}: result={r.get('result')} "
                      f"in={t.get('input')} out={t.get('output')} cache={t.get('cache')} "
                      + (f"(read {t.get('cache_read')}, creation {t.get('cache_creation')}) "
                         if "cache_read" in t else "")
                      + f"total={t.get('total')} wall={r.get('wall_seconds')}s "
                      f"turns={r.get('turns')} tool_calls={r.get('tool_calls')} "
                      f"overlap={r.get('overlap')} rename={r.get('rename_applied')} "
                      f"fallback={r.get('hidden_patch_fallback')}"
                      + (f" diff=+{r['agent_diff_added']}/-{r['agent_diff_deleted']}"
                         if "agent_diff_added" in r else "")
                      + (f" note={r['note']}" if r.get("note") else ""))
    measures = [("input+output", ("input", "output")),
                ("input+output+cache", ("input", "output", "cache"))]
    if any("cache_read" in r.get("tokens", {}) for arms in by_task.values()
           for rs in arms.values() for r in rs):
        # MEASURE.md's definition: input + output + cache reads
        measures.append(("input+output+cache_read", ("input", "output", "cache_read")))
    for name, keys in measures:
        for arm in ARMS[1:]:
            if not any(arm in arms for arms in by_task.values()):
                continue
            ratios = []
            for task, arms in sorted(by_task.items()):
                a, b = arms.get(arm, []), arms.get("no-skill", [])
                for ra, rb in zip(a, b):  # run i vs run i
                    ta, tb = tok(ra, keys), tok(rb, keys)
                    if ta is None or tb is None or tb == 0:
                        continue
                    ratios.append(ta / tb)
            if ratios:
                print(f"{arm} token ratio ({name}) vs no-skill: raw median "
                      f"{statistics.median(ratios)!r} over {len(ratios)} pairs")
            else:
                print(f"{arm} token ratio ({name}) vs no-skill: no measured pairs")
    for arm in ARMS:
        res = [r.get("result") for arms in by_task.values() for r in arms.get(arm, [])]
        if res:
            graded = res.count("pass") + res.count("fail")
            print(f"{arm} results: " + ", ".join(f"{k}={res.count(k)}"
                                                for k in sorted(set(res)))
                  + (f"; pass {res.count('pass')}/{graded} graded" if graded else ""))


def main_jsonl(rows_path: Path, holdout) -> int:
    rows = load_rows_jsonl(rows_path)
    superseded = [r for r in rows if str(r.get("status", "")).startswith("superseded")]
    if superseded:
        print(f"--- excluded, superseded ({len(superseded)} rows; redone, kept for the record) ---")
        for r in superseded:
            print(f"{r['task']} {r['arm']} run{r.get('run')}: result={r.get('result')} "
                  f"status={r.get('status')}")
        rows = [r for r in rows if r not in superseded]
    harness_bad = [r for r in rows if str(r.get("status", "")).startswith("invalid-harness")]
    if harness_bad:
        print(f"--- excluded, invalid-harness ({len(harness_bad)} rows; not in pass rate or ratios) ---")
        for r in harness_bad:
            print(f"{r['task']} {r['arm']} run{r.get('run')}: result={r.get('result')} "
                  f"status={r.get('status')}")
        rows = [r for r in rows if r not in harness_bad]
    print(f"rows counted: {len(rows)} (from {rows_path.name}, {len(harness_bad)} invalid-harness "
          f"and {len(superseded)} superseded excluded); not pass/fail: {sum(r.get('result') not in ('pass', 'fail') for r in rows)}")
    if not rows:
        print("no runs yet - results pending")
        return 0
    # passes are scored separately (rows without a "pass" field are pass 1);
    # a ratio only ever pairs rows of the same pass
    for p in sorted({r.get("pass") or 1 for r in rows}):
        pr = [r for r in rows if (r.get("pass") or 1) == p]
        tune = [r for r in pr if r["task"] not in holdout]
        hold = [r for r in pr if r["task"] in holdout]
        table_jsonl(tune, f"pass {p}, tuning set")
        if hold:
            table_jsonl(hold, f"pass {p}, HOLDOUT - reported separately, never mixed")
    return 0


def load_holdout():
    split_path = Path(__file__).parent / "tasks" / "holdout-split.json"
    if split_path.is_file():
        return set(json.loads(split_path.read_text()).get("holdout_task_ids", []))
    return set()


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: score.py <results dir with lines.tsv or rows.jsonl> | <rows.jsonl>", file=sys.stderr)
        return 2
    results_dir = Path(sys.argv[1])
    lines_path = results_dir / "lines.tsv"
    if not lines_path.is_file():
        rows_path = results_dir / "rows.jsonl"
        if results_dir.is_file() and results_dir.suffix == ".jsonl":
            rows_path = results_dir
        if rows_path.is_file():
            return main_jsonl(rows_path, load_holdout())
        print(f"no lines.tsv or rows.jsonl at {results_dir}", file=sys.stderr)
        return 1
    rows = load_lines(lines_path)
    bad = [r for r in rows if r["status"] != "OK"]
    print(f"lines: {len(rows)}; excluded (status != OK): {len(bad)}")
    if not rows:
        print("no runs yet - results pending")
        return 0
    holdout = load_holdout()
    tune = [r for r in rows if r["task"] not in holdout]
    hold = [r for r in rows if r["task"] in holdout]
    table(tune, "tuning set")
    if hold:
        table(hold, "HOLDOUT - reported separately, never mixed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
