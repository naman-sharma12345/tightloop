#!/usr/bin/env python3
# v5c blind packaging: a copy of benchmark/blind/r2_run/pack_r2.py. Changes: label -> build dir comes from the sealed KEY_v5c.json
# (read only inside this process; nothing about the mapping is printed or written outside the viewer, which holds labels only),
# 5 labels per app (expenses: 7, from the addendum key KEY_v5c_expenses7.json), and v5c paths. Strip rules, leak grep and viewer build are r2's.
import hashlib, json, os, re, shutil, subprocess, sys
TD = "/home/user/tab/tasks/70a3e3bd-9718-4f28-a168-4eee812d5557"
SNAP = "/home/user/tab/work/tl_blind_v5c"
BL = "/home/user/tab/work/tl_blind_v5c_labelled"
FB = "/home/user/tab/files/tl_blind/v5c"
KEYP = FB + "/KEY_v5c.json"; KEY_SHA = "a8d3c474ad9ed1dffdd47944707ac72bb1876c30e7376a4d2a6da9323391619f"
assert hashlib.sha256(open(KEYP, "rb").read()).hexdigest() == KEY_SHA, "KEY_v5c.json changed - stop"
sys.path.insert(0, SNAP + "/benchmark/blind"); import leakgrep_r2 as LG
KEY7 = FB + "/KEY_v5c_expenses7.json"; KEY7_SHA = "addafd22424fccaa9c71b16468e9d6dcbb6ec028b1feb8edb9d3fcb6faf876e7"
assert hashlib.sha256(open(KEY7, "rb").read()).hexdigest() == KEY7_SHA, "KEY_v5c_expenses7.json changed - stop"
# bookmarks + kanban from KEY_v5c; expenses ONLY from the 7-entry addendum key (Naman m:ecfa8839), KEY_v5c's expenses part unused
_K = json.load(open(KEYP))["apps"]; SRC = {(app, lab): v["dir"] for app, m in _K.items() if app != "expenses" for lab, v in m.items()}; del _K
_K = json.load(open(KEY7))["apps"]["expenses"]; SRC.update({("expenses", lab): v["dir"] for lab, v in _K.items()}); del _K
DROP_DIRS = {".claude", ".git", "node_modules", "target", "__pycache__", ".pytest_cache", ".tightloop", ".github"}
DROP_FILES = re.compile(r"^(AGENTS|CLAUDE|CONTRACT|PLAN|NOTES|TODO|SCRATCH|README|CHANGELOG)(\..*)?$|gate\.sh|tightloop|ponytail|skill|contract|\.plan|\.test\.|_test\.|^test_|\.spec\.|^tests?$|"
                        r"\.md$|\.log$|^console|^look.*\.(json|txt|png)$|^look\.py$|screen ?shot|^(shot|capture)[^/]*\.(png|jpe?g|webp)$|^\.(agents?|cursor|vscode)$", re.I)
HINT = re.compile(r"tightloop|ponytail|no-skill|skill|gate\.sh|GATE (PASS|FAIL)|contract|claude|anthropic|(?<![A-Za-z0-9])v[3-6][a-z]?(?![A-Za-z0-9])", re.I)
TITLES = {"bookmarks": "Bookmarks manager", "expenses": "Expense tracker", "kanban": "Kanban board"}
shutil.rmtree(BL, ignore_errors=True)
strip_log = {}; spec = {"apps": []}
for app in ["bookmarks", "expenses", "kanban"]:
    a = {"id": app, "title": TITLES[app], "builds": []}
    for lab in sorted(l for (ap, l) in SRC if ap == app):
        src = SRC[(app, lab)]; dst = f"{BL}/{app}/{lab}"; dropped = []; hints = []
        os.makedirs(dst, exist_ok=True)
        for dp, dns, fns in os.walk(src):
            for dn in list(dns):
                if dn in DROP_DIRS or DROP_FILES.search(dn): dropped.append(os.path.relpath(os.path.join(dp, dn), src) + "/"); dns.remove(dn)
            for fn in fns:
                rel = os.path.relpath(os.path.join(dp, fn), src)
                if DROP_FILES.search(fn): dropped.append(rel); continue
                os.makedirs(os.path.dirname(os.path.join(dst, rel)), exist_ok=True)
                shutil.copy2(os.path.join(dp, fn), os.path.join(dst, rel))
                try: txt = open(os.path.join(dst, rel), errors="strict").read()
                except Exception: continue
                for i, line in enumerate(txt.splitlines(), 1):
                    if HINT.search(line): hints.append(f"{rel}:{i}: {line.strip()[:160]}")
        strip_log[f"{app}/{lab}"] = {"dropped": dropped, "hint_lines_left": hints,
                                     "files": sorted(os.path.relpath(os.path.join(dp, f), dst) for dp, _, fs in os.walk(dst) for f in fs)}
        a["builds"].append({"label": lab, "dir": dst})
    spec["apps"].append(a)
SP = TD
json.dump(spec, open(f"{SP}/viewer_spec_v5c.json", "w"), indent=1)
print("hint lines left (all labels):", sum(len(v["hint_lines_left"]) for v in strip_log.values()), "; per-label strip counts not printed (they would hint at the mapping)")
if any(v["hint_lines_left"] for v in strip_log.values()):
    print("HINT LINES LEFT - review blind_strip_log_v5c.json before building the viewer"); sys.exit(3)
# LEAK GREP over every blinded build dir (must be 0), then build the one-zip viewer and leak-grep every zip entry (must be 0)
LOGP = f"{TD}/leakgrep_v5c.log"; lines = []
dir_hits = []
for app in spec["apps"]:
    for b in app["builds"]:
        h = LG.scan(b["dir"]); dir_hits += h; lines.append(f"dir {app['id']}/{b['label']}: {len(h)} hits")
lines += dir_hits; lines.append(f"LEAK GREP build dirs: {len(dir_hits)} hits over {sum(len(a['builds']) for a in spec['apps'])} dirs")
if dir_hits:
    open(LOGP, "w").write("\n".join(lines) + "\n"); print("\n".join(lines)); sys.exit(3)
VD = FB + "/viewer"
subprocess.run(["python3", f"{SNAP}/benchmark/blind/viewer/build_viewer.py", VD, f"{SP}/viewer_spec_v5c.json"], check=True, timeout=240)
zp = VD + ".zip"; import zipfile, tempfile
zf = zipfile.ZipFile(zp); names = zf.namelist()
zh = LG.scan(zp)                                         # zip listing (entry names) + every entry's bytes
lines += zh; lines.append(f"LEAK GREP zip listing+entries: {len(zh)} hits over {len(names)} entries ({os.path.basename(zp)})")
tmp = tempfile.mkdtemp(prefix="tlb-unzip-"); zf.extractall(tmp)
uh = LG.scan(tmp)                                        # the unzipped tree, file by file
lines += uh; lines.append(f"LEAK GREP unzipped tree: {len(uh)} hits over {sum(len(f) for _, _, f in os.walk(tmp))} files")
bad_dt = [n for n in names if zf.getinfo(n).date_time != (2026, 10, 18, 12, 0, 0)]
git = [n for n in names if "/.git/" in n or n.endswith("/.git") or "/.git" in n.split("builds/")[-1][:6]]
lines.append(f"zip entries with a non-fixed timestamp: {len(bad_dt)}; .git entries: {len(git)}")
shutil.rmtree(tmp, ignore_errors=True)
open(LOGP, "w").write("\n".join(lines) + "\n"); print("\n".join(lines))
if zh or uh or bad_dt or git: sys.exit(3)
