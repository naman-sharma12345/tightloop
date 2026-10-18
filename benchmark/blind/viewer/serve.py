#!/usr/bin/env python3
"""Blind viewer server: python3 serve.py [base_port]   (default 8000)
One process. The viewer page is on base_port; every build gets its OWN port (base_port+1, +2, ...), so each build is its own
browser origin: its own cache and its own localStorage, and no build can ever see another build's files or data.
Every response is sent with Cache-Control: no-store, and conditional requests are ignored (always a fresh 200).
Only the build folders are served on the build ports, with no directory listings; the viewer port answers only /, /index.html
and /manifest.json (404 for everything else), so nothing else in this folder is reachable from the browser."""
import functools, http.server, json, os, sys, threading
ROOT = os.path.dirname(os.path.abspath(__file__))
class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, max-age=0"); self.send_header("Pragma", "no-cache")
        super().end_headers()
    def send_head(self):
        for h in ("If-Modified-Since", "If-None-Match"):
            if h in self.headers: del self.headers[h]
        return super().send_head()
    def list_directory(self, path):
        self.send_error(404); return None
    def log_message(self, *a): pass
class Viewer(H):
    ALLOW = {"/": "/index.html", "/index.html": "/index.html", "/manifest.json": "/manifest.json"}
    def send_head(self):
        p = self.path.split("?", 1)[0].split("#", 1)[0]
        if p not in self.ALLOW: self.send_error(404); return None
        self.path = self.ALLOW[p]; return super().send_head()
def run(port, d, cls=H):
    http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(cls, directory=d)).serve_forever()
if __name__ == "__main__":
    base = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    m = json.load(open(os.path.join(ROOT, "manifest.json")))
    for b in m["builds"]:
        threading.Thread(target=run, args=(base + b["port_offset"], os.path.join(ROOT, b["path"])), daemon=True).start()
    print(f"Viewer: open http://localhost:{base}/  (builds on ports {base+1}-{base+len(m['builds'])}; Ctrl+C to stop)", flush=True)
    run(base, ROOT, Viewer)
