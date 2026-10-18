#!/usr/bin/env python3
"""Round-2 build egress allowlist (Naman m:f4cffa5e pt 2, m:5eb8c3c4 pt 4). The build sandbox has NO network of its own
(bwrap --unshare-net: loopback only). Two halves:
  proxy <unix_sock> <log>: runs OUTSIDE the sandbox (started by sandbox_r2.start_proxy). An HTTP CONNECT proxy on a unix socket
      that tunnels ONLY to the model API host on port 443 and answers 403 to everything else. The allowed host is read from
      ANTHROPIC_BASE_URL in its own environment (never from argv, never written to the log: the log says <model-api>).
  wrap <tcp_port> <unix_sock> -- cmd...: runs INSIDE the sandbox. Forwards 127.0.0.1:<tcp_port> to the unix socket in a forked
      child, then execs cmd with HTTPS_PROXY/HTTP_PROXY pointing at it and an environment cut down to ALLOW_ENV.
So the only way out of the sandbox is a CONNECT to the model API host."""
import os, socket, sys, threading, time
from urllib.parse import urlparse
ALLOW_ENV = ("HOME", "PATH", "LANG", "LC_ALL", "TERM", "USER", "LOGNAME", "SHELL", "TMPDIR", "CLAUDE_CONFIG_DIR",
             "ANTHROPIC_BASE_URL", "ANTHROPIC_API_KEY")
PROXY_ENV = ("HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy", "ALL_PROXY", "NO_PROXY", "no_proxy")
def pump(a, b):
    try:
        while True:
            d = a.recv(65536)
            if not d: break
            b.sendall(d)
    except OSError: pass
    finally:
        for s in (a, b):
            try: s.shutdown(socket.SHUT_RDWR)
            except OSError: pass
def proxy(sock_path, logp):
    allowed = urlparse(os.environ["ANTHROPIC_BASE_URL"]).hostname
    if os.path.exists(sock_path): os.remove(sock_path)
    srv = socket.socket(socket.AF_UNIX); srv.bind(sock_path); os.chmod(sock_path, 0o600); srv.listen(64)
    log = open(logp, "a", buffering=1)
    def handle(c):
        try:
            buf = b""
            while b"\r\n\r\n" not in buf and len(buf) < 16384:
                d = c.recv(4096)
                if not d: return
                buf += d
            line = buf.split(b"\r\n", 1)[0].decode(errors="replace"); parts = line.split()
            target = parts[1] if len(parts) > 1 else "?"
            host, _, port = target.rpartition(":")
            ok = len(parts) >= 2 and parts[0] == "CONNECT" and host == allowed and port == "443"
            shown = "<model-api>:443" if ok else target[:120]
            log.write(f"{time.strftime('%H:%M:%SZ', time.gmtime())} {'ALLOW' if ok else 'REFUSE'} {parts[0] if parts else '?'} {shown}\n")
            if not ok:
                c.sendall(b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"); return
            u = socket.create_connection((host, 443), timeout=30); u.settimeout(None)
            c.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
            rest = buf.split(b"\r\n\r\n", 1)[1]
            if rest: u.sendall(rest)
            t = threading.Thread(target=pump, args=(u, c), daemon=True); t.start(); pump(c, u); t.join()
        except Exception as e:
            log.write(f"{time.strftime('%H:%M:%SZ', time.gmtime())} ERROR {type(e).__name__}\n")
        finally:
            try: c.close()
            except OSError: pass
    while True:
        c, _ = srv.accept(); threading.Thread(target=handle, args=(c,), daemon=True).start()
def wrap(port, sock_path, cmd):
    lst = socket.socket(); lst.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); lst.bind(("127.0.0.1", port)); lst.listen(64)
    if os.fork() == 0:
        os.setsid()
        while True:
            c, _ = lst.accept()
            def go(c=c):
                try: u = socket.socket(socket.AF_UNIX); u.connect(sock_path)
                except OSError: c.close(); return
                t = threading.Thread(target=pump, args=(u, c), daemon=True); t.start(); pump(c, u)
            threading.Thread(target=go, daemon=True).start()
    lst.close()
    p = f"http://127.0.0.1:{port}"
    env = {k: v for k, v in os.environ.items() if k in ALLOW_ENV}
    env.update(HTTPS_PROXY=p, HTTP_PROXY=p, https_proxy=p, http_proxy=p, ALL_PROXY=p, NO_PROXY="", no_proxy="")
    os.execvpe(cmd[0], cmd, env)
if __name__ == "__main__":
    if sys.argv[1] == "proxy": proxy(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "wrap":
        i = sys.argv.index("--"); wrap(int(sys.argv[2]), sys.argv[3], sys.argv[i + 1:])
