# Run log (first pass)

Times UTC, 2026-10-18. Raw rows: rows.jsonl. Every row is kept; its status says
whether it counts.

## fd-01 (redo, harness 21e14a9, rows with status "ok...")

All 3 arms ran back to back, all tagged overlapped, all PASS.

| arm | input | output | cache | wall s | rename rule fired |
| --- | --- | --- | --- | --- | --- |
| no-skill | 18 | 3260 | 245597 | 104.0 | yes: test_and_pattern_with_forward_slash_is_rejected |
| ponytail | 14 | 2117 | 192365 | 81.7 | no |
| tightloop | 22 | 3585 | 359530 | 111.2 | yes: test_and_pattern_with_forward_slash_is_rejected |

Note: single overlapped run, n=1 per arm: tightloop used more tokens and wall
than no-skill (22/3585/359.5k, 111 s vs 18/3260/245.6k, 104 s); ponytail lowest
on both (14/2117/192.4k, 82 s). Data point only, no claim either way.

Rename rule detail. no-skill and tightloop each ADDED a new test function in
tests/tests.rs named test_and_pattern_with_forward_slash_is_rejected, the hidden
test's exact name; the rule renamed that added function to
..._agent before the hidden patch went in. no-skill also added
test_and_pattern_with_forward_slash_allowed_with_full_path (no collision, left
alone). ponytail added no new test function: it added one more
assert_failure_with_error call (`foo --and one/two`) inside the existing
test_pattern_with_forward_slash_is_rejected, so nothing collided and the rule
did not fire.

Earlier fd-01 rows, kept and not counted: 3 rows invalid-harness (name
collision, harness before 9925b99); 2 rows superseded (no-skill and ponytail
redo on 9925b99 before the overlap tag existed).

## gin-01: 3 invalid rows, cause, fix

The first 3 gin-01 rows (harness 21e14a9) are all result "invalid": the grader
never ran. Same cause on all 3 arms, word for word in each row's diff field:
"hidden patch did not apply: error: patch failed: recovery_test.go:142".
Each agent added its own test to recovery_test.go right after
TestPanicWithBrokenPipe, which is exactly where the hidden patch inserts
TestPanicWithAbortHandler, so the patch's context lines no longer matched.
no-skill and tightloop named theirs TestPanicWithAbortHandler (the rename rule
fired first, then the apply still failed on context); ponytail named its test
TestPanicWithErrAbortHandler and failed the same way. The earlier grader check
(real fix PASS) did not see this because the real fix touches only
recovery.go.

Fix: harness commit d30248527ca81878d46433c00448e231c295f424 (runner only, same for every arm): when the hidden
patch does not apply, the files it touches (here only recovery_test.go) are
restored to the start commit, dropping the agent's own edits in those files
only, and the patch is applied again; the raw agent diff is saved before
grading as always, and each row records hidden_patch_fallback and reset_files.
Rows whose patch applies directly are graded exactly as before. Unit check:
harness_checks/hidden_patch_fallback_check.json (the outcomes there on the 3
saved gin-01 diffs are a harness diagnostic, not rows). Those 3 rows are kept,
outputs/logs/diffs untouched, status now "invalid-harness (hidden patch
context conflict ...)". gin-01 is redone on all 3 arms under the fix.

## gin-02 (harness 21e14a9)

3/3 PASS, all overlapped, rename rule did not fire on any arm, the hidden patch
applied directly on all 3 (rows predate the hidden_patch_fallback field).

## fd-02

Dropped from this pass: grader_sanity/fd-02_status.txt (upstream commit
ed47664 itself fails its hidden test here: fd smart case also matches
one/two/C.Foo2). No fd-02 rows exist.

## gin-01 redo (harness d302485, 3 arms back to back, 14:18-14:21Z)

| arm | result | input | output | cache | wall s | overlap | rename fired | hidden-patch fallback (agent lines dropped) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| no-skill | PASS | 8 | 1869 | 129112 | 21.92 | overlapped | yes: TestPanicWithAbortHandler | yes: recovery_test.go +25/-0 |
| ponytail | PASS | 10 | 1828 | 168088 | 21.11 | overlapped | yes: TestPanicWithAbortHandler | yes: recovery_test.go +18/-0 |
| tightloop | PASS | 10 | 2420 | 188563 | 34.34 | overlapped | yes: TestPanicWithAbortHandler | yes: recovery_test.go +21/-0 |

On all 3 arms the agent again added its own TestPanicWithAbortHandler to recovery_test.go; the rename fired, the first apply still failed on context, and the fallback restored recovery_test.go before the hidden patch went in. The grader ran on all 3.

## Notes (Naman, 2026-10-18 ~14:24Z)

The grader scores the fix only, so agent-written tests in files the hidden patch touches are dropped and test-writing quality is not measured in these rows.

gin-01 (redo) and gin-02 are 3/3 PASS on every arm, so no arm separates on pass rate so far. Tokens and time are n=1 per arm and overlapped: data points only, no claim.

## fd-03 grader triple (holdout) - STOP

See grader_sanity/fd-03_triple_STOP.txt: real fix PASS, empty FAIL, half fix PASS (expected FAIL).
fd-03 arms not run; waiting for Naman's decision.
