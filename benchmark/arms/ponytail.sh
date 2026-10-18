#!/usr/bin/env bash
# ponytail arm: install the pinned ponytail skill into the task workspace.
# usage: ponytail.sh <repo_root> <task_workdir>
set -u
REPO_ROOT="$1"; WORK="$2"
PIN=09c434ab73ca43761c5d8b0c5d341926c2fba710
CACHE="$REPO_ROOT/benchmark/.cache/ponytail"
if [ ! -d "$CACHE" ]; then
  mkdir -p "$REPO_ROOT/benchmark/.cache"
  git clone -q https://github.com/DietrichGebert/ponytail "$CACHE" || exit 1
  git -C "$CACHE" checkout -q "$PIN" || exit 1
fi
head=$(git -C "$CACHE" rev-parse HEAD)
[ "$head" = "$PIN" ] || { echo "ponytail cache moved off pin: $head" >&2; exit 1; }
mkdir -p "$WORK/.claude/skills/ponytail"
cp "$CACHE/skills/ponytail/SKILL.md" "$WORK/.claude/skills/ponytail/SKILL.md"
