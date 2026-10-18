#!/usr/bin/env python3
# blind round 2 driver: 3 apps x 4 versions, one fresh claude session each, strictly sequential.
# Runs ONLY from the snapshot (SNAP) of a commit that contains the CHECKS commit, ONLY when START_OK exists (created by root alone),
# and ONLY when no other worker runs (guard below; Naman m:b3c5c470 pt 4, m:5eb8c3c4 pt 6). Before each build it waits while
# df < 3000 MiB, load/mem is high, a foreign hold file exists, or any other agent session / build runs on the box.
import json, os, re, sys, time, shutil, subprocess, tempfile, atexit
TD = "/home/user/tab/tasks/a84b5a07-3830-42f7-8e27-78e0788c75e3"
SNAP = "/home/user/tab/work/tl_blind_r2"          # git-archive snapshot of tightloop main (snap_r2.sh writes SNAP/.snap_commit)
OUT = "/home/user/tab/work/tl_blind_out/r2"        # raw builds by label (NEVER under files/)
COSTDIR = "/home/user/tab/files/tl_blind/r2"       # COST.json/.md: outside any viewer folder
HOLD = "/home/user/tab/tasks/77f85275-5fad-4ce4-ad2e-269d3b04d7ec/hold"   # pauses pass 3; a hold whose text starts "r2 builds by" is OURS
BENCH = "/home/user/tab/work/tightloop_bench"       # clone used to check the snapshot's ancestry
BUILD_LOG = TD + "/build_log.tsv"                   # Naman m:f4cffa5e pt 5: label, start, end, free disk after
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sandbox_r2 as S                               # the hardened sandbox (one prefix for builds and for the probe)
def log(*a): print(time.strftime('%H:%M:%SZ', time.gmtime()), *a, flush=True)
def report(msg): subprocess.run(["node", "/home/user/tab/progress-cli.mjs", "report", msg], capture_output=True, timeout=60)
def df(): st = os.statvfs("/home/user"); return st.f_bavail * st.f_frsize // (1024*1024)
def own_hold():
    try: return open(HOLD).read().startswith("r2 builds by")
    except OSError: return False
def other_workers(me=os.getpid()):
    """Any other agent session or build on the box: an agent CLI session (claude -p), a pass-3/4 runner.py, a cargo/rustc/go
    build, another round-2 driver. The idle pass-3 driver loops count only while no hold of ours pauses them."""
    why = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit() or int(pid) == me: continue
        try: cmd = open(f"/proc/{pid}/cmdline", "rb").read().replace(b"\0", b" ").decode(errors="replace")
        except OSError: continue
        a0 = cmd.split(" ")[0].split("/")[-1]
        if a0 == "claude" or (" claude " in f" {cmd} " and " -p " in cmd): why.append(f"agent-session:{pid}")
        elif "runner.py" in cmd and a0.startswith("python"): why.append(f"runner:{pid}")
        elif a0 in ("cargo", "rustc", "go"): why.append(f"build:{a0}:{pid}")
        elif "blind_driver_r2.py" in cmd and a0.startswith("python") and "--guard-test" not in cmd: why.append(f"r2-driver:{pid}")
        elif re.search(r"pass[34][a-z_]*driver\.py", cmd) and not own_hold(): why.append(f"pass3-driver-unpaused:{pid}")
    return sorted(why)
def guard(snap=SNAP, start_ok=S.START_OK, me=os.getpid()):
    """Refuse unless (a) the snapshot this driver runs from contains the CHECKS commit, (b) START_OK exists, (c) no other worker runs."""
    why = []
    if os.path.realpath(HERE) != os.path.realpath(snap + "/benchmark/blind/r2_run"): why.append("not running from the snapshot")
    try:
        sc = open(snap + "/.snap_commit").read().strip()
        r = subprocess.run(["git", "-C", BENCH, "log", "--format=%H %s", sc], capture_output=True, text=True, timeout=60)
        if r.returncode != 0 or not any(l.split(" ", 1)[1].startswith("blind round 2 CHECKS") for l in r.stdout.splitlines() if " " in l):
            why.append("snapshot does not contain the CHECKS commit")
    except OSError: why.append("snapshot has no .snap_commit")
    if not os.path.exists(start_ok): why.append("START_OK missing")
    ow = other_workers(me)
    if ow: why.append("other workers running: " + ",".join(ow))
    return why
