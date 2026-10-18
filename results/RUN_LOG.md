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

## Pass 2 harness addendum (2026-10-18 ~14:55Z, before any tightloop-v4 session)

- Gate backup check, same on every arm: after each session and before diffing, the runner looks for .git/tightloop-gate/ (left only if v4's gate.sh was killed mid-revert). If present it restores those files, marks the row invalid-harness ("gate killed mid-revert") and does not grade it.
- Per row, from the stream-json events: phase_reads (tool calls whose input names phases/fail.md or phases/risky.md, Read or Bash), gate_runs (Bash tool calls running tightloop/gate.sh) and gate_output_bytes (bytes of those calls' tool results).
- gate.sh runs are counted in tool_calls: each Bash tool_use that runs gate.sh is one distinct tool_use id, so it is one tool call; its output is a tool result, which enters the session's context, so it is inside the session's tokens.
- Environment fact: rustfmt is not installed on this box's Rust toolchain, so on fd tasks v4's gate prints "format unchecked" for .rs files (it never claims a pass). Not installed mid-pass, to keep the environment the same for all arms; a candidate for a later pass.
- Unit checks: results/harness_checks/pass2_gate_unit.txt (gate cases, the kill -9 case, the runner's restore + invalid-harness flag).
- Pass-2 fd-01 no-skill, ponytail and tightloop-v3 rows were run under f93099f before this addendum. The addendum changes only the post-session backup check (no effect when no backup exists) and adds counts, so those rows are unaffected; their phase/gate counts are 0 by construction (they cannot run v4's gate).

## Pass 2: fd-01 restart (2026-10-18 ~14:58Z; Pally/Naman option b, 8:26 PM IST)

- rustfmt was not installed when pass-2 fd-01 no-skill, ponytail and tightloop-v3 ran; each of them tried `cargo fmt` and got "cargo-fmt is not installed". Then the disk pause (Kimo G8) stopped the runner before tightloop-v4, breaking fd-01's 4-arms-back-to-back order.
- Those 3 rows are kept in rows.jsonl, marked status "superseded ..." with superseded_reason and superseded_by; score.py does not count them.
- rustfmt: `rustup component add rustfmt` reported "component rustfmt is up to date"; `rustfmt --version` and `cargo fmt --version` = rustfmt 1.10.0-stable (b940084d7e 2026-09-28). df before and after: 1916 MiB free.
- fd-01 is rerun with all 4 arms back to back, then gin-01, then gin-02, one session at a time; each session's checkout (with its build folder) is deleted right after grading. Runner relaunched with --pause-file so it can be held between sessions without stopping it.

## Pass 2: Go build cache clear between fd-01 and gin-01 (2026-10-18)
- After fd-01 x4 finished (15:16Z), df was 1905M free (< 2400 MiB), so the Go build cache (~/.cache/go-build, 813 MB) was cleared with `go clean -cache` at 15:16:36Z UTC. df before 1905M, after 2723M. Nothing else was deleted.
- Then one throwaway gin build (not a row, not graded): fresh clone of gin at gin-01's start commit c358d56 in a temp dir, `go test -count=1 -run NONE_THROWAWAY ./...` (compiles every package and test binary, runs no test), 15:17:11-15:17:56Z, RC=0; temp dir removed. Go cache after it: 260 MB; df 2461M.
- Purpose: no gin arm pays the cold-build cost alone. All 8 gin pass-2 rows run on this same warmed cache. gin timing is therefore not directly comparable to first-pass gin rows (different cache state).
- fd-01 pass-2 rows (attempt5/v3/v4 tags) ran under runner pid launched 15:07:25Z with `--tasks fd-01`; gin-01 and gin-02 run in a second runner invocation with identical flags (`--tasks gin-01 gin-02`).

## Pass 2 results (fd-01, gin-01, gin-02; 4 arms; harness e786442)
n=1 per arm, every row overlapped with other work on the box. These are data points, not claims. CLI 2.1.302, modelUsage claude-opus-5-5 on every row. Each task's 4 arms ran back to back in the order no-skill, ponytail, tightloop-v3, tightloop-v4; each /tmp/tlw-* checkout was deleted right after grading. rustfmt 1.10.0 present for every fd-01 row (v4's gate printed its format check as passed). No INVALID row, no grader oddity. Defect score: unmeasured (reviewer not approved).

Rows (tokens in/out/cache_read/cache_creation; wall; turns; tool calls exact from stream-json):
- fd-01 no-skill: PASS in 14/out 3220/cache_read 199211/cache_creation 37989 (in+out 3234; in+out+cache_read 202445), 109.84 s, turns 7, tools 6, rename yes, fallback no, overlapped, diff +25/-5, gate_runs 0, gate_out 0 B, fail.md 0 / risky.md 0 reads
- fd-01 ponytail: PASS in 12/out 1970/cache_read 165936/cache_creation 37953 (in+out 1982; in+out+cache_read 167918), 87.21 s, turns 6, tools 5, rename yes, fallback no, overlapped, diff +43/-29, gate_runs 0, gate_out 0 B, fail.md 0 / risky.md 0 reads
- fd-01 tightloop-v3: PASS in 24/out 4222/cache_read 461396/cache_creation 21356 (in+out 4246; in+out+cache_read 465642), 121.44 s, turns 13, tools 12, rename yes, fallback no, overlapped, diff +43/-29, gate_runs 0, gate_out 0 B, fail.md 0 / risky.md 0 reads
- fd-01 tightloop-v4: PASS in 10/out 1960/cache_read 152861/cache_creation 12095 (in+out 1970; in+out+cache_read 154831), 83.0 s, turns 5, tools 4, rename yes, fallback no, overlapped, diff +21/-4, gate_runs 2, gate_out 3302 B, fail.md 0 / risky.md 0 reads
- gin-01 no-skill: PASS in 8/out 2093/cache_read 94841/cache_creation 34323 (in+out 2101; in+out+cache_read 96942), 28.49 s, turns 4, tools 3, rename yes, fallback yes, overlapped, diff +26/-3, gate_runs 0, gate_out 0 B, fail.md 0 / risky.md 0 reads | fallback dropped: recovery_test.go +20/-0
- gin-01 ponytail: PASS in 8/out 1526/cache_read 121821/cache_creation 11529 (in+out 1534; in+out+cache_read 123355), 24.2 s, turns 4, tools 3, rename yes, fallback yes, overlapped, diff +22/-1, gate_runs 0, gate_out 0 B, fail.md 0 / risky.md 0 reads | fallback dropped: recovery_test.go +18/-0
- gin-01 tightloop-v3: PASS in 14/out 2935/cache_read 250057/cache_creation 17017 (in+out 2949; in+out+cache_read 253006), 48.75 s, turns 8, tools 7, rename yes, fallback yes, overlapped, diff +27/-0, gate_runs 0, gate_out 0 B, fail.md 0 / risky.md 0 reads | fallback dropped: recovery_test.go +22/-0
- gin-01 tightloop-v4: PASS in 8/out 1508/cache_read 120480/cache_creation 11487 (in+out 1516; in+out+cache_read 121996), 20.39 s, turns 4, tools 3, rename yes, fallback yes, overlapped, diff +22/-0, gate_runs 1, gate_out 1039 B, fail.md 0 / risky.md 0 reads | fallback dropped: recovery_test.go +19/-0
- gin-02 no-skill: PASS in 10/out 2506/cache_read 154744/cache_creation 12157 (in+out 2516; in+out+cache_read 157260), 55.62 s, turns 5, tools 4, rename no, fallback no, overlapped, diff +29/-2, gate_runs 0, gate_out 0 B, fail.md 0 / risky.md 0 reads
- gin-02 ponytail: PASS in 10/out 1819/cache_read 154038/cache_creation 10994 (in+out 1829; in+out+cache_read 155867), 28.85 s, turns 5, tools 4, rename no, fallback no, overlapped, diff +16/-2, gate_runs 0, gate_out 0 B, fail.md 0 / risky.md 0 reads
- gin-02 tightloop-v3: PASS in 14/out 2757/cache_read 246882/cache_creation 15994 (in+out 2771; in+out+cache_read 249653), 36.56 s, turns 8, tools 7, rename no, fallback no, overlapped, diff +16/-2, gate_runs 0, gate_out 0 B, fail.md 0 / risky.md 0 reads
- gin-02 tightloop-v4: PASS in 8/out 1957/cache_read 118546/cache_creation 11637 (in+out 1965; in+out+cache_read 120511), 26.83 s, turns 4, tools 3, rename no, fallback no, overlapped, diff +15/-1, gate_runs 1, gate_out 1469 B, fail.md 0 / risky.md 0 reads

Per-task token ratios vs no-skill (raw):
- fd-01 ponytail: in+out 1982/3234 = 0.6129; in+out+cache_read 167918/202445 = 0.8294
- fd-01 tightloop-v3: in+out 4246/3234 = 1.3129; in+out+cache_read 465642/202445 = 2.3001
- fd-01 tightloop-v4: in+out 1970/3234 = 0.6092; in+out+cache_read 154831/202445 = 0.7648
- gin-01 ponytail: in+out 1534/2101 = 0.7301; in+out+cache_read 123355/96942 = 1.2725
- gin-01 tightloop-v3: in+out 2949/2101 = 1.4036; in+out+cache_read 253006/96942 = 2.6099
- gin-01 tightloop-v4: in+out 1516/2101 = 0.7216; in+out+cache_read 121996/96942 = 1.2584
- gin-02 ponytail: in+out 1829/2516 = 0.7269; in+out+cache_read 155867/157260 = 0.9911
- gin-02 tightloop-v3: in+out 2771/2516 = 1.1014; in+out+cache_read 249653/157260 = 1.5875
- gin-02 tightloop-v4: in+out 1965/2516 = 0.7810; in+out+cache_read 120511/157260 = 0.7663

score.py medians over 3 pairs (raw; see score_output.txt):
- input+output: ponytail 0.7269475357710652, tightloop-v3 1.3129251700680271, tightloop-v4 0.7215611613517373
- input+output+cache_read (MEASURE.md): ponytail 0.9911420577387765, tightloop-v3 2.300091382844723, tightloop-v4 0.7663169273814066
- input+output+cache (read + creation): ponytail 0.9849129662312519, tightloop-v3 2.0254955621917032, tightloop-v4 0.7800161731113171
- 40% target (ratio at or below 0.4): not met by any arm, with or without cache reads.
- Pass rate: 3/3 on every arm; no arm separates on the hidden tests.

v4 against ponytail, per task: input+output fd-01 1970 vs 1982, gin-01 1516 vs 1534, gin-02 1965 vs 1829 (v4 higher on gin-02: a loss); input+output+cache_read fd-01 154831 vs 167918, gin-01 121996 vs 123355, gin-02 120511 vs 155867.

Lazy phase files (v4): phases/fail.md read 0 times and phases/risky.md read 0 times on all 3 tasks (also 0 on every other arm). v4 gate.sh runs: fd-01 2 (3302 bytes output), gin-01 1 (1039 B), gin-02 1 (1469 B); gate runs are inside v4's tool calls and tokens. Whether the split saved anything is not measured: the 1871 bytes of phase text were never loaded, but no arm with them folded into the core was run, so there is no comparison row.

Caveats: no-skill ran first in each task and paid the most cache_creation on fd-01 (37989) and gin-01 (34323), an order effect that is logged, not corrected. gin-01 used the hidden-patch fallback on all 4 arms (recovery_test.go agent lines dropped: no-skill +20, ponytail +18, v3 +22, v4 +19). Agent test renamed before grading on every fd-01 and gin-01 row (hidden-test name collision); none on gin-02.

## Pass 2 addendum (Naman via Pally, after the pass-2 commit ac0ee1f): reporting and analysis only
No runner, harness or grader change. The rows are the same 12.

1. Cost-weighted tokens (analysis only, results/analysis/cost_weighted.py; output in cost_weighted_output.txt).
   Weights relative to input = 1: input 1, output 5, cache_read 0.1, cache_creation 1.25.
   cost_weighted = input*1 + output*5 + cache_read*0.1 + cache_creation*1.25
   - fd-01: v4/no-skill 0.4814918580698228, v4/ponytail 0.5442024930697316
   - gin-01: v4/no-skill 0.5401573475382532, v4/ponytail 0.9919196876547376
   - gin-02: v4/no-skill 0.8376141067074899, v4/ponytail 0.9462122855955222
   - medians: v4/no-skill 0.5401573475382532; v4/ponytail 0.9462122855955222; ponytail/no-skill 0.8847659909711708; v3/no-skill 1.1250847837109912
   - Caveat: cache_creation carries weight 1.25 and no-skill ran first on each task, so it paid the most cache_creation on fd-01 (37989) and gin-01 (34323). That order effect pushes every arm's cost-weighted ratio down; it is logged, not corrected.
   40% target (median ratio at or below 0.4) for v4: missed on all three numbers: in+out 0.7215611613517373, in+out+cache_read 0.7663169273814066, cost-weighted 0.5401573475382532.

2. Phase files (kept, not cut): fail.md and risky.md were read 0 times on gin-02 as on fd-01 and gin-01, by every arm. No pass-2 row failed. The harness does not classify "risky code", and no row read risky.md. Would-be saving if they were dropped or never shipped: fail.md 970 bytes, risky.md 901 bytes (1871 bytes). They are not in the system prompt, so today they cost nothing unless read.

3. v4 gate.sh runs, from the session transcripts:
   - fd-01 (2 runs, 3302 B total): run 1 came in the same Bash call as the fix (python edit of src/main.rs + test, then gate) -> GATE PASS. Run 2 came after a second edit that only moved a 3-line comment ("Start with the cheap check: ...") to the function it describes; no code or test line changed. So run 2 was a recheck after an edit, but the edit was comment-only: a full gate rerun (revert, FAIL, PASS) for a cosmetic change. The agent piped the gate through grep GATE, so its visible output was one line.
   - gin-01 (1 run, 1039 B): the fix and test edit and the gate in one Bash call -> GATE PASS; no second run.
   - gin-02 (1 run, 1469 B): same shape as gin-01.

4. Time: cov_c (Kimo, headless chrome) ran beside every pass-2 session and could not be paused, so wall time on all 12 pass-2 rows is "overlapped, not comparable". Tokens, turns and tool calls stand.

Final pass-2 table:
- fd-01 no-skill: PASS | in+out+cache_read 202445 | in+out 3234 | cost-weighted 83521.35 | in 14 out 3220 cache_read 199211 cache_creation 37989 | time 109.84 s (overlapped, not comparable) | turns 7 | tool calls 6 | rename yes | fallback no | diff +25/-5 | gate_runs 0 (0 B) | fail.md 0 risky.md 0
- fd-01 ponytail: PASS | in+out+cache_read 167918 | in+out 1982 | cost-weighted 73896.85 | in 12 out 1970 cache_read 165936 cache_creation 37953 | time 87.21 s (overlapped, not comparable) | turns 6 | tool calls 5 | rename yes | fallback no | diff +43/-29 | gate_runs 0 (0 B) | fail.md 0 risky.md 0
- fd-01 tightloop-v3: PASS | in+out+cache_read 465642 | in+out 4246 | cost-weighted 93968.60 | in 24 out 4222 cache_read 461396 cache_creation 21356 | time 121.44 s (overlapped, not comparable) | turns 13 | tool calls 12 | rename yes | fallback no | diff +43/-29 | gate_runs 0 (0 B) | fail.md 0 risky.md 0
- fd-01 tightloop-v4: PASS | in+out+cache_read 154831 | in+out 1970 | cost-weighted 40214.85 | in 10 out 1960 cache_read 152861 cache_creation 12095 | time 83.0 s (overlapped, not comparable) | turns 5 | tool calls 4 | rename yes | fallback no | diff +21/-4 | gate_runs 2 (3302 B) | fail.md 0 risky.md 0
- gin-01 no-skill: PASS | in+out+cache_read 96942 | in+out 2101 | cost-weighted 62860.85 | in 8 out 2093 cache_read 94841 cache_creation 34323 | time 28.49 s (overlapped, not comparable) | turns 4 | tool calls 3 | rename yes | fallback yes (dropped recovery_test.go +20/-0) | diff +26/-3 | gate_runs 0 (0 B) | fail.md 0 risky.md 0
- gin-01 ponytail: PASS | in+out+cache_read 123355 | in+out 1534 | cost-weighted 34231.35 | in 8 out 1526 cache_read 121821 cache_creation 11529 | time 24.2 s (overlapped, not comparable) | turns 4 | tool calls 3 | rename yes | fallback yes (dropped recovery_test.go +18/-0) | diff +22/-1 | gate_runs 0 (0 B) | fail.md 0 risky.md 0
- gin-01 tightloop-v3: PASS | in+out+cache_read 253006 | in+out 2949 | cost-weighted 60965.95 | in 14 out 2935 cache_read 250057 cache_creation 17017 | time 48.75 s (overlapped, not comparable) | turns 8 | tool calls 7 | rename yes | fallback yes (dropped recovery_test.go +22/-0) | diff +27/-0 | gate_runs 0 (0 B) | fail.md 0 risky.md 0
- gin-01 tightloop-v4: PASS | in+out+cache_read 121996 | in+out 1516 | cost-weighted 33954.75 | in 8 out 1508 cache_read 120480 cache_creation 11487 | time 20.39 s (overlapped, not comparable) | turns 4 | tool calls 3 | rename yes | fallback yes (dropped recovery_test.go +19/-0) | diff +22/-0 | gate_runs 1 (1039 B) | fail.md 0 risky.md 0
- gin-02 no-skill: PASS | in+out+cache_read 157260 | in+out 2516 | cost-weighted 43210.65 | in 10 out 2506 cache_read 154744 cache_creation 12157 | time 55.62 s (overlapped, not comparable) | turns 5 | tool calls 4 | rename no | fallback no | diff +29/-2 | gate_runs 0 (0 B) | fail.md 0 risky.md 0
- gin-02 ponytail: PASS | in+out+cache_read 155867 | in+out 1829 | cost-weighted 38251.30 | in 10 out 1819 cache_read 154038 cache_creation 10994 | time 28.85 s (overlapped, not comparable) | turns 5 | tool calls 4 | rename no | fallback no | diff +16/-2 | gate_runs 0 (0 B) | fail.md 0 risky.md 0
- gin-02 tightloop-v3: PASS | in+out+cache_read 249653 | in+out 2771 | cost-weighted 58479.70 | in 14 out 2757 cache_read 246882 cache_creation 15994 | time 36.56 s (overlapped, not comparable) | turns 8 | tool calls 7 | rename no | fallback no | diff +16/-2 | gate_runs 0 (0 B) | fail.md 0 risky.md 0
- gin-02 tightloop-v4: PASS | in+out+cache_read 120511 | in+out 1965 | cost-weighted 36193.85 | in 8 out 1957 cache_read 118546 cache_creation 11637 | time 26.83 s (overlapped, not comparable) | turns 4 | tool calls 3 | rename no | fallback no | diff +15/-1 | gate_runs 1 (1469 B) | fail.md 0 risky.md 0
