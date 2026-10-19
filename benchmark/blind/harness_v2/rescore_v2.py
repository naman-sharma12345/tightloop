#!/usr/bin/env python3
"""APP HARNESS v2 rescore (NOT a build): run check_app_v2.py over SAVED build outputs and write both scores side by side.
usage: rescore_v2.py <out.tsv> <app> <build_dir> <v1_check.json> [<app> <build_dir> <v1_check.json> ...]
For each build: v1 score (from its saved v1 check.json, never re-run), v2 score (check_app_v2.py now), the buttons each
version found dead, and the dialog counts v2 logged. One row per build. Used for the v4c / v8 / v9 rescore after the queue."""
import json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1]; a = sys.argv[2:]
assert a and len(a) % 3 == 0, __doc__
new = not os.path.exists(out)
with open(out, "a") as f:
    if new: f.write("app\tbuild_dir\tv1_passed\tv1_total\tv2_passed\tv2_total\tv1_dead_buttons\tv2_dead_buttons\tv2_dialogs\n")
    for i in range(0, len(a), 3):
        app, bd, v1p = a[i:i + 3]
        v1 = json.load(open(v1p)); td = tempfile.mkdtemp(prefix="rescore-v2-")
        cj = os.path.join(td, "check.json")
        subprocess.run(["timeout", "-k", "5", "280", sys.executable, os.path.join(HERE, "check_app_v2.py"), app, bd, os.path.join(td, "shot.png"), cj],
                       capture_output=True, text=True)
        try: v2 = json.load(open(cj))
        except Exception: v2 = {}
        row = [app, bd, v1.get("passed"), v1.get("total"), v2.get("passed"), v2.get("total"), json.dumps(v1.get("buttons_no_effect")),
               json.dumps(v2.get("buttons_no_effect")), json.dumps(v2.get("dialog_counts"), sort_keys=True)]
        f.write("\t".join(str(x) for x in row) + "\n"); f.flush(); print("\t".join(str(x) for x in row), flush=True)