if "--guard-test" in sys.argv:          # refusal test: same guard, alternate snapshot / START_OK path given on the command line
    i = sys.argv.index("--guard-test"); why = guard(snap=sys.argv[i + 1], start_ok=sys.argv[i + 2])
    if why: log("REFUSED:", "; ".join(why)); sys.exit(7)
    log("guard would allow"); sys.exit(0)
_why = guard()
if _why:
    log("REFUSED:", "; ".join(_why)); sys.exit(7)
sys.path.insert(0, SNAP + "/benchmark")
import runner as R
R.ARMS["tightloop-v4c"] = os.path.join(SNAP, "benchmark", "arms", "tightloop-v4c")
_env = S.clean_env(); os.environ.clear(); os.environ.update(_env)     # allowlisted env only (values never logged)
SOCKD, _proxy = S.start_proxy(_env); atexit.register(S.stop_proxy, SOCKD, _proxy)
_rl = R.run_logged
CUR = {"wt": None, "cfg": None}
def _nice_rl(cmd, *a, **k):
    pre = S.prefix(CUR["wt"], CUR["cfg"], SOCKD) if CUR["wt"] and list(cmd)[:1] == ["claude"] else []
    return _rl(["nice", "-n", "15"] + pre + list(cmd), *a, **k)
R.run_logged = _nice_rl
def isolation_check(wt, cfg):
    """Before each session: list the workspace, grep it for checker/key material, and run the full hardened probe
    (sandbox_r2.PROBE_CODE) in the exact build invocation with this build's own workspace and config dir."""
    files = sorted(os.path.relpath(os.path.join(dp, f), wt) for dp, dns, fs in os.walk(wt) for f in fs if "/.git/" not in "/" + os.path.relpath(os.path.join(dp, f), wt) + "/")
    g = subprocess.run(["grep", "-rIlE", "check_app|KEY\\.json|blind/checks|checks/reference|blind_r2|COST", wt, "--exclude-dir=.git"], capture_output=True, text=True).stdout.split()
    tok, sp = S.sentinel()
    try: rep = S.run_probe(wt, cfg, SOCKD, tok, env=_env)
    finally: sp.kill()
    fails = [k for k, v in rep.items() if isinstance(v, dict) and v.get("ok") is False]
    return {"workspace_files": files, "grep_hits": g, "probe_ok": rep.get("ok"), "probe_failed_checks": fails,
            "visible_in_sandbox": rep.get("scan", {}).get("name_hits", []) + rep.get("scan", {}).get("content_hits", []) + rep.get("old_probe_paths", {}).get("visible", []),
            "writable": rep.get("writable", {}).get("host_backed_rw"), "ok": not g and rep.get("ok") is True}
AUDIT = re.compile(r"check_app|KEY(_v\d+)?\.json|mapping_r\d|blind/checks|checks/reference|blind_rows|tl_blind|raw\.githubusercontent|github\.com/naman-sharma12345", re.I)
def audit(log_stdout):
    try: txt = open(log_stdout, errors="replace").read()
    except OSError: return {"error": "no log"}
    hits = [m.group(0) for m in AUDIT.finditer(txt)]
    return {"hits": len(hits), "terms": sorted(set(hits))}
def release_hold(why):
    """Our hold pauses pass 3; it goes after build 12 or on a run-ending STOP (root steer 19:35Z)."""
    if own_hold():
        os.remove(HOLD); log("hold file removed:", why)
def tsv(label, t0, t1):
    new = not os.path.exists(BUILD_LOG)
    with open(BUILD_LOG, "a") as f:
        if new: f.write("build_label\tstart_utc\tend_utc\tdf_mib_after\n")
        f.write(f"{label}\t{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(t0))}\t{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(t1))}\t{df()}\n")
