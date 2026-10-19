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
    # each tightloop arm: (its skill folder in this repo, folder name installed in the checkout)
    "tightloop-v3": os.path.join(ROOT, "arms", "tightloop-v3"),
    "tightloop-v4": os.path.join(ROOT, "arms", "tightloop-v4"),  # 1.0: the pre-1.0 root skill, byte copy (the root .claude/skills/tightloop/ is now v11)
    # v4a = v4 minus its step-4 skeptic rule (one-rule iteration); gate.sh and phases/ identical to v4
    "tightloop-v4a": os.path.join(ROOT, "arms", "tightloop-v4a"),
    # v4b = v4 with step 4 kept but no gate rerun unless a code or test line changed
    "tightloop-v4b": os.path.join(ROOT, "arms", "tightloop-v4b"),
    # v5 = quality-first app mode with look.py self-check (design 0be26dc/A1, 70b7958/A2)
    "tightloop-v5": os.path.join(ROOT, "arms", "tightloop-v5"),
    # v5b = v5 with no screenshot and a lower-thinking instruction (pre-registered in A1)
    "tightloop-v5b": os.path.join(ROOT, "arms", "tightloop-v5b"),
    "tightloop-v4c": os.path.join(ROOT, "arms", "tightloop-v4c"), "tightloop-v8": os.path.join(ROOT, "arms", "tightloop-v8"),  # instinct rows: arm folders byte-identical to v6/v8-prep b16a28e
    "tightloop-v10": os.path.join(ROOT, "arms", "tightloop-v10"),  # v10 = v4c with the gate diff echo removed (instinct/PREREG_v10.md)
    "tightloop-v4c-gfix": os.path.join(ROOT, "arms", "tightloop-v4c-gfix"), "tightloop-v10-gfix": os.path.join(ROOT, "arms", "tightloop-v10-gfix"),  # gatefix: v4c / v10 with gate.sh line 25 anchored (instinct/GATEFIX.md)
}
# the v3 arm refuses to run unless its skill text is byte-identical to v3
TIGHTLOOP_V3_SHA256 = "f83ba03a192729f84e8d448680fa69dcadf41483f9ae056e6bba7dfc19d1bd6a"
# the v5 / v5b arms refuse to run unless their SKILL.md is byte-identical to the text
# committed in criteria amendment A2 (70b7958); the skill text is delivered by
# --append-system-prompt, so its tokens are in every call's measured usage
TIGHTLOOP_PINNED_SHA256 = {
    "tightloop-v3": TIGHTLOOP_V3_SHA256,
    "tightloop-v5": "04e3ca1487f2b795fa4c17a41f424fdb7f6635533170adbe5c322a97c4bc1d39",
    "tightloop-v5b": "a451229802a17d1df235a9907f300100181344400761d5af04c7d18bd5259caf",
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

def lock_busy(path):
    """True if another process holds an flock on path (checked without
    waiting; the lock is released at once if we got it). None if unknown."""
    try:
        import fcntl
    except ImportError:
        return None
    try:
        fd = os.open(path, os.O_RDONLY)
    except FileNotFoundError:
        return False
    except OSError:
        return None
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(fd, fcntl.LOCK_UN)
        return False
    except BlockingIOError:
        return True
    finally:
        os.close(fd)

def procs_under(prefix, exclude_pgid=None, cmd_substr=None):
    """Count processes whose working directory is under prefix (and whose
    command line contains cmd_substr, if given) via Linux /proc (None
    elsewhere), leaving out our own session's process group."""
    if not prefix or not os.path.isdir("/proc"):
        return None
    n = 0
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            if exclude_pgid is not None and os.getpgid(int(pid)) == exclude_pgid:
                continue
            if not os.readlink(f"/proc/{pid}/cwd").startswith(prefix):
                continue
            if cmd_substr:
                with open(f"/proc/{pid}/cmdline", "rb") as fh:
                    if cmd_substr.encode() not in fh.read():
                        continue
            n += 1
        except OSError:
            continue
    return n

def loadavg():
    try:
        return [round(x, 2) for x in os.getloadavg()]
    except (AttributeError, OSError):
        return UNMEASURED

def run_logged(cmd, cwd, timeout_s, log_path, shell=False, watch_lock=None,
               samples=None, watch_cwd=None, overlap=None, watch_cmd=None):
    """Run cmd in its own process group, stdout/stderr to files, kill the
    whole group on timeout. Returns (returncode or None on timeout, stdout,
    stderr). With watch_lock, appends lock_busy() to samples every ~30 s."""
    out_p, err_p = log_path + ".stdout", log_path + ".stderr"
    with open(out_p, "w") as fo, open(err_p, "w") as fe:
        p = subprocess.Popen(cmd, cwd=cwd, shell=shell, stdout=fo, stderr=fe,
                             stdin=subprocess.DEVNULL, start_new_session=True)
        try:
            deadline = time.time() + timeout_s
            t_start = time.time()
            def sample():
                if watch_lock and samples is not None:
                    samples.append(lock_busy(watch_lock))
                if overlap is not None:
                    la = loadavg()
                    overlap.append({"t": round(time.time() - t_start, 1),
                                    "load1": la[0] if isinstance(la, list) else la,
                                    "lock_busy": lock_busy(watch_lock) if watch_lock else None,
                                    "procs_under_prefix": procs_under(watch_cwd, p.pid, watch_cmd)})
            while True:
                sample()
                try:
                    rc = p.wait(timeout=max(0.1, min(30, deadline - time.time())))
                    sample()  # end sample
                    break
                except subprocess.TimeoutExpired:
                    if time.time() >= deadline:
                        raise
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

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()

def skill_folder(arm, ponytail_text):
    """The arm's skill folder as {relative path in the checkout: bytes, mode}.
    Same mechanism for every arm: ponytail gets its pinned SKILL.md at
    .claude/skills/ponytail/, each tightloop arm gets its whole folder at
    .claude/skills/tightloop/, no-skill gets nothing."""
    if arm == "no-skill":
        return {}
    if arm == "ponytail":
        return {".claude/skills/ponytail/SKILL.md": (ponytail_text.encode(), 0o644)}
    src = os.path.normpath(ARMS[arm])
    files = {}
    for dp, _, fns in os.walk(src):
        for fn in sorted(fns):
            if fn.endswith(".pyc"):
                continue
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, src).replace(os.sep, "/")
            with open(p, "rb") as fh:
                files[".claude/skills/tightloop/" + rel] = (fh.read(), os.stat(p).st_mode & 0o777)
    return files

