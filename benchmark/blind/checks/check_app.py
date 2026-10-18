#!/usr/bin/env python3
"""Hidden smoke checks for the blind app bake-off (never shown to the building agent).
usage: check_app.py <todo|notes|units> <app_dir> <screenshot.png> <out.json>
Serves app_dir on a free port, drives the page with Playwright, writes per-check results,
console errors and a 1280x800 screenshot of the app in an identical demo state for every build."""
import json, socket, subprocess, sys, time, re, os
from playwright.sync_api import sync_playwright

app, d, shot, out = sys.argv[1:5]
s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
                       cwd=d, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
        pg.goto(url); pg.wait_for_timeout(500)
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
            conv("Length", "km", "mi", "10", "")
        pg.wait_for_timeout(300)
        pg.screenshot(path=shot)
        b.close()
finally:
    srv.terminate(); srv.wait()
res["passed"] = sum(c["ok"] for c in res["checks"]); res["total"] = len(res["checks"])
json.dump(res, open(out, "w"), indent=1)
print(json.dumps({k: res[k] for k in ("passed", "total")}), len(res["console_errors"]) + len(res["page_errors"]), "errors")
