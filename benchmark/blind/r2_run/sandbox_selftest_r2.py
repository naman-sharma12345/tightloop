#!/usr/bin/env python3
"""Self-tests for the hardened round-2 sandbox (sandbox_r2.py). Prints a JSON report; exit 0 only if every test behaves.
  clean            : the probe passes on a fresh build workspace
  planted          : 3 names (KEY_v2.json, mapping_r2.json, notes.txt with key-shaped content) planted in 2 mount paths
                     (the workspace and the CLI config dir) -> the probe FAILS and lists all 6
  env_extra        : an extra variable name in the sandbox's environment -> env check FAILS
  home_extra       : an extra directory bound under /home/user -> home check FAILS
  writable_extra   : an extra writable host path bound in -> writable check FAILS
  old_sandbox      : the b0130d7 sandbox (no pid namespace) with a host sentinel process -> process check FAILS (positive control;
                     process-list only, so no file in that sandbox is read)
  two_builds       : fake build A writes its workspace + config dir, its output is copied to a scratch OUT; fake build B
                     (fresh workspace + config) cannot see A's workspace, A's config dir, or OUT; A's config dir is wiped after A
"""
import json, os, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sandbox_r2 as S
env = S.clean_env(); os.environ.clear(); os.environ.update(env)
T = {}
def summary(rep, keys): return {k: rep.get(k, {}).get("ok") for k in keys}
r = S.probe_once(env, check_net=False); T["clean"] = {"ok": r.get("ok") is True, "probe_ok": r.get("ok")}
FAKE = '{"apps": {"bookmarks": {"A": "x"}}, "seed": 1}\n'
planted = []
def plant(wt, cfg):
    for base in (wt, cfg):
        for n, body in (("KEY_v2.json", "{}\n"), ("mapping_r2.json", "{}\n"), ("notes.txt", FAKE)):
            d = os.path.join(base, "sub"); os.makedirs(d, exist_ok=True); p = os.path.join(d, n); open(p, "w").write(body)
            planted.append(p.replace(cfg, S.CFG_IN))
r = S.probe_once(env, extra_plant=plant, check_net=False)
caught = set(r["scan"]["name_hits"]) | set(r["scan"]["content_hits"])
T["planted"] = {"ok": r.get("ok") is False and r["scan"]["ok"] is False and all(p in caught for p in planted),
                "planted": planted, "name_hits": r["scan"]["name_hits"], "content_hits": r["scan"]["content_hits"]}
r = S.probe_once(dict(env, EXTRA_TEST_NAME="x"), check_net=False)
T["env_extra"] = {"ok": r["env_names_only"]["ok"] is False and "EXTRA_TEST_NAME" in r["env_names_only"]["unexpected"],
                  "unexpected": r["env_names_only"]["unexpected"]}
xd = tempfile.mkdtemp(prefix="tlb-extra-")
r = S.probe_once(env, extra=["--ro-bind", xd, "/home/user/extra"], check_net=False)
T["home_extra"] = {"ok": r["home"]["ok"] is False, "entries": r["home"]["entries"]}
r = S.probe_once(env, extra=["--bind", xd, "/var/tmp/shared"], check_net=False)
T["writable_extra"] = {"ok": r["writable"]["ok"] is False and "/var/tmp/shared" in r["writable"]["host_backed_rw"],
                       "host_backed_rw": r["writable"]["host_backed_rw"]}
shutil.rmtree(xd, ignore_errors=True)
# old sandbox (b0130d7 bwrap_prefix, verbatim shape) as a positive control for the process check
wt = tempfile.mkdtemp(prefix="tlb-"); cfg = tempfile.mkdtemp(prefix="tlb-cfg-")
old = ["bwrap", "--dev-bind", "/", "/", "--tmpfs", "/home/user/tab", "--bind", "/home/user/tab/work/tl_tools", "/home/user/tab/work/tl_tools",
       "--tmpfs", "/home/user/.prime", "--tmpfs", "/dev/shm", "--tmpfs", "/tmp", "--bind", wt, wt,
       "--ro-bind", S.HOSTS, "/etc/hosts", "--chdir", wt, "--die-with-parent"]
tok, sp = S.sentinel()
r = S.run_probe(wt, cfg, "/nonexistent", tok, check_net=False, use_prefix=old, env=env, procs_only=True)  # process list only: nothing else is read
sp.kill(); shutil.rmtree(wt, ignore_errors=True); shutil.rmtree(cfg, ignore_errors=True)
T["old_sandbox"] = {"ok": r["processes"]["ok"] is False and r["processes"]["host_sentinel_or_host_process_visible"] > 0,
                    "visible_host_processes": r["processes"]["n_other_processes"], "sentinel_or_host_marker_hits": r["processes"]["host_sentinel_or_host_process_visible"]}
# two fake builds
sd, pp = S.start_proxy(env)
OUTT = tempfile.mkdtemp(prefix="tlb-out-", dir="/home/user/tab/work")
wa = tempfile.mkdtemp(prefix="tlb-"); ca = tempfile.mkdtemp(prefix="tlb-cfg-")
ra = subprocess.run(S.prefix(wa, ca, sd) + ["bash", "-c", "echo A-OUTPUT > index.html && echo a > $CLAUDE_CONFIG_DIR/a.jsonl && ls $CLAUDE_CONFIG_DIR"],
                    capture_output=True, text=True, env=env, timeout=60)
shutil.copytree(wa, os.path.join(OUTT, "A"))
shutil.rmtree(ca)   # the driver wipes the config dir after each build
wb = tempfile.mkdtemp(prefix="tlb-"); cb = tempfile.mkdtemp(prefix="tlb-cfg-")
chk = "import os,sys,json; P=sys.argv[1:]; print(json.dumps({p: os.path.exists(p) for p in P} | {'own_cfg_listing': os.listdir(os.environ['CLAUDE_CONFIG_DIR'])}))"
paths = [wa, wa + "/index.html", ca, OUTT, OUTT + "/A/index.html", "/home/user/tab/work/tl_blind_out"]
rb = subprocess.run(S.prefix(wb, cb, sd) + ["python3", "-c", chk] + paths, capture_output=True, text=True, env=env, timeout=60)
try: vis = json.loads(rb.stdout.strip().splitlines()[-1])
except Exception: vis = {"error": rb.stderr[-300:]}
T["two_builds"] = {"ok": ra.returncode == 0 and os.path.exists(os.path.join(OUTT, "A", "index.html")) and not os.path.exists(ca)
                   and all(vis.get(p) is False for p in paths) and vis.get("own_cfg_listing") == [],
                   "build_A_rc": ra.returncode, "A_config_dir_wiped": not os.path.exists(ca),
                   "seen_from_B": vis, "note": "A's workspace still existed on the host while B ran (worst case)"}
for d in (wa, wb, cb, OUTT): shutil.rmtree(d, ignore_errors=True)
S.stop_proxy(sd, pp)
T["ok"] = all(v["ok"] for v in T.values())
print(json.dumps(T, indent=1)); sys.exit(0 if T["ok"] else 1)
