#!/usr/bin/env python3
"""runner.py - benchmark controller. Launches a headless agent CLI session per
task/arm/run, measures what the CLI reports, grades, writes one row per run.
It never solves tasks. Cross-platform (Windows, macOS, Linux), stdlib only.

Usage:
  python benchmark/runner.py --cli claude|codex --tasks fd-01 gin-01 ... \
      --runs 1 --out results/

Requires: git, Python 3.9+, the chosen agent CLI installed and logged in,
plus each task's toolchain (Rust for fd/clap/bat/tokio/ruff, Go for gin,
Node for zod/axios/vue/prettier, Python+pytest for black/pytest/pydantic).
"""
import argparse, json, os, platform, shutil, subprocess, sys, tempfile, time

ROOT = os.path.dirname(os.path.abspath(__file__))
ARMS = {
    "no-skill": None,
    "ponytail": os.path.join(ROOT, "arms", "ponytail.md"),
    "tightloop": os.path.join(ROOT, "..", ".claude", "skills", "tightloop", "SKILL.md"),
}
UNMEASURED = "unmeasured"

def run(cmd, cwd=None, timeout=None):
    return subprocess.run(cmd, cwd=cwd, timeout=timeout,
                          capture_output=True, text=True)

def git(*a, cwd=None):
    r = run(["git", *a], cwd=cwd)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(a)}: {r.stderr.strip()[:200]}")
    return r.stdout.strip()

def load_task(tid):
    with open(os.path.join(ROOT, "tasks", f"{tid}.json")) as f:
        return json.load(f)

def prepare(task, cache):
    """Fresh checkout at start_commit (bugfix/feature) or empty workspace
    (app). Hidden patch/tests are NOT applied here."""
    if task.get("kind") == "app":
        wt = tempfile.mkdtemp(prefix="tlw-")
        git("init", "-q", cwd=wt)
        return wt
    src = task["source"]
    key = src.rsplit("/", 1)[-1]
    bare = os.path.join(cache, key + ".git")
    if not os.path.isdir(bare):
        run(["git", "clone", "-q", "--bare", src, bare])
    else:
        run(["git", "-C", bare, "fetch", "-q", "origin"])
    wt = tempfile.mkdtemp(prefix="tlw-")
    git("clone", "-q", bare, wt)
    git("checkout", "-q", task["start_commit"], cwd=wt)
    return wt

def launch(cli, prompt, skill, cwd, timeout_s):
    """One fresh headless session. Returns (raw_text, parsed_metrics)."""
    if cli == "claude":
        cmd = ["claude", "-p", prompt, "--output-format", "json",
               "--permission-mode", "bypassPermissions"]
        if skill:
            cmd += ["--append-system-prompt", skill]
    else:
        cmd = ["codex", "exec", "--json", "--full-auto", prompt]
        if skill:  # codex reads AGENTS.md in the cwd
            with open(os.path.join(cwd, "AGENTS.md"), "w") as f:
                f.write(skill)
    t0 = time.time()
    r = run(cmd, cwd=cwd, timeout=timeout_s)
    wall = time.time() - t0
    m = {"input": UNMEASURED, "output": UNMEASURED, "cache": UNMEASURED,
         "total": UNMEASURED, "turns": UNMEASURED, "tool_calls": UNMEASURED,
         "model": UNMEASURED, "agent": f"{cli} {cli_version(cli)}",
         "wall_seconds": round(wall, 2)}
    text = r.stdout + r.stderr
    try:
        if cli == "claude":
            d = json.loads(r.stdout)
            u = d.get("usage", {})
            m.update({
                "input": u.get("input_tokens", UNMEASURED),
                "output": u.get("output_tokens", UNMEASURED),
                "cache": (u.get("cache_read_input_tokens", 0) or 0) +
                         (u.get("cache_creation_input_tokens", 0) or 0) or UNMEASURED,
                "total": u.get("total_tokens", UNMEASURED),
                "turns": d.get("num_turns", UNMEASURED),
                "model": d.get("model", UNMEASURED)})
        else:
            for line in r.stdout.splitlines():
                try:
                    ev = json.loads(line)
                except ValueError:
                    continue
                u = ev.get("usage") or (ev.get("msg") or {}).get("usage")
                if u:
                    m["input"] = u.get("input_tokens", UNMEASURED)
                    m["output"] = u.get("output_tokens", UNMEASURED)
                    m["cache"] = u.get("cached_input_tokens", UNMEASURED)
                    m["total"] = u.get("total_tokens", UNMEASURED)
    except ValueError:
        pass  # unparsable output stays unmeasured
    return text, m

