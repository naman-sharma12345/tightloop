# tightloop v9 pre-registration (written 2026-10-19T00:21:04Z, before any v9 build)

Direction: Naman m:a6d66c3d (5:46 AM IST Oct 19): "'no test files' becomes its own pre-registered version right after v8 (v9), so we still
get one clean change per version." Written BEFORE any v9 build, while the v8 builds are running and before v8 is judged or revealed.
Branch v6/v8-prep (on e94f991 = the v8 prereg). Structure copied from v8_PREREG.md. Docs-only: no harness, flag, checker or grader edit.

## 0. Base version (BASE RULE, fixed now)

- v9 base = tightloop-v8 IF v8 is KEPT under the v8_PREREG.md keep rule (v8 beats v4c(n=3) on BOTH tokens and blind quality);
  ELSE v9 base = tightloop-v4c (the last kept version).
- Two candidate arms are committed now (section 2). After the v8 reveal, root picks the arm by this rule and nothing else:
  base v8 -> benchmark/arms/tightloop-v9-on-v8; base v4c -> benchmark/arms/tightloop-v9-on-v4c. Nothing else may change: same
  order, same key file (the matching variant), same driver, same clocks. The arm not picked is never built.
- Base numbers: base v4c = the v4c n=3 runs per app (r2 + the 2 v4c-n3 builds); base v8 = the 3 v8 builds per app (v8_PREREG.md).
  v4c n=3 medians (% of r2 no-skill, cost-weighted, all runs): kanban 47.1 [45.3-56.6], bookmarks 55.3 [44.2-69.5],
  expenses 84.9 [69.2-104.3].

## 1. Evidence

v7 shipped unused test files in its output folders: the v7 blind judge (RANKS_v7.md, f86c480) noted an unused test.js on 6 of the
9 v7 builds (by the v7 reveal: kanban run 1, bookmarks runs 1 and 2, expenses runs 1, 2 and 3), each Q3 -1; the r2 rubric (b8d4711)
deducts 1 point for an unused test file. Two v6c expenses labels also shipped an unused test.js (RANKS_v6c.md). Base step 2 asks for "one test that fails without it",
which in a single-folder app build tends to land as test.js / tests/ in the shipped folder.

## 2. Definition (ONE change vs the base): the same one line, at the same place, in both candidate arms

Line (appended as a new last line of SKILL.md, right after "No plan or notes files, subagents, refactors, or comments that restate code."):
"Ship no test files, test scripts or tests/ folders in the output folder: run any self-check from a temp path outside it, or delete it
before you finish."
Everything else (frontmatter, steps 1-3, gate.sh, phases/) is byte-identical to the base arm.

Hypothesis: 0 shipped test files in 9/9 builds; tokens and blind quality not worse than the base.

Exact diff, base v4c (benchmark/arms/tightloop-v4c -> benchmark/arms/tightloop-v9-on-v4c; only SKILL.md differs):

```
diff --git a/benchmark/arms/tightloop-v4c/SKILL.md b/benchmark/arms/tightloop-v9-on-v4c/SKILL.md
index ea0372a..3605a04 100644
--- a/benchmark/arms/tightloop-v4c/SKILL.md
+++ b/benchmark/arms/tightloop-v9-on-v4c/SKILL.md
@@ -11,3 +11,4 @@ Every tool call re-sends ~30k tokens, so finish in 3 calls. This skill is alread
 3. Reply in 3 lines: change, GATE line, not checked. No more tool calls.
 
 No plan or notes files, subagents, refactors, or comments that restate code.
+Ship no test files, test scripts or tests/ folders in the output folder: run any self-check from a temp path outside it, or delete it before you finish.
```

Exact diff, base v8 (benchmark/arms/tightloop-v8 -> benchmark/arms/tightloop-v9-on-v8; only SKILL.md differs):

```
diff --git a/benchmark/arms/tightloop-v8/SKILL.md b/benchmark/arms/tightloop-v9-on-v8/SKILL.md
index 803b4e5..d7a34ad 100644
--- a/benchmark/arms/tightloop-v8/SKILL.md
+++ b/benchmark/arms/tightloop-v9-on-v8/SKILL.md
@@ -11,3 +11,4 @@ Every tool call re-sends ~30k tokens, so finish in 3 calls. This skill is alread
 3. Reply in 3 lines: change, GATE line, not checked. No more tool calls.
 
 No plan or notes files, subagents, refactors, or comments that restate code.
+Ship no test files, test scripts or tests/ folders in the output folder: run any self-check from a temp path outside it, or delete it before you finish.
```

