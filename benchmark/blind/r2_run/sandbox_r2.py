#!/usr/bin/env python3
"""Round-2 HARDENED build sandbox + the in-sandbox probe (Naman m:f4cffa5e pts 1-2, m:b3c5c470 pt 5, m:5eb8c3c4 pts 2-5).

prefix(wt, cfg) is the ONE bwrap invocation every build uses (blind_driver_r2.py) and the probe uses (this file): only the command
after the prefix differs (the agent CLI for a build, `python3 -c PROBE_CODE` for the probe).
  - root filesystem read-only (--ro-bind / /); private /dev, /proc (own pid namespace), ipc, uts, cgroup, NO network (--unshare-net)
  - /home/user is an EMPTY tmpfs with only the toolchains bound back READ-ONLY (TOOL_BINDS): so the keys, every repo/checker copy,
    task logs, agent session transcripts, ~/.netrc and the agent CLI's shared config are not there
  - /tmp, /var/tmp, /run, /dev/shm are private tmpfs (die with the sandbox)
  - writable host paths: exactly two, both fresh per build: the build's workspace (mkdtemp) and the CLI config dir (mkdtemp,
    bound at CFG_IN = CLAUDE_CONFIG_DIR, wiped after the build)
  - egress: only via egress_r2.py (CONNECT to the model API host:443; everything else 403), env cut to egress_r2.ALLOW_ENV
  - --new-session (no TIOCSTI), --die-with-parent; no_new_privs (sudo cannot elevate)

ONE command to re-run the probe (prints a JSON report, exit 0 = every check passed, 1 = a check failed):
    python3 benchmark/blind/r2_run/sandbox_r2.py --probe
"""
import json, os, random, secrets, shutil, socket, subprocess, sys, tempfile, time
HERE = os.path.dirname(os.path.abspath(__file__))
EGPY = os.path.join(HERE, "egress_r2.py")
HOSTS = os.path.join(HERE, "sandbox_hosts")
EG_DIR = "/home/user/tab/work/tl_r2_egress"
TOOL_BINDS = ["/home/user/tl-npm", "/home/user/go-dist", "/home/user/.cargo", "/home/user/.rustup"]
CFG_IN = "/tmp/.claude-cfg"
SOCK_IN = "/tmp/.egress"
PORT = 3128
PATH_IN = "/home/user/tl-npm/bin:/home/user/go-dist/go/bin:/home/user/.cargo/bin:/usr/local/bin:/usr/bin:/bin"
START_OK = "/home/user/tab/files/tl_blind/r2/START_OK"
OLD_PROBE_PATHS = ["/home/user/tab/files/tl_blind/r2/KEY.json", "/home/user/tab/files/tl_blind/r2/KEY_v2.json",
                   "/home/user/tab/files/tl_blind/r2/KEY_v3.json", "/home/user/tab/files/tl_blind/r2/KEY_v4.json",
                   "/home/user/tab/work/tl_blind_r2/benchmark/blind/checks/check_app.py", "/tmp/tlb_push/benchmark/blind/checks/check_app.py",
                   "/home/user/tab/work/tightloop_bench/benchmark/blind/checks/check_app.py", "/home/user/tab/tasks",
                   "/home/user/tab/work/tl_blind_out", "/home/user/.netrc", "/home/user/.prime", "/home/user/tab/work/tl_tools/claude-config"]

def clean_env():
    """The driver's and the probe's own environment: a fixed allowlist plus the model endpoint/credential the CLI needs.
    Values are never printed; the probe reports names only."""
    d = json.load(open("/home/user/tab/.model-capability.json"))
    e = {"HOME": "/home/user", "PATH": PATH_IN, "LANG": "C.UTF-8", "USER": "user", "LOGNAME": "user", "SHELL": "/bin/bash",
         "TMPDIR": "/tmp", "CLAUDE_CONFIG_DIR": CFG_IN,
         "ANTHROPIC_BASE_URL": d["base_url"].rstrip("/") + "/anthropic", "ANTHROPIC_API_KEY": d["token"]}
    return e

def start_proxy(env):
    """Start this process's own egress proxy (a unix socket in a fresh 0700 dir). Returns (sock_dir, Popen)."""
    os.makedirs(EG_DIR, exist_ok=True)
    sd = tempfile.mkdtemp(prefix="sock-", dir=EG_DIR)
    logp = os.path.join(EG_DIR, "egress-%d.log" % os.getpid())
    p = subprocess.Popen([sys.executable, EGPY, "proxy", os.path.join(sd, "egress.sock"), logp], env=env,
                         stdin=subprocess.DEVNULL, stdout=open(logp + ".out", "a"), stderr=subprocess.STDOUT, start_new_session=True)
    for _ in range(100):
        if os.path.exists(os.path.join(sd, "egress.sock")): break
        time.sleep(0.05)
    return sd, p

