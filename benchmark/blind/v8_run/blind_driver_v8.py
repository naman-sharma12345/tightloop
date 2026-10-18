#!/usr/bin/env python3
# tightloop v8 blind driver (v8_PREREG.md): 9 builds (arm tightloop-v8), one fresh claude session each, strictly
# sequential. A copy of benchmark/blind/v7_run/blind_driver_v7.py (itself a copy of the v6c/v5c/r2 drivers) with ONLY these changes:
#  - paths (TD/SNAP/OUT/COSTDIR, START_OK under files/tl_blind/v8), the v8 key path added to the sandbox probe's watch list;
#  - the plan is the committed build-id order results/v8_order.json (9 builds); arm tightloop-v8;
#  - its own hold: the hold text must contain "v8" (written and removed by root; this driver never creates or deletes it);
#  - a running r2, v5c, v6c, v7, v4c-n3 or v8 driver (other than itself) counts as another worker (wait);
#  - HARD CUTOFF 2026-10-19T03:00:00Z: no build starts at or after it; the build in progress finishes; logged "cut to n"
#    (no v8 build starts at/after 03:00Z; one in progress at 03:15Z is the last);
#  - logs under TD/logs_v8, rows TD/blind_rows_v8.jsonl, per-build row also to COSTDIR/BUILD_RESULTS.tsv (same columns as v5c/v6c/v7).
# Unchanged from v7: runner.launch, skill delivery (skill folder in the workspace + --append-system-prompt), sandbox (sandbox_r2),
# nice -n 15, 1800 s timeout, transcript audit + VOID rule, one RETRY on a harness crash only, the checks/check_app.py call.
import json, os, re, sys, time, shutil, subprocess, tempfile, atexit
TD = "/home/user/tab/tasks/3ef36da5-5a67-404d-9950-6511d9a611fd"
SNAP = "/home/user/tab/work/tl_blind_v8"         # git-archive snapshot of the v8 prereg commit (holds both the v4c-n3 and v8 drivers) (SNAP/.snap_commit)
OUT = "/home/user/tab/work/tl_blind_out/v8"       # raw builds by build id (NEVER under files/)
COSTDIR = "/home/user/tab/files/tl_blind/v8"
HOLD = "/home/user/tab/tasks/77f85275-5fad-4ce4-ad2e-269d3b04d7ec/hold"   # written/removed by root only
BENCH = "/home/user/tab/work/tightloop_bench"
BUILD_LOG = TD + "/build_log.tsv"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SNAP + "/benchmark/blind/r2_run")
import sandbox_r2 as S
S.START_OK = COSTDIR + "/START_OK"
S.OLD_PROBE_PATHS = S.OLD_PROBE_PATHS + ["/home/user/tab/files/tl_blind/v8/KEY_v8.json", "/home/user/tab/files/tl_blind/v7/KEY_v7.json", "/home/user/tab/work/tl_blind_v4cn3/benchmark/blind/checks/check_app.py", "/home/user/tab/work/tl_blind_v8/benchmark/blind/checks/check_app.py", "/home/user/tab/files/tl_blind/v6c/KEY_v6c.json", "/home/user/tab/files/tl_blind/v5c/KEY_v5c.json", "/home/user/tab/work/tl_blind_v7/benchmark/blind/checks/check_app.py", "/home/user/tab/work/tl_blind_v6c/benchmark/blind/checks/check_app.py", "/home/user/tab/work/tl_blind_v5c/benchmark/blind/checks/check_app.py"]
S.NAME_RE = r"^(KEY(_v\w+)?\.json|mapping(_r\d+)?\.json|check_app\.py|blind_rows.*\.jsonl|COST|METRICS\.json|\.netrc|BUILD_RESULTS\.tsv)$"
def log(*a): print(time.strftime('%H:%M:%SZ', time.gmtime()), *a, flush=True)
def report(msg): subprocess.run(["node", "/home/user/tab/progress-cli.mjs", "report", msg], capture_output=True, timeout=60)
def df(): st = os.statvfs("/home/user"); return st.f_bavail * st.f_frsize // (1024*1024)
def own_hold():
    try: return "v8" in open(HOLD).read().lower()
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
        elif ("blind_driver_r2.py" in cmd or "blind_driver_v5c.py" in cmd or "blind_driver_v6c.py" in cmd or "blind_driver_v7.py" in cmd or "blind_driver_v4cn3.py" in cmd or "blind_driver_v8.py" in cmd) and a0.startswith("python") and "--guard-test" not in cmd: why.append(f"r2-driver:{pid}")
        elif re.search(r"pass[34][a-z_]*driver\.py", cmd) and not own_hold(): why.append(f"pass3-driver-unpaused:{pid}")
    return sorted(why)
