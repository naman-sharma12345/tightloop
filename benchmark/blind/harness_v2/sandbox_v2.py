#!/usr/bin/env python3
"""APP HARNESS v2 build sandbox: r2_run/sandbox_r2.py (left frozen, sha256 9a6dcca5...6d21) with ONE change: Playwright's
browser folder is bound back READ-ONLY inside the sandbox.

Why (the v1 browser fault): sandbox_r2.prefix mounts an empty tmpfs on /home/user and binds back only TOOL_BINDS
(tl-npm, go-dist, .cargo, .rustup). Playwright looks for its browser in $HOME/.cache/ms-playwright, so when the building
agent tested its own app the launch crashed:
  "Executable doesn't exist at /home/user/.cache/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-linux64/..."
(r2 7/12 builds, v4c-n3 4/6, v8 1/9, v9 4/9). The agent then retried or installed, which cost tokens.

How it is used: `import sandbox_v2` patches sandbox_r2.prefix IN THE IMPORTING PROCESS ONLY (the file on disk is untouched),
so the build invocation and the hardened probe (sandbox_r2.run_probe, which calls prefix) both get the bind. Drivers keep
using the module object as S = sandbox_v2.S, exactly as the v1 drivers use sandbox_r2.

Self-test (no build, no model call):
    python3 benchmark/blind/harness_v2/sandbox_v2.py --browser-selftest <app_dir>
runs one headless-Chromium launch + page load of <app_dir> INSIDE the sandbox twice: with the v1 prefix and with the v2
prefix, and prints one JSON line each (launch ok or the error, page title, buttons seen, what /home/user holds, and that the
browser bind is read-only).

Probe fix (after d223c09 refused every build on the frozen probe's 'home' check): the importing process also gets a v2
PROBE_CODE whose 'home' check expects the 4 toolchains plus '.cache' holding ONLY a read-only ms-playwright; every other
probe check is the frozen text. Self-test (one model ping for the network check in case a):
    python3 benchmark/blind/harness_v2/sandbox_v2.py --probe-selftest
"""
import json, os, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "r2_run"))
import sandbox_r2 as S

PW_DIR = "/home/user/.cache/ms-playwright"   # Playwright's default browser path for HOME=/home/user (the sandbox's HOME)
V1_PREFIX = S.prefix

def prefix_v2(wt, cfg, sock_dir, extra=()):
    """The v1 prefix plus ONE read-only bind of the browser folder (added before any caller extras)."""
    return V1_PREFIX(wt, cfg, sock_dir, extra=("--ro-bind", PW_DIR, PW_DIR) + tuple(extra))

S.prefix = prefix_v2
S.HARNESS = "app-harness-v2"

# ---------------------------------------------------------------- v2 probe: the frozen PROBE_CODE with ONE check replaced
# The frozen probe's 'home' check wants /home/user to list EXACTLY the 4 toolchain folders. The v2 browser bind adds '.cache',
# so on d223c09 every build was refused before build 1 (ISOLATION STOP, failed probe checks ['home']; 0 builds ran).
# v2 'home' = the same check, expecting the 4 toolchains plus '.cache', AND (all inside the sandbox):
#   - /home/user/.cache lists ONLY 'ms-playwright'
#   - ms-playwright is not writable (os.access says no, a real file create fails, and its mount is 'ro')
#   - the only mounts under /home/user are the 4 toolchains and ms-playwright (nothing else bound anywhere under it)
# Every other probe check is the frozen text, byte for byte (the swap below asserts the old block is there exactly once).
V1_PROBE_CODE = S.PROBE_CODE
V1_HOME_CHECK = ("home = sorted(os.listdir('/home/user'))\n"
                 "exp = sorted(os.path.basename(t) for t in cfg['tool_binds'])\n"
                 "R['home'] = {'ok': home == exp and not any(os.access(t, os.W_OK) for t in cfg['tool_binds']),\n"
                 "             'entries': home, 'expected_readonly_toolchains': exp, 'toolchains_writable': [t for t in cfg['tool_binds'] if os.access(t, os.W_OK)]}\n")
