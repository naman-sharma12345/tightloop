#!/usr/bin/env bash
# tightloop ship gate. usage: gate.sh "<test command>" [source files you changed]
# 1 prove: with the listed source changes removed, the test must FAIL
# 2 test:  with them back, the test must PASS
# 3 diff:  format (per language), whitespace, debug leftovers, size; then the diff
# Exit 0 and "GATE PASS" only if 1-3 hold. All output is capped.
# Removed changes are backed up in .git/tightloop-gate/ and restored on any exit;
# a backup left by a killed run is restored at the start of the next run.
set -u
[ $# -ge 1 ] || { echo "usage: gate.sh \"<test command>\" [source files]"; exit 2; }
cmd=$1; shift
top=$(git rev-parse --show-toplevel) || exit 2
cd "$top" || exit 2
bk="$(git rev-parse --absolute-git-dir)/tightloop-gate"
restore() {
  [ -f "$bk/files" ] || { rm -rf "$bk"; return; }
  while IFS= read -r f; do
    # cp -p keeps the mode; touch makes the file newer than build outputs of the reverted copy
    if [ -e "$bk/tree/$f" ]; then mkdir -p "$(dirname "$f")"; cp -p "$bk/tree/$f" "$f"; touch "$f"; fi
  done < "$bk/files"
  rm -rf "$bk"
}
[ -d "$bk" ] && { echo "restored files left by an interrupted gate run"; restore; }
tmp=$(mktemp -d); fail=0
NOTESTS='running 0 tests|no tests to run|0 passed; 0 failed|collected 0 items|No tests found'
if [ $# -gt 0 ]; then
  mkdir -p "$bk/tree" || exit 2
  for f in "$@"; do mkdir -p "$bk/tree/$(dirname "$f")"; cp -p "$f" "$bk/tree/$f" || { rm -rf "$bk"; exit 2; }; done
  printf '%s\n' "$@" > "$bk/files"
  trap 'restore; rm -rf "$tmp"' EXIT
  trap 'exit 130' INT TERM HUP
  for f in "$@"; do
    if git cat-file -e "HEAD:$f" 2>/dev/null; then git show "HEAD:$f" > "$f"; else rm -f "$f"; fi
  done
  bash -c "$cmd" > "$tmp/without.out" 2>&1; rc=$?
  restore
  if grep -Eq "$NOTESTS" "$tmp/without.out"; then
    echo "PROVE UNKNOWN: no test ran without the change (test in a listed file?). Prove it by hand."; fail=1
  elif [ $rc -eq 0 ]; then
    echo "PROVE FAIL: the test passes without your change, so it does not prove the fix."; fail=1
  else
    echo "prove ok: test fails without the change (exit $rc). Last lines:"; tail -n 8 "$tmp/without.out"
  fi
else
  trap 'rm -rf "$tmp"' EXIT
  echo "prove skipped: no source files given"
fi
bash -c "$cmd" > "$tmp/with.out" 2>&1; rc=$?
if [ $rc -ne 0 ] || grep -Eq "$NOTESTS" "$tmp/with.out"; then
  echo "TEST FAIL (exit $rc):"; tail -n 30 "$tmp/with.out"; fail=1
else
  echo "test ok:"; tail -n 3 "$tmp/with.out"
fi
changed=$( { git diff --name-only HEAD; git ls-files --others --exclude-standard; } | sort -u)
go=$(printf '%s\n' $changed | grep '\.go$'); rs=$(printf '%s\n' $changed | grep '\.rs$')
for f in $go; do [ -f "$f" ] && [ -n "$(gofmt -l "$f" 2>/dev/null)" ] && { echo "FORMAT: run gofmt -w $f"; fail=1; }; done
if [ -n "$rs" ]; then
  if [ -f Cargo.toml ] && cargo fmt --version >/dev/null 2>&1; then out=$(cargo fmt --check 2>&1)
  elif rustfmt --version >/dev/null 2>&1; then out=$(rustfmt --check $rs 2>&1)
  else out=""; echo "format unchecked: rustfmt is not installed"; fi
  for f in $rs; do
    printf '%s\n' "$out" | grep -q "^Diff in .*$f" && { echo "FORMAT: run rustfmt on $f"; fail=1; }
  done
fi
git diff --check HEAD | head -n 10 | grep . && { echo "WHITESPACE errors above"; fail=1; }
git diff -U0 HEAD | grep -nE '^\+.*(dbg!|console\.log|println!\("(debug|DEBUG)|fmt\.Print|TODO|FIXME|XXX)' | head -n 5 |
  sed 's/^/debug? /'
git diff --shortstat HEAD; n=$(git ls-files --others --exclude-standard | wc -l); [ "$n" -gt 0 ] && echo "$n new file(s)"
git diff HEAD | head -n 80
[ $fail -eq 0 ] && { echo "GATE PASS"; exit 0; }
echo "GATE FAIL"; exit 1
