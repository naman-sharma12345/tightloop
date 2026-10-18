#!/usr/bin/env python3
"""Skill-size measurement for tightloop v5c (= v4c + finish checklist); a copy of
benchmark/design/tightloop-v5/measure_skill_tokens.py (A2 method) with the arm list changed only.
Calibrated size = raw_delta + 9 (DESIGN.md 4.2.1). No agent session:
only the token-counting endpoint (POST /v1/messages/count_tokens), which runs no model.
Reads ANTHROPIC_BASE_URL and ANTHROPIC_API_KEY from the environment (never written anywhere).

What the runner adds per arm to the first API call of a session (runner.py launch() +
install_skill()): (1) the arm's SKILL.md text via --append-system-prompt, and (2) one
entry in the CLI's skill listing ("The following skills are available for use with the
Skill tool:") for the installed .claude/skills/<name>/ folder: "- <name>: <description>".
Measured delta(arm) = count(system = BASE + "\n\n" + SKILL.md, listing with the arm's entry)
                    - count(system = BASE, listing without it).
Usage: python3 measure_skill_tokens.py <ponytail SKILL.md> <repo root>  -> JSON on stdout
"""
import json, os, sys, urllib.request, yaml
MODEL = "claude-opus-5-5"   # the model of the round-1 sessions (init event "model")
BASE = "You are an interactive CLI coding agent. Use the tools available to help the user."
PRE = "The following skills are available for use with the Skill tool:\n\n"
OTHERS = "- deep-research: Research a topic in depth.\n- design: Design UI.\n- verify: Verify work.\n"
SPEC = "Build a small notes app as specified."

def count(system, entry):
    body = {"model": MODEL, "system": system, "messages": [{"role": "user", "content": [
        {"type": "text", "text": "<system-reminder>\n" + PRE + entry + OTHERS + "</system-reminder>"},
        {"type": "text", "text": SPEC}]}]}
    req = urllib.request.Request(os.environ["ANTHROPIC_BASE_URL"].rstrip("/") + "/v1/messages/count_tokens",
        data=json.dumps(body).encode(), headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"],
        "anthropic-version": "2023-06-01", "content-type": "application/json",
        "user-agent": "tightloop-measure/1"})
    return json.load(urllib.request.urlopen(req, timeout=60))["input_tokens"]

def main(ponytail_path, root):
    arms = {"ponytail": ponytail_path,
            "tightloop-v4": os.path.join(root, ".claude/skills/tightloop/SKILL.md"),
            "tightloop-v4c": os.path.join(root, "benchmark/arms/tightloop-v4c/SKILL.md"),
            "tightloop-v5c": os.path.join(root, "benchmark/arms/tightloop-v5c/SKILL.md")}
    t0 = count(BASE, "")
    out = {"model": MODEL, "baseline_no_skill": t0, "arms": {}}
    for arm, p in arms.items():
        text = open(p, encoding="utf-8").read()
        fm = yaml.safe_load(text.split("---")[1])
        entry = "- %s: %s\n" % (fm["name"], " ".join(str(fm["description"]).split()))
        out["arms"][arm] = {"bytes": len(text.encode()), "raw_delta": count(BASE + "\n\n" + text, entry) - t0}
    print(json.dumps(out, indent=1))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
