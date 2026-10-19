#!/usr/bin/env python3
# tightloop v5 blind run driver: 3 apps x 3 runs x 5 arms = 45 scored sessions + 9 warm-ups, one session at a time.
# Mirrors benchmark/blind/r2_run/blind_driver_r2.py at 4a42a7c: the SAME hardened sandbox (r2_run/sandbox_r2.py prefix, own pid/net
# namespace, empty home, egress proxy to the model API only), the same pre-session isolation probe, the same post-session transcript
# audit (a hit VOIDS the build; the only allowed rerun), fresh CLI config per build wiped after it, and the same guard.
# Design: benchmark/design/tightloop-v5/DESIGN.md 4.1/4.10 (A1, A2). Block = one (app, run); a no-skill "reply OK" warm-up first
# (excluded from every median, counted in total cost), then the 5 arms in row (block index mod 5) of the cyclic 5x5 Latin square.
# Skill text reaches the CLI through --append-system-prompt-file in the build's own config dir (argv_v5.py), never argv.
# Session cap 600 s. A failed or bad scored build is never rerun or replaced.
# Runs ONLY from the snapshot SNAP of a commit that contains the v5 CHECKER commit, ONLY when START_OK exists (ROOT creates it),
# ONLY while the hold file is ours ("v5 builds by"), and ONLY when no other worker runs.
# Blinding (Naman m:d8220836 pt 3: the label->arm mapping lives only in the sealed key): logs, rows, build_log_v5.tsv and
# results_v5.tsv name a build by its Latin-square position (app-runN-pK), never by label. Each build is staged under
# OUT/.stage/<tag>; only when all 5 builds of a page exist are they moved, in label order A-E, into OUT/<app>/run<N>/<label>
# with a fixed mtime, so no file, log or timestamp pairs a position with a label. The mapping is read from the key in this
# process only to do that move; it is never written anywhere.
import json, os, re, sys, time, shutil, subprocess, tempfile, atexit, hashlib
TD = "/home/user/tab/tasks/c63a4d14-d00f-4e02-81d2-7cb6da909f27"
SNAP = "/home/user/tab/work/tl_blind_v5"            # git-archive snapshot (snap_v5.sh writes SNAP/.snap_commit)
OUT = "/home/user/tab/work/tl_blind_out/v5"         # raw builds by page/label (NEVER under files/)
FB = "/home/user/tab/files/tl_blind/v5"             # KEY.json (sealed), START_OK (root only), COST files
START_OK = FB + "/START_OK"
HOLD = "/home/user/tab/tasks/77f85275-5fad-4ce4-ad2e-269d3b04d7ec/hold"   # pauses pass 3; a hold whose text starts "v5 builds by" is OURS
BENCH = "/home/user/tab/work/tightloop_bench"       # clone used to check the snapshot's ancestry
BUILD_LOG = TD + "/build_log_v5.tsv"                # position tag, start, end, free disk after
RESULTS = TD + "/results_v5.tsv"                    # one line per finished build, written as it finishes (crash leaves partial results)
LOGS = TD + "/logs_v5"
CAP_S = 600
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "r2_run")); sys.path.insert(0, HERE)
import sandbox_r2 as S                               # the hardened sandbox, unchanged
# the probe's name/content/path lists gain the v5 material (module globals read by S.run_probe at call time; r2 files unchanged)
S.NAME_RE = r"^(KEY(_v\d+)?\.json|mapping(_r\d+|_v5)?\.json|check_app(_v5)?\.py|blind_rows.*\.jsonl|COST|METRICS\.json|\.netrc|START_OK)$"
S.CONTENT_RE = S.CONTENT_RE + r'|"pages"\s*:\s*\{\s*"(habits|recipes|pomodoro)/run|reference_v5|v5_INTEGRITY'
S.OLD_PROBE_PATHS = S.OLD_PROBE_PATHS + [FB + "/KEY.json", FB, SNAP + "/benchmark/blind/checks/check_app_v5.py",
                                         "/home/user/tab/work/tl_v5prep", OUT]
def log(*a): print(time.strftime('%H:%M:%SZ', time.gmtime()), *a, flush=True)
def report(msg): subprocess.run(["node", "/home/user/tab/progress-cli.mjs", "report", msg], capture_output=True, timeout=60)
def df(): st = os.statvfs("/home/user"); return st.f_bavail * st.f_frsize // (1024*1024)
def own_hold():
    try: return open(HOLD).read().startswith("v5 builds by")
    except OSError: return False
