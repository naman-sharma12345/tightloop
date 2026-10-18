#!/usr/bin/env python3
# round-2 blind packaging. Raw builds come stored by label (the driver resolved labels from the sealed key v4; this script only checks its sha),
# copy each build with version material stripped, log leftovers, build the one-zip viewer, verify it, re-shoot each label.
import hashlib, json, os, re, shutil, subprocess, sys
TD = "/home/user/tab/tasks/a84b5a07-3830-42f7-8e27-78e0788c75e3"
SNAP = os.environ.get("R2_SNAP", "/home/user/tab/work/tl_blind_r2")
OUT = os.environ.get("R2_OUT", "/home/user/tab/work/tl_blind_out/r2")   # env overrides exist only for the dry-run self-test
BL = os.environ.get("R2_BL", "/home/user/tab/work/tl_blind_r2_labelled")          # blinded copies (labels only)
FB = "/home/user/tab/files/tl_blind/r2"
KEYP = FB + "/KEY_v4.json"; KEY_SHA = "e765297c4a34e6908638bcc4348b78b76a2eadf05760da4756b82127e8f40d71"   # key v4 (reseal 993a431); v1 VOID, v2 BURNED, v3 VOID-UNUSED: never used
assert hashlib.sha256(open(KEYP, "rb").read()).hexdigest() == KEY_SHA, "KEY_v4.json changed - stop"   # sha only; not opened
sys.path.insert(0, SNAP + "/benchmark/blind"); import leakgrep_r2 as LG   # Naman m:ed447bea (c)
# raw builds are stored by LABEL by the driver (it resolved label -> version from the key); this script never opens the key
DROP_DIRS = {".claude", ".git", "node_modules", "target", "__pycache__", ".pytest_cache", ".tightloop", ".github"}
DROP_FILES = re.compile(r"^(AGENTS|CLAUDE|CONTRACT|PLAN|NOTES|TODO|SCRATCH|README|CHANGELOG)(\..*)?$|gate\.sh|tightloop|ponytail|skill|contract|\.plan|\.test\.|_test\.|^test_|\.spec\.|^tests?$|"
                        r"\.md$|\.log$|^console|^look.*\.(json|txt|png)$|^look\.py$|screen ?shot|^(shot|capture)[^/]*\.(png|jpe?g|webp)$|^\.(agents?|cursor|vscode)$", re.I)
HINT = re.compile(r"tightloop|ponytail|no-skill|skill|gate\.sh|GATE (PASS|FAIL)|contract|claude|anthropic|(?<![A-Za-z0-9])v4c?(?![A-Za-z0-9])", re.I)
TITLES = {"bookmarks": "Bookmarks manager", "expenses": "Expense tracker", "kanban": "Kanban board"}
shutil.rmtree(BL, ignore_errors=True)
strip_log = {}; spec = {"apps": []}
for app in ["bookmarks", "expenses", "kanban"]:
    a = {"id": app, "title": TITLES[app], "builds": []}
    for lab in "ABCD":
        src = f"{OUT}/{app}/{lab}"; dst = f"{BL}/{app}/{lab}"; dropped = []; hints = []
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
SP = os.environ.get("R2_SPECDIR", TD)
json.dump(strip_log, open(f"{SP}/blind_strip_log_r2.json", "w"), indent=1)
json.dump(spec, open(f"{SP}/viewer_spec_r2.json", "w"), indent=1)
for k, v in strip_log.items(): print(k, "dropped", len(v["dropped"]), "hints", len(v["hint_lines_left"]), "files", len(v["files"]))
if any(v["hint_lines_left"] for v in strip_log.values()):
    print("HINT LINES LEFT - review blind_strip_log_r2.json before building the viewer"); sys.exit(3)
# LEAK GREP over every blinded build dir (must be 0), then build the one-zip viewer and leak-grep every zip entry (must be 0)
LOGP = os.environ.get("R2_LEAKLOG", f"{TD}/leakgrep_r2.log"); lines = []
dir_hits = []
for app in spec["apps"]:
    for b in app["builds"]:
        h = LG.scan(b["dir"]); dir_hits += h; lines.append(f"dir {app['id']}/{b['label']}: {len(h)} hits")
lines += dir_hits; lines.append(f"LEAK GREP build dirs: {len(dir_hits)} hits over 12 dirs")
if dir_hits:
    open(LOGP, "w").write("\n".join(lines) + "\n"); print("\n".join(lines)); sys.exit(3)
VD = os.environ.get("R2_VD", FB + "/viewer")
subprocess.run(["python3", f"{SNAP}/benchmark/blind/viewer/build_viewer.py", VD, f"{SP}/viewer_spec_r2.json"], check=True, timeout=240)
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
