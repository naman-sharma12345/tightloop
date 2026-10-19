# tightloop v4c-n3 pre-registration (written 2026-10-18T23:29:04Z, before any v4c-n3 build)

Direction: Naman m:211e0d2f (4:53 AM IST Oct 19, pt 1): "v4c is n=1 per app and its the bar ... run v4c to n=3 on all three apps so the
compare is fair. one lucky v4c run is not a baseline." Written BEFORE any v4c-n3 build and before v7 is complete or judged.
Branch v6/v8-prep, based on origin/v6/v7-prep (22747fb, the v7 prereg). Structure copied from v7_PREREG.md.

## 0. Purpose

A fair baseline. tightloop-v4c is the last KEPT version and the bar for v7 and v8, but round 2 ran it once per app (n=1):
kanban 47.1%, bookmarks 44.2%, expenses 69.2% of r2 no-skill cost-weighted; r2 judge scores (b8d4711 rubric, r2_REVEAL.md at c0e44f8)
bookmarks 97, expenses 99, kanban 97. This round adds 6 NEW v4c builds (2 per app) so that, with the r2 build
as run 1, v4c reaches n=3 per app. This is NOT a new version: there is no prediction to hit and no keep decision; it only measures v4c.

## 1. Definition (nothing changes)

- Arm: benchmark/arms/tightloop-v4c, UNCHANGED (SKILL.md sha256 6c2683f102ddbb000b779a9aefe2367b8342f1253b66c8fe6056b3561b2cf7e7,
  978 bytes, 433 tokens by the repo method; gate.sh and phases/ as in r2). Same skill delivery as r2 (skill folder in the workspace +
  --append-system-prompt).
- Same 3 r2 specs (benchmark/blind/specs/r2/{bookmarks,expenses,kanban}.md), same checker (benchmark/blind/checks/check_app.py), same
  harness (runner.launch), same CLI flags, same sandbox (sandbox_r2), nice -n 15, 1800 s timeout, transcript audit + VOID rule, one RETRY
  on a harness crash only. No harness or grader edits; .claude/skills stays v4; holdout-split.json untouched.

## 2. Runs

- 6 builds: tightloop-v4c x runs 2 and 3 x the 3 r2 specs (run 1 = the r2 build, already on file).
- Order: results/v4cn3_order.json, seed 3844806013510945557 (random.Random(seed).shuffle, make_order_v4cn3.py), created 2026-10-18T23:26:39Z:
  v4cn3-kanban-2, v4cn3-bookmarks-2, v4cn3-expenses-3, v4cn3-expenses-2, v4cn3-bookmarks-3, v4cn3-kanban-3.
- Driver: benchmark/blind/v4cn3_run/blind_driver_v4cn3.py, a copy of the v7 driver with only paths, arm (tightloop-v4c), order file,
  hold text "v4c-n3", START_OK at /home/user/tab/files/tl_blind/v4cn3/START_OK and the clocks changed. It runs from the snapshot
  /home/user/tab/work/tl_blind_v4cn3 (git archive of the v8 prereg commit, which carries this driver unchanged).
- START_OK is written by root only after v7's builds end. Clock: no v4c-n3 build starts at or after 2026-10-19T03:00:00Z; the build in
  progress finishes and the run is reported "cut to n of 6".
- Key: none of its own. The 6 builds are judged blind inside the v8 judge set (KEY_v8.json, v8_PREREG.md section 6).

## 3. Denominators (the SAME as v5c/v6c/v7)

kanban 198,718.9 | bookmarks 249,587.55 | expenses 216,408.95 (r2 no-skill builds, cost-weighted, harness logs).
cost_weighted = input + 5*output + 0.1*cache_read + 1.25*cache_write (the driver's formula, unchanged).

## 4. What is reported

- Per build: cost-weighted tokens and % of no-skill, checker passes, crash count.
- Crash count per run = the number of times the browser-launch crash line ("Executable doesn't exist") appears in the build's
  stream-json log (the same count used for v7). A crash run = crash count >= 1. A count, not a cause.
- Per app at n=3 (r2 run + 2 new): median [min-max] of % of no-skill, WITH all runs and WITHOUT crash runs (n printed for each).
- Checker passes per run; blind quality from the v8 judge set (median [min-max] per app at n=3 once judged).
- No rescue reruns: a bad or crashed v4c run stays in. If runs are cut, n is printed next to every number.
