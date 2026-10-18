#!/usr/bin/env python3
"""Blind round 2 build order (Naman m:530473fd pt 4): the 12 builds (3 apps x labels A-D) in an order drawn with
secrets.SystemRandom (os.urandom). Writes results/blind_r2_order.json with LABELS ONLY (no version names). The driver builds
in exactly this order, one at a time, and resolves each label to its version from the sealed key inside the process.
Usage: make_order_r2.py <out.json>"""
import json, os, secrets, sys, datetime
out = sys.argv[1]
if os.path.exists(out): sys.exit("order file exists; refusing to overwrite")
items = [f"{app}-{lab}" for app in ["bookmarks", "expenses", "kanban"] for lab in "ABCD"]
secrets.SystemRandom().shuffle(items)
json.dump({"round": 2, "order": items, "rng": "secrets.SystemRandom().shuffle (os.urandom); labels only",
           "created_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}, open(out, "w"), indent=1)
print(out)
