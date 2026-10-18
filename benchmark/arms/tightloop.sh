#!/usr/bin/env bash
# tightloop arm: install this repository's skill into the task workspace.
# usage: tightloop.sh <repo_root> <task_workdir>
set -u
REPO_ROOT="$1"; WORK="$2"
mkdir -p "$WORK/.claude/skills/tightloop" "$WORK/.claude/agents"
cp "$REPO_ROOT/.claude/skills/tightloop/SKILL.md" "$WORK/.claude/skills/tightloop/SKILL.md"
cp "$REPO_ROOT/.claude/agents/scout.md" "$REPO_ROOT/.claude/agents/skeptic.md" "$WORK/.claude/agents/"
cp "$REPO_ROOT/AGENTS.md" "$WORK/AGENTS.md"
