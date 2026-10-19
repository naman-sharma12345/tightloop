#!/usr/bin/env python3
"""Hidden smoke checks for the v5 blind app run (never shown to the building agent).
usage: check_app_v5.py <habits|recipes|pomodoro> <app_dir> <screenshot.png> <out.json> [zip] [port]
Helpers copied from check_app.py (round 2), which is neither imported nor edited. The page runs on Playwright's fake clock
(UTC, start 2026-03-18 12:00): habits sees a fixed "today"; pomodoro's clock is PAUSED and only moves by clock.run_for,
so every timer check and the demo screenshot are deterministic.
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
        ctx = b.new_context(viewport={"width": 1280, "height": 800}, timezone_id="UTC", locale="en-US")
        pg = ctx.new_page()
        import datetime as _dt0
        T0 = _dt0.datetime(2026, 3, 18, 12, 0, 0, tzinfo=_dt0.timezone.utc)   # a Wednesday; python takes datetimes, not ms
        T1 = T0 + _dt0.timedelta(seconds=1)
        pg.clock.install(time=T0)
        if app == "pomodoro": pg.clock.pause_at(T1)
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
        # seeded Math.random and crypto.randomUUID, reset on every page load: the same steps give the same ids
        pg.add_init_script("""(() => { let s = 20260318; Math.random = () => { s = (s * 1103515245 + 12345) % 2147483648; return s / 2147483648; };
            let u = 0; if (window.crypto && crypto.randomUUID) crypto.randomUUID = () => '00000000-0000-4000-8000-' + String(++u).padStart(12, '0'); })()""")
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
        import datetime as _dt
        TODAY = _dt.date(2026, 3, 18)
        ds = lambda n: (TODAY - _dt.timedelta(days=n)).isoformat()      # n days before today
        POMO = app == "pomodoro"
        def settle(ms=250):
            # pomodoro: the paused fake clock moves only here; other apps: plain wait
            if POMO: pg.clock.run_for(ms); pg.wait_for_timeout(60)
            else: pg.wait_for_timeout(ms)
        def confirm_delete(click, count, before):
            # native confirm(): dismiss must change nothing, accept must delete
            DLG["accept"] = False; DLG["seen"].clear()
            click(); settle(300)
            kept = count() == before
            DLG["accept"] = True
            seen = "confirm" in DLG["seen"]
            click(); settle(300)
            res.setdefault("confirm_log", []).append({"seen": list(DLG["seen"]), "kept_on_dismiss": kept, "after_accept": count()})
            return seen and kept and count() == before - 1
        def num(t):
            m = re.search(r"-?\d+(?:\.\d+)?", t or ""); return float(m.group(0)) if m else None
        if app == "habits":
            for sel in ["form#habit-form", "#habit-name", "select#habit-color", "#prev-week", "#next-week"]:
                ck(f"{sel} exists", lambda sel=sel: pg.locator(sel).count() >= 1)
            ck("colour options are exactly teal, amber, rose, sky, lime, violet",
               lambda: sorted(pg.eval_on_selector_all("select#habit-color option", "o => o.map(x => x.value)")) == sorted(["teal", "amber", "rose", "sky", "lime", "violet"]))
            habits = lambda: pg.locator(".habit")
            row = lambda name: habits().filter(has=pg.locator(".habit-name", has_text=re.compile("^\\s*" + re.escape(name) + "\\s*$")))
            cell = lambda name, date: row(name).locator(f"button.day[data-date='{date}']")
            def add(name, color):
                pg.fill("#habit-name", name); pg.select_option("#habit-color", value=color); pg.press("#habit-name", "Enter"); settle(200)
            def add3():
                add("Read", "teal"); add("Run", "rose"); add("Meditate", "sky")
                return habits().count() == 3 and [row(n).get_attribute("data-color") for n in ("Read", "Run", "Meditate")] == ["teal", "rose", "sky"]
            ck("add 3 habits with name + colour (data-color set)", add3)
            def blank():
                pg.fill("#habit-name", "   "); pg.press("#habit-name", "Enter"); settle(200); return habits().count() == 3
            ck("blank habit not added", blank)
            def grid():
                dates = row("Read").locator("button.day").evaluate_all("e => e.map(x => x.dataset.date)")
                res["habits_grid_dates"] = dates
                return len(dates) == 7 and dates[-1] == ds(0) and dates[0] == ds(6)
            ck("week grid: 7 day buttons, last = today, first = today-6 (data-date)", grid)
            def toggle():
                c = cell("Read", ds(0)); c.click(); settle(200)
                on = "done" in (c.get_attribute("class") or "") and c.get_attribute("aria-pressed") == "true"
                c.click(); settle(200)
                off = "done" not in (c.get_attribute("class") or "") and c.get_attribute("aria-pressed") != "true"
                return on and off
            ck("clicking a day toggles done (class done + aria-pressed) and back", toggle)
            streak = lambda name: num(row(name).locator(".streak").inner_text())
            def streak_ok():
                for n in (1, 2, 4): cell("Read", ds(n)).click(); settle(150)
                a = streak("Read")                    # yesterday + day before, gap at -3: 2 (today not done yet)
                cell("Read", ds(0)).click(); settle(150)
                b_ = streak("Read")                   # today done: 3
                res["streak_seen"] = [a, b_]
                return a == 2 and b_ == 3
            ck("streak = consecutive done days ending today (or yesterday): 2, then 3 with today", streak_ok)
            def weeks():
                for n in range(1, 7): cell("Run", ds(n)).click(); settle(100)
                pg.click("#prev-week"); settle(200)
                last_prev = row("Run").locator("button.day").last.get_attribute("data-date")
                for n in (7, 8): cell("Run", ds(n)).click(); settle(100)
                pg.click("#next-week"); settle(200)
                try: pg.click("#next-week", timeout=1000)
                except Exception: pass
                settle(200)
                last_now = row("Run").locator("button.day").last.get_attribute("data-date")
                res["weeks_seen"] = [last_prev, last_now, streak("Run")]
                return last_prev == ds(7) and last_now == ds(0) and streak("Run") == 8
            ck("prev/next week move 7 days (not past today); streak counts across weeks (8)", weeks)
            def rename():
                row("Meditate").locator(".edit").click(); settle(200)
                r_ = habits().locator(".rename"); r_.fill("Meditate 10 min"); r_.press("Enter"); settle(200)
                return row("Meditate 10 min").count() == 1 and row("Meditate").count() == 0
            ck("rename a habit via .edit -> .rename + Enter", rename)
            def typed():
                pg.click("#habit-name"); pg.keyboard.type("Stretch", delay=20); pg.keyboard.press("Enter"); settle(200)
                return row("Stretch").count() == 1 and habits().count() == 4
            ck("typing a name with the keyboard + Enter adds it", typed)
            ck("delete asks with native confirm(); cancel keeps, OK deletes",
               lambda: confirm_delete(lambda: row("Stretch").locator(".delete").click(), lambda: habits().count(), 4))
            def reload():
                before = {n: (row(n).locator("button.day.done").evaluate_all("e => e.map(x => x.dataset.date)"), streak(n)) for n in ("Read", "Run")}
                pg.reload(); settle(600)
                after = {n: (row(n).locator("button.day.done").evaluate_all("e => e.map(x => x.dataset.date)"), streak(n)) for n in ("Read", "Run")}
                res["reload_habits"] = [before, after]
                return habits().count() == 3 and row("Meditate 10 min").count() == 1 and before == after and len(after["Read"][0]) == 4
            ck("habits, done days and streaks survive reload", reload)
        elif app == "recipes":
            for sel in ["form#recipe-form", "#recipe-title", "#recipe-servings", "#recipe-tags", "#recipe-ingredients", "#recipe-steps",
                        "#save-recipe", "#recipes", "#recipe-detail", "#search", "select#tag-filter"]:
                ck(f"{sel} exists", lambda sel=sel: pg.locator(sel).count() >= 1)
            cards = lambda: pg.locator("#recipes .recipe")
            vis = lambda: pg.locator("#recipes .recipe:visible")
            card = lambda t: cards().filter(has=pg.locator(".recipe-title", has_text=re.compile("^\\s*" + re.escape(t) + "\\s*$")))
            def add(t, s_, tags, ing, steps):
                pg.fill("#recipe-title", t); pg.fill("#recipe-servings", s_); pg.fill("#recipe-tags", tags)
                pg.fill("#recipe-ingredients", ing); pg.fill("#recipe-steps", steps); pg.click("#save-recipe"); settle(250)
            R3 = [("Pancakes", "4", "breakfast, sweet", "200 g flour\n1/2 cup milk\n2 eggs\n1.5 tbsp sugar\nsalt to taste", "Mix everything\nCook on a hot pan"),
                  ("Tomato soup", "2", "dinner, vegan", "6 tomatoes\n1 onion\n500 ml stock", "Chop\nSimmer 20 minutes"),
                  ("Green salad", "1", "vegan, lunch", "1 head lettuce\n0.5 cucumber\nolive oil", "Toss")]
            def add3():
                for r_ in R3: add(*r_)
                return cards().count() == 3
            ck("add 3 recipes", add3)
            def invalid():
                add("", "2", "x", "1 egg", "Boil"); a = cards().count()
                add("Bad servings", "0", "x", "1 egg", "Boil"); b_ = cards().count()
                pg.fill("#recipe-title", ""); pg.fill("#recipe-servings", ""); pg.fill("#recipe-tags", ""); pg.fill("#recipe-ingredients", ""); pg.fill("#recipe-steps", "")
                return a == 3 and b_ == 3
            ck("no title / servings 0 are rejected (nothing added)", invalid)
            def detail():
                card("Pancakes").locator(".recipe-title").click(); settle(300)
                D = pg.locator("#recipe-detail")
                return D.is_visible() and D.locator("li.ingredient").count() == 5 and "Cook on a hot pan" in D.inner_text() \
                    and pg.input_value("#scale-servings") == "4"
            ck("clicking a card opens #recipe-detail (5 ingredients, steps, scaler = 4)", detail)
            def qtys(): return [num(t) for t in pg.locator("#recipe-detail li.ingredient .qty").all_inner_texts()]
            def scaler():
                pg.click("#scale-servings", click_count=3); pg.keyboard.press("Control+A"); pg.keyboard.type("6", delay=30); pg.keyboard.press("Tab"); settle(300)
                six = qtys()
                pg.click("#scale-servings", click_count=3); pg.keyboard.press("Control+A"); pg.keyboard.type("2", delay=30); pg.keyboard.press("Tab"); settle(300)
                two = qtys()
                salt = pg.locator("#recipe-detail li.ingredient", has_text="salt to taste").count() == 1
                res["scaler_seen"] = {"6": six, "2": two, "salt_line": salt}
                return six == [300, 0.75, 3, 2.25] and two == [100, 0.25, 1, 0.75] and salt
            ck("typing servings 6 then 2 rescales (300/0.75/3/2.25, 100/0.25/1/0.75; 'salt to taste' unchanged)", scaler)
            def search():
                pg.fill("#search", "FLOUR"); settle(250); a = [t.strip() for t in vis().locator(".recipe-title").all_inner_texts()]
                pg.fill("#search", "soup"); settle(250); b_ = [t.strip() for t in vis().locator(".recipe-title").all_inner_texts()]
                pg.fill("#search", ""); settle(250); c_ = vis().count()
                res["search_seen"] = [a, b_, c_]
                return a == ["Pancakes"] and b_ == ["Tomato soup"] and c_ == 3
            ck("search filters by ingredient and title, case-insensitive", search)
            def tagf():
                vals = pg.eval_on_selector_all("select#tag-filter option", "o => o.map(x => x.value)")
                pg.select_option("#tag-filter", value="vegan"); settle(250); a = sorted(t.strip() for t in vis().locator(".recipe-title").all_inner_texts())
                pg.select_option("#tag-filter", value=""); settle(250); c_ = vis().count()
                res["tag_seen"] = [vals, a, c_]
                return vals[:1] == [""] and set(vals[1:]) == {"breakfast", "sweet", "dinner", "vegan", "lunch"} and a == ["Green salad", "Tomato soup"] and c_ == 3
            ck("tag filter ('' + one option per tag) narrows to that tag", tagf)
            def edit():
                card("Tomato soup").locator(".edit").click(); settle(250)
                loaded = pg.input_value("#recipe-title") == "Tomato soup"
                pg.fill("#recipe-title", "Spicy tomato soup"); pg.fill("#recipe-servings", "3"); pg.click("#save-recipe"); settle(300)
                return loaded and cards().count() == 3 and card("Spicy tomato soup").count() == 1 and card("Tomato soup").count() == 0
            ck("edit loads the recipe into the form and saves over it", edit)
            add("Toast", "1", "breakfast", "2 slices bread", "Toast it")
            ck("delete asks with native confirm(); cancel keeps, OK deletes",
               lambda: confirm_delete(lambda: card("Toast").locator(".delete").click(), lambda: cards().count(), 4))
            def reload():
                pg.reload(); settle(600)
                return cards().count() == 3 and card("Spicy tomato soup").count() == 1 and card("Pancakes").count() == 1
            ck("recipes survive reload", reload)
        elif app == "pomodoro":
            for sel in ["#time", "#mode", "#start", "#pause", "#reset", "#focus-min", "#short-min", "#long-min", "form#task-form",
                        "#task-input", "#history", "#clear-history"]:
                ck(f"{sel} exists", lambda sel=sel: pg.locator(sel).count() >= 1)
            tm = lambda: pg.inner_text("#time").strip()
            secs = lambda: (lambda m: int(m.group(1)) * 60 + int(m.group(2)) if m else None)(re.fullmatch(r"(\d{2}):(\d{2})", tm()))
            mode = lambda: pg.get_attribute("#mode", "data-mode")
            hist = lambda: pg.locator("#history li[data-mode]")
            tasks = lambda: pg.locator(".task")
            task = lambda t: tasks().filter(has=pg.locator(".task-name", has_text=re.compile("^\\s*" + re.escape(t) + "\\s*$")))
            ck("defaults: 25:00, focus, 25/5/15", lambda: tm() == "25:00" and mode() == "focus" and
               [pg.input_value(x) for x in ("#focus-min", "#short-min", "#long-min")] == ["25", "5", "15"])
            def typed():
                pg.click("#focus-min"); pg.keyboard.press("Control+A"); pg.keyboard.type("1", delay=30); pg.keyboard.press("Tab"); settle(300)
                ok = tm() == "01:00"
                for sel, v in (("#short-min", "1"), ("#long-min", "2")):
                    pg.click(sel); pg.keyboard.press("Control+A"); pg.keyboard.type(v, delay=30); pg.keyboard.press("Tab"); settle(200)
                return ok
            ck("typing focus 1 min while stopped shows 01:00 at once", typed)
            def tasks_ok():
                for t in ("Write report", "Email Sam"):
                    pg.fill("#task-input", t); pg.press("#task-input", "Enter"); settle(200)
                pg.fill("#task-input", "   "); pg.press("#task-input", "Enter"); settle(200)
                task("Email Sam").locator(".task-name").click(); settle(200)
                act = [t.strip() for t in pg.locator(".task.active .task-name").all_inner_texts()]
                return tasks().count() == 2 and act == ["Email Sam"]
            ck("add 2 tasks (blank ignored); clicking one makes it the only .active", tasks_ok)
            def start():
                pg.click("#start"); settle(3000); s_ = secs(); res["after_3s"] = tm(); return s_ is not None and 56 <= s_ <= 58
            ck("start counts down (01:00 -> 00:56..00:58 after 3 s)", start)
            def pause():
                pg.click("#pause"); settle(200); a = tm(); settle(5000); return tm() == a
            ck("pause stops the countdown", pause)
            def reset():
                pg.click("#reset"); settle(200); a = tm(); settle(3000); return a == "01:00" and tm() == "01:00"
            ck("reset returns to the full duration and stays stopped", reset)
            seq = []
            def run_until(cond, max_s):
                t = 0
                while t < max_s and not cond():
                    settle(5000); t += 5
                    if mode() and (not seq or seq[-1] != mode()): seq.append(mode())
                return cond()
            def auto():
                pg.click("#start"); seq.append(mode())
                run_until(lambda: mode() != "focus", 75)
                a = secs(); settle(3000); b_ = secs()
                res["auto_seen"] = [mode(), a, b_]
                return mode() == "short" and a is not None and b_ is not None and b_ < a
            ck("at 00:00 focus auto-advances to short break and keeps running", auto)
            ck("history gets one li[data-mode=focus] per finished focus",
               lambda: hist().count() == 1 and hist().first.get_attribute("data-mode") == "focus")
            def count_ok():
                c = [num(task(t).locator(".count").inner_text()) for t in ("Email Sam", "Write report")]
                res["count_seen"] = c; return c == [1, 0]
            ck("a finished focus adds 1 to the active task's .count only", count_ok)
            def long_ok():
                run_until(lambda: mode() == "long", 600)
                modes = hist().evaluate_all("e => e.map(x => x.dataset.mode)")
                res["mode_seq"] = seq; res["history_modes"] = modes
                pg.click("#pause"); settle(200)
                return seq == ["focus", "short", "focus", "short", "focus", "short", "focus", "long"] and \
                    sorted(modes) == sorted(["focus"] * 4 + ["short"] * 3)
            ck("long break after the 4th focus (any break back to focus); history has all 7", long_ok)
            def reload():
                before = ([num(task(t).locator(".count").inner_text()) for t in ("Email Sam", "Write report")], hist().count())
                pg.reload(); settle(600)
                after = ([num(task(t).locator(".count").inner_text()) for t in ("Email Sam", "Write report")], hist().count())
                act = [t.strip() for t in pg.locator(".task.active .task-name").all_inner_texts()]
                res["reload_pomo"] = [before, after, act, pg.input_value("#focus-min")]
                return before == after and act == ["Email Sam"] and pg.input_value("#focus-min") == "1" and tasks().count() == 2
            ck("settings, tasks, active task, counts and history survive reload", reload)
            ck("task delete asks with native confirm(); cancel keeps, OK deletes",
               lambda: confirm_delete(lambda: task("Write report").locator(".delete").click(), lambda: tasks().count(), 2))
            def clear():
                n0 = hist().count(); DLG["accept"] = False; DLG["seen"].clear(); pg.click("#clear-history"); settle(300)
                kept = hist().count() == n0; seen = "confirm" in DLG["seen"]; DLG["accept"] = True
                pg.click("#clear-history"); settle(300)
                return n0 > 0 and kept and seen and hist().count() == 0
            ck("clear history asks with native confirm(); cancel keeps, OK clears", clear)
        settle(300)
        # every visible button must change page state when clicked (copied from check_app.py round 2; pomodoro compares
        # against a replay of the same steps WITHOUT the click, since its display moves with the clock).
        SNAP = """() => JSON.stringify([document.body.innerHTML, document.documentElement.className, location.hash,
            [...document.querySelectorAll('input,textarea,select')].map(e => [e.value, e.checked]),
            Object.keys(localStorage).sort().map(k => [k, localStorage.getItem(k)])])"""
        fx = {"n": 0}
        for ev in ("download", "popup", "filechooser"): pg.on(ev, lambda *_: fx.__setitem__("n", fx["n"] + 1))
        def snap(): return pg.evaluate(SNAP) + str(fx["n"])
        BTN = "button:visible, input[type=button]:visible, input[type=submit]:visible, [role=button]:visible"
        TXT = "input[type=text]:visible, input:not([type]):visible, textarea:visible"
        def seed():
            pg.evaluate("localStorage.clear()")
            if POMO: pg.clock.set_system_time(T1)   # same fake start time for every replay (history timestamps)
            pg.goto(url); settle(400)
            if app == "habits":
                for n_, c_ in (("Read", "teal"), ("Run", "rose")):
                    pg.fill("#habit-name", n_); pg.select_option("#habit-color", value=c_); pg.press("#habit-name", "Enter"); settle(150)
                for n_ in (0, 1, 2):
                    pg.locator(".habit").first.locator(f"button.day[data-date='{ds(n_)}']").click(); settle(100)
            elif app == "recipes":
                for t_, s_, g_, i_, st_ in (("Pancakes", "4", "breakfast", "200 g flour\n2 eggs", "Mix\nCook"),
                                            ("Tomato soup", "2", "dinner", "6 tomatoes\n1 onion", "Simmer")):
                    pg.fill("#recipe-title", t_); pg.fill("#recipe-servings", s_); pg.fill("#recipe-tags", g_)
                    pg.fill("#recipe-ingredients", i_); pg.fill("#recipe-steps", st_); pg.click("#save-recipe"); settle(200)
            elif app == "pomodoro":
                for sel, v in (("#focus-min", "1"), ("#short-min", "1"), ("#long-min", "2")):
                    pg.fill(sel, v); pg.press(sel, "Tab"); settle(100)
                for t_ in ("Write report", "Email Sam"):
                    pg.fill("#task-input", t_); pg.press("#task-input", "Enter"); settle(100)
                try: pg.click("#start", timeout=2000)
                except Exception: pass
                settle(62000)
                try: pg.click("#pause", timeout=2000)
                except Exception: pass
            settle(300)
        def label_of(loc):
            try: return (loc.inner_text() or loc.get_attribute("aria-label") or loc.get_attribute("title") or loc.get_attribute("value") or "?").strip()[:30]
            except Exception: return "?"
        def fill_empty():
            for k in range(pg.locator(TXT).count()):
                f = pg.locator(TXT).nth(k)
                try:
                    if not f.input_value(): f.fill("Sample item")
                except Exception: pass
        LBL = "e => e.map(x => (x.innerText || x.getAttribute('aria-label') || x.getAttribute('title') || x.value || '?').trim().slice(0, 30))"
        def labels_now(): return pg.locator(BTN).evaluate_all(LBL)
        KEYS = []   # per button of the seed state: (label, occurrence among equal labels); found again by that, not by index,
                    # because a prefix click can show or hide other buttons and shift the indices
        def click_nth(i):
            lab, occ = KEYS[i]; hits = [k for k, x in enumerate(labels_now()) if x == lab]
            if occ >= len(hits): return False
            try: pg.locator(BTN).nth(hits[occ]).click(timeout=2000)
            except Exception: pass
            return True
        LAST = {}
        def diff(a, b):
            if a == b: return False
            k = next((x for x in range(min(len(a), len(b))) if a[x] != b[x]), min(len(a), len(b)))
            LAST["where"] = [a[max(0, k - 60):k + 60], b[max(0, k - 60):k + 60]]
            return True
        BASES = {}
        def acts(i, prefix, key):
            # state after (seed, prefix, click i, settle) differs from state without the click
            if POMO and key in BASES:
                base = BASES[key]
                if base is None:            # not replay-deterministic: before/after on one run
                    seed(); prefix(); settle(250); before = snap()
                    if not click_nth(i): return False
                    settle(250); return diff(before, snap())
                seed(); prefix()
                if not click_nth(i): return False
                settle(250); return diff(base, snap())
            seed(); prefix()
            if not POMO:
                before = snap()
                if not click_nth(i): return False
                settle(250); return diff(before, snap())
            settle(250); base = snap()
            seed(); prefix(); settle(250); base2 = snap()
            BASES[key] = base if base2 == base else None     # the no-click state is the same for every button
            if base2 != base:
                # the app is not replay-deterministic (e.g. random ids): fall back to before/after on one run
                res["replay_nondeterministic"] = True
                if not click_nth(i): return False
                settle(250); return diff(base2, snap())
            seed(); prefix()
            if not click_nth(i): return False
            settle(250); return diff(base, snap())
        def buttons_all_act():
            seed(); labels = labels_now()[:25]; n = len(labels); dead = []; how = res["buttons_how"] = []
            KEYS[:] = [(l, labels[:k].count(l)) for k, l in enumerate(labels)]
            for i in range(n):
                if acts(i, lambda: None, "none"): how.append([labels[i], "direct", LAST.get("where")]); continue
                if acts(i, fill_empty, "fill"): how.append([labels[i], "after filling empty text fields", LAST.get("where")]); continue
                ok = False
                for j in range(n):                       # second chance 2: after each other button has changed the state
                    if j == i: continue
                    def pre(j=j):
                        click_nth(j); settle(200)
                    if acts(i, pre, f"after:{j}"): ok = True; how.append([labels[i], "after " + labels[j], LAST.get("where")]); break
                if not ok:
                    dead.append(labels[i])
            res["buttons_tested"] = n; res["buttons_no_effect"] = dead
            seed()
            return not dead
        ck("every visible button changes page state", buttons_all_act)
        pg.set_viewport_size({"width": 375, "height": 800}); pg.wait_for_timeout(400)
        w375 = pg.evaluate("() => [document.documentElement.scrollWidth, window.innerWidth]")
        res["w375_scrollWidth_vs_viewport"] = w375
        ck("375 px wide: no horizontal page scroll (scrollWidth <= viewport)", lambda: w375[0] <= w375[1])
        pg.set_viewport_size({"width": 1280, "height": 800}); pg.wait_for_timeout(300)
        ck("no external network requests", lambda: not res["external_requests"])
        ck("no console errors or uncaught page errors", lambda: not res["console_errors"] and not res["page_errors"])
        pg.screenshot(path=shot)
        b.close()
finally:
    srv.terminate(); srv.wait()
res["passed"] = sum(c["ok"] for c in res["checks"]); res["total"] = len(res["checks"])
json.dump(res, open(out, "w"), indent=1)
print(json.dumps({k: res[k] for k in ("passed", "total")}), len(res["console_errors"]) + len(res["page_errors"]), "errors")
