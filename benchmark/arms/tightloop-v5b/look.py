#!/usr/bin/env python3
"""look.py: one real-browser self-check of a static web app (tightloop v5b: text only, NO screenshot).
usage: python3 look.py [app_dir]   (default: .)
Serves app_dir on a free localhost port (no-store), opens it in headless
Chromium, and prints at most ~25 lines. Generic checks only (no app-specific
or scoring-checker logic): console/page errors, every visible control used
once with its result (inputs filled + Enter, selects changed, buttons clicked,
confirm() accepted; result = "changed" or "no change"), and horizontal overflow
at 375 px. Writes NO screenshot and no image of any kind; everything is text.
Never edits the app."""
import functools, hashlib, http.server, os, sys, threading
os.environ.pop("FORCE_COLOR", None)
d = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
try:
    from playwright.sync_api import sync_playwright
except Exception:
    print("LOOK UNAVAILABLE: python playwright not importable; check by hand (node --check *.js)"); sys.exit(0)

class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store"); super().end_headers()
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(H, directory=d))
threading.Thread(target=srv.serve_forever, daemon=True).start()
url = "http://127.0.0.1:%d/" % srv.server_address[1]
errs, notes, log, quiet = [], [], [], []
dialogs = [0]
def state(p):
    try:
        return hashlib.md5(p.evaluate("document.body.innerText+JSON.stringify(localStorage)+location.hash+[...document.querySelectorAll('*')].filter(e=>e.offsetParent||e===document.body).length").encode()).hexdigest()
    except Exception:
        return "?"
def label(el):
    try:
        return el.evaluate("e=>e.id?'#'+e.id:JSON.stringify((e.getAttribute('aria-label')||e.innerText||e.value||e.placeholder||e.className||e.tagName).trim().slice(0,24))")
    except Exception:
        return "?"
with sync_playwright() as pw:
    b = pw.chromium.launch()
    p = b.new_page(viewport={"width": 1280, "height": 800})
    p.on("console", lambda m: m.type == "error" and errs.append("console: " + m.text[:120]))
    p.on("pageerror", lambda e: errs.append("pageerror: " + str(e)[:120]))
    p.on("dialog", lambda dl: (dialogs.__setitem__(0, dialogs[0] + 1), dl.accept()))
    p.goto(url); p.wait_for_timeout(400)
    first_text = " ".join(p.evaluate("document.body.innerText").split())[:160]
    groups = ["input:not([type=file]):not([type=hidden]):not([type=checkbox]):not([type=radio]):not([type=submit]):not([type=button]),textarea",
              "select", "input[type=checkbox],input[type=radio]",
              "button,[role=button],input[type=submit],input[type=button],a[href^='#']"]
    n_done = 0
    for g, sel in enumerate(groups):
        for i in range(40):
            els = [e for e in p.query_selector_all(sel) if e.is_visible() and e.is_enabled()]
            if i >= len(els):
                break
            e = els[i]; tag = e.evaluate("e=>e.tagName.toLowerCase()+'/'+(e.type||'')")
            before = state(p); d0 = dialogs[0]; name = label(e); res = "changed"
            try:
                if g == 0:
                    kind = tag.split("/")[1]
                    if e.get_attribute("inputmode") in ("decimal", "numeric"): kind = "number"
                    val = {"number": "12", "date": "2026-01-15", "month": "2026-01", "url": "https://example.com", "email": "a@b.co", "color": "#336699"}.get(kind, "Look test %d" % i)
                    e.fill(val, timeout=800)
                    if not tag.startswith("textarea"): e.press("Enter", timeout=800)
                elif g == 1:
                    opts = e.evaluate("e=>[...e.options].map(o=>o.value)")
                    k = e.evaluate("e=>e.selectedIndex")
                    if len(opts) > 1: e.select_option(opts[(k + 1) % len(opts)], timeout=800)
                else:
                    e.click(timeout=800)
                p.wait_for_timeout(120)
                n_done += 1
                if state(p) == before:
                    res = "no change"; quiet.append(name)
                if dialogs[0] > d0: res += ", confirm() accepted"
                log.append("  %s %s -> %s" % (("type", "select", "check", "click")[g], name, res))
                p.keyboard.press("Escape")
            except Exception as x:
                notes.append("could not use %s (%s)" % (label(e), str(x).split("\n")[0][:60]))
    p.set_viewport_size({"width": 375, "height": 800}); p.wait_for_timeout(250)
    sw = p.evaluate("document.documentElement.scrollWidth")
    b.close()
srv.shutdown()
lines = ["LOOK %s  (%s)" % ("OK" if not (errs or sw > 375) else "ISSUES", d)]
lines.append("errors: %d%s" % (len(errs), "".join("\n  " + x for x in errs[:4])))
lines.append("first load text: " + first_text)
lines.append("controls (%d used; %d with no change):" % (n_done, len(quiet)))
lines += log[:24] + (["  ... %d more" % (len(log) - 24)] if len(log) > 24 else []) + ["  " + x for x in notes[:4]]
lines.append("375px: scrollWidth %d %s" % (sw, "OK" if sw <= 375 else "OVERFLOW"))
lines.append("no screenshot (text-only check)")
print("\n".join(lines))