def other_workers(me=os.getpid()):
    """Any other agent session or build: a claude -p session, a runner.py, a cargo/rustc/go build, another blind driver
    (round 2 or v5). Idle pass-3/4 driver loops count only while no hold of ours pauses them."""
    why = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit() or int(pid) == me: continue
        try: cmd = open(f"/proc/{pid}/cmdline", "rb").read().replace(b"\0", b" ").decode(errors="replace")
        except OSError: continue
        a0 = cmd.split(" ")[0].split("/")[-1]
        if a0 == "claude" or (" claude " in f" {cmd} " and " -p " in cmd): why.append(f"agent-session:{pid}")
        elif "runner.py" in cmd and a0.startswith("python"): why.append(f"runner:{pid}")
        elif a0 in ("cargo", "rustc", "go"): why.append(f"build:{a0}:{pid}")
        elif re.search(r"blind_driver_(r2|v5)\.py", cmd) and a0.startswith("python") and "--guard-test" not in cmd: why.append(f"blind-driver:{pid}")
        elif re.search(r"pass[34][a-z_]*driver\.py", cmd) and not own_hold(): why.append(f"pass3-driver-unpaused:{pid}")
    return sorted(why)
def guard(snap=SNAP, start_ok=START_OK, me=os.getpid()):
    """Refuse unless (a) running from the snapshot, which contains the v5 CHECKER commit, (b) START_OK exists, (c) the hold is ours,
    (d) no other worker runs."""
    why = []
    if os.path.realpath(HERE) != os.path.realpath(snap + "/benchmark/blind/v5_run"): why.append("not running from the snapshot")
    try:
        sc = open(snap + "/.snap_commit").read().strip()
        r = subprocess.run(["git", "-C", BENCH, "log", "--format=%H %s", sc], capture_output=True, text=True, timeout=60)
        if r.returncode != 0 or not any(l.split(" ", 1)[1].startswith("tightloop v5 blind run: checker") for l in r.stdout.splitlines() if " " in l):
            why.append("snapshot does not contain the v5 checker commit")
    except OSError: why.append("snapshot has no .snap_commit")
    if not os.path.exists(start_ok): why.append("START_OK missing")
    if not own_hold(): why.append("hold file is not ours (root writes 'v5 builds by ...' to it with START_OK)")
    ow = other_workers(me)
    if ow: why.append("other workers running: " + ",".join(ow))
    return why
if "--guard-test" in sys.argv:          # refusal test: same guard, alternate snapshot / START_OK path given on the command line
    i = sys.argv.index("--guard-test"); why = guard(snap=sys.argv[i + 1], start_ok=sys.argv[i + 2])
    if why: log("REFUSED:", "; ".join(why)); sys.exit(7)
    log("guard would allow"); sys.exit(0)
_why = guard()
if _why:
    log("REFUSED:", "; ".join(_why))
    open(TD + "/driver_v5_refusals.log", "a").write(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()) + " REFUSED: " + "; ".join(_why) + "\n")
    sys.exit(7)
sys.path.insert(0, SNAP + "/benchmark")
import runner as R
APPS = ["habits", "recipes", "pomodoro"]; RUNS = [1, 2, 3]
ARMS5 = ["no-skill", "ponytail", "tightloop-v4", "tightloop-v5", "tightloop-v5b"]   # Latin-square base order
for a in ("tightloop-v5", "tightloop-v5b"):
    h = R.sha256_bytes(open(os.path.join(R.ARMS[a], "SKILL.md"), "rb").read())
    assert h == R.TIGHTLOOP_PINNED_SHA256[a], f"{a} SKILL.md is not the A2 text - stop"
