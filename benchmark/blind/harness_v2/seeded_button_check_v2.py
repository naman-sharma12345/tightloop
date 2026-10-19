#!/usr/bin/env python3
"""APP HARNESS v2: seeded button re-check (Naman m:35fb98df + m:afb27807). A NEW, separate script; check_app_v2.py is
untouched. Run ONCE on all 9 no-skill builds with IDENTICAL steps: no per-build code, no per-build tweaks.

Why: check_app_v2.py reseeds before every click, but its seed() has no branch for the r11 specs (habits, invoice, trip),
so those apps start EMPTY and Undo / Redo / Export have nothing to act on.

SEED STEPS (identical for every build):
  1. localStorage.clear(); load index.html; wait 400 ms.
  2. For each visible <form>, in page order: fill every visible, enabled, EMPTY field:
       text/search/other -> "Sample item"; textarea -> "Sample note"; number/range -> "5" (or its min if min > 0);
       date -> today (YYYY-MM-DD); time -> "10:00"; datetime-local -> today + "T10:00"; month -> YYYY-MM;
       email -> "sam@example.com"; url -> "https://example.com/"; tel -> "5551234";
       select left on its placeholder -> its first non-empty option. Checkbox/radio/file/color are left alone.
     Then submit that form (requestSubmit); wait 300 ms. The first form whose submit changes the page state is the seed;
     else reload (step 1) and try the next form.
  2b. If none did: for each visible button whose label matches (^|\b)(add|new)\b or starts with "+", in page order:
     reload (step 1), click it, wait 300 ms, then do step 2 on the forms now visible. The first that changes the state wins.
  3. If still none: fill the same way every field on the page, press Enter in the first text input.
  The page state = body HTML + <html> class + location.hash + every input value/checked + all localStorage
  + the count of downloads, popups and file choosers (the same snapshot check_app_v2.py uses).

BUTTON RULES (every visible button, same selector and 25-button cap as check_app_v2.py, in page order after the seed):
  Undo (label matches \bundo\b): seed, click Undo -> seeded-pass if the state changes.
  Redo (\bredo\b): seed, click the first Undo button, then click Redo -> seeded-pass if Redo changes the state.
  Export (\bexport\b) and every other button: seed, then click -> seeded-pass if the state changes.
  Undo / Redo / Export with no such button on the page: not-applicable.
  Dialogs answered like check_app_v2.py: prompt OK with text, confirm OK, alert dismissed.
  For a seeded-fail on an "other" button, the checker's two second chances are also tried and reported as a note only
  (rescued_by_checker_second_chance); the verdict stays the rule above.

usage: seeded_button_check_v2.py <app_dir> <out.json>
       seeded_button_check_v2.py --all <outputs_root> <results_dir>   (every build dir, each in its own no-network bwrap)
No network: --all runs each build inside bwrap --unshare-net (serve.py on 127.0.0.1 inside); any page request off
127.0.0.1 is also aborted and recorded.
"""
import json, os, socket, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
SERVE = os.path.join(os.path.dirname(HERE), "serve.py")

