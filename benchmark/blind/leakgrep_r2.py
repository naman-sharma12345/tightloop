#!/usr/bin/env python3
"""Round-2 blind leak grep (Naman m:ed447bea c). Run on every blinded build dir and on every entry of the viewer zip.
Usage: leakgrep_r2.py <dir-or-zip> [...]   -> prints one line per hit and a final "LEAK GREP: N hits"; exit 1 if N > 0.
A hit is: a version/skill word in any file name or file byte (skill names, tightloop, ponytail, no-skill/noskill, SKILL, .claude, version tags v3 v4 v4a v4b v4c v4d v5 v5b (v3-v6 + one letter),
claude/anthropic, gate.sh / GATE PASS, look.py and its output words), or a file that is version material by its kind:
.claude/ or other agent folders, agent notes (NOTES/PLAN/TODO/AGENTS/CLAUDE/CONTRACT/SCRATCH, any .md), screenshots and other
unreferenced raster images, console or run logs (.log, console*), look.py output (look*.json/txt)."""
import os, re, sys, zipfile
WORDS = re.compile(rb"tightloop|ponytail|no[-_ ]?skill|skill|claude|anthropic|gate\.sh|GATE (?:PASS|FAIL)|look\.py|look_report|"
                   rb"controls clicked|(?<![A-Za-z0-9])v[3-6][a-z]?(?![A-Za-z0-9])", re.I)
BAD_DIR = re.compile(r"(^|/)(\.claude|\.tightloop|\.agent[s]?|\.cursor|\.github|\.vscode|node_modules|__pycache__)(/|$)", re.I)
BAD_FILE = re.compile(r"(^|/)(NOTES|PLAN|TODO|AGENTS|CLAUDE|CONTRACT|SCRATCH|README|CHANGELOG)(\.[^/]*)?$|\.md$|\.log$|(^|/)console[^/]*$|"
                      r"(^|/)look[^/]*\.(json|txt)$|screen ?shot|(^|/)(shot|capture)[^/]*$", re.I)
IMG = re.compile(r"\.(png|jpe?g|webp|gif|bmp)$", re.I)   # an image no other file of the same build refers to = a stray (screenshot) -> hit
VIEWER_OWN = {"serve.py", "index.html", "manifest.json", "README.txt"}   # the viewer's own files at the zip top level
def _check(name, data, hits, where):
    rel = name.replace(os.sep, "/")
    if BAD_DIR.search(rel): hits.append(f"{where}:{rel}: version-material folder")
    # the viewer's own top-level files (serve.py, index.html, manifest.json, README.txt) are exempt from the file-kind rule only at
    # the viewer root: "<top>/<name>" in the zip, "<name>" or "<top>/<name>" in an unzipped tree; their bytes are still grepped
    parts = rel.split("/")
    at_root = (len(parts) == 2 and parts[1] in VIEWER_OWN) or (len(parts) == 1 and parts[0] in VIEWER_OWN and not where.endswith(".zip"))
    if BAD_FILE.search(rel) and not at_root:
        hits.append(f"{where}:{rel}: version-material file kind")
    for m in WORDS.finditer(rel.encode()): hits.append(f"{where}:{rel}: name contains {m.group(0).decode(errors='replace')!r}")
    for i, line in enumerate(data.splitlines(), 1):
        for m in WORDS.finditer(line):
            hits.append(f"{where}:{rel}:{i}: {m.group(0).decode(errors='replace')!r} in {line.strip()[:100].decode(errors='replace')!r}")
def _stray_images(items, where, hits):
    text = b"\n".join(d for n, d in items if not IMG.search(n))
    for n, _ in items:
        if IMG.search(n) and os.path.basename(n).encode() not in text: hits.append(f"{where}:{n}: image no file of the build refers to (screenshot?)")
def scan(path):
    hits = []; items = []
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            for n in z.namelist():
                if not n.endswith("/"): d = z.read(n); _check(n, d, hits, path); items.append((n, d))
                else: _check(n, b"", hits, path)
    else:
        for dp, dns, fns in os.walk(path):
            for d in dns: _check(os.path.relpath(os.path.join(dp, d), path) + "/", b"", hits, path)
            for f in fns:
                p = os.path.join(dp, f); d = open(p, "rb").read(); _check(os.path.relpath(p, path), d, hits, path); items.append((os.path.relpath(p, path), d))
    _stray_images(items, path, hits)
    return hits
if __name__ == "__main__":
    allh = []
    for p in sys.argv[1:]: allh += scan(p)
    for h in allh: print(h)
    print(f"LEAK GREP: {len(allh)} hits over {len(sys.argv[1:])} target(s)")
    sys.exit(1 if allh else 0)
