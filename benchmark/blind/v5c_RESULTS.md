# tightloop v5c results: builds and tokens (blind judge still pending)

Pre-registration: `benchmark/blind/v5c_PREREG.md` (commit 72b3bc1, before any build). Builds 21:41-22:20Z Oct 18, 10 of 10, in the
pre-registered order. Retries 0, VOID 0, overlap clean on every build. Source: the harness log (claude CLI stream-json result event
parsed by runner.launch), `results/blind_v5c_BUILD_RESULTS.tsv` and `results/blind_v5c_rows.jsonl`.
cost_weighted (cw) = in + 5*out + 0.1*cache_read + 1.25*cache_write, the same formula as r2. Denominators (r2 no-skill cw, the same r2 runs v4c was divided by):
kanban 198,718.9 / bookmarks 249,587.55 / expenses 216,408.95.

## v5c tokens per app (n=3), against r2

| app | v5c median cw (% no-skill) | v5c min-max (% no-skill) | v5c runs | r2 no-skill cw | r2 v4c cw (% no-skill) | v5c median - r2 v4c | v5c checker per run |
|---|---|---|---|---|---|---|---|
| bookmarks | 143,041 (57.3%) | 142,878-163,871 (57.2%-65.7%) | 163,871, 143,041, 142,878 | 249,587.55 | 110,207 (44.2%) | +32,834 (+30%) | 20/20, 20/20, 20/20 |
| expenses | 160,308 (74.1%) | 130,990-194,190 (60.5%-89.7%) | 130,990, 194,190, 160,308 | 216,408.95 | 149,831 (69.2%) | +10,477 (+7%) | 25/25, 25/25, 25/25 |
| kanban | 123,859 (62.3%) | 103,980-141,525 (52.3%-71.2%) | 141,525, 123,859, 103,980 | 198,718.90 | 93,579 (47.1%) | +30,280 (+32%) | 10/10, 10/10, 9/10 |
| 3-app total (sum of medians) | 427,207 (64.3%) | | | 664,715.40 | 353,617 (53.2%) | +73,590 (+21%) | |

Median in+out+cache_read: bookmarks 242,193, expenses 104,020, kanban 168,322.
Median output tokens: v5c bookmarks 19,456 / expenses 19,556 / kanban 14,316; r2 v4c 14,832 / 18,206 / 12,443.

## Checker defects (every v5c build)
- bookmarks 1, 2, 3: 20/20, no failed item, no dead button, 0 console/page errors.
- expenses 1, 2, 3: 25/25, no failed item, no dead button, 0 console/page errors.
- kanban 1, 2: 10/10, no dead button. kanban 3: 9/10, failed "every visible button changes page state"; buttons with no effect: "+ Add column" and 3 column-edit pencils (✎). 0 console/page errors.

