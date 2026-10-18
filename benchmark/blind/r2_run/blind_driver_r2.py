#!/usr/bin/env python3
# blind round 2 driver: 3 apps x 4 versions, one fresh claude session each, strictly sequential.
# Waits while the Kimo hold file exists, df < 3000 MiB, load/mem high, or a pass-3 session/build runs under /tmp/tlw-*.
import json, os, re, sys, time, shutil, subprocess, tempfile
TD = "/home/user/tab/tasks/a84b5a07-3830-42f7-8e27-78e0788c75e3"
SNAP = "/home/user/tab/work/tl_blind_r2"          # git-archive snapshot of tightloop main at the step-3 commit
OUT = "/home/user/tab/work/tl_blind_out/r2"        # raw builds by version name (NEVER under files/)
COSTDIR = "/home/user/tab/files/tl_blind/r2"       # COST.json/.md: outside any viewer folder
HOLD = "/home/user/tab/tasks/77f85275-5fad-4ce4-ad2e-269d3b04d7ec/hold"
sys.path.insert(0, SNAP + "/benchmark")
import runner as R
R.ARMS["tightloop-v4c"] = os.path.join(SNAP, "benchmark", "arms", "tightloop-v4c")
def cenv():
    d = json.load(open('/home/user/tab/.model-capability.json')); e = dict(os.environ)
    e['ANTHROPIC_BASE_URL'] = d['base_url'].rstrip('/') + '/anthropic'; e['ANTHROPIC_API_KEY'] = d['token']
    e['CLAUDE_CONFIG_DIR'] = '/home/user/tab/work/tl_tools/claude-config'
    h = '/home/user'; e['PATH'] = f"{h}/tl-npm/bin:{h}/go-dist/go/bin:{h}/.cargo/bin:" + e['PATH']; return e
os.environ.update(cenv())
_rl = R.run_logged
CUR = {"wt": None}
# Build isolation (Naman m:ad61cc34 pt 3): each session runs inside a bubblewrap mount namespace in which /home/user/tab
# (key, checker, specs repo, task logs, files), /tmp (other worktrees, the commit area), /home/user/.prime and /dev/shm are
# empty tmpfs; only the session's own fresh workspace and the claude config dir are mounted back in.
def bwrap_prefix(wt):
    return ["bwrap", "--dev-bind", "/", "/", "--tmpfs", "/home/user/tab", "--bind", "/home/user/tab/work/tl_tools", "/home/user/tab/work/tl_tools",
            "--tmpfs", "/home/user/.prime", "--tmpfs", "/dev/shm", "--tmpfs", "/tmp", "--bind", wt, wt,
            "--ro-bind", HOSTS, "/etc/hosts", "--chdir", wt, "--die-with-parent"]
HOSTS = TD + "/sandbox_hosts"   # /etc/hosts + GitHub hosts -> 0.0.0.0 (Naman m:ed447bea b); the model API host is untouched
def _nice_rl(cmd, *a, **k):
    pre = bwrap_prefix(CUR["wt"]) if CUR["wt"] and list(cmd)[:1] == ["claude"] else []
    return _rl(["nice", "-n", "15"] + pre + list(cmd), *a, **k)
R.run_logged = _nice_rl
PROBE = ["/home/user/tab/files/tl_blind/r2/KEY.json", "/home/user/tab/files/tl_blind/r2/KEY_v2.json", "/home/user/tab/work/tl_blind_r2/benchmark/blind/checks/check_app.py",
         "/tmp/tlb_push/benchmark/blind/checks/check_app.py", "/home/user/tab/work/tightloop_bench/benchmark/blind/checks/check_app.py",
         "/home/user/tab/tasks", "/home/user/tab/work/tl_blind_out"]
