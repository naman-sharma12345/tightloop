# tightloop v8 pre-registration (written 2026-10-18T23:30:53Z, before any v8 build)

Direction: Naman m:211e0d2f (4:53 AM IST Oct 19, pt 4): "v8 should target that block directly, one change, written down and hashed
before you build it. dont change the frozen split rule." Written BEFORE any v8 build, before any v4c-n3 build, and before v7 is complete
or judged. Branch v6/v8-prep (on 22747fb = v6/v7-prep, then cc35968 = the v4c-n3 prereg). Structure copied from v7_PREREG.md.

## 0. Base version and comparison

- BASE = tightloop-v4c (the 3-call skill, 433 tokens), the last KEPT version at prereg time. v5c failed (tokens); v6c failed its
  prediction; v7 is building now and is not judged.
- v8 is compared against tightloop-v4c at n=3 per app (the r2 build + the 2 v4c-n3 builds, v4cn3_PREREG.md), tokens and blind quality.
- IF v7 is later KEPT (beats v4c on BOTH tokens and blind quality under v7_PREREG.md), v8 is ALSO compared against v7 with the same
  rules below, and that comparison is labelled "v8 vs kept v7". The primary keep decision stays "v8 vs v4c" as written here.

## 1. Evidence (the frozen split, its rule NOT changed)

/home/user/tab/files/tl_blind/expenses_thinking/SPLIT_RULE.md, sha256 a3ccc9b4305e8bad5d15f0829f86b44fc3434b1b7d80422da4dde7af87ae1063
(written 2026-10-18T22:59:09Z, before any split), and SPLIT.tsv. In every expenses build the thinking text is empty (signature only), so
the split is by position. Almost all of the expenses thinking sits in ONE block, right before the single "write the whole app" call
(SPLIT.tsv prewrite_block column): no-skill 1,613; v4 1,554; ponytail 1,008 / 639; v4c 4,905; v5c 3,918 / 13,728 / 4,550;
v6c 733 / 12,566 / 13,551. In the 3 costly runs (v5c-2, v6c-2, v6c-3) that block is 12.6-13.7k thinking tokens, about 30-33% of
no-skill's whole expenses cost (x5 output weight), and it is the gap between the ~50-60% runs and the ~90% runs.

## 2. Definition (ONE change vs v4c)

v8 = tightloop-v4c with ONE sentence added to step 2, aimed at that pre-write thinking block: "Before this call, think only a short
plan (a few lines: files, data model, handlers); do not draft code or re-plan in thinking; write the code in the tool call."
Steps 1 and 3, the frontmatter, gate.sh and phases/ are byte-identical to v4c. No harness, flag or checker edits.

Hypothesis: the pre-write thinking block stays near 1-2k (as in no-skill / ponytail / v4), so expenses lands <= 60% of no-skill and the
spread across runs narrows, while quality stays at v4c's level because the code itself is still written in full in the tool call.

Exact diff (benchmark/arms/tightloop-v4c -> benchmark/arms/tightloop-v8; only SKILL.md differs):

```
--- a/benchmark/arms/tightloop-v4c/SKILL.md
+++ b/benchmark/arms/tightloop-v8/SKILL.md
@@ -7,7 +7,7 @@ description: Smallest proven fix in 3 tool calls. Use on any coding task.
 Every tool call re-sends ~30k tokens, so finish in 3 calls. This skill is already loaded; never call the Skill tool.
 
 1. One Bash: `rg -n` the key symbols, then `sed -n` only the 20-40 lines you need and the nearest test. No whole-file reads, no cat. Concurrency, security, data loss or public API: also `cat .claude/skills/tightloop/phases/risky.md` here.
-2. One Bash: apply all edits (root-cause fix + one test that fails without it) by heredoc/python, then in the same command `bash .claude/skills/tightloop/gate.sh "<narrowest test>" <changed source files> 2>&1 | tail -40`. Check empty, boundary and error inputs before writing. Only on GATE FAIL: read .claude/skills/tightloop/phases/fail.md, fix, rerun once.
+2. One Bash: apply all edits (root-cause fix + one test that fails without it) by heredoc/python, then in the same command `bash .claude/skills/tightloop/gate.sh "<narrowest test>" <changed source files> 2>&1 | tail -40`. Check empty, boundary and error inputs before writing. Before this call, think only a short plan (a few lines: files, data model, handlers); do not draft code or re-plan in thinking; write the code in the tool call. Only on GATE FAIL: read .claude/skills/tightloop/phases/fail.md, fix, rerun once.
 3. Reply in 3 lines: change, GATE line, not checked. No more tool calls.
 
 No plan or notes files, subagents, refactors, or comments that restate code.
```

SKILL.md sha256: v4c 6c2683f102ddbb000b779a9aefe2367b8342f1253b66c8fe6056b3561b2cf7e7; v8 10f98337ec7382d8fd45d3b47705c6ff69975b1d1d75c7a1ce9bc1645f31a256.
Bytes: v4c 978, v8 1139.

Skill size (same method as v4c/v5c/v6c/v7: token-counting endpoint, no session, raw delta + 9; script
benchmark/blind/v8_run/measure_skill_tokens_v8.py, output benchmark/blind/v8_run/skill_tokens_v8.json):
v4c 433 | v7 508 | v5c 535 | v6c 534 | v8 483 (raw 474; ponytail 1283 raw, v4 752 raw, v4c 424 raw and v7 499 raw reproduce, so the
method matches). v8 costs +50 tokens per skill load vs v4c.

## 3. Runs