KEYP = FB + "/KEY.json"; KEY_SHA = "43f5a85cc299abbf0f8a7000e1e5769d75a8eca30f1511ff0465cfa88fd29544"
assert hashlib.sha256(open(KEYP, "rb").read()).hexdigest() == KEY_SHA, "v5 KEY.json changed - stop"
_P = json.load(open(KEYP))["pages"]
LABEL = {(pg, arm): lab for pg, m in _P.items() for lab, arm in m.items()}   # in-process only; never logged
del _P
assert len(LABEL) == 45
_env = S.clean_env(); os.environ.clear(); os.environ.update(_env)     # allowlisted env only (values never logged)
SOCKD, _proxy = S.start_proxy(_env); atexit.register(S.stop_proxy, SOCKD, _proxy)
_rl = R.run_logged
CUR = {"wt": None, "cfg": None}
import argv_v5
def _nice_rl(cmd, *a, **k):
    pre = []
    if CUR["wt"] and list(cmd)[:1] == ["claude"]:
        pre = S.prefix(CUR["wt"], CUR["cfg"], SOCKD)
        cmd = argv_v5.sandbox_argv(cmd, CUR["cfg"], S.CFG_IN)   # skill text via a file in the build's own config dir, never argv
    return _rl(["nice", "-n", "15"] + pre + list(cmd), *a, **k)
R.run_logged = _nice_rl
LEAK = "check_app|KEY(_v\\d+)?\\.json|blind/checks|checks/reference|blind_r2|blind_v5|v5_INTEGRITY|benchmark/design|COST"
def isolation_check(wt, cfg):
    files = sorted(os.path.relpath(os.path.join(dp, f), wt) for dp, dns, fs in os.walk(wt) for f in fs if "/.git/" not in "/" + os.path.relpath(os.path.join(dp, f), wt) + "/")
    g = subprocess.run(["grep", "-rIlE", LEAK, wt, "--exclude-dir=.git"], capture_output=True, text=True).stdout.split()
    tok, sp = S.sentinel()
    try: rep = S.run_probe(wt, cfg, SOCKD, tok, env=_env)
    finally: sp.kill()
    fails = [k for k, v in rep.items() if isinstance(v, dict) and v.get("ok") is False]
    return {"workspace_files": files, "grep_hits": g, "probe_ok": rep.get("ok"), "probe_failed_checks": fails,
            "visible_in_sandbox": rep.get("scan", {}).get("name_hits", []) + rep.get("scan", {}).get("content_hits", []) + rep.get("old_probe_paths", {}).get("visible", []),
            "writable": rep.get("writable", {}).get("host_backed_rw"), "ok": not g and rep.get("ok") is True}
AUDIT = re.compile(r"check_app|KEY(_v\d+)?\.json|mapping_(r\d|v5)|blind/checks|checks/reference|blind_rows|tl_blind|v5_INTEGRITY|benchmark/design|raw\.githubusercontent|github\.com/naman-sharma12345", re.I)
def audit(log_stdout):
    try: txt = open(log_stdout, errors="replace").read()
    except OSError: return {"error": "no log"}
    hits = [m.group(0) for m in AUDIT.finditer(txt)]
    return {"hits": len(hits), "terms": sorted(set(hits))}
def release_hold(why):
    if own_hold(): os.remove(HOLD); log("hold file removed:", why)
def tsv(path, header, line):
    new = not os.path.exists(path)
    with open(path, "a") as f:
        if new: f.write(header + "\n")
        f.write(line + "\n")
def ts(t): return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(t))
def busy():
    why = []
    if os.path.exists(HOLD) and not own_hold(): why.append("foreign-hold")
    if not os.path.exists(HOLD): why.append("hold-gone")
    why += other_workers()
    la = os.getloadavg()[0]
    if la > 6: why.append(f"load {la:.1f}")
    ma = int([l for l in open("/proc/meminfo") if l.startswith("MemAvailable")][0].split()[1]) // 1024
    if ma < 1500: why.append(f"mem {ma}")
    if df() < 3000: why.append(f"disk {df()}")
    return sorted(set(why))
def wait_clear(tag):
    t_wait = time.time(); last = None; disk_warned = False; clear_since = None
    while True:
        b = busy()
        if b:
            clear_since = None
            if b != last: log("waiting", tag, b); last = b
            if any(x.startswith("disk") for x in b) and not disk_warned:
                report(f"DISK STOP {df()} MiB before v5 build {tag}; waiting, nothing deleted"); disk_warned = True
            time.sleep(20); continue
        if clear_since is None: clear_since = time.time(); log("clear; settling 30 s"); time.sleep(5); continue
        if time.time() - clear_since < 30: time.sleep(5); continue
        return round(time.time() - t_wait, 1)
