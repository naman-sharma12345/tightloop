# GATEFIX: the second-FAIL bug in gate.sh, and the tokio-02 rerun

Owner order: Naman m:d262995f (1:22 PM IST, Oct 19). Branch v6/gatefix, fast-forward from v6/v10 bbadd86001d26ee741c22d8d633bff839085a233.

## The bug
gate.sh line 25 (same bytes in tightloop-v4c and tightloop-v10):

    NOTESTS='running 0 tests|no tests to run|0 passed; 0 failed|collected 0 items|No tests found'

Line 49: `if [ $rc -ne 0 ] || grep -Eq "$NOTESTS" "$tmp/with.out"; then echo "TEST FAIL (exit $rc):" ...`

The alternative `0 passed; 0 failed` has no left edge, so it matches inside `10 passed; 0 failed`
(and 20, 30, 100 ... any count ending in 0). A passing cargo run is reported "TEST FAIL (exit 0)" and the gate ends "GATE FAIL".
This is what happened on the second gate of all 3 v10 tokio-02 runs (v10 rows 10-12: cargo printed
"test result: ok. 10 passed; 0 failed", gate said TEST FAIL (exit 0) / GATE FAIL).

## The fix (one line, in two new arms; the old arms are untouched)
- benchmark/arms/tightloop-v4c-gfix = byte copy of tightloop-v4c except line 25
- benchmark/arms/tightloop-v10-gfix = byte copy of tightloop-v10 except line 25

    NOTESTS='running 0 tests|no tests to run|(^|[^0-9])0 passed; 0 failed|collected 0 items|No tests found'

`running 0 tests`, `collected 0 items` are left as they are: the fixed word before the 0 already stops them matching
`running 10 tests` / `collected 10 items` (dry check below).

## Dry check (grep -E with each arm's own line 25, canned text, no model run)
| text | v4c / v10 (old) | v4c-gfix / v10-gfix |
|---|---|---|
| test result: ok. 10 passed; 0 failed; 0 ignored ... | MATCH (bug) | no match |
| 20 passed; 0 failed | MATCH (bug) | no match |
| test result: ok. 0 passed; 0 failed; 0 ignored | MATCH | MATCH |
| 0 passed; 0 failed | MATCH | MATCH |
| running 0 tests | MATCH | MATCH |
| running 10 tests | no match | no match |
| testing: warning: no tests to run | MATCH | MATCH |
| collected 0 items | MATCH | MATCH |
| collected 10 items | no match | no match |

End to end, whole gate.sh in a scratch git repo, test command printing "running 10 tests / test result: ok. 10 passed; 0 failed" with exit 0:
old v4c and v10 -> "TEST FAIL (exit 0)" + "GATE FAIL"; v4c-gfix and v10-gfix -> "test ok:" + "GATE PASS".

## Registration
benchmark/runner.py, the same 2-line pattern v10 used: one line added to ARMS, and the two names appended to the
skill-hash tuple line in main(). Nothing else in the harness, grader or task files changes.

## Rerun (ORDER_gatefix.json, committed before the first run)
tokio-02 only, n=3 per arm, strict alternation v4c-gfix, v10-gfix x3. Same per-session logic as the v10 pass
(seq.py from the v10 worker: go clean -cache before each session, disk floor 3000 MiB, sampler 6735e9c236a1,
KIMO_WINDOWS parser v7, a sidecar per row). Rows: gatefix/rows.jsonl (v10 row keys plus call1_cache).
gatefix/calls.jsonl: per row, model calls, tool calls, call-1 cache, each gate verdict, hidden-test result.
Question: is v10's tokio-02 saving (old v4c 5/5/6 model calls vs v10 4/4/4) real, or "stopped early" after a false FAIL?
