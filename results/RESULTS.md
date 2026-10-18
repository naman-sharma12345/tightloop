# tightloop first pass: results

2026-10-18 UTC. Raw rows: rows.jsonl (every row kept). Run log with every
harness change and decision: RUN_LOG.md. score.py output: score_output.txt.

## Raw rows counted (n=1 per arm, all tagged overlapped)

| task | arm | result | input | output | cache | total | wall s | turns | tool calls | overlap | rename fired (test) | hidden-patch fallback (agent lines dropped) | harness | log |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fd-01 | no-skill | PASS | 18 | 3260 | 245597 | unmeasured | 104.03 | 9 | unmeasured | overlapped | yes: test_and_pattern_with_forward_slash_is_rejected | no (field added later; patch applied directly) | 21e14a9 | logs/fd-01_no-skill_1_attempt3.* |
| fd-01 | ponytail | PASS | 14 | 2117 | 192365 | unmeasured | 81.7 | 7 | unmeasured | overlapped | no | no (field added later; patch applied directly) | 21e14a9 | logs/fd-01_ponytail_1_attempt3.* |
| fd-01 | tightloop | PASS | 22 | 3585 | 359530 | unmeasured | 111.24 | 12 | unmeasured | overlapped | yes: test_and_pattern_with_forward_slash_is_rejected | no (field added later; patch applied directly) | 21e14a9 | logs/fd-01_tightloop_1_attempt2.* |
| gin-01 | no-skill | PASS | 8 | 1869 | 129112 | unmeasured | 21.92 | 4 | unmeasured | overlapped | yes: TestPanicWithAbortHandler | yes: recovery_test.go +25/-0 | 2c7a6fd | logs/gin-01_no-skill_1_attempt2.* |
| gin-01 | ponytail | PASS | 10 | 1828 | 168088 | unmeasured | 21.11 | 5 | unmeasured | overlapped | yes: TestPanicWithAbortHandler | yes: recovery_test.go +18/-0 | 2c7a6fd | logs/gin-01_ponytail_1_attempt2.* |
| gin-01 | tightloop | PASS | 10 | 2420 | 188563 | unmeasured | 34.34 | 6 | unmeasured | overlapped | yes: TestPanicWithAbortHandler | yes: recovery_test.go +21/-0 | 2c7a6fd | logs/gin-01_tightloop_1_attempt2.* |
| gin-02 | no-skill | PASS | 10 | 2179 | 132171 | unmeasured | 25.99 | 5 | unmeasured | overlapped | no | no (field added later; patch applied directly) | 21e14a9 | logs/gin-02_no-skill_1.* |
| gin-02 | ponytail | PASS | 12 | 1804 | 162287 | unmeasured | 29.16 | 6 | unmeasured | overlapped | no | no (field added later; patch applied directly) | 21e14a9 | logs/gin-02_ponytail_1.* |
| gin-02 | tightloop | PASS | 12 | 2302 | 181475 | unmeasured | 30.23 | 8 | unmeasured | overlapped | no | no (field added later; patch applied directly) | 21e14a9 | logs/gin-02_tightloop_1.* |

Tokens: input / output / cache (cache = cache_read + cache_creation) exactly as
`claude -p --output-format json` reports them. Wall time = the agent session
only (clone and grading excluded).

## Read this before the numbers

- n=1 per arm per task, and every counted row ran while other jobs used the
  same machine (tag "overlapped"). These are data points only; no claim either
  way. Wall time is comparable only within the same tag (all counted rows are
  "overlapped"). Tokens and pass/fail do not depend on load.
- Pass rate: 3/3 tasks PASS on every arm (no-skill 3/3, ponytail 3/3,
  tightloop 3/3). No arm separates on pass rate.
- fd-01 (single overlapped run): tightloop used more tokens and wall than
  no-skill (22/3585/359.5k, 111 s vs 18/3260/245.6k, 104 s); ponytail lowest
  on both (14/2117/192.4k, 82 s). Data point only.
