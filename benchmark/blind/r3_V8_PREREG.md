# Pre-registered plan: blind round for tightloop-v8 (r3)

Written 2026-10-19, before any v8 blind-round build starts. Author: the benchmark scoring agent (no model session). The author runs nothing in this round; this doc only fixes the plan.

## Purpose

Decide whether tightloop-v8's app-build quality matches tightloop-v4c and no-skill on the round-2 apps. Until this round lands, v8 is tokens-only: no v8 better-on-tokens claim stands until v8's checker passes match v4c on the same tasks, and no quality claim exists without a sealed-key blind round.

## Design

- Apps: the r2 set - bookmarks, expenses, kanban, same specs as r2 (`benchmark/blind/specs`).
- Arms: tightloop-v8, tightloop-v4c, no-skill. No other arm joins once the key is sealed.
- Builds: 1 build per app per arm, built by Tab's session. Same harness as r2; retries and checker scores recorded as in r2's BUILD_RESULTS.tsv.
- Judging: a separate judge, not the builder and not this doc's author, judges from zipped builds with labels only. The judge works from its own copy of the zip (sha256 of both copies recorded), does a Playwright click-through of every spec feature at 1280x800 and 375 px, captures console and page errors and external requests, reads the source, and uses screenshots of post-click-through state for design lines only - the r2 judge protocol.

## Rubric

Reuse `benchmark/blind/r2_JUDGE_RUBRIC.md` from commit b8d4711, unchanged. Verified at write time: b8d4711 (2026-10-18T21:03:06Z) is the only commit that has ever touched that file (checked against main 066f2c1 and v6/instinct-rows b6e8654). If the rubric must change, the change is committed before the judged zip is opened and the new commit hash is recorded in the round's REVEAL doc; a rubric changed after the zip is opened voids the round.

## Sealed key

- A key file (the r2 model: `benchmark/blind/r2_KEY_v4.json`) maps labels to arms. It is written before judging starts and its sha256 is committed.
- The key is opened only after the judge's ranks commit lands.
- The REVEAL doc records the key sha256, the ranks commit sha256, and the ranks file sha256, mirroring `benchmark/blind/r2_REVEAL.md`.
- Leak check before the zip goes to the judge (r2 used `benchmark/blind/leakgrep_r2.py`): no arm-identifying string in any build.

## Pre-registered analysis

- Primary: judge total per app (/100) and mean rank across the 3 apps.
- Secondary: cost-weighted tokens (in + 5*out + 0.1*cache_read + 1.25*cache_write), output tokens, build seconds, checker score per build.
- n=1 build per app per arm is reported as a single sample, not a distribution - the same caveat r2 carries.
- Pass gate carried from the row scoring: v8 needs checker passes matching v4c on the same apps before any v8-over-v4c token claim. A broken build (r2's ponytail expenses went 17/25) is reported as broken, not averaged away.
- Integrity: the judge records any contamination in an integrity note, as r2's judge did. Any round where the key or the skill texts reach the judge's context before ranks are committed is void.

## Out of scope

No tuning-set reruns, no holdout tasks, no wall-time claims.