SKILL.md sha256: v9-on-v4c 71a34696aa70f570c6dc63010a1d5786e8baf05d168bca3c13d7c77887a051b3; v9-on-v8 1434c3e9ba06daf3d413dfa30fccfc465c7ddbe64b697e8430b96d80b010943c
(bases: v4c 6c2683f102ddbb000b779a9aefe2367b8342f1253b66c8fe6056b3561b2cf7e7, v8 10f98337ec7382d8fd45d3b47705c6ff69975b1d1d75c7a1ce9bc1645f31a256).
Bytes: v9-on-v4c 1131 (v4c 978), v9-on-v8 1292 (v8 1139).

Skill size (same method as v4c..v8: token-counting endpoint, no session, raw delta + 9; benchmark/blind/v9_run/measure_skill_tokens_v9.py,
output skill_tokens_v9.json; the ponytail cache is not on this box, so ponytail is skipped and v4/v4c/v5c/v6c/v7/v8 are the method check:
raw 752/424/526/525/499/474, all equal to skill_tokens_v8.json):
v9-on-v4c 481 (raw 472; +48 vs v4c 433) | v9-on-v8 531 (raw 522; +48 vs v8 483).

## 3. Runs

- 9 builds: the picked v9 arm x 3 runs x the same 3 r2 specs (benchmark/blind/specs/r2/{bookmarks,expenses,kanban}.md).
- Order: results/v9_order.json, seed 4124579294906762684 (random.Random(seed).shuffle, make_order_v9.py), created 2026-10-19T00:19:53Z:
  v9-bookmarks-3, v9-bookmarks-1, v9-bookmarks-2, v9-expenses-2, v9-kanban-3, v9-expenses-1, v9-expenses-3, v9-kanban-2, v9-kanban-1.
  The same order is used whichever arm is picked.
- Same checker (benchmark/blind/checks/check_app.py), same harness (runner.launch), same CLI flags, same sandbox (sandbox_r2), same
  snapshot method (git archive of this commit -> /home/user/tab/work/tl_blind_v9, .snap_commit), nice -n 15, 1800 s timeout,
  transcript audit + VOID rule, one RETRY on a harness crash only. No harness or grader edits; .claude/skills stays v4;
  holdout-split.json untouched. Known checker bug (the checker dismisses prompt(), so kanban add/rename via prompt() reads as dead
  buttons; files/tl_blind/notes/KNOWN_CHECKER_BUG_prompt.md) stays UNFIXED in this harness; checker results are reported as they come.
- Driver: benchmark/blind/v9_run/blind_driver_v9.py <arm>, a copy of the v8 driver; the arm is a REQUIRED first argument
  (tightloop-v9-on-v4c or tightloop-v9-on-v8, by name or as benchmark/arms/<name>; anything else exits 2). Other changes: paths,
  order file, hold text must contain "v9", START_OK at /home/user/tab/files/tl_blind/v9/START_OK, rows of a different arm in the
  rows file make it refuse (exit 8), and each row carries "test_files".
- Sequence: v8 builds -> v8 blind judge -> v8 reveal -> root applies the BASE RULE (section 0) and picks the arm -> root writes the
  hold (containing "v9") and v9/START_OK -> 9 v9 builds.
- Clocks: no v9 build starts at or after 2026-10-19T03:00:00Z (the night rule "nothing new starts after 8:30 IST"). A build still
  running at 03:15Z is the last one; the run is reported "cut to n of 9".

## 4. Denominators (the SAME as v5c..v8; r2 no-skill builds, cost-weighted, harness logs)

