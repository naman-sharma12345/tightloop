# tightloop v6c pre-registration (written 2026-10-18T22:15:56Z, before any v6c build)

Direction: Naman m:e1c448c3 (3:29 AM IST, pt 5) and m:5f617c79 (3:40 AM IST, pt 3): the finish checklist as a READ-ONLY review of what
already exists, not a rewrite pass and not a test harness; edit only if a listed item is actually missing. ONE change vs v5c.
This is a hypothesis. v5c (`v5c_PREREG.md`, commit 72b3bc1) was still building when this was written; nothing here uses its blind judge result.

## 0. Why (evidence available at writing time, all from v5c builds 1-8 of 10; not a result)
- v5c cost-weighted (cw) as % of r2 no-skill, harness log rows in files/tl_blind/v5c/BUILD_RESULTS.tsv: kanban 71, 52, 62; bookmarks 57, 57;
  expenses 74, 90. Every v5c run so far is above r2 v4c (kanban 47, bookmarks 44, expenses 69).
- Root's read of v5c kanban-1's stream-json (one build, a HINT only): the extra calls were a python http.server, a hand-written playwright
  click-test script and a chromium path hunt, i.e. building a test harness, not rewriting the app.
- First pass of v5c TOKEN_WHY.tsv (worker 70a3e3bd, 6 of 10 builds, as found at writing time; output tokens split per build):

```
build	output_total	thinking_tokens	visible_output	first_pass_write	after_a_verification	after_b_app_rewrites_edits	final_reply_text	visible_unattributed	app_files_written_or_edited_more_than_once	app_file_write_counts	mixed_calls_edit_plus_verify	tool_calls	first_pass_tool_calls
v5c-bookmarks-2	19456	3009	16447	16717	97	0	757	-1124	0	app.jsx1;index.htmlx1;styles.cssx1	0	3	2
v5c-bookmarks-3	17706	2762	14944	13353	1510	0	917	-836	0	app.jsx1;index.htmlx1;styles.cssx1	0	5	1
v5c-expenses-2	28520	14265	14255	15042	0	0	570	-1357	0	app.jsx1;index.htmlx1;styles.cssx1	0	2	2
v5c-expenses-3	19556	5175	14381	13094	1320	0	792	-825	0	app.jsx1;index.htmlx1;style.cssx1	0	6	1
v5c-kanban-1	15405	3631	11774	10486	1247	0	737	-696	0	app.jsx1;index.htmlx1;styles.cssx1	0	3	1
v5c-kanban-3	12513	850	11663	10051	1525	0	696	-609	0	app.jsx1;index.htmlx1;style.cssx1	0	4	2
```
  Read: "after_b_app_rewrites_edits" = 0 and "app files edited more than once" = 0 on all 6 rows, so the extra tokens are NOT rewrites. The extra
  is the verification step itself (extra tool calls, each re-sending the context: cache write/read) plus thinking. v5c's item (e) "click every
  feature once" is the item that invites a server + browser + script. v6c replaces it with a static check and forbids browser/server/test script.

## 1. Definition: v6c = v5c with step 4 rewritten as a read-only review
`benchmark/arms/tightloop-v6c/` is a byte copy of `benchmark/arms/tightloop-v5c/` (gate.sh, phases/fail.md, phases/risky.md identical; steps 1-3
and the front matter identical) with ONLY step 4 of SKILL.md replaced. Exact diff:

```diff
--- benchmark/arms/tightloop-v5c/SKILL.md
+++ benchmark/arms/tightloop-v6c/SKILL.md
@@ -12,4 +12,4 @@
 
 No plan or notes files, subagents, refactors, or comments that restate code.
 
-4. Apps/UI, before replying (one Bash at most), check and fix: (a) empty states show real text, no null/undefined; (b) visible focus styles; (c) labels on inputs; (d) one spacing and type scale; (e) click every feature once (add, edit, delete+confirm, filter, reload).
+4. Apps/UI, before replying: one read-only `rg -n` of your files (no browser/server/test script) to confirm (a) empty states show text, no null/undefined; (b) focus styles; (c) input labels; (d) one spacing/type scale; (e) buttons change state. Fix only missing items.
```
What changes: (1) the check is one read-only `rg -n` over the agent's own files, no browser, server or test script; (2) item (e) "click every
feature once" becomes a static "buttons change state"; (3) "check and fix" becomes "fix only missing items". Items (a)-(d) are the same checks.

Skill size (same method as v4c/v5c: token-counting endpoint, no session, raw delta + 9; script `benchmark/blind/v6c_run/measure_skill_tokens_v6c.py`,
a copy of the v5c script with the v6c arm added; output `benchmark/blind/v6c_run/skill_tokens_v6c.json`; the same run reproduces ponytail 1,283,
v4 752, v4c 424, v5c 526 raw):

| arm | bytes | raw delta | calibrated (raw+9) |
|---|---|---|---|
| tightloop-v4c | 978 | 424 | 433 |
| tightloop-v5c | 1,248 | 526 | 535 |
| tightloop-v6c | 1,248 | 525 | **534** |

## 2. Runs
- 3 v6c builds per app x 3 apps (bookmarks, expenses, kanban; the r2 specs `benchmark/blind/specs/r2/*.md` unchanged) = **9 builds**. No ponytail rerun.
- Same harness, flags, checker and snapshot method as v5c: `runner.launch` (claude CLI, same flags, skill folder in the workspace +
  `--append-system-prompt`), the r2 sandbox (`r2_run/sandbox_r2.py`), nice -n 15, 1800 s timeout, the r2 transcript audit/VOID rule, and the r2
  checker `benchmark/blind/checks/check_app.py` called exactly as in r2/v5c. The driver runs from a git-archive snapshot of this commit
  (/home/user/tab/work/tl_blind_v6c, `.snap_commit`). Driver: `benchmark/blind/v6c_run/blind_driver_v6c.py`, a copy of `blind_driver_v5c.py`;
  its header lists every change (paths, plan, its own "v6" hold, the v6c key on the probe watch list). No harness or grader edits;
  `.claude/skills` stays v4; holdout-split.json untouched.
