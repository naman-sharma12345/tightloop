#!/usr/bin/env python3
"""Blind round 2 label key, v2 (reseal; Naman m:fe05342f item d, root decision 2026-10-18).
Draws a seed with `secrets`, shuffles the 4 versions independently per app (fixed app order bookmarks, expenses, kanban) with
random.Random(seed), writes the key to the path given (refuses to overwrite), mode 0600, and prints ONLY the sha256 of the file.
The seed and the mapping exist only inside the written key: nothing else is printed, logged or returned.
Usage: make_key_r2.py <key_path> <repo_root>"""
import hashlib, json, os, random, secrets, sys, datetime
kp, repo = sys.argv[1], sys.argv[2]
if os.path.exists(kp): sys.exit("key exists; refusing to overwrite")
def sha(p): return hashlib.sha256(open(os.path.join(repo, p), "rb").read()).hexdigest()
arms = ["no-skill", "ponytail", "tightloop-v4", "tightloop-v4c"]
seed = secrets.randbits(63); rng = random.Random(seed)
apps = {}
for app in ["bookmarks", "expenses", "kanban"]:
    a = arms[:]; rng.shuffle(a); apps[app] = {L: v for L, v in zip("ABCD", a)}
key = {"round": 2, "key_version": 2, "seed": seed,
       "rng": "python random.Random(seed), seed = secrets.randbits(63); for app in [bookmarks, expenses, kanban]: shuffle([no-skill, ponytail, tightloop-v4, tightloop-v4c]) -> labels A,B,C,D",
       "arms": arms, "apps": apps,
       "arm_dirs": {"no-skill": "(no skill folder)", "ponytail": "pinned ponytail SKILL.md via runner.ponytail_skill (fallback benchmark/arms/ponytail.md)",
                    "tightloop-v4": ".claude/skills/tightloop (SKILL.md sha256 %s)" % sha(".claude/skills/tightloop/SKILL.md"),
                    "tightloop-v4c": "benchmark/arms/tightloop-v4c (SKILL.md sha256 %s)" % sha("benchmark/arms/tightloop-v4c/SKILL.md")},
       "made_by": "benchmark/blind/make_key_r2.py",
       "created_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
assert all(sorted(v.values()) == sorted(arms) for v in apps.values())
b = (json.dumps(key, indent=2, sort_keys=True) + "\n").encode()
fd = os.open(kp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, "wb") as f: f.write(b)
del seed, rng, apps, key, b
print(hashlib.sha256(open(kp, "rb").read()).hexdigest())