kanban 198,718.9 | bookmarks 249,587.55 | expenses 216,408.95.
cost_weighted = input + 5*output + 0.1*cache_read + 1.25*cache_write (the driver's formula, unchanged).

## 5. PREDICTION (written now)

- P1 test files: shipped test-file count = 0 in EVERY v9 build (9/9). Count = output-folder paths matching TEST_RE in
  blind_driver_v9.py / count_test_files_v9.py (test.js, tests.*, test_* / test-*, *.test.*, *.spec.*, *_test.*/-test.*, any tests/ test/
  __tests__/ spec/ folder; the harness-installed .claude/ skill folder excluded). The blind judge's "unused test file" notes (rubric Q3)
  are reported beside it; P1 is HIT only if both are 0 in every build. Also reported for the base runs (same script).
- P2 tokens: per app, v9 median cost-weighted <= base median + 5 percentage points (base = v4c n=3 or v8 n=3, by section 0).
  With base v4c the bounds are kanban 52.1, bookmarks 60.3, expenses 89.9 (% of no-skill); with base v8 they are computed from the v8
  n=3 medians by the same formula, with no other choice.
- P3 quality: per app, v9 blind-judge median >= base blind-judge median, both scored by the same v9 judge in the same judged set.
Each of P1-P3 is reported HIT or MISS per app (P1 per build) with the number and its n.

## 6. KEEP RULE

- v9 is kept over its base only if it BEATS the base on BOTH tokens (cost-weighted, % of no-skill) AND blind-judge quality.
- P1-P3 are predictions, not the keep rule: a v9 that only removes test files, without beating the base on tokens, is reported
  "FAILED-by-rule" with its numbers (P1 HIT shown beside it). The base stays.
- Report per app: median and min-max of the 3 v9 runs next to the base's n=3 median and min-max. If the ranges overlap, that app is
  "not distinguishable", not a win. A defect that shows in 1 of 3 runs goes in the range (stated per app), not hidden by the median.
- A fail stays a fail: no rescue reruns, no prompt tweaks, no re-tuning and no re-scoring after numbers are in.

## 7. Per-row reporting and crashes

- Every row (v9 and base): cost-weighted and % of no-skill, output tokens, thinking tokens (thinking_total) and prewrite_block, both
  from the FROZEN split rule (/home/user/tab/files/tl_blind/expenses_thinking/SPLIT_RULE.md, sha256
  a3ccc9b4305e8bad5d15f0829f86b44fc3434b1b7d80422da4dde7af87ae1063) via benchmark/blind/v9_run/split_prewrite_v9.py (a copy of
  split_prewrite_v8.py, docstring only changed; it exec's the rule's code unchanged after checking its sha), checker passes, shipped
  test files (count + names), crash count.
- Crash count per run = one count per crash: the number of browser-launch crash events ("Executable doesn't exist") in the build's
  stream-json log, counted once per tool result (not once per line that repeats it). A crash run = crash count >= 1. A count, not a cause.
- A crash column per run in every table; tokens per app reported WITH all runs and WITHOUT crash runs, n printed for each.

## 8. Blind plan

- New sealed key KEY_v9.json, made by benchmark/blind/v9_run/make_key_v9.py at 2026-10-19T00:20:11Z (before any v9 build; it names
  build ids and output dirs only) and stored ONLY under /home/user/tab/files/tl_blind/v9/ (mode 0600, not committed).
  sha256 68bd421d64cdb298e962214bc7909e1f343a0e056207cc97b4f8f246230375d9. Never read after creation (sha256 only).
- Because the base is decided only after the v8 reveal, the one key file holds two independently shuffled variants (own seed each):
  "base_v4c" (per app 3 v9 + 3 tightloop-v4c [r2 + 2 v4c-n3] + r2 no-skill) and "base_v8" (per app 3 v9 + 3 tightloop-v8 + r2 no-skill),
  7 labels A-G per app. The viewer is packed from the variant matching the base picked in section 0; the other variant is never used.
- Judged set per app = 3 v9 + 3 base + r2 no-skill. Rubric: the r2 rubric b8d4711, unchanged, committed by the judge before it opens
  the zip. The judge sees no arm names and no checker counts.
- Viewer zip /home/user/tab/files/tl_blind/v9/viewer.zip: PLAIN zip, no encryption, built the same way as v7/v8 (arm names, prompts,
  logs stripped; leak grep 0).

## 9. IF v9 LOSES

The numbers are reported as they are, P1-P3 HIT/MISS, and v9 is logged "v9 FAILED" (or "FAILED-by-rule" when it removes test files
but does not beat the base on tokens and quality; "not distinguishable" where ranges overlap). The base stays. No rescue, rerun, tweak
or re-score.

## 10. IF RUNS ARE CUT

If the 03:00Z / 03:15Z clocks (or anything else) stop v9 before all builds, n is printed next to every number (per app, e.g.
"expenses n=2"), the missing builds are named, and no claim is made beyond what the n supports. If v9 cannot start before 03:00Z it
is reported "v9 NOT STARTED", with this prereg standing for a later run under a new, dated amendment of its clocks only.