def run_one(d, out):
    from playwright.sync_api import sync_playwright
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    srv = subprocess.Popen([sys.executable, SERVE, d, str(port)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.0)
    url = f"http://127.0.0.1:{port}/index.html"
    res = {"app_dir": d, "blocked_requests": [], "console_errors": [], "page_errors": [], "dialogs": []}
    try:                                   # proof of no network: an outside connect must fail here
        socket.create_connection(("1.1.1.1", 443), timeout=3).close(); res["outside_connect"] = "REACHABLE"
    except OSError as e: res["outside_connect"] = "blocked (" + e.__class__.__name__ + ")"
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 1280, "height": 800})
            def route(r):
                if r.request.url.startswith(f"http://127.0.0.1:{port}") or r.request.url.startswith("data:") or r.request.url.startswith("blob:"):
                    r.continue_()
                else:
                    res["blocked_requests"].append(r.request.url[:200]); r.abort()
            pg.route("**/*", route)
            pg.on("console", lambda m: m.type == "error" and res["console_errors"].append(m.text[:200]))
            pg.on("pageerror", lambda e: res["page_errors"].append(str(e)[:200]))
            pg.set_default_timeout(4000)
            def on_dialog(dlg):   # same answers as check_app_v2.py (prompt: OK with text, alert dismissed, confirm OK)
                t_ = dlg.type
                try:
                    if t_ == "prompt": dlg.accept((dlg.default_value + " 2") if dlg.default_value else "Test item"); a = "OK"
                    elif t_ == "alert": dlg.dismiss(); a = "dismissed"
                    else: dlg.accept(); a = "OK"
                except Exception as e_: a = "error"
                if len(res["dialogs"]) < 100: res["dialogs"].append({"type": t_, "message": (dlg.message or "")[:80], "answer": a})
            pg.on("dialog", on_dialog)
            SNAP = """() => JSON.stringify([document.body.innerHTML, document.documentElement.className, location.hash,
                [...document.querySelectorAll('input,textarea,select')].map(e => [e.value, e.checked]),
                Object.keys(localStorage).sort().map(k => [k, localStorage.getItem(k)])])"""
            fx = {"n": 0}
            for ev in ("download", "popup", "filechooser"): pg.on(ev, lambda *_: fx.__setitem__("n", fx["n"] + 1))
            def snap(): return pg.evaluate(SNAP) + str(fx["n"])
            BTN = "button:visible, input[type=button]:visible, input[type=submit]:visible, [role=button]:visible"
            FILL = """(root) => {
                const today = new Date().toISOString().slice(0, 10), filled = [];
                const els = [...root.querySelectorAll('input, textarea, select')].filter(e => e.offsetParent !== null && !e.disabled && !e.readOnly);
                for (const e of els) {
                    const t = (e.getAttribute('type') || (e.tagName === 'SELECT' ? 'select' : e.tagName === 'TEXTAREA' ? 'textarea' : 'text')).toLowerCase();
                    if (['checkbox','radio','file','hidden','submit','button','reset','image','color'].includes(t)) continue;
                    if (t === 'select') {
                        const opts = [...e.options].filter(o => o.value !== '' && !o.disabled);
                        if (opts.length && (e.value === '' || e.selectedIndex <= 0)) { e.value = opts[0].value; filled.push('select'); }
                        else continue;
                    } else {
                        if (e.value) continue;
                        let v = 'Sample item';
                        if (t === 'number' || t === 'range') v = e.min && Number(e.min) > 0 ? e.min : '5';
                        else if (t === 'date') v = today; else if (t === 'time') v = '10:00';
                        else if (t === 'datetime-local') v = today + 'T10:00'; else if (t === 'month') v = today.slice(0, 7);
                        else if (t === 'email') v = 'sam@example.com'; else if (t === 'url') v = 'https://example.com/';
                        else if (t === 'tel') v = '5551234'; else if (t === 'textarea') v = 'Sample note';
                        const proto = e.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
                        Object.getOwnPropertyDescriptor(proto, 'value').set.call(e, v); filled.push(t);
                    }
                    e.dispatchEvent(new Event('input', {bubbles: true})); e.dispatchEvent(new Event('change', {bubbles: true}));
                }
                return filled; }"""
            SEED = {"how": None}
            def fresh():
                pg.evaluate("localStorage.clear()"); pg.goto(url); pg.wait_for_timeout(400)
            ADD_RE = r"(^|\b)(add|new)\b|^\s*\+"
            def try_forms(before, opener):
                nf = pg.locator("form").count()
                for k in range(nf):
                    f = pg.locator("form").nth(k)
                    try:
                        if not f.is_visible(): continue
                        filled = f.evaluate(FILL)
                        f.evaluate("f => f.requestSubmit ? f.requestSubmit() : f.submit()")
                    except Exception: continue
                    pg.wait_for_timeout(300)
                    if snap() != before:
                        return {"opened_with_button": opener, "form_index": k, "forms_on_page": nf, "fields_filled": filled, "changed_state": True}
                    fresh(); before = snap()
                    if opener is not None: return None      # the opener's form was tried; the caller reopens for the next opener
                return None
            def seed(record=False):
                fresh(); before = snap()
                how = try_forms(before, None)                                   # step 2: forms visible on load
                if how is None:                                                 # step 2b: forms behind an Add/New/+ button
                    names = [label_of(pg.locator(BTN).nth(q)) for q in range(min(pg.locator(BTN).count(), 25))]
                    for q, nm in enumerate(names):
                        if not __import__("re").search(ADD_RE, nm, __import__("re").I): continue
                        fresh(); before = snap()
                        try: pg.locator(BTN).nth(q).click(timeout=2000)
                        except Exception: continue
                        pg.wait_for_timeout(300); before = snap()
                        how = try_forms(before, nm)
                        if how is not None: break
                if how is None:                                                 # step 3: fields outside forms + Enter
                    fresh(); before = snap()
                    try:
                        filled = pg.evaluate("(FILL) => (new Function('return ' + FILL))()(document.body)", FILL)
                        tl = pg.locator("input[type=text]:visible, input:not([type]):visible")
                        if tl.count(): tl.first.press("Enter")
                    except Exception: filled = []
                    pg.wait_for_timeout(300)
                    how = {"opened_with_button": None, "form_index": None, "fields_filled": filled, "changed_state": snap() != before,
                           "note": "no form submit changed the state; filled fields on the page and pressed Enter"}
                if record: SEED["how"] = how
                return how["changed_state"]
            def label_of(loc):
                try: return (loc.inner_text() or loc.get_attribute("aria-label") or loc.get_attribute("title") or loc.get_attribute("value") or "?").strip()[:30]
                except Exception: return "?"
            pg.goto(url); pg.wait_for_timeout(400)
            seed(record=True); res["seed"] = SEED["how"]
            import re as _re
            def kind(name):
                if _re.search(r"\bundo\b", name, _re.I): return "undo"
                if _re.search(r"\bredo\b", name, _re.I): return "redo"
                if _re.search(r"\bexport\b", name, _re.I): return "export"
                return "other"
            n = min(pg.locator(BTN).count(), 25); results = []
            def click_i(i):
                bl = pg.locator(BTN)
                if i >= bl.count(): return False
                try: bl.nth(i).click(timeout=2000)
                except Exception: pass
                pg.wait_for_timeout(250); return True
            for i in range(n):
                seed(); bl = pg.locator(BTN)
                if i >= bl.count(): continue
                name = label_of(bl.nth(i)); k = kind(name); ent = {"index": i, "label": name, "kind": k}
                if k == "redo":
                    undo_i = next((j for j in range(min(bl.count(), 25)) if kind(label_of(bl.nth(j))) == "undo"), None)
                    ent["undo_clicked_first"] = undo_i is not None
                    if undo_i is not None: click_i(undo_i)
                    if i >= pg.locator(BTN).count(): ent["verdict"] = "seeded-fail"; ent["why"] = "button gone after Undo"; results.append(ent); continue
                before = snap(); click_i(i)
                ent["verdict"] = "seeded-pass" if snap() != before else "seeded-fail"
                if ent["verdict"] == "seeded-fail" and k == "other":
                    ok = False
                    seed(); bl = pg.locator(BTN)
                    for q in range(pg.locator("input[type=text]:visible, input:not([type]):visible, textarea:visible").count()):
                        f = pg.locator("input[type=text]:visible, input:not([type]):visible, textarea:visible").nth(q)
                        try:
                            if not f.input_value(): f.fill("Sample item")
                        except Exception: pass
                    mid = snap()
                    if click_i(i) and snap() != mid: ok = True
                    if not ok:
                        for j in range(n):
                            if j == i: continue
                            seed()
                            if not click_i(j): continue
                            if i >= pg.locator(BTN).count(): continue
                            mid = snap(); click_i(i)
                            if snap() != mid: ok = True; break
                    ent["rescued_by_checker_second_chance"] = ok
                results.append(ent)
            kinds = {r["kind"] for r in results}
            for k in ("undo", "redo", "export"):
                if k not in kinds: results.append({"index": None, "label": None, "kind": k, "verdict": "not-applicable", "why": "no such button on the page after the seed"})
            res["buttons_tested"] = n; res["buttons"] = results
            res["buttons_no_effect"] = [r["label"] for r in results if r["verdict"] == "seeded-fail"]
            b.close()
    finally:
        srv.terminate(); srv.wait()
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps({"seed_changed": (res.get("seed") or {}).get("changed_state"), "tested": res.get("buttons_tested"), "seeded_fail": res.get("buttons_no_effect"), "blocked": len(res["blocked_requests"]), "outside_connect": res["outside_connect"]}))

def run_all(root, rdir):
    os.makedirs(rdir, exist_ok=True)
    for bid in sorted(os.listdir(root)):
        d = os.path.join(root, bid)
        if not os.path.isfile(os.path.join(d, "index.html")): continue
        out = os.path.join(rdir, bid + ".seeded.json")
        cmd = ["timeout", "-k", "5", "400", "bwrap", "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp",
               "--bind", rdir, rdir, "--unshare-net", "--unshare-pid", "--die-with-parent", "--new-session",
               sys.executable, os.path.abspath(__file__), d, out]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=430)
        print(bid, "rc", r.returncode, (r.stdout.strip().splitlines() or [""])[-1], r.stderr.strip()[-300:] if r.returncode else "", flush=True)

if __name__ == "__main__":
    if sys.argv[1:2] == ["--all"]: run_all(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 3: run_one(sys.argv[1], sys.argv[2])
    else: print(__doc__); sys.exit(2)