num = lambda m, k: m.get(k) if isinstance(m.get(k), (int, float)) else 0
def thinking(stdout_path):
    """DESIGN 4.8: final result event usage.output_tokens_details.thinking_tokens, cross-checked against modelUsage[..].thinkingTokens."""
    t, mu = [], []
    try:
        for l in open(stdout_path, errors="replace"):
            if '"type":"result"' not in l.replace(" ", ""): continue
            ev = json.loads(l)
            if ev.get("type") != "result": continue
            t.append(((ev.get("usage") or {}).get("output_tokens_details") or {}).get("thinking_tokens"))
            mu.append(sum((v or {}).get("thinkingTokens", 0) or 0 for v in (ev.get("modelUsage") or {}).values()))
    except Exception as e: return {"thinking": None, "note": "parse error " + str(e)[:80]}
    if not t or any(x is None for x in t): return {"thinking": None, "note": "field absent"}
    T = sum(t)
    return {"thinking": T, "modelUsage_thinking": sum(mu), "match": T == sum(mu)}
USAGE_SOURCE = "claude CLI stream-json final result event (usage, num_turns) parsed by runner.launch; tool_calls = tool_use ids in the same log; wall = runner.launch clock; never the agent's own report"
pt_text, pt_note = R.ponytail_skill("/home/user/tab/work/tl_tools/tl-cache")
skills = {"no-skill": None, "ponytail": pt_text}
for a in ("tightloop-v4", "tightloop-v5", "tightloop-v5b"):
    skills[a] = open(os.path.join(os.path.normpath(R.ARMS[a]), "SKILL.md")).read()
rows_p = TD + "/blind_rows_v5.jsonl"; warm_p = TD + "/warmups_v5.jsonl"
done = set(); wdone = set()
if os.path.exists(rows_p):
    for l in open(rows_p): r = json.loads(l); done.add((r["page"], r["arm"]))
if os.path.exists(warm_p):
    for l in open(warm_p): wdone.add(json.loads(l)["page"])
os.makedirs(LOGS, exist_ok=True); os.makedirs(OUT, exist_ok=True)
BLOCKS = [(app, run) for run in RUNS for app in APPS]          # 9 blocks: run 1 of each app, then run 2, then run 3
log("plan: 9 blocks x (1 warm-up + 5 arms); done", len(done), "warm-ups done", len(wdone))
def session(tag, arm, prompt, cap):
    """One sandboxed session with a fresh workspace and a fresh config dir; returns (wt, inst, iso, raw, m, t0, t1) or exits on a STOP."""
    wt = tempfile.mkdtemp(prefix="tlb-"); cfg = tempfile.mkdtemp(prefix="tlb-cfg-")
    subprocess.run(["git", "init", "-q"], cwd=wt)
    inst = R.install_skill(R.skill_folder(arm, pt_text), wt)
    iso = isolation_check(wt, cfg)
    log("isolation", tag, "files", len(iso["workspace_files"]), "grep hits", iso["grep_hits"], "visible", iso["visible_in_sandbox"], "failed", iso["probe_failed_checks"], "ok", iso["ok"])
    if not iso["ok"]:
        report(f"ISOLATION STOP before v5 build {tag}: the hardened probe failed ({','.join(iso['probe_failed_checks']) or 'workspace grep'}); nothing launched")
        shutil.rmtree(cfg, ignore_errors=True); release_hold("run-ending ISOLATION STOP"); sys.exit(4)
    CUR["wt"] = wt; CUR["cfg"] = cfg
    t0 = time.time()
    raw, m = R.launch("claude", prompt, skills[arm], wt, cap, f"{LOGS}/{tag}.agent", watch_cwd="/tmp/tlw-")
    t1 = time.time(); CUR["wt"] = None; CUR["cfg"] = None
    shutil.rmtree(cfg, ignore_errors=True)            # fresh CLI config per build, wiped after it
    if m.get("infra_error") or not isinstance(m.get("output"), (int, float)):
        log("INFRA STOP", tag, m.get("infra_error"))
        report(f"V5 INFRA STOP at {tag}: the session produced no usable result ({str(m.get('infra_error'))[:200]}); nothing retried; stderr tail in the driver's task dir")
        shutil.rmtree(wt, ignore_errors=True); tsv(BUILD_LOG, "build\tstart_utc\tend_utc\tdf_mib_after", f"{tag}(INFRA-STOP)\t{ts(t0)}\t{ts(t1)}\t{df()}")
        release_hold("run-ending INFRA STOP"); sys.exit(5)
    return wt, inst, iso, raw, m, t0, t1
