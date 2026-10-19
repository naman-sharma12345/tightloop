#!/usr/bin/env python3
"""tightloop v5 blind run: sealed label key (DESIGN.md 4.1 as amended by A1/A2; method of make_key_r2.py, round-2 key v4).
Draws a seed with `secrets` (os.urandom), and with random.Random(seed) shuffles the 5 arms independently per (app, run) in the
fixed order habits, recipes, pomodoro x runs 1, 2, 3 -> labels A-E. Writes the key to the path given (refuses to overwrite),
mode 0600, and prints ONLY the sha256 of the written file. The seed and the mapping exist only inside the key: nothing else is
printed, logged or returned. Nothing secret comes in by argv or env.
Usage: make_key_v5.py <key_path> <repo_root>"""
import hashlib, json, os, random, secrets, sys, datetime
kp, repo = sys.argv[1], sys.argv[2]
if os.path.exists(kp): sys.exit("key exists; refusing to overwrite")
def sha(p): return hashlib.sha256(open(os.path.join(repo, p), "rb").read()).hexdigest()
arms = ["no-skill", "ponytail", "tightloop-v4", "tightloop-v5", "tightloop-v5b"]
APPS, RUNS = ["habits", "recipes", "pomodoro"], [1, 2, 3]
seed = secrets.randbits(63); rng = random.Random(seed)
pages = {}
for app in APPS:
    for run in RUNS:
        a = arms[:]; rng.shuffle(a); pages["%s/run%d" % (app, run)] = {L: v for L, v in zip("ABCDE", a)}
key = {"round": "v5", "key_version": 1, "seed": seed,
       "rng": "python random.Random(seed), seed = secrets.randbits(63); for app in [habits, recipes, pomodoro]: for run in [1, 2, 3]: "
              "shuffle([no-skill, ponytail, tightloop-v4, tightloop-v5, tightloop-v5b]) -> labels A,B,C,D,E",
       "arms": arms, "pages": pages,
       "arm_dirs": {"no-skill": "(no skill folder)",
                    "ponytail": "pinned ponytail SKILL.md via runner.ponytail_skill",
                    "tightloop-v4": ".claude/skills/tightloop (SKILL.md sha256 %s)" % sha(".claude/skills/tightloop/SKILL.md"),
                    "tightloop-v5": "benchmark/arms/tightloop-v5 (SKILL.md sha256 %s)" % sha("benchmark/arms/tightloop-v5/SKILL.md"),
                    "tightloop-v5b": "benchmark/arms/tightloop-v5b (SKILL.md sha256 %s)" % sha("benchmark/arms/tightloop-v5b/SKILL.md")},
       "specs": {app: sha("benchmark/blind/specs/v5/%s.md" % app) for app in APPS},
       "made_by": "benchmark/blind/make_key_v5.py",
       "created_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
assert all(sorted(v.values()) == sorted(arms) for v in pages.values()) and len(pages) == 9
b = (json.dumps(key, indent=2, sort_keys=True) + "\n").encode()
d = os.path.dirname(os.path.abspath(kp)); os.makedirs(d, mode=0o700, exist_ok=True)
fd = os.open(kp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, "wb") as f: f.write(b)
del seed, rng, pages, key, b
print(hashlib.sha256(open(kp, "rb").read()).hexdigest())
