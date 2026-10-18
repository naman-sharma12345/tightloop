#!/usr/bin/env python3
"""tightloop v7 build order (v7_PREREG.md; a copy of make_order_v6c.py): 9 v7 builds (3 apps x 3 runs),
shuffled with random.Random(seed), seed = secrets.randbits(63), recorded in the order file. Build ids carry no blind
label: labels A-E are drawn separately by make_key_v7.py into the sealed key, so the order says nothing about labels.
Usage: make_order_v7.py <out.json>"""
import json, os, random, secrets, sys, datetime
out = sys.argv[1]
if os.path.exists(out): sys.exit("order file exists; refusing to overwrite")
builds = [f"v7-{app}-{i}" for app in ["bookmarks", "expenses", "kanban"] for i in (1, 2, 3)]
seed = secrets.randbits(63); order = builds[:]; random.Random(seed).shuffle(order)
json.dump({"round": "v7", "seed": seed, "order": order,
           "rng": "random.Random(seed).shuffle(build list in make_order_v7.py order: v7-bookmarks-1..3, v7-expenses-1..3, v7-kanban-1..3), seed = secrets.randbits(63)",
           "created_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}, open(out, "w"), indent=1)
print(out)
