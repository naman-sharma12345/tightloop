#!/usr/bin/env python3
"""No-cache static server for blind judging: python3 serve.py <dir> <port>
Every response carries Cache-Control: no-store and conditional requests are ignored (always 200),
so a browser can never show one build's cached files for another. One port per label."""
import functools, http.server, sys
class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Pragma", "no-cache")
        super().end_headers()
    def send_head(self):
        for h in ("If-Modified-Since", "If-None-Match"):
            if h in self.headers: del self.headers[h]
        return super().send_head()
    def log_message(self, *a): pass
if __name__ == "__main__":
    d, port = sys.argv[1], int(sys.argv[2])
    http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(H, directory=d)).serve_forever()
