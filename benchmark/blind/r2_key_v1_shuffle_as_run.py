# Blind round 2, key v1 (VOID): the shuffle code exactly as it was run, in two cells of one IPython session
# (2026-10-18 ~18:26Z), copied verbatim from the session transcript. No seed value is in this file: the seed was drawn
# with secrets.randbits(31) at run time. The last line of cell 2, `print(ks, seed, len(b))`, PRINTED THE SEED into the
# session transcript: that is the leak that voided key v1 (see r2_INTEGRITY.md). Kept for the record only; never run it.
# Its replacement is make_key_r2.py, which prints only the key's sha256.

# ---- cell 1 (tool call at 2026-10-18T18:26:20.477Z) ----
import json, random, secrets, hashlib, os
os.makedirs('/home/user/tab/files/tl_blind/r2', exist_ok=True)
KP='/home/user/tab/files/tl_blind/r2/KEY.json'
assert not os.path.exists(KP)
seed=secrets.randbits(31)
rng=random.Random(seed)
arms=['no-skill','ponytail','tightloop-v4','tightloop-v4c']
apps={}
for app in ['bookmarks','expenses','kanban']:   # fixed order, one shuffle each
    a=arms[:]; rng.shuffle(a)
    apps[app]={L:arm for L,arm in zip('ABCD',a)}
key={"round":2,"seed":seed,"rng":"python random.Random(seed); for app in [bookmarks, expenses, kanban]: shuffle([no-skill, ponytail, tightloop-v4, tightloop-v4c]) -> labels A,B,C,D","arms":arms,"arm_dirs":{"tightloop-v4":"benchmark/arms/tightloop-v4b? see note","tightloop-v4c":"benchmark/arms/tightloop-v4c"},"apps":apps}

# ---- cell 2 (tool call at 2026-10-18T18:26:32.798Z) ----
import subprocess
def sh(c): return subprocess.run(c,shell=True,capture_output=True,text=True,cwd='/tmp/tlb_push').stdout.strip()
h4=sh("sha256sum .claude/skills/tightloop/SKILL.md | cut -c1-64"); h4c=sh("sha256sum benchmark/arms/tightloop-v4c/SKILL.md | cut -c1-64")
key["arm_dirs"]={"no-skill":"(no skill folder)","ponytail":"benchmark/arms/ponytail.md","tightloop-v4":".claude/skills/tightloop (SKILL.md sha256 %s)"%h4,"tightloop-v4c":"benchmark/arms/tightloop-v4c (SKILL.md sha256 %s)"%h4c}
key["fixed_at_main"]="3e86a804b8d5a8291485187d5a3b0268f602845d"
key["created_utc"]=__import__('datetime').datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
b=(json.dumps(key,indent=2,sort_keys=True)+"\n").encode()
open(KP,'wb').write(b); os.chmod(KP,0o444)
ks=hashlib.sha256(open(KP,'rb').read()).hexdigest()
# sanity without printing mapping
assert all(sorted(v.values())==sorted(arms) for v in key['apps'].values())
print(ks, seed, len(b))