for bi, (app, run) in enumerate(BLOCKS):
    page = f"{app}/run{run}"
    order = [ARMS5[(bi + j) % 5] for j in range(5)]      # row (bi mod 5) of the cyclic Latin square
    prompt = open(f"{SNAP}/benchmark/blind/specs/v5/{app}.md").read()
    if page not in wdone and not all((page, a) in done for a in ARMS5):
        tag = f"{app}-run{run}-warmup"; waited = wait_clear(tag)
        wt, inst, iso, raw, m, t0, t1 = session(tag, "no-skill", "reply OK", 120)
        shutil.rmtree(wt, ignore_errors=True)
        w = {"page": page, "block": bi, "input": m.get("input"), "output": m.get("output"), "cache_read": m.get("cache_read"),
             "cache_creation": m.get("cache_creation"), "wall_seconds": m.get("wall_seconds"), "started": ts(t0), "waited_s": waited}
        open(warm_p, "a").write(json.dumps(w) + "\n"); wdone.add(page)
        tsv(BUILD_LOG, "build\tstart_utc\tend_utc\tdf_mib_after", f"{tag}\t{ts(t0)}\t{ts(t1)}\t{df()}")
        log("warm-up", tag, "in", w["input"], "out", w["output"], "cache_read", w["cache_read"])
    for k, arm in enumerate(order, 1):
        if (page, arm) in done: continue
        tag = f"{app}-run{run}-p{k}"
        waited = wait_clear(tag); d0 = df(); voided = []
        for attempt in range(1, 4):
            wt, inst, iso, raw, m, t0, t1 = session(tag, arm, prompt, CAP_S)
            aud = audit(f"{LOGS}/{tag}.agent.stdout"); log("audit", tag, "attempt", attempt, aud)
            if aud.get("hits", 0) == 0: break
            # HARD RULE (r2_INTEGRITY.md, DESIGN 4.10): a checker / key / repo-path hit in the transcript VOIDS the build; it is rerun
            vd = f"{OUT}/void/{tag}_attempt{attempt}"; os.makedirs(os.path.dirname(vd), exist_ok=True)
            shutil.copytree(wt, vd, ignore=shutil.ignore_patterns(".git", "node_modules")); shutil.rmtree(wt, ignore_errors=True)
            for ext in (".stdout", ".stderr"):
                try: os.rename(f"{LOGS}/{tag}.agent{ext}", f"{LOGS}/{tag}.attempt{attempt}.VOID{ext}")
                except OSError: pass
            voided.append({"attempt": attempt, "audit": aud, "usage": {x: m.get(x) for x in ("input", "output", "cache_read", "cache_creation", "wall_seconds")}})
            tsv(BUILD_LOG, "build\tstart_utc\tend_utc\tdf_mib_after", f"{tag}(VOID-attempt{attempt})\t{ts(t0)}\t{ts(t1)}\t{df()}")
        else:
            report(f"VOID STOP at v5 build {tag}: 3 attempts in a row hit checker/key/repo terms in the transcript; stopped")
            release_hold("run-ending VOID STOP"); sys.exit(6)
        dst = f"{OUT}/.stage/{tag}"
        if os.path.exists(dst): shutil.rmtree(dst)
        shutil.copytree(wt, dst, ignore=shutil.ignore_patterns(".git", "node_modules", "target"))
        shutil.rmtree(wt, ignore_errors=True)
        tsv(BUILD_LOG, "build\tstart_utc\tend_utc\tdf_mib_after", f"{tag}\t{ts(t0)}\t{ts(t1)}\t{df()}")
        shot = f"{LOGS}/{tag}.png"; cj = f"{LOGS}/{tag}.check.json"
        cr = subprocess.run(["timeout", "-k", "5", "240", "nice", "-n", "15", "python3", f"{SNAP}/benchmark/blind/checks/check_app_v5.py", app, dst, shot, cj],
                            capture_output=True, text=True)
        try: chk = json.load(open(cj))
        except Exception: chk = {"passed": 0, "total": None, "error": (cr.stdout + cr.stderr)[-400:]}
        th = thinking(f"{LOGS}/{tag}.agent.stdout")
        row = {"page": page, "app": app, "run": run, "block": bi, "position": k, "arm": arm, "skill_files": inst,
               "prompt_sha": R.sha256_bytes(prompt.encode()),
               "input": m.get("input"), "output": m.get("output"), "cache_read": m.get("cache_read"), "cache_creation": m.get("cache_creation"),
               "in_out": num(m, "input") + num(m, "output"), "in_out_cache_read": num(m, "input") + num(m, "output") + num(m, "cache_read"),
               "cost_weighted": round(num(m, "input") + 5*num(m, "output") + 0.1*num(m, "cache_read") + 1.25*num(m, "cache_creation"), 2),
               "thinking": th, "cold": (m.get("cache_read") == 0), "usage_source": USAGE_SOURCE,
               "turns": m.get("turns"), "tool_calls": m.get("tool_calls"), "wall_seconds": m.get("wall_seconds"), "timed_out": m.get("timed_out"),
               "infra_error": m.get("infra_error"), "model": m.get("model_from_modelUsage"), "agent": m.get("agent"),
               "overlap": m.get("overlap"), "overlap_samples": m.get("overlap_samples"), "loadavg": [m.get("loadavg_start"), m.get("loadavg_end")],
               "waited_s": waited, "df_start": d0, "started": ts(t0),
               "files": sorted(os.path.relpath(os.path.join(dp, f), dst) for dp, _, fs in os.walk(dst) for f in fs),
               "isolation": {x: iso[x] for x in ("grep_hits", "visible_in_sandbox", "probe_failed_checks", "writable", "ok")}, "audit": aud, "voided_attempts": voided,
               "checks_passed": chk.get("passed"), "checks_total": chk.get("total"), "check_detail": chk}
        open(rows_p, "a").write(json.dumps(row) + "\n"); done.add((page, arm))
        # Naman m:98bbae98 pt 1: one line per build as it finishes (position tag, never the label)
        tsv(RESULTS, "build\tstart_utc\tend_utc\tin_out\tin_out_cache_read\tcost_weighted\tthinking\twall_s\tchecks\ttimed_out",
            f"{tag}\t{ts(t0)}\t{ts(t1)}\t{row['in_out']}\t{row['in_out_cache_read']}\t{row['cost_weighted']}\t{th.get('thinking')}\t{row['wall_seconds']}\t{row['checks_passed']}/{row['checks_total']}\t{row['timed_out']}")
        log("row", tag, "in+out", row["in_out"], "cw", row["cost_weighted"], "thinking", th.get("thinking"), "wall", row["wall_seconds"],
            "checks", row["checks_passed"], "/", row["checks_total"], "overlap", row["overlap"])
    # page complete: move its 5 staged builds into label folders in label order, fixed mtime (no position<->label trace)
    if all((page, a) in done for a in ARMS5) and not os.path.isdir(f"{OUT}/{app}/run{run}/E"):
        for lab in "ABCDE":
            k = 1 + order.index([a for a in ARMS5 if LABEL[(page, a)] == lab][0])
            src = f"{OUT}/.stage/{app}-run{run}-p{k}"; dst = f"{OUT}/{app}/run{run}/{lab}"
            os.makedirs(os.path.dirname(dst), exist_ok=True); os.rename(src, dst)
            for dp, dns, fns in os.walk(dst):
                for n in dns + fns: os.utime(os.path.join(dp, n), (1792324800, 1792324800))
            os.utime(dst, (1792324800, 1792324800))
        log("page", page, "moved to label folders")
shutil.rmtree(f"{OUT}/.stage", ignore_errors=True) if os.path.isdir(f"{OUT}/.stage") and not os.listdir(f"{OUT}/.stage") else None
lg = subprocess.run(["python3", f"{SNAP}/benchmark/blind/leakgrep_r2.py", OUT], capture_output=True, text=True, timeout=600)
open(TD + "/leakgrep_v5_raw.txt", "w").write(lg.stdout[-20000:] + lg.stderr[-2000:])
log("ALL DONE: 45 scored + 9 warm-ups; raw leak grep (before strip/pack):", (lg.stdout.strip().splitlines() or ["?"])[-1])
release_hold("after the last v5 build")
