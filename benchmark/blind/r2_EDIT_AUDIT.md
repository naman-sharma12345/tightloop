# Round 2: build-script edit audit (Naman m:f4cffa5e pt 3, m:b3c5c470)

Every change to the round-2 build driver and pack script since the saved originals, diffed line by line and marked WIRING
(paths, labels, logging, recorded fields, comments: no effect on what a build sees or on what is packed) or BEHAVIOUR
(changes what a build sees, the order, the isolation, what is stripped or what stops the run). BEHAVIOUR hunks are for
re-checking by someone other than the worker (root). Originals: the files a84b5a07 left, saved by 14334bcb at 19:07Z as
`*.orig_a84b5a07` (sha256 below). Line numbers are old-file -> new-file of each stage.

original blind_driver_r2.py.orig_a84b5a07 sha256 `f6316b4804dbf40c86aafe0efb0fe42dcbdb6875988f5fe8f07d83d8e7519526`
original pack_r2.py.orig_a84b5a07 sha256 `bc43bd767d4941525e0df1f563587fe92b40aaddbc9491614078deeda3a76bbf`

## benchmark/blind/r2_run/blind_driver_r2.py
### Stage 1: saved original (a84b5a07, 19:07Z) -> b55917c. The 12:37 IST (19:07Z) edits are marked [12:37]; the other hunks were made 19:08-19:15Z for the pre-build commit.  (17 hunks)
#### S1-1 BEHAVIOUR [12:37]  old 33-33 -> new 33-33: in-sandbox probe also tests the KEY_v2 path
```diff
-PROBE = ["/home/user/tab/files/tl_blind/r2/KEY.json", "/home/user/tab/work/tl_blind_r2/benchmark/blind/checks/check_app.py",
+PROBE = ["/home/user/tab/files/tl_blind/r2/KEY.json", "/home/user/tab/files/tl_blind/r2/KEY_v2.json", "/home/user/tab/work/tl_blind_r2/benchmark/blind/checks/check_app.py",
```
#### S1-2 BEHAVIOUR [12:37]  old 42-42 -> new 42-42: probe's find matches KEY*.json, not only KEY.json
```diff
-                        "find / -xdev \\( -name check_app.py -o -name KEY.json -o -name 'blind_rows*' \\) 2>/dev/null | head -20; "
+                        "find / -xdev \\( -name check_app.py -o -name 'KEY*.json' -o -name 'blind_rows*' \\) 2>/dev/null | head -20; "
```
#### S1-3 BEHAVIOUR  old 75-75 -> new 75-85: build ORDER from the committed random order file; labels resolved from key v2 inside the driver; usage-source text
```diff
-PLAN = [(a, V[(i + k) % 4]) for i, a in enumerate(APPS) for k in range(4)]   # rotated start per app
+# Build order (Naman m:530473fd pt 4): drawn with secrets, committed as labels only (results/blind_r2_order.json) before build 1.
+# Each label is resolved to its version from the sealed key v2 inside this process; logs and file names use the label.
+import hashlib
+KEYP2 = "/home/user/tab/files/tl_blind/r2/KEY_v2.json"; KEY2_SHA = "fd1d6896f82f74afb087dddbb69c9716ca2418c5fceba30b47cd5940a742b04c"
+assert hashlib.sha256(open(KEYP2, "rb").read()).hexdigest() == KEY2_SHA, "KEY_v2.json changed - stop"
+ORDER = json.load(open(SNAP + "/results/blind_r2_order.json"))["order"]
+assert sorted(ORDER) == sorted(f"{a}-{l}" for a in APPS for l in "ABCD")
+_K = json.load(open(KEYP2))["apps"]
+PLAN = [(t.split("-")[0], _K[t.split("-")[0]][t.split("-")[1]], t.split("-")[1]) for t in ORDER]
+del _K
+USAGE_SOURCE = "claude CLI stream-json final result event (usage, num_turns) parsed by runner.launch; tool_calls = tool_use ids in the same log; wall = runner.launch clock; never the agent's own report"
```
#### S1-4 WIRING  old 85-86 -> new 95-97: 
```diff
-log("plan", PLAN, "done", sorted(done))
-for app, arm in PLAN:
+log("plan (labels)", ORDER, "done", len(done))
+for app, arm, lab in PLAN:
+    tag = f"{app}-{lab}"
```
#### S1-5 WIRING  old 93-93 -> new 104-104: 
```diff
-            if b != last: log("waiting", app, arm, b); last = b
+            if b != last: log("waiting", tag, b); last = b
```
#### S1-6 WIRING  old 109-109 -> new 120-120: 
```diff
-        log("isolation", app, arm, "attempt", attempt, "workspace files", len(iso["workspace_files"]), iso["workspace_files"][:12], "grep hits", iso["grep_hits"], "visible in sandbox", iso["visible_in_sandbox"], "ok", iso["ok"])
+        log("isolation", tag, "attempt", attempt, "workspace files", len(iso["workspace_files"]), iso["workspace_files"][:12], "grep hits", iso["grep_hits"], "visible in sandbox", iso["visible_in_sandbox"], "ok", iso["ok"])
```
#### S1-7 WIRING  old 113-113 -> new 124-124: 
```diff
-        log("start", app, arm, "attempt", attempt, "wt", wt, "waited", waited, "df", d0)
+        log("start", tag, "attempt", attempt, "wt", wt, "waited", waited, "df", d0)
```
#### S1-8 WIRING  old 115-115 -> new 126-126: 
```diff
-        raw, m = R.launch("claude", prompt, skills[arm], wt, 1800, f"{TD}/logs_r2/{app}_{arm}.agent", watch_cwd="/tmp/tlw-")
+        raw, m = R.launch("claude", prompt, skills[arm], wt, 1800, f"{TD}/logs_r2/{tag}.agent", watch_cwd="/tmp/tlw-")
```
#### S1-9 WIRING  old 118-119 -> new 129-130: 
```diff
-            err = open(f"{TD}/logs_r2/{app}_{arm}.agent.stderr", errors="replace").read()[-600:]
-            log("INFRA STOP", app, arm, m.get("infra_error"), err)
+            err = open(f"{TD}/logs_r2/{tag}.agent.stderr", errors="replace").read()[-600:]
+            log("INFRA STOP", tag, m.get("infra_error"), err)
```
#### S1-10 WIRING  old 122-123 -> new 133-134: 
```diff
-        aud = audit(f"{TD}/logs_r2/{app}_{arm}.agent.stdout")
-        log("audit", app, arm, "attempt", attempt, aud)
+        aud = audit(f"{TD}/logs_r2/{tag}.agent.stdout")
+        log("audit", tag, "attempt", attempt, aud)
```
#### S1-11 WIRING  old 126-126 -> new 137-137: 
```diff
-        vd = f"{OUT}/void/{app}_{arm}_attempt{attempt}"; os.makedirs(os.path.dirname(vd), exist_ok=True)
+        vd = f"{OUT}/void/{tag}_attempt{attempt}"; os.makedirs(os.path.dirname(vd), exist_ok=True)
```
#### S1-12 WIRING  old 129-129 -> new 140-140: 
```diff
-            try: os.rename(f"{TD}/logs_r2/{app}_{arm}.agent{ext}", f"{TD}/logs_r2/{app}_{arm}.attempt{attempt}.VOID{ext}")
+            try: os.rename(f"{TD}/logs_r2/{tag}.agent{ext}", f"{TD}/logs_r2/{tag}.attempt{attempt}.VOID{ext}")
```
#### S1-13 WIRING  old 132-132 -> new 143-143: 
```diff
-        log("VOID", app, arm, "attempt", attempt, aud)
+        log("VOID", tag, "attempt", attempt, aud)
```
#### S1-14 WIRING  old 135-135 -> new 146-146: raw build stored under its label instead of its version name
```diff
-    dst = f"{OUT}/{app}/{arm}"
+    dst = f"{OUT}/{app}/{lab}"
```
#### S1-15 WIRING  old 139-139 -> new 150-150: 
```diff
-    shot = f"{TD}/logs_r2/{app}_{arm}.png"; cj = f"{TD}/logs_r2/{app}_{arm}.check.json"
+    shot = f"{TD}/logs_r2/{tag}.png"; cj = f"{TD}/logs_r2/{tag}.check.json"
```
#### S1-16 WIRING  old 149-149 -> new 160-160: row records the usage source
```diff
-           "turns": m.get("turns"), "tool_calls": m.get("tool_calls"), "wall_seconds": m.get("wall_seconds"), "timed_out": m.get("timed_out"),
+           "usage_source": USAGE_SOURCE, "turns": m.get("turns"), "tool_calls": m.get("tool_calls"), "wall_seconds": m.get("wall_seconds"), "timed_out": m.get("timed_out"),
```
#### S1-17 WIRING  old 158-158 -> new 169-169: 
```diff
-    log("row", app, arm, "in+out", row["in_out"], "cw", row["cost_weighted"], "turns", row["turns"], "wall", row["wall_seconds"],
+    log("row", tag, "in+out", row["in_out"], "cw", row["cost_weighted"], "turns", row["turns"], "wall", row["wall_seconds"],
```
### Stage 2: b55917c -> b0130d7 (the probe fix).  (1 hunks)
#### S2-1 BEHAVIOUR  old 42-42 -> new 42-42: probe runs find over each mount root (old find / -xdev skipped tmpfs mounts and missed a planted KEY_v2.json)
```diff
-                        "find / -xdev \\( -name check_app.py -o -name 'KEY*.json' -o -name 'blind_rows*' \\) 2>/dev/null | head -20; "
+                        "for r in / " + wt + " /tmp /home/user/tab /home/user/tab/work/tl_tools /home/user/.prime /dev/shm; do find $r -xdev \\( -name check_app.py -o -name 'KEY*.json' -o -name 'blind_rows*' \\) 2>/dev/null; done | sort -u | head -20; "
```
### Stage 3: b0130d7 -> this CHECKS commit (hardened sandbox, guard, key v4, build log).  (23 hunks)
#### S3-1 WIRING  old 3-4 -> new 3-6: header comment
```diff
-# Waits while the Kimo hold file exists, df < 3000 MiB, load/mem high, or a pass-3 session/build runs under /tmp/tlw-*.
-import json, os, re, sys, time, shutil, subprocess, tempfile
+# Runs ONLY from the snapshot (SNAP) of a commit that contains the CHECKS commit, ONLY when START_OK exists (created by root alone),
+# and ONLY when no other worker runs (guard below; Naman m:b3c5c470 pt 4, m:5eb8c3c4 pt 6). Before each build it waits while
+# df < 3000 MiB, load/mem is high, a foreign hold file exists, or any other agent session / build runs on the box.
+import json, os, re, sys, time, shutil, subprocess, tempfile, atexit
```
#### S3-2 WIRING  old 6-7 -> new 8-9: comments
```diff
-SNAP = "/home/user/tab/work/tl_blind_r2"          # git-archive snapshot of tightloop main at the step-3 commit
-OUT = "/home/user/tab/work/tl_blind_out/r2"        # raw builds by version name (NEVER under files/)
+SNAP = "/home/user/tab/work/tl_blind_r2"          # git-archive snapshot of tightloop main (snap_r2.sh writes SNAP/.snap_commit)
+OUT = "/home/user/tab/work/tl_blind_out/r2"        # raw builds by label (NEVER under files/)
```
#### S3-3 BEHAVIOUR  old 9-9 -> new 11-58: own-hold rule, other_workers(), guard() (snapshot has CHECKS commit + START_OK + no other worker; REFUSED + exit 7), --guard-test, sandbox import
```diff
-HOLD = "/home/user/tab/tasks/77f85275-5fad-4ce4-ad2e-269d3b04d7ec/hold"
+HOLD = "/home/user/tab/tasks/77f85275-5fad-4ce4-ad2e-269d3b04d7ec/hold"   # pauses pass 3; a hold whose text starts "r2 builds by" is OURS
+BENCH = "/home/user/tab/work/tightloop_bench"       # clone used to check the snapshot's ancestry
+BUILD_LOG = TD + "/build_log.tsv"                   # Naman m:f4cffa5e pt 5: label, start, end, free disk after
+HERE = os.path.dirname(os.path.abspath(__file__))
+sys.path.insert(0, HERE)
+import sandbox_r2 as S                               # the hardened sandbox (one prefix for builds and for the probe)
+def log(*a): print(time.strftime('%H:%M:%SZ', time.gmtime()), *a, flush=True)
+def report(msg): subprocess.run(["node", "/home/user/tab/progress-cli.mjs", "report", msg], capture_output=True, timeout=60)
+def df(): st = os.statvfs("/home/user"); return st.f_bavail * st.f_frsize // (1024*1024)
+def own_hold():
+    try: return open(HOLD).read().startswith("r2 builds by")
+    except OSError: return False
+def other_workers(me=os.getpid()):
+    """Any other agent session or build on the box: an agent CLI session (claude -p), a pass-3/4 runner.py, a cargo/rustc/go
+    build, another round-2 driver. The idle pass-3 driver loops count only while no hold of ours pauses them."""
+    why = []
+    for pid in os.listdir("/proc"):
+        if not pid.isdigit() or int(pid) == me: continue
+        try: cmd = open(f"/proc/{pid}/cmdline", "rb").read().replace(b"\0", b" ").decode(errors="replace")
+        except OSError: continue
+        a0 = cmd.split(" ")[0].split("/")[-1]
+        if a0 == "claude" or (" claude " in f" {cmd} " and " -p " in cmd): why.append(f"agent-session:{pid}")
+        elif "runner.py" in cmd and a0.startswith("python"): why.append(f"runner:{pid}")
+        elif a0 in ("cargo", "rustc", "go"): why.append(f"build:{a0}:{pid}")
+        elif "blind_driver_r2.py" in cmd and a0.startswith("python") and "--guard-test" not in cmd: why.append(f"r2-driver:{pid}")
+        elif re.search(r"pass[34][a-z_]*driver\.py", cmd) and not own_hold(): why.append(f"pass3-driver-unpaused:{pid}")
+    return sorted(why)
+def guard(snap=SNAP, start_ok=S.START_OK, me=os.getpid()):
+    """Refuse unless (a) the snapshot this driver runs from contains the CHECKS commit, (b) START_OK exists, (c) no other worker runs."""
+    why = []
+    if os.path.realpath(HERE) != os.path.realpath(snap + "/benchmark/blind/r2_run"): why.append("not running from the snapshot")
+    try:
+        sc = open(snap + "/.snap_commit").read().strip()
+        r = subprocess.run(["git", "-C", BENCH, "log", "--format=%H %s", sc], capture_output=True, text=True, timeout=60)
+        if r.returncode != 0 or not any(l.split(" ", 1)[1].startswith("blind round 2 CHECKS") for l in r.stdout.splitlines() if " " in l):
+            why.append("snapshot does not contain the CHECKS commit")
+    except OSError: why.append("snapshot has no .snap_commit")
+    if not os.path.exists(start_ok): why.append("START_OK missing")
+    ow = other_workers(me)
+    if ow: why.append("other workers running: " + ",".join(ow))
+    return why
+if "--guard-test" in sys.argv:          # refusal test: same guard, alternate snapshot / START_OK path given on the command line
+    i = sys.argv.index("--guard-test"); why = guard(snap=sys.argv[i + 1], start_ok=sys.argv[i + 2])
+    if why: log("REFUSED:", "; ".join(why)); sys.exit(7)
+    log("guard would allow"); sys.exit(0)
+_why = guard()
+if _why:
+    log("REFUSED:", "; ".join(_why)); sys.exit(7)
```
#### S3-4 BEHAVIOUR  old 13-18 -> new 62-63: environment cut to an allowlist (sandbox_r2.clean_env); own egress proxy started
```diff
-def cenv():
-    d = json.load(open('/home/user/tab/.model-capability.json')); e = dict(os.environ)
-    e['ANTHROPIC_BASE_URL'] = d['base_url'].rstrip('/') + '/anthropic'; e['ANTHROPIC_API_KEY'] = d['token']
-    e['CLAUDE_CONFIG_DIR'] = '/home/user/tab/work/tl_tools/claude-config'
-    h = '/home/user'; e['PATH'] = f"{h}/tl-npm/bin:{h}/go-dist/go/bin:{h}/.cargo/bin:" + e['PATH']; return e
-os.environ.update(cenv())
+_env = S.clean_env(); os.environ.clear(); os.environ.update(_env)     # allowlisted env only (values never logged)
+SOCKD, _proxy = S.start_proxy(_env); atexit.register(S.stop_proxy, SOCKD, _proxy)
```
#### S3-5 BEHAVIOUR  old 20-28 -> new 65-65: old bwrap_prefix removed; CUR carries the per-build config dir
```diff
-CUR = {"wt": None}
-# Build isolation (Naman m:ad61cc34 pt 3): each session runs inside a bubblewrap mount namespace in which /home/user/tab
-# (key, checker, specs repo, task logs, files), /tmp (other worktrees, the commit area), /home/user/.prime and /dev/shm are
-# empty tmpfs; only the session's own fresh workspace and the claude config dir are mounted back in.
-def bwrap_prefix(wt):
-    return ["bwrap", "--dev-bind", "/", "/", "--tmpfs", "/home/user/tab", "--bind", "/home/user/tab/work/tl_tools", "/home/user/tab/work/tl_tools",
-            "--tmpfs", "/home/user/.prime", "--tmpfs", "/dev/shm", "--tmpfs", "/tmp", "--bind", wt, wt,
-            "--ro-bind", HOSTS, "/etc/hosts", "--chdir", wt, "--die-with-parent"]
-HOSTS = TD + "/sandbox_hosts"   # /etc/hosts + GitHub hosts -> 0.0.0.0 (Naman m:ed447bea b); the model API host is untouched
+CUR = {"wt": None, "cfg": None}
```
#### S3-6 BEHAVIOUR  old 30-30 -> new 67-67: every build runs under the hardened sandbox_r2.prefix
```diff
-    pre = bwrap_prefix(CUR["wt"]) if CUR["wt"] and list(cmd)[:1] == ["claude"] else []
+    pre = S.prefix(CUR["wt"], CUR["cfg"], SOCKD) if CUR["wt"] and list(cmd)[:1] == ["claude"] else []
```
#### S3-7 BEHAVIOUR  old 33-38 -> new 70-72: old probe paths replaced by isolation_check(wt, cfg)
```diff
-PROBE = ["/home/user/tab/files/tl_blind/r2/KEY.json", "/home/user/tab/files/tl_blind/r2/KEY_v2.json", "/home/user/tab/work/tl_blind_r2/benchmark/blind/checks/check_app.py",
-         "/tmp/tlb_push/benchmark/blind/checks/check_app.py", "/home/user/tab/work/tightloop_bench/benchmark/blind/checks/check_app.py",
-         "/home/user/tab/tasks", "/home/user/tab/work/tl_blind_out"]
-def isolation_check(wt):
-    """Before each session: list the workspace, grep it for checker/key material, and probe from INSIDE the same sandbox that
-    the key and every checker copy are absent. Returns a dict that goes into the row and the log."""
+def isolation_check(wt, cfg):
+    """Before each session: list the workspace, grep it for checker/key material, and run the full hardened probe
+    (sandbox_r2.PROBE_CODE) in the exact build invocation with this build's own workspace and config dir."""
```
#### S3-8 BEHAVIOUR  old 41-47 -> new 75-82: isolation check = workspace grep + full hardened probe (sentinel host process) in the exact build invocation; transcript AUDIT also matches KEY_vN.json and mapping_rN
```diff
-    pr = subprocess.run(bwrap_prefix(wt) + ["bash", "-c", "for p in " + " ".join(PROBE) + "; do test -e $p && echo VISIBLE:$p; done; "
-                        "for r in / " + wt + " /tmp /home/user/tab /home/user/tab/work/tl_tools /home/user/.prime /dev/shm; do find $r -xdev \\( -name check_app.py -o -name 'KEY*.json' -o -name 'blind_rows*' \\) 2>/dev/null; done | sort -u | head -20; "
-                        "curl -sS -m 6 -o /dev/null https://raw.githubusercontent.com/ 2>/dev/null && echo VISIBLE:github-reachable"],
-                        capture_output=True, text=True, timeout=120)
-    vis = [l for l in pr.stdout.split("\n") if l.strip()]
-    return {"workspace_files": files, "grep_hits": g, "visible_in_sandbox": vis, "ok": not g and not vis}
-AUDIT = re.compile(r"check_app|KEY\.json|blind/checks|checks/reference|blind_rows|tl_blind|raw\.githubusercontent|github\.com/naman-sharma12345", re.I)
+    tok, sp = S.sentinel()
+    try: rep = S.run_probe(wt, cfg, SOCKD, tok, env=_env)
+    finally: sp.kill()
+    fails = [k for k, v in rep.items() if isinstance(v, dict) and v.get("ok") is False]
+    return {"workspace_files": files, "grep_hits": g, "probe_ok": rep.get("ok"), "probe_failed_checks": fails,
+            "visible_in_sandbox": rep.get("scan", {}).get("name_hits", []) + rep.get("scan", {}).get("content_hits", []) + rep.get("old_probe_paths", {}).get("visible", []),
+            "writable": rep.get("writable", {}).get("host_backed_rw"), "ok": not g and rep.get("ok") is True}
+AUDIT = re.compile(r"check_app|KEY(_v\d+)?\.json|mapping_r\d|blind/checks|checks/reference|blind_rows|tl_blind|raw\.githubusercontent|github\.com/naman-sharma12345", re.I)
```
#### S3-9 BEHAVIOUR  old 53-55 -> new 88-96: release_hold() + build_log.tsv writer
```diff
-def log(*a): print(time.strftime('%H:%M:%SZ', time.gmtime()), *a, flush=True)
-def report(msg): subprocess.run(["node", "/home/user/tab/progress-cli.mjs", "report", msg], capture_output=True, timeout=60)
-def df(): st = os.statvfs("/home/user"); return st.f_bavail * st.f_frsize // (1024*1024)
+def release_hold(why):
+    """Our hold pauses pass 3; it goes after build 12 or on a run-ending STOP (root steer 19:35Z)."""
+    if own_hold():
+        os.remove(HOLD); log("hold file removed:", why)
+def tsv(label, t0, t1):
+    new = not os.path.exists(BUILD_LOG)
+    with open(BUILD_LOG, "a") as f:
+        if new: f.write("build_label\tstart_utc\tend_utc\tdf_mib_after\n")
+        f.write(f"{label}\t{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(t0))}\t{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(t1))}\t{df()}\n")
```
#### S3-10 BEHAVIOUR  old 58-58 -> new 99-100: busy(): a foreign hold or any other worker (agent session, runner, cargo/rustc/go, other driver) blocks the next build; our own hold does not
```diff
-    if os.path.exists(HOLD): why.append("kimo-hold")
+    if os.path.exists(HOLD) and not own_hold(): why.append("foreign-hold")
+    why += other_workers()
```
#### S3-11 WIRING  old 76-76 -> new 118-118: comment v2->v4
```diff
-# Each label is resolved to its version from the sealed key v2 inside this process; logs and file names use the label.
+# Each label is resolved to its version from the sealed key v4 inside this process; logs and file names use the label.
```
#### S3-12 WIRING  old 78-79 -> new 120-121: key v4 path + sha
```diff
-KEYP2 = "/home/user/tab/files/tl_blind/r2/KEY_v2.json"; KEY2_SHA = "fd1d6896f82f74afb087dddbb69c9716ca2418c5fceba30b47cd5940a742b04c"
-assert hashlib.sha256(open(KEYP2, "rb").read()).hexdigest() == KEY2_SHA, "KEY_v2.json changed - stop"
+KEYP4 = "/home/user/tab/files/tl_blind/r2/KEY_v4.json"; KEY4_SHA = "e765297c4a34e6908638bcc4348b78b76a2eadf05760da4756b82127e8f40d71"   # v1 VOID, v2 BURNED, v3 VOID-UNUSED (r2_INTEGRITY.md)
+assert hashlib.sha256(open(KEYP4, "rb").read()).hexdigest() == KEY4_SHA, "KEY_v4.json changed - stop"
```
#### S3-13 WIRING  old 82-82 -> new 124-124: key v4 path
```diff
-_K = json.load(open(KEYP2))["apps"]
+_K = json.load(open(KEYP4))["apps"]
```
#### S3-14 BEHAVIOUR  old 114-114 -> new 156-156: fresh CLI config dir per build
```diff
-        wt = tempfile.mkdtemp(prefix="tlb-")
+        wt = tempfile.mkdtemp(prefix="tlb-"); cfg = tempfile.mkdtemp(prefix="tlb-cfg-")   # both fresh per build; cfg wiped after
```
#### S3-15 BEHAVIOUR  old 119-120 -> new 161-162: probe gets the build config dir
```diff
-        iso = isolation_check(wt)
-        log("isolation", tag, "attempt", attempt, "workspace files", len(iso["workspace_files"]), iso["workspace_files"][:12], "grep hits", iso["grep_hits"], "visible in sandbox", iso["visible_in_sandbox"], "ok", iso["ok"])
+        iso = isolation_check(wt, cfg)
+        log("isolation", tag, "attempt", attempt, "workspace files", len(iso["workspace_files"]), iso["workspace_files"][:12], "grep hits", iso["grep_hits"], "visible in sandbox", iso["visible_in_sandbox"], "failed probe checks", iso["probe_failed_checks"], "writable host paths", iso["writable"], "ok", iso["ok"])
```
#### S3-16 BEHAVIOUR  old 122-123 -> new 164-166: ISOLATION STOP names the failed checks; wipes cfg; releases hold (run-ending STOP)
```diff
-            report(f"ISOLATION STOP before round-2 build {len(done)+1}/12: checker, key or GitHub reachable from the build sandbox; nothing launched"); log("ISOLATION STOP"); sys.exit(4)
-        CUR["wt"] = wt
+            report(f"ISOLATION STOP before round-2 build {len(done)+1}/12: the hardened probe failed ({','.join(iso['probe_failed_checks']) or 'workspace grep'}); nothing launched")
+            log("ISOLATION STOP"); shutil.rmtree(cfg, ignore_errors=True); release_hold("run-ending ISOLATION STOP"); sys.exit(4)
+        CUR["wt"] = wt; CUR["cfg"] = cfg
```
#### S3-17 BEHAVIOUR  old 127-127 -> new 170-171: config dir wiped right after each build
```diff
-        CUR["wt"] = None
+        t1 = time.time(); CUR["wt"] = None; CUR["cfg"] = None
+        shutil.rmtree(cfg, ignore_errors=True)            # fresh CLI config per build, wiped after it (Naman m:5eb8c3c4 pt 5)
```
#### S3-18 BEHAVIOUR  old 132-132 -> new 176-176: INFRA STOP logs build_log row and releases hold
```diff
-            shutil.rmtree(wt, ignore_errors=True); sys.exit(5)
+            shutil.rmtree(wt, ignore_errors=True); tsv(tag + "(INFRA-STOP)", t0, t1); release_hold("run-ending INFRA STOP"); sys.exit(5)
```
#### S3-19 WIRING  old 143-143 -> new 187-187: void attempt logged in build_log.tsv
```diff
-        log("VOID", tag, "attempt", attempt, aud)
+        tsv(f"{tag}(VOID-attempt{attempt})", t0, t1); log("VOID", tag, "attempt", attempt, aud)
```
#### S3-20 BEHAVIOUR  old 145-145 -> new 189-189: VOID STOP releases hold
```diff
-        report(f"VOID STOP at round-2 build {len(done)+1}/12: 3 attempts in a row hit checker/key/repo terms in the transcript; stopped"); sys.exit(6)
+        report(f"VOID STOP at round-2 build {len(done)+1}/12: 3 attempts in a row hit checker/key/repo terms in the transcript; stopped"); release_hold("run-ending VOID STOP"); sys.exit(6)
```
#### S3-21 WIRING  old 150-149 -> new 194-194: build_log.tsv row per build
```diff
+    tsv(tag, t0, t1)
```
#### S3-22 WIRING  old 165-165 -> new 210-210: row records failed probe checks + writable host paths
```diff
-           "isolation": {k: iso[k] for k in ("grep_hits", "visible_in_sandbox", "ok")}, "isolation_workspace_files": iso["workspace_files"], "audit": aud, "voided_attempts": voided,
+           "isolation": {k: iso[k] for k in ("grep_hits", "visible_in_sandbox", "probe_failed_checks", "writable", "ok")}, "isolation_workspace_files": iso["workspace_files"], "audit": aud, "voided_attempts": voided,
```
#### S3-23 BEHAVIOUR  old 171-171 -> new 216-216: hold removed after build 12
```diff
-log("ALL DONE")
+log("ALL DONE"); release_hold("after build 12")
```
## benchmark/blind/r2_run/pack_r2.py
### Stage 1: saved original (a84b5a07, 19:07Z) -> b55917c. The 12:37 IST (19:07Z) edits are marked [12:37]; the other hunks were made 19:08-19:15Z for the pre-build commit.  (7 hunks)
#### S1-1 WIRING  old 2-2 -> new 2-2: comment
```diff
-# round-2 blind packaging: labels from the SEALED key (files/tl_blind/r2/KEY.json, sha committed bc4b673; never rewritten),
+# round-2 blind packaging. Raw builds come stored by label (the driver resolved labels from the sealed key v2; this script only checks its sha),
```
#### S1-2 WIRING  old 6-8 -> new 6-8: env overrides used only by the dry-run self-test; defaults unchanged
```diff
-SNAP = "/home/user/tab/work/tl_blind_r2"
-OUT = "/home/user/tab/work/tl_blind_out/r2"
-BL = "/home/user/tab/work/tl_blind_r2_labelled"          # blinded copies (labels only)
+SNAP = os.environ.get("R2_SNAP", "/home/user/tab/work/tl_blind_r2")
+OUT = os.environ.get("R2_OUT", "/home/user/tab/work/tl_blind_out/r2")   # env overrides exist only for the dry-run self-test
+BL = os.environ.get("R2_BL", "/home/user/tab/work/tl_blind_r2_labelled")          # blinded copies (labels only)
```
#### S1-3 BEHAVIOUR [12:37]  old 10-12 -> new 10-13: key path/sha v2; leak-grep module imported; pack no longer reads the key
```diff
-KEYP = FB + "/KEY.json"; KEY_SHA = "2fa05c9609411681d61c4eede6c0b29a5a451733a4b14a051eb5a48a47ba0433"
-assert hashlib.sha256(open(KEYP, "rb").read()).hexdigest() == KEY_SHA, "KEY.json changed - stop"
-key = json.load(open(KEYP))
+KEYP = FB + "/KEY_v2.json"; KEY_SHA = "fd1d6896f82f74afb087dddbb69c9716ca2418c5fceba30b47cd5940a742b04c"   # key v2 (reseal); v1 KEY.json is VOID (seed printed), never used
+assert hashlib.sha256(open(KEYP, "rb").read()).hexdigest() == KEY_SHA, "KEY_v2.json changed - stop"   # sha only; not opened
+sys.path.insert(0, SNAP + "/benchmark/blind"); import leakgrep_r2 as LG   # Naman m:ed447bea (c)
+# raw builds are stored by LABEL by the driver (it resolved label -> version from the key); this script never opens the key
```
#### S1-4 BEHAVIOUR [12:37]  old 14-14 -> new 15-16: more files stripped from builds before packing (md, logs, look.py output, screenshots, editor dirs)
```diff
-DROP_FILES = re.compile(r"^(AGENTS|CLAUDE|CONTRACT|PLAN|NOTES|TODO|SCRATCH|README)(\..*)?$|gate\.sh|tightloop|ponytail|skill|contract|\.plan|\.test\.|_test\.|^test_|\.spec\.|^tests?$", re.I)
+DROP_FILES = re.compile(r"^(AGENTS|CLAUDE|CONTRACT|PLAN|NOTES|TODO|SCRATCH|README|CHANGELOG)(\..*)?$|gate\.sh|tightloop|ponytail|skill|contract|\.plan|\.test\.|_test\.|^test_|\.spec\.|^tests?$|"
+                        r"\.md$|\.log$|^console|^look.*\.(json|txt|png)$|^look\.py$|screen ?shot|^(shot|capture)[^/]*\.(png|jpe?g|webp)$|^\.(agents?|cursor|vscode)$", re.I)
```
#### S1-5 BEHAVIOUR  old 22-22 -> new 24-24: raw build read by label (driver stored it so); no key lookup
```diff
-        arm = key["apps"][app][lab]; src = f"{OUT}/{app}/{arm}"; dst = f"{BL}/{app}/{lab}"; dropped = []; hints = []
+        src = f"{OUT}/{app}/{lab}"; dst = f"{BL}/{app}/{lab}"; dropped = []; hints = []
```
#### S1-6 WIRING  old 40-41 -> new 42-44: output dir for strip log/spec overridable for the dry run
```diff
-json.dump(strip_log, open(f"{TD}/blind_strip_log_r2.json", "w"), indent=1)
-json.dump(spec, open(f"{TD}/viewer_spec_r2.json", "w"), indent=1)
+SP = os.environ.get("R2_SPECDIR", TD)
+json.dump(strip_log, open(f"{SP}/blind_strip_log_r2.json", "w"), indent=1)
+json.dump(spec, open(f"{SP}/viewer_spec_r2.json", "w"), indent=1)
```
#### S1-7 BEHAVIOUR [12:37]  old 45-44 -> new 48-71: leak grep over build dirs, zip listing+entries, unzipped tree, mtimes, .git; any hit stops the pack (exit 3)
```diff
+# LEAK GREP over every blinded build dir (must be 0), then build the one-zip viewer and leak-grep every zip entry (must be 0)
+LOGP = os.environ.get("R2_LEAKLOG", f"{TD}/leakgrep_r2.log"); lines = []
+dir_hits = []
+for app in spec["apps"]:
+    for b in app["builds"]:
+        h = LG.scan(b["dir"]); dir_hits += h; lines.append(f"dir {app['id']}/{b['label']}: {len(h)} hits")
+lines += dir_hits; lines.append(f"LEAK GREP build dirs: {len(dir_hits)} hits over 12 dirs")
+if dir_hits:
+    open(LOGP, "w").write("\n".join(lines) + "\n"); print("\n".join(lines)); sys.exit(3)
+VD = os.environ.get("R2_VD", FB + "/viewer")
+subprocess.run(["python3", f"{SNAP}/benchmark/blind/viewer/build_viewer.py", VD, f"{SP}/viewer_spec_r2.json"], check=True, timeout=240)
+zp = VD + ".zip"; import zipfile, tempfile
+zf = zipfile.ZipFile(zp); names = zf.namelist()
+zh = LG.scan(zp)                                         # zip listing (entry names) + every entry's bytes
+lines += zh; lines.append(f"LEAK GREP zip listing+entries: {len(zh)} hits over {len(names)} entries ({os.path.basename(zp)})")
+tmp = tempfile.mkdtemp(prefix="tlb-unzip-"); zf.extractall(tmp)
+uh = LG.scan(tmp)                                        # the unzipped tree, file by file
+lines += uh; lines.append(f"LEAK GREP unzipped tree: {len(uh)} hits over {sum(len(f) for _, _, f in os.walk(tmp))} files")
+bad_dt = [n for n in names if zf.getinfo(n).date_time != (2026, 10, 18, 12, 0, 0)]
+git = [n for n in names if "/.git/" in n or n.endswith("/.git") or "/.git" in n.split("builds/")[-1][:6]]
+lines.append(f"zip entries with a non-fixed timestamp: {len(bad_dt)}; .git entries: {len(git)}")
+shutil.rmtree(tmp, ignore_errors=True)
+open(LOGP, "w").write("\n".join(lines) + "\n"); print("\n".join(lines))
+if zh or uh or bad_dt or git: sys.exit(3)
```
### Stage 2: b55917c -> b0130d7 (the probe fix).  (0 hunks)
(no change)
### Stage 3: b0130d7 -> this CHECKS commit (hardened sandbox, guard, key v4, build log).  (2 hunks)
#### S3-1 WIRING  old 2-2 -> new 2-2: comment v2->v4
```diff
-# round-2 blind packaging. Raw builds come stored by label (the driver resolved labels from the sealed key v2; this script only checks its sha),
+# round-2 blind packaging. Raw builds come stored by label (the driver resolved labels from the sealed key v4; this script only checks its sha),
```
#### S3-2 WIRING  old 10-11 -> new 10-11: key v4 path + sha (sha check only)
```diff
-KEYP = FB + "/KEY_v2.json"; KEY_SHA = "fd1d6896f82f74afb087dddbb69c9716ca2418c5fceba30b47cd5940a742b04c"   # key v2 (reseal); v1 KEY.json is VOID (seed printed), never used
-assert hashlib.sha256(open(KEYP, "rb").read()).hexdigest() == KEY_SHA, "KEY_v2.json changed - stop"   # sha only; not opened
+KEYP = FB + "/KEY_v4.json"; KEY_SHA = "e765297c4a34e6908638bcc4348b78b76a2eadf05760da4756b82127e8f40d71"   # key v4 (reseal 993a431); v1 VOID, v2 BURNED, v3 VOID-UNUSED: never used
+assert hashlib.sha256(open(KEYP, "rb").read()).hexdigest() == KEY_SHA, "KEY_v4.json changed - stop"   # sha only; not opened
```
## New files in this CHECKS commit (all BEHAVIOUR: they define the sandbox every build runs in)
- benchmark/blind/r2_run/sandbox_r2.py (235 lines)
- benchmark/blind/r2_run/egress_r2.py (77 lines)
- benchmark/blind/r2_run/sandbox_selftest_r2.py (73 lines)
- benchmark/blind/r2_run/gen_key_watch_r2.py (64 lines)
- benchmark/blind/r2_run/registry_check_r2.py (30 lines)
- benchmark/blind/r2_run/guard_refusal_test_r2.sh (14 lines)
- benchmark/blind/r2_run/snap_r2.sh (12 lines)
- benchmark/blind/r2_run/cli_smoke_r2.py (21 lines)
