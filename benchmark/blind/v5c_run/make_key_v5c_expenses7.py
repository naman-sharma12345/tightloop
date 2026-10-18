#!/usr/bin/env python3
"""v5c expenses addendum key (Naman m:ecfa8839, 3:47 AM IST Oct 19, made BEFORE any judging): expenses gets 7 entries, the 3 v5c builds,
the round-2 no-skill, tightloop-v4c and ponytail builds, and the ponytail rerun, as separate entries with labels A-G drawn fresh
(random.Random(seed), seed = secrets.randbits(63)). It replaces KEY_v5c.json for expenses only (that file is not opened by this script).
The round-2 builds are located through the round-2 key v4 (revealed at c0e44f8, sha256 checked). Writes the key (refuses to overwrite),
mode 0600, prints ONLY its sha256. Usage: make_key_v5c_expenses7.py <key_path>"""
import hashlib, json, os, random, secrets, sys, datetime
kp = sys.argv[1]
if os.path.exists(kp): sys.exit("key exists; refusing to overwrite")
R2KEY = "/home/user/tab/files/tl_blind/r2/KEY_v4.json"; R2SHA = "e765297c4a34e6908638bcc4348b78b76a2eadf05760da4756b82127e8f40d71"
R2OUT = "/home/user/tab/work/tl_blind_out/r2"; OUT = "/home/user/tab/work/tl_blind_out/v5c"
assert hashlib.sha256(open(R2KEY, "rb").read()).hexdigest() == R2SHA, "round-2 key changed - stop"
r2 = json.load(open(R2KEY))["apps"]["expenses"]
def r2dir(arm): return f"{R2OUT}/expenses/" + [l for l, v in r2.items() if v == arm][0]
items = [{"build": f"v5c-expenses-{i}", "arm": "tightloop-v5c", "dir": f"{OUT}/v5c-expenses-{i}"} for i in (1, 2, 3)]
items += [{"build": f"r2-expenses-{a}", "arm": a + " (round 2 build)", "dir": r2dir(a)} for a in ("no-skill", "tightloop-v4c", "ponytail")]
items.append({"build": "ponytail-expenses-rerun", "arm": "ponytail (v5c-round rerun)", "dir": f"{OUT}/ponytail-expenses-rerun"})
assert all(os.path.isdir(x["dir"]) for x in items)
seed = secrets.randbits(63); random.Random(seed).shuffle(items)
key = {"round": "v5c", "app": "expenses", "addendum": "Naman m:ecfa8839 (3:47 AM IST Oct 19), before any judging; replaces KEY_v5c.json for expenses",
       "seed": seed, "apps": {"expenses": {L: it for L, it in zip("ABCDEFG", items)}}, "made_by": "benchmark/blind/v5c_run/make_key_v5c_expenses7.py",
       "rng": "random.Random(seed).shuffle(items in script order); seed = secrets.randbits(63)",
       "created_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
b = (json.dumps(key, indent=2, sort_keys=True) + "\n").encode()
fd = os.open(kp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, "wb") as f: f.write(b)
del seed, items, key, b, r2
print(hashlib.sha256(open(kp, "rb").read()).hexdigest())
