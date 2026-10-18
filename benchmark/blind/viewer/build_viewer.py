#!/usr/bin/env python3
"""Build the blind viewer: build_viewer.py <out_dir> <spec.json>
spec.json: {"apps":[{"id":"todo","title":"Todo","builds":[{"label":"A","dir":"/path/to/A"}, ...]}, ...]}
Copies each build into builds/<app>-<label>-<nonce>/ (a distinct path per build), writes manifest.json with each file's sha256
and a port offset per build (serve.py gives every build its own port = its own origin), then zips the folder as <out_dir>.zip."""
import hashlib, json, os, secrets, shutil, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
out, spec = sys.argv[1], json.load(open(sys.argv[2]))
shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
shutil.copy(os.path.join(HERE, "serve.py"), out); shutil.copy(os.path.join(HERE, "index.html"), out)
man = {"apps": [], "builds": []}; off = 0
for app in spec["apps"]:
    a = {"id": app["id"], "title": app["title"], "builds": []}
    for b in app["builds"]:
        off += 1; rel = f"builds/{app['id']}-{b['label']}-{secrets.token_hex(4)}"
        shutil.copytree(b["dir"], os.path.join(out, rel))
        files = {}
        for dp, _, fs in os.walk(os.path.join(out, rel)):
            for f in fs:
                p = os.path.join(dp, f); files[os.path.relpath(p, os.path.join(out, rel))] = hashlib.sha256(open(p, "rb").read()).hexdigest()
        e = {"app": app["id"], "label": b["label"], "path": rel, "port_offset": off, "files": files}
        a["builds"].append({k: e[k] for k in ("label", "path", "port_offset")}); man["builds"].append(e)
    man["apps"].append(a)
json.dump(man, open(os.path.join(out, "manifest.json"), "w"), indent=1)
open(os.path.join(out, "README.txt"), "w").write("Run: python3 serve.py   then open http://localhost:8000/\n(Python 3, no installs. Each version runs on its own port so versions never share files or saved data.)\n")
z = out.rstrip("/") + ".zip"; top = os.path.basename(out.rstrip("/"))
with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
    for dp, _, fs in os.walk(out):
        for f in sorted(fs):
            p = os.path.join(dp, f); zi = zipfile.ZipInfo(os.path.join(top, os.path.relpath(p, out)), date_time=(2026, 10, 18, 12, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED; zi.external_attr = 0o644 << 16; zf.writestr(zi, open(p, "rb").read())
print(z)
