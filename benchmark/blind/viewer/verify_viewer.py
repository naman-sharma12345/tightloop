#!/usr/bin/env python3
"""Prove the viewer serves every build its own bytes: verify_viewer.py <viewer_dir> <base_port> <proof.json> [shots_prefix]
Starts serve.py, opens the viewer, opens every tile full size, and checks that every file the build's iframe loaded matches the
manifest sha256 for THAT build, that each build ran on its own origin, and that no console/page error occurred in the viewer."""
import hashlib, json, os, subprocess, sys, time
from playwright.sync_api import sync_playwright
vd, base, outp = sys.argv[1], int(sys.argv[2]), sys.argv[3]; shots = sys.argv[4] if len(sys.argv) > 4 else None
man = json.load(open(os.path.join(vd, "manifest.json")))
srv = subprocess.Popen([sys.executable, os.path.join(vd, "serve.py"), str(base)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.2); res = {"builds": [], "viewer_errors": []}
try:
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1440, "height": 900}); pg.set_default_timeout(5000)
        got = {}
        def keep(r):
            try:
                port = int(r.url.split("://", 1)[1].split("/", 1)[0].split(":")[1])
                if r.status == 200 and port != base: got.setdefault(port, {})[r.url.split(f":{port}/", 1)[1].split("?")[0] or "index.html"] = hashlib.sha256(r.body()).hexdigest()
            except Exception: pass
        pg.on("response", keep); pg.on("pageerror", lambda e: res["viewer_errors"].append(str(e)[:150]))
        pg.goto(f"http://localhost:{base}/"); pg.wait_for_timeout(1500)
        if shots: pg.screenshot(path=shots + "_grid.png")
        for ai, app in enumerate(man["apps"]):
            pg.locator("#tabs button").nth(ai).click(); pg.wait_for_timeout(800)
            for k, bb in enumerate(app["builds"]):
                port = base + bb["port_offset"]; got.pop(port, None)
                pg.locator(".tile").nth(k).click(); pg.wait_for_timeout(1200)
                fr = pg.frame_locator("#frame"); frame = [f for f in pg.frames if f.url.startswith(f"http://localhost:{port}/")]
                origin = frame[0].evaluate("location.origin") if frame else None
                ent = [e for e in man["builds"] if e["port_offset"] == bb["port_offset"]][0]
                loaded = got.get(port, {})
                mism = [f for f, h in loaded.items() if ent["files"].get(f) != h]
                if shots and k == 0: pg.screenshot(path=f"{shots}_{app['id']}_{bb['label']}_open.png")
                res["builds"].append({"app": app["id"], "label": bb["label"], "port": port, "origin": origin, "loaded": sorted(loaded),
                                      "mismatched": mism, "ok": bool(loaded) and "index.html" in loaded and not mism and origin == f"http://localhost:{port}"})
                pg.click("#close"); pg.wait_for_timeout(300)
        b.close()
    # Everything reachable over HTTP (Pally m:699f008f pt 3): fetch every file each port can serve, grep the bytes for the
    # real version names, and probe that the viewer port serves nothing but its page and manifest.
    import re, urllib.request, urllib.error
    NAMES = re.compile(rb"no-skill|ponytail|tightloop|skill|(?<![A-Za-z0-9])v4c?(?![A-Za-z0-9])", re.I)
    def fetch(port, rel):
        try: return urllib.request.urlopen(f"http://127.0.0.1:{port}/{rel}", timeout=5).read(), 200
        except urllib.error.HTTPError as e: return b"", e.code
    hits, fetched = [], 0
    for rel in ("", "index.html", "manifest.json"):
        body, st = fetch(base, rel); fetched += 1
        hits += [(base, rel or "/", m.group(0).decode(errors="replace")) for m in NAMES.finditer(body)]
    for e in man["builds"]:
        port = base + e["port_offset"]; bdir = os.path.join(vd, e["path"])
        for dp, _, fs in os.walk(bdir):
            for f in fs:
                rel = os.path.relpath(os.path.join(dp, f), bdir); body, st = fetch(port, rel); fetched += 1
                if st != 200: hits.append((port, rel, f"HTTP {st}"))
                hits += [(port, rel, body[max(0, m.start() - 30):m.end() + 30].decode(errors="replace")) for m in NAMES.finditer(body)]
        for d in ("..", "../..", "../manifest.json"):   # nothing outside the build folder
            body, st = fetch(port, d)
            if st == 200 and body and b"<title" not in body[:400] and d != "..": hits.append((port, d, "outside file served"))
    blocked = {rel: fetch(base, rel)[1] for rel in ("serve.py", "README.txt", "builds/", man["builds"][0]["path"] + "/index.html")}
    res["name_grep"] = {"files_fetched": fetched, "hits": hits[:50], "n_hits": len(hits)}
    res["viewer_port_blocked"] = blocked
    bad_names = [f for dp, _, fs in os.walk(vd) for f in fs if re.search(r"KEY|COST|METRIC|check|\.png$", f, re.I)]
    res["forbidden_files_in_viewer_dir"] = bad_names
finally:
    srv.terminate(); srv.wait()
origins = [x["origin"] for x in res["builds"]]
res["distinct_origins"] = len(set(origins)) == len(origins)
res["all_ok"] = (all(x["ok"] for x in res["builds"]) and res["distinct_origins"] and not res["viewer_errors"]
                 and res["name_grep"]["n_hits"] == 0 and all(v == 404 for v in res["viewer_port_blocked"].values()) and not res["forbidden_files_in_viewer_dir"])
json.dump(res, open(outp, "w"), indent=1)
print(json.dumps({"all_ok": res["all_ok"], "n": len(res["builds"]), "distinct_origins": res["distinct_origins"], "viewer_errors": res["viewer_errors"],
                  "name_grep": res["name_grep"], "viewer_port_blocked": res["viewer_port_blocked"], "forbidden_files": res["forbidden_files_in_viewer_dir"],
                  "bad": [(x["app"], x["label"], x["mismatched"], x["loaded"]) for x in res["builds"] if not x["ok"]]}))
