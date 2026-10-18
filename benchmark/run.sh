#!/usr/bin/env bash
# benchmark/run.sh - run every task under every arm, capture tokens + outcomes.
#
# Usage: benchmark/run.sh --arm all --tasks benchmark/tasks/tasks.json
#
# Each task directory under results/<run-id>/<task>/<arm>/ gets:
#   agent.log     - raw agent output
#   tokens.json   - token counts read from the agent's own usage report
#   tests.json    - hidden-test and regression-test outcomes
#   review.json   - reviewer-agent defect findings
#   diff.patch    - the produced diff
#
# The runner refuses to invent numbers: if the agent CLI cannot report
# token usage, the run is marked failed and excluded, never estimated.
set -u
fail=0
step() { printf '== %s\n' "$1"; }

ARM="all"
TASKS="benchmark/tasks/tasks.json"
while [ $# -gt 0 ]; do
  case "$1" in
    --arm) ARM="$2"; shift 2 ;;
    --tasks) TASKS="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [ ! -f "$TASKS" ]; then
  step "no task set at $TASKS - task shortlist is pending review; nothing to run"
  exit 1
fi

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="benchmark/results/$RUN_ID"
mkdir -p "$OUT"
printf '{"run_id":"%s","arm_selection":"%s","tasks_file":"%s"}\n' \
  "$RUN_ID" "$ARM" "$TASKS" > "$OUT/run.json"

step "run $RUN_ID"
step "TODO: per-task clone, per-arm agent invocation, hidden-test evaluation"
step "results scaffold at $OUT"
exit "$fail"