## Ponytail expenses, both runs side by side (the rerun does not replace r2; the blind judge decides)
| run | cw | checker | judge |
|---|---|---|---|
| r2 (Oct 18 20:29Z) | 107,753 | 17/25 (list never showed) | 56 in r2; re-judged in this round's blind set |
| rerun (Oct 18 22:03Z) | 113,048 | 25/25, no dead button, 0 errors | pending (in this round's blind set) |

## Checklist token cost
- Static: the skill grows from 433 to 535 tokens (+102 per load; count_tokens method, raw+9).
- Per build: v5c median minus r2 v4c cw = bookmarks +32,834 (+30%), expenses +10,477 (+7%), kanban +30,280 (+32%); 3-app total +73,590 (+21%).
- Where the output went: `results/blind_v5c_TOKEN_WHY.tsv` (files/tl_blind/v5c/TOKEN_WHY.tsv), made under ONE written rule,
  `benchmark/blind/v5c_TOKEN_SPLIT_RULE.md` (v1 committed 7f9f269 before re-splitting; v1.1 amendment in the same file), applied to all
  10 builds. Disclosure: a first TOKEN_WHY.tsv (9 v5c builds, three generations, 22:12-22:23Z) existed before the rule was written.
  Re-applying the rule changed no number for any of the 9 v5c builds; the ponytail rerun row is new.
  Per v5c build (n=9), visible output: first-pass write 9,304-15,423; click-test/verification script 0-1,599 (0 in expenses 1 and 2,
  which wrote no click test); rewrite/edit of app files 0 in all 9; other tool calls 0; final reply 570-917. Thinking 850-14,265.
  App files written or edited more than once: 0 in all 9. Tool calls 2-8.
- Did the click test run? In NO build. 8 of 10 builds (7 v5c + the ponytail rerun) wrote a Playwright click-through script.
  Every launch failed with "BrowserType.launch: Executable doesn't exist at /home/user/.cache/ms-playwright/chromium_headless_shell-1243/..."
  (the build sandbox mounts an empty /home/user, so the browser binary is not there). Several builds then searched the disk for a chrome
  binary or tried `playwright install` (no network), and that failed too. v5c expenses 1 and 2 wrote no click-test script.
  So checklist item (e) "click every feature once" was attempted but never executed in any v5c build. The scripts' targets
  (never executed) are listed per build in the TSV. kanban-3's script targeted #add-column and a column delete button, never the
  column-edit pencils that the checker found dead.

## Pre-registered readings (tokens and checker; quality waits for the blind judge)
- PREDICTION tokens <= 60% of no-skill per app: bookmarks 57.3% HIT; expenses 74.1% MISS (THE miss; range 60.5-89.7%); kanban 62.3% MISS (range 52.3-71.2%).
- PREDICTION checker >= r2 no-skill (median of 3): bookmarks 20 HIT, expenses 25 HIT, kanban 10 HIT (range 9-10: kanban 3 has the dead-button defect above).
- KEEP RULE: its token half (<= 60% of no-skill on every app) fails on expenses and kanban, so v5c cannot be "beats v4c", whatever the judge says.
  Verdict: "no change vs v4c". The judge's per-app median and min-max are still reported when they exist, next to the 3-app total.
- FAIL line ("parity or worse than ponytail on real tokens = FAIL; no re-scoring after numbers are in"): the v5c sum of medians is 427,207 =
  102.8% of ponytail's r2 sum 415,470 (>= 95%). **FAIL.** With the rerun's expenses number in place of r2's, it would be 101.5%; still FAIL.
  Per app, v5c median vs ponytail r2: bookmarks 83%, expenses 149%, kanban 92%.

## Blind set
viewer.zip sha256 e6ead87f37745650cea98ee0b858a0f8c4b431bf908bc056e9d252589c23ddf9 (files/tl_blind/v5c/viewer.zip, 17 labels): bookmarks A-E and kanban A-E (3 v5c + r2 no-skill + r2 v4c,
labels from the sealed KEY_v5c.json sha256 a8d3c474...619f); expenses A-G = 7 entries (3 v5c + r2 no-skill + r2 v4c + r2 ponytail
+ ponytail rerun as SEPARATE entries), labels from a NEW sealed key KEY_v5c_expenses7.json, sha256
addafd22424fccaa9c71b16468e9d6dcbb6ec028b1feb8edb9d3fcb6faf876e7 (`make_key_v5c_expenses7.py`, fresh secrets seed, shuffle over all 7).
ADDENDUM: the 7-entry expenses set was made at Naman's instruction (m:ecfa8839, 3:47 AM IST Oct 19) BEFORE any judging. KEY_v5c.json's
expenses part (6 labels) is unused. A first viewer.zip (sha256 55afd9b1e75ff607d64dd4693c9d1e5edd80daa97a6a182b534d1b164f76f983, 6 expenses labels)
was packed at 22:21Z, never judged and never sent, and was deleted when this one replaced it. The mapping exists only in the two sealed keys,
which were never opened by hand. Leak grep: 0 hits over 17 build dirs, 55 zip entries and the unzipped tree; fixed zip timestamps; no .git entries.