def cli_version(cli):
    r = run([cli, "--version"])
    return r.stdout.strip().split()[0] if r.returncode == 0 and r.stdout.strip() else "unknown"

def grade(task, wt):
    if task.get("kind") == "app":
        tdir = os.path.join(ROOT, "apps", task["name"], "tests")
        for f in os.listdir(tdir):
            shutil.copy(os.path.join(tdir, f), wt)
    else:
        patch = os.path.join(ROOT, "tasks", task["hidden_patch"])
        r = run(["git", "apply", "--whitespace=nowarn", patch], cwd=wt)
        if r.returncode != 0:
            return "invalid", "hidden patch did not apply: " + r.stderr.strip()[:200]
    stat = git("diff", "--shortstat", cwd=wt) or "0 changed"
    r = subprocess.run(task["check_command"], cwd=wt, shell=True,
                       capture_output=True, text=True, timeout=900)
    return ("pass" if r.returncode == 0 else "fail"), stat

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cli", choices=["claude", "codex"], required=True)
    ap.add_argument("--tasks", nargs="+", required=True)
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--out", default="results")
    ap.add_argument("--timeout", type=int, default=1800, help="seconds per session")
    ap.add_argument("--cache", default=".tl-cache", help="repo clone cache dir")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    os.makedirs(a.cache, exist_ok=True)
    env = {"os": f"{platform.system()} {platform.release()}",
           "python": platform.python_version(),
           "cli": a.cli, "cli_version": cli_version(a.cli),
           "git": run(["git", "--version"]).stdout.strip()}
    rows = os.path.join(a.out, "rows.jsonl")
    with open(os.path.join(a.out, "environment.json"), "w") as f:
        json.dump(env, f, indent=2)
    with open(rows, "a") as out:
        for tid in a.tasks:
            task = load_task(tid)
            for arm, skill_path in ARMS.items():
                skill = None
                if skill_path:
                    with open(os.path.normpath(skill_path)) as f:
                        skill = f.read()
                for i in range(a.runs):
                    wt = prepare(task, a.cache)
                    try:
                        prompt = task["instruction"]
                        if task.get("kind") == "app" and task.get("spec"):
                            with open(os.path.join(ROOT, task["spec"])) as f:
                                prompt = f.read()
                        raw, m = launch(a.cli, prompt, skill, wt, a.timeout)
                        result, diffstat = grade(task, wt)
                    finally:
                        shutil.rmtree(wt, ignore_errors=True)
                    row = {"task": tid, "arm": arm, "run": i + 1,
                           "agent": m.pop("agent"), "model": m.pop("model"),
                           "environment": env,
                           "start_commit": task.get("start_commit", "n/a"),
                           "tokens": {k: m[k] for k in ("input", "output", "cache", "total")},
                           "wall_seconds": m["wall_seconds"],
                           "turns": m["turns"], "tool_calls": m["tool_calls"],
                           "diff": diffstat, "result": result}
                    out.write(json.dumps(row) + "\n")
                    out.flush()
                    print(f"{tid} {arm} run{i+1}: {result} "
                          f"tokens={row['tokens']} wall={m['wall_seconds']}s")
    print(f"rows in {os.path.abspath(rows)}")

if __name__ == "__main__":
    main()
