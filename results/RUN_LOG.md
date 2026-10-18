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

## fd-03 excluded (Naman, 2026-10-18 ~14:27Z, option b)

fd-03 excluded: hidden test cannot tell the half fix from the real fix when threads > 1 (src/exec/job.rs buffer_output = threads > 1); grader check: real fix PASS 43 s, empty FAIL 44 s, half fix PASS 37 s; fallback did not fire. Evidence: 0c09c75 (results/grader_sanity/fd-03_*).

Note: a grader variant that also runs the test with --threads 1 is an idea for a LATER pass only; it is not applied now. No fd-03 arm session was run and no grader or harness edit was made for fd-03.

No further task is in this pass's queue (benchmark/FREEZE.md: first pass = fd-01, fd-02, fd-03, gin-01, gin-02).

## Pass 2 harness (2026-10-18 ~14:45Z): what changed and why

Arms: no-skill, ponytail, tightloop-v3, tightloop-v4 (all 4 back to back per task). Tasks: fd-01, gin-01, gin-02. fd-02 and fd-03 stay dropped; holdout-split.json untouched.

- tightloop-v3 reads benchmark/arms/tightloop-v3/SKILL.md and refuses to run unless its sha256 is f83ba03a192729f84e8d448680fa69dcadf41483f9ae056e6bba7dfc19d1bd6a (v3 as at d3a3680). tightloop-v4 reads .claude/skills/tightloop/SKILL.md.
- Skill folder in the checkout, same rule for every arm (Naman, 8:07 PM IST): before the session, the arm's skill folder is copied into the fresh checkout and git-excluded (.git/info/exclude), so it never enters the diff, the rename rule or grading. ponytail: .claude/skills/ponytail/SKILL.md (the pinned file). tightloop-v3: its folder (SKILL.md only) at .claude/skills/tightloop/. tightloop-v4: .claude/skills/tightloop/ (SKILL.md, gate.sh, phases/). no-skill: nothing at all (no system-prompt text, no files). The SKILL.md text is still also passed with --append-system-prompt, as in pass 1.
- Claude Code now runs with --output-format stream-json --verbose on every arm. tool_calls = distinct tool_use ids in the event stream, an exact count (subagent calls included; tool_calls_main = those not inside a subagent; tool_calls_by_name per tool). Tokens are read from the final result event, the same fields as before.
- tokens now also carry cache_read and cache_creation separately (tokens.cache is still their sum). score.py reports the median per-task ratio for input+output, input+output+cache, and input+output+cache_read (MEASURE.md's definition), and scores each pass separately.
- Rows carry pass=2, arm_version, skill_files (path, bytes, sha256), agent_diff_added / agent_diff_deleted.
- Unchanged: the rename rule and the hidden-patch fallback exactly as in 2c7a6fd; --wait-lock-max 0 (lock only sampled for the overlap tag); --min-free-mib 1900; CLI 2.1.302; model claude-opus-5-5; fresh checkout per run.
- Unit check without an agent: results/harness_checks/pass2_unit.txt.

Comparability: the first-pass rows (no-skill, ponytail, and v3 as "tightloop") ran without the skill folder in the checkout and with --output-format json. They are NOT directly comparable to pass-2 rows. v3 is rerun under the pass-2 harness, so all 4 pass-2 arms are same-harness. First-pass rows stay in rows.jsonl untouched.

Defect score: unmeasured. MEASURE.md describes a reviewer agent, but the harness has none; a concrete reviewer proposal waits for Naman's OK.