- Order: `results/v6c_order.json`, random.Random(seed), seed 6718903109003726878 (secrets.randbits(63)), recorded:
  v6c-kanban-1, v6c-bookmarks-3, v6c-bookmarks-2, v6c-bookmarks-1, v6c-expenses-3, v6c-kanban-3, v6c-expenses-2, v6c-expenses-1, v6c-kanban-2.
- Retries: none, except a harness crash (no usable result event): one retry, logged as RETRY with its reason and tokens. A transcript that
  touches checker/key material is VOID and rerun (r2 rule), logged with its tokens. App failures are never retried. No rescue reruns, no tweaks.
- Per build: BUILD_RESULTS.tsv (same columns as v5c) and TOKEN_WHY.tsv (same columns as v5c's) under files/tl_blind/v6c/.
- Baselines (r2 harness-log rows, cw = in + 5*out + 0.1*cache_read + 1.25*cache_write), unchanged denominators:

| app | r2 no-skill cw | 60% line | r2 v4c cw (% no-skill) |
|---|---|---|---|
| bookmarks | 249,587.55 | 149,752.53 | 110,207 (44%) |
| expenses | 216,408.95 | 129,845.37 | 149,831 (69%) |
| kanban | 198,718.90 | 119,231.34 | 93,579 (47%) |

## 3. PREDICTION (written now)
- P1 tokens: v6c median cw <= 60% of r2 no-skill on every app (bookmarks <= 149,753; expenses <= 129,845; kanban <= 119,231).
- P2 tokens vs v5c: v6c median cw < v5c median cw on every app (v5c medians taken from files/tl_blind/v5c/BUILD_RESULTS.tsv once all 9 v5c builds
  are in; v6c's builds start only after that file is complete).
- P3 checker: v6c median checker passes >= v5c median checker passes on every app; every run's count is reported.
Each line is reported HIT or MISS with the number. Note written now: v4c expenses was already 69% with no checklist, so P1 expenses is the likely miss.

## 4. KEEP RULE (Naman m:aca6d590 pt 1-2, m:5f617c79 pt 2; brief for this round)
Keep v6c over the previous kept version only if it beats it on BOTH tokens AND blind-judge quality. Otherwise the verdict is "no change".
- Previous kept version at writing time: tightloop-v4c (r2). v5c has no verdict yet. If v5c is kept by its own prereg rule before this round's
  judge result exists, v6c is compared to v5c instead (tokens: v5c's 3 runs per app; quality: each round judges the same r2 v4c builds, so the
  comparison is v6c's margin over v4c here vs v5c's margin over v4c in its round, labelled CROSS-ROUND). Both comparisons are reported either way.
- Per app, always reported: v6c median and min-max (cw tokens, checker passes, judge score).
- "Distinguishable" per app: a single-build reference X (r2 v4c) counts as beaten only if X lies outside v6c's min-max range on the better side
  (tokens: v6c max < X; quality: v6c min > X); if X lies inside the range the app is "not distinguishable". For an n=3 reference (v5c) the two
  ranges must not overlap. Judge differences of 3 points or less are noise (noise band 3), so a quality win on an app also needs median - X >= 4.
- Beats on tokens = distinguishably better on at least 2 of 3 apps and distinguishably worse on none. Same for quality.
- Ceiling note, written now: r2 v4c scored 97/99/97, so a +4 quality margin is impossible on expenses and needs a perfect 100+ on the others; if
  this round's judge re-scores v4c at 97 or above, a quality "beat" is out of reach on that app and the honest verdict is "not distinguishable".
  That is accepted in advance; the rule is not loosened after the numbers are in.
- Defects that show in 1 of 3 runs go into the range (min), never hidden behind the median. A fail stays a fail: no rescue reruns, no prompt tweaks,
  no re-scoring after the numbers are in.

## 5. Blind judging plan
- New sealed key `KEY_v6c.json`, made by `benchmark/blind/v6c_run/make_key_v6c.py` (a copy of make_key_v5c.py; secrets seed, random.Random shuffle
  per app, labels freshly drawn) and stored ONLY under /home/user/tab/files/tl_blind/v6c/. sha256
  **b07d9fe54b35f8f59ec1fcc32cb65e7fcb7eb57fd4ecafef105f3468057b02a0** (also `results/blind_v6c_key_sha256.txt`). Never printed or opened after creation; scripts use it only to pack the viewer.
- Judged set per app: the 3 v6c builds + the r2 no-skill build + the r2 tightloop-v4c build = 5 labels A-E (fresh per app).
- Viewer zip built the same way as r2/v5c (strip arm names, prompts, logs; leak grep 0 hits required), at files/tl_blind/v6c/viewer.zip.
- A separate blind judge worker scores every label on the r2 rubric (commit b8d4711, `benchmark/blind/r2_JUDGE_RUBRIC.md`), unchanged, from
  clicking through every feature. The mapping stays out of every file and message until the judge's ranks are committed and hashed.

## 6. What is reported
Per app: v6c median and min-max cw (and in+out+cache_read) vs r2 no-skill, r2 v4c and v5c; checker passes per run; TOKEN_WHY per build
(first-pass write vs verification vs rewrites, files edited twice, tool calls); P1-P3 HIT/MISS; the keep verdict per section 4.
