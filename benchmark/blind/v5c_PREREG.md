# tightloop v5c pre-registration (written 2026-10-18T21:35:22Z, before any v5c build)

Direction: Naman m:ff1086f5 (2:59 AM IST, Oct 19). Target: parity with no-skill on quality at about half the tokens.
Round 2 (r2) put tightloop-v4c at 53% of no-skill's cost-weighted tokens but 1-3 judge points behind on polish and a11y.
Fix tried here: a cheap FIXED finish checklist appended to the skill. Nothing else changes.

## 1. Definition: v5c = v4c + finish checklist
`benchmark/arms/tightloop-v5c/` is a byte copy of `benchmark/arms/tightloop-v4c/` (gate.sh, phases/fail.md, phases/risky.md identical)
with ONE step appended to SKILL.md. Exact diff:

```diff
--- benchmark/arms/tightloop-v4c/SKILL.md	2026-10-18 21:31:28.385031734 +0000
+++ benchmark/arms/tightloop-v5c/SKILL.md	2026-10-18 21:32:42.030108955 +0000
@@ -11,3 +11,5 @@
 3. Reply in 3 lines: change, GATE line, not checked. No more tool calls.
 
 No plan or notes files, subagents, refactors, or comments that restate code.
+
+4. Apps/UI, before replying (one Bash at most), check and fix: (a) empty states show real text, no null/undefined; (b) visible focus styles; (c) labels on inputs; (d) one spacing and type scale; (e) click every feature once (add, edit, delete+confirm, filter, reload).
```

Skill size (token-counting endpoint, no session; method and +9 calibration of benchmark/design/tightloop-v5/DESIGN.md 4.2.1;
script `benchmark/blind/v5c_run/measure_skill_tokens_v5c.py`, output `benchmark/blind/v5c_run/skill_tokens_v5c.json`):

