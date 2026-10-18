#!/usr/bin/env python3
"""Key v4 generation under watch (Naman m:5eb8c3c4 pt 2). Runs OUTSIDE the build sandbox:
  1. starts the hardened sandbox (sandbox_r2.prefix, same invocation as a build) running the probe's process-list loop
     (every 50 ms for LOOP_S seconds, counting every visible process whose argv carries a host marker incl. 'make_key');
  2. after 1.5 s runs the committed generator benchmark/blind/make_key_r2.py (sha256 checked first) as a host subprocess:
     <key_path> and the repo path are its only arguments; no seed in argv or env; its stdout (one 64-hex line) is captured;
  3. a positive control afterwards: the same loop in the b0130d7 sandbox (no pid namespace) while a dummy host process whose
     argv contains 'make_key' runs; it must be seen there.
Prints a JSON log (the key's sha256 and timings; never the key). Exit 0 only if: generator rc 0, 64-hex sha, >=1 loop sample
inside the generator's lifetime, 0 hits in the hardened loop, >0 hits in the positive control.
Usage: gen_key_watch_r2.py <key_path> <repo_root> <expected_make_key_sha256>"""
import hashlib, json, os, re, shutil, subprocess, sys, tempfile, threading, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sandbox_r2 as S
kp, repo, want = sys.argv[1], sys.argv[2], sys.argv[3]
gen = os.path.join(repo, "benchmark/blind/make_key_r2.py")
assert hashlib.sha256(open(gen, "rb").read()).hexdigest() == want, "make_key_r2.py differs from the committed method"
assert not os.path.exists(kp), "key exists"
env = S.clean_env(); os.environ.clear(); os.environ.update(env)
LOOP_S, IV = 5.0, 0.05
def loop_in(pre_fn, tok, out):
    wt = tempfile.mkdtemp(prefix="tlb-"); cfg = tempfile.mkdtemp(prefix="tlb-cfg-")
    out["rep"] = S.run_probe(wt, cfg, out.get("sd", "/nonexistent"), tok, check_net=False, env=env,
                             loop={"seconds": LOOP_S, "interval": IV}, use_prefix=pre_fn(wt, cfg), timeout=60)
    shutil.rmtree(wt, ignore_errors=True); shutil.rmtree(cfg, ignore_errors=True)
LOG = {"generator": "benchmark/blind/make_key_r2.py", "generator_sha256": want, "loop_interval_s": IV, "loop_seconds": LOOP_S}
# 1+2: hardened loop + real generator
sd, pp = S.start_proxy(env); tok, sp = S.sentinel()
H = {"sd": sd}
th = threading.Thread(target=loop_in, args=(lambda wt, cfg: S.prefix(wt, cfg, sd), tok, H)); th.start()
time.sleep(1.5)
g0 = time.time()
g = subprocess.run([sys.executable, gen, kp, repo], capture_output=True, text=True, env={"PATH": S.PATH_IN, "LANG": "C.UTF-8"}, timeout=60)
g1 = time.time()
th.join(); sp.kill(); S.stop_proxy(sd, pp)
out = g.stdout.strip()
LOG["generator_rc"] = g.returncode; LOG["generator_stdout_is_one_64hex_line"] = bool(re.fullmatch(r"[0-9a-f]{64}", out))
LOG["generator_stderr_bytes"] = len(g.stderr)
LOG["key_sha256"] = out if LOG["generator_stdout_is_one_64hex_line"] else None
LOG["key_sha256_recomputed"] = hashlib.sha256(open(kp, "rb").read()).hexdigest() if os.path.exists(kp) else None
LOG["key_mode"] = oct(os.stat(kp).st_mode & 0o777) if os.path.exists(kp) else None
LOG["generator_start_utc"] = time.strftime("%H:%M:%S", time.gmtime(g0)) + ".%03dZ" % int((g0 % 1) * 1000)
LOG["generator_ms"] = round((g1 - g0) * 1000, 1)
smp = H["rep"].get("samples", [])
inwin = [s for s in smp if g0 - IV <= s[0] <= g1 + IV]
LOG["hardened"] = {"samples": len(smp), "samples_during_generator": len(inwin), "max_visible_processes": max((s[1] for s in smp), default=None),
                   "samples_with_host_or_generator_process_visible": sum(1 for s in smp if s[2]),
                   "first_sample_utc": time.strftime("%H:%M:%SZ", time.gmtime(smp[0][0])) if smp else None,
                   "last_sample_utc": time.strftime("%H:%M:%SZ", time.gmtime(smp[-1][0])) if smp else None}
# 3: positive control in the old sandbox with a dummy 'make_key' process
O = {}
wt0 = tempfile.mkdtemp(prefix="tlb-")
old = lambda wt, cfg: ["bwrap", "--dev-bind", "/", "/", "--tmpfs", "/home/user/tab", "--tmpfs", "/home/user/.prime", "--tmpfs", "/dev/shm",
                       "--tmpfs", "/tmp", "--bind", wt, wt, "--ro-bind", S.HOSTS, "/etc/hosts", "--chdir", wt, "--die-with-parent"]
th = threading.Thread(target=loop_in, args=(old, tok + "x", O)); th.start(); time.sleep(1.5)
d = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(1.0)", "make_key_dummy"]); d.wait(); th.join()
shutil.rmtree(wt0, ignore_errors=True)
smp = O["rep"].get("samples", [])
LOG["positive_control_old_sandbox"] = {"samples": len(smp), "samples_with_host_or_dummy_visible": sum(1 for s in smp if s[2]),
                                       "max_visible_processes": max((s[1] for s in smp), default=None)}
LOG["ok"] = (LOG["generator_rc"] == 0 and LOG["generator_stdout_is_one_64hex_line"] and LOG["key_sha256"] == LOG["key_sha256_recomputed"]
             and LOG["hardened"]["samples_during_generator"] >= 1 and LOG["hardened"]["samples_with_host_or_generator_process_visible"] == 0
             and LOG["positive_control_old_sandbox"]["samples_with_host_or_dummy_visible"] > 0)
print(json.dumps(LOG, indent=1)); sys.exit(0 if LOG["ok"] else 1)
