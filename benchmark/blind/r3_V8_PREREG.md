# Pre-registered plan: blind round for tightloop-v8 (r3)

Written 2026-10-19, before any v8 blind-round build starts. Author: the benchmark scoring agent (no model session). The author runs nothing in this round; this doc only fixes the plan.

## Gate status: UNMET - do not spend this round on v8 as-is

The row scoring's pass gate ("no v8 better-on-tokens claim until its passes match v4c") is currently UNMET: on tuning, v8 passes gin-01 1/3 vs v4c 3/3, and v8 costs 1.20x no-skill on tokio-02 (v4c 0.98), all n=3. Until a fixed v8-line arm matches v4c's checker passes on tuning, no blind round is spent on v8 as-is. This plan sits ready for the fixed arm.

## Purpose

Decide whether a tightloop-v8-line arm's app-build quality matches tightloop-v4c and no-skill on the round-2 apps. Until this round lands, v8 is tokens-only: no v8 better-on-tokens claim stands until v8's checker passes match v4c on the same tasks, and no quality claim exists without a sealed-key blind round.

## Design

- Apps: the r2 set - bookmarks, expenses, kanban, same specs as r2 (benchmark/blind/specs).
- Arms: tightloop-v8 (the fixed arm), tightloop-v4c, no-skill. No other arm joins once the key is sealed.
- Builds: built by Tab's session, same harness as r2; retries and checker scores recorded as in r2's BUILD_RESULTS.tsv. The author of this doc runs nothing.
- Sample size (thin n), two pre-registered options:
  - Option A (if budget allows): 2 builds per cell = 6 builds per app, 18 total.
  - Option B (fallback): 1 build per cell = 3 builds per app; the judge scores the same zip twice, in a shuffled order the second time, and the spread between the two scorings is reported alongside each score.
- Reporting is per app, not only pooled. Per-app totals and front scores are the primary output; pooled means are secondary.
- Judging: a separate judge, not the builder and not this doc's author, judges from zipped builds with labels only. The judge works from its own copy of the zip (sha256 of both copies recorded), does a Playwright click-through of every spec feature at 1280x800 and 375 px, captures console and page errors and external requests, reads the source, and uses screenshots of post-click-through state for design lines only - the r2 judge protocol.

## Scoring: absolute 0-10 per front, no ranks

This replaces r2's rank ordering. Each build gets an absolute score per front and one total:

- FUNCTION (how it works): 0-10
- DESIGN (how it looks): 0-10
- QUALITY: 0-10
- Build total: sum of the three fronts, 0-30.

### What changed vs the r2 rubric (b8d4711), exactly

The fronts, sub-lines, full-marks conditions, click-through method, and deductions-within-a-line rule of benchmark/blind/r2_JUDGE_RUBRIC.md at commit b8d4711 are kept unchanged. b8d4711 (2026-10-18T21:03:06Z) is the only commit that has ever touched that file (checked against main 066f2c1 and v6/instinct-rows 64ec5bc at write time). The only change is aggregation:

- The judge still scores every b8d4711 sub-line on its native points (F1-F5 out of 40, D1-D5 out of 35, Q1-Q3 out of 25), with a one-line reason each.
- Each front's raw points are then scaled to 0-10 (FUNCTION: raw/40 x 10; DESIGN: raw/35 x 10; QUALITY: raw/25 x 10), and the three scaled fronts sum to the build total (0-30).
- Ranks and the mean-rank overall order are dropped; absolute totals and per-front scores are reported per app instead.

A rubric change beyond this aggregation mapping, made before the zip is opened, is committed and recorded in the round's REVEAL doc; a rubric changed after the zip is opened voids the round.

## Pass line (fixed now)

Per app: v8 passes on that app only if v8's build total >= 2x no-skill's build total AND v8 is not below no-skill on any front. With 2 builds per cell (option A), each side's per-app total is the mean of its 2 builds; with option B, the mean of the two scorings, with the spread reported. The round verdict is per app; there is no pooled pass.

## Sealed key and manifest hashes

- Sealed key: r3_KEY_v1.json (3 apps x 3 arms x 2 builds, labels A-F shuffled per app). Generated 2026-10-19, held sealed outside the repo by the scoring agent; never shown to the builder or the judge before ranks are committed. sha256: 6cabbc786f07c61fc27716e56cc908d29036b80ee736c47d8b175a137c884c82. If only 1 build per cell is run (option B), only each label's build-1 entries are used and the build-2 labels stay unused; the key and its hash still stand.
- The key is opened only after the judge's ranks-file commit lands. The REVEAL doc records the key sha256, the ranks commit sha256, and the ranks file sha256, mirroring benchmark/blind/r2_REVEAL.md, and the published key must hash to the value above.
- Holdout manifest anchor: holdout/HOLDOUT_MANIFEST.tsv at v6/instinct-rows 64ec5bc, sha256 f2f4211650d5226ebd13ff6b67c3fe70b6ca81052e08b6f2d287978c73206e4b (490 bytes). Manifest timing note kept: the manifest was first committed in 33f55c1 (2026-10-19T06:32:38Z), about 88 minutes after the first holdout row (c8ebc4f, 05:04:21Z); the ghcli-01b manifest line and order file (0351248, 06:58:39Z) precede the first ghcli-01b row (523eb20, 07:03:42Z).
- Leak check before the zip goes to the judge (r2 used benchmark/blind/leakgrep_r2.py): no arm-identifying string in any build.

## Pre-registered analysis

- Primary: per-app front scores (0-10 each) and build totals (0-30), and the pass line above.
- Secondary: cost-weighted tokens (in + 5*out + 0.1*cache_read + 1.25*cache_write), output tokens, build seconds, checker score per build.
- Option A reports 2 builds per cell; option B reports 1 build scored twice with its spread. Either way the sample is small and is reported as such, the same caveat r2 carries.
- A broken build (r2's ponytail expenses went 17/25) is reported as broken, not averaged away.
- Integrity: the judge records any contamination in an integrity note, as r2's judge did. Any round where the key or the skill texts reach the judge's context before the score commit lands is void.

## Out of scope

No tuning-set reruns, no holdout tasks, no wall-time claims.