V2_HOME_CHECK = ("home = sorted(os.listdir('/home/user'))\n"
                 "exp = sorted([os.path.basename(t) for t in cfg['tool_binds']] + ['.cache'])\n"
                 "PW = %r\n"
                 "try: cache = sorted(os.listdir('/home/user/.cache'))\n"
                 "except OSError as e: cache = ['<unreadable: %%s>' %% e.__class__.__name__]\n"
                 "pw_create = False\n"
                 "try:\n"
                 "    fd = os.open(PW + '/.v2_home_write_probe', os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600); os.close(fd); pw_create = True\n"
                 "    os.unlink(PW + '/.v2_home_write_probe')\n"
                 "except OSError: pass\n"
                 "pw_mounts = [m for m in mounts if m['mp'] == PW]\n"
                 "pw_ro = bool(pw_mounts) and all(m['opts'].split(',')[0] == 'ro' for m in pw_mounts)\n"
                 "under_home = sorted(set(m['mp'] for m in mounts if m['mp'].startswith('/home/user/')))\n"
                 "exp_mounts = sorted(list(cfg['tool_binds']) + [PW])\n"
                 "R['home'] = {'ok': home == exp and not any(os.access(t, os.W_OK) for t in cfg['tool_binds'])\n"
                 "                   and cache == ['ms-playwright'] and not os.access(PW, os.W_OK) and not pw_create and pw_ro and under_home == exp_mounts,\n"
                 "             'entries': home, 'expected': exp, 'toolchains_writable': [t for t in cfg['tool_binds'] if os.access(t, os.W_OK)],\n"
                 "             'cache_entries': cache, 'browser_dir_writable_access': os.access(PW, os.W_OK), 'browser_dir_create_worked': pw_create,\n"
                 "             'browser_mount_ro': pw_ro, 'mounts_under_home': under_home, 'expected_mounts_under_home': exp_mounts}\n") % PW_DIR
assert V1_PROBE_CODE.count(V1_HOME_CHECK) == 1, "frozen probe text changed: the v2 'home' swap refuses"
PROBE_CODE_V2 = V1_PROBE_CODE.replace(V1_HOME_CHECK, V2_HOME_CHECK)
S.PROBE_CODE = PROBE_CODE_V2      # sandbox_r2.run_probe reads its module global PROBE_CODE at call time: this process only

def probe_selftest():
    """(a) the full v2 probe with the v2 prefix: ok True; (a0) the frozen probe with the v2 prefix: fails 'home' (the d223c09
    refusal); (b1, b1f, b2, b3) the v2 probe with one deliberate extra bind (a folder in .cache, a file in .cache, a folder in
    /home/user, a WRITABLE ms-playwright): each must fail 'home'. Every case runs the full probe, network check included."""
    env = S.clean_env(); os.environ.clear(); os.environ.update(env)
    dummy = tempfile.mkdtemp(prefix="tlb-v2dummy-")
    def show(name, rep):
        fails = sorted(k for k, v in rep.items() if isinstance(v, dict) and v.get("ok") is False)
        checks = {k: v.get("ok") for k, v in rep.items() if isinstance(v, dict) and "ok" in v}
        print(S.redact(json.dumps({"case": name, "ok": rep.get("ok"), "checks": checks, "failed": fails, "home": rep.get("home"),
                                   "error": rep.get("error"), "stderr_tail": rep.get("stderr_tail")}), env), flush=True)
        return rep.get("ok"), fails
    res = {}
    try:
        res["a"] = show("a: v2 probe + v2 prefix (expect ok True)", S.probe_once(env))
        S.PROBE_CODE = V1_PROBE_CODE
        try: res["a0"] = show("a0: FROZEN probe + v2 prefix (expect fail on home, the d223c09 refusal)", S.probe_once(env))
        finally: S.PROBE_CODE = PROBE_CODE_V2
        res["b1"] = show("b1: v2 probe + extra ro-bind /home/user/.cache/dummy (expect fail on home)",
                         S.probe_once(env, extra=("--ro-bind", dummy, "/home/user/.cache/dummy")))
        dfile = os.path.join(dummy, "stray.txt"); open(dfile, "w").write("x")
        res["b1f"] = show("b1f: v2 probe + extra ro-bind of a FILE /home/user/.cache/stray.txt (expect fail on home)",
                          S.probe_once(env, extra=("--ro-bind", dfile, "/home/user/.cache/stray.txt")))
        res["b2"] = show("b2: v2 probe + extra ro-bind /home/user/dummy (expect fail on home)",
                         S.probe_once(env, extra=("--ro-bind", dummy, "/home/user/dummy")))
        res["b3"] = show("b3: v2 probe + WRITABLE bind over the browser dir (expect fail on home)",
                         S.probe_once(env, extra=("--bind", dummy, PW_DIR)))
    finally:
        shutil.rmtree(dummy, ignore_errors=True)
    ok = (res["a"][0] is True and res["a0"][0] is False and res["a0"][1] == ["home"]
          and all(res[k][0] is False and "home" in res[k][1] for k in ("b1", "b1f", "b2", "b3")))
    print("PROBE SELFTEST", "PASS" if ok else "FAIL", {k: v[1] for k, v in res.items()}, flush=True)
    return ok