def stop_proxy(sd, p):
    try: p.kill(); p.wait(5)
    except Exception: pass
    shutil.rmtree(sd, ignore_errors=True)

def prefix(wt, cfg, sock_dir, extra=()):
    a = ["bwrap", "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc",
         "--tmpfs", "/home/user"]
    for t in TOOL_BINDS: a += ["--ro-bind", t, t]
    a += ["--tmpfs", "/tmp", "--tmpfs", "/var/tmp", "--tmpfs", "/run", "--tmpfs", "/dev/shm",
          "--bind", wt, wt, "--bind", cfg, CFG_IN,
          "--ro-bind", sock_dir, SOCK_IN, "--ro-bind", EGPY, "/tmp/.egress.py", "--ro-bind", HOSTS, "/etc/hosts"]
    a += list(extra)
    a += ["--unshare-pid", "--unshare-ipc", "--unshare-uts", "--unshare-net", "--unshare-cgroup-try",
          "--die-with-parent", "--new-session", "--chdir", wt,
          "python3", "/tmp/.egress.py", "wrap", str(PORT), SOCK_IN + "/egress.sock", "--"]
    return a

# ---------------------------------------------------------------- the probe (runs INSIDE the sandbox)
PROBE_CODE = r"""
import json, os, re, subprocess, sys, time
cfg = json.loads(sys.argv[1]); R = {}
def proc_scan():
    out = []
    for p in os.listdir('/proc'):
        if not p.isdigit(): continue
        try: cl = open('/proc/%s/cmdline' % p, 'rb').read().replace(b'\0', b' ').decode(errors='replace')
        except OSError: continue
        if int(p) == os.getpid() or cl.startswith('python3 /tmp/.egress.py wrap '): continue
        out.append((int(p), cl))
    return out
MARK = re.compile(r'prime-agent|turn-v2|blind_driver|pass3|pass4|runner\.py|forkserver|make_key|kernel-venv|ipykernel|egress_r2\.py proxy')
def proc_check():
    ps = [(p, cl) for p, cl in proc_scan() if not (p == 1 and cl.startswith('bwrap '))]
    bad = [pid for pid, cl in ps if cfg['token'] in cl or MARK.search(cl)]
    try: ns = os.readlink('/proc/self/ns/pid')
    except OSError as e: ns = 'err'
    names = sorted(set(cl.split(' ')[0].split('/')[-1] for _, cl in ps))
    ok = (not bad) and ns != cfg['host_ns'] and len(ps) <= 12
    allv = sorted((p, cl.split(' ')[0].split('/')[-1]) for p, cl in proc_scan())
    return {'ok': ok, 'all_visible_besides_probe': allv, 'n_other_processes': len(ps), 'pids_other': sorted(p for p, _ in ps), 'argv0': names,
            'note': 'besides this probe, the sandbox init (pid 1, bwrap) and the sandbox egress forwarder',
            'host_sentinel_or_host_process_visible': len(bad), 'own_pid_namespace': ns != cfg['host_ns']}
if cfg.get('loop'):
    L = cfg['loop']; t_end = time.time() + L['seconds']; samples = []
    while time.time() < t_end:
        ps = [(p, cl) for p, cl in proc_scan() if not (p == 1 and cl.startswith('bwrap '))]
        hit = [1 for _, cl in ps if cfg['token'] in cl or MARK.search(cl)]
        samples.append((round(time.time(), 3), len(ps), len(hit)))
        time.sleep(L['interval'])
    print(json.dumps({'samples': samples})); sys.exit(0)
R['processes'] = proc_check()
if cfg.get('procs_only'):
    R['ok'] = R['processes']['ok']; print(json.dumps(R)); sys.exit(0)
names = sorted(os.environ); allow = set(cfg['allow_env'])
try: init_names = sorted(set(x.split(b'=', 1)[0].decode() for x in open('/proc/1/environ', 'rb').read().split(b'\0') if x))
except OSError as e: init_names = ['<unreadable: %s>' % e.__class__.__name__]
R['env_names_only'] = {'ok': set(names) <= allow and all(n in allow or n.startswith('<unreadable') for n in init_names),
                       'names': names, 'pid1_names': init_names, 'unexpected': sorted((set(names) | set(init_names)) - allow)}
def curl(url, extra=()):
    try:
        r = subprocess.run(['curl', '-sS', '-m', '12', '-o', '/tmp/.cr', '-w', '%{http_code}'] + list(extra) + [url],
                           capture_output=True, text=True, timeout=30)
        return r.returncode, r.stdout.strip()[-3:], r.stderr.strip()[-80:]
    except Exception as e: return -1, '000', type(e).__name__
if cfg.get('check_net', True):
    blocked = {}
    for h in cfg['blocked_hosts']:
        rc, code, err = curl('https://%s/' % h); blocked[h] = {'rc': rc, 'http': code, 'refused': rc != 0 and code != '200'}
    rc_d, code_d, _ = curl('https://example.com/', ['--noproxy', '*'])
    old = os.umask(0o077); open('/tmp/.h', 'w').write('x-api-key: %s\n' % os.environ.get('ANTHROPIC_API_KEY', '')); os.umask(old)
    body = '{"model":"claude-opus-5-5","max_tokens":5,"messages":[{"role":"user","content":"Reply with OK"}]}'
    rc, code, err = curl(os.environ.get('ANTHROPIC_BASE_URL', '') + '/v1/messages',
                         ['-H', 'content-type: application/json', '-H', 'anthropic-version: 2023-06-01', '-H', '@/tmp/.h', '-d', body])
    os.remove('/tmp/.h')
    try: txt = ''.join(c.get('text', '') for c in json.load(open('/tmp/.cr')).get('content', []))[:12]
    except Exception: txt = ''
    R['network'] = {'ok': all(v['refused'] for v in blocked.values()) and code == '200' and rc_d != 0,
                    'blocked': blocked, 'direct_no_proxy_rc': rc_d, 'allowed_model_api_http': code, 'allowed_reply': txt}
mounts = []
for l in open('/proc/self/mountinfo'):
    f = l.split(); sep = f.index('-'); mounts.append({'mp': f[4].replace('\\040', ' '), 'opts': f[5], 'fstype': f[sep + 1], 'root': f[3]})
rw = [m for m in mounts if m['opts'].split(',')[0] == 'rw' and m['mp'] not in ('/proc',) and not m['mp'].startswith('/proc/')]
rw_host = [m['mp'] for m in rw if m['fstype'] not in ('tmpfs', 'devtmpfs', 'devpts', 'mqueue', 'proc') and os.access(m['mp'], os.W_OK)]
rw_noaccess = [m['mp'] for m in rw if m['fstype'] not in ('tmpfs', 'devtmpfs', 'devpts', 'mqueue', 'proc') and not os.access(m['mp'], os.W_OK)]
R['writable'] = {'ok': sorted(rw_host) == sorted([cfg['wt'], cfg['cfg_in']]),
                 'host_backed_rw': sorted(rw_host), 'rw_mount_but_no_write_permission': sorted(rw_noaccess), 'private_tmpfs_rw': sorted(m['mp'] for m in rw if m['mp'] not in rw_host and m['mp'] not in rw_noaccess)}
NAME = re.compile(cfg['name_re']); CONTENT = re.compile(cfg['content_re'].encode())
skip = ('/proc', '/sys', '/dev')
roots = sorted(set([m['mp'] for m in mounts if not m['mp'].startswith(skip)] + ['/tmp', '/home/user']))
name_hits, content_hits, sockets, nfiles = [], [], [], 0
for r in roots:
    big = r == '/' or r in cfg['tool_binds']
    for dp, dns, fs in os.walk(r):
        try:
            if os.stat(dp).st_dev != os.stat(r).st_dev: dns[:] = []; continue
        except OSError: continue
        dns[:] = [d for d in dns if not os.path.join(dp, d).startswith(skip)]
        for fn in fs + dns:
            p = os.path.join(dp, fn)
            if NAME.search(fn): name_hits.append(p)
        for fn in fs:
            p = os.path.join(dp, fn); nfiles += 1
            try:
                st = os.lstat(p)
            except OSError: continue
            import stat as S
            if S.S_ISSOCK(st.st_mode): sockets.append(p); continue
            if big or not S.S_ISREG(st.st_mode) or st.st_size > 4_000_000: continue
            try:
                if CONTENT.search(open(p, 'rb').read()): content_hits.append(p)
            except OSError: pass
allowed_socks = [cfg['sock_in'] + '/egress.sock']
R['scan'] = {'ok': not name_hits and not content_hits, 'roots': roots, 'files_seen': nfiles,
             'name_hits': sorted(set(name_hits)), 'content_hits': sorted(set(content_hits)),
             'name_rule': cfg['name_re'], 'content_rule': 'key/mapping or checker signature (see sandbox_r2.CONTENT_RE)',
             'content_scope': 'every mount except / and the read-only toolchain binds (those get the name rule)'}
R['unix_sockets'] = {'ok': sorted(set(sockets)) == allowed_socks, 'visible': sorted(set(sockets))}
home = sorted(os.listdir('/home/user'))
exp = sorted(os.path.basename(t) for t in cfg['tool_binds'])
R['home'] = {'ok': home == exp and not any(os.access(t, os.W_OK) for t in cfg['tool_binds']),
             'entries': home, 'expected_readonly_toolchains': exp, 'toolchains_writable': [t for t in cfg['tool_binds'] if os.access(t, os.W_OK)]}
R['old_probe_paths'] = {'ok': not any(os.path.exists(p) for p in cfg['old_paths']), 'visible': [p for p in cfg['old_paths'] if os.path.exists(p)]}
try: s = subprocess.run(['sudo', '-n', 'true'], capture_output=True, timeout=10).returncode
except Exception: s = -1
R['no_privilege'] = {'ok': s != 0, 'sudo_rc': s}
R['ok'] = all(v.get('ok') for v in R.values() if isinstance(v, dict))
print(json.dumps(R))
"""
NAME_RE = r"^(KEY(_v\d+)?\.json|mapping(_r\d+)?\.json|check_app\.py|blind_rows.*\.jsonl|COST|METRICS\.json|\.netrc)$"
CONTENT_RE = r'"apps"\s*:\s*\{\s*"(bookmarks|expenses|kanban)"|"seed"\s*:\s*\d|check_app|blind/checks|checks/reference|"A"\s*:\s*"(no-skill|ponytail|tightloop)'
BLOCKED = ["github.com", "raw.githubusercontent.com", "api.github.com", "codeload.github.com", "objects.githubusercontent.com",
           "cdn.jsdelivr.net", "registry.npmjs.org", "pypi.org", "files.pythonhosted.org", "crates.io", "index.crates.io",
           "static.crates.io", "proxy.golang.org", "example.com"]

