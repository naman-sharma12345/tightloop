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
import argparse, hashlib, json, os, platform, re, shutil, signal, subprocess, sys, tempfile, time, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
ARMS = {
    "no-skill": None,
    "ponytail": None,  # pinned upstream SKILL.md, loaded by ponytail_skill()
    "tightloop": os.path.join(ROOT, "..", ".claude", "skills", "tightloop", "SKILL.md"),
}
UNMEASURED = "unmeasured"
# ponytail arm: the real skill file at the pin recorded in arms/ponytail.md
PONYTAIL_PIN = "09c434ab73ca43761c5d8b0c5d341926c2fba710"
PONYTAIL_URL = ("https://raw.githubusercontent.com/DietrichGebert/ponytail/"
                + PONYTAIL_PIN + "/skills/ponytail/SKILL.md")
PONYTAIL_SHA256 = "9badd22a32e19cb884e46dfa8d3aae82bb81dfa5484105b8b4f0262df823a509"
# solver sessions may not use the CLI's own web tools; Bash keeps network
# (the API itself, and cargo/go module downloads, need it)
DISALLOWED_TOOLS = ["WebFetch", "WebSearch"]
SECRET_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL",
              "OPENAI_API_KEY", "OPENAI_BASE_URL")

def run(cmd, cwd=None, timeout=None):
    return subprocess.run(cmd, cwd=cwd, timeout=timeout,
                          capture_output=True, text=True)

def git(*a, cwd=None):
    r = run(["git", *a], cwd=cwd)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(a)}: {r.stderr.strip()[:200]}")
    return r.stdout.strip()

def scrub(text):
    """Remove credential / endpoint values of this environment from a log."""
    for k in SECRET_ENV:
        v = os.environ.get(k)
        if v and len(v) >= 8:
            text = text.replace(v, f"<{k} redacted>")
    return text

def run_logged(cmd, cwd, timeout_s, log_path, shell=False):
    """Run cmd in its own process group, stdout/stderr to files, kill the
    whole group on timeout. Returns (returncode or None on timeout, stdout,
    stderr)."""
    out_p, err_p = log_path + ".stdout", log_path + ".stderr"
    with open(out_p, "w") as fo, open(err_p, "w") as fe:
        p = subprocess.Popen(cmd, cwd=cwd, shell=shell, stdout=fo, stderr=fe,
                             stdin=subprocess.DEVNULL, start_new_session=True)
        try:
            rc = p.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            p.wait()
            rc = None
    texts = []
    for pth in (out_p, err_p):
        with open(pth, errors="replace") as f:
            t = scrub(f.read())
        with open(pth, "w") as f:
            f.write(t)
        texts.append(t)
    return rc, texts[0], texts[1]

def strip_pr_refs(instruction):
    """Drop upstream PR numbers like "(#4336)" so the prompt does not point
    at the reference fix. Task JSON is left as it is."""
    return re.sub(r"\s*\(#\d+\)", "", instruction).strip()

def ponytail_skill(cache):
    """The pinned ponytail SKILL.md (fetched once into the cache, sha256
    checked). Falls back to arms/ponytail.md, labelled, if it cannot be
    fetched."""
    os.makedirs(cache, exist_ok=True)
    p = os.path.join(cache, f"ponytail-{PONYTAIL_PIN[:12]}-SKILL.md")
    if not os.path.isfile(p):
        try:
            data = urllib.request.urlopen(PONYTAIL_URL, timeout=60).read()
            if hashlib.sha256(data).hexdigest() == PONYTAIL_SHA256:
                with open(p, "wb") as f:
                    f.write(data)
        except OSError:
            pass
    if os.path.isfile(p):
        with open(p) as f:
            return f.read(), f"ponytail SKILL.md @ {PONYTAIL_PIN} (sha256 {PONYTAIL_SHA256[:12]})"
    with open(os.path.join(ROOT, "arms", "ponytail.md")) as f:
        return f.read(), "description doc, not the skill (ponytail SKILL.md could not be fetched)"

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

