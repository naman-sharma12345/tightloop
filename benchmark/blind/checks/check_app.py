#!/usr/bin/env python3
"""Hidden smoke checks for the blind app bake-off (never shown to the building agent).
usage: check_app.py <todo|notes|units|kanban|expenses|bookmarks> <app_dir> <screenshot.png> <out.json>
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
        DLG = {"accept": True, "seen": []}   # native dialogs: accepted unless a check sets accept False; types recorded
        pg.on("dialog", lambda dlg: (DLG["seen"].append(dlg.type), dlg.accept() if DLG["accept"] else dlg.dismiss()))
        served = {}
        def keep(r):
            try:
                if r.url.startswith(f"http://127.0.0.1:{port}/") and r.status == 200: served[r.url.split(f":{port}/", 1)[1].split("?")[0] or "index.html"] = r.body()
            except Exception: pass
        pg.on("response", keep)
        # count the drag-related events the page itself receives (capture phase), so the log says which kind moved a card
        pg.add_init_script("""(() => { window.__dragEv = {}; for (const t of ['pointerdown','mousedown','mousemove','mouseup','pointerup',
            'dragstart','dragover','drop','dragend']) document.addEventListener(t, () => { window.__dragEv[t] = (window.__dragEv[t] || 0) + 1; }, true); })()""")
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
        if app == "kanban":
            ck("input #new-card and the 3 columns exist", lambda: pg.locator("#new-card").count() == 1 and all(pg.locator(f".column[data-col={c}]").count() == 1 for c in ("todo", "doing", "done")))
            col = lambda c: pg.locator(f".column[data-col={c}] .card")
            def add3():
                for t in ["Write spec", "Fix login bug", "Design logo"]:
                    pg.fill("#new-card", t); pg.press("#new-card", "Enter"); pg.wait_for_timeout(150)
                return col("todo").count() == 3
            ck("add 3 cards with Enter (land in To do)", add3)
            def blank():
                pg.fill("#new-card", "   "); pg.press("#new-card", "Enter"); pg.wait_for_timeout(150)
                return pg.locator(".card").count() == 3
            ck("blank card not added", blank)
            # Drag (Pally m:92db7ccb pt 5): try REAL mouse events first (down / stepped moves / up through the browser's
            # input pipeline, which also starts a native HTML5 drag on draggable elements), then, only if the card did not
            # move, synthetic HTML5 drag events (dragstart/dragenter/dragover/drop/dragend sharing one DataTransfer).
            # The move counts if either works; res["drag_method"] records which. BLIND_DRAG_ONLY=pointer|html5 forces one
            # path (self-test only).
            only = os.environ.get("BLIND_DRAG_ONLY", "")
            moved = lambda: col("done").count() == 1 and col("todo").count() == 2
            def drag_pointer():
                src = col("todo").nth(0).bounding_box(); dst = pg.locator(".column[data-col=done]").bounding_box()
                sx, sy = src["x"] + src["width"] / 2, src["y"] + src["height"] / 2
                tx, ty = dst["x"] + dst["width"] / 2, dst["y"] + min(dst["height"] - 10, 120)
                pg.mouse.move(sx, sy); pg.mouse.down(); pg.mouse.move(sx + 8, sy + 8, steps=4)
                pg.mouse.move(tx, ty, steps=15); pg.wait_for_timeout(100); pg.mouse.move(tx, ty + 2, steps=2); pg.mouse.up()
                pg.wait_for_timeout(400)
            def drag_html5():
                pg.evaluate("""() => {
                    const src = document.querySelector('.column[data-col=todo] .card'); const col = document.querySelector('.column[data-col=done]');
                    const r = col.getBoundingClientRect(); const x = r.left + r.width / 2, y = r.top + Math.min(r.height - 10, 120);
                    let dst = document.elementFromPoint(x, y); if (!dst || !col.contains(dst)) dst = col;
                    const dt = new DataTransfer(); const sr = src.getBoundingClientRect();
                    const fire = (el, t, px, py) => el.dispatchEvent(new DragEvent(t, {bubbles: true, cancelable: true, composed: true, dataTransfer: dt, clientX: px, clientY: py}));
                    fire(src, 'dragstart', sr.left + 5, sr.top + 5); fire(dst, 'dragenter', x, y); fire(dst, 'dragover', x, y);
                    fire(dst, 'drop', x, y); fire(src, 'dragend', x, y); }""")
                pg.wait_for_timeout(400)
            ev = lambda: pg.evaluate("() => Object.assign({}, window.__dragEv || {})")
            def drag():
                res["drag_tried"] = []; res["drag_events"] = {}
                if only != "html5":
                    pg.evaluate("() => { window.__dragEv = {}; }")
                    res["drag_tried"].append("pointer"); drag_pointer(); res["drag_events"]["pointer"] = ev()
                    if moved():
                        e_ = res["drag_events"]["pointer"]
                        res["drag_method"] = "pointer (real mouse events" + ("; the page got native HTML5 dragstart/drop from them)" if e_.get("drop") else "; no HTML5 drag events reached the page)")
                        return True
                if only != "pointer" and col("todo").count() == 3:
                    pg.evaluate("() => { window.__dragEv = {}; }")
                    res["drag_tried"].append("html5"); drag_html5(); res["drag_events"]["html5"] = ev()
                    if moved(): res["drag_method"] = "html5 (synthetic dragstart/dragover/drop events)"; return True
                res["drag_method"] = "none"; return False
            ck("drag a card from To do to Done (real mouse events, else HTML5 drag events)", drag)
            def modal():
                col("todo").nth(0).click(); pg.wait_for_timeout(400)
                opened = pg.locator("#card-modal").is_visible()
                fields = all(pg.locator(f"#card-modal {s_}").count() == 1 for s_ in ("#card-title", "#card-desc", "#card-delete"))
                pg.keyboard.press("Escape"); pg.wait_for_timeout(300)
                return opened and fields and not pg.locator("#card-modal").is_visible()
            ck("card click opens #card-modal with #card-title/#card-desc/#card-delete, Escape closes it", modal)
            def del_cancel():
                DLG["accept"] = False; DLG["seen"].clear()
                col("todo").nth(0).click(); pg.wait_for_timeout(300); pg.click("#card-modal #card-delete"); pg.wait_for_timeout(300)
                DLG["accept"] = True; ok = "confirm" in DLG["seen"] and pg.locator(".card").count() == 3
                if pg.locator("#card-modal").is_visible(): pg.keyboard.press("Escape"); pg.wait_for_timeout(300)
                return ok
            ck("card delete asks with native confirm(); Cancel keeps the card", del_cancel)
            def del_accept():
                col("todo").nth(0).click(); pg.wait_for_timeout(300); pg.click("#card-modal #card-delete"); pg.wait_for_timeout(400)
                return pg.locator(".card").count() == 2 and not pg.locator("#card-modal").is_visible()
            ck("card delete, confirmed, removes the card and closes the modal", del_accept)
            def reload():
                pg.reload(); pg.wait_for_timeout(600)
                return pg.locator(".card").count() == 2 and col("done").count() == 1
            ck("board survives reload", reload)
        elif app == "expenses":
            for sel in ["form#expense-form", "#desc", "#amount", "select#category", "#date", "#expenses", "#total", "#chart", "#month", "#export-csv"]:
                ck(f"{sel} exists", lambda sel=sel: pg.locator(sel).count() >= 1)
            rows = lambda: pg.locator("#expenses li, #expenses tr").filter(has_text=re.compile(r"\d"))
            import datetime as _dt
            def month_date():
                # #date is set inside the month the picker shows (Pally m:92db7ccb pt 4), not left to "today"
                today = _dt.date.today(); m = re.search(r"(\d{4})-(\d{2})", pg.input_value("#month") or "")
                ym = m.group(0) if m else today.strftime("%Y-%m"); res["month_shown"] = ym
                return today.isoformat() if ym == today.strftime("%Y-%m") else ym + "-15"
            ck("#month defaults to the current month", lambda: re.search(r"\d{4}-\d{2}", pg.input_value("#month") or "") is not None and month_date().startswith(_dt.date.today().strftime("%Y-%m")))
            def add(d, a, c):
                pg.fill("#desc", d); pg.fill("#amount", a); pg.select_option("#category", value=c)
                try: pg.fill("#date", month_date())
                except Exception as e: res.setdefault("date_fill_errors", []).append(str(e)[:120])
                pg.evaluate("document.querySelector('form#expense-form').requestSubmit()"); pg.wait_for_timeout(250)
            def add3():
                add("Coffee", "4.50", "Food"); add("Bus pass", "2.75", "Transport"); add("Rent", "1200", "Housing")
                return rows().count() == 3
            ck("add 3 expenses (dated inside the shown month)", add3)
            def total_is(v):
                t = pg.inner_text("#total").strip(); res["total_text"] = t
                if re.search(r"[A-Za-z]", t): return False
                n = re.sub(r"[^\d.\-]", "", t)
                return n != "" and abs(float(n) - v) < 0.001
            ck("#total holds only the number 1207.25", lambda: total_is(1207.25))
            def invalid():
                add("", "5", "Food"); add("Bad", "-3", "Food"); add("Bad2", "abc", "Food")
                return rows().count() == 3
            ck("invalid expenses not added", invalid)
            ck("each expense has .edit and .delete buttons", lambda: all(rows().nth(i).locator(".edit").count() >= 1 and rows().nth(i).locator(".delete").count() >= 1 for i in range(rows().count())))
            def edit():
                rows().filter(has_text="Coffee").first.locator(".edit").first.click(); pg.wait_for_timeout(300)
                hit = None
                for f in pg.locator("input:visible").all():
                    try: v = f.input_value()
                    except Exception: continue
                    if re.fullmatch(r"\s*4\.50?\s*", v or ""): hit = f; break
                if hit is None: return False
                hit.fill("5.50"); pg.click("#save-edit"); pg.wait_for_timeout(300)
                return rows().count() == 3 and total_is(1208.25)
            ck(".edit -> change amount 4.50 to 5.50 -> #save-edit updates the total to 1208.25", edit)
            def chart():
                return pg.evaluate("""() => { const c = document.querySelector('#chart'); if (!c) return false;
                    if (c.tagName.toLowerCase() === 'canvas') { const b = document.createElement('canvas'); b.width = c.width; b.height = c.height; return c.toDataURL() !== b.toDataURL(); }
                    return c.querySelectorAll('rect,path,circle,line,polyline,polygon').length > 0; }""")
            ck("#chart has drawn content", chart)
            def csv():
                with pg.expect_download(timeout=3000) as dl: pg.click("#export-csv")
                p_ = dl.value.path(); txt = open(p_).read() if p_ else ""
                return txt.lower().lstrip("\ufeff").startswith("date,description,category,amount") and "Rent" in txt and "1200" in txt
            ck("Export CSV downloads the expenses with the header row", csv)
            def del_cancel():
                DLG["accept"] = False; DLG["seen"].clear()
                rows().filter(has_text="Bus pass").first.locator(".delete").first.click(); pg.wait_for_timeout(300)
                DLG["accept"] = True
                return "confirm" in DLG["seen"] and rows().count() == 3
            ck("delete asks with native confirm(); Cancel keeps the expense", del_cancel)
            def del_accept():
                rows().filter(has_text="Bus pass").first.locator(".delete").first.click(); pg.wait_for_timeout(300)
                return rows().count() == 2 and total_is(1205.50)
            ck("delete, confirmed, removes it and the total becomes 1205.50", del_accept)
            def set_month(ym):
                if pg.evaluate("document.querySelector('#month').tagName.toLowerCase()") == "select":
                    vals = pg.eval_on_selector_all("#month option", "os => os.map(o => o.value)")
                    pg.select_option("#month", value=[v for v in vals if ym in v][0])
                else:
                    pg.fill("#month", ym); pg.dispatch_event("#month", "change")
                pg.wait_for_timeout(400)
            def other_month():
                # (Pally m:c9c6e9cc item 4) pick the PREVIOUS month, add an expense dated inside it, and check that it is saved
                # with that date: it shows in that month's list and total, and not in the current month's.
                t_ = _dt.date.today(); prev = (t_.replace(day=1) - _dt.timedelta(days=1)).strftime("%Y-%m"); cur_ = t_.strftime("%Y-%m")
                set_month(prev); n0 = rows().count()
                add("Old book", "30", "Fun")   # add() sets #date inside the month the picker shows
                res["other_month"] = {"month": prev, "date_set": month_date(), "rows_before": n0, "rows_after": rows().count(), "total_text": pg.inner_text("#total").strip()}
                in_prev = n0 == 0 and rows().count() == 1 and rows().filter(has_text="Old book").count() == 1 and total_is(30)
                set_month(cur_)
                back = rows().count() == 2 and rows().filter(has_text="Old book").count() == 0 and total_is(1205.50)
                res["other_month"].update({"current_rows": rows().count(), "current_total_text": pg.inner_text("#total").strip()})
                return in_prev and back
            ck("#date set inside a chosen past month is saved there: shows in that month's list and total, not in the current month", other_month)
            def reload():
                pg.reload(); pg.wait_for_timeout(600); return rows().count() == 2 and total_is(1205.50)
            ck("expenses survive reload", reload)
        elif app == "bookmarks":
            for sel in ["form#bookmark-form", "#title", "#url", "#tags", "select#folder", "#search", "#export", "#import"]:
                ck(f"{sel} exists", lambda sel=sel: pg.locator(sel).count() >= 1)
            cards = lambda: pg.locator(".bookmark:visible")
            def add(t, u, g):
                pg.fill("#title", t); pg.fill("#url", u); pg.fill("#tags", g)
                pg.evaluate("document.querySelector('form#bookmark-form').requestSubmit()"); pg.wait_for_timeout(250)
            def add3():
                add("GitHub", "https://github.com", "code, work"); add("MDN Web Docs", "https://developer.mozilla.org", "docs, code"); add("Hacker News", "https://news.ycombinator.com", "news")
                return cards().count() == 3
            ck("add 3 bookmarks", add3)
            def invalid():
                add("Broken", "not a url", "x"); return cards().count() == 3
            ck("invalid URL rejected", invalid)
            def search():
                pg.fill("#search", "DOCS"); pg.wait_for_timeout(300); n1 = cards().count()
                pg.fill("#search", ""); pg.wait_for_timeout(300); n2 = cards().count()
                return n1 == 1 and n2 == 3
            ck("search filters by tag/title (case-insensitive) and clears", search)
            ck("each card has .edit and .delete buttons", lambda: all(cards().nth(i).locator(".edit").count() >= 1 and cards().nth(i).locator(".delete").count() >= 1 for i in range(cards().count())))
            def export():
                with pg.expect_download(timeout=3000) as dl: pg.click("#export")
                p_ = dl.value.path(); data = json.load(open(p_)) if p_ else None
                res["export_sample"] = json.dumps(data)[:300]
                return (isinstance(data, list) and len(data) == 3 and "https://github.com" in [str(x.get("url", "")).rstrip("/") for x in data]
                        and all(isinstance(x, dict) and {"title", "url", "tags", "folder"} <= set(x) and isinstance(x["tags"], list)
                                and all(isinstance(t, str) for t in x["tags"]) for x in data))
            ck("Export is a JSON array of {title, url, tags[], folder}", export)
            def imp():
                import tempfile
                fp = os.path.join(tempfile.mkdtemp(), "import.json")
                json.dump([{"title": "GitHub again", "url": "https://github.com", "tags": ["code"], "folder": "Unsorted"},
                           {"title": "Python", "url": "https://www.python.org", "tags": ["lang", "docs"], "folder": "Unsorted"}], open(fp, "w"))
                fi = pg.locator("#import") if pg.locator("input#import[type=file]").count() else pg.locator("#import input[type=file]").first
                fi.set_input_files(fp); pg.wait_for_timeout(600)
                return cards().count() == 4
            ck("Import via #import file input merges, skipping the duplicate URL (3 -> 4)", imp)
            def del_cancel():
                DLG["accept"] = False; DLG["seen"].clear()
                cards().filter(has_text="Hacker News").first.locator(".delete").first.click(); pg.wait_for_timeout(300)
                DLG["accept"] = True
                return "confirm" in DLG["seen"] and cards().count() == 4
            ck("delete asks with native confirm(); Cancel keeps the bookmark", del_cancel)
            def del_accept():
                cards().filter(has_text="Hacker News").first.locator(".delete").first.click(); pg.wait_for_timeout(300)
                return cards().count() == 3
            ck("delete, confirmed, removes the bookmark", del_accept)
            def reload():
                pg.reload(); pg.wait_for_timeout(600); return cards().count() == 3
            ck("bookmarks survive reload", reload)
        pg.wait_for_timeout(300)
        # added after round 1 (Pally m:5a251122): every visible button must change page state when clicked.
        # Each button is tried from a fresh demo state; a button that changes nothing there gets a second
        # chance after each other button has changed the state (e.g. "All" after "Active").
        SNAP = """() => JSON.stringify([document.body.innerHTML, document.documentElement.className, location.hash,
            [...document.querySelectorAll('input,textarea,select')].map(e => [e.value, e.checked]),
            Object.keys(localStorage).sort().map(k => [k, localStorage.getItem(k)])])"""
        fx = {"n": 0}
        for ev in ("download", "popup", "filechooser"): pg.on(ev, lambda *_: fx.__setitem__("n", fx["n"] + 1))
        SNAP0 = SNAP
        def snap(): return pg.evaluate(SNAP0) + str(fx["n"])
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
            elif app == "kanban":
                for t in ["Write spec", "Fix login bug"]:
                    pg.fill("#new-card", t); pg.press("#new-card", "Enter")
            elif app == "expenses":
                for d_, a_, c_ in [("Coffee", "4.50", "Food"), ("Rent", "1200", "Housing")]:
                    pg.fill("#desc", d_); pg.fill("#amount", a_); pg.select_option("#category", value=c_)
                    try: pg.fill("#date", month_date())
                    except Exception: pass
                    pg.evaluate("document.querySelector('form#expense-form').requestSubmit()"); pg.wait_for_timeout(150)
            elif app == "bookmarks":
                for t_, u_, g_ in [("GitHub", "https://github.com", "code"), ("MDN", "https://developer.mozilla.org", "docs")]:
                    pg.fill("#title", t_); pg.fill("#url", u_); pg.fill("#tags", g_)
                    pg.evaluate("document.querySelector('form#bookmark-form').requestSubmit()"); pg.wait_for_timeout(150)
            pg.wait_for_timeout(300)
        def label_of(loc):
            try: return (loc.inner_text() or loc.get_attribute("aria-label") or loc.get_attribute("title") or loc.get_attribute("value") or "?").strip()[:30]
            except Exception: return "?"
        def buttons_all_act():
            seed(); n = min(pg.locator(BTN).count(), 25); dead = []
            for i in range(n):
                seed(); bl = pg.locator(BTN)
                if i >= bl.count(): continue
                b = bl.nth(i); name = label_of(b); before = snap()
                try: b.click(timeout=2000)
                except Exception: pass
                pg.wait_for_timeout(250)
                if snap() != before: continue
                ok = False
                # second chance 1: buttons that act on typed input (e.g. "Add") get every empty text field filled first
                seed(); bl = pg.locator(BTN)
                for k in range(pg.locator("input[type=text]:visible, input:not([type]):visible, textarea:visible").count()):
                    f = pg.locator("input[type=text]:visible, input:not([type]):visible, textarea:visible").nth(k)
                    try:
                        if not f.input_value(): f.fill("Sample item")
                    except Exception: pass
                mid = snap()
                if i < bl.count():
                    try: bl.nth(i).click(timeout=2000)
                    except Exception: pass
                    pg.wait_for_timeout(250)
                    if snap() != mid: continue
                # second chance 2: after each other button has changed the state
                for j in range(n):
                    if j == i: continue
                    seed(); bl = pg.locator(BTN)
                    if max(i, j) >= bl.count(): continue
                    try: bl.nth(j).click(timeout=2000)
                    except Exception: continue
                    pg.wait_for_timeout(200); bl = pg.locator(BTN)
                    if i >= bl.count(): continue
                    mid = snap()
                    try: bl.nth(i).click(timeout=2000)
                    except Exception: continue
                    pg.wait_for_timeout(250)
                    if snap() != mid: ok = True; break
                if not ok: dead.append(name)
            res["buttons_tested"] = n; res["buttons_no_effect"] = dead
            seed()
            return not dead
        ck("every visible button changes page state", buttons_all_act)
        if app == "units": conv("Length", "km", "mi", "10", "")
        # 375 px rule (Pally m:92db7ccb pt 6): at a 375 px wide viewport the page must not scroll sideways:
        # document.documentElement.scrollWidth <= viewport width. A check for the round-2 apps whose spec promises it,
        # except kanban (its board scrolls sideways by design); for the other apps the number is only recorded.
        pg.set_viewport_size({"width": 375, "height": 800}); pg.wait_for_timeout(400)
        w375 = pg.evaluate("() => [document.documentElement.scrollWidth, window.innerWidth]")
        res["w375_scrollWidth_vs_viewport"] = w375
        if app in ("expenses", "bookmarks"):
            ck("375 px wide: no horizontal page scroll (scrollWidth <= viewport)", lambda: w375[0] <= w375[1])
        pg.set_viewport_size({"width": 1280, "height": 800}); pg.wait_for_timeout(300)
        # added after round 1: any console error or uncaught page error fails the build, for every app
        ck("no console errors or uncaught page errors", lambda: not res["console_errors"] and not res["page_errors"])
        pg.screenshot(path=shot)
        b.close()
finally:
    srv.terminate(); srv.wait()
res["passed"] = sum(c["ok"] for c in res["checks"]); res["total"] = len(res["checks"])
json.dump(res, open(out, "w"), indent=1)
print(json.dumps({k: res[k] for k in ("passed", "total")}), len(res["console_errors"]) + len(res["page_errors"]), "errors")