def restore_gate_backup(wt):
    """tightloop-v4's gate.sh backs up the source files it reverts in
    .git/tightloop-gate/ (files = list, tree/ = copies) and restores them on
    exit. If a session ended with that dir present (the gate was killed
    mid-revert), restore the files the same way and return their list; the
    row is then marked invalid-harness and not graded. Same check on every arm."""
    gd = run(["git", "rev-parse", "--absolute-git-dir"], cwd=wt).stdout.strip()
    bk = os.path.join(gd, "tightloop-gate") if gd else None
    if not bk or not os.path.isdir(bk):
        return []
    restored = []
    lst = os.path.join(bk, "files")
    if os.path.isfile(lst):
        with open(lst) as fh:
            for f in [x for x in fh.read().split("\n") if x]:
                src = os.path.join(bk, "tree", f)
                if os.path.isfile(src):
                    os.makedirs(os.path.dirname(os.path.join(wt, f)) or wt, exist_ok=True)
                    shutil.copy2(src, os.path.join(wt, f))
                    os.utime(os.path.join(wt, f))  # newer than any build of the reverted copy
                    restored.append(f)
    shutil.rmtree(bk, ignore_errors=True)
    return restored or ["(backup dir without files)"]

def install_skill(files, wt):
    """Write the arm's skill folder into the checkout and git-exclude it
    (.git/info/exclude), so it is never part of the agent's diff, the rename
    rule or grading. Returns [{path, bytes, sha256}]."""
    out = []
    for rel, (data, mode) in sorted(files.items()):
        p = os.path.join(wt, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as fh:
            fh.write(data)
        os.chmod(p, mode)
        out.append({"path": rel, "bytes": len(data), "sha256": sha256_bytes(data)})
    if files:
        ex = run(["git", "rev-parse", "--git-path", "info/exclude"], cwd=wt).stdout.strip()
        ex = ex if os.path.isabs(ex) else os.path.join(wt, ex)
        os.makedirs(os.path.dirname(ex), exist_ok=True)
        dirs = sorted({"/" + "/".join(r.split("/")[:3]) + "/" for r in files})
        with open(ex, "a") as fh:
            fh.write("\n" + "\n".join(dirs) + "\n")
    return out

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

def launch(cli, prompt, skill, cwd, timeout_s, log_path, watch_lock=None, watch_cwd=None,
           watch_cmd=None):
    """One fresh headless session. Returns (raw_text, parsed_metrics).
    Raw stdout/stderr are kept at log_path.stdout / .stderr."""
    if cli == "claude":
        cmd = ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose",
               "--permission-mode", "bypassPermissions",
               "--disallowedTools", *DISALLOWED_TOOLS]
        if skill:
            cmd += ["--append-system-prompt", skill]
    else:
        cmd = ["codex", "exec", "--json", "--full-auto", prompt]
        if skill:  # codex reads AGENTS.md in the cwd
            with open(os.path.join(cwd, "AGENTS.md"), "w") as f:
                f.write(skill)
    samples = []
    overlap = []
    load0 = loadavg()
    t0 = time.time()
    rc, stdout, stderr = run_logged(cmd, cwd, timeout_s, log_path,
                                    watch_lock=watch_lock, samples=samples,
                                    watch_cwd=watch_cwd, overlap=overlap, watch_cmd=watch_cmd)
    wall = time.time() - t0
    load1 = loadavg()
    m = {"input": UNMEASURED, "output": UNMEASURED, "cache": UNMEASURED,
         "total": UNMEASURED, "turns": UNMEASURED, "tool_calls": UNMEASURED,
         "model": UNMEASURED, "model_from_modelUsage": UNMEASURED,
         "cache_read": UNMEASURED, "cache_creation": UNMEASURED,
         "tool_calls_main": UNMEASURED, "tool_calls_by_name": UNMEASURED,
         "skills_listed": UNMEASURED,
         "phase_reads": UNMEASURED, "gate_runs": UNMEASURED, "gate_output_bytes": UNMEASURED,
         "agent": f"{cli} {cli_version(cli)}",
         "wall_seconds": round(wall, 2), "timed_out": rc is None,
         "infra_error": None, "loadavg_start": load0, "loadavg_end": load1,
         "lock_busy_during": ("unknown" if not watch_lock or None in samples or not samples
                              else "yes" if any(samples) else "no"),
         "lock_samples": len(samples),
         "overlap_samples": overlap,
         "overlap": ("unknown" if not (watch_lock or watch_cwd) or not overlap else
                     "overlapped" if any(s["lock_busy"] or (s["procs_under_prefix"] or 0) > 0
                                         for s in overlap) else "clean")}
    text = stdout + stderr
    try:
        if cli == "claude":
            # stream-json: one event per line; the final "result" event carries
            # what --output-format json used to (usage, num_turns, modelUsage).
            # tool_calls = distinct tool_use ids in assistant events, counted
            # exactly (subagent calls included; tool_calls_main = parent only).
            evs = []
            for line in stdout.splitlines():
                try:
                    evs.append(json.loads(line))
                except ValueError:
                    continue
            res = [e for e in evs if isinstance(e, dict) and e.get("type") == "result"]
            if not res:
                raise ValueError("no result event")
            d = res[-1]
            uses = {}
            for e in evs:
                if isinstance(e, dict) and e.get("type") == "assistant":
                    for c in (e.get("message") or {}).get("content") or []:
                        if isinstance(c, dict) and c.get("type") == "tool_use":
                            uses[c["id"]] = (c.get("name"), e.get("parent_tool_use_id"))
            by_name = {}
            for nm, _ in uses.values():
                by_name[nm] = by_name.get(nm, 0) + 1
            # per tool_use: its input text; per tool_result: its content bytes
            inputs, results = {}, {}
            for e in evs:
                if not isinstance(e, dict):
                    continue
                for c in (e.get("message") or {}).get("content") or []:
                    if not isinstance(c, dict):
                        continue
                    if c.get("type") == "tool_use" and e.get("type") == "assistant":
                        inputs[c["id"]] = json.dumps(c.get("input"))
                    elif c.get("type") == "tool_result" and e.get("type") == "user":
                        cont = c.get("content")
                        if isinstance(cont, list):
                            cont = "".join(x.get("text", "") for x in cont if isinstance(x, dict))
                        results[c.get("tool_use_id")] = len(str(cont or "").encode())
            phase_reads = {}
            for ph in ("phases/fail.md", "phases/risky.md"):
                phase_reads[ph.split("/")[1]] = sum(1 for i in inputs.values() if ph in i)
            gate_ids = [k for k, i in inputs.items()
                        if uses.get(k, ("",))[0] == "Bash" and "tightloop/gate.sh" in i]
            init = [e for e in evs if isinstance(e, dict) and e.get("type") == "system"
                    and e.get("subtype") == "init"]
            m.update({"tool_calls": len(uses),
                      "tool_calls_main": sum(1 for _, par in uses.values() if par is None),
                      "tool_calls_by_name": by_name,
                      "skills_listed": (init[0].get("skills", UNMEASURED) if init else UNMEASURED),
                      "phase_reads": phase_reads, "gate_runs": len(gate_ids),
                      "gate_output_bytes": sum(results.get(k, 0) for k in gate_ids)})
            u = d.get("usage", {})
            m.update({
                "input": u.get("input_tokens", UNMEASURED),
                "output": u.get("output_tokens", UNMEASURED),
                "cache": (u.get("cache_read_input_tokens", 0) or 0) +
                         (u.get("cache_creation_input_tokens", 0) or 0) or UNMEASURED,
                "total": u.get("total_tokens", UNMEASURED),
                "cache_read": u.get("cache_read_input_tokens", UNMEASURED),
                "cache_creation": u.get("cache_creation_input_tokens", UNMEASURED),
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

def save_diff(wt, path):
    """The agent's change vs the start commit, untracked files included,
    written before the grader touches the tree. Returns lines added+deleted."""
    tracked = run(["git", "diff", "HEAD"], cwd=wt).stdout
    parts = [tracked]
    others = run(["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=wt).stdout
    for f in [x for x in others.split("\0") if x]:
        parts.append(run(["git", "diff", "--no-index", "--", os.devnull, f], cwd=wt).stdout)
    text = scrub("".join(parts))
    with open(path, "w") as fh:
        fh.write(text)
    ls = text.splitlines()
    return (sum(1 for l in ls if l.startswith("+") and not l.startswith("+++")),
            sum(1 for l in ls if l.startswith("-") and not l.startswith("---")))

def rename_colliding_tests(task, wt):
    """If the agent ADDED a test function with the same name as a hidden test
    (Rust `fn NAME(`, Go `func NAME(`), rename only that added definition to
    NAME_agent so the hidden patch does not create a duplicate. Lines that
    exist at the start commit, the hidden patch, task files and graders are
    never touched. Returns a list of {file, line, from, to}."""
    names = task.get("hidden_tests") or []
    if not names:
        return []
    pats = {n: re.compile(r"^(\s*(?:pub\s+)?(?:async\s+)?fn\s+|\s*func\s+)" + re.escape(n) + r"(\s*[(<])")
            for n in names}
    added = {}  # file -> set of 1-based line numbers added by the agent
    cur = None
    for l in run(["git", "diff", "-U0", "HEAD"], cwd=wt).stdout.splitlines():
        if l.startswith("+++ "):
            cur = l[6:] if l.startswith("+++ b/") else None
        elif l.startswith("@@") and cur:
            m = re.search(r"\+(\d+)(?:,(\d+))?", l)
            start, count = int(m.group(1)), int(m.group(2) or 1)
            added.setdefault(cur, set()).update(range(start, start + count))
    others = run(["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=wt).stdout
    for f in [x for x in others.split("\0") if x]:
        added[f] = None  # whole file is the agent's
    done = []
    for f, lines in added.items():
        p = os.path.join(wt, f)
        if not os.path.isfile(p):
            continue
        try:
            with open(p) as fh:
                content = fh.read().split("\n")
        except (UnicodeDecodeError, OSError):
            continue
        changed = False
        for i, line in enumerate(content, 1):
            if lines is not None and i not in lines:
                continue
            for n, pat in pats.items():
                if pat.match(line):
                    new = pat.sub(lambda m: m.group(1) + n + "_agent" + m.group(2), line, count=1)
                    content[i - 1] = new
                    done.append({"file": f, "line": i, "from": n, "to": n + "_agent"})
                    changed = True
        if changed:
            with open(p, "w") as fh:
                fh.write("\n".join(content))
    return done

def grade(task, wt, timeout_s, log_path, reset):
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
            # Same rule on every arm, only when the hidden patch does not apply
            # to the agent's tree: the files the hidden patch touches (its test
            # files) are restored to the start commit, dropping the agent's own
            # edits in those files only, and the patch is applied again. The
            # agent's raw diff was already saved; what was dropped is logged.
            first_err = r.stderr.strip()[:200]
            files = hidden_patch_files(patch, wt)
            for f in files:
                n = run(["git", "diff", "--numstat", "HEAD", "--", f], cwd=wt).stdout.split()
                tracked = run(["git", "cat-file", "-e", "HEAD:" + f], cwd=wt).returncode == 0
                if tracked:
                    run(["git", "checkout", "HEAD", "--", f], cwd=wt)
                elif os.path.exists(os.path.join(wt, f)):
                    os.remove(os.path.join(wt, f))
                reset.append({"file": f,
                              "agent_lines_added": int(n[0]) if n and n[0].isdigit() else 0,
                              "agent_lines_deleted": int(n[1]) if len(n) > 1 and n[1].isdigit() else 0})
            r = run(["git", "apply", "--whitespace=nowarn", patch], cwd=wt)
            if r.returncode != 0:
                return "invalid", ("hidden patch did not apply, even after restoring its files: "
                                   + r.stderr.strip()[:200] + " (first error: " + first_err + ")")
    stat = git("diff", "--shortstat", cwd=wt) or "0 changed"
    rc, _, _ = run_logged(task["check_command"], wt, timeout_s, log_path, shell=True)
    if rc is None:
        return "timeout", stat
    return ("pass" if rc == 0 else "fail"), stat

def hidden_patch_files(patch, wt):
    """Paths the hidden patch touches, from git's own reading of it."""
    out = run(["git", "apply", "--numstat", "-z", patch], cwd=wt).stdout
    files = []
    for rec in [x for x in out.split("\0") if x]:
        parts = rec.split("\t")
        if len(parts) >= 3 and parts[2]:
            files.append(parts[2])
    return sorted(set(files))

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
    dirty = run(["git", "status", "--porcelain", "--untracked-files=no", "--", "."], cwd=ROOT).stdout.strip()
    return (r.stdout.strip() or "unknown") + (" (+uncommitted changes)" if dirty else "")

def free_mib(path):
    s = shutil.disk_usage(path)
    return s.free // (1024 * 1024)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cli", choices=["claude", "codex"], required=True)
    ap.add_argument("--tasks", nargs="+", required=True)
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--rotate", action="store_true",
                    help="rotate arm order per repeat: shift (2*task_index + run_index) mod "
                    "number_of_arms (the pre-registered pass-3 shift rule); default off keeps "
                    "the fixed ARMS order")
    ap.add_argument("--out", default="results")
    ap.add_argument("--timeout", type=int, default=1800, help="seconds per session")
    ap.add_argument("--grade-timeout", type=int, default=900, help="seconds per grader run")
    ap.add_argument("--cache", default=".tl-cache", help="repo clone cache dir")
    ap.add_argument("--wait-lock", default=None,
                    help="flock file another job on this machine holds while it runs: "
                         "wait until free before each session (not held), sample during it")
    ap.add_argument("--wait-lock-max", type=int, default=1800,
                    help="max seconds to wait for --wait-lock before starting anyway")
    ap.add_argument("--arms", nargs="+", default=list(ARMS), choices=list(ARMS),
                    help="arms to run, in the fixed order no-skill, ponytail, tightloop-v3, tightloop-v4, tightloop-v4a, tightloop-v4b, tightloop-v5, tightloop-v5b")
    ap.add_argument("--pass-label", type=int, default=None,
                    help="benchmark pass number written to every row as 'pass'")
    ap.add_argument("--lock-wait-scope", choices=["session", "task"], default="session",
                    help="wait for --wait-lock before every session, or only before the "
                         "first arm of each task so a task's arms run back to back")
    ap.add_argument("--overlap-cwd", default=None,
                    help="also tag a session overlapped if any process outside it has its "
                         "working directory under this prefix at a sample")
    ap.add_argument("--overlap-cmd", default=None,
                    help="with --overlap-cwd, only count processes whose command line contains this")
    ap.add_argument("--pause-file", default=None,
                    help="before each session, wait while this file exists")
    ap.add_argument("--min-free-mib", type=int, default=0,
                    help="stop before a new session if free disk (at --out) is below this")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    os.makedirs(a.cache, exist_ok=True)
    logs = os.path.join(a.out, "logs")
    os.makedirs(logs, exist_ok=True)
    diffs = os.path.join(a.out, "diffs")
    os.makedirs(diffs, exist_ok=True)
    tasks = [load_task(t) for t in a.tasks]
    ponytail_text, ponytail_note = ponytail_skill(a.cache)
    skills = {"no-skill": (None, "no skill"),
              "ponytail": (ponytail_text, ponytail_note)}
    versions = {"no-skill": "n/a", "ponytail": "ponytail " + PONYTAIL_PIN[:12]}
    for arm in ("tightloop-v3", "tightloop-v4", "tightloop-v4a", "tightloop-v4b",
                "tightloop-v5", "tightloop-v5b", "tightloop-v4c", "tightloop-v8", "tightloop-v10", "tightloop-v4c-gfix", "tightloop-v10-gfix"):
        with open(os.path.join(os.path.normpath(ARMS[arm]), "SKILL.md"), "rb") as f:
            raw_skill = f.read()
        h = sha256_bytes(raw_skill)
        pin = TIGHTLOOP_PINNED_SHA256.get(arm)
        if pin and h != pin:
            if arm in a.arms:
                sys.exit(f"{arm} skill sha256 {h} != pinned {pin}: refusing to run")
        rel = os.path.relpath(os.path.join(os.path.normpath(ARMS[arm]), "SKILL.md"),
                              os.path.join(ROOT, "..")).replace(os.sep, "/")
        skills[arm] = (raw_skill.decode(), f"{arm}: {rel} ({len(raw_skill)} bytes, sha256 {h}) "
                       "from this harness commit")
        versions[arm] = f"{arm.split('-')[1]} sha256 {h[:12]}"
    folders = {arm: skill_folder(arm, ponytail_text) for arm in ARMS}
    env = {"os": f"{platform.system()} {platform.release()}",
           "machine": platform.machine(),
           "python": platform.python_version(),
           "cli": a.cli, "cli_version": cli_version(a.cli),
           "git": run(["git", "--version"]).stdout.strip(),
           "harness_commit": harness_commit(),
           "tools": tool_versions(),
           "task_start_commits": {t["name"]: t.get("start_commit", "n/a") for t in tasks},
           "arms": {k: v[1] for k, v in skills.items()},
           "skill_delivery": (("--append-system-prompt with the arm's SKILL.md text" if a.cli == "claude"
                               else "AGENTS.md in the task checkout")
                              + "; plus, same rule for every arm, the arm's skill folder copied "
                              "into the checkout before the session and git-excluded via "
                              ".git/info/exclude (never in the diff or graded): ponytail -> "
                              ".claude/skills/ponytail/SKILL.md; tightloop-v3 -> its folder "
                              "benchmark/arms/tightloop-v3/ at .claude/skills/tightloop/; "
                              "tightloop-v4 -> benchmark/arms/tightloop-v4/ (SKILL.md, gate.sh, "
                              "phases/) at .claude/skills/tightloop/; tightloop-v4a -> its folder benchmark/arms/tightloop-v4a/ "
                              "at .claude/skills/tightloop/; tightloop-v4b -> benchmark/arms/tightloop-v4b/ at the same path; "
                              "tightloop-v5 -> benchmark/arms/tightloop-v5/ (SKILL.md, look.py, gate.sh, phases/) "
                              "at the same path; tightloop-v5b -> benchmark/arms/tightloop-v5b/ at the same path; "
                              "no-skill -> nothing (no system-prompt "
                              "text, no files)"),
           "skill_folders": {arm: [{"path": r, "bytes": len(d), "sha256": sha256_bytes(d)}
                                   for r, (d, _) in sorted(f.items())]
                             for arm, f in folders.items()},
           "arm_versions": versions,
           "prompt": "task instruction with upstream PR refs like (#123) removed",
           "network": ("Claude Code built-in web tools denied with --disallowedTools "
                       + " ".join(DISALLOWED_TOOLS) + ". NOT network-isolated: the CLI "
                       "needs the model API, and its Bash tool (cargo, go, git, curl) "
                       "keeps network access." if a.cli == "claude" else
                       "no restriction applied (codex)"),
           "session_timeout_s": a.timeout, "grade_timeout_s": a.grade_timeout,
           "unmeasured_fields": (["tokens.total (claude -p result has no total_tokens)",
                                  "model (claude -p JSON has no top-level model; see "
                                  "model_from_modelUsage per row)"]
                                 if a.cli == "claude" else ["turns", "tool_calls", "model"]),
           "notes": ("tokens.cache = cache_read_input_tokens + cache_creation_input_tokens; "
                     "tokens.cache_read and tokens.cache_creation are the two parts. "
                     "claude runs with --output-format stream-json --verbose; tool_calls = "
                     "distinct tool_use ids in the event stream (exact count, subagents "
                     "included), tool_calls_main = those not inside a subagent"),
           "grading_rename_rule": ("after the session and before the hidden patch: a test function "
                                   "the agent ADDED (Rust `fn NAME(`, Go `func NAME(`) whose name equals "
                                   "a hidden test name is renamed NAME_agent; same rule on every arm; "
                                   "the raw diff is saved to diffs/ before the rename")}
    if a.wait_lock or a.overlap_cwd:
        env["overlap_rule"] = ("row overlap=overlapped if at any sample (start, about every 30 s, "
                               "end) the lock was held by another process or a process outside "
                               f"the session had its cwd under {a.overlap_cwd}"
                               + (f" and '{a.overlap_cmd}' in its command line" if a.overlap_cmd else "")
                               + "; else clean. "
                               f"lock wait scope: {a.lock_wait_scope}. Compare wall time only "
                               "within the same overlap tag.")
    if a.wait_lock:
        env["shared_machine"] = (f"wall times measured on a shared machine; another job holds "
                                 f"{a.wait_lock} while it runs. Each session starts only once "
                                 f"that lock is free (waited up to {a.wait_lock_max}s, not held); "
                                 "per row: loadavg_start, loadavg_end, lock_busy_during "
                                 "(sampled about every 30 s), lock_wait_seconds")
    if a.rotate:
        env["arm_order"] = ("rotated per repeat: shift (2*task_index + run_index) mod number_of_arms "
                            "(the pre-registered pass-3 shift rule); rows are appended to rows.jsonl "
                            "in execution order, so a row's position is its line number within its task")
    else:
        env["arm_order"] = "fixed ARMS order (no rotation)"
    with open(os.path.join(a.out, "environment.json"), "w") as f:
        json.dump(env, f, indent=2)
    rows = os.path.join(a.out, "rows.jsonl")
    models_seen = set()
    stopped = None
    with open(rows, "a") as out:
        arm_list = [x for x in ARMS if x in a.arms]
        for t_idx, task in enumerate(tasks):
            tid = task["name"]
            if a.rotate and len(arm_list) > 1:
                seq = [(arm, i) for i in range(a.runs)
                       for arm in (arm_list[(2 * t_idx + i) % len(arm_list):]
                                   + arm_list[:(2 * t_idx + i) % len(arm_list)])]
            else:
                seq = [(arm, i) for arm in arm_list for i in range(a.runs)]
            for arm, i in seq:
                skill, arm_note = skills[arm]
                if True:
                    if a.min_free_mib and free_mib(a.out) < a.min_free_mib:
                        stopped = (f"DISK STOP {free_mib(a.out)} MiB free before "
                                   f"{tid}/{arm}/run{i+1}")
                        break
                    tag = f"{tid}_{arm}_{i+1}"
                    k = 1
                    while any(os.path.exists(os.path.join(d, tag + s)) for d, s in
                              ((logs, ".agent.stdout"), (diffs, ".diff"))):
                        k += 1  # never overwrite an earlier attempt's files
                        tag = f"{tid}_{arm}_{i+1}_attempt{k}"
                    free_start = free_mib(a.out)
                    wt = prepare(task, a.cache)
                    installed = install_skill(folders[arm], wt)
                    lock_wait = 0.0
                    pause_wait = 0.0
                    if a.pause_file:
                        p0 = time.time()
                        while os.path.exists(a.pause_file):
                            time.sleep(30)
                        pause_wait = round(time.time() - p0, 1)
                    first_of_task = arm == [x for x in ARMS if x in a.arms][0] and i == 0
                    if a.wait_lock and (a.lock_wait_scope == "session" or first_of_task):
                        w0 = time.time()
                        while lock_busy(a.wait_lock) and time.time() - w0 < a.wait_lock_max:
                            time.sleep(5)
                        lock_wait = round(time.time() - w0, 1)
                    gate_killed = []
                    try:
                        prompt = strip_pr_refs(task["instruction"])
                        if task.get("kind") == "app" and task.get("spec"):
                            with open(os.path.join(ROOT, task["spec"])) as f:
                                prompt = f.read()
                        raw, m = launch(a.cli, prompt, skill, wt, a.timeout,
                                        os.path.join(logs, tag + ".agent"),
                                        watch_lock=a.wait_lock, watch_cwd=a.overlap_cwd,
                                        watch_cmd=a.overlap_cmd)
                        note = None
                        gate_killed = restore_gate_backup(wt)
                        diff_added, diff_deleted = save_diff(wt, os.path.join(diffs, tag + ".diff"))
                        renamed = []
                        reset = []
                        if m["timed_out"]:
                            result, diffstat = "timeout", "session timed out; grader not run"
                            note = f"session exceeded {a.timeout}s"
                        elif m["infra_error"]:
                            result, diffstat = "invalid", "grader not run"
                            note = m["infra_error"]
                        elif gate_killed:
                            result, diffstat = "invalid", "grader not run"
                            note = ("gate killed mid-revert: .git/tightloop-gate/ was left behind; "
                                    f"restored {gate_killed} before diffing, row not graded")
                        else:
                            if task.get("kind") != "app":
                                renamed = rename_colliding_tests(task, wt)
                            result, diffstat = grade(task, wt, a.grade_timeout,
                                                     os.path.join(logs, tag + ".grade"), reset)
                            if result == "timeout":
                                note = f"grader exceeded {a.grade_timeout}s"
                    finally:
                        shutil.rmtree(wt, ignore_errors=True)
                    if isinstance(m["model_from_modelUsage"], list):
                        models_seen.update(m["model_from_modelUsage"])
                    row = {"task": tid, "arm": arm, "run": i + 1,
                           "pass": a.pass_label, "arm_version": versions[arm],
                           "skill_files": installed,
                           "agent": m.pop("agent"), "model": m.pop("model"),
                           "model_from_modelUsage": m["model_from_modelUsage"],
                           "arm_note": arm_note,
                           "environment": env,
                           "start_commit": task.get("start_commit", "n/a"),
                           "prompt": prompt,
                           "tokens": {k: m[k] for k in ("input", "output", "cache", "cache_read",
                                                         "cache_creation", "total")},
                           "wall_seconds": m["wall_seconds"],
                           "turns": m["turns"], "tool_calls": m["tool_calls"],
                           "tool_calls_main": m["tool_calls_main"],
                           "tool_calls_by_name": m["tool_calls_by_name"],
                           "skills_listed": m["skills_listed"],
                           "diff": diffstat, "result": result, "note": note,
                           "loadavg_start": m["loadavg_start"], "loadavg_end": m["loadavg_end"],
                           "lock_busy_during": m["lock_busy_during"],
                           "overlap": m["overlap"], "overlap_samples": m["overlap_samples"],
                           "lock_samples": m["lock_samples"], "lock_wait_seconds": lock_wait,
                           "pause_wait_seconds": pause_wait,
                           "phase_reads": m["phase_reads"], "gate_runs": m["gate_runs"],
                           "gate_output_bytes": m["gate_output_bytes"],
                           "agent_diff_lines": diff_added + diff_deleted,
                           "agent_diff_added": diff_added, "agent_diff_deleted": diff_deleted,
                           "rename_applied": "yes" if renamed else "no",
                           "renamed_tests": sorted({r["from"] for r in renamed}),
                           "renamed_agent_tests": renamed,
                           "diff_file": os.path.join("diffs", tag + ".diff"),
                           "free_mib_start": free_start,
                           "logs": os.path.join("logs", tag + ".*"),
                           "hidden_patch_fallback": "yes" if reset else "no",
                           "reset_files": reset,
                           "status": "; ".join(
                               ["ok"]
                               + (["agent test renamed before grading (hidden-test name collision)"]
                                  if renamed else [])
                               + (["hidden patch did not apply to the agent's tree; its files were "
                                   "restored to the start commit before applying it"]
                                  if reset else []))}
                    if gate_killed:
                        row["status"] = "invalid-harness (gate killed mid-revert; files restored, not graded)"
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