def launch(cli, prompt, skill, cwd, timeout_s, log_path):
    """One fresh headless session. Returns (raw_text, parsed_metrics).
    Raw stdout/stderr are kept at log_path.stdout / .stderr."""
    if cli == "claude":
        cmd = ["claude", "-p", prompt, "--output-format", "json",
               "--permission-mode", "bypassPermissions",
               "--disallowedTools", *DISALLOWED_TOOLS]
        if skill:
            cmd += ["--append-system-prompt", skill]
    else:
        cmd = ["codex", "exec", "--json", "--full-auto", prompt]
        if skill:  # codex reads AGENTS.md in the cwd
            with open(os.path.join(cwd, "AGENTS.md"), "w") as f:
                f.write(skill)
    t0 = time.time()
    rc, stdout, stderr = run_logged(cmd, cwd, timeout_s, log_path)
    wall = time.time() - t0
    m = {"input": UNMEASURED, "output": UNMEASURED, "cache": UNMEASURED,
         "total": UNMEASURED, "turns": UNMEASURED, "tool_calls": UNMEASURED,
         "model": UNMEASURED, "model_from_modelUsage": UNMEASURED,
         "agent": f"{cli} {cli_version(cli)}",
         "wall_seconds": round(wall, 2), "timed_out": rc is None,
         "infra_error": None}
    text = stdout + stderr
    try:
        if cli == "claude":
            d = json.loads(stdout)
            u = d.get("usage", {})
            m.update({
                "input": u.get("input_tokens", UNMEASURED),
                "output": u.get("output_tokens", UNMEASURED),
                "cache": (u.get("cache_read_input_tokens", 0) or 0) +
                         (u.get("cache_creation_input_tokens", 0) or 0) or UNMEASURED,
                "total": u.get("total_tokens", UNMEASURED),
                "turns": d.get("num_turns", UNMEASURED),
                "model": d.get("model", UNMEASURED)})
            if d.get("modelUsage"):
                m["model_from_modelUsage"] = sorted(d["modelUsage"])
            if d.get("api_error_status") is not None:
                m["infra_error"] = (f"api_error_status {d.get('api_error_status')}: "
                                    + str(d.get("result", ""))[:300])
        else:
            for line in stdout.splitlines():
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
        # unparsable output stays unmeasured; with no timeout it is an
        # infrastructure error (auth, network, rate limit, crash)
        if rc is not None and cli == "claude":
            m["infra_error"] = f"exit {rc}, no JSON result: " + text.strip()[-300:]
    return text, m

def cli_version(cli):
    r = run([cli, "--version"])
    return r.stdout.strip().split()[0] if r.returncode == 0 and r.stdout.strip() else "unknown"

def grade(task, wt, timeout_s, log_path):
    if task.get("kind") == "app":
        tdir = os.path.join(ROOT, "apps", task["name"], "tests")
        for f in os.listdir(tdir):
            src = os.path.join(tdir, f)
            if os.path.isdir(src):
                shutil.copytree(src, os.path.join(wt, f))
            else:
                shutil.copy(src, wt)
    else:
        patch = os.path.join(ROOT, "tasks", task["hidden_patch"])
        r = run(["git", "apply", "--whitespace=nowarn", patch], cwd=wt)
        if r.returncode != 0:
            return "invalid", "hidden patch did not apply: " + r.stderr.strip()[:200]
    stat = git("diff", "--shortstat", cwd=wt) or "0 changed"
    rc, _, _ = run_logged(task["check_command"], wt, timeout_s, log_path, shell=True)
    if rc is None:
        return "timeout", stat
    return ("pass" if rc == 0 else "fail"), stat

def tool_versions():
    v = {}
    for name, cmd in (("go", ["go", "version"]), ("rustc", ["rustc", "--version"]),
                      ("cargo", ["cargo", "--version"]), ("node", ["node", "--version"])):
        try:
            r = run(cmd)
            v[name] = r.stdout.strip() or "not found"
        except OSError:
            v[name] = "not found"
    return v

def harness_commit():
    r = run(["git", "rev-parse", "HEAD"], cwd=ROOT)
    dirty = run(["git", "status", "--porcelain", "--", "."], cwd=ROOT).stdout.strip()
    return (r.stdout.strip() or "unknown") + (" (+uncommitted changes)" if dirty else "")