| arm | bytes | raw delta | calibrated (raw+9) |
|---|---|---|---|
| tightloop-v4c | 978 | 424 | 433 (matches the repo's 433) |
| tightloop-v5c | 1,248 | 526 | 535 |
| checklist added | +270 | +102 | **+102 tokens** |

The same run reproduces ponytail 1,283 raw and tightloop-v4 752 raw (A2 values), so the method is unchanged.
Per-build cost of the checklist is measured after the builds as: v5c median cost-weighted minus the r2 v4c build's cost-weighted, per app.

## 2. Runs
- 3 v5c builds per app x 3 apps (bookmarks, expenses, kanban; the r2 specs `benchmark/blind/specs/r2/*.md` unchanged) = 9 builds,
  plus 1 ponytail expenses rerun (r2 ponytail expenses: 56 pts, checker 17/25, list never shown) = **10 builds**.
- Same harness as r2: `runner.launch` (claude CLI, same flags, skill folder in the workspace + `--append-system-prompt`), the r2
  sandbox (`r2_run/sandbox_r2.py`), nice -n 15, 1800 s timeout, the r2 transcript audit/VOID rule, and the r2 checker
  `benchmark/blind/checks/check_app.py` called exactly as in r2. Driver: `benchmark/blind/v5c_run/blind_driver_v5c.py` (a copy of
  `blind_driver_r2.py`; its header lists every change). No harness or grader edits; `.claude/skills` stays v4; holdout-split.json untouched.
- Order: `results/v5c_order.json`, random.Random(seed) with seed 2094089791236836462 (secrets.randbits(63)), recorded:
  v5c-kanban-1, v5c-bookmarks-2, v5c-expenses-3, v5c-kanban-3, v5c-bookmarks-3, ponytail-expenses-rerun, v5c-expenses-2, v5c-kanban-2, v5c-bookmarks-1, v5c-expenses-1.
- Retries: none, except a harness crash (no usable result event): one retry, logged as RETRY with its reason and its tokens kept.
  A transcript that touches checker/key material is VOID and rerun (r2 rule), also logged with its tokens. App failures are never retried.
- Comparison rows come from r2 (`files/tl_blind/r2/BUILD_RESULTS.tsv`, harness log, cost_weighted = in + 5*out + 0.1*cache_read + 1.25*cache_write):

| app | r2 no-skill cw / checks / judge | r2 tightloop-v4c cw (% no-skill) / checks / judge | r2 ponytail cw / checks / judge |
|---|---|---|---|
| bookmarks | 249,588 / 20 of 20 / 99 | 110,207 (44%) / 20 of 20 / 97 | 172,819 / 20 of 20 / 96 |
| expenses | 216,409 / 25 of 25 / 100 | 149,831 (69%) / 25 of 25 / 99 | 107,753 / 17 of 25 / 56 |
| kanban | 198,719 / 10 of 10 / 100 | 93,579 (47%) / 10 of 10 / 97 | 134,898 / 9 of 10 / 96 |

## 3. PREDICTION (written now)
- v5c median cost-weighted <= 60% of r2 no-skill per app: bookmarks <= 149,753; expenses <= 129,845; kanban <= 119,231.
  (Note written now: r2 v4c expenses was already 69%, so expenses is the likely miss.)
- v5c checker pass count >= r2 no-skill on every app (bookmarks 20, expenses 25, kanban 10), read on the median of the 3 runs;
  every run's count is reported.
Each line is reported HIT or MISS with the number.

## 4. KEEP RULE
Noise band = 3 judge points (r2 judge scores within 1-3 points are noise; never a win from n=1).
v5c beats v4c only if its blind judge median score >= v4c's score + more than the noise band (>= +4) AND its median cost-weighted
stays <= 60% of no-skill; otherwise the verdict is "no change vs v4c".
- v4c's score = the r2 judge's score (bookmarks 97, expenses 99, kanban 97). The same r2 v4c builds are re-judged in this round, and
  that score is shown beside it.
- Ceiling note, written before any build: with r2 v4c at 97/99/97 out of 100, a margin of more than 3 points cannot be reached on any
  single app. The rule is therefore applied on the sum over the 3 apps: v5c (sum of per-app medians) >= 293 + 4 = 297, AND tokens <= 60%
  of no-skill on every app. Per-app results are reported as well, but a single app decides nothing.
- Quality parity with no-skill (Naman's target) is read as: v5c median within 3 points of no-skill's score from the same judge, per app.

## 5. FAIL line
parity or worse than ponytail on real tokens = FAIL; no re-scoring after numbers are in.
Read as: v5c's median cost-weighted summed over the 3 apps >= 95% of ponytail's r2 sum (415,470; the ponytail expenses rerun is
reported beside it and does not replace the r2 number). Per-app ratios are also reported.

## 6. Blind judging plan
- New sealed key `KEY_v5c.json`, made by `benchmark/blind/v5c_run/make_key_v5c.py` (secrets seed, random.Random shuffle per app) and stored
  ONLY under /home/user/tab/files/tl_blind/v5c/. sha256 **a8d3c474ad9ed1dffdd47944707ac72bb1876c30e7376a4d2a6da9323391619f**
  (also `results/blind_v5c_key_sha256.txt`). It is never printed or opened after creation; scripts use it only to pack the viewer.
- Judged set per app: the 3 v5c builds + the r2 no-skill build + the r2 tightloop-v4c build = 5 labels A-E; expenses also gets the
  ponytail rerun = 6 labels A-F.
- Viewer zip built the same way as r2 (strip arm names, prompts, logs; leak grep 0 hits required), at files/tl_blind/v5c/viewer.zip.
- A separate blind judge worker scores every label on the r2 rubric (commit b8d4711, `benchmark/blind/r2_JUDGE_RUBRIC.md`), unchanged,
  from clicking through every feature.

## 7. What is reported
Per app: v5c median and min-max cost-weighted (and in+out+cache_read) vs r2 no-skill and r2 v4c, checker passes per run,
the ponytail expenses rerun (does the broken list repeat: yes/no, checker count), and the checklist's token cost (static +102 tokens;
per build: v5c median minus r2 v4c cost-weighted).
