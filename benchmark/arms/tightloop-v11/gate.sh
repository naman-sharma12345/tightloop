#!/usr/bin/env bash
# tightloop v11 ship gate. usage: gate.sh "<full test command>" [changed files]
# Test files are never reverted; with no files listed, the changed code files from git are used.
# 0 format: gofmt / cargo fmt the changed files (fixed for you, and said so)
# 1 test:  with your change the test must PASS (run first, so a broken command is named, not taken as proof)
# 2 prove: with the changed code files back at HEAD the test must FAIL (a code change needs a test
#          that fails without it). Exempt: test-only changes (every changed file is a test file) and
#          config/docs-only changes (no changed file has a code extension): prove is skipped and said so.
# 3 check: no whitespace errors; possible debug leftovers are listed (not a failure, as in v4c)
# No diff is printed. Output is short and the LAST line is the verdict with its reason.
# Reverted files are backed up in .git/tightloop-gate/ and restored on any exit;
# a backup left by a killed run is restored at the start of the next run.
set -u
[ $# -ge 1 ] || { echo "GATE FAIL: usage: gate.sh \"<full test command>\" [changed files]"; exit 2; }
cmd=$1; shift
top=$(git rev-parse --show-toplevel) || exit 2
cd "$top" || exit 2
bk="$(git rev-parse --absolute-git-dir)/tightloop-gate"
tmp=$(mktemp -d)
reason=""
fail() { [ -n "$reason" ] || reason=$1; }
verdict() {
  if [ -z "$reason" ]; then echo "GATE PASS ($1)"; exit 0; fi
  echo "GATE FAIL: $reason"; exit 1
}
restore() {
  [ -f "$bk/files" ] || { rm -rf "$bk"; return; }
  while IFS= read -r f; do
    # cp -p keeps the mode; touch makes the file newer than build outputs of the reverted copy
    if [ -e "$bk/tree/$f" ]; then mkdir -p "$(dirname "$f")"; cp -p "$bk/tree/$f" "$f"; touch "$f"; fi
  done < "$bk/files"
  rm -rf "$bk"
}
[ -d "$bk" ] && { echo "restored files left by an interrupted gate run"; restore; }
trap 'restore; rm -rf "$tmp"' EXIT
trap 'exit 130' INT TERM HUP

TESTFILE='(_test\.go$|_test\.py$|(^|/)test_[^/]*\.py$|(^|/)tests?/|\.(test|spec)\.[cm]?[jt]sx?$)'
# '0 passed; 0 failed' is anchored: unanchored it matched "10 passed; 0 failed" and failed passing runs (v4c/v10)
NOTESTS='running 0 tests|no tests to run|(^|[^0-9])0 passed; 0 failed|collected 0 items|No tests found'
RAN='test result: ok\. [1-9]|^ok[[:space:]]|[1-9][0-9]* passed|^PASS$|--- PASS|^OK'
STRONG='error(\[|:)|^error|--- FAIL|panicked|Error:|Exception:|undefined:|cannot find'
ERR="$STRONG|assert|expected|not found"
START="Traceback|$ERR"
CODE='\.(go|rs|py|js|jsx|ts|tsx|mjs|cjs|java|kt|c|h|cc|cpp|hpp|rb|php|swift|cs|scala|sh)$'
NOISE='^[[:space:]]*(Compiling|Downloading|Downloaded|Blocking|Updating|Locking|Finished|Running|Fresh|Checking) '
first_err() {  # the first error line, else the last non-blank line
  { grep -vE "$NOISE" "$1" | grep -m1 -E "$STRONG" || grep -vE "$NOISE" "$1" | grep -m1 -E "$ERR" || grep -v '^[[:space:]]*$' "$1" | tail -n 1; } | sed 's/^[[:space:]]*//' | cut -c1-160
}
show_err() {  # up to 15 lines from the first error, else the last 15 lines
  grep -vE "$NOISE" "$1" > "$tmp/clean"
  n=$(grep -n -m1 -E "$START" "$tmp/clean" | cut -d: -f1)
  if [ -n "$n" ]; then sed -n "${n},$((n + 14))p" "$tmp/clean"; else tail -n 15 "$tmp/clean"; fi
}
notests() { grep -Eq "$NOTESTS" "$1" && ! grep -E "$RAN" "$1" | grep -vEq "$NOTESTS"; }  # cargo prints 'running 0 tests' for binaries the filter skips
changed_files() { { git diff --name-only HEAD; git ls-files --others --exclude-standard; } | sort -u; }

# a bare test name is not a command
w=${cmd%% *}
if [ "$w" = "$cmd" ] && ! command -v "$w" >/dev/null 2>&1; then
  fail "COMMAND: '$cmd' is not a command. Pass the full test command, e.g. go test -run TestX ./pkg/ or cargo test --test <file> <name>"
  verdict ""
fi

# source files to revert for the proof; test files are never reverted
src=()
for f in "$@"; do
  if printf '%s\n' "$f" | grep -Eq "$TESTFILE"; then echo "not reverting $f (test file)"; else src+=("$f"); fi
done

# 0 format
changed=$(changed_files)
for f in $(printf '%s\n' $changed | grep '\.go$'); do
  [ -f "$f" ] && [ -n "$(gofmt -l "$f" 2>/dev/null)" ] && gofmt -w "$f" && echo "formatted $f (gofmt)"
done
rs=$(printf '%s\n' $changed | grep '\.rs$')
if [ -n "$rs" ]; then
  if [ -f Cargo.toml ] && cargo fmt --version >/dev/null 2>&1; then
    bad=$(cargo fmt --check 2>/dev/null | sed -nE 's/^Diff in (.*\.rs)( at line |:[0-9]).*/\1/p' | sed "s#^$top/##" | sort -u)
    others=$(printf '%s\n' $bad | grep -vxF -f <(printf '%s\n' $rs))
    if [ -n "$bad" ] && [ -z "$others" ]; then cargo fmt >/dev/null 2>&1 && echo "formatted $(echo $bad) (cargo fmt)"
    else for f in $rs; do printf '%s\n' $bad | grep -qxF "$f" && fail "FORMAT: run rustfmt on $f only"; done; fi
  else echo "format unchecked: cargo fmt is not installed"; fi
fi

# 1 test, with the change
pre=$reason; reason=""
bash -c "$cmd" > "$tmp/with.out" 2>&1; rc=$?
if [ $rc -eq 127 ] || grep -q 'command not found' "$tmp/with.out"; then
  show_err "$tmp/with.out"
  fail "COMMAND NOT FOUND: pass the full test command, e.g. go test -run TestX ./pkg/ or cargo test --test <file> <name>"
elif notests "$tmp/with.out"; then
  fail "NO TEST RAN: the filter matched no test; check the test name and package path"
elif [ $rc -ne 0 ]; then
  show_err "$tmp/with.out"
  fail "TEST FAIL (exit $rc): $(first_err "$tmp/with.out"). Fix the first error; recheck the root cause in the code, not the test"
else
  echo "test ok: $(grep -vE "$NOISE" "$tmp/with.out" | grep -v '^[[:space:]]*$' | tail -n 1 | cut -c1-160)"
fi
[ -n "$reason" ] && verdict ""
reason=$pre

# 2 prove, without the change
changed=$(changed_files)
new=$(git ls-files --others --exclude-standard)
added() { git diff -U0 HEAD | grep -E '^\+[^+]'; for f in $new; do [ -f "$f" ] && sed 's/^/+/' "$f"; done; }
code_src=$(printf '%s\n' $changed | grep -E "$CODE" | grep -vE "$TESTFILE")
has_test=no
{ printf '%s\n' $changed | grep -Eq "$TESTFILE" ||
  added | grep -Eq '#\[(tokio::)?test|func Test|def test_|(^|[^a-zA-Z_.])(it|test|describe)\('; } && has_test=yes
if [ ${#src[@]} -eq 0 ] && [ -n "$code_src" ]; then
  while IFS= read -r f; do src+=("$f"); done <<< "$code_src"
  echo "proving with the changed code files: ${src[*]}"
fi
if [ ${#src[@]} -eq 0 ]; then
  if [ $has_test = yes ]; then echo "prove skipped: test-only change"
  else echo "prove skipped: no code file changed (config or docs only)"; fi
else
  mkdir -p "$bk/tree" || exit 2
  for f in "${src[@]}"; do
    [ -e "$f" ] || git cat-file -e "HEAD:$f" 2>/dev/null || { fail "NO SUCH FILE: $f"; continue; }
    if [ -e "$f" ]; then mkdir -p "$bk/tree/$(dirname "$f")"; cp -p "$f" "$bk/tree/$f"; fi
  done
  printf '%s\n' "${src[@]}" > "$bk/files"
  [ -n "$reason" ] && { restore; verdict ""; }
  for f in "${src[@]}"; do
    if git cat-file -e "HEAD:$f" 2>/dev/null; then git show "HEAD:$f" > "$f"; else rm -f "$f"; fi
  done
  bash -c "$cmd" > "$tmp/without.out" 2>&1; rc=$?
  restore
  if [ $rc -ne 0 ]; then
    echo "prove ok: fails without the change: $(first_err "$tmp/without.out")"
  elif notests "$tmp/without.out"; then
    fail "PROVE UNKNOWN: no test ran without the change (is the test inside a listed file?). Revert only the fix lines by hand once, run, restore"
  elif [ -z "$code_src" ]; then
    echo "not proven: the test also passes without this config change"
  else
    fail "PROVE FAIL: the test passes without your change; assert the exact input and output the task names"
  fi
fi

# 3 checks. A code change must come with a test that fails without it: the prove step above
# enforces that (PROVE FAIL / PROVE UNKNOWN). Test-only and config-only changes are exempt (no code file changed).
ws=$(git diff --check HEAD | head -n 1)
[ -n "$ws" ] && fail "WHITESPACE: $ws"
added | grep -E 'dbg!|console\.log|println!\("(debug|DEBUG)|fmt\.Print|TODO|FIXME|XXX' | head -n 3 | cut -c1-120 | sed 's/^/debug? /'
size=$(git diff --shortstat HEAD | sed 's/^ *//'); n=$(printf '%s\n' $new | grep -c .)
[ "$n" -gt 0 ] && size="$size, $n new file(s)"
verdict "$size"
