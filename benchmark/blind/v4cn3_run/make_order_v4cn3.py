#!/usr/bin/env python3
"""tightloop v4c-n3 build order (v4cn3_PREREG.md; a copy of make_order_v4cn3.py): 6 NEW tightloop-v4c builds (3 apps x runs 2,3; the r2 build is run 1),
shuffled with random.Random(seed), seed = secrets.randbits(63), recorded in the order file. Build ids carry no blind
label: labels are drawn separately by make_key_v8.py (v4c-n3 builds are judged in the v8 set) into the sealed key, so the order says nothing about labels.
Usage: make_order_v4cn3.py <out.json>"""
import json, os, random, secrets, sys, datetime
out = sys.argv[1]
if os.path.exists(out): sys.exit("order file exists; refusing to overwrite")
builds = [f"v4cn3-{app}-{i}" for app in ["bookmarks", "expenses", "kanban"] for i in (2, 3)]
seed = secrets.randbits(63); order = builds[:]; random.Random(seed).shuffle(order)
json.dump({"round": "v4c-n3", "seed": seed, "order": order,
           "rng": "random.Random(seed).shuffle(build list in make_order_v4cn3.py order: v4cn3-bookmarks-2..3, v4cn3-expenses-2..3, v4cn3-kanban-2..3), seed = secrets.randbits(63)",
           "created_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}, open(out, "w"), indent=1)
print(out)