def free_mib(path):
    s = shutil.disk_usage(path)
    return s.free // (1024 * 1024)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cli", choices=["claude", "codex"], required=True)
    ap.add_argument("--tasks", nargs="+", required=True)
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--out", default="results")
    ap.add_argument("--timeout", type=int, default=1800, help="seconds per session")
    ap.add_argument("--grade-timeout", type=int, default=900, help="seconds per grader run")
    ap.add_argument("--cache", default=".tl-cache", help="repo clone cache dir")
    ap.add_argument("--min-free-mib", type=int, default=0,
                    help="stop before a new session if free disk (at --out) is below this")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    os.makedirs(a.cache, exist_ok=True)
    logs = os.path.join(a.out, "logs")
    os.makedirs(logs, exist_ok=True)
    tasks = [load_task(t) for t in a.tasks]
    ponytail_text, ponytail_note = ponytail_skill(a.cache)
    with open(os.path.normpath(ARMS["tightloop"])) as f:
        tightloop_text = f.read()
    skills = {"no-skill": (None, "no skill"),
              "ponytail": (ponytail_text, ponytail_note),
              "tightloop": (tightloop_text, "tightloop .claude/skills/tightloop/SKILL.md "
                            "from this harness commit")}
    env = {"os": f"{platform.system()} {platform.release()}",
           "machine": platform.machine(),
           "python": platform.python_version(),
           "cli": a.cli, "cli_version": cli_version(a.cli),
           "git": run(["git", "--version"]).stdout.strip(),
           "harness_commit": harness_commit(),
           "tools": tool_versions(),
           "task_start_commits": {t["name"]: t.get("start_commit", "n/a") for t in tasks},
           "arms": {k: v[1] for k, v in skills.items()},
           "skill_delivery": ("--append-system-prompt" if a.cli == "claude"
                              else "AGENTS.md in the task checkout"),
           "prompt": "task instruction with upstream PR refs like (#123) removed",
           "network": ("Claude Code built-in web tools denied with --disallowedTools "
                       + " ".join(DISALLOWED_TOOLS) + ". NOT network-isolated: the CLI "
                       "needs the model API, and its Bash tool (cargo, go, git, curl) "
                       "keeps network access." if a.cli == "claude" else
                       "no restriction applied (codex)"),
           "session_timeout_s": a.timeout, "grade_timeout_s": a.grade_timeout,
           "unmeasured_fields": (["tool_calls (not in claude -p JSON)",
                                  "tokens.total (claude -p JSON has no total_tokens)",
                                  "model (claude -p JSON has no top-level model; see "
                                  "model_from_modelUsage per row)"]
                                 if a.cli == "claude" else ["turns", "tool_calls", "model"]),
           "notes": "tokens.cache = cache_read_input_tokens + cache_creation_input_tokens"}
    with open(os.path.join(a.out, "environment.json"), "w") as f:
        json.dump(env, f, indent=2)
    rows = os.path.join(a.out, "rows.jsonl")
    models_seen = set()
    stopped = None
    with open(rows, "a") as out:
        for task in tasks:
            tid = task["name"]
            for arm in ARMS:
                skill, arm_note = skills[arm]
                for i in range(a.runs):
                    if a.min_free_mib and free_mib(a.out) < a.min_free_mib:
                        stopped = (f"DISK STOP {free_mib(a.out)} MiB free before "
                                   f"{tid}/{arm}/run{i+1}")
                        break
                    tag = f"{tid}_{arm}_{i+1}"
                    wt = prepare(task, a.cache)
                    try:
                        prompt = strip_pr_refs(task["instruction"])
                        if task.get("kind") == "app" and task.get("spec"):
                            with open(os.path.join(ROOT, task["spec"])) as f:
                                prompt = f.read()
                        raw, m = launch(a.cli, prompt, skill, wt, a.timeout,
                                        os.path.join(logs, tag + ".agent"))
                        note = None
                        if m["timed_out"]:
                            result, diffstat = "timeout", "session timed out; grader not run"
                            note = f"session exceeded {a.timeout}s"
                        elif m["infra_error"]:
                            result, diffstat = "invalid", "grader not run"
                            note = m["infra_error"]
                        else:
                            result, diffstat = grade(task, wt, a.grade_timeout,
                                                     os.path.join(logs, tag + ".grade"))
                            if result == "timeout":
                                note = f"grader exceeded {a.grade_timeout}s"
                    finally:
                        shutil.rmtree(wt, ignore_errors=True)
                    if isinstance(m["model_from_modelUsage"], list):
                        models_seen.update(m["model_from_modelUsage"])
                    row = {"task": tid, "arm": arm, "run": i + 1,
                           "agent": m.pop("agent"), "model": m.pop("model"),
                           "model_from_modelUsage": m["model_from_modelUsage"],
                           "arm_note": arm_note,
                           "environment": env,
                           "start_commit": task.get("start_commit", "n/a"),
                           "prompt": prompt,
                           "tokens": {k: m[k] for k in ("input", "output", "cache", "total")},
                           "wall_seconds": m["wall_seconds"],
                           "turns": m["turns"], "tool_calls": m["tool_calls"],
                           "diff": diffstat, "result": result, "note": note,
                           "logs": os.path.join("logs", tag + ".*")}
                    out.write(json.dumps(row) + "\n")
                    out.flush()
                    print(f"{tid} {arm} run{i+1}: {result} "
                          f"tokens={row['tokens']} wall={m['wall_seconds']}s", flush=True)
                if stopped:
                    break
            if stopped:
                break
    env["models_reported_modelUsage"] = sorted(models_seen) or UNMEASURED
    if stopped:
        env["stopped"] = stopped
        print(stopped)
    with open(os.path.join(a.out, "environment.json"), "w") as f:
        json.dump(env, f, indent=2)
    print(f"rows in {os.path.abspath(rows)}")

if __name__ == "__main__":
    main()
