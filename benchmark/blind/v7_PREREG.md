# tightloop v7 pre-registration (written 2026-10-18T22:27:43Z, before any v7 build)

Direction: Naman m:249181d3 (3:54 AM IST, pt 4): v7 pre-registered by 5:15 AM IST (23:45Z); one change per version; any version run with
fewer runs than v5c gets its n printed next to every number. Written BEFORE v5c or v6c is judged and before any v7 build.
Branch v7/v7-prep, based on origin/v6/v6c-prep (0a961b3, the v6c prereg + amendment). Structure copied from v6c_PREREG.md.

## 0. Base version and comparison

- BASE = tightloop-v4c (the 3-call skill, 433 tokens), the last KEPT version at prereg time. v5c and v6c are NOT judged yet.
- v7 is compared against r2 v4c (tokens and blind quality). IF v5c or v6c is later KEPT (beats v4c on BOTH tokens and blind quality
  under its own prereg), v7 is ALSO compared against that kept version, with the same rules below, and that comparison is labelled
  "v7 vs kept v5c" / "v7 vs kept v6c". The primary keep decision stays "v7 vs v4c" as written here.
- Facts on file at writing (harness logs, cost-weighted, % of r2 no-skill): v5c kanban 71.2/52.3/62.3, bookmarks 57.3/57.2/65.7,
  expenses 74.1/89.7/60.5 (all 9 v5c builds in; v5c not yet judged). r2 v4c: kanban 47.1, bookmarks 44.2, expenses 69.2 (n=1 each).
  The v5c token split (TOKEN_WHY first split) shows rewrite tokens 0: the extra tokens sit in the extra verification calls plus thinking.
  The browser-crash count is a count, not a cause: the browser is absent in the build sandbox; r2 no-skill also crashed once per app,
  r2 v4c 0. v6c (step 4 as a read-only rg review, 534 tokens) is building now; its numbers are not known at writing.

## 1. Definition (ONE change vs v4c)

v7 = tightloop-v4c with ONLY step 2 extended: the finish checklist is folded into the write step as write-time requirements
(empty-state text, focus styles, input labels, one spacing/type scale, every button wired to a handler). There is NO separate review
step, NO test step and no extra tool call; steps 1 and 3, the frontmatter, gate.sh and phases/ are byte-identical to v4c.

Hypothesis: the quality items arrive at first-pass write cost with zero extra calls, so tokens stay near v4c while the polish/a11y
items v4c lost 1-3 judge points on (r2) are present.

Exact diff (benchmark/arms/tightloop-v4c -> benchmark/arms/tightloop-v7; only SKILL.md differs):

```
--- a/benchmark/arms/tightloop-v4c/SKILL.md
+++ b/benchmark/arms/tightloop-v7/SKILL.md
@@ -7,7 +7,7 @@
 Every tool call re-sends ~30k tokens, so finish in 3 calls. This skill is already loaded; never call the Skill tool.
 
 1. One Bash: `rg -n` the key symbols, then `sed -n` only the 20-40 lines you need and the nearest test. No whole-file reads, no cat. Concurrency, security, data loss or public API: also `cat .claude/skills/tightloop/phases/risky.md` here.
-2. One Bash: apply all edits (root-cause fix + one test that fails without it) by heredoc/python, then in the same command `bash .claude/skills/tightloop/gate.sh "<narrowest test>" <changed source files> 2>&1 | tail -40`. Check empty, boundary and error inputs before writing. Only on GATE FAIL: read .claude/skills/tightloop/phases/fail.md, fix, rerun once.
+2. One Bash: apply all edits (root-cause fix + one test that fails without it) by heredoc/python, then in the same command `bash .claude/skills/tightloop/gate.sh "<narrowest test>" <changed source files> 2>&1 | tail -40`. Check empty, boundary and error inputs before writing. Apps/UI: write these in this same pass, no review or test step, no extra call: empty states with real text (never null/undefined), visible focus styles, a label on every input, one spacing/type scale, every button wired to a handler that changes state. Only on GATE FAIL: read .claude/skills/tightloop/phases/fail.md, fix, rerun once.
 3. Reply in 3 lines: change, GATE line, not checked. No more tool calls.
 
 No plan or notes files, subagents, refactors, or comments that restate code.
```

SKILL.md sha256: v4c 6c2683f102ddbb000b779a9aefe2367b8342f1253b66c8fe6056b3561b2cf7e7; v7 592ffa42f903d0775a719d72f5c3d15c08b6ae00110db655df5777f63f82f349. Bytes: v4c 978, v7 1231 (v5c 1248).

