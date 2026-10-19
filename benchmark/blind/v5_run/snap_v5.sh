#!/bin/bash
# v5 run snapshot: git-archive one tightloop commit into /home/user/tab/work/tl_blind_v5 (the ONLY place the v5 driver runs from).
# usage: bash benchmark/blind/v5_run/snap_v5.sh <commit>   (fetch only touches the clone's object store, never its working tree)
set -euo pipefail
B=/home/user/tab/work/tightloop_bench; S=/home/user/tab/work/tl_blind_v5
timeout 60 git -C "$B" fetch -q origin
C=$(git -C "$B" rev-parse --verify "$1^{commit}")
rm -rf "$S"; mkdir -p "$S"
git -C "$B" archive "$C" | tar -x -C "$S"
echo "$C" > "$S/.snap_commit"
echo "snapshot $C -> $S"