- The grader scores the fix only, so agent-written tests in files the hidden
  patch touches are dropped and test-writing quality is not measured in these
  rows.
- Two harness rules act on the agent's tree after the session and before the
  hidden test patch, the same on every arm, logged per row (columns above):
  (1) rename: an ADDED test function with a hidden test's exact name gets
  "_agent" (fired on fd-01 no-skill and tightloop, all 3 gin-01 arms);
  (2) hidden-patch fallback (from d302485): only if the hidden patch does not
  apply, the files it touches are restored to the start commit and it is
  applied again (fired on all 3 gin-01 arms; agent test lines dropped shown).
  The raw agent diff of every row is saved in diffs/ before either rule.

## score.py

```
--- excluded, superseded (2 rows; redone, kept for the record) ---
fd-01 no-skill run1: result=pass status=superseded (fd-01 redone with all 3 arms back to back under the overlap tag, root/Naman 7:07 PM IST); kept, not counted
fd-01 ponytail run1: result=pass status=superseded (fd-01 redone with all 3 arms back to back under the overlap tag, root/Naman 7:07 PM IST); kept, not counted
--- excluded, invalid-harness (6 rows; not in pass rate or ratios) ---
fd-01 no-skill run1: result=fail status=invalid-harness (name collision)
fd-01 ponytail run1: result=fail status=invalid-harness (name collision)
fd-01 tightloop run1: result=fail status=invalid-harness (name collision)
gin-01 no-skill run1: result=invalid status=invalid-harness (hidden patch context conflict at recovery_test.go:142; fixed in d302485, gin-01 redone)
gin-01 ponytail run1: result=invalid status=invalid-harness (hidden patch context conflict at recovery_test.go:142; fixed in d302485, gin-01 redone)
gin-01 tightloop run1: result=invalid status=invalid-harness (hidden patch context conflict at recovery_test.go:142; fixed in d302485, gin-01 redone)
rows counted: 9 (from rows.jsonl, 6 invalid-harness and 2 superseded excluded); not pass/fail: 0
--- tuning set (3 tasks) ---
fd-01 no-skill run1: result=pass in=18 out=3260 cache=245597 total=unmeasured wall=104.03s turns=9 tool_calls=unmeasured
fd-01 ponytail run1: result=pass in=14 out=2117 cache=192365 total=unmeasured wall=81.7s turns=7 tool_calls=unmeasured
fd-01 tightloop run1: result=pass in=22 out=3585 cache=359530 total=unmeasured wall=111.24s turns=12 tool_calls=unmeasured
gin-01 no-skill run1: result=pass in=8 out=1869 cache=129112 total=unmeasured wall=21.92s turns=4 tool_calls=unmeasured
gin-01 ponytail run1: result=pass in=10 out=1828 cache=168088 total=unmeasured wall=21.11s turns=5 tool_calls=unmeasured
gin-01 tightloop run1: result=pass in=10 out=2420 cache=188563 total=unmeasured wall=34.34s turns=6 tool_calls=unmeasured
gin-02 no-skill run1: result=pass in=10 out=2179 cache=132171 total=unmeasured wall=25.99s turns=5 tool_calls=unmeasured
gin-02 ponytail run1: result=pass in=12 out=1804 cache=162287 total=unmeasured wall=29.16s turns=6 tool_calls=unmeasured
gin-02 tightloop run1: result=pass in=12 out=2302 cache=181475 total=unmeasured wall=30.23s turns=8 tool_calls=unmeasured
ponytail token ratio (input+output) vs no-skill: raw median 0.8296025582457743 over 3 pairs
tightloop token ratio (input+output) vs no-skill: raw median 1.100366076876144 over 3 pairs
ponytail token ratio (input+output+cache) vs no-skill: raw median 1.2213679666567432 over 3 pairs
tightloop token ratio (input+output+cache) vs no-skill: raw median 1.4580842666178075 over 3 pairs
no-skill results: pass=3; pass 3/3 graded
ponytail results: pass=3; pass 3/3 graded
tightloop results: pass=3; pass 3/3 graded
```

## Excluded rows (kept in rows.jsonl, not counted)