def host_ns(): return os.readlink("/proc/self/ns/pid")

def run_probe(wt, cfg, sock_dir, token, check_net=True, extra=(), env=None, loop=None, timeout=240, use_prefix=None, procs_only=False):
    from egress_r2 import ALLOW_ENV, PROXY_ENV
    c = {"token": token, "host_ns": host_ns(), "wt": wt, "cfg_in": CFG_IN, "sock_in": SOCK_IN, "tool_binds": TOOL_BINDS,
         "allow_env": list(ALLOW_ENV) + list(PROXY_ENV), "blocked_hosts": BLOCKED, "check_net": check_net,
         "name_re": NAME_RE, "content_re": CONTENT_RE, "old_paths": OLD_PROBE_PATHS, "loop": loop, "procs_only": procs_only}
    pre = use_prefix if use_prefix is not None else prefix(wt, cfg, sock_dir, extra)
    r = subprocess.run(["timeout", "-k", "5", str(timeout)] + pre + ["python3", "-c", PROBE_CODE, json.dumps(c)],
                       capture_output=True, text=True, env=env, timeout=timeout + 20)
    try: return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception: return {"ok": False, "error": "probe produced no report", "rc": r.returncode, "stderr_tail": r.stderr[-300:]}

def sentinel():
    tok = "%d.%06d" % (random.randint(200, 299), secrets.randbelow(10**6))
    return tok, subprocess.Popen(["sleep", tok], start_new_session=True)