def busy():
    why = []
    if os.path.exists(HOLD) and not own_hold(): why.append("foreign-hold")
    why += other_workers()
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
# Each label is resolved to its version from the sealed key v4 inside this process; logs and file names use the label.
import hashlib
KEYP4 = "/home/user/tab/files/tl_blind/r2/KEY_v4.json"; KEY4_SHA = "e765297c4a34e6908638bcc4348b78b76a2eadf05760da4756b82127e8f40d71"   # v1 VOID, v2 BURNED, v3 VOID-UNUSED (r2_INTEGRITY.md)
assert hashlib.sha256(open(KEYP4, "rb").read()).hexdigest() == KEY4_SHA, "KEY_v4.json changed - stop"
ORDER = json.load(open(SNAP + "/results/blind_r2_order.json"))["order"]
assert sorted(ORDER) == sorted(f"{a}-{l}" for a in APPS for l in "ABCD")
_K = json.load(open(KEYP4))["apps"]
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
        wt = tempfile.mkdtemp(prefix="tlb-"); cfg = tempfile.mkdtemp(prefix="tlb-cfg-")   # both fresh per build; cfg wiped after
        subprocess.run(["git", "init", "-q"], cwd=wt)
        files = R.skill_folder(arm, pt_text)
        inst = R.install_skill(files, wt)
        prompt = open(f"{SNAP}/benchmark/blind/specs/r2/{app}.md").read()
        iso = isolation_check(wt, cfg)
        log("isolation", tag, "attempt", attempt, "workspace files", len(iso["workspace_files"]), iso["workspace_files"][:12], "grep hits", iso["grep_hits"], "visible in sandbox", iso["visible_in_sandbox"], "failed probe checks", iso["probe_failed_checks"], "writable host paths", iso["writable"], "ok", iso["ok"])
        if not iso["ok"]:
            report(f"ISOLATION STOP before round-2 build {len(done)+1}/12: the hardened probe failed ({','.join(iso['probe_failed_checks']) or 'workspace grep'}); nothing launched")
            log("ISOLATION STOP"); shutil.rmtree(cfg, ignore_errors=True); release_hold("run-ending ISOLATION STOP"); sys.exit(4)
        CUR["wt"] = wt; CUR["cfg"] = cfg
        log("start", tag, "attempt", attempt, "wt", wt, "waited", waited, "df", d0)
        t0 = time.time()
        raw, m = R.launch("claude", prompt, skills[arm], wt, 1800, f"{TD}/logs_r2/{tag}.agent", watch_cwd="/tmp/tlw-")
        t1 = time.time(); CUR["wt"] = None; CUR["cfg"] = None
        shutil.rmtree(cfg, ignore_errors=True)            # fresh CLI config per build, wiped after it (Naman m:5eb8c3c4 pt 5)
        if m.get("infra_error") or not isinstance(m.get("output"), (int, float)):
            err = open(f"{TD}/logs_r2/{tag}.agent.stderr", errors="replace").read()[-600:]
            log("INFRA STOP", tag, m.get("infra_error"), err)
            report(f"BUILD INFRA STOP at round-2 build {len(done)+1}/12: the session produced no usable result ({str(m.get('infra_error'))[:200]}); no row written, nothing retried; stderr tail in my task dir")
            shutil.rmtree(wt, ignore_errors=True); tsv(tag + "(INFRA-STOP)", t0, t1); release_hold("run-ending INFRA STOP"); sys.exit(5)
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
        tsv(f"{tag}(VOID-attempt{attempt})", t0, t1); log("VOID", tag, "attempt", attempt, aud)
    else:
        report(f"VOID STOP at round-2 build {len(done)+1}/12: 3 attempts in a row hit checker/key/repo terms in the transcript; stopped"); release_hold("run-ending VOID STOP"); sys.exit(6)
    dst = f"{OUT}/{app}/{lab}"
    if os.path.exists(dst): shutil.rmtree(dst)
    shutil.copytree(wt, dst, ignore=shutil.ignore_patterns(".git", "node_modules", "target"))
    shutil.rmtree(wt, ignore_errors=True)
    tsv(tag, t0, t1)
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
           "isolation": {k: iso[k] for k in ("grep_hits", "visible_in_sandbox", "probe_failed_checks", "writable", "ok")}, "isolation_workspace_files": iso["workspace_files"], "audit": aud, "voided_attempts": voided,
           "checks_passed": chk.get("passed"), "checks_total": chk.get("total"), "drag_method": chk.get("drag_method"), "check_detail": chk}
    open(rows_p, "a").write(json.dumps(row) + "\n"); done.add((app, arm))
    subprocess.run(["python3", f"{SNAP}/benchmark/blind/cost_table.py", rows_p, f"{COSTDIR}/COST"], capture_output=True, timeout=60)
    log("row", tag, "in+out", row["in_out"], "cw", row["cost_weighted"], "turns", row["turns"], "wall", row["wall_seconds"],
        "checks", row["checks_passed"], "/", row["checks_total"], "overlap", row["overlap"])
log("ALL DONE"); release_hold("after build 12")
