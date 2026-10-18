#!/usr/bin/env python3
# blind app bake-off driver: 3 apps x 3 arms, one fresh claude session each, sequential.
import json, os, sys, time, shutil, subprocess, tempfile
TD = "/home/user/tab/tasks/2a4ce3c5-0127-47bb-ac69-2a2747594489"
WT = "/home/user/tab/work/tl_blind"
OUT = "/home/user/tab/work/tl_blind_out"
HOLD = "/home/user/tab/tasks/77f85275-5fad-4ce4-ad2e-269d3b04d7ec/hold"
sys.path.insert(0, WT + "/benchmark")
import runner as R
def cenv():
    d = json.load(open('/home/user/tab/.model-capability.json')); e = dict(os.environ)
    e['ANTHROPIC_BASE_URL'] = d['base_url'].rstrip('/') + '/anthropic'; e['ANTHROPIC_API_KEY'] = d['token']
    e['CLAUDE_CONFIG_DIR'] = '/home/user/tab/work/tl_tools/claude-config'
    h = '/home/user'; e['PATH'] = f"{h}/tl-npm/bin:{h}/go-dist/go/bin:{h}/.cargo/bin:" + e['PATH']; return e
os.environ.update(cenv())
# Pally 22:36 IST: hold file no longer blocks; sessions run under nice -n 15
_rl = R.run_logged
def _nice_rl(cmd, *a, **k): return _rl(["nice", "-n", "15"] + list(cmd), *a, **k)
R.run_logged = _nice_rl
def log(*a): print(time.strftime('%H:%M:%SZ', time.gmtime()), *a, flush=True)
def report(msg): subprocess.run(["node", "/home/user/tab/progress-cli.mjs", "report", msg], capture_output=True, timeout=60)
def df(): st = os.statvfs("/home/user"); return st.f_bavail * st.f_frsize // (1024*1024)
def busy():
    why = []
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
    if df() < 1900: why.append(f"disk {df()}")
    return sorted(set(why))
PLAN = [("todo", "no-skill"), ("todo", "ponytail"), ("todo", "tightloop-v4"),
        ("notes", "ponytail"), ("notes", "tightloop-v4"), ("notes", "no-skill"),
        ("units", "tightloop-v4"), ("units", "no-skill"), ("units", "ponytail")]
pt_text, pt_note = R.ponytail_skill("/home/user/tab/work/tl_tools/tl-cache")
skills = {"no-skill": None, "ponytail": pt_text,
          "tightloop-v4": open(os.path.join(os.path.normpath(R.ARMS["tightloop-v4"]), "SKILL.md")).read()}
rows_p = TD + "/blind_rows.jsonl"
done = set()
if os.path.exists(rows_p):
    for l in open(rows_p): r = json.loads(l); done.add((r["app"], r["arm"]))
os.makedirs(TD + "/logs", exist_ok=True)
for app, arm in PLAN:
    if (app, arm) in done: continue
    t_wait = time.time(); last = None; disk_warned = False
    while True:
        b = busy()
        if not b: break
        if b != last: log("waiting", app, arm, b); last = b
        if any(x.startswith("disk") for x in b) and not disk_warned:
            report(f"DISK STOP {df()} MiB before blind build {len(done)+1}/9; waiting, nothing deleted"); disk_warned = True
        time.sleep(20)
    waited = round(time.time() - t_wait, 1)
    d0 = df()
    wt = tempfile.mkdtemp(prefix="tlb-")
    subprocess.run(["git", "init", "-q"], cwd=wt)
    files = R.skill_folder(arm if arm != "tightloop-v4" else "tightloop-v4", pt_text)
    inst = R.install_skill(files, wt)
    prompt = open(f"{WT}/benchmark/blind/specs/{app}.md").read()
    log("start", app, arm, "wt", wt, "waited", waited, "df", d0)
    t0 = time.time()
    raw, m = R.launch("claude", prompt, skills[arm], wt, 1200, f"{TD}/logs/{app}_{arm}.agent", watch_cwd="/tmp/tlw-")
    dst = f"{OUT}/{app}/{arm}"
    if os.path.exists(dst): shutil.rmtree(dst)
    shutil.copytree(wt, dst, ignore=shutil.ignore_patterns(".git", "node_modules", "target"))
    shutil.rmtree(wt, ignore_errors=True)
    shot = f"{TD}/logs/{app}_{arm}.png"; cj = f"{TD}/logs/{app}_{arm}.check.json"
    cr = subprocess.run(["timeout", "-k", "5", "120", "python3", f"{WT}/benchmark/blind/checks/check_app.py", app, dst, shot, cj],
                        capture_output=True, text=True)
    try: chk = json.load(open(cj))
    except Exception: chk = {"passed": 0, "total": None, "error": (cr.stdout + cr.stderr)[-400:]}
    num = lambda k: m.get(k) if isinstance(m.get(k), (int, float)) else 0
    row = {"app": app, "arm": arm, "skill_files": inst, "prompt_sha": R.sha256_bytes(prompt.encode()),
           "input": m.get("input"), "output": m.get("output"), "cache_read": m.get("cache_read"), "cache_creation": m.get("cache_creation"),
           "in_out": num("input") + num("output"), "in_out_cache_read": num("input") + num("output") + num("cache_read"),
           "cost_weighted": round(num("input") + 5*num("output") + 0.1*num("cache_read") + 1.25*num("cache_creation"), 2),
           "turns": m.get("turns"), "tool_calls": m.get("tool_calls"), "wall_seconds": m.get("wall_seconds"), "timed_out": m.get("timed_out"),
           "infra_error": m.get("infra_error"), "model": m.get("model_from_modelUsage"), "agent": m.get("agent"),
           "overlap": m.get("overlap"), "overlap_samples": m.get("overlap_samples"), "loadavg": [m.get("loadavg_start"), m.get("loadavg_end")],
           "waited_s": waited, "df_start": d0, "started": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(t0)),
           "files": sorted(os.path.relpath(os.path.join(dp, f), dst) for dp, _, fs in os.walk(dst) for f in fs),
           "checks_passed": chk.get("passed"), "checks_total": chk.get("total"), "check_detail": chk}
    open(rows_p, "a").write(json.dumps(row) + "\n"); done.add((app, arm))
    log("row", app, arm, "in+out", row["in_out"], "cw", row["cost_weighted"], "turns", row["turns"], "wall", row["wall_seconds"],
        "checks", row["checks_passed"], "/", row["checks_total"], row["overlap"])
log("ALL DONE")