| task | arm | run | result | status | log |
| --- | --- | --- | --- | --- | --- |
| fd-01 | no-skill | 1 | fail | invalid-harness (name collision) | logs/fd-01_no-skill_1.* |
| fd-01 | ponytail | 1 | fail | invalid-harness (name collision) | logs/fd-01_ponytail_1.* |
| fd-01 | tightloop | 1 | fail | invalid-harness (name collision) | logs/fd-01_tightloop_1.* |
| fd-01 | no-skill | 1 | pass | superseded (fd-01 redone with all 3 arms back to back under the overlap tag, root/Naman 7:07 PM IST); kept, not counted | logs/fd-01_no-skill_1_attempt2.* |
| fd-01 | ponytail | 1 | pass | superseded (fd-01 redone with all 3 arms back to back under the overlap tag, root/Naman 7:07 PM IST); kept, not counted | logs/fd-01_ponytail_1_attempt2.* |
| gin-01 | no-skill | 1 | invalid | invalid-harness (hidden patch context conflict at recovery_test.go:142; fixed in d302485, gin-01 redone) | logs/gin-01_no-skill_1.* |
| gin-01 | ponytail | 1 | invalid | invalid-harness (hidden patch context conflict at recovery_test.go:142; fixed in d302485, gin-01 redone) | logs/gin-01_ponytail_1.* |
| gin-01 | tightloop | 1 | invalid | invalid-harness (hidden patch context conflict at recovery_test.go:142; fixed in d302485, gin-01 redone) | logs/gin-01_tightloop_1.* |

## Dropped tasks (no counted rows, not in arm counts)

- fd-02: the upstream fix ed47664 itself fails the hidden test here: the test
  runs `fd --full-path one/two/c` and expects only one/two/c.foo, but fd's
  smart case also returns one/two/C.Foo2 (grader_sanity/fd-02_status.txt,
  fd-02_upstream_commit_itself.log). No fd-02 session was run.
- fd-03 (the frozen holdout): hidden test cannot tell the half fix from the
  real fix when threads > 1 (src/exec/job.rs buffer_output = threads > 1);
  grader check: real fix PASS 43 s, empty FAIL 44 s, half fix PASS 37 s;
  fallback did not fire (grader_sanity/fd-03_*). No fd-03 session was run, so
  there is no holdout table in this pass. A --threads 1 grader variant is an
  idea for a later pass only.

## Grader checks (no agent)

- fd-01: real fix PASS, empty FAIL, half fix FAIL
- gin-01: real fix PASS, empty FAIL, half fix FAIL
- gin-02: real fix PASS, empty FAIL, half fix FAIL
- fd-02: real fix FAIL (dropped), empty FAIL, half fix FAIL
- fd-03: real fix PASS, empty FAIL, half fix PASS (dropped)
Files: grader_sanity/ (sanity json, grader_checks_*.json, patches, logs).

## Unmeasured

- tool_calls: not in `claude -p` JSON output; not counted from an event
  stream, never estimated.
- tokens.total: the JSON has no total_tokens field.
- model (top level): the JSON has no top-level model; model_from_modelUsage per
  row = claude-opus-5-5 on every row.

## Environment

Claude Code CLI 2.1.302 on every row, model claude-opus-5-5 (modelUsage) on
every row, fresh clone + checkout of the start commit per session. Linux
6.1.158+ x86_64 (4 CPUs, shared with other jobs), Python 3.11.6, go1.27.2,
rustc/cargo 1.99.0, node v22.23.2, git 2.39.5. Built-in web tools denied
(--disallowedTools WebFetch WebSearch); not network-isolated. Skills via
--append-system-prompt (ponytail SKILL.md @ 09c434ab, sha256 9badd22a32e1;
tightloop SKILL.md from the harness commit). Full record: environment.json and
each row's environment field. Start commits: fd-01 a8a77d2, gin-01 c358d56,
gin-02 df27537. Harness of counted rows: fd-01 and gin-02 21e14a9, gin-01
2c7a6fd.
