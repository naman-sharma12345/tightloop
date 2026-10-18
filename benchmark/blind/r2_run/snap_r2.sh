#!/bin/bash
# Make the round-2 build snapshot from ONE tightloop commit: git archive into SNAP plus SNAP/.snap_commit (the commit's full sha).
# The driver's guard reads .snap_commit and refuses unless that commit's ancestry contains the "blind round 2 CHECKS" commit.
# Usage: snap_r2.sh <commit> [repo=/home/user/tab/work/tightloop_bench] [snap=/home/user/tab/work/tl_blind_r2]
set -eu
C=$1; REPO=${2:-/home/user/tab/work/tightloop_bench}; SNAP=${3:-/home/user/tab/work/tl_blind_r2}
FULL=$(git -C "$REPO" rev-parse --verify "$C^{commit}")
rm -rf "$SNAP.new"; mkdir -p "$SNAP.new"
git -C "$REPO" archive "$FULL" | tar -x -C "$SNAP.new"
echo "$FULL" > "$SNAP.new/.snap_commit"
rm -rf "$SNAP"; mv "$SNAP.new" "$SNAP"
echo "snapshot $SNAP = $FULL"