Skill size (same method as v4c/v5c/v6c: token-counting endpoint, no session, raw delta + 9; script
`benchmark/blind/v7_run/measure_skill_tokens_v7.py`, output `benchmark/blind/v7_run/skill_tokens_v7.json`):
v4c 433 | v5c 535 | v6c 534 | v7 508 (raw 499; ponytail 1283 raw and v4 752 raw reproduce, so the method matches).
v7 costs +75 tokens per skill load vs v4c, and is <= v5c's size (535) as required.

## 2. Runs

- 9 builds: tightloop-v7 x 3 runs x the same 3 r2 specs (benchmark/blind/specs/r2/{bookmarks,expenses,kanban}.md).
- Order: results/v7_order.json, seed 1801867438129130158 (random.Random(seed).shuffle, make_order_v7.py), created 2026-10-18T22:26:54Z:
  expenses-3, kanban-1, kanban-3, bookmarks-1, expenses-1, bookmarks-3, bookmarks-2, expenses-2, kanban-2.
- Same checker (benchmark/blind/checks/check_app.py), same harness (runner.launch), same CLI flags, same sandbox (sandbox_r2), same
  snapshot method (git archive of this commit -> /home/user/tab/work/tl_blind_v7, .snap_commit), nice -n 15, 1800 s timeout,
  transcript audit + VOID rule, one RETRY on a harness crash only. No harness or grader edits; .claude/skills stays v4;
  holdout-split.json untouched.
- Driver: benchmark/blind/v7_run/blind_driver_v7.py, a copy of the v6c driver with only paths, arm, order file, hold text "v7",
  START_OK at /home/user/tab/files/tl_blind/v7/START_OK and the clocks changed.
- Clocks: START_OK is written by root only after v6c's builds end. If START_OK has not appeared by 2026-10-19T02:30:00Z, v7 is NOT
  run and that is reported. No build starts at or after 2026-10-19T03:15:00Z; the build in progress finishes and the run is reported
  "cut to n of 9".

## 3. Denominators (the SAME as v5c and v6c; r2 no-skill builds, cost-weighted, harness logs)

kanban 198,718.9 | bookmarks 249,587.55 | expenses 216,408.95.
cost_weighted = input + 5*output + 0.1*cache_read + 1.25*cache_write (the driver's formula, unchanged).

## 4. PREDICTION (written now)

- P1 tokens: v7 median cost-weighted <= 60% of r2 no-skill per app AND <= r2 v4c + 5 percentage points per app.
  Effective bounds: kanban <= 52.09% (103,515), bookmarks <= 49.16% (122,686), expenses <= 60.0% (129,845; v4c+5 = 74.23% is looser).
  Flag written now: r2 v4c expenses itself was 69.2%, so expenses is the likely miss.
- P2 checker: v7 checker passes >= r2 v4c per app on every run: kanban 10/10, bookmarks 20/20, expenses 25/25 (r2 v4c was full on all 3).
- P3 quality: v7 blind-judge median >= r2 v4c's score per app (r2 v4c: bookmarks 97, expenses 99, kanban 97, judged in r2).
Each is reported HIT or MISS per app with the number.

## 5. KEEP RULE

- v7 is kept over v4c only if it beats v4c on BOTH tokens (cost-weighted, % of no-skill) AND blind-judge quality.
- Report per app: median and min-max of the 3 v7 runs, next to r2 v4c (n=1). If v4c's value lies inside v7's min-max (overlap), that
  app is "not distinguishable", not a win. A defect that shows in 1 of 3 runs goes in the range (stated per app), not hidden by the median.
- A fail stays a fail: no rescue reruns, no prompt tweaks, no re-scoring after numbers are in.

## 6. Blind plan

- New sealed key KEY_v7.json, made by benchmark/blind/v7_run/make_key_v7.py and stored ONLY under /home/user/tab/files/tl_blind/v7/
  (mode 0600, not committed). sha256 04e71298d2a99cac5ccba2e846b6da21d0b865af1c31b268fa3cb3f1200307cb. Never read after creation (sha256 only).
- Labels freshly shuffled per app (fresh seed inside the key). Judged set per app = 3 v7 builds + the r2 no-skill build + the r2 v4c
  build (5 labels A-E). Rubric: the r2 rubric b8d4711, unchanged. The judge sees no arm names and no checker counts.
- Viewer zip /home/user/tab/files/tl_blind/v7/viewer.zip built the same way as v5c/v6c (arm names, prompts, logs stripped; leak grep 0).

## 7. IF v7 LOSES

The numbers are reported as they are, P1-P3 HIT/MISS per app, and v7 is logged "v7 FAILED" (or "not distinguishable" where ranges
overlap). The previous kept version stays. No rescue, rerun, tweak or re-score.

## 8. IF RUNS ARE CUT

If the 03:15Z cutoff (or anything else) stops the run before 9 builds, n is printed next to every number (per app, e.g. "kanban n=2"),
the missing builds are named, and no claim is made beyond what the n supports.