def isolation_check(wt):
    """Before each session: list the workspace, grep it for checker/key material, and probe from INSIDE the same sandbox that
    the key and every checker copy are absent. Returns a dict that goes into the row and the log."""
    files = sorted(os.path.relpath(os.path.join(dp, f), wt) for dp, dns, fs in os.walk(wt) for f in fs if "/.git/" not in "/" + os.path.relpath(os.path.join(dp, f), wt) + "/")
    g = subprocess.run(["grep", "-rIlE", "check_app|KEY\\.json|blind/checks|checks/reference|blind_r2|COST", wt, "--exclude-dir=.git"], capture_output=True, text=True).stdout.split()
    pr = subprocess.run(bwrap_prefix(wt) + ["bash", "-c", "for p in " + " ".join(PROBE) + "; do test -e $p && echo VISIBLE:$p; done; "
                        "for r in / " + wt + " /tmp /home/user/tab /home/user/tab/work/tl_tools /home/user/.prime /dev/shm; do find $r -xdev \\( -name check_app.py -o -name 'KEY*.json' -o -name 'blind_rows*' \\) 2>/dev/null; done | sort -u | head -20; "
                        "curl -sS -m 6 -o /dev/null https://raw.githubusercontent.com/ 2>/dev/null && echo VISIBLE:github-reachable"],
                        capture_output=True, text=True, timeout=120)
    vis = [l for l in pr.stdout.split("\n") if l.strip()]
    return {"workspace_files": files, "grep_hits": g, "visible_in_sandbox": vis, "ok": not g and not vis}
AUDIT = re.compile(r"check_app|KEY\.json|blind/checks|checks/reference|blind_rows|tl_blind|raw\.githubusercontent|github\.com/naman-sharma12345", re.I)
def audit(log_stdout):
    try: txt = open(log_stdout, errors="replace").read()
    except OSError: return {"error": "no log"}
    hits = [m.group(0) for m in AUDIT.finditer(txt)]
    return {"hits": len(hits), "terms": sorted(set(hits))}
def log(*a): print(time.strftime('%H:%M:%SZ', time.gmtime()), *a, flush=True)
def report(msg): subprocess.run(["node", "/home/user/tab/progress-cli.mjs", "report", msg], capture_output=True, timeout=60)
def df(): st = os.statvfs("/home/user"); return st.f_bavail * st.f_frsize // (1024*1024)
def busy():
    why = []
    if os.path.exists(HOLD): why.append("kimo-hold")
    la = os.getloadavg()[0]
    if la > 6: why.append(f"load {la:.1f}")
    ma = int([l for l in open("/proc/meminfo") if l.startswith("MemAvailable")][0].split()[1]) // 1024
    if ma < 1500: why.append(f"mem {ma}")
    for pid in os.listdir("/proc"):
        if not pid.isdigit(): continue
        try:
            cwd = os.readlink(f"/proc/{pid}/cwd"); cmd = open(f"/proc/{pid}/cmdline", "rb").read().replace(b"\0", b" ").decode(errors="replace")
        except OSError: continue
        if cwd.startswith("/tmp/tlw-"):
            if "claude" in cmd and " -p " in cmd: why.append("pass3-claude")
            elif cmd.split(" ")[0].split("/")[-1] in ("cargo", "go", "rustc"): why.append("pass3-build")
    if df() < 3000: why.append(f"disk {df()}")
    return sorted(set(why))
APPS = ["bookmarks", "expenses", "kanban"]
V = ["no-skill", "ponytail", "tightloop-v4", "tightloop-v4c"]
# Build order (Naman m:530473fd pt 4): drawn with secrets, committed as labels only (results/blind_r2_order.json) before build 1.
# Each label is resolved to its version from the sealed key v2 inside this process; logs and file names use the label.
import hashlib
KEYP2 = "/home/user/tab/files/tl_blind/r2/KEY_v2.json"; KEY2_SHA = "fd1d6896f82f74afb087dddbb69c9716ca2418c5fceba30b47cd5940a742b04c"
assert hashlib.sha256(open(KEYP2, "rb").read()).hexdigest() == KEY2_SHA, "KEY_v2.json changed - stop"
ORDER = json.load(open(SNAP + "/results/blind_r2_order.json"))["order"]
assert sorted(ORDER) == sorted(f"{a}-{l}" for a in APPS for l in "ABCD")
_K = json.load(open(KEYP2))["apps"]
PLAN = [(t.split("-")[0], _K[t.split("-")[0]][t.split("-")[1]], t.split("-")[1]) for t in ORDER]
del _K
USAGE_SOURCE = "claude CLI stream-json final result event (usage, num_turns) parsed by runner.launch; tool_calls = tool_use ids in the same log; wall = runner.launch clock; never the agent's own report"
pt_text, pt_note = R.ponytail_skill("/home/user/tab/work/tl_tools/tl-cache")
skills = {"no-skill": None, "ponytail": pt_text,
          "tightloop-v4": open(os.path.join(os.path.normpath(R.ARMS["tightloop-v4"]), "SKILL.md")).read(),
          "tightloop-v4c": open(os.path.join(R.ARMS["tightloop-v4c"], "SKILL.md")).read()}
