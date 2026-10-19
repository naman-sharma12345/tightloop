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
    if len(sys.argv) >= 3 and sys.argv[1] == "--browser-selftest":
        o = browser_selftest(sys.argv[2])
        v1 = o["v1_prefix (sandbox_r2, frozen)"]; v2 = o["v2_prefix (sandbox_v2)"]
        ok = v1.get("launch") != "ok" and v2.get("launch") == "ok" and v2.get("browser_bind_writable") is False
        print("SELFTEST", "PASS" if ok else "FAIL", "(v1 launch:", v1.get("launch"), "| v2 launch:", v2.get("launch"),
              "| v2 browser bind writable:", v2.get("browser_bind_writable"), ")")
        sys.exit(0 if ok else 1)
    print(__doc__); sys.exit(2)
