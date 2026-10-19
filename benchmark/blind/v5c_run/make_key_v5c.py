#!/usr/bin/env python3
"""tightloop v5c blind label key (v5c_PREREG.md). Per app the judged set is the 3 v5c builds + the round-2 no-skill build +
the round-2 tightloop-v4c build (5 labels A-E); expenses also gets the ponytail rerun (6 labels A-F). The round-2 builds are
located through the round-2 key v4 (revealed at c0e44f8, sha256 checked). Labels are drawn with random.Random(seed),
seed = secrets.randbits(63). Writes the key to the path given (refuses to overwrite), mode 0600, prints ONLY its sha256.
Usage: make_key_v5c.py <key_path>"""
import hashlib, json, os, random, secrets, sys, datetime
kp = sys.argv[1]
if os.path.exists(kp): sys.exit("key exists; refusing to overwrite")
R2KEY = "/home/user/tab/files/tl_blind/r2/KEY_v4.json"; R2SHA = "e765297c4a34e6908638bcc4348b78b76a2eadf05760da4756b82127e8f40d71"
R2OUT = "/home/user/tab/work/tl_blind_out/r2"; OUT = "/home/user/tab/work/tl_blind_out/v5c"
assert hashlib.sha256(open(R2KEY, "rb").read()).hexdigest() == R2SHA, "round-2 key changed - stop"
r2 = json.load(open(R2KEY))["apps"]
def r2dir(app, arm): return f"{R2OUT}/{app}/" + [l for l, v in r2[app].items() if v == arm][0]
seed = secrets.randbits(63); rng = random.Random(seed); apps = {}
for app in ["bookmarks", "expenses", "kanban"]:
    items = [{"build": f"v5c-{app}-{i}", "arm": "tightloop-v5c", "dir": f"{OUT}/v5c-{app}-{i}"} for i in (1, 2, 3)]
    items += [{"build": f"r2-{app}-{a}", "arm": a + " (round 2 build)", "dir": r2dir(app, a)} for a in ("no-skill", "tightloop-v4c")]
    if app == "expenses": items.append({"build": "ponytail-expenses-rerun", "arm": "ponytail", "dir": f"{OUT}/ponytail-expenses-rerun"})
    rng.shuffle(items); apps[app] = {L: it for L, it in zip("ABCDEF", items)}
key = {"round": "v5c", "seed": seed, "apps": apps, "made_by": "benchmark/blind/v5c_run/make_key_v5c.py",
       "rng": "random.Random(seed).shuffle(items in script order) per app in [bookmarks, expenses, kanban]; seed = secrets.randbits(63)",
       "created_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
b = (json.dumps(key, indent=2, sort_keys=True) + "\n").encode()
fd = os.open(kp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, "wb") as f: f.write(b)
del seed, rng, apps, key, b, r2
print(hashlib.sha256(open(kp, "rb").read()).hexdigest())