def guard(snap=SNAP, start_ok=S.START_OK, me=os.getpid()):
    """Refuse unless (a) the snapshot this driver runs from contains the CHECKS commit, (b) START_OK exists, (c) no other worker runs."""
    why = []
    if os.path.realpath(HERE) != os.path.realpath(snap + "/benchmark/blind/v8_run"): why.append("not running from the snapshot")
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
    log("run end (" + why + "); the hold is root's to remove")
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
ORDER = json.load(open(SNAP + "/results/v8_order.json"))["order"]
assert sorted(ORDER) == sorted([f"v8-{a}-{i}" for a in APPS for i in (1, 2, 3)])
PLAN = [(b.split("-")[1], "tightloop-v8", b) for b in ORDER]
R.ARMS["tightloop-v8"] = os.path.join(SNAP, "benchmark", "arms", "tightloop-v8")
USAGE_SOURCE = "claude CLI stream-json final result event (usage, num_turns) parsed by runner.launch; tool_calls = tool_use ids in the same log; wall = runner.launch clock; never the agent's own report"
pt_text, pt_note = R.ponytail_skill("/home/user/tab/work/tl_tools/tl-cache")
skills = {"ponytail": pt_text, "tightloop-v8": open(os.path.join(R.ARMS["tightloop-v8"], "SKILL.md")).read()}
TSV = COSTDIR + "/BUILD_RESULTS.tsv"
def results_tsv(row, status):
    new = not os.path.exists(TSV)
    with open(TSV, "a") as f:
        if new: f.write("build\tstart_utc\tend_utc\tinput\toutput\tcache_read\tcache_write\tcost_weighted\tchecks_passed\tchecks_total\tstatus\tdf_mib_after\tusage_source\n")
        f.write("\t".join(str(x) for x in [row["build"], row["started"], row["ended"], row["input"], row["output"], row["cache_read"], row["cache_creation"],
                row["cost_weighted"], row["checks_passed"], row["checks_total"], status, df(),
                "harness: claude CLI stream-json final result event parsed by runner.launch (driver row), not the agent's own report"]) + "\n")
rows_p = TD + "/blind_rows_v8.jsonl"
done = set()
if os.path.exists(rows_p):
    for l in open(rows_p): r = json.loads(l); done.add(r["build"])
os.makedirs(TD + "/logs_v8", exist_ok=True); os.makedirs(COSTDIR, exist_ok=True)
log("plan (build ids)", ORDER, "done", len(done))
CUTOFF = 1792378800   # 2026-10-19T03:00:00Z
FIRST_START_DEADLINE = 1792378800   # 2026-10-19T03:00:00Z (same as CUTOFF)
def cut(where):
    log("CUTOFF 03:00Z reached", where, "- no further build starts; cut to", len(done), "of", len(PLAN), sorted(done))
    report(f"v8 CUTOFF 03:00Z: cut to {len(done)} of {len(PLAN)} builds ({where}); built: {','.join(sorted(done))}"); release_hold("cutoff")