- 9 builds: tightloop-v8 x 3 runs x the same 3 r2 specs (benchmark/blind/specs/r2/{bookmarks,expenses,kanban}.md).
- Order: results/v8_order.json, seed 7457798093998887802 (random.Random(seed).shuffle, make_order_v8.py), created 2026-10-18T23:26:39Z:
  v8-kanban-2, v8-bookmarks-2, v8-expenses-3, v8-bookmarks-3, v8-bookmarks-1, v8-expenses-2, v8-kanban-1, v8-expenses-1, v8-kanban-3.
- Same checker (benchmark/blind/checks/check_app.py), same harness (runner.launch), same CLI flags, same sandbox (sandbox_r2), same
  snapshot method (git archive of this commit -> /home/user/tab/work/tl_blind_v8, .snap_commit), nice -n 15, 1800 s timeout,
  transcript audit + VOID rule, one RETRY on a harness crash only. No harness or grader edits; .claude/skills stays v4;
  holdout-split.json untouched.
- Driver: benchmark/blind/v8_run/blind_driver_v8.py, a copy of the v7 driver with only paths, arm (tightloop-v8), order file, hold text
  "v8", START_OK at /home/user/tab/files/tl_blind/v8/START_OK and the clocks changed.
- Sequence: v7's builds end -> root writes v4cn3/START_OK -> 6 v4c-n3 builds -> root writes v8/START_OK -> 9 v8 builds.
- Clocks: no v8 build starts at or after 2026-10-19T03:00:00Z. A build still running at 03:15Z is the last one; the run is reported
  "cut to n of 9".

## 4. Denominators (the SAME as v5c/v6c/v7; r2 no-skill builds, cost-weighted, harness logs)

kanban 198,718.9 | bookmarks 249,587.55 | expenses 216,408.95.
cost_weighted = input + 5*output + 0.1*cache_read + 1.25*cache_write (the driver's formula, unchanged).

## 5. PREDICTION (written now)

- P1 tokens: v8 median cost-weighted <= 60% of r2 no-skill per app AND <= v4c(n=3) median + 5 percentage points per app.
  The v4c(n=3) medians do not exist yet (v4c-n3 builds after this commit); the bound is min(60%, v4c n=3 median + 5) per app, computed
  from the v4c-n3 results by this formula with no other choice. For reference only, at n=1 (r2) it would be kanban 52.1%,
  bookmarks 49.2%, expenses 60.0%.
- P2 checker: per app, v8 median checker passes >= v4c(n=3) median checker passes (ranges printed; r2 v4c was 10/10, 20/20, 25/25).
- P3 quality: per app, v8 blind-judge median >= v4c(n=3) blind-judge median, both scored by the same v8 judge in the same judged set.
- P4 pre-write block: per app, the median prewrite_block of the 3 v8 runs <= 3,000 thinking tokens (expenses is the primary test),
  measured with the FROZEN split rule via benchmark/blind/v8_run/split_prewrite_v8.py (it exec's the rule's code unchanged after
  checking sha a3ccc9b4...; prewrite_block = the scaled thinking block right before the first app write, the SPLIT.tsv column; the
  script reproduces SPLIT.tsv's prewrite_block for all 11 expenses runs already on file). The same is reported for the v4c-n3 runs.
- Spread (descriptive, not a keep criterion): v8 expenses max-min in points vs v4c(n=3)'s.
Each of P1-P4 is reported HIT or MISS per app with the number and its n.

## 6. KEEP RULE

- v8 is kept over v4c only if it beats v4c(n=3) on BOTH tokens (cost-weighted, % of no-skill) AND blind-judge quality.
- Report per app: median and min-max of the 3 v8 runs next to v4c's n=3 median and min-max. If the ranges overlap, that app is
  "not distinguishable", not a win. A defect that shows in 1 of 3 runs goes in the range (stated per app), not hidden by the median.
- A fail stays a fail: no rescue reruns, no prompt tweaks, no re-tuning and no re-scoring after numbers are in.

## 7. Crashes

- Crash count per run = the number of times the browser-launch crash line ("Executable doesn't exist") appears in the build's
  stream-json log (the count used for v7). A crash run = crash count >= 1. A count, not a cause.
- A crash column per run in every table; tokens per app reported WITH all runs and WITHOUT crash runs, n printed for each.

## 8. Blind plan

- New sealed key KEY_v8.json, made by benchmark/blind/v8_run/make_key_v8.py at 23:28Z (before any v4c-n3 or v8 build; it names build ids
  and output dirs only) and stored ONLY under /home/user/tab/files/tl_blind/v8/ (mode 0600, not committed).
  sha256 0a0e2877f89ae723f47857e6a0c8d5ffb52e180b21d655a79d1988223b909d51. Never read after creation (sha256 only). After the key was made, one docstring word in make_key_v8.py was corrected
  ("a copy of make_key_v7.py"); no code line changed.
- Labels freshly shuffled per app (fresh seed inside the key). Judged set per app = 3 v8 builds + 3 tightloop-v4c builds (the r2 build +
  the 2 v4c-n3 builds) + the r2 no-skill build (7 labels A-G). Rubric: the r2 rubric b8d4711, unchanged. The judge sees no arm names
  and no checker counts.
- Viewer zip /home/user/tab/files/tl_blind/v8/viewer.zip: PLAIN zip, no encryption (Naman m:211e0d2f), built the same way as v5c/v6c/v7
  (arm names, prompts, logs stripped; leak grep 0).

## 9. IF v8 LOSES

The numbers are reported as they are, P1-P4 HIT/MISS per app, and v8 is logged "v8 FAILED" (or "not distinguishable" where ranges
overlap). The previous kept version stays. No rescue, rerun, tweak or re-score.

## 10. IF RUNS ARE CUT

If the 03:00Z / 03:15Z clocks (or anything else) stop v4c-n3 or v8 before all builds, n is printed next to every number (per app, e.g.
"expenses n=2"), the missing builds are named, and no claim is made beyond what the n supports.