def redact(s, env):
    from urllib.parse import urlparse
    for k in ("ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL"):
        v = env.get(k)
        if v: s = s.replace(v, "<" + k.lower() + ">")
    h = urlparse(env.get("ANTHROPIC_BASE_URL", "")).hostname
    if h: s = s.replace(h, "<model-api-host>")
    return s

def probe_once(env, extra_plant=None, extra=(), check_net=True):
    """Fresh workspace + fresh config dir + own proxy + a host sentinel process, exactly as a build gets them."""
    wt = tempfile.mkdtemp(prefix="tlb-"); cfg = tempfile.mkdtemp(prefix="tlb-cfg-")
    subprocess.run(["git", "init", "-q"], cwd=wt)
    if extra_plant: extra_plant(wt, cfg)
    sd, pp = start_proxy(env); tok, sp = sentinel()
    try: rep = run_probe(wt, cfg, sd, tok, check_net=check_net, extra=extra, env=env)
    finally:
        sp.kill(); stop_proxy(sd, pp); shutil.rmtree(wt, ignore_errors=True); shutil.rmtree(cfg, ignore_errors=True)
    rep["host_sentinel_pid"] = sp.pid
    return rep

if __name__ == "__main__":
    sys.path.insert(0, HERE)
    if sys.argv[1:2] == ["--probe"]:
        env = clean_env(); os.environ.clear(); os.environ.update(env)
        rep = probe_once(env)
        print(redact(json.dumps(rep, indent=1), env))
        sys.exit(0 if rep.get("ok") else 1)
