#!/usr/bin/env python3
"""Test (root steer 20:10Z): for every v5 arm, the argv the v5 driver launches holds no skill text; the skill file inside the
sandbox config dir is byte-identical to the arm's SKILL.md; no-skill gets no flag. Runs runner.launch with run_logged stubbed
(nothing is launched, no session). Usage: argv_test_v5.py <repo_root>   exit 0 = pass."""
import os, sys, tempfile, shutil
repo = sys.argv[1]
sys.path.insert(0, os.path.join(repo, "benchmark")); sys.path.insert(0, os.path.join(repo, "benchmark/blind/v5_run"))
sys.argv = [sys.argv[0]]
import runner as R, argv_v5 as A
CFG_IN = "/tmp/.claude-cfg"
class Stop(Exception): pass
seen = {}
def fake(cmd, *a, **k): seen["cmd"] = cmd; raise Stop()
R.run_logged = fake
fails = 0
texts = {"no-skill": None, "ponytail": open(os.path.join(repo, "benchmark/arms/ponytail.md")).read()}
for a in ("tightloop-v4", "tightloop-v5", "tightloop-v5b"):
    texts[a] = open(os.path.join(os.path.normpath(R.ARMS[a]), "SKILL.md")).read()
for arm, text in texts.items():
    cfg = tempfile.mkdtemp(); wt = tempfile.mkdtemp()
    try:
        try: R.launch("claude", "SPEC PROMPT", text, wt, 5, os.path.join(wt, "x.agent"))
        except Stop: pass
        cmd = A.sandbox_argv(seen["cmd"], cfg, CFG_IN); joined = "\0".join(cmd)
        lines = [l for l in (text or "").splitlines() if len(l.strip()) >= 12]
        leaked = [l for l in lines if l in joined]
        ok = not leaked and "--append-system-prompt" not in cmd
        if text:
            f = os.path.join(cfg, A.NAME)
            ok = ok and open(f).read() == text and cmd[cmd.index("--append-system-prompt-file") + 1] == CFG_IN + "/" + A.NAME
        else:
            ok = ok and "--append-system-prompt-file" not in cmd
        print(f"{arm}: argv items {len(cmd)}, skill lines checked {len(lines)}, leaked {len(leaked)}, ok {ok}")
        fails += not ok
    finally: shutil.rmtree(cfg); shutil.rmtree(wt)
print("ARGV TEST:", "PASS" if fails == 0 else f"FAIL ({fails})"); sys.exit(1 if fails else 0)