for app, arm, bid in PLAN:
    tag = bid
    if bid in done: continue
    if time.time() >= CUTOFF: cut("before " + tag); sys.exit(0)
    if not done and time.time() >= FIRST_START_DEADLINE:
        log("START deadline 03:00Z passed before build 1; not started"); report("v8 NOT STARTED: 03:00Z start deadline passed before build 1"); release_hold("start deadline"); sys.exit(0)
    t_wait = time.time(); last = None; disk_warned = False; clear_since = None
    while True:
        b = busy()
        if b:
            clear_since = None
            if b != last: log("waiting", tag, b); last = b
            if any(x.startswith("disk") for x in b) and not disk_warned:
                report(f"DISK STOP {df()} MiB before blind v8 build {len(done)+1}/9; waiting, nothing deleted"); disk_warned = True
            time.sleep(20); continue
        if clear_since is None: clear_since = time.time(); log("clear; settling 60 s so a waiting pass-3 session shows itself first"); time.sleep(5); continue
        if time.time() - clear_since < 60: time.sleep(5); continue
        break
    if time.time() >= CUTOFF: cut("while waiting before " + tag); sys.exit(0)
    waited = round(time.time() - t_wait, 1); d0 = df()
    voided = []; infra_retried = False
    for attempt in range(1, 5):
        wt = tempfile.mkdtemp(prefix="tlb-"); cfg = tempfile.mkdtemp(prefix="tlb-cfg-")   # both fresh per build; cfg wiped after
        subprocess.run(["git", "init", "-q"], cwd=wt)
        files = R.skill_folder(arm, pt_text)
        inst = R.install_skill(files, wt)
        prompt = open(f"{SNAP}/benchmark/blind/specs/r2/{app}.md").read()
        iso = isolation_check(wt, cfg)
        log("isolation", tag, "attempt", attempt, "workspace files", len(iso["workspace_files"]), iso["workspace_files"][:12], "grep hits", iso["grep_hits"], "visible in sandbox", iso["visible_in_sandbox"], "failed probe checks", iso["probe_failed_checks"], "writable host paths", iso["writable"], "ok", iso["ok"])
        if not iso["ok"]:
            report(f"ISOLATION STOP before v8 build {len(done)+1}/9: the hardened probe failed ({','.join(iso['probe_failed_checks']) or 'workspace grep'}); nothing launched")
            log("ISOLATION STOP"); shutil.rmtree(cfg, ignore_errors=True); release_hold("run-ending ISOLATION STOP"); sys.exit(4)
        CUR["wt"] = wt; CUR["cfg"] = cfg
        log("start", tag, "attempt", attempt, "wt", wt, "waited", waited, "df", d0)
        t0 = time.time()
        raw, m = R.launch("claude", prompt, skills[arm], wt, 1800, f"{TD}/logs_v8/{tag}.agent", watch_cwd="/tmp/tlw-")
        t1 = time.time(); CUR["wt"] = None; CUR["cfg"] = None
        shutil.rmtree(cfg, ignore_errors=True)            # fresh CLI config per build, wiped after it (Naman m:5eb8c3c4 pt 5)
        if m.get("infra_error") or not isinstance(m.get("output"), (int, float)):
            err = open(f"{TD}/logs_v8/{tag}.agent.stderr", errors="replace").read()[-600:]
            log("INFRA", tag, m.get("infra_error"), err)
            shutil.rmtree(wt, ignore_errors=True)
            if not infra_retried:     # harness crash only (no usable result event): ONE retry, logged as RETRY
                infra_retried = True
                for ext in (".stdout", ".stderr"):
                    try: os.rename(f"{TD}/logs_v8/{tag}.agent{ext}", f"{TD}/logs_v8/{tag}.attempt{attempt}.RETRY{ext}")
                    except OSError: pass
                voided.append({"attempt": attempt, "retry_reason": "harness crash: " + str(m.get("infra_error"))[:200], "usage": {k: m.get(k) for k in ("input", "output", "cache_read", "cache_creation", "wall_seconds")}})
                tsv(f"{tag}(RETRY-harness-crash-attempt{attempt})", t0, t1); continue
            report(f"BUILD INFRA STOP at v8 build {len(done)+1}/9: second harness crash ({str(m.get('infra_error'))[:200]}); no row written")
            tsv(tag + "(INFRA-STOP)", t0, t1); release_hold("run-ending INFRA STOP"); sys.exit(5)
        aud = audit(f"{TD}/logs_v8/{tag}.agent.stdout")
        log("audit", tag, "attempt", attempt, aud)
        if aud.get("hits", 0) == 0: break
        # HARD RULE (r2_INTEGRITY.md): any checker / key / repo-path hit in the transcript VOIDS the build and it is rerun
        vd = f"{OUT}/void/{tag}_attempt{attempt}"; os.makedirs(os.path.dirname(vd), exist_ok=True)
        shutil.copytree(wt, vd, ignore=shutil.ignore_patterns(".git", "node_modules")); shutil.rmtree(wt, ignore_errors=True)
        for ext in (".stdout", ".stderr"):
            try: os.rename(f"{TD}/logs_v8/{tag}.agent{ext}", f"{TD}/logs_v8/{tag}.attempt{attempt}.VOID{ext}")
            except OSError: pass
        voided.append({"attempt": attempt, "audit": aud, "usage": {k: m.get(k) for k in ("input", "output", "cache_read", "cache_creation", "wall_seconds")}})
        tsv(f"{tag}(VOID-attempt{attempt})", t0, t1); log("VOID", tag, "attempt", attempt, aud)
    else:
        report(f"VOID STOP at v8 build {len(done)+1}/9: repeated attempts hit checker/key/repo terms in the transcript; stopped"); release_hold("run-ending VOID STOP"); sys.exit(6)
    dst = f"{OUT}/{bid}"
    if os.path.exists(dst): shutil.rmtree(dst)
    shutil.copytree(wt, dst, ignore=shutil.ignore_patterns(".git", "node_modules", "target"))
    shutil.rmtree(wt, ignore_errors=True)
    tsv(tag, t0, t1)
    shot = f"{TD}/logs_v8/{tag}.png"; cj = f"{TD}/logs_v8/{tag}.check.json"
    cr = subprocess.run(["timeout", "-k", "5", "240", "python3", f"{SNAP}/benchmark/blind/checks/check_app.py", app, dst, shot, cj],
                        capture_output=True, text=True)
    try: chk = json.load(open(cj))
    except Exception: chk = {"passed": 0, "total": None, "error": (cr.stdout + cr.stderr)[-400:]}
    num = lambda k: m.get(k) if isinstance(m.get(k), (int, float)) else 0
    row = {"build": bid, "app": app, "arm": arm, "skill_files": inst, "prompt_sha": R.sha256_bytes(prompt.encode()),
           "input": m.get("input"), "output": m.get("output"), "cache_read": m.get("cache_read"), "cache_creation": m.get("cache_creation"),
           "in_out": num("input") + num("output"), "in_out_cache_read": num("input") + num("output") + num("cache_read"),
           "cost_weighted": round(num("input") + 5*num("output") + 0.1*num("cache_read") + 1.25*num("cache_creation"), 2),
           "usage_source": USAGE_SOURCE, "turns": m.get("turns"), "tool_calls": m.get("tool_calls"), "wall_seconds": m.get("wall_seconds"), "timed_out": m.get("timed_out"),
           "infra_error": m.get("infra_error"), "model": m.get("model_from_modelUsage"), "agent": m.get("agent"),
           "overlap": m.get("overlap"), "overlap_samples": m.get("overlap_samples"), "loadavg": [m.get("loadavg_start"), m.get("loadavg_end")],
           "waited_s": waited, "df_start": d0, "started": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(t0)), "ended": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(t1)),
           "files": sorted(os.path.relpath(os.path.join(dp, f), dst) for dp, _, fs in os.walk(dst) for f in fs),
           "isolation": {k: iso[k] for k in ("grep_hits", "visible_in_sandbox", "probe_failed_checks", "writable", "ok")}, "isolation_workspace_files": iso["workspace_files"], "audit": aud, "voided_attempts": voided,
           "checks_passed": chk.get("passed"), "checks_total": chk.get("total"), "drag_method": chk.get("drag_method"), "check_detail": chk}
    open(rows_p, "a").write(json.dumps(row) + "\n"); done.add(bid)
    results_tsv(row, ("RETRIED-" if voided else "") + ("OK" if not m.get("timed_out") else "TIMEOUT"))
    log("row", tag, "in+out", row["in_out"], "cw", row["cost_weighted"], "turns", row["turns"], "wall", row["wall_seconds"],
        "checks", row["checks_passed"], "/", row["checks_total"], "overlap", row["overlap"])
log("ALL DONE"); release_hold("after build 9")
