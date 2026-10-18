#!/usr/bin/env python3
"""Hidden smoke checks for the blind app bake-off (never shown to the building agent).
usage: check_app.py <todo|notes|units> <app_dir> <screenshot.png> <out.json>
Serves app_dir on a free port, drives the page with Playwright, writes per-check results,
console errors and a 1280x800 screenshot of the app in an identical demo state for every build."""
import json, socket, subprocess, sys, time, re, os
from playwright.sync_api import sync_playwright

app, d, shot, out = sys.argv[1:5]
ZIP = sys.argv[5] if len(sys.argv) > 5 else None          # the label's zip: served bytes must match it
PORT = int(sys.argv[6]) if len(sys.argv) > 6 else None    # the label's own port from the run instructions
if PORT: port = PORT
else:
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
SERVE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "serve.py")
srv = subprocess.Popen([sys.executable, SERVE, d, str(port)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.0)
url = f"http://127.0.0.1:{port}/index.html"
res = {"app": app, "checks": [], "console_errors": [], "page_errors": [], "external_requests": []}
def ck(name, fn):
    try:
        ok = bool(fn())
        res["checks"].append({"name": name, "ok": ok})
    except Exception as e:
        res["checks"].append({"name": name, "ok": False, "error": str(e)[:200]})

try:
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1280, "height": 800})
        pg.on("console", lambda m: m.type == "error" and res["console_errors"].append(m.text[:200]))
        pg.on("pageerror", lambda e: res["page_errors"].append(str(e)[:200]))
        pg.on("request", lambda r: (not r.url.startswith(f"http://127.0.0.1:{port}") and not r.url.startswith("data:"))
              and res["external_requests"].append(r.url[:200]))
        pg.set_default_timeout(4000)
        pg.on("dialog", lambda dlg: dlg.accept())
        served = {}
        def keep(r):
            try:
                if r.url.startswith(f"http://127.0.0.1:{port}/") and r.status == 200: served[r.url.split(f":{port}/", 1)[1].split("?")[0] or "index.html"] = r.body()
            except Exception: pass
        pg.on("response", keep)
        pg.goto(url); pg.wait_for_timeout(500)
        if ZIP:
            import zipfile, urllib.request
            zf = zipfile.ZipFile(ZIP); entries = {n.split("/", 1)[1]: zf.read(n) for n in zf.namelist() if not n.endswith("/")}
            def bytes_match():
                bad = [k for k, v in served.items() if k in entries and entries[k] != v] + [k for k in served if k not in entries]
                for k, v in entries.items():   # fetch every file fresh, outside the browser cache
                    try: got = urllib.request.urlopen(f"http://127.0.0.1:{port}/{k}?fresh={time.time()}").read()
                    except Exception as e: got = None
                    if got != v: bad.append("fresh:" + k)
                res["bytes_mismatch"] = bad; res["browser_loaded"] = sorted(served)
                return not bad and "index.html" in served
            ck("served bytes match the label's zip (browser + fresh fetch)", bytes_match)
        if app == "todo":
            ck("input #new-task exists", lambda: pg.locator("#new-task").count() == 1)
            def add3():
                for t in ["Buy milk", "Write report", "Call mom"]:
                    pg.fill("#new-task", t); pg.press("#new-task", "Enter")
                return pg.locator("#list li").count() == 3
            ck("add 3 tasks with Enter", add3)
            def blank():
                pg.fill("#new-task", "   "); pg.press("#new-task", "Enter")
                return pg.locator("#list li").count() == 3
            ck("blank task not added", blank)
            def toggle():
                pg.locator("#list li").nth(0).locator("input[type=checkbox]").check()
                pg.wait_for_timeout(200)
                return re.search(r"\b2\b", pg.inner_text("#left")) is not None
            ck("checking one task leaves 2", toggle)
            def reload():
                pg.reload(); pg.wait_for_timeout(500)
                return pg.locator("#list li").count() == 3
            ck("tasks survive reload", reload)
            def active():
                pg.get_by_text(re.compile(r"^\s*Active\s*$")).first.click(); pg.wait_for_timeout(200)
                n = sum(1 for i in range(pg.locator("#list li").count()) if pg.locator("#list li").nth(i).is_visible())
                pg.get_by_text(re.compile(r"^\s*All\s*$")).first.click(); pg.wait_for_timeout(200)
                return n == 2
            ck("Active filter shows 2", active)
            def delete():
                li = pg.locator("#list li").nth(2); li.hover()
                btn = li.locator("button").last; btn.click(); pg.wait_for_timeout(200)
                ok = pg.locator("#list li").count() == 2
                pg.fill("#new-task", "Call mom"); pg.press("#new-task", "Enter"); pg.wait_for_timeout(200)
                return ok
            ck("delete a task", delete)
        elif app == "notes":
            ck("editor and preview exist", lambda: pg.locator("textarea#editor").count() == 1 and pg.locator("#preview").count() == 1)
            def render():
                pg.fill("#editor", "# Groceries\n\n**Milk** and *eggs*\n\n- apples\n- bread\n\n`code` and [a link](https://example.com)\n")
                pg.wait_for_timeout(400); pv = pg.locator("#preview")
                return (pv.locator("h1").count() >= 1 and "Groceries" in pv.locator("h1").first.inner_text()
                        and pv.locator("strong").count() >= 1 and pv.locator("em").count() >= 1
                        and pv.locator("li").count() == 2 and pv.locator("code").count() >= 1
                        and pv.locator("a[href='https://example.com']").count() == 1)
            ck("live preview renders the markdown subset", render)
            def xss():
                pg.fill("#editor", "# Test\n<img src=x onerror=\"window.__pwned=1\"><b>hi</b>\n"); pg.wait_for_timeout(500)
                return (pg.evaluate("window.__pwned") is None and pg.locator("#preview img").count() == 0
                        and pg.locator("#preview b").count() == 0)
            ck("typed HTML shown as text, not executed", xss)
            pg.fill("#editor", "# Groceries\n\n**Milk** and *eggs* from the corner shop.\n\n- apples\n- bread\n- `oat milk`\n\nRecipe: [pancakes](https://example.com)\n")
            pg.wait_for_timeout(400)
            def reload():
                pg.reload(); pg.wait_for_timeout(600)
                return "Groceries" in pg.input_value("#editor") or "Groceries" in pg.inner_text("body")
            ck("note survives reload", reload)
            def newnote():
                pg.get_by_text(re.compile(r"new", re.I)).first.click(); pg.wait_for_timeout(300)
                pg.fill("#editor", "# Trip ideas\n\n## Weekend\n\n- *Lisbon* in **spring**\n- hike the coast\n"); pg.wait_for_timeout(400)
                body = pg.inner_text("body")
                return "Groceries" in body and "Trip ideas" in body
            ck("new note; sidebar lists both titles", newnote)
        elif app == "units":
            for sel in ["select#category", "select#from", "select#to", "input#value", "#result"]:
                ck(f"{sel} exists", lambda sel=sel: pg.locator(sel).count() == 1)
            def conv(cat, f, t, v, want):
                pg.select_option("#category", label=cat); pg.wait_for_timeout(200)
                pg.select_option("#from", value=f); pg.select_option("#to", value=t)
                pg.fill("#value", v); pg.wait_for_timeout(300)
                return want in pg.inner_text("#result")
            ck("10 km -> 6.2137 mi", lambda: conv("Length", "km", "mi", "10", "6.2137"))
            ck("100 C -> 212 F", lambda: conv("Temperature", "C", "F", "100", "212"))
            ck("1 lb -> 0.4536 kg", lambda: conv("Weight", "lb", "kg", "1", "0.4536"))
            def empty():
                pg.fill("#value", ""); pg.wait_for_timeout(300)
                txt = pg.inner_text("body")
                return "NaN" not in txt and "undefined" not in txt
            ck("empty input shows no NaN/undefined", empty)
            def swap():
                conv("Length", "km", "mi", "10", "")
                btn = pg.locator("button").filter(has_text=re.compile(r"swap|⇄|↔|⇆|⇅|↕", re.I))
                if btn.count() == 0:
                    btn = pg.locator("button[aria-label*=wap i], button[title*=wap i], #swap")
                btn.first.click(); pg.wait_for_timeout(300)
                ok = pg.input_value("#from") == "mi" and pg.input_value("#to") == "km"
                btn.first.click(); pg.wait_for_timeout(300)
                return ok
            ck("swap exchanges units", swap)
            def typed_change():
                # added after round 1: type by keyboard (input event), fire change too, and require the
                # result to CHANGE to the expected number (catches a converter whose handlers are dead)
                pg.select_option("#category", label="Length"); pg.wait_for_timeout(200)
                pg.select_option("#from", value="m"); pg.select_option("#to", value="ft")
                pg.fill("#value", "1"); pg.wait_for_timeout(200)
                before = pg.inner_text("#result")
                pg.click("#value", click_count=3); pg.keyboard.type("3")
                pg.dispatch_event("#value", "change"); pg.wait_for_timeout(300)
                after = pg.inner_text("#result")
                return after != before and "9.8425" in after
            ck("typed value changes result to expected (3 m -> 9.8425 ft)", typed_change)
            conv("Length", "km", "mi", "10", "")
        pg.wait_for_timeout(300)
        # added after round 1 (Pally m:5a251122): every visible button must change page state when clicked.
        # Each button is tried from a fresh demo state; a button that changes nothing there gets a second
        # chance after each other button has changed the state (e.g. "All" after "Active").
        SNAP = """() => JSON.stringify([document.body.innerHTML, document.documentElement.className, location.hash,
            [...document.querySelectorAll('input,textarea,select')].map(e => [e.value, e.checked]),
            Object.keys(localStorage).sort().map(k => [k, localStorage.getItem(k)])])"""
        BTN = "button:visible, input[type=button]:visible, input[type=submit]:visible, [role=button]:visible"
        def seed():
            pg.evaluate("localStorage.clear()"); pg.goto(url); pg.wait_for_timeout(400)
            if app == "todo":
                for t in ["Buy milk", "Write report", "Call mom"]:
                    pg.fill("#new-task", t); pg.press("#new-task", "Enter")
                pg.locator("#list li").nth(0).locator("input[type=checkbox]").check()
            elif app == "notes":
                pg.fill("#editor", "# Groceries\n\n- apples\n"); pg.wait_for_timeout(200)
            elif app == "units":
                pg.select_option("#category", label="Length"); pg.select_option("#from", value="km"); pg.select_option("#to", value="mi"); pg.fill("#value", "10")
            pg.wait_for_timeout(300)
        def label_of(loc):
            try: return (loc.inner_text() or loc.get_attribute("aria-label") or loc.get_attribute("title") or loc.get_attribute("value") or "?").strip()[:30]
            except Exception: return "?"
        def buttons_all_act():
            seed(); n = min(pg.locator(BTN).count(), 25); dead = []
            for i in range(n):
                seed(); bl = pg.locator(BTN)
                if i >= bl.count(): continue
                b = bl.nth(i); name = label_of(b); before = pg.evaluate(SNAP)
                try: b.click(timeout=2000)
                except Exception: pass
                pg.wait_for_timeout(250)
                if pg.evaluate(SNAP) != before: continue
                ok = False
                # second chance 1: buttons that act on typed input (e.g. "Add") get every empty text field filled first
                seed(); bl = pg.locator(BTN)
                for k in range(pg.locator("input[type=text]:visible, input:not([type]):visible, textarea:visible").count()):
                    f = pg.locator("input[type=text]:visible, input:not([type]):visible, textarea:visible").nth(k)
                    try:
                        if not f.input_value(): f.fill("Sample item")
                    except Exception: pass
                mid = pg.evaluate(SNAP)
                if i < bl.count():
                    try: bl.nth(i).click(timeout=2000)
                    except Exception: pass
                    pg.wait_for_timeout(250)
                    if pg.evaluate(SNAP) != mid: continue
                # second chance 2: after each other button has changed the state
                for j in range(n):
                    if j == i: continue
                    seed(); bl = pg.locator(BTN)
                    if max(i, j) >= bl.count(): continue
                    try: bl.nth(j).click(timeout=2000)
                    except Exception: continue
                    pg.wait_for_timeout(200); bl = pg.locator(BTN)
                    if i >= bl.count(): continue
                    mid = pg.evaluate(SNAP)
                    try: bl.nth(i).click(timeout=2000)
                    except Exception: continue
                    pg.wait_for_timeout(250)
                    if pg.evaluate(SNAP) != mid: ok = True; break
                if not ok: dead.append(name)
            res["buttons_tested"] = n; res["buttons_no_effect"] = dead
            seed()
            return not dead
        ck("every visible button changes page state", buttons_all_act)
        if app == "units": conv("Length", "km", "mi", "10", "")
        # added after round 1: any console error or uncaught page error fails the build, for every app
        ck("no console errors or uncaught page errors", lambda: not res["console_errors"] and not res["page_errors"])
        pg.screenshot(path=shot)
        b.close()
finally:
    srv.terminate(); srv.wait()
res["passed"] = sum(c["ok"] for c in res["checks"]); res["total"] = len(res["checks"])
json.dump(res, open(out, "w"), indent=1)
print(json.dumps({k: res[k] for k in ("passed", "total")}), len(res["console_errors"]) + len(res["page_errors"]), "errors")