SELFTEST_CODE = r"""
import json, os, subprocess, sys, time
R = {'home_user': sorted(os.listdir('/home/user'))}
try:
    open('/home/user/.cache/ms-playwright/.v2_write_probe', 'w').write('x'); R['browser_bind_writable'] = True
except OSError as e: R['browser_bind_writable'] = False
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8765', '--bind', '127.0.0.1', '-d', os.getcwd()],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.0)
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:120]))
        pg.goto('http://127.0.0.1:8765/index.html'); pg.wait_for_timeout(500)
        R.update(launch='ok', title=pg.title(), buttons=pg.locator('button').count(), page_errors=errs,
                 browser_version=b.version)
        b.close()
except Exception as e:
    R.update(launch='FAILED', error=str(e).replace(chr(10), ' ')[:300])
finally:
    srv.terminate()
print(json.dumps(R))
"""

def browser_selftest(app_dir):
    env = S.clean_env()
    sd, proxy = S.start_proxy(env)
    out = {}
    try:
        for name, pf in (("v1_prefix (sandbox_r2, frozen)", V1_PREFIX), ("v2_prefix (sandbox_v2)", prefix_v2)):
            wt = tempfile.mkdtemp(prefix="tlb-v2st-"); cfg = tempfile.mkdtemp(prefix="tlb-v2st-cfg-")
            for f in os.listdir(app_dir):
                if os.path.isfile(os.path.join(app_dir, f)): shutil.copy2(os.path.join(app_dir, f), wt)
            cmd = ["timeout", "-k", "5", "120"] + pf(wt, cfg, sd) + ["python3", "-c", SELFTEST_CODE]
            r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=150, stdin=subprocess.DEVNULL)
            line = (r.stdout.strip().splitlines() or [""])[-1]
            try: rep = json.loads(line)
            except Exception: rep = {"launch": "NO-REPORT", "rc": r.returncode, "stderr": r.stderr[-300:]}
            rep["rc"] = r.returncode
            out[name] = rep
            print(name, json.dumps(rep), flush=True)
            shutil.rmtree(wt, ignore_errors=True); shutil.rmtree(cfg, ignore_errors=True)
    finally:
        S.stop_proxy(sd, proxy)
    return out

if __name__ == "__main__":
    if sys.argv[1:2] == ["--probe-selftest"]:
        sys.exit(0 if probe_selftest() else 1)
    if len(sys.argv) >= 3 and sys.argv[1] == "--browser-selftest":
        o = browser_selftest(sys.argv[2])
        v1 = o["v1_prefix (sandbox_r2, frozen)"]; v2 = o["v2_prefix (sandbox_v2)"]
        ok = v1.get("launch") != "ok" and v2.get("launch") == "ok" and v2.get("browser_bind_writable") is False
        print("SELFTEST", "PASS" if ok else "FAIL", "(v1 launch:", v1.get("launch"), "| v2 launch:", v2.get("launch"),
              "| v2 browser bind writable:", v2.get("browser_bind_writable"), ")")
        sys.exit(0 if ok else 1)
    print(__doc__); sys.exit(2)
