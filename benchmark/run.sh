#!/usr/bin/env bash
# benchmark/run.sh - run the same task set under every arm, raw lines only.
#
# Usage:
#   benchmark/run.sh --tasks benchmark/tasks/tasks.json \
#     --agent-cmd 'claude -p "$(cat $INSTRUCTION_FILE)" --output-format json > $AGENT_LOG' \
#     [--arms no-skill,ponytail,tightloop] [--only <task>]
#
# Per task x arm the runner writes ONE raw line to results/<run-id>/lines.tsv:
#   run_id  task  arm  tokens_in  tokens_out  wall_s  tests_passed  tests_total  diff_lines  status
# plus artifacts under results/<run-id>/<task>/<arm>/:
#   agent.log  usage.json  tests.json  diff.patch
#
# Hard rules:
# - tokens come from the agent CLI's own usage report (usage.json); if it
#   cannot be produced, the line's status is NO_USAGE and nothing is
#   estimated.
# - hidden tests are applied AFTER the agent finishes, from the task's
#   pinned patch; the check command comes from the task file.
# - no averages here; score.py turns lines into tables.
set -u
fail=0
step() { printf '== %s\n' "$1"; }

TASKS=""
AGENT_CMD=""
ARMS="no-skill,ponytail,tightloop"
ONLY=""
while [ $# -gt 0 ]; do
  case "$1" in
    --tasks) TASKS="$2"; shift 2 ;;
    --agent-cmd) AGENT_CMD="$2"; shift 2 ;;
    --arms) ARMS="$2"; shift 2 ;;
    --only) ONLY="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
[ -n "$TASKS" ] || { echo "need --tasks" >&2; exit 2; }
[ -f "$TASKS" ] || { step "no task set at $TASKS - nothing to run"; exit 1; }
[ -n "$AGENT_CMD" ] || { echo "need --agent-cmd (the coding agent invocation template)" >&2; exit 2; }
command -v jq >/dev/null || { echo "need jq" >&2; exit 2; }

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="benchmark/results/$RUN_ID"
mkdir -p "$OUT"
OUT="$(cd "$OUT" && pwd)"
printf '{"run_id":"%s","arms":"%s","tasks_file":"%s","agent_cmd":%s}\n' \
  "$RUN_ID" "$ARMS" "$TASKS" "$(jq -Rn --arg c "$AGENT_CMD" '$c')" > "$OUT/run.json"
printf 'run_id\ttask\tarm\ttokens_in\ttokens_out\twall_s\ttests_passed\ttests_total\tdiff_lines\tstatus\n' > "$OUT/lines.tsv"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

run_arm() { # task_json arm
  local TJ="$1" ARM="$2"
  local NAME SRC START INSTR PATCH CHECK
  NAME=$(jq -r .name "$TJ"); SRC=$(jq -r .source "$TJ")
  START=$(jq -r .start_commit "$TJ"); INSTR=$(jq -r .instruction "$TJ")
  PATCH=$(jq -r .hidden_patch "$TJ"); CHECK=$(jq -r .check_command "$TJ")
  local DIR="$OUT/$NAME/$ARM"
  local WORK="$DIR/work"
  mkdir -p "$DIR"
  export DIR
  git clone -q "$SRC" "$WORK" || { echo clone-failed; return; }
  git -C "$WORK" checkout -q "$START" || { echo checkout-failed; return; }
  "$SCRIPT_DIR/arms/$ARM.sh" "$REPO_ROOT" "$WORK" || { echo arm-setup-failed; return; }

  local INSTRUCTION_FILE="$DIR/instruction.md" AGENT_LOG="$DIR/agent.log"
  printf '%s\n' "$INSTR" > "$INSTRUCTION_FILE"
  export INSTRUCTION_FILE AGENT_LOG WORK
  local T0 T1 WALL
  T0=$(date +%s)
  ( cd "$WORK" && eval "$AGENT_CMD" ) >>"$AGENT_LOG" 2>&1
  T1=$(date +%s); WALL=$((T1 - T0))

  # tokens: the agent command must leave usage.json in $DIR (adapter duty);
  # accept common shapes, else NO_USAGE.
  local TIN TOUT STATUS
  TIN=""; TOUT=""
  if [ -f "$DIR/usage.json" ]; then
    TIN=$(jq -r '.tokens_in // .usage.input_tokens // .usage.input // empty' "$DIR/usage.json")
    TOUT=$(jq -r '.tokens_out // .usage.output_tokens // .usage.output // empty' "$DIR/usage.json")
  fi
  if [ -z "$TIN" ] || [ -z "$TOUT" ]; then STATUS="NO_USAGE"; TIN=""; TOUT=""; fi

  # hidden tests: apply the pinned patch, run the check command
  local TP=0 TT=0
  if [ -n "$PATCH" ] && [ "$PATCH" != "null" ]; then
    git -C "$WORK" apply --whitespace=nowarn "$REPO_ROOT/benchmark/tasks/$PATCH" \
      || { STATUS="PATCH_FAIL"; }
    if [ "${STATUS:-}" != "PATCH_FAIL" ]; then
      TT=$(jq -r '.hidden_tests | length' "$TJ")
      if ( cd "$WORK" && eval "$CHECK" ) >"$DIR/tests.log" 2>&1; then
        TP=$TT
      else
        TP=0
        STATUS="TESTS_FAIL"
      fi
      printf '{"check_command":%s,"hidden_tests":%s,"all_passed":%s}
' \
        "$(jq -Rn --arg c "$CHECK" '$c')" "$(jq -c .hidden_tests "$TJ")" \
        "$([ "$TP" = "$TT" ] && echo true || echo false)" > "$DIR/tests.json"
    fi
  fi
  git -C "$WORK" diff --numstat | awk '{a+=$1; d+=$2} END {print a+d+0}' > "$DIR/.dlines" 2>/dev/null || echo 0 > "$DIR/.dlines"
  local DL; DL=$(cat "$DIR/.dlines"); DL=${DL:-0}
  [ -n "${STATUS:-}" ] || STATUS="OK"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$RUN_ID" "$NAME" "$ARM" "$TIN" "$TOUT" "$WALL" "$TP" "$TT" "$DL" "$STATUS" \
    >> "$OUT/lines.tsv"
}

jq -c '.[]' "$TASKS" | while read -r TASKLINE; do
  TJ="$OUT/.task.json"; printf '%s' "$TASKLINE" > "$TJ"
  NAME=$(jq -r .name "$TJ")
  [ -n "$ONLY" ] && [ "$ONLY" != "$NAME" ] && continue
  IFS=',' read -ra AL <<< "$ARMS"
  for ARM in "${AL[@]}"; do
    step "task $NAME arm $ARM"
    run_arm "$TJ" "$ARM"
  done
done

step "done: $OUT/lines.tsv"
exit "$fail"