rows_p = TD + "/blind_rows_r2.jsonl"
done = set()
if os.path.exists(rows_p):
    for l in open(rows_p): r = json.loads(l); done.add((r["app"], r["arm"]))
os.makedirs(TD + "/logs_r2", exist_ok=True); os.makedirs(COSTDIR, exist_ok=True)
log("plan (labels)", ORDER, "done", len(done))
for app, arm, lab in PLAN:
    tag = f"{app}-{lab}"
    if (app, arm) in done: continue
    t_wait = time.time(); last = None; disk_warned = False; clear_since = None
    while True:
        b = busy()
        if b:
            clear_since = None
            if b != last: log("waiting", tag, b); last = b
            if any(x.startswith("disk") for x in b) and not disk_warned:
                report(f"DISK STOP {df()} MiB before blind round-2 build {len(done)+1}/12; waiting, nothing deleted"); disk_warned = True
            time.sleep(20); continue
        if clear_since is None: clear_since = time.time(); log("clear; settling 60 s so a waiting pass-3 session shows itself first"); time.sleep(5); continue
        if time.time() - clear_since < 60: time.sleep(5); continue
        break
    waited = round(time.time() - t_wait, 1); d0 = df()
    voided = []
    for attempt in range(1, 4):
        wt = tempfile.mkdtemp(prefix="tlb-")
        subprocess.run(["git", "init", "-q"], cwd=wt)
        files = R.skill_folder(arm, pt_text)
        inst = R.install_skill(files, wt)
        prompt = open(f"{SNAP}/benchmark/blind/specs/r2/{app}.md").read()
        iso = isolation_check(wt)
        log("isolation", tag, "attempt", attempt, "workspace files", len(iso["workspace_files"]), iso["workspace_files"][:12], "grep hits", iso["grep_hits"], "visible in sandbox", iso["visible_in_sandbox"], "ok", iso["ok"])
        if not iso["ok"]:
            report(f"ISOLATION STOP before round-2 build {len(done)+1}/12: checker, key or GitHub reachable from the build sandbox; nothing launched"); log("ISOLATION STOP"); sys.exit(4)
        CUR["wt"] = wt
        log("start", tag, "attempt", attempt, "wt", wt, "waited", waited, "df", d0)
        t0 = time.time()
        raw, m = R.launch("claude", prompt, skills[arm], wt, 1800, f"{TD}/logs_r2/{tag}.agent", watch_cwd="/tmp/tlw-")
        CUR["wt"] = None
        if m.get("infra_error") or not isinstance(m.get("output"), (int, float)):
            err = open(f"{TD}/logs_r2/{tag}.agent.stderr", errors="replace").read()[-600:]
            log("INFRA STOP", tag, m.get("infra_error"), err)
            report(f"BUILD INFRA STOP at round-2 build {len(done)+1}/12: the session produced no usable result ({str(m.get('infra_error'))[:200]}); no row written, nothing retried; stderr tail in my task dir")
            shutil.rmtree(wt, ignore_errors=True); sys.exit(5)
        aud = audit(f"{TD}/logs_r2/{tag}.agent.stdout")
        log("audit", tag, "attempt", attempt, aud)
        if aud.get("hits", 0) == 0: break
        # HARD RULE (r2_INTEGRITY.md): any checker / key / repo-path hit in the transcript VOIDS the build and it is rerun
        vd = f"{OUT}/void/{tag}_attempt{attempt}"; os.makedirs(os.path.dirname(vd), exist_ok=True)
        shutil.copytree(wt, vd, ignore=shutil.ignore_patterns(".git", "node_modules")); shutil.rmtree(wt, ignore_errors=True)
        for ext in (".stdout", ".stderr"):
            try: os.rename(f"{TD}/logs_r2/{tag}.agent{ext}", f"{TD}/logs_r2/{tag}.attempt{attempt}.VOID{ext}")
            except OSError: pass
        voided.append({"attempt": attempt, "audit": aud, "usage": {k: m.get(k) for k in ("input", "output", "cache_read", "cache_creation", "wall_seconds")}})
        log("VOID", tag, "attempt", attempt, aud)
    else:
        report(f"VOID STOP at round-2 build {len(done)+1}/12: 3 attempts in a row hit checker/key/repo terms in the transcript; stopped"); sys.exit(6)
    dst = f"{OUT}/{app}/{lab}"
    if os.path.exists(dst): shutil.rmtree(dst)
    shutil.copytree(wt, dst, ignore=shutil.ignore_patterns(".git", "node_modules", "target"))
    shutil.rmtree(wt, ignore_errors=True)
    shot = f"{TD}/logs_r2/{tag}.png"; cj = f"{TD}/logs_r2/{tag}.check.json"
    cr = subprocess.run(["timeout", "-k", "5", "240", "python3", f"{SNAP}/benchmark/blind/checks/check_app.py", app, dst, shot, cj],
                        capture_output=True, text=True)
    try: chk = json.load(open(cj))
    except Exception: chk = {"passed": 0, "total": None, "error": (cr.stdout + cr.stderr)[-400:]}
    num = lambda k: m.get(k) if isinstance(m.get(k), (int, float)) else 0
    row = {"app": app, "arm": arm, "skill_files": inst, "prompt_sha": R.sha256_bytes(prompt.encode()),
           "input": m.get("input"), "output": m.get("output"), "cache_read": m.get("cache_read"), "cache_creation": m.get("cache_creation"),
           "in_out": num("input") + num("output"), "in_out_cache_read": num("input") + num("output") + num("cache_read"),
           "cost_weighted": round(num("input") + 5*num("output") + 0.1*num("cache_read") + 1.25*num("cache_creation"), 2),
           "usage_source": USAGE_SOURCE, "turns": m.get("turns"), "tool_calls": m.get("tool_calls"), "wall_seconds": m.get("wall_seconds"), "timed_out": m.get("timed_out"),
           "infra_error": m.get("infra_error"), "model": m.get("model_from_modelUsage"), "agent": m.get("agent"),
           "overlap": m.get("overlap"), "overlap_samples": m.get("overlap_samples"), "loadavg": [m.get("loadavg_start"), m.get("loadavg_end")],
           "waited_s": waited, "df_start": d0, "started": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(t0)),
           "files": sorted(os.path.relpath(os.path.join(dp, f), dst) for dp, _, fs in os.walk(dst) for f in fs),
           "isolation": {k: iso[k] for k in ("grep_hits", "visible_in_sandbox", "ok")}, "isolation_workspace_files": iso["workspace_files"], "audit": aud, "voided_attempts": voided,
           "checks_passed": chk.get("passed"), "checks_total": chk.get("total"), "drag_method": chk.get("drag_method"), "check_detail": chk}
    open(rows_p, "a").write(json.dumps(row) + "\n"); done.add((app, arm))
    subprocess.run(["python3", f"{SNAP}/benchmark/blind/cost_table.py", rows_p, f"{COSTDIR}/COST"], capture_output=True, timeout=60)
    log("row", tag, "in+out", row["in_out"], "cw", row["cost_weighted"], "turns", row["turns"], "wall", row["wall_seconds"],
        "checks", row["checks_passed"], "/", row["checks_total"], "overlap", row["overlap"])
log("ALL DONE")
