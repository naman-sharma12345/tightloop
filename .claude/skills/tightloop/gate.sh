#!/usr/bin/env bash
# tightloop ship gate. usage: gate.sh "<test command>" [source files you changed]
# 1 prove: with the listed source changes removed, the test must FAIL
# 2 test:  with them back, the test must PASS
# 3 diff:  format, whitespace, debug leftovers, size; then the diff itself
# Exit 0 and "GATE PASS" only if 1-3 hold. All output is capped.
set -u
[ $# -ge 1 ] || { echo "usage: gate.sh \"<test command>\" [source files]"; exit 2; }
cmd=$1; shift
top=$(git rev-parse --show-toplevel) || exit 2
cd "$top" || exit 2
tmp=$(mktemp -d); fail=0
NOTESTS='running 0 tests|no tests to run|0 passed; 0 failed|collected 0 items|No tests found'
restore() { for f in "$@"; do [ -e "$tmp/$f" ] && cp -p "$tmp/$f" "$f"; done; }
if [ $# -gt 0 ]; then
  for f in "$@"; do mkdir -p "$tmp/$(dirname "$f")"; cp -p "$f" "$tmp/$f" || exit 2; done
  trap 'restore "$@"; rm -rf "$tmp"' EXIT
  for f in "$@"; do
    if git cat-file -e "HEAD:$f" 2>/dev/null; then git show "HEAD:$f" > "$f"; else rm -f "$f"; fi
  done
  bash -c "$cmd" > "$tmp/without.out" 2>&1; rc=$?
  restore "$@"
  if grep -Eq "$NOTESTS" "$tmp/without.out"; then
    echo "PROVE UNKNOWN: no test ran without the change (test in a listed file?). Prove it by hand."; fail=1
  elif [ $rc -eq 0 ]; then
    echo "PROVE FAIL: the test passes without your change, so it does not prove the fix."; fail=1
  else
    echo "prove ok: test fails without the change (exit $rc). Last lines:"; tail -n 8 "$tmp/without.out"
  fi
else
  echo "prove skipped: no source files given"
fi
bash -c "$cmd" > "$tmp/with.out" 2>&1; rc=$?
if [ $rc -ne 0 ] || grep -Eq "$NOTESTS" "$tmp/with.out"; then
  echo "TEST FAIL (exit $rc):"; tail -n 30 "$tmp/with.out"; fail=1
else
  echo "test ok:"; tail -n 3 "$tmp/with.out"
fi
changed=$( { git diff --name-only HEAD; git ls-files --others --exclude-standard; } | sort -u)
for f in $changed; do
  [ -f "$f" ] || continue
  case "$f" in
    *.go) command -v gofmt >/dev/null && [ -n "$(gofmt -l "$f")" ] && { echo "FORMAT: run gofmt -w $f"; fail=1; } ;;
    *.rs) command -v rustfmt >/dev/null && ! rustfmt --check --edition 2021 "$f" >/dev/null 2>&1 &&
          echo "format warn: rustfmt differs on $f (fix only lines you changed)" ;;
  esac
done
git diff --check HEAD | head -n 10 | grep . && { echo "WHITESPACE errors above"; fail=1; }
git diff -U0 HEAD | grep -nE '^\+.*(dbg!|console\.log|println!\("(debug|DEBUG)|fmt\.Print|TODO|FIXME|XXX)' | head -n 5 |
  sed 's/^/debug? /'
git diff --shortstat HEAD; n=$(git ls-files --others --exclude-standard | wc -l); [ "$n" -gt 0 ] && echo "$n new file(s)"
git diff HEAD | head -n 80
[ $fail -eq 0 ] && { echo "GATE PASS"; exit 0; }
echo "GATE FAIL"; exit 1
