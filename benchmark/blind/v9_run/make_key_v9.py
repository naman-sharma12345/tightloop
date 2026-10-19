#!/usr/bin/env python3
"""tightloop v9 blind label key (v9_PREREG.md); a copy of make_key_v8.py. The v9 base is not known at prereg time (v9_PREREG.md
section 0: base = v8 if v8 is KEPT under v8_PREREG.md, else v4c), so the ONE key file holds TWO independently shuffled label sets and
the viewer zip is packed from the variant that matches the base root picks by that rule (the other variant is never used):
  "base_v4c": per app the 3 v9 builds + the 3 tightloop-v4c builds (round-2 build + the 2 v4c-n3 builds) + the round-2 no-skill build;
  "base_v8":  per app the 3 v9 builds + the 3 tightloop-v8 builds + the round-2 no-skill build.
7 labels A-G per app per variant. The v9 build dirs are the same in both variants (tl_blind_out/v9/v9-<app>-<i>); the v9 arm name is
not in the key (it is in the build rows). Made at prereg time, before any v9 build exists (the key names build ids and output dirs only).
The round-2 builds are located through the round-2 key v4 (revealed at c0e44f8, sha256 checked); the v8 and v4c-n3 build dirs are named
by build id and need no key. Labels: random.Random(seed_variant).shuffle per app, seed_variant = secrets.randbits(63) per variant.
Writes the key to the path given (refuses to overwrite), mode 0600, prints ONLY its sha256.
Usage: make_key_v9.py <key_path>"""
import hashlib, json, os, random, secrets, sys, datetime
kp = sys.argv[1]
if os.path.exists(kp): sys.exit("key exists; refusing to overwrite")
R2KEY = "/home/user/tab/files/tl_blind/r2/KEY_v4.json"; R2SHA = "e765297c4a34e6908638bcc4348b78b76a2eadf05760da4756b82127e8f40d71"
R2OUT = "/home/user/tab/work/tl_blind_out/r2"; OUT = "/home/user/tab/work/tl_blind_out/v9"
OUT8 = "/home/user/tab/work/tl_blind_out/v8"; OUT4 = "/home/user/tab/work/tl_blind_out/v4cn3"
assert hashlib.sha256(open(R2KEY, "rb").read()).hexdigest() == R2SHA, "round-2 key changed - stop"
r2 = json.load(open(R2KEY))["apps"]
def r2dir(app, arm): return f"{R2OUT}/{app}/" + [l for l, v in r2[app].items() if v == arm][0]
variants = {}
for var in ["base_v4c", "base_v8"]:
    seed = secrets.randbits(63); rng = random.Random(seed); apps = {}
    for app in ["bookmarks", "expenses", "kanban"]:
        items = [{"build": f"v9-{app}-{i}", "arm": "tightloop-v9 (arm picked by the base rule)", "dir": f"{OUT}/v9-{app}-{i}"} for i in (1, 2, 3)]
        if var == "base_v4c":
            items += [{"build": f"v4cn3-{app}-{i}", "arm": "tightloop-v4c (v4c-n3 build)", "dir": f"{OUT4}/v4cn3-{app}-{i}"} for i in (2, 3)]
            items += [{"build": f"r2-{app}-{a}", "arm": a + " (round 2 build)", "dir": r2dir(app, a)} for a in ("no-skill", "tightloop-v4c")]
        else:
            items += [{"build": f"v8-{app}-{i}", "arm": "tightloop-v8", "dir": f"{OUT8}/v8-{app}-{i}"} for i in (1, 2, 3)]
            items += [{"build": f"r2-{app}-no-skill", "arm": "no-skill (round 2 build)", "dir": r2dir(app, "no-skill")}]
        rng.shuffle(items); apps[app] = {L: it for L, it in zip("ABCDEFG", items)}
    variants[var] = {"seed": seed, "apps": apps}
key = {"round": "v9", "variants": variants, "made_by": "benchmark/blind/v9_run/make_key_v9.py",
       "rng": "per variant in [base_v4c, base_v8]: seed = secrets.randbits(63); random.Random(seed).shuffle(items in script order) per app in [bookmarks, expenses, kanban]",
       "use": "pack the viewer from variants[base] where base is picked by v9_PREREG.md section 0 after the v8 reveal",
       "created_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
b = (json.dumps(key, indent=2, sort_keys=True) + "\n").encode()
fd = os.open(kp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, "wb") as f: f.write(b)
del seed, rng, apps, key, b, r2, variants
print(hashlib.sha256(open(kp, "rb").read()).hexdigest())
