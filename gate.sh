#!/usr/bin/env bash
set -u
fail=0
step() { printf '== %s\n' "$1"; shift; if ! "$@" 2>&1 | tail -30; then :; fi; }
run() { if ! "$@" >/tmp/tl.out 2>&1; then tail -30 /tmp/tl.out; echo "GATE FAIL: $*"; fail=1; else echo "ok: $*"; fi; }
# edit these for the project
run cargo build -q            # or: npm run build / python -m compileall .
run cargo clippy -q -- -D warnings
run cargo fmt --check
run cargo test -q             # or: pytest -q / npm test --silent
echo "== diff size"; git diff --stat | tail -3
echo "== untracked"; git status --short | head -20
[ "$fail" = 0 ] && echo "GATE PASS" || { echo "GATE FAIL"; exit 1; }
