#!/usr/bin/env python3
"""tightloop v5c build order (v5c_PREREG.md): 9 v5c builds (3 apps x 3 runs) + 1 ponytail expenses rerun = 10 builds,
shuffled with random.Random(seed), seed = secrets.randbits(63), recorded in the order file. Build ids carry no blind
label: labels A-E/F are drawn separately by make_key_v5c.py into the sealed key, so the order says nothing about labels.
Usage: make_order_v5c.py <out.json>"""
import json, os, random, secrets, sys, datetime
out = sys.argv[1]
if os.path.exists(out): sys.exit("order file exists; refusing to overwrite")
builds = [f"v5c-{app}-{i}" for app in ["bookmarks", "expenses", "kanban"] for i in (1, 2, 3)] + ["ponytail-expenses-rerun"]
seed = secrets.randbits(63); order = builds[:]; random.Random(seed).shuffle(order)
json.dump({"round": "v5c", "seed": seed, "order": order,
           "rng": "random.Random(seed).shuffle(build list in make_order_v5c.py order: v5c-bookmarks-1..3, v5c-expenses-1..3, v5c-kanban-1..3, ponytail-expenses-rerun), seed = secrets.randbits(63)",
           "created_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}, open(out, "w"), indent=1)
print(out)
