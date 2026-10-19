#!/usr/bin/env python3
"""tightloop v9 build order (v9_PREREG.md; a copy of make_order_v8.py): 9 v9 builds (3 apps x 3 runs; one v9 arm, picked later by the base rule),
shuffled with random.Random(seed), seed = secrets.randbits(63), recorded in the order file. Build ids carry no blind
label: labels A-G are drawn separately by make_key_v9.py into the sealed key, so the order says nothing about labels.
Usage: make_order_v9.py <out.json>"""
import json, os, random, secrets, sys, datetime
out = sys.argv[1]
if os.path.exists(out): sys.exit("order file exists; refusing to overwrite")
builds = [f"v9-{app}-{i}" for app in ["bookmarks", "expenses", "kanban"] for i in (1, 2, 3)]
seed = secrets.randbits(63); order = builds[:]; random.Random(seed).shuffle(order)
json.dump({"round": "v9", "seed": seed, "order": order,
           "rng": "random.Random(seed).shuffle(build list in make_order_v9.py order: v9-bookmarks-1..3, v9-expenses-1..3, v9-kanban-1..3), seed = secrets.randbits(63)",
           "created_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}, open(out, "w"), indent=1)
print(out)
