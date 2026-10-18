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
finally:
    srv.terminate(); srv.wait()
origins = [x["origin"] for x in res["builds"]]
res["distinct_origins"] = len(set(origins)) == len(origins)
res["all_ok"] = all(x["ok"] for x in res["builds"]) and res["distinct_origins"] and not res["viewer_errors"]
json.dump(res, open(outp, "w"), indent=1)
print(json.dumps({"all_ok": res["all_ok"], "n": len(res["builds"]), "distinct_origins": res["distinct_origins"], "viewer_errors": res["viewer_errors"],
                  "bad": [(x["app"], x["label"], x["mismatched"], x["loaded"]) for x in res["builds"] if not x["ok"]]}))
