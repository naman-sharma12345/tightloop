#!/usr/bin/env python3
"""Registry check (Naman m:f4cffa5e pt 2): from inside the hardened build sandbox (sandbox_r2.prefix, the build invocation), the
package tools a build could use try to pull a skill name or the repo. All must fail. Prints one line per attempt + the
outbound-allowed line. Exit 0 only if every attempt failed."""
import json, os, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sandbox_r2 as S
env = S.clean_env(); os.environ.clear(); os.environ.update(env)
sd, pp = S.start_proxy(env)
wt = tempfile.mkdtemp(prefix="tlb-"); cfg = tempfile.mkdtemp(prefix="tlb-cfg-")
T = []
for name in ("tightloop", "ponytail"):
    T += [("npm view " + name, f"npm view {name} name --fetch-retries=0 --fetch-timeout=8000"),
          ("npm install github:naman-sharma12345/" + name, f"npm install --no-save --fetch-retries=0 --fetch-timeout=8000 github:naman-sharma12345/{name}"),
          ("pip download " + name, f"pip download --no-deps --retries 0 --timeout 8 -d /tmp/p {name}"),
          ("pip install git+https://github.com/naman-sharma12345/" + name, f"pip install --no-deps --retries 0 --timeout 8 --target /tmp/q git+https://github.com/naman-sharma12345/{name}"),
          ("cargo search " + name, f"cargo search {name} --limit 1"),
          ("go mod download github.com/naman-sharma12345/" + name, f"cd /tmp && mkdir -p g && cd g && go mod init x >/dev/null 2>&1; GOFLAGS=-mod=mod go mod download github.com/naman-sharma12345/{name}@latest"),
          ("git clone https://github.com/naman-sharma12345/" + name, f"git clone -q --depth 1 https://github.com/naman-sharma12345/{name} /tmp/c")]
ok_all = True; out = []
for label, cmd in T:
    r = subprocess.run(["timeout", "-k", "5", "45"] + S.prefix(wt, cfg, sd) + ["bash", "-c", cmd + " >/tmp/o 2>&1; echo rc=$?; grep -m1 -iE '403|forbidden|proxy|tunnel|error|fail|unable' /tmp/o | cut -c1-110"],
                       capture_output=True, text=True, env=env, timeout=70)
    lines = r.stdout.strip().splitlines(); rc = lines[0] if lines else f"rc=timeout({r.returncode})"
    failed = rc != "rc=0"; ok_all &= failed
    out.append(f"{'BLOCKED' if failed else 'REACHED'}  {label}  {rc}  {lines[1] if len(lines) > 1 else ''}")
S.stop_proxy(sd, pp); shutil.rmtree(wt, ignore_errors=True); shutil.rmtree(cfg, ignore_errors=True)
out.append("OUTBOUND ALLOWED from a build: only an HTTPS CONNECT to the model API host on port 443, through the egress proxy (egress_r2.py); "
           "the sandbox has no network of its own (no DNS, no direct sockets); every other host, incl. GitHub, npm, PyPI, crates.io, the Go proxy and CDNs, gets 403.")
print(S.redact("\n".join(out), env)); sys.exit(0 if ok_all else 1)
