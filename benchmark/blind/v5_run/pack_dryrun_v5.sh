#!/bin/bash
# pack_v5.py dry run on 45 fake builds (no model, no session): every page/label gets a tiny index.html; expects exit 0, 0 leak hits.
set -u
T=$(mktemp -d); R=${1:-$(cd "$(dirname "$0")/../../.." && pwd)}
for app in habits recipes pomodoro; do for run in 1 2 3; do for L in A B C D E; do
  d=$T/out/$app/run$run/$L; mkdir -p $d/.claude/skills/x; echo "<!doctype html><title>$app</title><p>$app $run</p>" > $d/index.html; echo x > $d/.claude/skills/x/SKILL.md; echo n > $d/NOTES.md
done; done; done
mkdir -p $T/spec
V5_SNAP=$R V5_OUT=$T/out V5_BL=$T/bl V5_SPECDIR=$T/spec V5_LEAKLOG=$T/leak.log V5_VD=$T/viewer timeout -k 5 200 python3 $R/benchmark/blind/v5_run/pack_v5.py | tail -6
rc=${PIPESTATUS[0]}; echo "pack rc=$rc"; tail -4 $T/leak.log; rm -rf $T
